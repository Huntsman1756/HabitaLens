"""Geocodificacion con CartoCiudad (cliente propio, sin pycartociudad)."""

from __future__ import annotations

from habitalens.geocoding.cartociudad import (
    CartoCiudadClient,
    GeocodeCandidate,
    GeocodingError,
)

__all__ = ["CartoCiudadClient", "GeocodeCandidate", "GeocodingError"]
