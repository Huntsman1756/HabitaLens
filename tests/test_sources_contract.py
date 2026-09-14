"""Contrato por fuente: controles positivos y ausencia honesta."""

from __future__ import annotations

from habitalens.evidence import CORPUS, CorpusProperty, EvidenceEngine
from habitalens.evidence.models import FindingStatus
from habitalens.sources import get_source
from tests.conftest import PROPERTIES, load_property, make_evidence_sources


def _control(property_id: str) -> CorpusProperty:
    return CorpusProperty(property_id, "n/a", "n/a", "control", "n/a", "control")


def _control_wkt(name: str) -> str:
    return (PROPERTIES / f"{name}.wkt").read_text(encoding="utf-8")


def _find(report, kind: str):
    return next(finding for finding in report.findings if finding.kind == kind)


def test_snczi_positive_control(tmp_path) -> None:
    engine = EvidenceEngine(sources=make_evidence_sources(tmp_path))
    report = engine.evaluate(
        _control("control_ebro_flood"), _control_wkt("control_ebro_flood"), "EPSG:4326"
    )
    flood = _find(report, "snczi.flood_q100")
    assert flood.status == FindingStatus.OBSERVED
    assert flood.observed is True
    assert flood.operational_crs == "EPSG:25830"


def test_snczi_absence_is_observed_not_unavailable(tmp_path) -> None:
    item = next(c for c in CORPUS if c.id == "p01_madrid_castellana")
    wkt, source_crs = load_property(item.id)
    report = EvidenceEngine(sources=make_evidence_sources(tmp_path)).evaluate(
        item, wkt, source_crs
    )
    flood = _find(report, "snczi.flood_q100")
    assert flood.status == FindingStatus.OBSERVED
    assert flood.observed is False
    assert not report.by_status(FindingStatus.UNAVAILABLE)


def test_eprtr_positive_control(tmp_path) -> None:
    engine = EvidenceEngine(sources=make_evidence_sources(tmp_path))
    report = engine.evaluate(
        _control("control_bilbao_plant"),
        _control_wkt("control_bilbao_plant"),
        "EPSG:4326",
    )
    facilities = _find(report, "eprtr.facilities")
    assert facilities.observed is True
    distance = _find(report, "eprtr.nearest_facility_distance_m")
    assert distance.status == FindingStatus.DERIVED
    assert distance.value is not None and distance.value < 5.0
    assert distance.unit == "m"


def test_eprtr_absence_reported_not_unavailable(tmp_path) -> None:
    item = next(c for c in CORPUS if c.id == "p08_araba_rustica")
    wkt, source_crs = load_property(item.id)
    report = EvidenceEngine(sources=make_evidence_sources(tmp_path)).evaluate(
        item, wkt, source_crs
    )
    facilities = _find(report, "eprtr.facilities")
    distance = _find(report, "eprtr.nearest_facility_distance_m")
    assert facilities.status == FindingStatus.OBSERVED and facilities.observed is False
    assert distance.status == FindingStatus.DERIVED and distance.value is None


def test_csn_source_is_registered_but_not_usable() -> None:
    source = get_source("csn_radon")
    assert source.usable is False
    assert source.unusable_reason
    assert "licencia" in source.unusable_reason.lower()
