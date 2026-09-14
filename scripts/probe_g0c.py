"""Probe de cierre G0-C: gates por fuente + casos UNAVAILABLE/INCONCLUSIVE."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.evidence import EvidenceEngine
from habitalens.evidence.corpus_g0c import CORPUS_G0C, CorpusPropertyG0C
from habitalens.provenance import ProvenanceRecorder
from habitalens.sources import get_source

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / ".habitalens-g0c"
PROPERTIES = ROOT / "tests" / "fixtures" / "data" / "properties_g0c"

CONTROLS = (
    (CorpusPropertyG0C("ctrl_granada_ncse", "C", "n/a", "n/a", "Granada", "control", "EPSG:4326"),
     "POLYGON((-3.6065 37.1775, -3.6055 37.1775, -3.6055 37.1785, -3.6065 37.1785, -3.6065 37.1775))"),
    (CorpusPropertyG0C("ctrl_madrid_ncse_null", "C", "n/a", "n/a", "Madrid", "control", "EPSG:4326"),
     "POLYGON((-3.7043 40.4163, -3.7033 40.4163, -3.7033 40.4173, -3.7043 40.4173, -3.7043 40.4163))"),
    (CorpusPropertyG0C("ctrl_madrid_btn", "C", "n/a", "n/a", "Madrid", "control", "EPSG:4326"),
     "POLYGON((-3.7118 40.4062, -3.7108 40.4062, -3.7108 40.4072, -3.7118 40.4072, -3.7118 40.4062))"),
    (CorpusPropertyG0C("ctrl_madrid_siu", "C", "n/a", "n/a", "Madrid", "control", "EPSG:4326"),
     "POLYGON((-3.7055 40.4155, -3.7045 40.4155, -3.7045 40.4165, -3.7055 40.4165, -3.7055 40.4155))"),
)


def main() -> None:
    cache = CacheStore(CACHE_ROOT)
    provenance = ProvenanceRecorder(CACHE_ROOT)
    sources = {
        sid: get_source(sid, cache=cache, provenance=provenance)
        for sid in ("siu", "ncse02", "btn")
    }
    for source in sources.values():
        print(f"source {source.source_id}: usable={source.usable} version={source.source_version()}")

    engine = EvidenceEngine(sources=sources)
    print("\n=== controles ===")
    for control, wkt in CONTROLS:
        report = engine.evaluate(control, wkt, control.source_crs)
        pretty = [
            (f.kind, f.status.value, f.observed, round(f.value, 1) if isinstance(f.value, (int, float)) else f.value)
            for f in report.findings
        ]
        print(control.id, pretty)

    print("\n=== corpus (24) ===")
    counters = {sid: Counter() for sid in sources}
    hard: list[str] = []
    for item in CORPUS_G0C:
        wkt = (PROPERTIES / f"{item.id}.wkt").read_text(encoding="utf-8")
        report = engine.evaluate(item, wkt, item.source_crs)
        for finding in report.findings:
            counters[finding.source][finding.status.value] += 1
            if finding.status.value in {"unavailable", "inconclusive"}:
                hard.append(
                    f"  {item.id} {finding.source} {finding.kind}: {finding.status.value} "
                    f"({finding.note})"
                )
    for source_id, counter in counters.items():
        print(f"{source_id}: {dict(counter)}")
    print("\ncasos UNAVAILABLE/INCONCLUSIVE:")
    for line in hard:
        print(line)


if __name__ == "__main__":
    main()
