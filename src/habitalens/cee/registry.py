"""Registro de proveedores CEE por region (P1.B)."""

from __future__ import annotations

from habitalens.cee.base import CeeLookupResult, CeeProvider
from habitalens.cee.catalunya.provider import CatalunyaCeeProvider

_CEE_TYPES: dict[str, type[CeeProvider]] = {
    "catalunya": CatalunyaCeeProvider,
}


def cee_regions() -> list[str]:
    return list(_CEE_TYPES)


def get_cee_provider(region: str, **kwargs) -> CeeProvider:
    try:
        provider_type = _CEE_TYPES[region]
    except KeyError as exc:
        raise KeyError(f"region CEE no soportada: {region}") from exc
    return provider_type(**kwargs)


def lookup_any(refcat: str, **kwargs) -> list[CeeLookupResult]:
    """Consulta la referencia en todas las regiones soportadas."""

    return [get_cee_provider(region, **kwargs).lookup(refcat) for region in cee_regions()]
