"""Resolucion de propiedad: direccion/refcat -> parcela + edificios.

Composicion: direccion -> CartoCiudad -> TerritoryRouter -> CadastreProvider.
El geocoder no accede al catastro y los proveedores no geocodifican.
"""

from __future__ import annotations

import hashlib

from habitalens.cadastre_providers.base import CadastreProvider
from habitalens.cadastre_providers.registry import get_provider
from habitalens.geocoding import CartoCiudadClient, GeocodeCandidate
from habitalens.property import Address, Property, infer_territory
from habitalens.resolver.territory_router import TerritoryRouter


class ResolverError(RuntimeError):
    """No se pudo resolver la consulta."""


class PropertyResolver:
    def __init__(
        self,
        providers: dict[str, CadastreProvider] | None = None,
        geocoder: CartoCiudadClient | None = None,
        router: TerritoryRouter | None = None,
    ):
        self.providers = providers or {}
        self.geocoder = geocoder or CartoCiudadClient()
        self.router = router or TerritoryRouter()

    def _provider(self, provider_id: str) -> CadastreProvider:
        if provider_id in self.providers:
            return self.providers[provider_id]
        provider = get_provider(provider_id)
        self.providers[provider_id] = provider
        return provider

    def resolve(self, reference: str) -> Property:
        if infer_territory(reference) is not None:
            return self.resolve_refcat(reference)
        return self.resolve_address(reference)

    def resolve_refcat(self, refcat: str) -> Property:
        provider_id = self.router.route_refcat(refcat)
        return self._build(provider_id, refcat, address=None)

    def resolve_address(self, query: str) -> Property:
        candidate: GeocodeCandidate | None = self.geocoder.geocode(query)
        if candidate is None:
            raise ResolverError(f"CartoCiudad no devolvio candidatos para: {query}")
        address: Address = candidate.to_address()
        provider_id = self.router.route_address(address)
        provider = self._provider(provider_id)
        # Estrategia de adquisicion: la localizacion del geocoder (coordenadas)
        # es mas fiable que el refcat para territorios forales. Se intenta por
        # coordenadas y, si el proveedor no lo soporta, por refcat.
        parcel = None
        if candidate.lat is not None and candidate.lng is not None:
            try:
                parcel = provider.get_parcel_near(candidate.lat, candidate.lng)
            except NotImplementedError:
                parcel = None
        if parcel is None:
            refcat = candidate.refcat
            if not refcat:
                raise ResolverError(
                    "INCONCLUSIVE: CartoCiudad no devolvio referencia catastral ni "
                    f"localizacion util para {query!r}; ver docs/decisions.md"
                )
            parcel = provider.get_parcel(refcat)
        buildings = tuple(provider.get_buildings(parcel.refcat))
        property_id = hashlib.sha256(
            f"{provider_id}:{parcel.refcat}".encode()
        ).hexdigest()[:16]
        return Property(
            property_id=property_id,
            territory=parcel.territory,
            parcel=parcel,
            buildings=buildings,
            address=address,
        )

    def _build(self, provider_id: str, refcat: str, address: Address | None) -> Property:
        provider = self._provider(provider_id)
        parcel = provider.get_parcel(refcat)
        buildings = tuple(provider.get_buildings(refcat))
        property_id = hashlib.sha256(
            f"{provider_id}:{parcel.refcat}".encode()
        ).hexdigest()[:16]
        return Property(
            property_id=property_id,
            territory=parcel.territory,
            parcel=parcel,
            buildings=buildings,
            address=address,
        )
