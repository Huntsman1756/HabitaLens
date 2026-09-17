"""SNCZI: consulta WFS 2.0 por BBOX e interseccion con la geometria de propiedad.

Servicio verificado: ``https://gis.miteco.gob.es/geoserver/agua/wfs`` (workspace
``agua``). El WFS declara DefaultCRS EPSG:4258 y acepta ``srsName=EPSG:4326`` con
bbox en orden lon,lat. Licencia CC BY 4.0 (atribucion MITECO).

Semantica de cobertura ESTRICTA: SNCZI solo cubre el dominio publico hidraulico
de competencia estatal; las cuencas de competencia autonomica no estan en la
capa. Por tanto 0 intersecciones -> INCONCLUSIVE (ausencia no acreditable),
nunca OBSERVED-ausencia. Un hallazgo OBSERVED exige interseccion verificada.
"""

from __future__ import annotations

from habitalens.evidence.geometry import bounds_wgs84, to_wgs84
from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.net import HttpRequest
from habitalens.sources.base import EvidenceSource, feature_geometry, json_features


def _polygons(content: bytes) -> list:
    return [
        feature_geometry(feature, {"Polygon", "MultiPolygon"})
        for feature in json_features(content, limit=50)
    ]


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
                    status=FindingStatus.OBSERVED if hits else FindingStatus.INCONCLUSIVE,
                    observed=True if hits else None,
                    value=float(len(hits)) if hits else None,
                    unit="zones" if hits else None,
                    note=None if hits else "sin intersecciones: cobertura SNCZI no acreditada",
                    source_crs="EPSG:4326",
                    operational_crs=operational_crs,
                    method="wfs-getfeature-bbox-intersects",
                    inputs=("property_geometry", layer),
                    provenance_id=provenance_id,
                )
            )
        return findings
