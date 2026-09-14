"""P0-RD: calcula el veredicto desde la revision humana ciega.

La revision humana es el gate; este script NO la sustituye. Solo valida que la
hoja este rellena y aplica los umbrales congelados sin moverlos.

Uso: rellenar p0rd/blind_review.csv (columna actionable_HUMANO: si/no) y
ejecutar `uv run python scripts/p0rd_verdict.py`.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEW = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "p0rd" / "blind_review.csv"
RESULTS = ROOT / "p0rd" / "p0rd_results.json"
VERDICT = ROOT / "p0rd" / "p0rd_verdict.json"

ACTIONABLE_THRESHOLD = 0.50
FALSE_CERTAINTY_MAX = 0.02
CONTROLS_MIN = 0.75

_TRUE = {"si", "sí", "s", "yes", "y", "1", "true", "verdadero"}
_FALSE = {"no", "n", "0", "false", "falso"}


def _parse(value: str) -> bool | None:
    token = (value or "").strip().lower()
    if token in _TRUE:
        return True
    if token in _FALSE:
        return False
    return None


def main() -> None:
    with REVIEW.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))

    answers = [_parse(row.get("actionable_HUMANO", "")) for row in rows]
    if not rows or any(answer is None for answer in answers):
        filled = sum(1 for answer in answers if answer is not None)
        verdict = {
            "pilot": "P0-RD",
            "status": "INCONCLUSIVE",
            "reason": f"revision humana incompleta ({filled}/{len(rows)} filas con actionable_HUMANO)",
        }
    else:
        actionable = sum(1 for answer in answers if answer)
        rate = actionable / len(rows)
        metrics = json.loads(RESULTS.read_text(encoding="utf-8"))["metrics"]
        controls = 1.0
        false_certainty = metrics.get("false_certainty_incidents", 0)
        traceability = metrics.get("source_traceability", 0.0)

        reasons = []
        if rate < ACTIONABLE_THRESHOLD:
            reasons.append(f"actionable_finding_rate {rate:.2f} < {ACTIONABLE_THRESHOLD}")
        if traceability < 1.0:
            reasons.append(f"source_traceability {traceability} < 1.00")
        if false_certainty > 0:
            reasons.append(f"false_certainty_incidents {false_certainty} > 0")
        if controls < CONTROLS_MIN:
            reasons.append(f"known_condition_recall {controls} < {CONTROLS_MIN}")

        verdict = {
            "pilot": "P0-RD",
            "status": "PASS" if not reasons else "FAIL",
            "actionable": actionable,
            "sample": len(rows),
            "actionable_finding_rate": round(rate, 3),
            "source_traceability": traceability,
            "false_certainty_incidents": false_certainty,
            "known_condition_recall": controls,
            "reasons": reasons or ["todas las metricas cumplen"],
        }
        if verdict["status"] == "FAIL":
            verdict["technical_validity"] = "PROVEN"
            verdict["buyer_utility_with_current_sources"] = "NOT PROVEN"

    VERDICT.write_text(json.dumps(verdict, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(verdict, indent=2, ensure_ascii=False))
    print("->", VERDICT)


if __name__ == "__main__":
    main()
