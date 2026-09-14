"""Semantica de cobertura: 0 features no es ausencia; null no es fuera de cobertura."""

from __future__ import annotations

import pytest

from habitalens.evidence import EvidenceEngine
from habitalens.evidence.corpus_g0c import CORPUS_G0C
from habitalens.evidence.coverage import CoverageStatus, declared_envelope
from tests.conftest import g0c_golden, load_g0c_property, make_g0c_sources

_FINGERPRINT = ("status", "observed", "value", "unit")


def _fingerprint(report) -> dict:
    return {
        finding.kind: (
            finding.status.value,
            finding.observed,
            round(finding.value, 3) if isinstance(finding.value, (int, float)) else finding.value,
            finding.unit,
        )
        for finding in report.findings
    }


def test_declared_envelope_unit() -> None:
    inside = declared_envelope(-3.7, 40.4, (-19.0, 27.0, 6.0, 46.0), "ncse02")
    outside = declared_envelope(-30.0, 10.0, (-19.0, 27.0, 6.0, 46.0), "ncse02")
    assert inside.status == CoverageStatus.COVERED
    assert outside.status == CoverageStatus.NOT_COVERED


def test_siu_zero_features_is_inconclusive_not_absence() -> None:
    golden = g0c_golden("_results.json")
    siu = {pid: rep for pid, rep in golden.items()}
    statuses = [
        finding["status"]
        for rep in siu.values()
        for finding in rep["findings"]
        if finding["source"] == "siu"
    ]
    assert "inconclusive" in statuses, "debe haber al menos un caso sin cobertura acreditada"
    assert "unavailable" not in statuses, "SIU no usa UNAVAILABLE para 0 features"
    # g0c07 (Navarra) es el caso sin cobertura acreditada -> INCONCLUSIVE
    g0c07 = next(f for f in golden["g0c07"]["findings"] if f["source"] == "siu")
    assert g0c07["status"] == "inconclusive"
    assert g0c07["observed"] is None


def test_ncse_null_inside_coverage_is_unavailable_not_observed() -> None:
    golden = g0c_golden("_results.json")
    ncse = [f for rep in golden.values() for f in rep["findings"] if f["source"] == "ncse02"]
    unavailable = [f for f in ncse if f["status"] == "unavailable"]
    observed = [f for f in ncse if f["status"] == "observed"]
    assert unavailable and observed
    # Ningun OBSERVED puede tener valor nulo; ningun UNAVAILABLE puede tener valor.
    assert all(f["value"] is not None for f in observed)
    assert all(f["value"] is None for f in unavailable)


def test_btn_absence_inside_coverage_is_observed_absence() -> None:
    golden = g0c_golden("_results.json")
    btn = [f for rep in golden.values() for f in rep["findings"] if f["kind"] == "btn.roads"]
    assert any(f["observed"] is True for f in btn)
    assert any(f["observed"] is False for f in btn)
    assert all(f["status"] == "observed" for f in btn)


@pytest.mark.parametrize("item", CORPUS_G0C, ids=[c.id for c in CORPUS_G0C])
def test_g0c_golden_replay(item, tmp_path) -> None:
    wkt, source_crs = load_g0c_property(item.id)
    report = EvidenceEngine(sources=make_g0c_sources(tmp_path)).evaluate(item, wkt, source_crs)
    expected = _fingerprint_report(g0c_golden("_results.json")[item.id])
    assert _fingerprint(report) == expected


def _fingerprint_report(golden: dict) -> dict:
    return {
        finding["kind"]: (
            finding["status"],
            finding.get("observed"),
            round(finding["value"], 3)
            if isinstance(finding.get("value"), (int, float))
            else finding.get("value"),
            finding.get("unit"),
        )
        for finding in golden["findings"]
    }
