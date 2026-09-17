"""CSN radon: potencial de radon via capa ArcGIS del SIU (MIVAU).

Servicio verificado (2026-09-17):
`SIU/Potencial_riesgo_de_radon/MapServer/0` en `mapas.fomento.gob.es`, que
republica el Mapa del Potencial de Radon de Espana (CSN, 2017). Categorias
`cat_radon`: P90 en Bq/m3 por zonas (`< 100`, `101 - 200`, `201 - 300`,
`301 - 400`, `> 400`).

La consulta envia la geometria de la parcela por POST con
``spatialRel=esriSpatialRelIntersects``: solo vuelven las zonas que
intersectan la parcela, verificado por el servidor.

- >=1 zona -> OBSERVED con la peor categoria que toca la parcela.
- 0 zonas dentro de la cobertura -> INCONCLUSIVE: el mapa es estatal pero un
  hueco puntual no es demostrable como "sin riesgo" (enclaves, mar, borde).
- Fuera de la cobertura declarada -> UNAVAILABLE.

Atribucion obligatoria: "Mapa del Potencial de Radon de Espana CSN, 2017".
"""

from __future__ import annotations

import json
from urllib.parse import urlencode

from habitalens.evidence.coverage import declared_envelope
from habitalens.evidence.geometry import to_wgs84
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import (
    EvidenceSource,
    arcgis_next_request,
    arcgis_polygon,
    json_features,
)


class CsnRadonSource(EvidenceSource):
    source_id = "csn_radon"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        parcel = to_wgs84(geometry, source_crs)
        point = parcel.centroid
        bounds = tuple(self.config["coverage_bounds_wgs84"])
        coverage = declared_envelope(point.x, point.y, bounds, self.source_id)
        if not coverage.is_covered:
            return [self._finding(
                property_id, operational_crs, FindingStatus.UNAVAILABLE,
                note=f"fuera de cobertura declarada ({coverage.basis})",
            )]

        body = urlencode(
            {
                "f": "geojson",
                "geometry": json.dumps(arcgis_polygon(parcel)),
                "geometryType": "esriGeometryPolygon",
                "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects",
                "outFields": "cod_color,cat_radon,RiesoRadon",
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
            "potential", property_id, request, arcgis_next_request
        )
        provenance_id = pages[0][1]
        features = [f for content, _ in pages for f in json_features(content, page=True)]

        zones = {}
        for feature in features:
            props = feature.get("properties") or {}
            code = props.get("cod_color")
            label = props.get("RiesoRadon") or props.get("cat_radon")
            if isinstance(code, (int, float)) and not isinstance(code, bool) and label:
                zones[int(code)] = str(label)
        if not zones:
            return [self._finding(
                property_id, operational_crs, FindingStatus.INCONCLUSIVE,
                provenance_id=provenance_id,
                note="0 zonas dentro de la cobertura: no demostrable como ausencia",
            )]

        worst = max(zones)
        note = zones[worst]
        if len(zones) > 1:
            note = f"{note}; parcela en varias zonas: " + "; ".join(
                zones[code] for code in sorted(zones)
            )
        return [self._finding(
            property_id, operational_crs, FindingStatus.OBSERVED,
            observed=True, value=float(worst), unit="categoria P90",
            provenance_id=provenance_id, note=note,
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
            kind="csn_radon.potential",
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
