"""Corpus G0-C: 24 propiedades congeladas, 10 bloque A + 14 bloque B."""

from __future__ import annotations

from habitalens.cadastre_providers import provider_ids
from habitalens.evidence.corpus_g0c import CORPUS_G0C, property_by_id


def test_corpus_g0c_size_and_uniqueness() -> None:
    assert len(CORPUS_G0C) == 24
    assert len({item.id for item in CORPUS_G0C}) == 24
    assert len({item.refcat for item in CORPUS_G0C}) == 24


def test_corpus_g0c_blocks() -> None:
    blocks = {block: sum(1 for item in CORPUS_G0C if item.block == block) for block in ("A", "B")}
    assert blocks == {"A": 10, "B": 14}


def test_corpus_g0c_providers_valid() -> None:
    for item in CORPUS_G0C:
        assert item.provider_id in provider_ids()
        assert item.source_crs.startswith("EPSG:")


def test_corpus_g0c_lookup() -> None:
    assert property_by_id("g0c07").provider_id == "navarra"
    assert property_by_id("g0c05").provider_id == "bizkaia"
