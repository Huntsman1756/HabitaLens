"""SIU (MIVAU): clases de suelo, via ArcGIS REST (`Servicios_OGC`, capa 15).

La consulta envia la geometria de la parcela por POST (las parcelas reales
exceden el limite de URL en GET) con ``spatialRel=esriSpatialRelIntersects``:
solo vuelven las clases cuya geometria intersecta la parcela, de modo que la
interseccion queda verificada por el servidor sin exponer ni persistir
geometria de respuesta.

- Si devuelve >=1 clase -> OBSERVED: la interseccion esta verificada. La
  parcela puede tocar varias clases; se listan todas en la nota.
- Si devuelve 0 features -> INCONCLUSIVE, NUNCA OBSERVED-ausencia: el servicio
  no expone una lista por municipio (cobertura agregada: 5.898 municipios
  integrados) y no puede acreditarse que el municipio este entre ellos.

Licencia: reutilizacion bajo RISP (Ley 37/2007 / RD 1495/2011), atribucion
obligatoria; sin licencia CC explicita.
"""

from __future__ import annotations

import json
from urllib.parse import urlencode

from habitalens.evidence.geometry import to_wgs84
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import (
    EvidenceSource,
    arcgis_next_request,
    arcgis_polygon,
    json_features,
)


class SiuSource(EvidenceSource):
    source_id = "siu"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        parcel = to_wgs84(geometry, source_crs)
        body = urlencode(
            {
                "f": "geojson",
                "geometry": json.dumps(arcgis_polygon(parcel)),
                "geometryType": "esriGeometryPolygon",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "ProvINE,ClaseSuelo",
                "orderByFields": "OBJECTID",
                "returnGeometry": "false",
            }
        ).encode()
        request = HttpRequest(
            method="POST",
            url=self.config["rest_query"],
            data=body,
            headers=(("Content-Type", "application/x-www-form-urlencoded"),),
        )
        pages = self._fetch_pages(
            "clases_suelo", property_id, request, arcgis_next_request
        )
        provenance_id = pages[0][1]
        features = [f for content, _ in pages for f in json_features(content, page=True)]

        if not features:
            return [self._finding(
                property_id, operational_crs, FindingStatus.INCONCLUSIVE,
                provenance_id=provenance_id,
                note=(
                    "0 features: cobertura SIU no acreditada; no se interpreta "
                    "como ausencia de clasificacion"
                ),
            )]

        classes = []
        for feature in features:
            props = feature.get("properties") or {}
            clase = props.get("ClaseSuelo")
            provine = props.get("ProvINE")
            entry = f"{clase} (ProvINE={provine})"
            if entry not in classes:
                classes.append(entry)
        return [self._finding(
            property_id, operational_crs, FindingStatus.OBSERVED,
            observed=True, value=float(len(classes)), unit="classes",
            provenance_id=provenance_id, note="; ".join(classes),
        )]

    def _finding(
        self,
        property_id: str,
        operational_crs: str,
        status: FindingStatus,
        *,
        observed: bool | None = None,
        value: float | None = None,
        unit: str | None = None,
        provenance_id: str | None = None,
        note: str | None = None,
    ) -> EvidenceFinding:
        return EvidenceFinding(
            property_id=property_id,
            source=self.source_id,
            source_version=self.source_version(),
            kind="siu.clase_suelo",
            status=status,
            observed=observed,
            value=value,
            unit=unit,
            source_crs=self.config["default_crs"],
            operational_crs=operational_crs,
            method="arcgis-rest-parcel-intersects",
            inputs=("property_geometry", self.config["layer"]),
            provenance_id=provenance_id,
            note=note,
        )
