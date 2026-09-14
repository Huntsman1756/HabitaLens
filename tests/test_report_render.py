"""Render HTML/PDF desde el manifest (fuente unica de verdad)."""

from __future__ import annotations

from habitalens.report import build_view_model, canonical_pdf_content, generate_report, render_html
from habitalens.report.disclaimers import missing_disclaimers
from tests.conftest import make_report_manifest


def _manifest(tmp_path):
    return make_report_manifest(tmp_path, property_ids={"g0c01", "g0c07"})


def test_generate_report_creates_artifacts(tmp_path) -> None:
    manifest = _manifest(tmp_path)
    artifacts = generate_report(manifest, tmp_path / "out")

    assert artifacts.html_path.exists()
    assert artifacts.pdf_path.exists()
    assert artifacts.manifest_path.exists()
    assert artifacts.pdf_pages >= 1

    html = artifacts.html_path.read_text(encoding="utf-8")
    pdf = canonical_pdf_content(artifacts.pdf_path)
    source_ids = [source["source"] for source in manifest["sources"]]
    assert missing_disclaimers(html, source_ids) == []
    assert missing_disclaimers(pdf, source_ids) == []


def test_report_states_are_explicit(tmp_path) -> None:
    artifacts = generate_report(_manifest(tmp_path), tmp_path / "out")
    html = artifacts.html_path.read_text(encoding="utf-8")
    assert "OBSERVED" in html
    assert "UNAVAILABLE" in html
    assert "INCONCLUSIVE" in html
    # El caso SIU sin cobertura acreditada se presenta como INCONCLUSIVE.
    assert "no acreditada" in html or "INCONCLUSIVE" in html


def test_html_renders_from_view_model(tmp_path) -> None:
    manifest = _manifest(tmp_path)
    view = build_view_model(manifest)
    html = render_html(view)
    for entry in manifest["properties"]:
        assert entry["property_id"] in html
    assert view.disclaimers
