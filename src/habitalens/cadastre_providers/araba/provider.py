"""Adaptador Araba/Alava: GeoServer INSPIRE WFS CP/BU + ATOM.

Verificado: filtro ad-hoc FES sobre ``INSPIRE_CP:nationalCadastralReference``.
No existe servicio INSPIRE AD para Araba.
"""

from __future__ import annotations

from habitalens.cadastre_providers.base import CadastreProvider
from habitalens.cadastre_providers.wfs import equals_filter, get_feature_request
from habitalens.net import HttpRequest
from habitalens.property import RefCat, Territory


class ArabaProvider(CadastreProvider):
    provider_id = "araba"
    territory = Territory.ARABA

    def _get_parcel_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        value = RefCat.parse(refcat, self.territory).normalized
        filter_xml = equals_filter(
            self.config["filter"]["parcel_property"],
            value,
            prefixes={"INSPIRE_CP": "INSPIRE_CP"},
        )
        request = get_feature_request(
            self.config["wfs"]["parcel"],
            self.config["types"]["parcel"],
            filter_xml=filter_xml,
        )
        return self._fetch_raw("parcel", refcat, request), request

    def _get_buildings_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        request = self._bbox_request(
            self.config["wfs"]["building"], self.config["types"]["building"], refcat
        )
        return self._fetch_raw("building", refcat, request), request
