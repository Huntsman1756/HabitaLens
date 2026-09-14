"""Registro de fuentes de evidencia G0-B."""

from __future__ import annotations

from habitalens.sources.base import EvidenceSource
from habitalens.sources.btn.source import BtnSource
from habitalens.sources.csn_radon.source import CsnRadonSource
from habitalens.sources.eprtr.source import EprtrSource
from habitalens.sources.ncse02.source import Ncse02Source
from habitalens.sources.siu.source import SiuSource
from habitalens.sources.snczi.source import SncziSource

_SOURCE_TYPES: dict[str, type[EvidenceSource]] = {
    "snczi": SncziSource,
    "eprtr": EprtrSource,
    "csn_radon": CsnRadonSource,
    "siu": SiuSource,
    "ncse02": Ncse02Source,
    "btn": BtnSource,
}


def source_ids() -> list[str]:
    return list(_SOURCE_TYPES)


def get_source(source_id: str, **kwargs) -> EvidenceSource:
    try:
        source_type = _SOURCE_TYPES[source_id]
    except KeyError as exc:
        raise KeyError(f"fuente desconocida: {source_id}") from exc
    return source_type(**kwargs)


def all_sources(**kwargs) -> dict[str, EvidenceSource]:
    return {sid: get_source(sid, **kwargs) for sid in source_ids()}
