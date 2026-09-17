"""CEE Cataluna: consulta por referencia catastral via Socrata (ICAEN).

Endpoint verificado: `analisi.transparenciacatalunya.cat/resource/j6ii-t3w2`.
Sin registro para la referencia -> INCONCLUSIVE (la cobertura completa del
registro por referencia no esta acreditada); nunca se afirma "no consta".
"""

from __future__ import annotations

import json
import re

from habitalens.cee.base import CeeLookupResult, CeeProvider, CeeRecord, CeeStatus
from habitalens.net import HttpRequest

_REFCAT_SAFE = re.compile(r"[A-Za-z0-9.\-_]+")


class CatalunyaCeeProvider(CeeProvider):
    region = "catalunya"

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
            params=(("$where", f"referencia_cadastral='{refcat}'"), ("$limit", "1")),
        )
        content = self._fetch(f"lookup:{refcat}", request)
        rows = json.loads(content.decode("utf-8", errors="ignore"))
        if not rows:
            return CeeLookupResult(
                refcat=refcat,
                region=self.region,
                status=CeeStatus.INCONCLUSIVE,
                note="sin registro para esta referencia; cobertura completa no acreditada",
            )
        row = rows[0]
        built = row.get("metres_cadastre")
        record = CeeRecord(
            refcat=str(row.get("referencia_cadastral") or refcat),
            rating=row.get("qualificaci_de_consum_d") or row.get("qualificaci_emissions"),
            date=row.get("data_entrada"),
            built_m2=float(built) if built not in (None, "") else None,
            address=" ".join(
                str(part)
                for part in (row.get("adre_a"), row.get("numero"), row.get("poblacio"))
                if part
            )
            or None,
            region=self.region,
            source_version=self.source_version(),
        )
        return CeeLookupResult(refcat=refcat, region=self.region, status=CeeStatus.FOUND, record=record)
