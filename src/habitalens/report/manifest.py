"""Manifest de procedencia: fuente unica de verdad del informe (G0-D)."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    field_validator,
    model_validator,
)

from habitalens import DISCLAIMER
from habitalens.evidence.models import PropertyEvidence
from habitalens.report.disclaimers import _GENERIC_ATTRIBUTION, ATTRIBUTIONS
from habitalens.report.guard import assert_no_score

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


Text = Annotated[str, StringConstraints(min_length=1, pattern=r"\S")]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]


class _ManifestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False, hide_input_in_errors=True)


class ManifestFinding(_ManifestModel):
    property_id: Text
    source: Text
    source_version: Text
    kind: Text
    status: Literal["observed", "derived", "unavailable", "inconclusive"]
    observed: bool | None = None
    value: float | str | None = None
    unit: Text | None = None
    source_crs: Text | None = None
    operational_crs: Text | None = None
    method: Text
    inputs: list[Text] | tuple[Text, ...] = ()
    provenance_id: Text | None = None
    retrieved_at: Text
    note: str | None = None

    @field_validator("retrieved_at")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("timestamp must include a timezone")
        return value

    @model_validator(mode="after")
    def consistent_status(self) -> Self:
        if not self.kind.startswith(f"{self.source}."):
            raise ValueError("finding kind must belong to its source")
        if self.status == "observed" and self.observed is None:
            raise ValueError("observed findings require an explicit boolean")
        if self.status != "observed" and self.observed is not None:
            raise ValueError("only observed findings can declare observation")
        if self.status in {"unavailable", "inconclusive"} and self.value is not None:
            raise ValueError("unavailable/inconclusive findings cannot declare a value")
        return self


class ManifestProperty(_ManifestModel):
    property_id: Text
    label: str | None = None
    provider_id: Text | None = None
    refcat: str | None = None
    context: str | None = None
    source_crs: Text
    operational_crs: Text
    findings: list[ManifestFinding]

    @model_validator(mode="after")
    def consistent_findings(self) -> Self:
        seen = set()
        for finding in self.findings:
            if finding.property_id != self.property_id:
                raise ValueError("finding property identity does not match its parent")
            if finding.operational_crs not in {None, self.operational_crs}:
                raise ValueError("finding operational CRS does not match its parent")
            key = (finding.source, finding.kind)
            if key in seen:
                raise ValueError("duplicate finding")
            seen.add(key)
        return self


class ManifestSource(_ManifestModel):
    source: Text
    source_version: Text
    attribution: Text


class HtmlArtifact(_ManifestModel):
    sha256: Digest


class PdfArtifact(_ManifestModel):
    canonical_sha256: Digest
    pages: int = Field(ge=1)
    engine: Text
    font_stack: Text


class ManifestArtifacts(_ManifestModel):
    html: HtmlArtifact | None = None
    pdf: PdfArtifact | None = None

    @model_validator(mode="after")
    def complete_pair(self) -> Self:
        if (self.html is None) != (self.pdf is None):
            raise ValueError("artifact metadata must contain both HTML and PDF")
        return self


class ReportManifest(_ManifestModel):
    schema_version: Literal["1"]
    template_version: Literal["1"]
    report_id: Text
    generated_at: Text
    corpus_version: Text
    disclaimer: Text
    sources: list[ManifestSource]
    properties: list[ManifestProperty]
    artifacts: ManifestArtifacts

    @field_validator("generated_at")
    @classmethod
    def valid_timestamp(cls, value: str) -> str:
        return ManifestFinding.valid_timestamp(value)

    @field_validator("disclaimer")
    @classmethod
    def mandatory_disclaimer(cls, value: str) -> str:
        if " ".join(DISCLAIMER.split()) not in " ".join(value.split()):
            raise ValueError("manifest must retain the mandatory disclaimer")
        return value

    @model_validator(mode="after")
    def consistent_inventory(self) -> Self:
        versions = {source.source: source.source_version for source in self.sources}
        if len(versions) != len(self.sources):
            raise ValueError("duplicate source inventory entry")
        if len({entry.property_id for entry in self.properties}) != len(self.properties):
            raise ValueError("duplicate property identity")
        used = set()
        for entry in self.properties:
            for finding in entry.findings:
                if versions.get(finding.source) != finding.source_version:
                    raise ValueError("finding source/version does not match inventory")
                used.add(finding.source)
        if used != set(versions):
            raise ValueError("source inventory must exactly match findings")
        return self


def validate_manifest(manifest: dict) -> None:
    assert_no_geometry_keys(manifest)
    assert_no_score(canonical_json(manifest))
    ReportManifest.model_validate(manifest)
    assert_no_geometry_text(canonical_json(manifest))


def assert_no_geometry_text(text: str) -> None:
    if re.search(
        r"\b(?:POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|GEOMETRYCOLLECTION)\s*(?:Z|M|ZM)?\s*\("
        r"|<(?:\w+:)?(?:posList|coordinates|MultiSurface)\b",
        text,
        re.IGNORECASE,
    ):
        raise ValueError("geometry content is not permitted in reports")


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
        ManifestProperty.model_validate(entry)
        for finding in entry["findings"]:
            previous = versions.setdefault(finding["source"], finding["source_version"])
            if previous != finding["source_version"]:
                raise ValueError("multiple versions for the same source")
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
    validate_manifest(manifest)
    return manifest


def canonical_json(data: dict) -> str:
    return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=2, separators=(",", ": "), allow_nan=False)


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
