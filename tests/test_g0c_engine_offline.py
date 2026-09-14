"""Motor G0-C: determinismo y no fuga de geometria."""

from __future__ import annotations

from habitalens.evidence import EvidenceEngine
from habitalens.evidence.corpus_g0c import CORPUS_G0C
from habitalens.property.models import FORBIDDEN_FIELD_TOKENS
from tests.conftest import load_g0c_property, make_g0c_sources

IGNORED = ("retrieved_at", "provenance_id")


def test_g0c_engine_is_deterministic(tmp_path) -> None:
    item = CORPUS_G0C[0]
    wkt, source_crs = load_g0c_property(item.id)
    engine = EvidenceEngine(sources=make_g0c_sources(tmp_path))
    first = engine.evaluate(item, wkt, source_crs)
    second = engine.evaluate(item, wkt, source_crs)

    def normalized(report):
        return [f.model_dump(exclude=set(IGNORED)) for f in report.findings]

    assert normalized(first) == normalized(second)


def test_g0c_findings_do_not_leak_geometry(tmp_path) -> None:
    item = CORPUS_G0C[5]
    wkt, source_crs = load_g0c_property(item.id)
    report = EvidenceEngine(sources=make_g0c_sources(tmp_path)).evaluate(item, wkt, source_crs)
    for finding in report.findings:
        for field in type(finding).model_fields:
            assert not any(token in field.lower() for token in FORBIDDEN_FIELD_TOKENS)
    payload = report.model_dump_json().lower()
    for token in ("poslist", "coordinates", "geojson", "__geo_interface__", "linestring", "multisurface"):
        assert token not in payload


def test_g0c_findings_record_crs(tmp_path) -> None:
    item = CORPUS_G0C[0]
    wkt, source_crs = load_g0c_property(item.id)
    report = EvidenceEngine(sources=make_g0c_sources(tmp_path)).evaluate(item, wkt, source_crs)
    assert report.source_crs == source_crs
    assert report.operational_crs == "EPSG:25830"
    assert all(f.operational_crs == "EPSG:25830" for f in report.findings)
