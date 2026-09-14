# P0 — Buyer Utility Validation: informe de ejecucion

- Fecha: 2026-09-14.
- Preregistro: `p0-preregistered` (`54de15872f4e5d3b677520bfe51c1d65c0a5b9ab`)
  + enmienda **P0-E1**.
- Producto evaluado: G0-D `PASS` (`g0-d-pass`).
- **Veredicto: P0 = INCONCLUSIVE.**

## 1. Muestra preregistrada (P0-E1): no obtenible

Marco fijado en P0-E1: Portal Idealista, consulta de vivienda de segunda mano en
venta, snapshot unico, muestreo sistematico `eligible[0::3][:10]`.

Intento de obtencion (evidencia):

| Comprobacion | Resultado |
|--------------|-----------|
| `https://www.idealista.com/robots.txt` | 200; `User-agent: *` con `Disallow: /*/pagina-*.htm`, `Disallow: /pagina/` y multiples rutas de resultados/ordenacion |
| `GET /venta-viviendas/` (UA identificable) | **HTTP 403** (bloqueo anti-bot) |

No se ha eludido el bloqueo: el preregistro (seccion 8) obliga a respetar
`robots.txt` y los terminos de uso. Por tanto **el marco de muestreo no es
obtenible de forma reproducible** desde este entorno y la muestra de 10 anuncios
no se ha capturado.

Consecuencia directa segun la seccion 6: **INCONCLUSIVE** (muestra no
obtenible de forma reproducible).

## 2. Metricas de control (calculables sin la muestra)

Ejecutado `scripts/p0_validate.py` sobre las fixtures congeladas (G0-B, G0-C):

| Metrica | Valor | Umbral | Estado |
|---------|-------|--------|--------|
| `known_condition_recall` | 1.00 (5/5) | >= 0.75 | PASS |
| `false_certainty_incidents` | 0 | 0 en controles | PASS |
| `source_traceability` | 1.00 (118/118) | = 1.0 | PASS |
| `actionable_finding_rate` | **no medido** | >= 0.5 | pendiente de muestra + revision humana |

Controles verdaderos detectados: Ebro Q100 (SNCZI), Bilbao-ELMET (E-PRTR),
Granada 0.23 g (NCSE-02), Madrid carretera (BTN), Madrid clase de suelo (SIU).

Controles de certeza falsa correctos: NCSE `null` Madrid -> `UNAVAILABLE`;
SIU Navarra (`g0c07`) -> `INCONCLUSIVE` (ninguno convertido en OBSERVED-ausencia).

## 3. Revision humana ciega

No ejecutada: (a) no hay muestra; (b) la revision ciega de utilidad para el
comprador es un paso humano por diseno (seccion 4 del preregistro) y no puede
ser realizada por el ejecutor automatico. `human_review = PENDING`.

## 4. Veredicto

```text
P0   INCONCLUSIVE
```

Motivo: muestra no obtenible de forma reproducible (Idealista 403 + robots) y
revision humana ciega pendiente. **No** es FAIL de producto: las metricas
medibles cumplen; simplemente no puede medirse la utilidad real sobre la
muestra preregistrada.

## 5. Que haria falta para completar P0 (propuesta, no aplicada)

Enmienda **P0-E2** (a decidir antes de mirar resultados): sustituir el marco por
uno obtenible de forma reproducible y compatible con ToS, por ejemplo:

1. **Snapshot provisto por el operador**: una persona guarda la pagina/CSV de
   resultados (IDs + direcciones) y la deposita como fichero versionado; el
   ejecutor no scrapea. Se mantiene `eligible[0::k][:10]` y `k=3`.
2. **Fuente con acceso permitido**: un portal con API/feed publico o un conjunto
   de direcciones provisto por el revisor.

En cualquiera de los dos casos, la revision ciega la realiza una persona y se
registra en `docs/p0-report.md`. Sin ese paso, P0 permanece INCONCLUSIVE.

## 6. No se ha cambiado el alcance

- No se han anadido fuentes ni reglas.
- El motor y el informe quedan congelados en `g0-d-pass`.
- CSN sigue INCONCLUSIVE; IS-47 no se incorpora.
