# P0-RD — DGC Residential Utility Pilot: informe

- Fecha: 2026-09-14.
- Preregistro: `docs/p0-rd-preregistration.md`.
- Frame congelado **antes** de cualquier consulta de riesgo: commit `1fe2f3a`
  (`p0rd/p0rd_frame.json`).
- **Veredicto: P0-RD = INCONCLUSIVE** (revision humana ciega pendiente), con una
  senal provisional **desfavorable** (lectura estricta ~1/10).

## 1. Frame

- Pool DGC congelado `SHA256 33b709872bd0af04a5e2b89f523b2a365729525d8c1c784ca8311b89c7e96fec`
  (36.180 viviendas residenciales).
- Seleccion `SHA256("habitalens-p0rd-v1|"+stable_property_id)` ascendente, 10
  primeras resolubles, **0 sustituciones**.
- 10 refcats: `3865207WE0036N, 7330630DG1073D, 6326304UF9762N, 0170012UK9207S,
  6424509DG1062B, 5049117WE0054N, 9321008DG1092B, 6915509DG1061B, 7305706DG1070B,
  5131430DG1053D`.

## 2. Hallazgos (resumen por propiedad)

| id | SNCZI Q100 | SNCZI DPH | NCSE-02 | EPRTR dist | SIU | BTN via |
|----|-----------|-----------|---------|-----------|-----|---------|
| p0rd01 | no | no | UNAVAILABLE | 1614 m | clase | no |
| p0rd02 | no | no | 0.04 g | 1384 m | clase | no |
| p0rd03 | no | no | **0.17 g** | 1179 m | clase | **si (5 m)** |
| p0rd04 | no | no | UNAVAILABLE | 2326 m | clase | si (2 m) |
| p0rd05 | no | no | 0.04 g | 1457 m | clase | si (4 m) |
| p0rd06 | no | no | UNAVAILABLE | 859 m | clase | si (2 m) |
| p0rd07 | no | no | 0.04 g | 1722 m | clase | no |
| p0rd08 | no | no | 0.04 g | 1863 m | clase | no |
| p0rd09 | no | no | 0.04 g | 1975 m | clase | no |
| p0rd10 | no | no | 0.04 g | 1056 m | clase | si (3 m) |

## 3. Metricas maquinables

| Metrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| `source_traceability` | 1.00 (82/82) | = 1.00 | PASS |
| `false_certainty_incidents` | 0 | <= 0.02 | PASS |
| `known_condition_recall` (controles) | 1.00 (5/5) | >= 0.75 | PASS |
| `actionable_finding_rate` | **humana, pendiente** | >= 0.50 | INCONCLUSIVE |

## 4. Senal de utilidad (provisional, no humana)

- Proxy crudo (cualquier NCSE observado cuenta): **7/10**.
- **Lectura estricta**: los valores NCSE son `0.04 g` en 6 de 7 casos (muy
  bajos); `0.04 g` no justifica una accion concreta de comprador. Con criterio
  estricto, solo `p0rd03` (`0.17 g`, carretera a 5 m) roza lo accionable.
  Lectura estricta: **~1/10**.

Conclusion provisional: con las fuentes actuales, en viviendas residenciales
ordinarias del territorio DGC, HabitaLens produce sobre todo hallazgos
**anodinos**; el unico hallazgo potencialmente accionable es la peligrosidad
sismica, y solo cuando es apreciable.

## 5. Veredicto

```text
P0-RD   INCONCLUSIVE   # revision humana ciega pendiente
senal provisional      FAIL (~1/10 bajo lectura estricta)
```

La revision humana ciega decide. Hoja de revision: `p0rd/blind_review.csv`
(10 filas; el revisor rellena `actionable_HUMANO`, `motivo`, `comprobacion_1a5`).
Los informes estan en `p0rd/reports/<id>/` (HTML/PDF/manifest).

## 6. Implicacion de producto

Si la revision confirma FAIL, la conclusion no es "fallo tecnico" (motor,
portabilidad y trazabilidad estan probados) sino que **las fuentes actuales no
bastan para aportar valor accionable frecuente al comprador**. Segun la regla de
gestion, eso se resuelve estudiando producto, no anadiendo fuentes a ciegas.

## 7. Regla de freeze cumplida

- `p0rd_frame.json` commiteado (`1fe2f3a`) **antes** de la primera consulta de
  riesgo.
- Sin sustituciones por interes; sin cambios de umbrales; sin fuentes nuevas.
