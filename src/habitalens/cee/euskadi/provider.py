"""CEE Euskadi: consulta por referencia catastral via API REST (api.euskadi.eus).

Endpoint verificado: `api.euskadi.eus/energy-efficiency/buildings` con filtro
`cadastral-ref` (referencia catastral foral: formato numerico provincial,
p.ej. `4774399` en Gipuzkoa, `48.020.1619.04006` en Bizkaia).

Sin registro para la referencia -> INCONCLUSIVE (la cobertura completa del
registro por referencia no esta acreditada); nunca se afirma "no consta".

Las referencias catastrales forales difieren del formato DGC de 20 caracteres;
se acepta cualquier referencia no vacia sin caracteres peligrosos y el propio
servicio valida el formato.
"""

from __future__ import annotations

import json
import re

from habitalens.cee.base import CeeLookupResult, CeeProvider, CeeRecord, CeeStatus
from habitalens.net import HttpRequest

_REFCAT_SAFE = re.compile(r"[A-Za-z0-9.\-_/ ]+")


class EuskadiCeeProvider(CeeProvider):
    region = "euskadi"

    def lookup(self, refcat: str) -> CeeLookupResult:
        refcat = str(refcat).strip()
        if not _REFCAT_SAFE.fullmatch(refcat):
            return CeeLookupResult(
                refcat=refcat,
                region=self.region,
                status=CeeStatus.INCONCLUSIVE,
                note="referencia catastral con formato no valido",
            )
        request = HttpRequest(
            method="GET",
            url=self.config["resource"],
            params=(("cadastral-ref", refcat), ("itemsOfPage", "1")),
        )
        content = self._fetch(f"lookup:{refcat}", request)
        data = json.loads(content.decode("utf-8", errors="ignore"))
        if not isinstance(data, dict):
            return CeeLookupResult(
                refcat=refcat,
                region=self.region,
                status=CeeStatus.INCONCLUSIVE,
                note="respuesta del registro no interpretable",
            )
        items = data.get("items")
        # La API omite `items` cuando totalItems es 0.
        if items is None and data.get("totalItems") == 0:
            items = []
        if not isinstance(items, list):
            return CeeLookupResult(
                refcat=refcat,
                region=self.region,
                status=CeeStatus.INCONCLUSIVE,
                note="respuesta del registro no interpretable",
            )
        if not items:
            return CeeLookupResult(
                refcat=refcat,
                region=self.region,
                status=CeeStatus.INCONCLUSIVE,
                note="sin registro para esta referencia; cobertura completa no acreditada",
            )
        item = items[0]
        return CeeLookupResult(
            refcat=refcat,
            region=self.region,
            status=CeeStatus.FOUND,
            record=CeeRecord(
                refcat=str(item.get("cadastralData") or refcat),
                rating=item.get("energyRating"),
                date=item.get("date"),
                built_m2=None,
                address=item.get("address"),
                region=self.region,
                source_version=self.source_version(),
            ),
        )
