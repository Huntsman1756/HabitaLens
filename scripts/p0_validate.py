"""P0: metricas calculables sin el juicio humano (controles y trazabilidad).

No captura anuncios: registra el estado de la muestra y evalua los controles
preregistrados con las fixtures congeladas.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "tests" / "fixtures" / "data"

# Controles verdaderos: (artefacto, hallazgo, campo, valor esperado)
TRUE_POSITIVES = (
    ("evidence", "control_ebro_flood", "snczi.flood_q100", "observed", True),
    ("evidence", "control_bilbao_plant", "eprtr.facilities", "observed", True),
    ("evidence_g0c", "ctrl_granada_ncse", "ncse02.hazard", "observed", True),
    ("evidence_g0c", "ctrl_madrid_btn", "btn.roads", "observed", True),
    ("evidence_g0c", "ctrl_madrid_siu", "siu.clase_suelo", "observed", True),
)

# Controles de certeza falsa: NUNCA deben ser OBSERVED.
FALSE_CERTAINTY = (
    ("evidence_g0c", "ctrl_madrid_ncse_null", "ncse02.hazard", "unavailable"),
    ("evidence_g0c", "g0c07", "siu.clase_suelo", "inconclusive"),
)


def _load(folder: str, name: str) -> dict:
    path = DATA / folder / f"_{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _finding(report: dict, kind: str) -> dict:
    return next(f for f in report["findings"] if f["kind"] == kind)


def main() -> None:
    metrics: dict = {}

    recall_hits = 0
    for folder, item, kind, status, observed in TRUE_POSITIVES:
        report = _load(folder, "controls")[item]
        finding = _finding(report, kind)
        ok = finding["status"] == status and finding.get("observed") is observed
        recall_hits += int(ok)
        print(f"TP {item} {kind}: {finding['status']} observed={finding.get('observed')} -> {ok}")
    metrics["known_condition_recall"] = recall_hits / len(TRUE_POSITIVES)
    metrics["true_positives_total"] = len(TRUE_POSITIVES)
    metrics["true_positives_detected"] = recall_hits

    false_certainty = 0
    for folder, item, kind, expected in FALSE_CERTAINTY:
        source = "results" if item.startswith("g0c") and item != "ctrl" else "controls"
        source = "results" if item in {"g0c07"} else "controls"
        report = _load(folder, source)[item]
        finding = _finding(report, kind)
        bad = finding["status"] == "observed" and finding.get("observed") is False
        false_certainty += int(bad)
        print(f"FC {item} {kind}: {finding['status']} -> {'BAD' if bad else 'ok'} (esperado {expected})")
    metrics["false_certainty_incidents"] = false_certainty

    total_findings = 0
    traceable = 0
    for folder, name in (("evidence_g0c", "results"), ("evidence_g0c", "controls")):
        for report in _load(folder, name).values():
            for finding in report["findings"]:
                if finding["status"] in {"observed", "derived"}:
                    total_findings += 1
                    traceable += int(bool(finding.get("provenance_id")))
    metrics["source_traceability"] = (traceable / total_findings) if total_findings else 0.0
    metrics["traceable_findings"] = traceable
    metrics["measurable_findings"] = total_findings

    metrics["sample_status"] = "INACCESSIBLE (Idealista 403 + robots restringe resultados)"
    metrics["actionable_finding_rate"] = None  # requiere revision humana ciega
    metrics["human_review"] = "PENDING"

    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    out = ROOT / "p0_metrics.json"
    out.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
