"""Comparabilidad de superficie: nunca 'el anuncio miente' sin concepto."""

from __future__ import annotations

from habitalens.evidence.surface import (
    KIND_MISMATCH,
    KIND_POTENTIAL,
    AreaComparison,
    ComparabilityStatus,
    SurfaceComponents,
    SurfaceConcept,
    area_finding,
    compare_area,
)
from habitalens.property.models import FORBIDDEN_FIELD_TOKENS

OFFICIAL = SurfaceComponents(built_m2=82.0, common_m2=9.0, annex_m2=12.0)


def test_unknown_concept_is_potential_not_factual() -> None:
    result = compare_area(95.0, OFFICIAL, advertised_concept=SurfaceConcept.UNKNOWN)
    assert result.comparability == ComparabilityStatus.NOT_COMPARABLE
    assert result.kind == KIND_POTENTIAL
    assert result.reference_m2 == 91.0  # construida + comunes
    assert result.difference_m2 == 4.0


def test_built_concept_is_direct_mismatch() -> None:
    result = compare_area(95.0, OFFICIAL, advertised_concept=SurfaceConcept.CONSTRUIDA)
    assert result.comparability == ComparabilityStatus.DIRECT
    assert result.kind == KIND_MISMATCH
    assert result.reference_m2 == 82.0
    assert result.exceeds_tolerance is True


def test_built_with_common_is_direct() -> None:
    result = compare_area(
        93.0, OFFICIAL, advertised_concept=SurfaceConcept.CONSTRUIDA_CON_COMUNES, tolerance=0.05
    )
    assert result.comparability == ComparabilityStatus.DIRECT
    assert result.reference_m2 == 91.0
    assert result.exceeds_tolerance is False


def test_util_is_partial() -> None:
    result = compare_area(80.0, SurfaceComponents(built_m2=100.0), advertised_concept=SurfaceConcept.UTIL)
    assert result.comparability == ComparabilityStatus.PARTIAL
    assert result.kind == KIND_POTENTIAL
    assert result.exceeds_tolerance is True
    finding = area_finding("p1", result, source_version="test")
    assert finding.kind == KIND_POTENTIAL
    assert "no acredita discrepancia" in finding.note


def test_insufficient_when_no_official_built() -> None:
    official = SurfaceComponents(common_m2=9.0)
    result = compare_area(95.0, official, advertised_concept=SurfaceConcept.CONSTRUIDA)
    assert result.comparability == ComparabilityStatus.INSUFFICIENT
    assert result.reference_m2 is None
    assert result.exceeds_tolerance is None


def test_area_finding_kind_and_no_leak() -> None:
    result = compare_area(95.0, OFFICIAL, advertised_concept=SurfaceConcept.UNKNOWN, refcat="X")
    finding = area_finding("p1", result, source_version="p1-v1")
    assert finding.kind == KIND_POTENTIAL
    assert finding.status.value == "derived"
    for field in type(finding).model_fields:
        assert not any(token in field.lower() for token in FORBIDDEN_FIELD_TOKENS)
    payload = finding.model_dump_json().lower()
    for token in ("poslist", "coordinates", "polygon", "__geo_interface__"):
        assert token not in payload
    assert "verificar que concepto" in (finding.note or "")


def test_area_comparison_is_frozen_dataclass() -> None:
    result = compare_area(95.0, OFFICIAL)
    assert isinstance(result, AreaComparison)
