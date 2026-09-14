"""Adaptador Gipuzkoa: WFS INSPIRE CP/BU/AD (MapServer) + ATOM.

Verificado: filtro ad-hoc FES sobre ``cp:nationalCadastralReference``. En
Gipuzkoa el valor del refcat nacional es el label de 7 digitos; si se recibe el
localId con guiones (``069-8594149-3232``) se reintenta con el label.
"""

from __future__ import annotations

from habitalens.cadastre_providers.base import CadastreProvider
from habitalens.cadastre_providers.inspire import parse_parcel_features
from habitalens.cadastre_providers.wfs import equals_filter, get_feature_request
from habitalens.net import HttpRequest
from habitalens.property import RefCat, Territory

_CP_PREFIXES = {"cp": "http://inspire.ec.europa.eu/schemas/cp/4.0"}


class GipuzkoaProvider(CadastreProvider):
    provider_id = "gipuzkoa"
    territory = Territory.GIPUZKOA

    def _candidate_refcats(self, refcat: str) -> list[str]:
        normalized = RefCat.parse(refcat, self.territory).normalized
        candidates = [normalized]
        if "-" in normalized:
            label = normalized.split("-")[1]
            if label not in candidates:
                candidates.append(label)
        return candidates

    def _request_for(self, value: str) -> HttpRequest:
        filter_xml = equals_filter(
            self.config["filter"]["parcel_property"], value, prefixes=_CP_PREFIXES
        )
        return get_feature_request(
            self.config["wfs"]["parcel"],
            self.config["types"]["parcel"],
            filter_xml=filter_xml,
        )

    def _get_parcel_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        content = b""
        request = self._request_for(refcat)
        for index, value in enumerate(self._candidate_refcats(refcat)):
            key = refcat if index == 0 else f"{refcat}:{value}"
            request = self._request_for(value)
            content = self._fetch_raw("parcel", key, request)
            if parse_parcel_features(content):
                return content, request
        return content, request

    def _get_buildings_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        request = self._bbox_request(
            self.config["wfs"]["building"], self.config["types"]["building"], refcat
        )
        return self._fetch_raw("building", refcat, request), request
