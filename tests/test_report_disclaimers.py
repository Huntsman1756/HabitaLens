"""Disclaimers obligatorios presentes e insustituibles."""

from __future__ import annotations

import pytest

from habitalens import DISCLAIMER
from habitalens.report.disclaimers import (
    DisclaimerError,
    assert_disclaimers,
    required_disclaimers,
)


def test_disclaimer_text_is_the_mandatory_one() -> None:
    assert "no representa ni sustituye" in DISCLAIMER
    assert "caracter oficial ni fehaciente" in DISCLAIMER


def test_assert_disclaimers_raises_when_missing() -> None:
    with pytest.raises(DisclaimerError):
        assert_disclaimers("texto sin avisos", ["siu", "ncse02"])


def test_assert_disclaimers_passes_when_present() -> None:
    text = "\n".join(required_disclaimers(["siu", "ncse02", "btn"]))
    assert_disclaimers(text, ["siu", "ncse02", "btn"])


def test_attribution_per_source_required() -> None:
    assert any("SIU" in item for item in required_disclaimers(["siu"]))
    assert any("IGN" in item for item in required_disclaimers(["ncse02"]))
    assert any("NO activada" in item or "INCONCLUSIVE" in item for item in required_disclaimers(["csn_radon"]))
