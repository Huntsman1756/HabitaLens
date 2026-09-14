"""Contrato de consulta de CEE por registro autonomico.

Sin geometria y sin score. La ausencia de registro se marca INCONCLUSIVE
mientras no pueda acreditarse cobertura completa del registro por referencia.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.config import load_endpoints
from habitalens.licensing import LicenseDeclaration, load_license
from habitalens.net import HttpRequest, HttpSource, Source
from habitalens.provenance import ProvenanceRecorder


class CeeStatus(StrEnum):
    FOUND = "found"
    NOT_FOUND = "not_found"
    INCONCLUSIVE = "inconclusive"


@dataclass(frozen=True)
class CeeRecord:
    refcat: str
    rating: str | None
    date: str | None
    built_m2: float | None
    address: str | None
    region: str
    source_version: str


@dataclass(frozen=True)
class CeeLookupResult:
    refcat: str
    region: str
    status: CeeStatus
    record: CeeRecord | None = None
    note: str | None = None


class CeeProvider(ABC):
    region: str = ""

    def __init__(
        self,
        source: Source | None = None,
        cache: CacheStore | None = None,
        provenance: ProvenanceRecorder | None = None,
        refresh: bool = False,
    ):
        if not self.region:
            raise ValueError(f"{type(self).__name__} no define region")
        self.package_dir = Path(inspect.getfile(type(self))).parent
        self.license: LicenseDeclaration = load_license(self.package_dir)
        self._cache = cache or getattr(source, "cache", None) or CacheStore()
        self.source: Source = source or HttpSource(cache=self._cache)
        self.provenance = provenance or ProvenanceRecorder(self._cache.root)
        self.refresh = refresh
        self.config = load_endpoints()["cee_sources"][self.region]

    def source_version(self) -> str:
        return str(self.config["source_version"])

    @abstractmethod
    def lookup(self, refcat: str) -> CeeLookupResult: ...

    def _fetch(self, key: str, request: HttpRequest, *, ext: str = "json") -> bytes:
        return self.source.fetch(
            f"cee_{self.region}",
            key,
            request,
            refresh=self.refresh,
            ext=ext,
            meta={"region": self.region},
        )
