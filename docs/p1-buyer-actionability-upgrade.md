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

## 6. Enmiendas

- (sin enmiendas)
