"""Adaptador DGC: WFS CP/BU/AD + ATOM municipal (jerarquico por provincia).

Verificado en vivo: el WFS de la DGC no aplica filtros ad-hoc (devuelve una
pagina fija), por lo que ``resolve_reference`` usa el ATOM municipal jerarquico
como estrategia de resolucion. Los edificios se obtienen por BBOX sobre el WFS
BU a partir de la geometria interna de la parcela.
"""

from __future__ import annotations

from habitalens.cadastre_providers.atom import (
    extract_zip_text,
    find_municipality_zip,
    find_province_feed,
    municipality_from_refcat_dgc,
    parse_atom_entries,
)
from habitalens.cadastre_providers.base import CadastreProvider, ProviderError
from habitalens.net import HttpRequest
from habitalens.property import Territory


class DgcProvider(CadastreProvider):
    provider_id = "dgc"
    territory = Territory.DGC

    def _get_parcel_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        municipality = municipality_from_refcat_dgc(refcat)
        if len(municipality) < 5:
            raise ProviderError(f"dgc: refcat sin municipio decodificable: {refcat}")
        province = municipality[:2]
        index_url = self.config["atom"]["parcel_index"]
        index_request = HttpRequest(method="GET", url=index_url)
        index_content = self._fetch_raw("atom-index", "parcel-index", index_request)
        province_feed = find_province_feed(parse_atom_entries(index_content), province)
        if not province_feed:
            raise ProviderError(f"dgc: sin sub-feed ATOM para provincia {province}")
        province_content = self._fetch_raw(
            "atom-province",
            province,
            HttpRequest(method="GET", url=province_feed),
        )
        zip_url = find_municipality_zip(
            parse_atom_entries(province_content), municipality
        )
        if not zip_url:
            raise ProviderError(
                f"dgc: sin ZIP ATOM para municipio {municipality} en provincia {province}"
            )
        request = HttpRequest(method="GET", url=zip_url)
        payload = self._fetch_raw("atom-zip", f"parcel:{municipality}", request, ext="zip")
        return b"".join(extract_zip_text(payload)), request

    def _get_buildings_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        request = self._bbox_request(
            self.config["wfs"]["building"], self.config["types"]["building"], refcat
        )
        return self._fetch_raw("building", refcat, request), request
