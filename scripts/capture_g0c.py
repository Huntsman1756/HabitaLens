"""Captura live G0-C: SIU + NCSE-02 + BTN sobre el corpus de 24 + controles."""

from __future__ import annotations

import gzip
import json
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.evidence import EvidenceEngine
from habitalens.evidence.corpus_g0c import CORPUS_G0C, CorpusPropertyG0C
from habitalens.net import HttpRequest, HttpSource
from habitalens.provenance import ProvenanceRecorder
from habitalens.sources import get_source

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / ".habitalens-g0c"
PROPERTIES = ROOT / "tests" / "fixtures" / "data" / "properties_g0c"
EVIDENCE = ROOT / "tests" / "fixtures" / "data" / "evidence_g0c"

SOURCE_IDS = ("siu", "ncse02", "btn")

CONTROLS = (
    (
        CorpusPropertyG0C("ctrl_granada_ncse", "C", "n/a", "n/a", "Granada", "control", "EPSG:4326"),
        "POLYGON((-3.6065 37.1775, -3.6055 37.1775, -3.6055 37.1785, -3.6065 37.1785, -3.6065 37.1775))",
    ),
    (
        CorpusPropertyG0C("ctrl_madrid_ncse_null", "C", "n/a", "n/a", "Madrid", "control", "EPSG:4326"),
        "POLYGON((-3.7043 40.4163, -3.7033 40.4163, -3.7033 40.4173, -3.7043 40.4173, -3.7043 40.4163))",
    ),
    (
        CorpusPropertyG0C("ctrl_madrid_btn", "C", "n/a", "n/a", "Madrid RoadLink", "control", "EPSG:4326"),
        "POLYGON((-3.7118 40.4062, -3.7108 40.4062, -3.7108 40.4072, -3.7118 40.4072, -3.7118 40.4062))",
    ),
    (
        CorpusPropertyG0C("ctrl_madrid_siu", "C", "n/a", "n/a", "Madrid SIU", "control", "EPSG:4326"),
        "POLYGON((-3.7055 40.4155, -3.7045 40.4155, -3.7045 40.4165, -3.7055 40.4165, -3.7055 40.4155))",
    ),
)


class MirrorSource(HttpSource):
    def __init__(self, cache: CacheStore, out_dir: Path):
        super().__init__(cache=cache)
        self.out_dir = out_dir
        self.index: dict[str, str] = {}

    def fetch(self, namespace, key, request: HttpRequest, **kwargs):
        data = super().fetch(namespace, key, request, **kwargs)
        ext = kwargs.get("ext", "json")
        safe = f"{namespace}__{key}".replace(":", "_").replace(",", "_").replace(".", "_")
        safe = safe.replace("/", "_").replace("#", "_")
        name = f"{safe}.{ext}.gz"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        (self.out_dir / name).write_bytes(gzip.compress(data))
        self.index[f"{namespace}:{key}"] = name
        return data


def _wkt(name: str) -> str:
    return (PROPERTIES / f"{name}.wkt").read_text(encoding="utf-8")


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    cache = CacheStore(CACHE_ROOT)
    provenance = ProvenanceRecorder(CACHE_ROOT)
    mirror = MirrorSource(cache, EVIDENCE)
    sources = {}
    for source_id in SOURCE_IDS:
        source = get_source(source_id, cache=cache, provenance=provenance)
        source.source = mirror
        sources[source_id] = source
    engine = EvidenceEngine(sources=sources)

    results = {}
    for item in CORPUS_G0C:
        report = engine.evaluate(item, _wkt(item.id), item.source_crs)
        results[item.id] = report.model_dump(mode="json")
        print(item.id, item.provider_id, item.refcat, [(f.kind, f.status.value) for f in report.findings])

    controls = {}
    for control, wkt in CONTROLS:
        report = engine.evaluate(control, wkt, control.source_crs)
        controls[control.id] = report.model_dump(mode="json")
        print(control.id, [(f.kind, f.status.value, f.value) for f in report.findings])

    (EVIDENCE / "_index.json").write_text(json.dumps(mirror.index, indent=2, sort_keys=True), encoding="utf-8")
    (EVIDENCE / "_results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    (EVIDENCE / "_controls.json").write_text(json.dumps(controls, indent=2, ensure_ascii=False), encoding="utf-8")
    print("fixtures escritas en", EVIDENCE)


if __name__ == "__main__":
    main()
