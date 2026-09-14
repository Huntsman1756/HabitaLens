# G0-D — Preregistro (contrato congelado; NO ejecutado)

Estado: **preregistrado**. No se ejecuta todavia.

Referencias: G0-A `PASS` (`g0-a-pass`), G0-B `INCONCLUSIVE`/CSN externo
(`g0-b-inconclusive`), G0-C `PASS` (`g0-c-pass`, `dce2074cc7d04c48da5e3bf7240fc7bb7023e081`).

Este documento congela el contrato de producto **antes** de renderizar nada.
Cualquier cambio posterior se registra como enmienda fechada (seccion 12).

## 0. Pregunta del gate

> Podemos convertir hallazgos de evidencia (OBSERVED/DERIVED/UNAVAILABLE/
> INCONCLUSIVE) en un producto presentable y auditable, con procedencia
> completa y disclaimers, **sin inventar un score global de vivienda**?

G0-D es el salto de motor a producto. No anade fuentes ni reglas de riesgo.

## 1. Estado heredado (no se toca)

- G0-C `PASS`; el motor de evidencia y la semantica de cobertura quedan
  congelados.
- G0-B sigue `INCONCLUSIVE` solo por CSN (dependencia externa). En el producto,
  CSN debe aparecer **explicitamente como INCONCLUSIVE**; nunca omitido ni
  convertido en "sin riesgo".
- `IS-47` no se incorpora.

## 2. Alcance

- **Render HTML** de un informe por propiedad (o por conjunto del corpus).
- **Render PDF** del mismo informe.
- **Manifest de procedencia** (`provenance_manifest.json`) con fuentes,
  versiones, CRS, metodos y hashes.
- **Disclaimers** obligatorios.
- **Presentacion por hallazgo**: cada hallazgo con su semantica.
- **Cero score global de vivienda** (guard de primera clase).

## 3. Fuera de alcance (prohibido en G0-D)

- Score/indice/valoracion global de la vivienda o agregacion tipo semaforo.
- Reglas de riesgo o umbrales normativos, recomendaciones de compra.
- Datos de mercado, historico inmobiliario, precios, IA, usuarios, pagos.
- Visor web interactivo.
- Geometria en cualquier salida (HTML/PDF/JSON/manifest).

## 4. Contrato del manifest de procedencia

`provenance_manifest.json` (sin geometria) debe contener por hallazgo:

```text
property_id
source
source_version
kind
status            # observed | derived | unavailable | inconclusive
observed          # bool | null
value, unit       # solo cuando aplique
source_crs
operational_crs
method
inputs
provenance_id
retrieved_at
note
```

Y a nivel de documento: identificador de informe, corpus/version de corpus,
version de reglas de presentacion, fecha, y hashes de los artefactos generados.
Ningun campo de geometria/coordenadas.

## 5. Contrato de presentacion por hallazgo

Cada hallazgo debe mostrar de forma legible y no ambigua:

- que fuente y version;
- **su estado explicito** (OBSERVED / DERIVED / UNAVAILABLE / INCONCLUSIVE);
- el valor y unidad cuando exista;
- `source_crs` y `operational_crs`;
- metodo e inputs;
- `provenance_id` para trazabilidad.

Reglas de render:

- `UNAVAILABLE` y `INCONCLUSIVE` **nunca** se colapsan en "sin afeccion" ni se
  ocultan.
- `OBSERVED` con `observed=false` se presenta como "ausencia observada en
  cobertura acreditada", no como "sin riesgo".
- Prohibido cualquier agregado que produzca una nota global.

## 6. Disclaimers

Obligatorios en HTML y PDF (y no eliminables por opcion):

> "HabitaLens es un proyecto independiente. Genera analisis derivados a partir
> de fuentes publicas y no representa ni sustituye a la Direccion General del
> Catastro ni a ninguna otra administracion publica. Sus resultados no tienen
> caracter oficial ni fehaciente."

Ademas, por fuente, la atribucion/licencia correspondiente (SNCZI/MITECO,
E-PRTR/EEA, SIU/MIVAU, NCSE-02/IGN, BTN/IGN-CNIG; CSN no activado).

## 7. Determinismo

- Regla: misma evidencia de entrada + misma version de plantilla = mismo
  contenido de informe.
- Orden de hallazgos estable (por `source`, `kind`).
- PDF reproducible: metadatos de fecha fijados (p. ej. `SOURCE_DATE_EPOCH`);
  el determinismo se evalua a nivel de contenido/estructura.
- No se usan timestamps de render dentro del cuerpo del informe.

## 8. Gates de G0-D

```text
Renderer HTML            PASS | FAIL
Renderer PDF             PASS | FAIL
Provenance manifest      PASS | FAIL
Disclaimers              PASS | FAIL
No-global-score guard    PASS | FAIL
Determinism              PASS | FAIL
Geometry-leak guard      PASS | FAIL
Global G0-D              PASS | FAIL | INCONCLUSIVE
```

Criterios:

- **Renderer**: genera HTML y PDF para el corpus sin error, con todos los
  hallazgos representados.
- **Manifest**: schema completo y valido por hallazgo; sin geometria.
- **Disclaimers**: presentes e identicos en HTML y PDF; test que falla si se
  eliminan.
- **No-global-score**: ningun campo/tabla/texto de nota global; test que
  falla si aparece una clave prohibida (`score`, `rating`, `overall`,
  `valoracion_global`, `semaforo`, ...).
- **Determinism**: dos renders con la misma entrada producen el mismo
  contenido (html normalizado y manifiesto identicos).
- **Geometry-leak**: HTML/PDF/JSON/manifest sin geometria ni coordenadas.

## 9. Controles

- **Control positivo**: informe del corpus con hallazgos OBSERVED y DERIVED
  presentes y correctamente etiquetados (p. ej. NCSE Granada, BTN Madrid).
- **Control de estado duro**: informe que incluye un `INCONCLUSIVE` (SIU
  Navarra) y un `UNAVAILABLE` (NCSE null Madrid) que **deben** aparecer como
  tales.
- **Control negativo de score**: intento de inyectar un score global debe
  fallar el guard.

## 10. Riesgos y supuestos

- Estabilidad de librerias de render (PDF) puede afectar byte-determinismo;
  se evalua a nivel de contenido.
- Renderizado de caracteres/idioma; se fija codificacion UTF-8.
- Riesgo de que un lector infiera valoracion; mitigado con etiquetas de estado
  y disclaimer.

## 11. Artefactos esperados

- `src/habitalens/report/` (render HTML/PDF, manifest, disclaimers).
- `tests/` render + manifest + disclaimers + no-score + determinism + leakage.
- `docs/decisions.md`, `docs/probe-evidence.md` actualizados.

## 12. Enmiendas

- (sin enmiendas)
