"""Contrato `CadastreProvider` y logica comun de los adaptadores.

Contrato minimo::

    resolve_reference(refcat) -> Parcel
    get_parcel(refcat) -> Parcel
    get_buildings(refcat) -> list[Building]
    source_version() -> str
    coverage() -> TerritoryMask

Ninguna implementacion expone `resolve_address()`: la geocodificacion es
responsabilidad exclusiva de CartoCiudad + TerritoryRouter.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.cadastre_providers.inspire import (
    ParsedBuilding,
    ParsedParcel,
    extract_version,
    parse_building_features,
    parse_parcel_features,
)
from habitalens.cadastre_providers.wfs import capabilities_request
from habitalens.config import provider_config
from habitalens.licensing import LicenseDeclaration, load_license
from habitalens.net import HttpRequest, HttpSource, Source
from habitalens.property import Building, Parcel, RefCat, Territory, TerritoryMask
from habitalens.provenance import ProvenanceRecord, ProvenanceRecorder


class ProviderError(RuntimeError):
    """Error generico de un proveedor catastral."""


class ParcelNotFoundError(ProviderError):
    """El proveedor no devolvio la parcela solicitada."""


class CadastreProvider(ABC):
    provider_id: str = ""
    territory: Territory

    def __init__(
        self,
        source: Source | None = None,
        cache: CacheStore | None = None,
        provenance: ProvenanceRecorder | None = None,
        refresh: bool = False,
        persist: bool = True,
    ):
        if not self.provider_id:
            raise ProviderError(f"{type(self).__name__} no define provider_id")
        module_file = inspect.getfile(type(self))
        self.package_dir = Path(module_file).parent
        # Guarda de licencias: obligatoria antes de cualquier operacion.
        self.license: LicenseDeclaration = load_license(self.package_dir)
        self._cache = cache or getattr(source, "cache", None) or CacheStore()
        self.source: Source = source or HttpSource(cache=self._cache)
        self.provenance = provenance or ProvenanceRecorder(self._cache.root)
        self.refresh = refresh
        self.persist = persist
        self.config = provider_config(self.provider_id)
        self._declared_source_version = self.config["source_version"]
        self._source_version: str | None = None
        self._parcel_geometry_cache: dict[str, object] = {}
        self._last_parcel_content: bytes | None = None

    # -- contrato publico -------------------------------------------------
    def resolve_reference(self, refcat: str) -> Parcel:
        normalized = RefCat.parse(refcat, self.territory).normalized
        return self.get_parcel(normalized)

    def get_parcel(self, refcat: str) -> Parcel:
        parsed_list, content, request = self._fetch_parcels(refcat)
        return self._finalize_parcel(refcat, parsed_list, content, request)

    def get_parcel_near(self, lat: float, lon: float) -> Parcel:
        """Localiza la parcela por coordenadas (localizacion del geocoder).

        Es la estrategia de adquisicion cuando el refcat no es resoluble en el
        proveedor. Por defecto no esta implementada; DGC la implementa via BBOX.
        """

        content, request = self._get_parcel_near_content(lat, lon)
        parsed_list = parse_parcel_features(content, self._parcel_tokens())
        for item in parsed_list:
            self._parcel_geometry_cache[item.refcat] = (item.geometry, item.crs)
        parsed_list = self._order_by_proximity(parsed_list, lon, lat)
        if not parsed_list:
            raise ParcelNotFoundError(
                f"{self.provider_id}: ninguna parcela contiene la localizacion "
                f"({lat}, {lon})"
            )
        return self._finalize_parcel(None, parsed_list, content, request)

    @staticmethod
    def _order_by_proximity(
        parsed_list: list[ParsedParcel], lon: float, lat: float
    ) -> list[ParsedParcel]:
        """Prioriza la parcela que contiene el punto (geometria normalizada lon/lat)."""

        try:
            from shapely.geometry import Point

            crs = next((item.crs for item in parsed_list if item.geometry), "EPSG:4326")
            if crs.split(":")[-1] not in {"4326", "4258", "4230"}:
                from pyproj import Transformer

                x, y = Transformer.from_crs(
                    "EPSG:4326", crs, always_xy=True
                ).transform(lon, lat)
                point = Point(x, y)
            else:
                point = Point(lon, lat)
        except ImportError:  # pragma: no cover
            return parsed_list
        inside = [
            item
            for item in parsed_list
            if item.geometry is not None and item.geometry.covers(point)
        ]
        if not inside:
            return []
        inside.sort(key=lambda item: item.geometry.area)
        outside = [item for item in parsed_list if item not in inside]
        return inside + outside

    def _get_parcel_near_content(self, lat: float, lon: float) -> tuple[bytes, HttpRequest]:
        """Peticion WFS por BBOX alrededor de la localizacion (lat, lon WGS84).

        Orden de eje: geograficas en lat,lon (INSPIRE/MapServer/ArcGIS);
        proyectadas se transforman a la CRS del servicio solo para el BBOX.
        """

        wfs = self.config.get("wfs", {})
        types = self.config.get("types", {})
        if not wfs.get("parcel") or not types.get("parcel"):
            raise NotImplementedError(
                f"{self.provider_id}: get_parcel_near no disponible"
            )
        crs = self.config.get("crs", "EPSG:4326")
        urn = self._epsg_urn(crs)
        bbox = self._near_bbox(lat, lon, crs)
        from habitalens.cadastre_providers.wfs import get_feature_request

        request = get_feature_request(
            wfs["parcel"], types["parcel"], bbox=bbox, count=200, srs_name=urn
        )
        key = f"near:{lat:.5f},{lon:.5f}"
        return self._fetch_raw("parcel-near", key, request), request

    @staticmethod
    def _epsg_urn(crs: str) -> str:
        return f"urn:ogc:def:crs:EPSG::{crs.split(':')[-1]}"

    @classmethod
    def _near_bbox(cls, lat: float, lon: float, crs: str) -> str:
        epsg = crs.split(":")[-1]
        urn = cls._epsg_urn(crs)
        if epsg in {"4326", "4258", "4230"}:
            delta = 0.002
            return f"{lat - delta},{lon - delta},{lat + delta},{lon + delta},{urn}"
        from pyproj import Transformer

        transformer = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        x, y = transformer.transform(lon, lat)
        delta = 250.0
        return f"{x - delta},{y - delta},{x + delta},{y + delta},{urn}"

    def _finalize_parcel(
        self,
        refcat: str | None,
        parsed_list: list[ParsedParcel],
        content: bytes,
        request: HttpRequest,
    ) -> Parcel:
        if not parsed_list:
            raise ParcelNotFoundError(
                f"{self.provider_id}: sin parcela para {refcat or 'localizacion'}"
            )
        target = self._select_parcel(parsed_list, refcat) if refcat else parsed_list[0]
        cache_path = self._persist_geometry(target.refcat, parsed_list)
        provenance = self._record(
            kind="parcel",
            refcat=target.refcat,
            request=request,
            content=content,
            crs=target.crs,
            cache_path=cache_path,
        )
        return Parcel(
            refcat=target.refcat,
            provider=self.provider_id,
            territory=self.territory,
            area_m2=target.area_m2,
            land_use=target.land_use,
            crs=target.crs,
            source_version=self.source_version(),
            provenance_id=provenance.provenance_id,
        )

    def get_buildings(self, refcat: str) -> list[Building]:
        parsed_list, content, request = self._fetch_buildings(refcat)
        cache_path = self._persist_geometry(refcat, parsed_list, kind="building")
        provenance = self._record(
            kind="building",
            refcat=refcat,
            request=request,
            content=content,
            crs=parsed_list[0].crs if parsed_list else self.config["crs"],
            cache_path=cache_path,
        )
        return [
            Building(
                building_id=item.building_id,
                refcat=item.refcat or RefCat.parse(refcat, self.territory).normalized,
                provider=self.provider_id,
                territory=self.territory,
                area_m2=item.area_m2,
                crs=item.crs,
                source_version=self.source_version(),
                provenance_id=provenance.provenance_id,
            )
            for item in parsed_list
        ]

    def source_version(self) -> str:
        if self._source_version is not None:
            return self._source_version
        request = capabilities_request(self.config["wfs"]["parcel"])
        try:
            content = self.source.fetch(
                self.provider_id,
                "capabilities",
                request,
                refresh=self.refresh,
                ext="xml",
                meta={"provider": self.provider_id, "kind": "capabilities"},
            )
        except (KeyError, RuntimeError):
            self._source_version = self._declared_source_version
            return self._source_version
        observed = extract_version(content)
        self._source_version = observed or self._declared_source_version
        return self._source_version

    def coverage(self) -> TerritoryMask:
        coverage = self.config.get("coverage", {})
        return TerritoryMask(
            territory=self.territory,
            level=coverage.get("level", "unknown"),
            codes=tuple(coverage.get("codes", ())),
            description=coverage.get("description"),
        )

    @classmethod
    def provider_name(cls) -> str:
        return cls.provider_id

    # -- a implementar por cada adaptador --------------------------------
    @abstractmethod
    def _get_parcel_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        ...

    @abstractmethod
    def _get_buildings_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        ...

    # -- helpers compartidos ---------------------------------------------
    def _fetch_raw(
        self, kind: str, key: str, request: HttpRequest, *, ext: str = "xml"
    ) -> bytes:
        return self.source.fetch(
            self.provider_id,
            f"{kind}:{key}",
            request,
            refresh=self.refresh,
            ext=ext,
            meta={"provider": self.provider_id, "kind": kind},
        )

    def _bbox_request(self, url: str, type_name: str, refcat: str, count: int = 200) -> HttpRequest:
        bounds = self._parcel_bounds(refcat)
        if bounds is None:
            raise ProviderError(
                f"{self.provider_id}: sin geometria de parcela para calcular bbox "
                f"de edificios ({refcat})"
            )
        minx, miny, maxx, maxy, crs = bounds
        urn = self._epsg_urn(crs)
        style = self.config.get("bbox_crs_style_buildings", "urn")
        crs_token = urn if style == "urn" else crs
        axis = self.config.get("bbox_axis_buildings", "latlon")
        geographic = crs.split(":")[-1] in {"4326", "4258", "4230"}
        from habitalens.cadastre_providers.wfs import bbox_value, get_feature_request

        if geographic and axis == "latlon":
            bbox = bbox_value(miny, minx, maxy, maxx, crs_token)
        else:
            bbox = bbox_value(minx, miny, maxx, maxy, crs_token)
        return get_feature_request(url, type_name, bbox=bbox, count=count, srs_name=crs_token)

    def _fetch_parcels(
        self, refcat: str
    ) -> tuple[list[ParsedParcel], bytes, HttpRequest]:
        content, request = self._get_parcel_content(refcat)
        self._last_parcel_content = content
        parsed = parse_parcel_features(content, self._parcel_tokens())
        for item in parsed:
            self._parcel_geometry_cache[item.refcat] = (item.geometry, item.crs)
        return parsed, content, request

    def _fetch_buildings(
        self, refcat: str
    ) -> tuple[list[ParsedBuilding], bytes, HttpRequest]:
        content, request = self._get_buildings_content(refcat)
        return parse_building_features(content, self._building_tokens()), content, request

    def _parcel_tokens(self) -> tuple[str, ...]:
        tokens = self.config.get("parcel_feature_tokens")
        return tuple(tokens) if tokens else ("CadastralParcel",)

    def _building_tokens(self) -> tuple[str, ...]:
        tokens = self.config.get("building_feature_tokens")
        return tuple(tokens) if tokens else ("Building",)

    def _select_parcel(
        self, parsed: list[ParsedParcel], refcat: str | None
    ) -> ParsedParcel:
        if refcat is None:
            return parsed[0]
        normalized = RefCat.parse(refcat, self.territory).normalized
        for item in parsed:
            if item.refcat.strip().upper() == normalized:
                return item
        # Nunca devolver una parcela distinta a la solicitada.
        raise ParcelNotFoundError(
            f"{self.provider_id}: refcat {refcat} no encontrado entre "
            f"{len(parsed)} parcelas"
        )

    def _parcel_geometry(self, refcat: str):
        if refcat not in self._parcel_geometry_cache:
            self._fetch_parcels(refcat)
        return self._parcel_geometry_cache.get(refcat, (None, self.config["crs"]))

    def _parcel_bounds(self, refcat: str) -> tuple[float, float, float, float, str] | None:
        geometry, crs = self._parcel_geometry(refcat)
        if geometry is None:
            return None
        minx, miny, maxx, maxy = geometry.bounds
        return minx, miny, maxx, maxy, crs

    def _persist_geometry(self, refcat: str, parsed: list, kind: str = "parcel") -> Path | None:
        if not self.persist:
            return None
        items = [(item.refcat, item.geometry, item.crs) for item in parsed if item.geometry]
        if not items:
            return None
        try:
            import geopandas as gpd
        except ImportError:  # pragma: no cover - dependencia declarada
            return None
        refcats = [item[0] for item in items]
        geometries = [item[1] for item in items]
        crs = items[0][2]
        frame = gpd.GeoDataFrame({"refcat": refcats}, geometry=geometries, crs=crs)
        return self._cache.write_geoparquet(
            self.provider_id,
            f"{kind}:{refcat}",
            frame,
            meta={
                "provider": self.provider_id,
                "source_version": self.source_version(),
                "crs": crs,
                "kind": kind,
            },
        )

    def _record(
        self,
        *,
        kind: str,
        refcat: str,
        request: HttpRequest,
        content: bytes,
        crs: str,
        cache_path: Path | None = None,
    ) -> ProvenanceRecord:
        return self.provenance.record(
            provider=self.provider_id,
            territory=self.territory.value,
            kind=kind,
            source_version=self.source_version(),
            crs=crs,
            refcat=refcat,
            url=request.url,
            request_params=request.params,
            offline=self.source.offline,
            cache_path=str(cache_path) if cache_path else None,
            content=content,
        )
