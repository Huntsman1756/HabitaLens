"""G0-D: producto. Informe HTML/PDF + manifest de procedencia.

El `provenance_manifest.json` es la fuente unica de verdad; HTML y PDF se
renderizan exclusivamente desde el `ReportViewModel` derivado del manifest, sin
reconstruir logica de evidencia. Cero score global de vivienda.
"""

from __future__ import annotations

from habitalens.report.disclaimers import (
    ATTRIBUTIONS,
    DisclaimerError,
    assert_disclaimers,
)
from habitalens.report.guard import ScoreGuardError, assert_no_score, find_forbidden_terms
from habitalens.report.manifest import (
    SCHEMA_VERSION,
    TEMPLATE_VERSION,
    build_manifest,
    canonical_json,
)
from habitalens.report.model import ReportViewModel, build_view_model
from habitalens.report.render import canonical_pdf_content, render_html, render_pdf
from habitalens.report.service import generate_report

__all__ = [
    "ATTRIBUTIONS",
    "SCHEMA_VERSION",
    "TEMPLATE_VERSION",
    "DisclaimerError",
    "ReportViewModel",
    "ScoreGuardError",
    "assert_disclaimers",
    "assert_no_score",
    "build_manifest",
    "build_view_model",
    "canonical_json",
    "canonical_pdf_content",
    "find_forbidden_terms",
    "generate_report",
    "render_html",
    "render_pdf",
]
