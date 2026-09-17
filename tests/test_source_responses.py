from __future__ import annotations

import json
import socket
from pathlib import Path
from xml.etree.ElementTree import ParseError

import pytest
from shapely.geometry import box, mapping

from habitalens.cache import CacheStore
from habitalens.evidence import CorpusProperty, EvidenceEngine
from habitalens.evidence.models import FindingStatus
from habitalens.net import FixtureSource, HttpxTransport
from habitalens.provenance import ProvenanceRecorder
from habitalens.sources import get_source
from habitalens.sources.btn.source import _lines
from habitalens.sources.eprtr.source import _points
from habitalens.sources.ncse02.source import _features
from habitalens.sources.snczi.source import _polygons

PROPERTY = CorpusProperty("response", "n/a", "n/a", "control", "n/a", "control")
GEOMETRY = box(-3.71, 40.40, -3.70, 40.41)
JSON_SOURCES = ("eprtr", "snczi", "siu")
XML_SOURCES = ("btn", "ncse02")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        pytest.fail("network access is forbidden")

    monkeypatch.setattr(HttpxTransport, "send", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)


def _source(tmp_path: Path, source_id: str, content: bytes):
    return get_source(
        source_id,
        source=FixtureSource({source_id: content}),
        cache=CacheStore(tmp_path / source_id),
        provenance=ProvenanceRecorder(tmp_path / source_id),
    )


def _report(tmp_path: Path, source_id: str, content: bytes):
    source = _source(tmp_path, source_id, content)
    return EvidenceEngine(sources={source_id: source}).evaluate(
        PROPERTY, GEOMETRY.wkt, "EPSG:4326"
    )


def _collection(features=(), **metadata) -> bytes:
    return json.dumps({"type": "FeatureCollection", "features": list(features), **metadata}).encode()


def _feature(geometry=None, properties=None):
    return {"type": "Feature", "geometry": geometry, "properties": properties or {}}


def _xml(body="", attributes='numberMatched="0" numberReturned="0"') -> bytes:
    return (
        '<wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" '
        'xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:t="urn:test" '
        f'{attributes}>{body}</wfs:FeatureCollection>'
    ).encode()


def _road(positions="40.405 -3.72 40.405 -3.69"):
    return (
        '<wfs:member><t:RoadLink><gml:LineString srsName="urn:ogc:def:crs:EPSG::4258">'
        f'<gml:posList>{positions}</gml:posList></gml:LineString></t:RoadLink></wfs:member>'
    )


def _hazard(value="0.12", positions="40.39 -3.72 40.39 -3.69 40.42 -3.69 40.42 -3.72 40.39 -3.72"):
    field = "" if value is None else f"<t:aceleracion>{value}</t:aceleracion>"
    return (
        f'<wfs:member><t:HazardArea2002.NCSE-02>{field}'
        '<gml:Polygon srsName="urn:ogc:def:crs:EPSG::4258"><gml:exterior><gml:LinearRing>'
        f'<gml:posList>{positions}</gml:posList>'
        '</gml:LinearRing></gml:exterior></gml:Polygon></t:HazardArea2002.NCSE-02></wfs:member>'
    )


def _assert_error(tmp_path, source_id, content):
    source = _source(tmp_path, source_id, content)
    with pytest.raises((ValueError, TypeError)):
        source.evaluate(GEOMETRY, "EPSG:4326", "EPSG:25830", PROPERTY.id)
    report = _report(tmp_path, source_id, content)
    assert len(report.findings) == 1
    finding = report.findings[0]
    assert finding.kind == f"{source_id}.status"
    assert finding.status == FindingStatus.INCONCLUSIVE
    assert finding.observed is None and finding.value is None


