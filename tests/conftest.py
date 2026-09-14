"""Fixtures y utilidades offline. Ningun test realiza llamadas live."""

from __future__ import annotations

from pathlib import Path

import pytest

from habitalens.cache import CacheStore
from habitalens.net import FixtureSource
from habitalens.provenance import ProvenanceRecorder

DATA = Path(__file__).parent / "fixtures" / "data"

# Mapa provider_id -> {clave_de_fetch: fichero de fixture}
PROVIDER_FIXTURES: dict[str, dict[str, str]] = {
    "dgc": {
        "capabilities": "dgc_capabilities.xml",
        "atom-index:parcel-index": "dgc_atom_index.xml",
        "atom-province:17": "dgc_atom_province_17.xml",
        "atom-zip:parcel:17079": "dgc_parcel.gml",
        "building:1707903VK4810F": "dgc_buildings.gml",
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
