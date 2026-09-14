"""Determinismo: misma evidencia (manifest) -> mismo informe."""

from __future__ import annotations

import json

from habitalens.report import generate_report
from tests.conftest import make_report_manifest


def test_html_and_pdf_are_deterministic(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01", "g0c05", "g0c07"})
    first = generate_report(manifest, tmp_path / "r1")
    second = generate_report(manifest, tmp_path / "r2")

    assert first.html_sha256 == second.html_sha256
    assert first.pdf_canonical_sha256 == second.pdf_canonical_sha256
    assert first.pdf_pages == second.pdf_pages


def test_manifest_artifacts_are_stable(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01", "g0c07"})
    first = generate_report(manifest, tmp_path / "r1")
    second = generate_report(manifest, tmp_path / "r2")

    manifest_a = json.loads(first.manifest_path.read_text(encoding="utf-8"))
    manifest_b = json.loads(second.manifest_path.read_text(encoding="utf-8"))
    assert manifest_a["artifacts"] == manifest_b["artifacts"]
    assert manifest_a["properties"] == manifest_b["properties"]
