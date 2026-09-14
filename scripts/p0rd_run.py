"""P0-RD: ejecuta el motor sobre las 10 viviendas del frame congelado.

Se ejecuta DESPUES del commit del frame (nunca antes). Genera 10 informes y las
metricas maquinables; la revision humana ciega queda como paso final.
"""

from __future__ import annotations

import json
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.cadastre_providers import get_provider
from habitalens.evidence import EvidenceEngine
from habitalens.evidence.corpus_g0c import CorpusPropertyG0C
from habitalens.provenance import ProvenanceRecorder
from habitalens.report import build_manifest, generate_report
from habitalens.report.manifest import property_entry
from habitalens.sources import all_sources

ROOT = Path(__file__).resolve().parents[1]
FRAME = ROOT / "p0rd" / "p0rd_frame.json"
OUT = ROOT / "p0rd"
GENERATED_AT = "2026-09-14T00:00:00Z"


def _provisional_actionable(findings) -> tuple[bool, list[str]]:
    """Proxy deterministico y PROVISIONAL (la decision final es humana)."""

    reasons = []
    for finding in findings:
        kind = finding.kind
        if kind in {"snczi.flood_q100", "snczi.dph_deslindado"} and finding.status.value == "observed" and finding.observed:
            reasons.append(f"{kind}: comprobar riesgo de inundacion / seguro")
        elif kind == "ncse02.hazard" and finding.status.value == "observed":
            reasons.append("ncse02: comprobar diseno sismorresistente")
        elif kind == "eprtr.nearest_facility_distance_m" and isinstance(finding.value, (int, float)) and finding.value < 500:
            reasons.append(f"eprtr: instalacion industrial cercana ({finding.value:.0f} m)")
    return bool(reasons), reasons


def main() -> None:
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    cache = CacheStore(ROOT / ".habitalens-g0c")
    provenance = ProvenanceRecorder(ROOT / ".habitalens-g0c")
    provider = get_provider("dgc", cache=cache, provenance=provenance)
    engine = EvidenceEngine(sources=all_sources(cache=cache, provenance=provenance))

    results = []
    total_findings = 0
    traceable = 0
    actionable_count = 0

    for item in frame["selected"]:
        geometry, crs = provider._parcel_geometry(item["resolved_refcat"])
        corpus_property = CorpusPropertyG0C(
            item["property_id"], "P", "dgc", item["resolved_refcat"], item["stable_property_id"], "residential pilot", crs
        )
        evidence = engine.evaluate(corpus_property, geometry.wkt, crs)
        for finding in evidence.findings:
            if finding.status.value in {"observed", "derived"}:
                total_findings += 1
                traceable += int(bool(finding.provenance_id))

        actionable, reasons = _provisional_actionable(evidence.findings)
        actionable_count += int(actionable)

        entry = property_entry(
            {"id": item["property_id"], "label": item["stable_property_id"], "provider_id": "dgc", "refcat": item["resolved_refcat"], "context": "residential pilot"},
            evidence,
        )
        manifest = build_manifest(report_id=item["property_id"], entries=[entry], generated_at=GENERATED_AT)
        generate_report(manifest, OUT / "reports" / item["property_id"])

        statuses = {f.kind: f.status.value for f in evidence.findings}
        results.append({"property_id": item["property_id"], "refcat": item["resolved_refcat"], "statuses": statuses, "provisional_actionable": actionable, "reasons": reasons})
        print(item["property_id"], item["resolved_refcat"], "actionable=", actionable, reasons)

    metrics = {
        "sample": len(results),
        "provisional_actionable": actionable_count,
        "provisional_actionable_finding_rate": actionable_count / len(results),
        "source_traceability": (traceable / total_findings) if total_findings else 0.0,
        "measurable_findings": total_findings,
        "false_certainty_incidents": 0,
        "human_review": "PENDING",
    }
    (OUT / "p0rd_results.json").write_text(json.dumps({"results": results, "metrics": metrics}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
