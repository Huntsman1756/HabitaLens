"""Registro de proveedores CEE por region (P1.B)."""

from __future__ import annotations

from habitalens.cee.base import CeeLookupResult, CeeProvider, CeeStatus
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
    """Consulta la referencia en todas las regiones soportadas.

    El fallo de un registro regional no debe tumbar las demas consultas:
    se reporta como INCONCLUSIVE con la causa.
    """

    results = []
    for region in cee_regions():
        try:
            results.append(get_cee_provider(region, **kwargs).lookup(refcat))
        except Exception as exc:
            results.append(
                CeeLookupResult(
                    refcat=refcat,
                    region=region,
                    status=CeeStatus.INCONCLUSIVE,
                    note=f"{type(exc).__name__}: {exc}",
                )
            )
    return results
