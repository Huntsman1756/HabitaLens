"""Ningun artefacto de informe expone geometria."""

from __future__ import annotations

from habitalens.report import canonical_pdf_content, generate_report
from tests.conftest import make_report_manifest

_TOKENS = ("point(", "linestring", "poslist", "coordinates", "multisurface", "geojson")


def test_rendered_report_has_no_geometry(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01", "g0c07"})
    artifacts = generate_report(manifest, tmp_path / "out")
    html = artifacts.html_path.read_text(encoding="utf-8").lower()
    pdf = canonical_pdf_content(artifacts.pdf_path).lower()
    for text in (html, pdf):
        for token in _TOKENS:
            assert token not in text, token
