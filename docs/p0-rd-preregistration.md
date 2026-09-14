# P0-RD — DGC Residential Utility Pilot (preregistro)

- Estado: **preregistrado** antes de seleccionar viviendas.
- Fecha: 2026-09-14.
- No altera retroactivamente P0-R (que queda `INCONCLUSIVE` por frame incompleto).
- Pregunta: HabitaLens encuentra informacion **accionable** con suficiente
  frecuencia en viviendas residenciales ordinarias del territorio DGC?

Se separan tres dimensiones: motor tecnico (ya demostrado), portabilidad a los 5
proveedores (ya demostrada en G0-A) y **utilidad para el comprador** (esto es lo
que mide P0-RD, en territorio DGC).

## 1. BASE

Pool DGC ya congelado, construido sin consultar ninguna capa de riesgo:

```text
pool            p0r/p0r_pool_dgc.json.gz
SHA256          33b709872bd0af04a5e2b89f523b2a365729525d8c1c784ca8311b89c7e96fec
candidatos      36.180 viviendas residenciales (currentUse=1_residential, numberOfDwellings>=1)
```

## 2. SELECTION

```text
score = SHA256("habitalens-p0rd-v1|" + stable_property_id)
```

- Orden ascendente por `score`.
- Se toman las **10 primeras resolubles** (resolucion de adquisicion DGC; no es
  consulta de riesgo).
- Si una no resuelve, se toma la siguiente y se registra el motivo.

## 3. ANTES DE RIESGOS

Commitear `p0rd/p0rd_frame.json` con las 10 seleccionadas (refcat, score,
evidencia de resolucion) **antes** de cualquier consulta a SNCZI/SIU/NCSE/BTN/E-PRTR.

## 4. DESPUES

```text
10 viviendas -> motor actual (g0-d-pass) -> 10 manifests -> 10 informes
             -> revision ciega -> metricas P0
```

## 5. UMBRALES (identicos a P0)

| Metrica | Umbral |
|---------|--------|
| `actionable_finding_rate` | >= 0.50 (5/10) |
| `false_certainty_rate` | <= 0.02 |
| `source_traceability` | = 1.00 |
| `known_condition_recall` (controles) | >= 0.75 |

Definicion de `actionable`: accion concreta antes de ofertar (documentacion,
comprobacion, pregunta, profesional, visita, investigacion). "Es interesante" no
cuenta. `UNAVAILABLE`/`INCONCLUSIVE` no cuentan automaticamente.

## 6. VEREDICTO

```text
P0-RD   PASS | FAIL | INCONCLUSIVE
```

- PASS si las metricas cumplen; FAIL si `actionable_finding_rate < 0.50` o fallan
  certeza/trazabilidad/controles; INCONCLUSIVE si la revision no se completa.

## 7. REGLA DE GESTION

Ningun gate nuevo puede bloquear el proyecto salvo que responda a una
incertidumbre que pueda cambiar una decision de producto. P0-FORAL (portabilidad
foral) sera un test posterior, no condicion previa.

## 8. PROHIBICIONES

Sin fuentes nuevas, sin cambiar umbrales, sin seleccion manual por interes, sin
consultar riesgo antes del commit del frame.

## 9. Enmiendas

- (sin enmiendas)
