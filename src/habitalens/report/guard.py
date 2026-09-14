"""Guard fuerte contra scores/valoraciones agregadas de vivienda (G0-D).

No solo bloquea `overall_score`: cualquier termino equivalente o agregado
tipo semaforo/nota global a nivel de propiedad.
"""

from __future__ import annotations

import re

#: Terminos prohibidos (case-insensitive) en cualquier artefacto publico.
FORBIDDEN_SCORE_TERMS: tuple[str, ...] = (
    "overall_score",
    "risk_score",
    "property_score",
    "global_score",
    "score",
    "rating",
    "grade",
    "overall_status",
    "traffic_light",
    "trafficlight",
    "semaforo",
    "recommendation",
    "recommendations",
    "buy_recommendation",
    "recomendacion",
    "recomendaciones",
    "valoracion_global",
    "valoracion",
    "nota_global",
    "puntuacion",
    "clasificacion_global",
)


class ScoreGuardError(RuntimeError):
    """Aparece un termino de score/valoracion agregada prohibido."""


def find_forbidden_terms(text: str) -> list[str]:
    lowered = text.lower()
    found = []
    for term in FORBIDDEN_SCORE_TERMS:
        if re.search(rf"\b{re.escape(term)}\b", lowered):
            found.append(term)
    return found


def assert_no_score(text: str) -> None:
    found = find_forbidden_terms(text)
    if found:
        raise ScoreGuardError(f"terminos de score prohibidos: {', '.join(sorted(set(found)))}")
