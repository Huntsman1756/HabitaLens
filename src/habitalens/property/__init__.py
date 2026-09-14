"""Modelos publicos minimos de inmueble, parcela y edificio.

Regla de geometria (G0-A): los objetos publicos NO exponen coordenadas, GeoJSON
catastral, ``__geo_interface__`` ni geometrias reconstruibles. La geometria vive
exclusivamente en la cache local para procesamiento interno.
"""

from __future__ import annotations

from habitalens.property.models import (
    Address,
    Building,
    Parcel,
    Property,
    RefCat,
    Territory,
    TerritoryMask,
    infer_territory,
)

__all__ = [
    "Address",
    "Building",
    "Parcel",
    "Property",
    "RefCat",
    "Territory",
    "TerritoryMask",
    "infer_territory",
]
