"""Operaciones geometricas internas. La geometria NUNCA se expone en modelos.

Solo se registran en los hallazgos valores derivados (interseccion booleana,
distancias en unidades explicitas); nunca coordenadas.
"""

from __future__ import annotations

from pyproj import Transformer
from shapely import wkt as shapely_wkt
from shapely.geometry.base import BaseGeometry
from shapely.ops import transform as shapely_transform

from habitalens.evidence.crs import horizontal_epsg


def parse_wkt(text: str) -> BaseGeometry:
    return shapely_wkt.loads(text)


def _transformer(src_crs: str, dst_crs: str) -> Transformer:
    return Transformer.from_crs(
        f"EPSG:{horizontal_epsg(src_crs)}",
        f"EPSG:{horizontal_epsg(dst_crs)}",
        always_xy=True,
    )


def transform(geometry: BaseGeometry, src_crs: str, dst_crs: str) -> BaseGeometry:
    if horizontal_epsg(src_crs) == horizontal_epsg(dst_crs):
        return geometry
    return shapely_transform(_transformer(src_crs, dst_crs).transform, geometry)


def to_wgs84(geometry: BaseGeometry, src_crs: str) -> BaseGeometry:
    return transform(geometry, src_crs, "EPSG:4326")


def bounds_wgs84(geometry: BaseGeometry, src_crs: str) -> tuple[float, float, float, float]:
    """(minlon, minlat, maxlon, maxlat) en EPSG:4326."""

    return to_wgs84(geometry, src_crs).bounds


def intersects(first: BaseGeometry, second: BaseGeometry) -> bool:
    return bool(first.intersects(second))


def distance_m(first: BaseGeometry, second: BaseGeometry) -> float:
    """Distancia minima en metros. Ambas geometrias deben estar en CRS metrico."""

    return float(first.distance(second))
