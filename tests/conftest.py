"""Fixtures y utilidades offline. Ningun test realiza llamadas live."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from habitalens.cache import CacheStore
from habitalens.net import FixtureSource
from habitalens.provenance import ProvenanceRecorder

DATA = Path(__file__).parent / "fixtures" / "data"
EVIDENCE = DATA / "evidence"
PROPERTIES = DATA / "properties"

# Mapa provider_id -> {clave_de_fetch: fichero de fixture}
PROVIDER_FIXTURES: dict[str, dict[str, str]] = {
    "dgc": {
        "capabilities": "dgc_capabilities.xml",
        "parcel:1707903VK4810F": "dgc_parcel.gml",
        "building:1707903VK4810F": "dgc_buildings.gml",
        "dnprc:1707903VK4810F": "dgc_dnprc.xml",
        "dnprc:0000000XX0000X": "dgc_dnprc_negative.xml",
    },
    "navarra": {
        "capabilities": "navarra_capabilities.xml",
        "parcel:001010001": "navarra_parcel.xml",
        "building:001010001": "navarra_buildings.xml",
    },
    "bizkaia": {
        "capabilities": "bizkaia_capabilities.xml",
        "atom-index:parcel-index": "bizkaia_atom_index.xml",
        "atom-zip:parcel:020": "bizkaia_parcel.gml",
        "building:48.020.1619.04006": "bizkaia_buildings.xml",
    },
    "gipuzkoa": {
        "capabilities": "gipuzkoa_capabilities.xml",
        "parcel:8594149": "gipuzkoa_parcel.xml",
        "building:8594149": "gipuzkoa_buildings.xml",
    },
    "araba": {
        "capabilities": "araba_capabilities.xml",
        "parcel:64010007": "araba_parcel.xml",
        "building:64010007": "araba_buildings.xml",
    },
}

CONTRACT_CASES = [
    ("dgc", "1707903VK4810F"),
    ("navarra", "001010001"),
    ("bizkaia", "48.020.1619.04006"),
    ("gipuzkoa", "8594149"),
    ("araba", "64010007"),
]


def build_source(provider_id: str, extra: dict[str, str | Path | bytes] | None = None):
    mapping: dict[str, str | Path | bytes] = {}
    for key, filename in PROVIDER_FIXTURES[provider_id].items():
        mapping[f"{provider_id}:{key}"] = DATA / filename
    if extra:
        mapping.update(extra)
    return FixtureSource(mapping)


def make_provider(provider_id: str, tmp_path: Path, extra=None):
    from habitalens.cadastre_providers import get_provider

    return get_provider(
        provider_id,
        source=build_source(provider_id, extra),
        cache=CacheStore(tmp_path / provider_id),
        provenance=ProvenanceRecorder(tmp_path / provider_id),
        persist=True,
    )


@pytest.fixture
def data_dir() -> Path:
    return DATA


def evidence_index() -> dict[str, str]:
    return json.loads((EVIDENCE / "_index.json").read_text(encoding="utf-8"))


def load_property(name: str) -> tuple[str, str]:
    wkt = (PROPERTIES / f"{name}.wkt").read_text(encoding="utf-8")
    meta = json.loads((PROPERTIES / f"{name}.json").read_text(encoding="utf-8"))
    return wkt, meta["source_crs"]


def make_evidence_sources(tmp_path: Path):
    from habitalens.sources import all_sources

    mapping = {key: EVIDENCE / name for key, name in evidence_index().items()}
    fixture_source = FixtureSource(mapping)
    sources = all_sources(
        cache=CacheStore(tmp_path / "cache"), provenance=ProvenanceRecorder(tmp_path)
    )
    for source in sources.values():
        source.source = fixture_source
    return sources


def evidence_golden(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))
