# P1 — Buyer Actionability Upgrade (preregistro)

- Estado: **preregistrado**. Arranca tras cerrar la primera version del producto
  (`p0-rd-fail`).
- Objetivo: subir la **utilidad accionable** con informacion ligada a la
  transaccion y a la documentacion del inmueble, **no** mas riesgos geograficos.

## 1. Alcance (solo dos capacidades)

### A. Area comparison (superficie anunciada vs oficial)

- Entrada **manual**: `refcat|direccion`, `m2_anunciados`, `tipo_superficie`
  (si se conoce). Sin scraping.
- **Semantica de comparabilidad** (correccion clave): Catastro distingue
  superficie construida privativa, elementos comunes y anejos; el mercado anuncia
  util o construida con o sin comunes.
  - Si el anuncio declara el **mismo concepto** comparable con el oficial ->
    `AREA_MISMATCH` (diferencia factual, con tolerancia).
  - Si solo se sabe el m2 sin concepto -> `POTENTIAL_AREA_MISMATCH` (no se afirma
    discrepancia; se pide verificar que concepto usa el anuncio).
- Salida: componentes oficiales (construida, comunes, anejos) cuando existan,
  `comparability` (directa/parcial/no_comparable), diferencia y nota.

### B. CEE (certificado de eficiencia energetica)

- Familia de adaptadores **regionales** (no un unico `cee_catalunya`):
  `cee_providers/{catalunya,madrid,castilla_la_mancha,...}`.
- Fuentes oficiales con referencia catastral:
  - Cataluna: registro ICAEN + Open Data (consulta por refcat).
  - Madrid: dataset oficial, **CC BY 4.0**.
  - Castilla-La Mancha: registro autonomico con refcat, **CC BY-SA 3.0**.
- Hallazgos: `CEE encontrado` (valor, fecha, registro) y **discrepancia** si el
  anuncio declara otra calificacion; o `no consta` **solo** donde se acredite
  cobertura completa del registro (si no -> `UNAVAILABLE`/`INCONCLUSIVE`).
- Contexto normativo: RD 390/2021 exige calificacion en publicidad y anexar el
  certificado registrado al contrato de compraventa.

## 2. Fuera de alcance (explicito)

- **NO** OSMnx ni nuevas capas GIS de entorno/riesgo.
- **NO** precios, ruido, incendios, ITE/IEE, IA, usuarios, pagos.
- **NO** scraping de portales.

## 3. Medicion (misma pregunta)

Se re-mide utilidad con 10-20 viviendas introduciendo ademas el dato manual de
superficie (y CEE cuando aplique). Pregunta al revisor humano:

> "Esto me haria comprobar algo antes de ofertar?"

Sin cambiar umbrales: `actionable_finding_rate >= 0.50`,
`false_certainty_rate <= 0.02`, `source_traceability = 1.00`.

## 4. Criterios de aceptacion

- A: modulo con semantica de comparabilidad + tests; nunca convierte un m2 sin
  concepto en "el anuncio miente".
- B: al menos un adaptador regional con `LICENSE.yaml` y acceso verificado; el
  resto se anade con su propio preregistro.
- Sin geometria en salida publica; sin score.

## 5. Gates

```text
P1.A Area comparison   PASS | FAIL | INCONCLUSIVE
P1.B CEE (por region)  PASS | FAIL | INCONCLUSIVE
P1 global (utilidad)   PASS | FAIL | INCONCLUSIVE
```

## 6. Estado de ejecucion

- **P1.A Area comparison: PASS (implementado).** Modulo
  `evidence/surface.py` con `SurfaceConcept`/`ComparabilityStatus`/
  `SurfaceComponents` y `compare_area`; CLI `habitalens surface <refcat>
  --advertised N --concept ... [--official-built/--official-common]`. Un m2 sin
  concepto produce `area.potential_mismatch` ("verificar que concepto usa el
  anuncio"), nunca una discrepancia factual.
- **P1.B CEE: PASS parcial (Cataluna) / pendiente (Madrid, CLM).**
  - Cataluna: adaptador `cee/catalunya` consultable por refcat (Socrata
    `j6ii-t3w2`), con `LICENSE.yaml`. CLI `habitalens cee <refcat>`. Verificado
    live: `9533603DG4393S0001LT` -> calificacion E, `metres_cadastre 62.81`.
    Sin registro -> `INCONCLUSIVE` (no "no consta").
  - Madrid: dataset oficial **CC BY 4.0**, pero en **ZIP por anyos** (no API de
    consulta) -> adaptador de descarga+indice pendiente, con su preregistro.
  - Castilla-La Mancha: **XML por provincia/anyo**, **CC BY-SA 3.0** -> pendiente.
- **P1 global (utilidad)**: pendiente de una nueva medicion con 10-20 viviendas
  aportando el m2 anunciado (y CEE donde aplique).

## 7. Enmiendas

- **E1 (2026-09-17).** CEE Euskadi activado: Open Data Euskadi expone
  `api.euskadi.eus/energy-efficiency/buildings` (OpenAPI 3.0, CC BY) con filtro
  `cadastral-ref` sobre las referencias forales (formato provincial, no DGC-20).
  Adaptador `cee/euskadi` con `LICENSE.yaml`; verificado live: `4774399`
  (Bergara) -> edificio con `energyRating` F. La API omite `items` cuando
  `totalItems` es 0; respuesta vacia -> INCONCLUSIVE (cobertura completa no
  acreditada).
- **E2 (2026-09-17).** CEE Andalucia evaluado: el portal CKAN de la Junta
  publica el registro como 8 recursos `.xml.7z` provinciales
  (`datastore_active: false`, ~1,46M registros, actualizacion trimestral). Sin
  API de consulta por referencia -> mismo veredicto que Madrid/CLM: adaptador
  de descarga+indice pendiente con su preregistro; no se implementa aun para no
  introducir infraestructura de indice masivo sin preregistro propio.
