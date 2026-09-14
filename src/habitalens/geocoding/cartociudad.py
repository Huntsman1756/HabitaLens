"""Cliente propio minimo contra la API oficial de CartoCiudad.

No se usa ``pycartociudad`` como dependencia (solo como referencia historica de
parametros). Las coordenadas del geocoder son de direccion, no geometria
catastral, y no se serializan en la salida publica.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from habitalens.cache import CacheStore
from habitalens.config import load_endpoints
from habitalens.net import HttpRequest, HttpSource, Source
from habitalens.property import Address, Territory

# Codigos de provincia INE para territorios forales.
_PROVINCE_TERRITORY = {
    "01": Territory.ARABA,
    "20": Territory.GIPUZKOA,
    "31": Territory.NAVARRA,
    "48": Territory.BIZKAIA,
}


class GeocodingError(RuntimeError):
    """Error de geocodificacion."""


def _load_json(payload: bytes):
    """Carga JSON tolerando respuestas vacias o no-JSON de CartoCiudad."""

    text = payload.decode("utf-8", errors="ignore").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


@dataclass
class GeocodeCandidate:
    label: str
    province: str | None
    province_code: str | None
    municipality: str | None
    municipality_code: str | None
    postal_code: str | None
    refcat: str | None
    candidate_id: str | None = None
    lat: float | None = None
    lng: float | None = None

    @property
    def territory_hint(self) -> Territory | None:
        if self.province_code and self.province_code in _PROVINCE_TERRITORY:
            return _PROVINCE_TERRITORY[self.province_code]
        if self.province_code:
            return Territory.DGC
        return None

    def to_address(self) -> Address:
        return Address(
            label=self.label,
            municipality=self.municipality,
            province=self.province,
            postal_code=self.postal_code,
            refcat_candidate=self.refcat,
            territory_hint=self.territory_hint,
        )


def _candidate_from_mapping(data: dict) -> GeocodeCandidate:
    return GeocodeCandidate(
        label=str(data.get("address") or data.get("label") or "").strip(),
        province=data.get("province"),
        province_code=str(data["provinceCode"]) if data.get("provinceCode") else None,
        municipality=data.get("muni"),
        municipality_code=str(data["muniCode"]) if data.get("muniCode") else None,
        postal_code=str(data["postalCode"]) if data.get("postalCode") else None,
        refcat=(str(data["refCatastral"]).strip() if data.get("refCatastral") else None),
        candidate_id=str(data["id"]) if data.get("id") else None,
        lat=float(data["lat"]) if data.get("lat") is not None else None,
        lng=float(data["lng"]) if data.get("lng") is not None else None,
    )


class CartoCiudadClient:
    def __init__(
        self,
        source: Source | None = None,
        cache: CacheStore | None = None,
        refresh: bool = False,
    ):
        self.endpoints = load_endpoints()["geocoding"]["cartociudad"]
        self._cache = cache or CacheStore()
        self.source: Source = source or HttpSource(cache=self._cache)
        self.refresh = refresh

    @staticmethod
    def _key(kind: str, query: str) -> str:
        digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:16]
        return f"{kind}:{digest}"

    def candidates(self, query: str) -> list[GeocodeCandidate]:
        request = HttpRequest(
            method="GET", url=self.endpoints["candidates"], params=(("q", query),)
        )
        payload = self.source.fetch(
            "cartociudad",
            self._key("candidates", query),
            request,
            refresh=self.refresh,
            ext="json",
            meta={"kind": "candidates", "query": query},
        )
        data = _load_json(payload) or []
        if isinstance(data, dict):
            data = [data]
        return [_candidate_from_mapping(item) for item in data]

    def find(self, query: str) -> GeocodeCandidate | None:
        request = HttpRequest(
            method="GET", url=self.endpoints["find"], params=(("q", query),)
        )
        payload = self.source.fetch(
            "cartociudad",
            self._key("find", query),
            request,
            refresh=self.refresh,
            ext="json",
            meta={"kind": "find", "query": query},
        )
        data = _load_json(payload)
        if isinstance(data, list):
            data = data[0] if data else None
        if not data:
            return None
        return _candidate_from_mapping(data)

    def reverse(self, lon: float, lat: float) -> GeocodeCandidate | None:
        request = HttpRequest(
            method="GET",
            url=self.endpoints["reverse"],
            params=(("lon", str(lon)), ("lat", str(lat))),
        )
        payload = self.source.fetch(
            "cartociudad",
            self._key("reverse", f"{lon},{lat}"),
            request,
            refresh=self.refresh,
            ext="json",
            meta={"kind": "reverse"},
        )
        data = _load_json(payload)
        if not data:
            return None
        if isinstance(data, list):
            data = data[0] if data else None
        return _candidate_from_mapping(data) if data else None

    @staticmethod
    def _normalize(text: str) -> str:
        import unicodedata

        decomposed = unicodedata.normalize("NFKD", str(text).lower())
        return "".join(char for char in decomposed if not unicodedata.combining(char)).strip()

    @classmethod
    def _locality(cls, query: str) -> str:
        parts = [part.strip() for part in re.split(r"[,]", query) if part.strip()]
        return parts[-1] if parts else ""

    @classmethod
    def _locality_ok(cls, query: str, option: GeocodeCandidate) -> bool:
        locality = cls._normalize(cls._locality(query))
        if len(locality) < 3:
            return True
        haystack = cls._normalize(f"{option.municipality or ''} {option.label}")
        return locality in haystack

    def _match_locality(
        self, query: str, options: list[GeocodeCandidate]
    ) -> GeocodeCandidate | None:
        matches = [option for option in options if self._locality_ok(query, option)]
        if not matches:
            return None
        locality = self._normalize(self._locality(query))
        exact = [
            option
            for option in matches
            if self._normalize(option.municipality or "") == locality
        ]
        pool = exact or matches
        with_refcat = [option for option in pool if option.refcat]
        return (with_refcat or pool)[0]

    def geocode(self, query: str) -> GeocodeCandidate | None:
        """Estrategia: desambiguacion estricta por localidad.

        Si la consulta incluye una localidad (p.ej. "Vigo") solo se acepta un
        candidato cuya localidad coincida; asi se evita devolver la parcela de
        otra ciudad cuando la calle es ambigua. Sin coincidencia -> ``None``.
        """

        options = self.candidates(query)
        matched = self._match_locality(query, options) if options else None
        if matched is not None:
            return matched
        found = self.find(query)
        if found is not None and self._locality_ok(query, found):
            return found
        if self._normalize(self._locality(query)):
            return None
        if options:
            with_refcat = [option for option in options if option.refcat]
            if with_refcat:
                return with_refcat[0]
        return found or (options[0] if options else None)
