"""ReportViewModel: unica representacion intermedia entre manifest y render."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from habitalens.report.disclaimers import required_disclaimers

STATUS_ORDER = ("OBSERVED", "DERIVED", "UNAVAILABLE", "INCONCLUSIVE")

STATUS_LABELS = {
    "observed": "OBSERVED (observado)",
    "derived": "DERIVED (derivado)",
    "unavailable": "UNAVAILABLE (sin cobertura/dato oficial)",
    "inconclusive": "INCONCLUSIVE (no concluyente)",
}

KIND_LABELS = {
    "snczi.flood_q100": "Zonas inundables Q100 (SNCZI)",
    "snczi.dph_deslindado": "Dominio publico hidraulico deslindado (SNCZI)",
    "eprtr.facilities": "Instalaciones E-PRTR en el entorno",
    "eprtr.nearest_facility_distance_m": "Distancia a la instalacion E-PRTR mas cercana",
    "csn_radon.status": "Potencial de radon (CSN)",
    "siu.clase_suelo": "Clasificacion del suelo (SIU)",
    "ncse02.hazard": "Peligrosidad sismica NCSE-02",
    "btn.roads": "Infraestructura viaria (BTN)",
    "btn.rail": "Infraestructura ferroviaria (BTN)",
    "btn.roads_nearest_distance_m": "Distancia a la via BTN mas cercana",
    "btn.rail_nearest_distance_m": "Distancia al ferrocarril BTN mas cercano",
}


@dataclass(frozen=True)
class FindingView:
    source: str
    kind: str
    label: str
    status: str
    status_label: str
    value_text: str
    source_crs: str | None
    operational_crs: str | None
    method: str
    provenance_id: str | None
    note: str | None


@dataclass(frozen=True)
class PropertyView:
    property_id: str
    label: str
    refcat: str
    source_crs: str
    operational_crs: str
    findings: tuple[FindingView, ...]


@dataclass(frozen=True)
class ReportViewModel:
    report_id: str
    generated_at: str
    disclaimers: tuple[str, ...]
    sources: tuple[dict[str, Any], ...]
    properties: tuple[PropertyView, ...]
    status_order: tuple[str, ...] = STATUS_ORDER


def value_text(finding: dict) -> str:
    status = finding["status"]
    value = finding.get("value")
    unit = finding.get("unit")
    if status == "observed":
        base = "presente" if finding.get("observed") else "ausente"
        if value is not None and unit == "g":
            return f"{value} g"
        return base
    if status == "derived":
        if value is None:
            return "sin dato en el entorno analizado"
        return f"{value} {unit}" if unit else str(value)
    return "-"


def build_finding_view(finding: dict) -> FindingView:
    status = finding["status"]
    return FindingView(
        source=finding["source"],
        kind=finding["kind"],
        label=KIND_LABELS.get(finding["kind"], finding["kind"]),
        status=status,
        status_label=STATUS_LABELS.get(status, status),
        value_text=value_text(finding),
        source_crs=finding.get("source_crs"),
        operational_crs=finding.get("operational_crs"),
        method=finding.get("method", ""),
        provenance_id=finding.get("provenance_id"),
        note=finding.get("note"),
    )


def build_view_model(manifest: dict) -> ReportViewModel:
    properties = []
    for entry in manifest["properties"]:
        findings = sorted(
            (build_finding_view(f) for f in entry["findings"]),
            key=lambda f: (f.source, f.kind),
        )
        properties.append(
            PropertyView(
                property_id=entry["property_id"],
                label=entry.get("label") or entry["property_id"],
                refcat=entry.get("refcat") or "",
                source_crs=entry["source_crs"],
                operational_crs=entry["operational_crs"],
                findings=tuple(findings),
            )
        )
    source_ids = [source["source"] for source in manifest["sources"]]
    return ReportViewModel(
        report_id=manifest["report_id"],
        generated_at=manifest["generated_at"],
        disclaimers=tuple(required_disclaimers(source_ids)),
        sources=tuple(manifest["sources"]),
        properties=tuple(properties),
    )
