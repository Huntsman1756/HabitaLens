"""Controles positivos G0-C fuera del corpus + casos dificiles."""

from __future__ import annotations

from habitalens.evidence import EvidenceEngine
from habitalens.evidence.corpus_g0c import CorpusPropertyG0C
from habitalens.evidence.models import FindingStatus
from tests.conftest import make_g0c_sources

GRANADA = "POLYGON((-3.6065 37.1775, -3.6055 37.1775, -3.6055 37.1785, -3.6065 37.1785, -3.6065 37.1775))"
MADRID_NULL = "POLYGON((-3.7043 40.4163, -3.7033 40.4163, -3.7033 40.4173, -3.7043 40.4173, -3.7043 40.4163))"
MADRID_BTN = "POLYGON((-3.7118 40.4062, -3.7108 40.4062, -3.7108 40.4072, -3.7118 40.4072, -3.7118 40.4062))"
MADRID_SIU = "POLYGON((-3.7055 40.4155, -3.7045 40.4155, -3.7045 40.4165, -3.7055 40.4165, -3.7055 40.4155))"


def _control(property_id: str) -> CorpusPropertyG0C:
    return CorpusPropertyG0C(property_id, "C", "n/a", "n/a", "control", "control", "EPSG:4326")


def _find(report, kind: str):
    return next(f for f in report.findings if f.kind == kind)


def test_ncse_positive_control_granada(tmp_path) -> None:
    report = EvidenceEngine(sources=make_g0c_sources(tmp_path)).evaluate(
        _control("ctrl_granada_ncse"), GRANADA, "EPSG:4326"
    )
    hazard = _find(report, "ncse02.hazard")
    assert hazard.status == FindingStatus.OBSERVED
    assert hazard.value == 0.23
    assert hazard.unit == "g"


def test_ncse_null_inside_coverage_is_unavailable(tmp_path) -> None:
    report = EvidenceEngine(sources=make_g0c_sources(tmp_path)).evaluate(
        _control("ctrl_madrid_ncse_null"), MADRID_NULL, "EPSG:4326"
    )
    hazard = _find(report, "ncse02.hazard")
    assert hazard.status == FindingStatus.UNAVAILABLE
    assert hazard.value is None


def test_btn_positive_control_detects_road(tmp_path) -> None:
    report = EvidenceEngine(sources=make_g0c_sources(tmp_path)).evaluate(
        _control("ctrl_madrid_btn"), MADRID_BTN, "EPSG:4326"
    )
    roads = _find(report, "btn.roads")
    assert roads.status == FindingStatus.OBSERVED and roads.observed is True
    distance = _find(report, "btn.roads_nearest_distance_m")
    assert distance.value is not None and distance.value < 50.0


def test_siu_control_is_observed_with_verified_intersection(tmp_path) -> None:
    # La consulta SIU envia la parcela por POST: solo vuelven clases cuya
    # geometria la intersecta -> OBSERVED verificado por el servidor.
    report = EvidenceEngine(sources=make_g0c_sources(tmp_path)).evaluate(
        _control("ctrl_madrid_siu"), MADRID_SIU, "EPSG:4326"
    )
    clase = _find(report, "siu.clase_suelo")
    assert clase.status == FindingStatus.OBSERVED
    assert clase.observed is True and clase.value == 1.0
    assert "SUELO URBANO" in clase.note
