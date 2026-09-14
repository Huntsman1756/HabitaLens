"""Servicio de generacion: manifest -> view model -> HTML + PDF (G0-D)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from habitalens.report.disclaimers import assert_disclaimers
from habitalens.report.guard import assert_no_score
from habitalens.report.manifest import assert_no_geometry_keys, canonical_json
from habitalens.report.model import build_view_model
from habitalens.report.render import (
    FONT_STACK,
    PDF_ENGINE,
    canonical_pdf_content,
    pdf_page_count,
    render_html,
    render_pdf,
)


@dataclass(frozen=True)
class ReportArtifacts:
    html_path: Path
    pdf_path: Path
    manifest_path: Path
    html_sha256: str
    pdf_canonical_sha256: str
    pdf_pages: int


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def generate_report(manifest: dict, out_dir: Path) -> ReportArtifacts:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    view = build_view_model(manifest)
    source_ids = [source["source"] for source in manifest["sources"]]

    html = render_html(view)
    assert_no_score(html)
    assert_disclaimers(html, source_ids)
    assert_no_geometry_keys(manifest)

    html_path = out_dir / "report.html"
    html_path.write_text(html, encoding="utf-8")

    pdf_path = render_pdf(view, out_dir / "report.pdf")
    pdf_content = canonical_pdf_content(pdf_path)
    assert_no_score(pdf_content)
    assert_disclaimers(pdf_content, source_ids)

    manifest = dict(manifest)
    manifest["artifacts"] = {
        "html": {"sha256": _sha256(html)},
        "pdf": {
            "canonical_sha256": _sha256(pdf_content),
            "pages": pdf_page_count(pdf_path),
            "engine": PDF_ENGINE,
            "font_stack": FONT_STACK,
        },
    }
    assert_no_geometry_keys(manifest)
    manifest_path = out_dir / "provenance_manifest.json"
    manifest_path.write_text(canonical_json(manifest), encoding="utf-8")

    return ReportArtifacts(
        html_path=html_path,
        pdf_path=pdf_path,
        manifest_path=manifest_path,
        html_sha256=_sha256(html),
        pdf_canonical_sha256=_sha256(pdf_content),
        pdf_pages=pdf_page_count(pdf_path),
    )
