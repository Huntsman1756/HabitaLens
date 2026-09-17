"""BTN (IGN/CNIG): infraestructura de transporte (carretera y ferrocarril).

Servicio verificado: `https://servicios.idee.es/wfs-inspire/transportes`.
Capas con geometria consultable por BBOX: `tn-ro:RoadLink`, `tn-ra:RailwayLink`
(las capas `Road`/`RailwayLine` no tienen geometria). CRS nativo EPSG:4258.
Licencia CC BY 4.0 compatible (atribucion IGN).

Cobertura nacional declarada; 0 features dentro del sobre = ausencia de
infraestructura (OBSERVED-ausencia), no "sin cobertura".
"""

from __future__ import annotations

from shapely.geometry import LineString

from habitalens.evidence.coverage import declared_envelope
from habitalens.evidence.geometry import distance_m, to_wgs84, transform
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import (
    EvidenceSource,
    wfs_next_request,
    xml_features,
    xml_positions,
)

_NATIVE_CRS = "EPSG:4258"


def _lines(pages: list[bytes]) -> list[LineString]:
    lines: list[LineString] = []
    for content in pages:
        for element in xml_features(
            content, {"RoadLink", "RailwayLink"}, limit=50, page=True
        ):
            positions = xml_positions(element)
            if len(positions) != 1:
                raise ValueError("unsupported multipart transport feature")
            line = LineString(positions[0])
            if line.is_empty or not line.is_valid:
                raise ValueError("invalid transport geometry")
            lines.append(line)
    return lines


class BtnSource(EvidenceSource):
    source_id = "btn"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        point = to_wgs84(geometry, source_crs).centroid
        bounds = tuple(self.config["coverage_bounds_wgs84"])
        coverage = declared_envelope(point.x, point.y, bounds, self.source_id)
        metric_geometry = transform(geometry, source_crs, operational_crs)
        minx, miny, maxx, maxy = metric_geometry.bounds
        bbox = f"{minx},{miny},{maxx},{maxy},urn:ogc:def:crs:EPSG::{operational_crs.split(':')[-1]}"

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
                    ("count", "50"),
                ),
            )
            pages = self._fetch_pages(
                name, property_id, request, wfs_next_request, ext="xml"
            )
            provenance_id = pages[0][1]

            if not coverage.is_covered:
                findings.append(self._finding(
                    property_id, operational_crs, f"{self.source_id}.{name}",
                    FindingStatus.UNAVAILABLE, provenance_id=provenance_id,
                    note=f"fuera de cobertura declarada ({coverage.basis})",
                ))
                continue

            lines = _lines([content for content, _ in pages])
            findings.append(self._finding(
                property_id, operational_crs, f"{self.source_id}.{name}",
                FindingStatus.OBSERVED, observed=bool(lines), value=float(len(lines)),
                unit="segments", provenance_id=provenance_id,
            ))
            if lines:
                metric_lines = [transform(line, _NATIVE_CRS, operational_crs) for line in lines]
                nearest = min(distance_m(metric_geometry, line) for line in metric_lines)
                findings.append(self._finding(
                    property_id, operational_crs,
                    f"{self.source_id}.{name}_nearest_distance_m",
                    FindingStatus.DERIVED, value=nearest, unit="m",
                    provenance_id=provenance_id,
                ))
        return findings

    def _finding(
        self,
        property_id: str,
        operational_crs: str,
        kind: str,
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
            kind=kind,
            status=status,
            observed=observed,
            value=value,
            unit=unit,
            source_crs=self.config["default_crs"],
            operational_crs=operational_crs,
            method="wfs-getfeature-bbox",
            inputs=("property_geometry", "operational_bbox"),
            provenance_id=provenance_id,
            note=note,
        )
