"""NCSE-02: aceleracion sismica basica por municipio (IGN).

Servicio verificado: `https://www.ign.es/wms-inspire/geofisica`, capa
`HazardArea2002.NCSE-02` (WFS proxied GeoServer; geometrias EPSG:4258).
Licencia CC BY 4.0 (atribucion IGN).

Semantica de cobertura (clave):
- Fuera del sobre declarado -> UNAVAILABLE (sin cobertura oficial).
- Poligono de municipio con `aceleracion` -> OBSERVED.
- Poligono presente pero `aceleracion` vacio (null) -> UNAVAILABLE (dentro de
  cobertura, sin valor NCSE-02; NO es "ausencia" ni "fuera de cobertura").
- Sin poligono interpretable -> INCONCLUSIVE.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from habitalens.cadastre_providers.inspire import _geometry_from, localname
from habitalens.evidence.coverage import declared_envelope
from habitalens.evidence.geometry import to_wgs84
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import EvidenceSource

_FEATURE = "HazardArea2002.NCSE-02"


def _features(content: bytes) -> list[dict]:
    root = ET.fromstring(content)
    features = []
    for element in root.iter():
        if localname(element.tag) != _FEATURE:
            continue
        fields = {}
        for child in element.iter():
            name = localname(child.tag)
            if name in {"aceleracion", "coeficient", "ine_mun", "nombre"}:
                text = (child.text or "").strip()
                if text and name not in fields:
                    fields[name] = text
        features.append({"geometry": _geometry_from(element), **fields})
    return features


class Ncse02Source(EvidenceSource):
    source_id = "ncse02"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        point = to_wgs84(geometry, source_crs).centroid
        bounds = tuple(self.config["coverage_bounds_wgs84"])
        coverage = declared_envelope(point.x, point.y, bounds, self.source_id)

        if not coverage.is_covered:
            return [self._finding(
                property_id, operational_crs, FindingStatus.UNAVAILABLE,
                note=f"fuera de cobertura declarada ({coverage.basis})",
            )]

        delta = 0.002
        bbox = f"{point.x - delta},{point.y - delta},{point.x + delta},{point.y + delta},EPSG:4326"
        request = HttpRequest(
            method="GET",
            url=self.config["service"],
            params=(
                ("service", "WFS"),
                ("version", "2.0.0"),
                ("request", "GetFeature"),
                ("typeName", self.config["layer"]),
                ("bbox", bbox),
                ("count", "30"),
            ),
        )
        content = self._fetch("hazard", property_id, request)
        provenance_id = self._record("hazard", property_id, request, content)
        features = _features(content)

        containing = [
            feature
            for feature in features
            if feature.get("geometry") is not None and feature["geometry"].covers(point)
        ]
        if not containing:
            return [self._finding(
                property_id, operational_crs, FindingStatus.INCONCLUSIVE,
                provenance_id=provenance_id,
                note="dentro de cobertura pero sin poligono interpretable",
            )]

        feature = containing[0]
        if not feature.get("aceleracion"):
            return [self._finding(
                property_id, operational_crs, FindingStatus.UNAVAILABLE,
                provenance_id=provenance_id,
                note=f"dentro de cobertura, sin valor NCSE-02 ({feature.get('nombre')})",
            )]
        return [self._finding(
            property_id, operational_crs, FindingStatus.OBSERVED,
            observed=True, value=float(feature["aceleracion"]), unit="g",
            provenance_id=provenance_id,
            note=f"{feature.get('nombre')} inex={feature.get('ine_mun')} K={feature.get('coeficient')}",
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
            kind="ncse02.hazard",
            status=status,
            observed=observed,
            value=value,
            unit=unit,
            source_crs=self.config["default_crs"],
            operational_crs=operational_crs,
            method="wfs-getfeature-point-in-polygon",
            inputs=("property_geometry", self.config["layer"]),
            provenance_id=provenance_id,
            note=note,
        )
