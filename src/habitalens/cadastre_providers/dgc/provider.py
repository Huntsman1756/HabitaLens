"""Adaptador DGC (Direccion General del Catastro).

G0-A.1: la resolucion por referencia catastral usa las **stored queries**
documentadas por la DGC, no filtros ad-hoc:

* parcela:   ``wfsCP.aspx?...&STOREDQUERY_ID=GetParcel&refcat=<RC>``
* edificios: ``wfsBU.aspx?...&STOREDQUERY_ID=GetBuildingByParcel&refcat=<RC>``

Se corrobora opcionalmente la referencia con el servicio REST libre
``Consulta_DNPRC`` (datos no protegidos), que ademas devuelve provincia y
municipio oficiales: la RC urbana **no** codifica el municipio en sus primeros
caracteres.

Se conserva ``get_parcel_near`` (BBOX lat,lon) como adquisicion por
localizacion procedente del geocoder.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from habitalens.cadastre_providers.base import CadastreProvider
from habitalens.net import HttpRequest
from habitalens.property import Territory


@dataclass(frozen=True)
class DnprcData:
    refcat: str
    province_code: str | None
    municipality_code: str | None
    municipality_name: str | None
    province_name: str | None
    area_m2: float | None
    land_use: str | None
    address: str | None
    error: str | None = None

    @property
    def exists(self) -> bool:
        return self.error is None


def _localname(tag: str) -> str:
    if "}" in tag:
        tag = tag.split("}", 1)[1]
    if ":" in tag:
        tag = tag.rsplit(":", 1)[1]
    return tag


def _first_text(root: ET.Element, names: tuple[str, ...]) -> str | None:
    wanted = set(names)
    for element in root.iter():
        if _localname(element.tag) in wanted and element.text and element.text.strip():
            return element.text.strip()
    return None


def parse_dnprc(content: bytes, requested_refcat: str | None = None) -> DnprcData:
    root = ET.fromstring(content)
    error = _first_text(root, ("des",))
    requested = (requested_refcat or "").strip().upper().replace(" ", "")
    units = [element for element in root.iter() if _localname(element.tag) in {"bi", "rcdnp"}]

    def unit_reference(unit: ET.Element) -> str:
        return "".join(_first_text(unit, (name,)) or "" for name in ("pc1", "pc2", "car", "cc1", "cc2"))

    candidates = units
    if requested:
        candidates = [
            unit for unit in units
            if unit_reference(unit) == requested
            or (len(requested) == 14 and unit_reference(unit)[:14] == requested)
        ]
    selected = candidates[0] if len(candidates) == 1 and error is None else None
    metadata = selected if selected is not None else root
    pc1 = _first_text(metadata, ("pc1",))
    pc2 = _first_text(metadata, ("pc2",))
    refcat = f"{pc1}{pc2}" if pc1 and pc2 else ""
    if requested and len(requested) == 20 and selected is not None:
        refcat = unit_reference(selected)
    if not candidates and error is None:
        error = "referencia solicitada no encontrada en la respuesta DNPRC"
    area_raw = _first_text(selected, ("sfc",)) if selected is not None else None
    area = None
    if area_raw:
        try:
            area = float(area_raw.replace(".", "").replace(",", "."))
        except ValueError:
            area = None
    street = _first_text(metadata, ("nv",))
    number = _first_text(metadata, ("pnp",))
    address = f"{street} {number}".strip() if street else None
    return DnprcData(
        refcat=refcat,
        province_code=_first_text(metadata, ("cp",)),
        municipality_code=_first_text(metadata, ("cm",)),
        municipality_name=_first_text(metadata, ("nm",)),
        province_name=_first_text(metadata, ("np",)),
        area_m2=area,
        land_use=_first_text(selected, ("luso",)) if selected is not None else None,
        address=address,
        error=error,
    )


class DgcProvider(CadastreProvider):
    provider_id = "dgc"
    territory = Territory.DGC

    def _stored_query_request(self, kind: str, refcat: str) -> HttpRequest:
        cfg = self.config["stored_queries"][kind]
        url = self.config["wfs"]["parcel" if kind == "parcel" else "building"]
        return HttpRequest(
            method="GET",
            url=url,
            params=(
                ("service", "WFS"),
                ("version", "2.0.0"),
                ("request", "GetFeature"),
                ("STOREDQUERY_ID", cfg),
                ("refcat", refcat),
            ),
        )

    def _get_parcel_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        request = self._stored_query_request("parcel", refcat)
        return self._fetch_raw("parcel", refcat, request), request

    def _get_buildings_content(self, refcat: str) -> tuple[bytes, HttpRequest]:
        request = self._stored_query_request("building", refcat)
        return self._fetch_raw("building", refcat, request), request

    def corroborate_reference(self, refcat: str) -> DnprcData:
        """Corrobora la RC con `Consulta_DNPRC` (existencia, provincia, municipio)."""

        request = HttpRequest(
            method="GET", url=self.config["dnprc"], params=(("RefCat", refcat),)
        )
        content = self._fetch_raw("dnprc", refcat, request)
        return parse_dnprc(content, requested_refcat=refcat)
