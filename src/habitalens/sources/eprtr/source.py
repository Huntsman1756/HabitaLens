"""E-PRTR / European Industrial Emissions Portal: puntos de instalaciones.

No existe WFS. Se usa la API REST de ArcGIS con salida GeoJSON (verificado):
``https://air.discomap.eea.europa.eu/arcgis/services/Air/IED_SiteMap/MapServer/0/query``
Licencia CC BY 4.0 (atribucion EEA).
"""

from __future__ import annotations

import json

from shapely.geometry import Point

from habitalens.evidence.geometry import bounds_wgs84, distance_m, transform
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import EvidenceSource


def _points(content: bytes) -> list[Point]:
    data = json.loads(content.decode("utf-8", errors="ignore"))
    points = []
    for feature in data.get("features", []):
        geometry = feature.get("geometry") or {}
        if geometry.get("type") == "Point":
            coords = geometry.get("coordinates")
            if coords and len(coords) >= 2:
                points.append(Point(float(coords[0]), float(coords[1])))
    return points


class EprtrSource(EvidenceSource):
    source_id = "eprtr"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        margin = float(self.config.get("search_radius_deg", 0.05))
        minlon, minlat, maxlon, maxlat = bounds_wgs84(geometry, source_crs)
        minlon, minlat = minlon - margin, minlat - margin
        maxlon, maxlat = maxlon + margin, maxlat + margin
        method = f"arcgis-rest-bbox-query radius={margin}deg"
        request = HttpRequest(
            method="GET",
            url=self.config["query"],
            headers=(
                (
                    "User-Agent",
                    "HabitaLens/0.0.1 (G0-B; +https://github.com/Huntsman1756/HabitaLens)",
                ),
            ),
            params=(
                ("where", "1=1"),
                ("geometry", f"{minlon},{minlat},{maxlon},{maxlat}"),
                ("geometryType", "esriGeometryEnvelope"),
                ("inSR", "4326"),
                ("spatialRel", "esriSpatialRelIntersects"),
                ("outFields", "siteName,countryCode"),
                ("returnGeometry", "true"),
                ("outSR", "4326"),
                ("f", "geojson"),
            ),
        )
        content = self._fetch("facilities", property_id, request, ext="json")
        provenance_id = self._record("facilities", property_id, request, content)
        points = _points(content)

        findings = [
            EvidenceFinding(
                property_id=property_id,
                source=self.source_id,
                source_version=self.source_version(),
                kind="eprtr.facilities",
                status=FindingStatus.OBSERVED,
                observed=bool(points),
                value=float(len(points)),
                unit="facilities",
                source_crs="EPSG:4326",
                operational_crs=operational_crs,
                method=method,
                inputs=("property_geometry", f"bbox+{margin}deg"),
                provenance_id=provenance_id,
            )
        ]

        nearest_distance: float | None = None
        nearest_site: str | None = None
        if points:
            metric_geometry = transform(geometry, source_crs, operational_crs)
            metric_points = [transform(point, "EPSG:4326", operational_crs) for point in points]
            distances = [distance_m(metric_geometry, point) for point in metric_points]
            index = min(range(len(distances)), key=distances.__getitem__)
            nearest_distance = distances[index]
            data = json.loads(content.decode("utf-8", errors="ignore"))
            attributes = data.get("features", [{}])[index].get("properties", {})
            nearest_site = attributes.get("siteName")
        findings.append(
            EvidenceFinding(
                property_id=property_id,
                source=self.source_id,
                source_version=self.source_version(),
                kind="eprtr.nearest_facility_distance_m",
                status=FindingStatus.DERIVED,
                value=nearest_distance,
                unit="m",
                source_crs="EPSG:4326",
                operational_crs=operational_crs,
                method="min-distance-in-operational-crs",
                inputs=("property_geometry", "eprtr.facilities"),
                provenance_id=provenance_id,
                note=nearest_site
                or f"sin instalaciones en radio {margin}deg",
            )
        )
        return findings
