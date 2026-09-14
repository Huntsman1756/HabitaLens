"""Manifest de procedencia: fuente unica de verdad del informe (G0-D)."""

from __future__ import annotations

import json

from habitalens import DISCLAIMER
from habitalens.evidence.models import PropertyEvidence
from habitalens.report.disclaimers import _GENERIC_ATTRIBUTION, ATTRIBUTIONS

SCHEMA_VERSION = "1"
TEMPLATE_VERSION = "1"

#: Campos que nunca deben aparecer en el manifest (guarda de geometria).
FORBIDDEN_MANIFEST_KEYS = (
    "geometry",
    "geom",
    "coordinates",
    "coords",
    "poslist",
    "wkt",
    "geojson",
    "shape",
    "bbox",
)


def property_entry(meta: dict, evidence: PropertyEvidence) -> dict:
    return {
        "property_id": meta.get("id", evidence.property_id),
        "label": meta.get("label"),
        "provider_id": meta.get("provider_id"),
        "refcat": meta.get("refcat"),
        "context": meta.get("context"),
        "source_crs": evidence.source_crs,
        "operational_crs": evidence.operational_crs,
        "findings": [finding.model_dump(mode="json") for finding in evidence.findings],
    }


def _sources_from_entries(entries: list[dict]) -> list[dict]:
    versions: dict[str, str] = {}
    for entry in entries:
        for finding in entry["findings"]:
            versions.setdefault(finding["source"], finding["source_version"])
    return [
        {
            "source": source,
            "source_version": versions[source],
            "attribution": ATTRIBUTIONS.get(source, _GENERIC_ATTRIBUTION),
        }
        for source in sorted(versions)
    ]


def build_manifest(
    *,
    report_id: str,
    entries: list[dict],
    generated_at: str,
    corpus_version: str = "g0c",
    template_version: str = TEMPLATE_VERSION,
) -> dict:
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "report_id": report_id,
        "generated_at": generated_at,
        "corpus_version": corpus_version,
        "template_version": template_version,
        "disclaimer": DISCLAIMER,
        "sources": _sources_from_entries(entries),
        "properties": entries,
        "artifacts": {},
    }
    return manifest


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2, separators=(",", ": "))


def assert_no_geometry_keys(data: dict) -> None:
    def walk(node) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                lowered = str(key).lower()
                if any(token in lowered for token in FORBIDDEN_MANIFEST_KEYS):
                    raise ValueError(f"clave de geometria en manifest: {key}")
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(data)
