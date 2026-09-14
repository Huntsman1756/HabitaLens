"""SNCZI: consulta WFS 2.0 por BBOX e interseccion con la geometria de propiedad.

Servicio verificado: ``https://gis.miteco.gob.es/geoserver/agua/wfs`` (workspace
``agua``). El WFS declara DefaultCRS EPSG:4258 y acepta ``srsName=EPSG:4326`` con
bbox en orden lon,lat. Licencia CC BY 4.0 (atribucion MITECO).
"""

from __future__ import annotations

import json

from shapely.geometry import shape

from habitalens.evidence.geometry import bounds_wgs84, to_wgs84
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import EvidenceSource


def _polygons(content: bytes) -> list:
    data = json.loads(content.decode("utf-8", errors="ignore"))
    polygons = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry")
        if geometry:
            polygons.append(shape(geometry))
    return polygons


class SncziSource(EvidenceSource):
    source_id = "snczi"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        minlon, minlat, maxlon, maxlat = bounds_wgs84(geometry, source_crs)
        bbox = f"{minlon},{minlat},{maxlon},{maxlat},EPSG:4326"
        geometry_wgs84 = to_wgs84(geometry, source_crs)
        findings: list[EvidenceFinding] = []
        for name, layer in self.config["layers"].items():
            request = HttpRequest(
                method="GET",
                url=self.config["service"],
                params=(
                    ("service", "WFS"),
                    ("version", "2.0.0"),
                    ("request", "GetFeature"),
                    ("typeNames", layer),
                    ("bbox", bbox),
                    ("srsName", "EPSG:4326"),
                    ("count", "50"),
                    ("outputFormat", "application/json"),
                ),
            )
            content = self._fetch(name, f"{property_id}:{name}", request, ext="json")
            provenance_id = self._record(name, property_id, request, content)
            polygons = _polygons(content)
            hits = [poly for poly in polygons if geometry_wgs84.intersects(poly)]
            findings.append(
                EvidenceFinding(
                    property_id=property_id,
                    source=self.source_id,
                    source_version=self.source_version(),
                    kind=f"snczi.{name}",
                    status=FindingStatus.OBSERVED,
                    observed=bool(hits),
                    value=float(len(hits)),
                    unit="zones",
                    source_crs="EPSG:4326",
                    operational_crs=operational_crs,
                    method="wfs-getfeature-bbox-intersects",
                    inputs=("property_geometry", layer),
                    provenance_id=provenance_id,
                )
            )
        return findings
