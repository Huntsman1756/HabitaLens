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
EVIDENCE_G0C = DATA / "evidence_g0c"
PROPERTIES_G0C = DATA / "properties_g0c"

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
    """Fuentes G0-B (snczi, eprtr, csn_radon) con fixtures G0-B congeladas."""

    from habitalens.sources import get_source

    mapping = {key: EVIDENCE / name for key, name in evidence_index().items()}
    fixture_source = FixtureSource(mapping)
    sources = {}
    for source_id in ("snczi", "eprtr", "csn_radon"):
        source = get_source(
            source_id,
            cache=CacheStore(tmp_path / source_id),
            provenance=ProvenanceRecorder(tmp_path / source_id),
        )
        source.source = fixture_source
        sources[source_id] = source
    return sources


def evidence_golden(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def g0c_index() -> dict[str, str]:
    return json.loads((EVIDENCE_G0C / "_index.json").read_text(encoding="utf-8"))


def g0c_corpus() -> list[dict]:
    path = DATA.parents[2] / "src" / "habitalens" / "evidence" / "corpus_g0c.json"
    return json.loads(path.read_text(encoding="utf-8"))["entries"]


def load_g0c_property(property_id: str) -> tuple[str, str]:
    wkt = (PROPERTIES_G0C / f"{property_id}.wkt").read_text(encoding="utf-8")
    source_crs = next(e["source_crs"] for e in g0c_corpus() if e["id"] == property_id)
    return wkt, source_crs


def make_g0c_sources(tmp_path: Path):
    from habitalens.sources import get_source

    mapping = {key: EVIDENCE_G0C / name for key, name in g0c_index().items()}
    fixture_source = FixtureSource(mapping)
    sources = {}
    for source_id in ("siu", "ncse02", "btn"):
        source = get_source(
            source_id,
            cache=CacheStore(tmp_path / source_id),
            provenance=ProvenanceRecorder(tmp_path / source_id),
        )
        source.source = fixture_source
        sources[source_id] = source
    return sources


def g0c_golden(name: str) -> dict:
    return json.loads((EVIDENCE_G0C / name).read_text(encoding="utf-8"))


def make_report_manifest(tmp_path: Path, property_ids=None, report_id: str = "test-report"):
    from habitalens.evidence import EvidenceEngine
    from habitalens.evidence.corpus_g0c import CORPUS_G0C
    from habitalens.report import build_manifest
    from habitalens.report.manifest import property_entry

    engine = EvidenceEngine(sources=make_g0c_sources(tmp_path))
    entries = []
    for item in CORPUS_G0C:
        if property_ids is not None and item.id not in property_ids:
            continue
        wkt, source_crs = load_g0c_property(item.id)
        evidence = engine.evaluate(item, wkt, source_crs)
        entries.append(
            property_entry(
                {
                    "id": item.id,
                    "label": item.label,
                    "provider_id": item.provider_id,
                    "refcat": item.refcat,
                    "context": item.context,
                },
                evidence,
            )
        )
    return build_manifest(
        report_id=report_id, entries=entries, generated_at="2026-09-14T00:00:00Z"
    )
