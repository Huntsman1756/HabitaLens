# P0-R — Residential Property Utility (preregistro congelado; NO ejecutado)

Estado: **preregistrado**. No se ejecuta todavia.

Referencias: P0 `INCONCLUSIVE` (`p0-inconclusive`), P0.1 `DEFERRED`, P0-T0
`FAIL`, `g0-d-pass`. Umbrales de P0 intactos.

## 0. Pregunta

> HabitaLens produce informacion **accionable** con suficiente frecuencia cuando
> se aplica a **viviendas residenciales ordinarias** elegidas sin mirar antes sus
> riesgos?

No mide integracion con portales; mide **utilidad del producto**.

## 1. Marco de muestreo

Fuentes catastrales **oficiales ya validadas en G0-A**. No se usa ningun portal.

```text
FRAME
fuentes catastrales oficiales ya aprobadas en G0-A

ELIGIBLE
edificio/inmueble con uso residencial acreditado
y al menos una vivienda cuando el proveedor exponga ese atributo

SELECTION
determinista por hash de identificador oficial,
sin consultar SNCZI / SIU / NCSE / BTN / E-PRTR antes del freeze

STRATA
DGC       6 propiedades
Navarra   1
Bizkaia   1
Gipuzkoa  1
Alava     1

TOTAL
10
```

DGC merece 6 y no 2 porque la integracion foral ya esta probada en G0-A; no se
sobrerrepresentan los sistemas forales.

## 2. Elegibilidad (uso residencial)

- Uso residencial acreditado con atributos oficiales del proveedor (para DGC,
  `currentUse = 1_residential` y `numberOfDwellings` segun la documentacion de
  Catastro; para forales, su atributo equivalente cuando exista).
- El **pool de candidatos** y la procedencia de cada atributo se congelan en el
  fichero de frame (seccion 6) **antes** de cualquier consulta de riesgo.

## 3. Seleccion

```text
score = SHA256("habitalens-p0r-v1|" + provider + "|" + stable_property_id)
```

- Ordenar los elegibles por `score` ascendente.
- Tomar los primeros de cada estrato hasta completar su cuota.
- Si un elegido no puede resolverse, pasar al **siguiente hash** (regla
  preregistrada). No hay sustitucion por interes.

## 4. Regla de congelacion (critica)

**No se consulta ninguna capa de riesgo (SNCZI, SIU, NCSE-02, BTN, E-PRTR) hasta
haber commiteado las 10 referencias seleccionadas** en `p0r_frame.json`
(pools + scores + seleccion final). A partir de ahi son inmutables.

## 5. Pipeline y metricas (identicas a P0)

```text
10 viviendas -> HabitaLens (g0-d-pass) -> 10 manifests -> 10 informes
             -> revision humana ciega -> metricas P0 originales
```

| Metrica | Umbral |
|---------|--------|
| `actionable_finding_rate` | >= 0.50 |
| `false_certainty_rate` | <= 0.02 |
| `source_traceability` | = 1.00 |
| `known_condition_recall` (controles) | >= 0.75 |

Pregunta al revisor (ciega, misma que P0):

> Si estuvieras considerando comprar esta vivienda, hay algo en este informe que
> te llevaria a comprobar, preguntar, solicitar documentacion o consultar a
> alguien antes de ofertar?

Definicion operativa de **actionable finding**: exige una accion concreta antes
de ofertar; "es interesante" no cuenta.

## 6. Congelacion y entregables

- `p0r_frame.json`: pools elegibles, `score` por candidato y las 10 seleccionadas
  (commiteado antes de consultar riesgo).
- `docs/p0-r-report.md`: metricas, tabla por propiedad, veredicto.

## 7. Veredicto

```text
P0-R   PASS | FAIL | INCONCLUSIVE
```

- **PASS** si las metricas cumplen.
- **FAIL** si `actionable_finding_rate < 0.50` (aunque los controles se detecten
  perfectamente), o si `false_certainty_rate`/`source_traceability` incumplen.
- **INCONCLUSIVE** si el pool residencial no puede obtenerse de forma
  reproducible o la revision ciega no se completa.

Un `4/10` es **FAIL**: seria la senal de que hay que estudiar producto antes de
anadir fuentes.

## 8. Prohibiciones

- No anadir fuentes de riesgo ni funcionalidad.
- No cambiar umbrales.
- No seleccionar ni retirar propiedades por interes.
- No consultar capas de riesgo antes del freeze.
- No scraping ni evasion.

## 9. Enmiendas

- **P0-R-E1 — Frame materialization (2026-09-14).** Se aplica antes de cualquier
  consulta a SNCZI/SIU/NCSE/BTN/E-PRTR.

```text
Para cada proveedor se construye el conjunto candidato exclusivamente
a partir de datos catastrales autorizados en G0-A.

Cada fila candidata contiene unicamente:
provider
stable_property_id
residential_eligibility
source_version

No se incorporan atributos procedentes de fuentes G0-B/G0-C.

El procedimiento exacto para enumerar candidatos debe ser determinista
y quedar registrado por proveedor.

El pool completo utilizado para la seleccion se congela con:
- numero total de candidatos;
- SHA-256 del fichero;
- source_version;
- procedimiento de adquisicion.

Despues, y solo despues:

score = SHA256("habitalens-p0r-v1|" + provider + "|" + stable_property_id)

Se ordena ascendentemente y se toman: DGC 6, Navarra 1, Bizkaia 1,
Gipuzkoa 1, Alava 1.

Una sustitucion solo esta permitida si el inmueble seleccionado no puede
resolverse tecnicamente como propiedad residencial; se toma el siguiente
hash y se registra el motivo.

No se sustituye por tener resultados poco interesantes, muchos
UNAVAILABLE o ausencia de hallazgos.
```

  Se congelan dos artefactos: `p0r_pool_manifest.json` (de donde salieron las
  candidatas) y `p0r_frame.json` (las diez seleccionadas). El commit de
  `p0r_frame.json` debe **preceder** a cualquier consulta de riesgo.

  Nota: `UNAVAILABLE` e `INCONCLUSIVE` **no** cuentan automaticamente como
  `actionable`; solo cuentan si provocan una accion concreta segun la definicion
  ya congelada. Criterio duro: 5/10 o mas actionable = PASS; 4/10 o menos =
  FAIL; traceability < 1.00 = FAIL; false certainty > 0.02 = FAIL; controles
  conocidos < 0.75 = FAIL; revision no completada = INCONCLUSIVE.
