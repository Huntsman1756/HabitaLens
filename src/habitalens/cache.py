"""Cache local de HabitaLens bajo ``~/.habitalens/cache/``.

Guarda respuestas crudas (XML/GML/JSON) y capas GeoParquet por proveedor. El
refetch es explicito mediante ``--refresh``. La geometria catastral vive aqui,
nunca en los modelos publicos.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path

CACHE_ROOT_ENV = "HABITALENS_CACHE"

_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def default_root() -> Path:
    import os

    override = os.environ.get(CACHE_ROOT_ENV)
    if override:
        return Path(override)
    return Path.home() / ".habitalens"


class CacheMeta(dict):
    """Metadatos de una entrada de cache (provider, fecha, version, CRS, origen)."""


class CacheStore:
    def __init__(self, root: Path | None = None):
        self.root = Path(root) if root is not None else default_root()
        self.raw_dir = self.root / "cache" / "raw"
        self.geo_dir = self.root / "cache" / "geo"
        self.meta_dir = self.root / "cache" / "meta"

    def ensure(self) -> CacheStore:
        for directory in (self.raw_dir, self.geo_dir, self.meta_dir):
            directory.mkdir(parents=True, exist_ok=True)
        return self

    @staticmethod
    def _slug(key: str) -> str:
        return _SAFE.sub("_", key)[:180]

    def raw_path(self, namespace: str, key: str, ext: str = "xml") -> Path:
        directory = self.raw_dir / namespace
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{self._slug(key)}.{ext}"

    def meta_path(self, namespace: str, key: str) -> Path:
        directory = self.meta_dir / namespace
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{self._slug(key)}.json"

    def read_raw(self, namespace: str, key: str, ext: str = "xml") -> bytes | None:
        path = self.raw_path(namespace, key, ext)
        if path.is_file():
            return path.read_bytes()
        return None

    def write_raw(
        self,
        namespace: str,
        key: str,
        content: bytes,
        *,
        ext: str = "xml",
        meta: dict | None = None,
    ) -> Path:
        path = self.raw_path(namespace, key, ext)
        path.write_bytes(content)
        record = {
            "namespace": namespace,
            "key": key,
            "captured_at": datetime.now(UTC).isoformat(),
            "sha256": hashlib.sha256(content).hexdigest(),
            "bytes": len(content),
        }
        if meta:
            record.update(meta)
        self.meta_path(namespace, key).write_text(
            json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return path

    def read_meta(self, namespace: str, key: str) -> dict | None:
        path = self.meta_path(namespace, key)
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
        return None

    def write_geoparquet(self, namespace: str, key: str, frame, meta: dict | None = None) -> Path:
        directory = self.geo_dir / namespace
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{self._slug(key)}.geoparquet"
        frame.to_parquet(path)
        record = {
            "namespace": namespace,
            "key": key,
            "captured_at": datetime.now(UTC).isoformat(),
        }
        if meta:
            record.update(meta)
        self.meta_path(namespace, f"geo_{key}").write_text(
            json.dumps(record, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        return path

    def read_geoparquet(self, namespace: str, key: str):
        import geopandas as gpd

        path = self.geo_dir / namespace / f"{self._slug(key)}.geoparquet"
        if not path.is_file():
            return None
        return gpd.read_parquet(path)

    def clear(self) -> None:
        import shutil

        if self.root.exists():
            shutil.rmtree(self.root, ignore_errors=True)
