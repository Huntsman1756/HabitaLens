"""Cobertura como ciudadano de primera clase de G0-C.

Regla dura: `query devuelve 0 features` NO es "sin afecciones". Para emitir
OBSERVED-ausencia hay que acreditar cobertura. Si no puede acreditarse, el
resultado es UNAVAILABLE (sin cobertura oficial) o INCONCLUSIVE (indeterminable).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CoverageStatus(StrEnum):
    COVERED = "covered"
    NOT_COVERED = "not_covered"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Coverage:
    status: CoverageStatus
    basis: str
    declared_bounds: tuple[float, float, float, float] | None = None

    @property
    def is_covered(self) -> bool:
        return self.status == CoverageStatus.COVERED


def point_in_bounds(
    lon: float, lat: float, bounds: tuple[float, float, float, float]
) -> bool:
    minlon, minlat, maxlon, maxlat = bounds
    return minlon <= lon <= maxlon and minlat <= lat <= maxlat


def declared_envelope(
    lon: float, lat: float, bounds: tuple[float, float, float, float], source: str
) -> Coverage:
    if point_in_bounds(lon, lat, bounds):
        return Coverage(CoverageStatus.COVERED, f"{source}:declared_envelope", bounds)
    return Coverage(CoverageStatus.NOT_COVERED, f"{source}:outside_envelope", bounds)
