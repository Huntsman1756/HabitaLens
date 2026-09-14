"""Probe live G0-B: gates por fuente + replay del corpus preregistrado."""

from __future__ import annotations

import json
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.evidence import CORPUS, CorpusProperty, EvidenceEngine
from habitalens.provenance import ProvenanceRecorder
from habitalens.sources import all_sources

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "fixtures" / "data"
PROPERTIES = DATA / "properties"

CONTROLS = (
    (
        CorpusProperty("control_ebro_flood", "n/a", "n/a", "Ebro", "n/a", "control"),
        "POLYGON((-0.882 41.658, -0.878 41.658, -0.878 41.662, -0.882 41.662, -0.882 41.658))",
    ),
    (
        CorpusProperty("control_bilbao_plant", "n/a", "n/a", "ELMET", "n/a", "control"),
        "POLYGON((-2.9921 43.3688, -2.9911 43.3688, -2.9911 43.3696, -2.9921 43.3696, -2.9921 43.3688))",
    ),
)


def _summary(report) -> str:
    parts = []
    for finding in report.findings:
        if finding.status.value == "observed":
            parts.append(f"{finding.kind}={finding.observed}")
        elif finding.status.value == "derived":
            value = finding.value
            value = round(value, 1) if isinstance(value, (int, float)) else value
            parts.append(f"{finding.kind}={value}{finding.unit or ''}")
        else:
            parts.append(f"{finding.kind}:{finding.status.value}")
    return " | ".join(parts)


def main() -> None:
    cache = CacheStore(ROOT / ".habitalens-g0b")
    provenance = ProvenanceRecorder(ROOT / ".habitalens-g0b")
    sources = all_sources(cache=cache, provenance=provenance)
    for source in sources.values():
        print(f"source {source.source_id}: usable={source.usable} version={source.source_version()}")
    engine = EvidenceEngine(sources=sources)

    print("\n=== controles (live) ===")
    results = {}
    for corpus_property, wkt in CONTROLS:
        report = engine.evaluate(corpus_property, wkt, "EPSG:4326")
        results[corpus_property.id] = report.model_dump(mode="json")
        print(f"{corpus_property.id}: {_summary(report)}")

    print("\n=== corpus preregistrado (live) ===")
    for item in CORPUS:
        wkt, source_crs = load_property(item.id)
        report = engine.evaluate(item, wkt, source_crs)
        results[item.id] = report.model_dump(mode="json")
        print(f"{item.id:24s} [{source_crs} -> {report.operational_crs}] {_summary(report)}")

    (ROOT / "probe_g0b_output.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_property(name: str) -> tuple[str, str]:
    wkt = (PROPERTIES / f"{name}.wkt").read_text(encoding="utf-8")
    meta = json.loads((PROPERTIES / f"{name}.json").read_text(encoding="utf-8"))
    return wkt, meta["source_crs"]


if __name__ == "__main__":
    main()