@pytest.mark.parametrize("source_id", JSON_SOURCES)
@pytest.mark.parametrize("content", [
    b'{"error":{"code":503,"message":"Service temporarily unavailable"}}',
    b'{"exceptions":[{"message":"Layer unavailable"}]}',
    b'{}', b'[]', b'null', b'{', b'<html>Service unavailable</html>',
    b'{"type":"FeatureCollection"}',
    b'{"type":"FeatureCollection","features":null}',
    b'{"type":"FeatureCollection","features":{}}',
    b'{"type":"FeatureCollection","features":[],"error":{}}',
    b'{"type":"FeatureCollection","features":[],"label":"\xff"}',
    _collection([None]), _collection([{}]),
    _collection([{"type": "Feature", "properties": []}]),
])
def test_json_errors_never_become_absence(tmp_path, source_id, content):
    _assert_error(tmp_path, source_id, content)


@pytest.mark.parametrize("source_id", JSON_SOURCES)
@pytest.mark.parametrize("metadata", [
    {"numberMatched": 1}, {"numberReturned": 1}, {"totalFeatures": 2},
    {"count": 1}, {"numberMatched": -1}, {"numberMatched": True},
    {"numberReturned": "invalid"}, {"numberReturned": 0.5},
    {"exceededTransferLimit": True}, {"properties": {"exceededTransferLimit": True}},
    {"hasMore": True}, {"truncated": True}, {"next": "page-2"},
    {"links": [{"rel": "next", "href": "page-2"}]},
])
def test_json_incomplete_responses_are_rejected(tmp_path, source_id, metadata):
    _assert_error(tmp_path, source_id, _collection(**metadata))


@pytest.mark.parametrize("source_id", ("snczi", "siu"))
def test_zero_features_without_coverage_is_inconclusive(tmp_path, source_id):
    report = _report(tmp_path, source_id, _collection(numberMatched=0, numberReturned=0))
    assert report.findings
    for finding in report.findings:
        assert finding.status == FindingStatus.INCONCLUSIVE
        assert finding.observed is None and finding.value is None
        assert finding.provenance_id


def test_eprtr_valid_empty_retains_bounded_absence(tmp_path):
    report = _report(tmp_path, "eprtr", _collection())
    facilities, nearest = report.findings
    assert facilities.status == FindingStatus.OBSERVED
    assert facilities.observed is False and facilities.value == 0
    assert nearest.status == FindingStatus.DERIVED and nearest.value is None


