"""Registro append-only de provenance en ``~/.habitalens/provenance/``.

Se registra la version/esquema realmente observado por proveedor, no una
suposicion. Soporta modo live y modo fixture (offline) para trazabilidad.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provenance_id: str
    provider: str
    territory: str
    kind: str
    refcat: str | None = None
    url: str | None = None
    request_params: tuple[tuple[str, str], ...] = ()
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    source_version: str
    crs: str
    offline: bool = False
    fixture: str | None = None
    cache_path: str | None = None
    content_sha256: str | None = None


def _new_id() -> str:
    return uuid.uuid4().hex[:16]


class ProvenanceRecorder:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root is not None else Path.home() / ".habitalens"
        self.dir = self.root / "provenance"
        self.path = self.dir / "provenance.jsonl"

    def record(
        self,
        *,
        provider: str,
        territory: str,
        kind: str,
        source_version: str,
        crs: str,
        refcat: str | None = None,
        url: str | None = None,
        request_params: tuple[tuple[str, str], ...] = (),
        offline: bool = False,
        fixture: str | None = None,
        cache_path: str | None = None,
        content: bytes | None = None,
    ) -> ProvenanceRecord:
        digest = hashlib.sha256(content).hexdigest() if content is not None else None
        record = ProvenanceRecord(
            provenance_id=_new_id(),
            provider=provider,
            territory=territory,
            kind=kind,
            refcat=refcat,
            url=url,
            request_params=tuple(request_params),
            source_version=source_version,
            crs=crs,
            offline=offline,
            fixture=fixture,
            cache_path=cache_path,
            content_sha256=digest,
        )
        self.dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(record.model_dump_json() + "\n")
        return record

    def load(self) -> list[ProvenanceRecord]:
        if not self.path.is_file():
            return []
        records = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(ProvenanceRecord.model_validate(json.loads(line)))
        return records
