"""Adaptador Bizkaia: ArcGIS INSPIRE WFS + ATOM municipal.

Verificado: el WFS InspireFeatureDownload ignora filtros de atributo (FES y CQL)
pero soporta BBOX. ``resolve_reference`` usa el ATOM municipal; los edificios se
obtienen por BBOX sobre el servicio INSPIRE Buildings.
"""

from __future__ import annotations

from habitalens.cadastre_providers.atom import (
    extract_zip_text,
    find_municipality_zip,
    municipality_from_refcat_bizkaia,
    parse_atom_entries,
)
from habitalens.cadastre_providers.base import CadastreProvider, ProviderError
from habitalens.net import HttpRequest
from habitalens.property import Territory


class BizkaiaProvider(CadastreProvider):
    provider_id = "bizkaia"
    territory = Territory.BIZKAIA

    def _get_parcel_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        municipality = municipality_from_refcat_bizkaia(refcat)
        if not municipality:
            raise ProviderError(f"bizkaia: refcat sin municipio decodificable: {refcat}")
        index_url = self.config["atom"]["parcel_index"]
        index_content = self._fetch_raw(
            "atom-index", "parcel-index", HttpRequest(method="GET", url=index_url)
        )
        zip_url = find_municipality_zip(parse_atom_entries(index_content), municipality)
        if not zip_url:
            zip_url = self.config["atom"]["municipality_zip"].format(code=municipality)
        request = HttpRequest(method="GET", url=zip_url)
        payload = self._fetch_raw("atom-zip", f"parcel:{municipality}", request, ext="zip")
        return b"".join(extract_zip_text(payload)), request

    def _get_buildings_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        request = self._bbox_request(
            self.config["wfs"]["building"], self.config["types"]["building"], refcat
        )
        return self._fetch_raw("building", refcat, request), request
