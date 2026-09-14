"""Nucleo de evidencia espacial (G0-B).

Convierte geometria de propiedad + fuentes oficiales heterogeneas en hallazgos
deterministas y trazables, clasificados como OBSERVED, DERIVED, UNAVAILABLE o
INCONCLUSIVE. Ninguna salida publica expone geometria.
"""

from __future__ import annotations

from habitalens.evidence.corpus import CORPUS, CorpusProperty, property_by_id
from habitalens.evidence.crs import choose_operational_crs, horizontal_epsg
from habitalens.evidence.engine import EvidenceEngine
from habitalens.evidence.models import (
    EvidenceFinding,
    FindingStatus,
    PropertyEvidence,
)

__all__ = [
    "CORPUS",
    "CorpusProperty",
    "EvidenceEngine",
    "EvidenceFinding",
    "FindingStatus",
    "PropertyEvidence",
    "choose_operational_crs",
    "horizontal_epsg",
    "property_by_id",
]
