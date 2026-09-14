"""Registro de proveedores disponibles en G0-A."""

from __future__ import annotations

from habitalens.cadastre_providers.araba.provider import ArabaProvider
from habitalens.cadastre_providers.base import CadastreProvider
from habitalens.cadastre_providers.bizkaia.provider import BizkaiaProvider
from habitalens.cadastre_providers.dgc.provider import DgcProvider
from habitalens.cadastre_providers.gipuzkoa.provider import GipuzkoaProvider
from habitalens.cadastre_providers.navarra.provider import NavarraProvider
from habitalens.property import Territory

_PROVIDER_TYPES: dict[str, type[CadastreProvider]] = {
    "dgc": DgcProvider,
    "navarra": NavarraProvider,
    "bizkaia": BizkaiaProvider,
    "gipuzkoa": GipuzkoaProvider,
    "araba": ArabaProvider,
}

_TERRITORY_TO_PROVIDER: dict[Territory, str] = {
    Territory.DGC: "dgc",
    Territory.NAVARRA: "navarra",
    Territory.BIZKAIA: "bizkaia",
    Territory.GIPUZKOA: "gipuzkoa",
    Territory.ARABA: "araba",
}


def provider_ids() -> list[str]:
    return list(_PROVIDER_TYPES)


def get_provider(provider_id: str, **kwargs) -> CadastreProvider:
    try:
        cls = _PROVIDER_TYPES[provider_id]
    except KeyError as exc:
        raise KeyError(f"proveedor desconocido: {provider_id}") from exc
    return cls(**kwargs)


def provider_id_for_territory(territory: Territory) -> str:
    return _TERRITORY_TO_PROVIDER[territory]


def all_providers(**kwargs) -> dict[str, CadastreProvider]:
    return {pid: get_provider(pid, **kwargs) for pid in provider_ids()}
