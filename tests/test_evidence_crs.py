"""Politica CRS: CRS operacional explicito y reduccion de CRS compuestos."""

from __future__ import annotations

from habitalens.evidence.crs import (
    choose_operational_crs,
    epsg_code,
    horizontal_epsg,
    is_geographic,
)
from habitalens.evidence.geometry import parse_wkt, transform


def test_epsg_code_parsing() -> None:
    assert epsg_code("EPSG:25830") == "25830"
    assert epsg_code("urn:ogc:def:crs:EPSG::4258") == "4258"
    assert epsg_code("http://www.opengis.net/def/crs/EPSG/0/4326") == "4326"


def test_compound_crs_reduced_to_horizontal() -> None:
    # El hallazgo Gipuzkoa EPSG:5730 no debe usarse tal cual para operaciones 2D.
    assert horizontal_epsg("EPSG:5730") == "25830"
    assert horizontal_epsg("EPSG:4979") == "4326"
    assert not is_geographic("EPSG:5730")


def test_operational_crs_by_utm_zone() -> None:
    assert choose_operational_crs(-8.0) == "EPSG:25829"
    assert choose_operational_crs(-3.7) == "EPSG:25830"
    assert choose_operational_crs(2.0) == "EPSG:25831"


def test_compound_transform_uses_horizontal_component() -> None:
    point = parse_wkt("POINT(-1.98 43.32)")
    via_compound = transform(point, "EPSG:4326", "EPSG:5730")
    via_horizontal = transform(point, "EPSG:4326", "EPSG:25830")
    assert abs(via_compound.x - via_horizontal.x) < 1e-6
    assert abs(via_compound.y - via_horizontal.y) < 1e-6
    assert via_compound.x > 400_000  # coordenada metrica
