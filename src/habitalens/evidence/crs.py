"""Politica CRS de G0-B.

Se conserva siempre el ``source_crs`` de la evidencia; toda operacion de
distancia/interseccion se realiza en un CRS operacional explicito (zona UTM
ETRS89 coherente con la longitud del centroide). No se asume EPSG:25830
nacional. Los CRS compuestos (p. ej. EPSG:5730) se reducen a su componente
horizontal para operaciones 2D, registrando la vertical por separado.
"""

from __future__ import annotations

#: Componente horizontal de los CRS compuestos 3D usados en los proveedores.
_COMPOUND_HORIZONTAL: dict[str, str] = {
    "5730": "25830",  # ETRS89 / UTM 30N + altura
    "5731": "25831",
    "5732": "25832",
    "4979": "4326",  # WGS84 3D -> WGS84 2D
    "4937": "4258",  # ETRS89 3D -> ETRS89 2D
}

_GEOGRAPHIC = {"4326", "4258", "4230"}


def epsg_code(crs: str) -> str:
    import re

    matches = re.findall(r"\d{3,5}", str(crs))
    if matches:
        return matches[-1]
    return str(crs).strip()


def horizontal_epsg(crs: str) -> str:
    """Devuelve el codigo EPSG horizontal (2D) de un CRS, simple o compuesto."""

    code = epsg_code(crs)
    return _COMPOUND_HORIZONTAL.get(code, code)


def is_geographic(crs: str) -> bool:
    return horizontal_epsg(crs) in _GEOGRAPHIC


def utm_etrs89_epsg(lon: float) -> str:
    """Zona UTM ETRS89 (EPSG:258xx) a partir de la longitud en grados."""

    zone = int((lon + 180.0) // 6.0) + 1
    return f"EPSG:{25800 + zone}"


def choose_operational_crs(lon: float) -> str:
    """CRS operacional explicito para operaciones metricas 2D."""

    return utm_etrs89_epsg(lon)
