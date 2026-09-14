"""Adaptadores de proveedores catastrales (G0-A).

Cada proveedor expone el contrato :class:`CadastreProvider`. Ningun proveedor
implementa geocodificacion: la composicion direccion -> CartoCiudad ->
TerritoryRouter -> CadastreProvider vive en ``habitalens.resolver``.
"""

from __future__ import annotations

from habitalens.cadastre_providers.base import CadastreProvider
from habitalens.cadastre_providers.registry import (
    all_providers,
    get_provider,
    provider_ids,
)

__all__ = ["CadastreProvider", "all_providers", "get_provider", "provider_ids"]