@pytest.mark.parametrize("source_id,parser", [("eprtr", _points), ("snczi", _polygons)])
@pytest.mark.parametrize("geometry", [
    None, {}, {"type": "Point", "coordinates": []},
    {"type": "Point", "coordinates": [float("nan"), 40]},
    {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
])
def test_bad_geometry_is_not_silently_skipped(tmp_path, source_id, parser, geometry):
    content = _collection([_feature(geometry)])
    with pytest.raises((ValueError, TypeError)):
        parser(content)
    _assert_error(tmp_path, source_id, content)


def test_eprtr_positive_and_nearest_name_remain_aligned(tmp_path):
    content = _collection([
        _feature({"type": "Point", "coordinates": [-3.74, 40.4]}, {"siteName": "far"}),
        _feature({"type": "Point", "coordinates": [-3.705, 40.405]}, {"siteName": "near"}),
    ], count=2, exceededTransferLimit=False)
    facilities, nearest = _report(tmp_path, "eprtr", content).findings
    assert facilities.observed is True and facilities.value == 2
    assert nearest.value == 0 and nearest.note == "near"
    data = json.loads(content)
    data["features"][0]["geometry"] = None
    _assert_error(tmp_path, "eprtr", json.dumps(data).encode())


@pytest.mark.parametrize("intersects", [True, False])
def test_snczi_requires_verified_hit(tmp_path, intersects):
    polygon = GEOMETRY.buffer(0.001) if intersects else box(-4, 39, -3.9, 39.1)
    content = _collection([_feature(mapping(polygon))], numberMatched=1, numberReturned=1)
    for finding in _report(tmp_path, "snczi", content).findings:
        assert finding.status == (FindingStatus.OBSERVED if intersects else FindingStatus.INCONCLUSIVE)
        assert finding.observed is (True if intersects else None)
        assert finding.value == (1 if intersects else None)


@pytest.mark.parametrize("classes", [["Urbano"], ["Urbano", "Rural"], ["Rural", "Urbano"]])
def test_siu_intersecting_classes_are_observed(tmp_path, classes):
    # La consulta envia la parcela por POST; solo vuelven clases que la
    # intersectan de verdad (verificado por el servidor).
    content = _collection([_feature(properties={"ClaseSuelo": value, "ProvINE": "28"}) for value in classes])
    finding, = _report(tmp_path, "siu", content).findings
    assert finding.kind == "siu.clase_suelo"
    assert finding.status == FindingStatus.OBSERVED
    assert finding.observed is True
    assert finding.value == len(set(classes)) and finding.unit == "classes"
    assert all(value in finding.note for value in set(classes))
    assert finding.method == "arcgis-rest-parcel-intersects"


@pytest.mark.parametrize("source_id", XML_SOURCES)
@pytest.mark.parametrize("content", [
    b'<ExceptionReport><Exception>Service unavailable</Exception></ExceptionReport>',
    b'<ServiceExceptionReport><ServiceException>Layer unavailable</ServiceException></ServiceExceptionReport>',
    b'<html>Service unavailable</html>', b'<FeatureCollection>',
    _xml('<t:Exception>Service unavailable</t:Exception>'),
    _xml('<wfs:member/>'),
    _xml('<wfs:member><t:Unexpected/></wfs:member>'),
    _xml(attributes='numberMatched="1" numberReturned="0"'),
    _xml(attributes='numberReturned="1"'),
    _xml(attributes='numberMatched="-1"'),
    _xml(attributes='numberMatched="invalid"'),
    _xml(attributes='next="page-2"'),
    _xml(attributes='truncated="true"'),
])
def test_xml_errors_and_incomplete_collections(tmp_path, source_id, content):
    source = _source(tmp_path, source_id, content)
    with pytest.raises((ValueError, ParseError)):
        source.evaluate(GEOMETRY, "EPSG:4326", "EPSG:25830", PROPERTY.id)
    report = _report(tmp_path, source_id, content)
    finding, = report.findings
    assert finding.kind == f"{source_id}.status"
    assert finding.status == FindingStatus.INCONCLUSIVE
    assert finding.observed is None and finding.value is None


@pytest.mark.parametrize("source_id", XML_SOURCES)
def test_valid_empty_xml_preserves_coverage_contract(tmp_path, source_id):
    report = _report(tmp_path, source_id, _xml())
    for finding in report.findings:
        assert finding.provenance_id
        if source_id == "btn":
            assert finding.status == FindingStatus.OBSERVED
            assert finding.observed is False and finding.value == 0
        else:
            assert finding.status == FindingStatus.INCONCLUSIVE
            assert finding.observed is None and finding.value is None


def test_btn_positive_and_malformed_positions(tmp_path):
    content = _xml(_road(), 'numberMatched="1" numberReturned="1"')
    assert len(_lines([content])) == 1
    report = _report(tmp_path, "btn", content)
    roads = next(f for f in report.findings if f.kind == "btn.roads")
    assert roads.status == FindingStatus.OBSERVED and roads.value == 1
    for positions in ("", "40 -3 41", "40 -3", "nan -3 41 -4"):
        _assert_error(tmp_path, "btn", _xml(_road(positions), 'numberMatched="1"'))


@pytest.mark.parametrize("value,status", [("0.12", FindingStatus.OBSERVED), ("0", FindingStatus.OBSERVED), ("", FindingStatus.UNAVAILABLE), (None, FindingStatus.UNAVAILABLE)])
def test_ncse_valid_and_explicit_null_value(tmp_path, value, status):
    content = _xml(_hazard(value), 'numberMatched="1" numberReturned="1"')
    assert len(_features(content)) == 1
    finding, = _report(tmp_path, "ncse02", content).findings
    assert finding.status == status
    assert finding.value == (float(value) if value else None)


@pytest.mark.parametrize("value", ["NaN", "inf", "not-a-number", "-0.1"])
def test_ncse_invalid_value_is_not_unavailable(tmp_path, value):
    _assert_error(tmp_path, "ncse02", _xml(_hazard(value), 'numberMatched="1"'))


@pytest.mark.parametrize("source_id,body", [
    ("btn", '<wfs:member><t:RoadLink/></wfs:member>'),
    ("ncse02", '<wfs:member><t:HazardArea2002.NCSE-02><t:aceleracion>0.1</t:aceleracion></t:HazardArea2002.NCSE-02></wfs:member>'),
    ("ncse02", _hazard(positions="40 -3 40 -4 41 -4 40")),
    ("ncse02", _hazard(positions="40 -3 40 -4 41 -4 41 -3")),
])
def test_xml_missing_or_partial_geometry_is_rejected(tmp_path, source_id, body):
    _assert_error(tmp_path, source_id, _xml(body, 'numberMatched="1"'))


@pytest.mark.parametrize("source_id,limit", [("snczi", 50), ("btn", 50), ("ncse02", 30)])
def test_request_limit_requires_complete_total(tmp_path, source_id, limit):
    if source_id == "snczi":
        features = [_feature(mapping(GEOMETRY))] * limit
        incomplete = _collection(features, numberReturned=limit, numberMatched="unknown")
        complete = _collection(features, numberReturned=limit, numberMatched=limit)
    else:
        body = (_road() if source_id == "btn" else _hazard()) * limit
        incomplete = _xml(body, f'numberReturned="{limit}" numberMatched="unknown"')
        complete = _xml(body, f'numberReturned="{limit}" numberMatched="{limit}"')
    _assert_error(tmp_path, source_id, incomplete)
    report = _report(tmp_path, source_id, complete)
    assert any(f.status == FindingStatus.OBSERVED for f in report.findings)


@pytest.mark.parametrize("source_id", JSON_SOURCES)
def test_partial_positive_json_does_not_claim_exhaustive_count(tmp_path, source_id):
    geometry = mapping(GEOMETRY) if source_id == "snczi" else {"type": "Point", "coordinates": [-3.705, 40.405]}
    _assert_error(tmp_path, source_id, _collection([_feature(geometry)], numberMatched=2, numberReturned=1))


@pytest.mark.parametrize("source_id", XML_SOURCES)
def test_partial_positive_xml_does_not_claim_exhaustive_result(tmp_path, source_id):
    body = _road() if source_id == "btn" else _hazard()
    _assert_error(tmp_path, source_id, _xml(body, 'numberMatched="2" numberReturned="1"'))


def test_snczi_degenerate_component_is_dropped_not_counted(tmp_path):
    # Un miembro MultiPolygon sin area no aporta nada (habitual en WFS publicos):
    # se descarta sin invalidar la feature. Una geometria sin nada
    # interpretable sigue siendo error.
    polygon = mapping(GEOMETRY)
    degenerate = [[[-3.7, 40.4], [-3.7, 40.4], [-3.7, 40.4], [-3.7, 40.4]]]
    content = _collection([
        _feature({"type": "MultiPolygon", "coordinates": [polygon["coordinates"], degenerate]})
    ])
    report = _report(tmp_path, "snczi", content)
    assert any(f.status == FindingStatus.OBSERVED for f in report.findings)
    _assert_error(tmp_path, "snczi", _collection([
        _feature({"type": "MultiPolygon", "coordinates": [degenerate]})
    ]))


@pytest.mark.parametrize("source_id", XML_SOURCES)
@pytest.mark.parametrize("attribute", ['srsDimension="3"', 'count="999"'])
def test_xml_position_metadata_is_validated(tmp_path, source_id, attribute):
    body = _road() if source_id == "btn" else _hazard()
    body = body.replace("<gml:posList>", f"<gml:posList {attribute}>")
    _assert_error(tmp_path, source_id, _xml(body, 'numberMatched="1"'))
