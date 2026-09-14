"""Captura live de G0-B: geometria de las 8 propiedades + respuestas de fuentes.

Escribe fixtures internas (WKT de propiedad + JSON de fuentes) para los tests
offline. La geometria de propiedad es interna de test; nunca se expone.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.cadastre_providers import get_provider
from habitalens.evidence import CORPUS, CorpusProperty, EvidenceEngine
from habitalens.net import HttpRequest, HttpSource
from habitalens.provenance import ProvenanceRecorder
from habitalens.sources import all_sources

#: Controles positivos (no forman parte del corpus preregistrado).
CONTROLS: tuple[tuple[CorpusProperty, str, str], ...] = (
    (
        CorpusProperty("control_ebro_flood", "n/a", "n/a", "Ebro-Zaragoza", "n/a", "control"),
        "POLYGON((-0.882 41.658, -0.878 41.658, -0.878 41.662, -0.882 41.662, -0.882 41.658))",
        "EPSG:4326",
    ),
    (
        CorpusProperty("control_bilbao_plant", "n/a", "n/a", "Bilbao-ELMET", "n/a", "control"),
        "POLYGON((-2.9921 43.3688, -2.9911 43.3688, -2.9911 43.3696, -2.9921 43.3696, -2.9921 43.3688))",
        "EPSG:4326",
    ),
)

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / ".habitalens-g0b"
DATA = ROOT / "tests" / "fixtures" / "data"
PROPERTIES = DATA / "properties"
EVIDENCE = DATA / "evidence"


class MirrorSource(HttpSource):
    """Delegado live que ademas copia cada respuesta a fixtures."""

    def __init__(self, cache: CacheStore, out_dir: Path):
        super().__init__(cache=cache)
        self.out_dir = out_dir
        self.index: dict[str, str] = {}

    def fetch(self, namespace, key, request: HttpRequest, **kwargs):
        data = super().fetch(namespace, key, request, **kwargs)
        ext = kwargs.get("ext", "json")
        safe = f"{namespace}__{key}".replace(":", "_").replace(",", "_").replace(".", "_")
        safe = safe.replace("/", "_")
        name = f"{safe}.{ext}.gz"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / name).write_bytes(gzip.compress(data))
        self.index[f"{namespace}:{key}"] = name
        return data


def main() -> None:
    PROPERTIES.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    cache = CacheStore(CACHE_ROOT)
    provenance = ProvenanceRecorder(CACHE_ROOT)

    geometries: dict[str, tuple[str, str]] = {}
    for item in CORPUS:
        provider = get_provider(
            item.provider_id, cache=cache, provenance=provenance, persist=True
        )
        provider.get_parcel(item.refcat)
        geometry, crs = provider._parcel_geometry(item.refcat)
        if geometry is None:
            raise SystemExit(f"sin geometria para {item.id} ({item.refcat})")
        wkt = geometry.wkt
        (PROPERTIES / f"{item.id}.wkt").write_text(wkt, encoding="utf-8")
        (PROPERTIES / f"{item.id}.json").write_text(
            json.dumps({"property_id": item.id, "source_crs": crs, "refcat": item.refcat}),
            encoding="utf-8",
        )
        geometries[item.id] = (wkt, crs)
        print(f"{item.id}: {item.provider_id} {item.refcat} crs={crs}")

    mirror = MirrorSource(cache, EVIDENCE)
    sources = all_sources(cache=cache, provenance=provenance)
    for source in sources.values():
        source.source = mirror
    engine = EvidenceEngine(sources=sources)

    results = {}
    for item in CORPUS:
        wkt, crs = geometries[item.id]
        report = engine.evaluate(item, wkt, crs)
        results[item.id] = report.model_dump(mode="json")
        statuses = [(f.kind, f.status.value) for f in report.findings]
        print(item.id, report.operational_crs, statuses)

    controls = {}
    for corpus_property, wkt, crs in CONTROLS:
        (PROPERTIES / f"{corpus_property.id}.wkt").write_text(wkt, encoding="utf-8")
        report = engine.evaluate(corpus_property, wkt, crs)
        controls[corpus_property.id] = report.model_dump(mode="json")
        print(corpus_property.id, [(f.kind, f.status.value) for f in report.findings])

    (EVIDENCE / "_index.json").write_text(
        json.dumps(mirror.index, indent=2, sort_keys=True), encoding="utf-8"
    )
    (EVIDENCE / "_results.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (EVIDENCE / "_controls.json").write_text(
        json.dumps(controls, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("fixtures escritas en", EVIDENCE)


if __name__ == "__main__":
    main()
