"""Discrepancia de superficie anunciada vs oficial."""

from __future__ import annotations

import pytest

from habitalens.evidence.models import FindingStatus
from habitalens.evidence.surface import compare_surface, surface_finding
from habitalens.property.models import FORBIDDEN_FIELD_TOKENS


def test_exact_match() -> None:
    result = compare_surface(100.0, 100.0)
    assert result.difference_m2 == 0.0
    assert result.relative_difference == 0.0
    assert result.exceeds_tolerance is False


def test_advertised_larger_within_tolerance() -> None:
    result = compare_surface(103.0, 100.0, tolerance=0.05)
    assert result.relative_difference == pytest.approx(0.03)
    assert result.exceeds_tolerance is False


def test_advertised_larger_exceeds_tolerance() -> None:
    result = compare_surface(120.0, 100.0, tolerance=0.05)
    assert result.difference_m2 == pytest.approx(20.0)
    assert result.relative_difference == pytest.approx(0.20)
    assert result.exceeds_tolerance is True


def test_advertised_smaller_exceeds_tolerance() -> None:
    result = compare_surface(80.0, 100.0, tolerance=0.05)
    assert result.relative_difference == pytest.approx(-0.20)
    assert result.exceeds_tolerance is True


def test_invalid_inputs_raise() -> None:
    with pytest.raises(ValueError):
        compare_surface(0.0, 100.0)
    with pytest.raises(ValueError):
        compare_surface(100.0, -1.0)
    with pytest.raises(ValueError):
        compare_surface(100.0, 100.0, tolerance=-0.1)


def test_surface_finding_is_derived_and_leak_free() -> None:
    comparison = compare_surface(90.0, 100.0, refcat="1234567VK1234A")
    finding = surface_finding("p1", comparison, source_version="surface-v1")
    assert finding.status == FindingStatus.DERIVED
    assert finding.unit == "m2"
    for field in type(finding).model_fields:
        assert not any(token in field.lower() for token in FORBIDDEN_FIELD_TOKENS)
    payload = finding.model_dump_json().lower()
    for token in ("poslist", "coordinates", "polygon", "__geo_interface__"):
        assert token not in payload
