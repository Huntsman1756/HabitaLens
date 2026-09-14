"""Adaptador Navarra: WFS INSPIRE CP + capas CATAST_ locales para BU/AD.

Verificado: el unico tipo INSPIRE es ``CP:CadastralParcel``; no hay BU/AD
INSPIRE ni ATOM. Los edificios se obtienen de ``IDENA:CATAST_Pol_Edificacion``
por BBOX (CRS de la parcela). El filtro ad-hoc funciona con la propiedad
``nationalCadastralReference`` sin prefijo.
"""

from __future__ import annotations

from habitalens.cadastre_providers.base import CadastreProvider
from habitalens.cadastre_providers.wfs import equals_filter, get_feature_request
from habitalens.net import HttpRequest
from habitalens.property import RefCat, Territory


class NavarraProvider(CadastreProvider):
    provider_id = "navarra"
    territory = Territory.NAVARRA

    def _get_parcel_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        value = RefCat.parse(refcat, self.territory).normalized
        filter_xml = equals_filter(self.config["filter"]["parcel_property"], value)
        request = get_feature_request(
            self.config["wfs"]["parcel"],
            self.config["types"]["parcel"],
            filter_xml=filter_xml,
        )
        return self._fetch_raw("parcel", refcat, request), request

    def _get_buildings_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        request = self._bbox_request(
            self.config["wfs"]["local"], self.config["types"]["building"], refcat
        )
        return self._fetch_raw("building", refcat, request), request
