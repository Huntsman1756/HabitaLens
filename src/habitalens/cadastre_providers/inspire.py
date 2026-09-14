"""Parser de GML/INSPIRE compartido por los adaptadores.

La geometria se extrae SOLO para uso interno (cache/DB). Los objetos que
devuelve este modulo son internos y jamas se exponen desde los modelos publicos.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

_GEOGRAPHIC_EPSG = {"4326", "4258", "4230"}
_EPSG_RE = re.compile(r"EPSG[/:]+(?:0[/:]+)?(\d+)", re.IGNORECASE)


def _iter_roots(content: bytes):
    """Itera raices XML, tolerando varios documentos concatenados (ATOM/GML)."""

    try:
        yield ET.fromstring(content)
        return
    except ET.ParseError:
        pass
    for chunk in re.split(rb"(?=<\?xml)", content):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            yield ET.fromstring(chunk)
        except ET.ParseError:
            continue


def localname(tag: str) -> str:
    if "}" in tag:
        tag = tag.split("}", 1)[1]
    if ":" in tag:
        tag = tag.rsplit(":", 1)[1]
    return tag


def _attr_local(element: ET.Element, name: str) -> str | None:
    for key, value in element.attrib.items():
        if localname(key) == name or key == name:
            return value
    return None


def _first_text(element: ET.Element, names: set[str]) -> str | None:
    for child in element.iter():
        if child is element:
            continue
        if localname(child.tag) in names and child.text and child.text.strip():
            return child.text.strip()
    return None


def _find_descendants(element: ET.Element, names: set[str]) -> list[ET.Element]:
    return [el for el in element.iter() if el is not element and localname(el.tag) in names]


def crs_from_element(element: ET.Element) -> str | None:
    for el in element.iter():
        srs = el.attrib.get("srsName") or _attr_local(el, "srsName")
        if srs:
            match = _EPSG_RE.search(srs)
            if match:
                return f"EPSG:{match.group(1)}"
    return None


def _coords_from_poslist(text: str, crs: str) -> list[tuple[float, float]]:
    numbers = [float(part) for part in text.split()]
    points = list(zip(numbers[0::2], numbers[1::2], strict=False))
    if crs.split(":")[-1] in _GEOGRAPHIC_EPSG:
        # GML/INSPIRE usa orden lat lon; se normaliza a (lon, lat) para shapely.
        points = [(lon, lat) for lat, lon in points]
    return points


def _ring_from(element: ET.Element | None, crs: str):
    if element is None:
        return None
    for descendant in element.iter():
        if localname(descendant.tag) == "posList" and descendant.text:
            return _coords_from_poslist(descendant.text, crs)
        if localname(descendant.tag) == "pos" and descendant.text:
            return _coords_from_poslist(descendant.text, crs)
    return None


def _geometry_from(element: ET.Element):
    try:
        from shapely.geometry import MultiPolygon, Point, Polygon
    except ImportError:  # pragma: no cover - dependencia declarada
        return None

    crs = crs_from_element(element) or "EPSG:4326"
    polygon_elements = _find_descendants(element, {"Polygon", "PolygonPatch"})
    polygons = []
    for poly_el in polygon_elements:
        exterior = None
        interiors = []
        for descendant in poly_el.iter():
            name = localname(descendant.tag)
            if name == "exterior":
                exterior = _ring_from(descendant, crs)
            elif name == "interior":
                ring = _ring_from(descendant, crs)
                if ring:
                    interiors.append(ring)
        if exterior:
            try:
                polygons.append(Polygon(exterior, holes=interiors))
            except (ValueError, TypeError):
                continue
    if polygons:
        return polygons[0] if len(polygons) == 1 else MultiPolygon(polygons)
    for descendant in element.iter():
        if localname(descendant.tag) == "Point":
            for pos in descendant.iter():
                if localname(pos.tag) == "pos" and pos.text:
                    coords = _coords_from_poslist(pos.text, crs)
                    if coords:
                        return Point(coords[0])
    return None


@dataclass
class ParsedParcel:
    refcat: str
    crs: str
    area_m2: float | None = None
    land_use: str | None = None
    geometry: object | None = None


@dataclass
class ParsedBuilding:
    building_id: str
    crs: str
    refcat: str | None = None
    area_m2: float | None = None
    geometry: object | None = None


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_parcel_features(
    content: bytes, feature_tokens: tuple[str, ...] = ("CadastralParcel",)
) -> list[ParsedParcel]:
    results: list[ParsedParcel] = []
    for root in _iter_roots(content):
        results.extend(_parse_parcels_from_root(root, feature_tokens))
    return results


def _parse_parcels_from_root(
    root: ET.Element, feature_tokens: tuple[str, ...]
) -> list[ParsedParcel]:
    results: list[ParsedParcel] = []
    for element in root.iter():
        name = localname(element.tag)
        if any(name.endswith(token) for token in feature_tokens) and "Zoning" not in name:
            refcat = _first_text(element, {"nationalCadastralReference"}) or _first_text(
                element, {"localId"}
            )
            if not refcat:
                continue
            crs = crs_from_element(element) or "EPSG:4326"
            results.append(
                ParsedParcel(
                    refcat=refcat,
                    crs=crs,
                    area_m2=_to_float(_first_text(element, {"areaValue"})),
                    land_use=_first_text(element, {"landUse", "label"}),
                    geometry=_geometry_from(element),
                )
            )
    return results


def parse_building_features(
    content: bytes, feature_tokens: tuple[str, ...] = ("Building",)
) -> list[ParsedBuilding]:
    results: list[ParsedBuilding] = []
    for root in _iter_roots(content):
        results.extend(_parse_buildings_from_root(root, feature_tokens))
    return results


def _parse_buildings_from_root(
    root: ET.Element, feature_tokens: tuple[str, ...]
) -> list[ParsedBuilding]:
    results: list[ParsedBuilding] = []
    for element in root.iter():
        name = localname(element.tag)
        if any(name.endswith(token) for token in feature_tokens) and "Part" not in name:
            gml_id = _attr_local(element, "id") or _first_text(
                element, {"localId", "reference"}
            )
            crs = crs_from_element(element) or "EPSG:4326"
            results.append(
                ParsedBuilding(
                    building_id=str(gml_id) if gml_id else f"building-{len(results)}",
                    crs=crs,
                    refcat=_first_text(element, {"nationalCadastralReference"}),
                    area_m2=_to_float(_first_text(element, {"areaValue"})),
                    geometry=_geometry_from(element),
                )
            )
    return results


def extract_version(content: bytes) -> str | None:
    """Extrae un identificador de version/esquema observado en un XML."""

    text = content[:200_000].decode("utf-8", errors="ignore")
    for pattern in (
        r"ServiceTypeVersion>([^<]+)<",
        r'WFS_Capabilities version="([^"]+)"',
        r'wfs:FeatureCollection[^>]*timeStamp="([^"]+)"',
    ):
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return None
