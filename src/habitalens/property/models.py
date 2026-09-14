"""Modelos publicos con guarda de geometria.

Los modelos son deliberadamente "planos": solo contienen atributos alfanumericos
y numericos derivados. Ninguna instancia contiene coordenadas, posLists, WKT,
GeoJSON ni ninguna estructura de la que pueda reconstruirse la geometria catastral.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Tokens que no pueden aparecer como campos publicos: si aparecen, la guarda de
# geometria del test falla. La geometria se mantiene fuera de los modelos.
FORBIDDEN_FIELD_TOKENS = (
    "geom",
    "geometry",
    "coordinate",
    "coords",
    "coord",
    "wkt",
    "geojson",
    "poslist",
    "shape",
    "polygon",
    "multisurface",
    "centroid",
    "bbox",
    "extent",
)


class _PublicModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, validate_assignment=True)


class Territory(StrEnum):
    """Territorios cubiertos por los cinco proveedores de G0-A."""

    DGC = "dgc"
    NAVARRA = "navarra"
    BIZKAIA = "bizkaia"
    GIPUZKOA = "gipuzkoa"
    ARABA = "araba"


_BIZKAIA_RE = re.compile(r"^\d{2}\.\d{3}\.\d{4}\.\d{5}$")
_GIPUZKOA_DASH_RE = re.compile(r"^\d{3}-\d{7}-\d{4}$")
_GIPUZKOA_LABEL_RE = re.compile(r"^\d{7}$")
_ALAVA_RE = re.compile(r"^\d{8}$")
_NAVARRA_RE = re.compile(r"^\d{9}$")
_DGC_RE = re.compile(r"^\d{7}[A-Z0-9]{2}\d{4}[A-Z0-9]$")


class RefCat(_PublicModel):
    """Referencia catastral como valor, sin geometria."""

    raw: str
    normalized: str
    territory: Territory | None = None

    @field_validator("raw", "normalized")
    @classmethod
    def _non_empty(cls, value: str) -> str:
        if value is None or not str(value).strip():
            raise ValueError("refcat vacia")
        return str(value).strip()

    @classmethod
    def parse(cls, raw: str, territory: Territory | None = None) -> RefCat:
        cleaned = str(raw).strip()
        normalized = cleaned.upper().replace(" ", "")
        inferred = territory or infer_territory(normalized)
        return cls(raw=cleaned, normalized=normalized, territory=inferred)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return self.normalized


def infer_territory(refcat: str) -> Territory | None:
    """Infiere el territorio a partir del formato del refcat.

    Es una heuristica: la decision fiable debe venir del geocoder o de una
    indicacion explicita. Se documenta en docs/decisions.md.
    """

    value = refcat.strip().upper()
    if _BIZKAIA_RE.match(value):
        return Territory.BIZKAIA
    if _GIPUZKOA_DASH_RE.match(value) or _GIPUZKOA_LABEL_RE.match(value):
        return Territory.GIPUZKOA
    if _ALAVA_RE.match(value):
        return Territory.ARABA
    if _NAVARRA_RE.match(value):
        return Territory.NAVARRA
    if _DGC_RE.match(value):
        return Territory.DGC
    return None


class Address(_PublicModel):
    """Direccion normalizada devuelta por CartoCiudad (sin geometria persistida)."""

    label: str
    municipality: str | None = None
    province: str | None = None
    postal_code: str | None = None
    refcat_candidate: str | None = None
    territory_hint: Territory | None = None


class Parcel(_PublicModel):
    """Parcela catastral normalizada, sin geometria publica."""

    refcat: str
    provider: str
    territory: Territory
    area_m2: float | None = None
    land_use: str | None = None
    municipality: str | None = None
    crs: str
    source_version: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provenance_id: str

    @field_validator("refcat")
    @classmethod
    def _refcat_non_empty(cls, value: str) -> str:
        if not str(value).strip():
            raise ValueError("refcat vacia")
        return str(value).strip()


class Building(_PublicModel):
    """Edificio asociado a una parcela, sin geometria publica."""

    building_id: str
    refcat: str
    provider: str
    territory: Territory
    area_m2: float | None = None
    crs: str
    source_version: str
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    provenance_id: str


class Property(_PublicModel):
    """Agregado minimo parcela + edificios (y direccion si procede)."""

    property_id: str
    territory: Territory
    parcel: Parcel
    buildings: tuple[Building, ...] = ()
    address: Address | None = None


class TerritoryMask(_PublicModel):
    """Cobertura declarada por un proveedor. Sin geometria: solo codigos."""

    territory: Territory
    level: str
    codes: tuple[str, ...] = ()
    description: str | None = None

    def covers(self, refcat: str) -> bool:
        return infer_territory(refcat) == self.territory
