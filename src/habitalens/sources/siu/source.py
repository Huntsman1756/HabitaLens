"""SIU (MIVAU): clases de suelo, via ArcGIS REST (`Servicios_OGC`, capa 15).

Semantica de cobertura ESTRICTA: el servicio no expone una lista por municipio
(solo cobertura agregada: 5.898 municipios integrados) y la consulta es solo
BBOX sin geometria devuelta. Por tanto:

- Si devuelve 0 features -> INCONCLUSIVE, NUNCA OBSERVED-ausencia: no puede
  acreditarse que el municipio este entre los integrados.
- Si devuelve features -> INCONCLUSIVE: una clase candidata por BBOX no
  acredita la clasificacion de la propiedad (sin geometria no hay
  interseccion verificable).

Licencia: reutilizacion bajo RISP (Ley 37/2007 / RD 1495/2011), atribucion
obligatoria; sin licencia CC explicita.
"""

from __future__ import annotations

from habitalens.evidence.geometry import bounds_wgs84
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import EvidenceSource, json_features


class SiuSource(EvidenceSource):
    source_id = "siu"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        minlon, minlat, maxlon, maxlat = bounds_wgs84(geometry, source_crs)
        request = HttpRequest(
            method="GET",
            url=self.config["rest_query"],
            params=(
                ("geometry", f"{minlon},{minlat},{maxlon},{maxlat}"),
                ("geometryType", "esriGeometryEnvelope"),
                ("inSR", "4326"),
                ("spatialRel", "esriSpatialRelIntersects"),
                ("outFields", "ProvINE,ClaseSuelo"),
                ("returnGeometry", "false"),
                ("f", "geojson"),
            ),
        )
        content = self._fetch("clases_suelo", property_id, request)
        provenance_id = self._record("clases_suelo", property_id, request, content)
        features = json_features(content)

        if not features:
            return [self._finding(
                property_id, operational_crs, FindingStatus.INCONCLUSIVE,
                provenance_id=provenance_id,
                note=(
                    "0 features: cobertura SIU no acreditada; no se interpreta "
                    "como ausencia de clasificacion"
                ),
            )]

        return [self._finding(
            property_id, operational_crs, FindingStatus.INCONCLUSIVE,
            provenance_id=provenance_id,
            note="resultado solo BBOX sin geometria: clasificacion de la propiedad no verificada",
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
            method="arcgis-rest-bbox-query",
            inputs=("property_geometry", self.config["layer"]),
            provenance_id=provenance_id,
            note=note,
        )
