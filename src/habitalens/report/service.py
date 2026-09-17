"""Servicio de generacion: manifest -> view model -> HTML + PDF (G0-D)."""

from __future__ import annotations

import hashlib
import html as html_lib
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from tempfile import TemporaryDirectory

from habitalens.report.disclaimers import assert_snapshot_disclaimers
from habitalens.report.guard import assert_no_score
from habitalens.report.manifest import assert_no_geometry_text, canonical_json, validate_manifest
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


def _publish(stage: Path, out_dir: Path) -> None:
    names = ("report.html", "report.pdf", "provenance_manifest.json")
    existed = out_dir.exists()
    backups = stage / "backups"
    backups.mkdir()
    for name in names:
        target = out_dir / name
        if target.exists():
            if not target.is_file() or target.is_symlink():
                raise ValueError("report destination must be a regular file")
            copy2(target, backups / name)
    published = []
    out_dir.mkdir(exist_ok=True)
    try:
        for name in names:
            (stage / name).replace(out_dir / name)
            published.append(name)
    except OSError:
        for name in reversed(published):
            backup = backups / name
            if backup.exists():
                backup.replace(out_dir / name)
            else:
                (out_dir / name).unlink()
        if not existed:
            out_dir.rmdir()
        raise


def generate_report(manifest: dict, out_dir: Path) -> ReportArtifacts:
    manifest = deepcopy(manifest)
    view = build_view_model(manifest)
    out_dir = Path(out_dir)
    if out_dir.is_symlink():
        raise ValueError("report destination must not be a symbolic link")

    html = render_html(view)
    assert_no_score(html_lib.unescape(html))
    assert_no_geometry_text(html_lib.unescape(html))
    assert_snapshot_disclaimers(html_lib.unescape(html), view.disclaimers)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix=".habitalens-stage-", dir=out_dir.parent) as temporary:
        stage = Path(temporary)
        html_path = stage / "report.html"
        html_path.write_bytes(html.encode("utf-8"))
        html_hash = hashlib.sha256(html_path.read_bytes()).hexdigest()
        pdf_path = render_pdf(view, stage / "report.pdf")
        pdf_content = canonical_pdf_content(pdf_path)
        assert_no_score(pdf_content)
        assert_no_geometry_text(pdf_content)
        assert_snapshot_disclaimers(pdf_content, view.disclaimers)
        pdf_hash = _sha256(pdf_content)
        pages = pdf_page_count(pdf_path)
        manifest["artifacts"] = {
            "html": {"sha256": html_hash},
            "pdf": {
                "canonical_sha256": pdf_hash,
                "pages": pages,
                "engine": PDF_ENGINE,
                "font_stack": FONT_STACK,
            },
        }
        validate_manifest(manifest)
        (stage / "provenance_manifest.json").write_bytes(canonical_json(manifest).encode("utf-8"))
        _publish(stage, out_dir)

    return ReportArtifacts(
        html_path=out_dir / "report.html",
        pdf_path=out_dir / "report.pdf",
        manifest_path=out_dir / "provenance_manifest.json",
        html_sha256=html_hash,
        pdf_canonical_sha256=pdf_hash,
        pdf_pages=pages,
    )
