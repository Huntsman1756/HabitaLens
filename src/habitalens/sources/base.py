"""Contrato EvidenceSource + guarda de licencia para fuentes G0-B.

Regla: licencia y acceso antes que parsing. Una fuente sin ``LICENSE.yaml``
valido no puede inicializarse. Una fuente con licencia no declarada o sin
servicio verificable se marca ``usable=False`` y el motor solo emite
INCONCLUSIVE para ella.
"""

from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.config import load_endpoints
from habitalens.evidence.models import EvidenceFinding
from habitalens.licensing import LicenseDeclaration, load_license
from habitalens.net import HttpRequest, HttpSource, Source
from habitalens.provenance import ProvenanceRecorder


class SourceUnavailableError(RuntimeError):
    """La fuente no puede aportar dato aplicable (no es INCONCLUSIVE)."""


class EvidenceSource(ABC):
    source_id: str = ""

    def __init__(
        self,
        source: Source | None = None,
        cache: CacheStore | None = None,
        provenance: ProvenanceRecorder | None = None,
        refresh: bool = False,
    ):
        if not self.source_id:
            raise ValueError(f"{type(self).__name__} no define source_id")
        self.package_dir = Path(inspect.getfile(type(self))).parent
        self.license: LicenseDeclaration = load_license(self.package_dir)
        self._cache = cache or getattr(source, "cache", None) or CacheStore()
        self.source: Source = source or HttpSource(cache=self._cache)
        self.provenance = provenance or ProvenanceRecorder(self._cache.root)
        self.refresh = refresh
        self.config = load_endpoints()["evidence_sources"][self.source_id]
        self.usable: bool = bool(self.config.get("usable", True))
        self.unusable_reason: str | None = self.config.get("unusable_reason")

    def source_version(self) -> str:
        return str(self.config["source_version"])

    @abstractmethod
    def evaluate(
        self,
        geometry,
        source_crs: str,
        operational_crs: str,
        property_id: str,
    ) -> list[EvidenceFinding]:
        ...

    def _fetch(
        self,
        kind: str,
        key: str,
        request: HttpRequest,
        *,
        ext: str = "json",
    ) -> bytes:
        # La clave incluye un hash de la peticion (url+params): cambiar bbox,
        # radio o capa nunca reutiliza una respuesta cacheada obsoleta.
        import hashlib

        digest = hashlib.sha256(
            f"{request.url}?{request.query_string()}".encode()
        ).hexdigest()[:10]
        return self.source.fetch(
            self.source_id,
            f"{kind}:{key}:{digest}",
            request,
            refresh=self.refresh,
            ext=ext,
            meta={"source": self.source_id, "kind": kind, "key": key},
        )

    def _record(self, kind: str, property_id: str, request: HttpRequest, content: bytes) -> str:
        record = self.provenance.record(
            provider=self.source_id,
            territory="multi",
            kind=kind,
            source_version=self.source_version(),
            crs=str(self.config.get("default_crs", "EPSG:4326")),
            refcat=property_id,
            url=request.url,
            request_params=request.params,
            offline=self.source.offline,
            content=content,
        )
        return record.provenance_id
