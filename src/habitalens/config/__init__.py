"""Configuracion versionada de endpoints. No se dispersan URLs por el codigo."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml


@lru_cache(maxsize=1)
def load_endpoints() -> dict:
    path = Path(__file__).parent / "endpoints.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def provider_config(provider_id: str) -> dict:
    data = load_endpoints()
    try:
        return data["providers"][provider_id]
    except KeyError as exc:  # pragma: no cover - defensive
        raise KeyError(f"proveedor sin configuracion de endpoints: {provider_id}") from exc


__all__ = ["load_endpoints", "provider_config"]
