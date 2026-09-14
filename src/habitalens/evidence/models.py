"""Modelos publicos de evidencia. Sin geometria (guarda de no exposicion)."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FindingStatus(StrEnum):
    """Taxonomia de hallazgos, sin ambiguedad.

    OBSERVED: la fuente contiene una entidad que intersecta/aplica.
    DERIVED: valor calculado a partir de entidades observadas.
    UNAVAILABLE: fuente disponible pero sin cobertura/dato aplicable al lugar.
    INCONCLUSIVE: la fuente no pudo comprobarse de forma suficiente.
    """

    OBSERVED = "observed"
    DERIVED = "derived"
    UNAVAILABLE = "unavailable"
    INCONCLUSIVE = "inconclusive"


class _EvidenceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_assignment=True)


class EvidenceFinding(_EvidenceModel):
    property_id: str
    source: str
    source_version: str
    kind: str
    status: FindingStatus
    observed: bool | None = None
    value: float | str | None = None
    unit: str | None = None
    source_crs: str | None = None
    operational_crs: str | None = None
    method: str
    inputs: tuple[str, ...] = ()
    provenance_id: str | None = None
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    note: str | None = None

    @field_validator("property_id", "source", "kind", "method")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("campo obligatorio vacio")
        return str(value).strip()


class PropertyEvidence(_EvidenceModel):
    property_id: str
    source_crs: str
    operational_crs: str
    findings: tuple[EvidenceFinding, ...] = ()

    def by_status(self, status: FindingStatus) -> tuple[EvidenceFinding, ...]:
        return tuple(f for f in self.findings if f.status == status)
