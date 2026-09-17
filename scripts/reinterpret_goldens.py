"""Reinterpret frozen fixture responses under the corrected source semantics.

Updates only the interpretation fields (status/observed/value/unit/note/...) in
the golden result records; provenance_id and retrieved_at from the original
live capture are preserved.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tests.conftest import (  # noqa: E402
    DATA,
    load_g0c_property,
    load_property,
    make_evidence_sources,
    make_g0c_sources,
)

from habitalens.evidence import CORPUS, CorpusProperty, EvidenceEngine  # noqa: E402
from habitalens.evidence.corpus_g0c import CORPUS_G0C, CorpusPropertyG0C  # noqa: E402

SEMANTIC = (
    "source", "source_version", "kind", "status", "observed", "value", "unit",
    "source_crs", "operational_crs", "method", "inputs", "note",
)

G0B_CONTROLS = (
    ("control_ebro_flood", "EPSG:4326"),
    ("control_bilbao_plant", "EPSG:4326"),
)
G0C_CONTROLS = (
    ("ctrl_granada_ncse", "POLYGON((-3.6065 37.1775, -3.6055 37.1775, -3.6055 37.1785, -3.6065 37.1785, -3.6065 37.1775))"),
    ("ctrl_madrid_ncse_null", "POLYGON((-3.7043 40.4163, -3.7033 40.4163, -3.7033 40.4173, -3.7043 40.4173, -3.7043 40.4163))"),
    ("ctrl_madrid_btn", "POLYGON((-3.7118 40.4062, -3.7108 40.4062, -3.7108 40.4072, -3.7118 40.4072, -3.7118 40.4062))"),
    ("ctrl_madrid_siu", "POLYGON((-3.7055 40.4155, -3.7045 40.4155, -3.7045 40.4165, -3.7055 40.4165, -3.7055 40.4155))"),
)


def merge(golden: dict, report) -> None:
    replay = {f["kind"]: f for f in report.model_dump(mode="json")["findings"]}
    merged = []
    for finding in golden["findings"]:
        r = replay.pop(finding["kind"], None)
        if r is None:
            continue  # kind no longer emitted under corrected semantics
        merged.append({
            **{field: r[field] for field in SEMANTIC},
            "property_id": finding["property_id"],
            "provenance_id": finding["provenance_id"],
            "retrieved_at": finding["retrieved_at"],
        })
    merged.extend(replay.values())  # kinds nuevos (p.ej. btn.status)
    golden["source_crs"] = report.source_crs
    golden["operational_crs"] = report.operational_crs
    golden["findings"] = merged


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        results_path = DATA / "evidence" / "_results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        engine = EvidenceEngine(sources=make_evidence_sources(tmp / "g0b"))
        for item in CORPUS:
            wkt, crs = load_property(item.id)
            merge(results[item.id], engine.evaluate(item, wkt, crs))
        controls_path = DATA / "evidence" / "_controls.json"
        controls = json.loads(controls_path.read_text(encoding="utf-8"))
        for name, crs in G0B_CONTROLS:
            wkt = (DATA / "properties" / f"{name}.wkt").read_text(encoding="utf-8")
            prop = CorpusProperty(name, "n/a", "n/a", name, "n/a", "control")
            merge(controls[name], engine.evaluate(prop, wkt, crs))
        results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        controls_path.write_text(json.dumps(controls, indent=2, ensure_ascii=False), encoding="utf-8")

        results_path = DATA / "evidence_g0c" / "_results.json"
        results = json.loads(results_path.read_text(encoding="utf-8"))
        engine = EvidenceEngine(sources=make_g0c_sources(tmp / "g0c"))
        for item in CORPUS_G0C:
            wkt, crs = load_g0c_property(item.id)
            merge(results[item.id], engine.evaluate(item, wkt, crs))
        controls_path = DATA / "evidence_g0c" / "_controls.json"
        controls = json.loads(controls_path.read_text(encoding="utf-8"))
        for cid, wkt in G0C_CONTROLS:
            prop = CorpusPropertyG0C(cid, "C", "n/a", "n/a", cid, "control", "EPSG:4326")
            merge(controls[cid], engine.evaluate(prop, wkt, "EPSG:4326"))
        results_path.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        controls_path.write_text(json.dumps(controls, indent=2, ensure_ascii=False), encoding="utf-8")
    print("goldens reinterpreted")


if __name__ == "__main__":
    main()
