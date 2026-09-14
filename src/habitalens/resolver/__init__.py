"""Resolucion de direccion/refcat a parcela + edificios."""

from __future__ import annotations

from habitalens.resolver.property_resolver import PropertyResolver, ResolverError
from habitalens.resolver.territory_router import TerritoryRouter, TerritoryRoutingError

__all__ = [
    "PropertyResolver",
    "ResolverError",
    "TerritoryRouter",
    "TerritoryRoutingError",
]
