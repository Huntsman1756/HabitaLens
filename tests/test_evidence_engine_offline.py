"""Replay determinista del corpus + guarda de no fuga de geometria."""

from __future__ import annotations

import pytest

from habitalens.evidence import CORPUS, EvidenceEngine
from habitalens.evidence.models import EvidenceFinding, PropertyEvidence
from habitalens.property.models import FORBIDDEN_FIELD_TOKENS
from tests.conftest import (
    PROPERTIES,
    evidence_golden,
    load_property,
    make_evidence_sources,
)

IGNORED = ("retrieved_at", "provenance_id")


def _fingerprint(report: PropertyEvidence) -> dict:
    return {
        finding.kind: (
            finding.status.value,
            finding.observed,
            round(finding.value, 3) if isinstance(finding.value, (int, float)) else finding.value,
            finding.unit,
            finding.source_crs,
            finding.operational_crs,
        )
        for finding in report.findings
    }


@pytest.mark.parametrize("item", CORPUS, ids=[c.id for c in CORPUS])
def test_golden_replay_matches_live_capture(item, tmp_path) -> None:
    wkt, source_crs = load_property(item.id)
    engine = EvidenceEngine(sources=make_evidence_sources(tmp_path))
    report = engine.evaluate(item, wkt, source_crs)

    golden = evidence_golden("_results.json")[item.id]
    expected = {
        finding["kind"]: (
            finding["status"],
            finding.get("observed"),
            round(finding["value"], 3)
            if isinstance(finding.get("value"), (int, float))
            else finding.get("value"),
            finding.get("unit"),
            finding.get("source_crs"),
            finding.get("operational_crs"),
        )
        for finding in golden["findings"]
    }
    assert _fingerprint(report) == expected


def test_engine_is_deterministic(tmp_path) -> None:
    item = CORPUS[0]
    wkt, source_crs = load_property(item.id)
    engine = EvidenceEngine(sources=make_evidence_sources(tmp_path))
    first = engine.evaluate(item, wkt, source_crs)
    second = engine.evaluate(item, wkt, source_crs)

    def normalized(report):
        return [
            finding.model_dump(exclude=set(IGNORED)) for finding in report.findings
        ]

    assert normalized(first) == normalized(second)


def test_csn_is_inconclusive_not_unavailable(tmp_path) -> None:
    item = CORPUS[0]
    wkt, source_crs = load_property(item.id)
    report = EvidenceEngine(sources=make_evidence_sources(tmp_path)).evaluate(
        item, wkt, source_crs
    )
    csn = [f for f in report.findings if f.source == "csn_radon"]
    assert csn and all(f.status.value == "inconclusive" for f in csn)


def test_no_geometry_leakage(tmp_path) -> None:
    item = CORPUS[0]
    wkt, source_crs = load_property(item.id)
    report = EvidenceEngine(sources=make_evidence_sources(tmp_path)).evaluate(
        item, wkt, source_crs
    )
    for model in (EvidenceFinding, PropertyEvidence):
        for field in model.model_fields:
            assert not any(token in field.lower() for token in FORBIDDEN_FIELD_TOKENS)
        assert not hasattr(model, "__geo_interface__")
    payload = report.model_dump_json().lower()
    for token in ("poslist", "polygon", "coordinates", "geojson", "__geo_interface__", "shape"):
        assert token not in payload


def test_property_fixtures_are_internal_only() -> None:
    # Las geometrias de propiedad viven solo en fixtures de test, no en el paquete.
    assert any(PROPERTIES.glob("*.wkt"))
