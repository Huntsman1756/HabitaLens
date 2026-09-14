"""Encaminamiento territorial.

Estrategia (documentada en docs/decisions.md): el territorio devuelto por el
geocoder (codigo de provincia INE) es la senal mas fiable para territorios
forales; el prefijo/patron del refcat se usa como corroboracion o cuando no hay
geocoder. Nunca se inventa un sexto territorio.
"""

from __future__ import annotations

from habitalens.cadastre_providers.registry import provider_id_for_territory
from habitalens.property import Address, Territory, infer_territory


class TerritoryRoutingError(RuntimeError):
    """No se pudo determinar a que proveedor encaminar la consulta."""


class TerritoryRouter:
    def route_refcat(self, refcat: str) -> str:
        territory = infer_territory(refcat)
        if territory is None:
            raise TerritoryRoutingError(
                f"refcat sin patron territorial reconocible: {refcat}"
            )
        return provider_id_for_territory(territory)

    def route_address(self, address: Address) -> str:
        if address.refcat_candidate:
            territory = infer_territory(address.refcat_candidate)
            if territory is not None:
                return provider_id_for_territory(territory)
        if address.territory_hint is not None:
            return provider_id_for_territory(address.territory_hint)
        raise TerritoryRoutingError(f"direccion sin territorio resoluble: {address.label}")

    def route(self, *, refcat: str | None = None, address: Address | None = None) -> str:
        errors: list[str] = []
        if address is not None:
            try:
                return self.route_address(address)
            except TerritoryRoutingError as exc:
                errors.append(str(exc))
        if refcat is not None:
            try:
                return self.route_refcat(refcat)
            except TerritoryRoutingError as exc:
                errors.append(str(exc))
        raise TerritoryRoutingError(
            "encaminamiento imposible: " + " | ".join(errors or ["sin datos"])
        )


__all__ = ["Territory", "TerritoryRouter", "TerritoryRoutingError", "infer_territory"]
