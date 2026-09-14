"""Render HTML/PDF desde el ReportViewModel (nunca desde la evidencia directa)."""

from __future__ import annotations

import html as html_lib
from pathlib import Path

from habitalens.report.model import PropertyView, ReportViewModel

PDF_ENGINE = "fpdf2"
FONT_STACK = "Helvetica (core)"
_FONT = "Helvetica"
_PDF_SAFE = str.maketrans(
    {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u", "ñ": "n", "ü": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U", "Ñ": "N", "Ü": "U",
    }
)


def _property_html(prop: PropertyView) -> str:
    rows = []
    for finding in prop.findings:
        note = html_lib.escape(finding.note or "")
        rows.append(
            "      <tr>"
            f"<td>{html_lib.escape(finding.source)}</td>"
            f"<td>{html_lib.escape(finding.label)}</td>"
            f"<td>{html_lib.escape(finding.status)}</td>"
            f"<td>{html_lib.escape(finding.status_label)}</td>"
            f"<td>{html_lib.escape(finding.value_text)}</td>"
            f"<td>{html_lib.escape(finding.source_crs or '')} / {html_lib.escape(finding.operational_crs or '')}</td>"
            f"<td>{html_lib.escape(finding.method)}</td>"
            f"<td>{html_lib.escape(finding.provenance_id or '')}</td>"
            f"<td>{note}</td>"
            "      </tr>"
        )
    return (
        f'    <article class="property" id="property-{html_lib.escape(prop.property_id)}">\n'
        f"      <h2>{html_lib.escape(prop.label)}</h2>\n"
        f'      <p class="identity">propiedad: {html_lib.escape(prop.property_id)} | '
        f"refcat: {html_lib.escape(prop.refcat)} | "
        f"crs fuente: {html_lib.escape(prop.source_crs)} | "
        f"crs operacional: {html_lib.escape(prop.operational_crs)}</p>\n"
        "      <table>\n"
        "        <thead><tr><th>fuente</th><th>hallazgo</th><th>estado</th><th>estado (es)</th>"
        "<th>valor</th><th>crs</th><th>metodo</th><th>provenance</th><th>nota</th></tr></thead>\n"
        "        <tbody>\n" + "\n".join(rows) + "\n        </tbody>\n"
        "      </table>\n"
        "    </article>"
    )


def render_html(view: ReportViewModel) -> str:
    disclaimers = "\n".join(
        f'      <li>{html_lib.escape(text)}</li>' for text in view.disclaimers
    )
    properties = "\n".join(_property_html(prop) for prop in view.properties)
    return (
        '<!doctype html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        f"<title>HabitaLens - {html_lib.escape(view.report_id)}</title>\n"
        "</head>\n<body>\n"
        "  <header>\n"
        "    <h1>Informe HabitaLens</h1>\n"
        f'    <p class="meta">informe: {html_lib.escape(view.report_id)} | '
        f"fecha: {html_lib.escape(view.generated_at)} | plantilla: 1</p>\n"
        "  </header>\n"
        '  <section id="disclaimers">\n    <h2>Disclaimers y atribuciones</h2>\n    <ul>\n'
        f"{disclaimers}\n    </ul>\n  </section>\n"
        "  <main>\n"
        f"{properties}\n"
        "  </main>\n"
        "</body>\n</html>\n"
    )


def _finding_lines(prop: PropertyView) -> list[str]:
    lines = [
        f"- {prop.label}",
        f"  propiedad {prop.property_id} | refcat {prop.refcat}",
        f"  crs fuente {prop.source_crs} | crs operacional {prop.operational_crs}",
    ]
    for finding in prop.findings:
        note = f" | nota: {finding.note}" if finding.note else ""
        lines.append(
            f"  * {finding.label} [{finding.status}] {finding.value_text} "
            f"(fuente {finding.source} {finding.source_crs}/{finding.operational_crs}; "
            f"metodo {finding.method}; provenance {finding.provenance_id}){note}"
        )
    return lines


def _line(pdf, height: float, text: str, size: float) -> None:
    pdf.set_font(_FONT, size=size)
    pdf.multi_cell(0, height, _safe(text), new_x="LMARGIN", new_y="NEXT")


def render_pdf(view: ReportViewModel, path: Path) -> Path:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_title(f"HabitaLens - {view.report_id}")
    pdf.set_author("HabitaLens")
    pdf.set_creator("HabitaLens G0-D")
    pdf.set_subject("Informe de evidencia (sin valoracion)")
    pdf.add_page()
    _line(pdf, 8, "Informe HabitaLens", 14)
    _line(pdf, 6, f"Informe: {view.report_id} | fecha: {view.generated_at}", 10)
    _line(pdf, 6, "Disclaimers y atribuciones", 11)
    for text in view.disclaimers:
        _line(pdf, 5, f"- {text}", 8)
    for prop in view.properties:
        for line in _finding_lines(prop):
            _line(pdf, 5, line, 9)
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(path))
    return path


def _safe(text: str) -> str:
    return text.translate(_PDF_SAFE).encode("latin-1", errors="replace").decode("latin-1")


def canonical_pdf_content(path: Path) -> str:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    pages = [(page.extract_text() or "").strip() for page in reader.pages]
    return "\n\f\n".join(pages)


def pdf_page_count(path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(str(path)).pages)
