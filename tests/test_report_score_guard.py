"""Guard fuerte contra scores/valoraciones agregadas."""

from __future__ import annotations

import pytest

from habitalens.report import (
    ScoreGuardError,
    assert_no_score,
    find_forbidden_terms,
    generate_report,
)
from habitalens.report.guard import FORBIDDEN_SCORE_TERMS
from tests.conftest import make_report_manifest


@pytest.mark.parametrize("term", FORBIDDEN_SCORE_TERMS)
def test_each_forbidden_term_is_detected(term: str) -> None:
    assert term in find_forbidden_terms(f"El informe incluye {term} de la vivienda")


def test_clean_evidence_text_passes() -> None:
    assert_no_score("Estados: OBSERVED, DERIVED, UNAVAILABLE, INCONCLUSIVE. Informe sin opinion.")


def test_score_like_words_inside_words_do_not_trigger() -> None:
    assert find_forbidden_terms("clasificacion del suelo y recomendablemente neutro") == []


def test_generate_report_rejects_injected_aggregate_score(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["properties"][0]["findings"][0]["note"] = "overall_score: 8 (semaforo verde)"
    with pytest.raises(ScoreGuardError):
        generate_report(manifest, tmp_path / "out")
