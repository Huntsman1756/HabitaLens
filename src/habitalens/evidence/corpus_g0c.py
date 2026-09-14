"""Corpus preregistrado de G0-C (24 propiedades), congelado en corpus_g0c.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

_CORPUS_FILE = Path(__file__).parent / "corpus_g0c.json"


@dataclass(frozen=True)
class CorpusPropertyG0C:
    id: str
    block: str
    provider_id: str
    refcat: str
    label: str
    context: str
    source_crs: str


def load_corpus(path: Path | None = None) -> tuple[CorpusPropertyG0C, ...]:
    data = json.loads((path or _CORPUS_FILE).read_text(encoding="utf-8"))
    return tuple(
        CorpusPropertyG0C(
            id=entry["id"],
            block=entry["block"],
            provider_id=entry["provider_id"],
            refcat=entry["refcat"],
            label=entry["label"],
            context=entry["context"],
            source_crs=entry["source_crs"],
        )
        for entry in data["entries"]
    )


CORPUS_G0C: tuple[CorpusPropertyG0C, ...] = load_corpus()


def property_by_id(property_id: str) -> CorpusPropertyG0C:
    for item in CORPUS_G0C:
        if item.id == property_id:
            return item
    raise KeyError(f"propiedad fuera del corpus G0-C: {property_id}")
