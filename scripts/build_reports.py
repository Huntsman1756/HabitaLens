"""G0-D: construye manifests de evidencia y renderiza informes HTML/PDF.

Usa las fixtures offline de G0-C (no toca la red). El manifest es la fuente de
verdad; HTML y PDF se renderizan desde el mismo view model.
"""

from __future__ import annotations

import json
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.evidence import EvidenceEngine
from habitalens.evidence.corpus_g0c import CORPUS_G0C
from habitalens.net import FixtureSource
from habitalens.provenance import ProvenanceRecorder
from habitalens.report import build_manifest, generate_report
from habitalens.report.manifest import property_entry
from habitalens.sources import get_source

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "fixtures" / "data"
EVIDENCE = DATA / "evidence_g0c"
PROPERTIES = DATA / "properties_g0c"
OUT = ROOT / "reports"
GENERATED_AT = "2026-09-14T00:00:00Z"


def _sources(tmp_path: Path):
    index = json.loads((EVIDENCE / "_index.json").read_text(encoding="utf-8"))
    fixture_source = FixtureSource({key: EVIDENCE / name for key, name in index.items()})
    sources = {}
    for source_id in ("siu", "ncse02", "btn"):
        source = get_source(
            source_id, cache=CacheStore(tmp_path / source_id), provenance=ProvenanceRecorder(tmp_path / source_id)
        )
        source.source = fixture_source
        sources[source_id] = source
    return sources


def main() -> None:
    tmp = ROOT / ".habitalens-report"
    engine = EvidenceEngine(sources=_sources(tmp))
    entries = []
    for item in CORPUS_G0C:
        wkt = (PROPERTIES / f"{item.id}.wkt").read_text(encoding="utf-8")
        evidence = engine.evaluate(item, wkt, item.source_crs)
        entries.append(
            property_entry(
                {"id": item.id, "label": item.label, "provider_id": item.provider_id, "refcat": item.refcat, "context": item.context},
                evidence,
            )
        )
    manifest = build_manifest(report_id="g0c-corpus", entries=entries, generated_at=GENERATED_AT)
    artifacts = generate_report(manifest, OUT / "g0c-corpus")
    print("html", artifacts.html_path)
    print("pdf", artifacts.pdf_path, "pages", artifacts.pdf_pages)
    print("manifest", artifacts.manifest_path)
    print("html_sha256", artifacts.html_sha256)


if __name__ == "__main__":
    main()
