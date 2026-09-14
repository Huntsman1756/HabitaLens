"""CEE (certificado de eficiencia energetica) por registro autonomico (P1.B)."""

from __future__ import annotations

from habitalens.cee.base import CeeLookupResult, CeeProvider, CeeRecord, CeeStatus
from habitalens.cee.registry import cee_regions, get_cee_provider, lookup_any

__all__ = [
    "CeeLookupResult",
    "CeeProvider",
    "CeeRecord",
    "CeeStatus",
    "cee_regions",
    "get_cee_provider",
    "lookup_any",
]
