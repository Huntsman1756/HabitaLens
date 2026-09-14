# G0-C — Preregistro (congelado antes de ejecutar SIU, NCSE-02 ni BTN)

Estado: **preregistrado**. No se ha ejecutado ninguna fuente de G0-C.

Referencias: G0-A `PASS` (`g0-a-pass`), G0-B `INCONCLUSIVE`
(`g0-b-inconclusive`, `37dfbc1`), G0-B.1 cerrado, decision de progresion en
`docs/g0-b-progression-decision.md`.

Este documento fija alcance, semantica de cobertura, corpus, controles y
criterios de aceptacion **antes** de ejecutar ninguna fuente. Cualquier cambio
posterior se registra como enmienda fechada (seccion 13).

## 0. Pregunta del gate

> Sabemos distinguir correctamente si una fuente oficial **cubre** la zona de
> una propiedad antes de interpretar su respuesta, y podemos convertir eso en
> hallazgos deterministas OBSERVED / DERIVED / UNAVAILABLE / INCONCLUSIVE?

El problema central de G0-C es la **cobertura**, no la geometria (ya resuelta
en G0-B).

## 1. Estado heredado (no se toca)

- `G0-B = INCONCLUSIVE`. No se promociona a PASS.
- **CSN permanece INCONCLUSIVE.** Ningun hallazgo de CSN puede ascender a
  OBSERVED/DERIVED en G0-C.
- **IS-47 (2025) no se incorpora.** No sustituye a `csn_radon_potential_map`.
  En su caso sera un adaptador distinto (`csn_radon_priority_municipal`) con
  semantica normativa propia y preregistro aparte.
- El motor espacial de G0-B (taxonomia, CRS operacional, provenance,
  determinismo) se reutiliza sin cambios de semantica.

## 2. Semantica de cobertura (estricta)

```text
OBSERVED     La fuente cubre la zona y hemos observado algo.
DERIVED      La fuente cubre la zona y el motor calcula una consecuencia.
UNAVAILABLE  La fuente funciona, pero oficialmente no cubre ese ambito/caso.
INCONCLUSIVE No se puede determinar de forma fiable si hay cobertura, interpretar
             la respuesta, resolver CRS/schema, o acreditar la fuente.
```

Regla dura:

> `query devuelve 0 features` **NO** equivale a "suelo sin afecciones".

Para emitir OBSERVED-ausencia es obligatorio demostrar **cobertura** del
ambito consultado (p.ej. el municipio/termino esta dentro de la extension
declarada de la capa y el schema/CRS se han interpretado correctamente). Si la
cobertura no puede acreditarse, el resultado es **UNAVAILABLE** (sin cobertura
oficial) o **INCONCLUSIVE** (no podemos determinarlo), nunca OBSERVED-ausencia.

## 3. Alcance

- **Fuentes (3): SIU, NCSE-02, BTN.** Cada una con `LICENSE.yaml`, endpoint y
  versionado reproducibles verificados **antes** de parsear.
- **Corpus: 24 propiedades** (seccion 5), seleccionadas por diversidad
  administrativa/geografica, **no** por resultado.
- **Controles positivos fuera del corpus** (seccion 6).
- Semantica de cobertura como gate de primera clase.
- Fixtures congeladas + tests offline + evidencia live separada.

Fuera de alcance (no se implementa): reglas de riesgo o umbrales normativos,
scores, informes, HTML/PDF, visor web, IA, usuarios, pagos, historico
inmobiliario, reproyeccion como fin.

## 4. Fuentes (hipotesis de acceso; endpoints NO ejecutados aun)

| Fuente | Que se busca | Hipotesis de acceso (a validar) |
|--------|--------------|---------------------------------|
| SIU | Clasificacion/afecciones del suelo (Sistema de Informacion Urbana) | Servicios OGC/descarga MITMA; capas de clasificacion urbanistica |
| NCSE-02 | Peligrosidad sismica (Norma de Construccion Sismorresistente) | Cartografia de peligrosidad sismica (IGN/CTE) |
| BTN | Infraestructuras/topografia (Base Topografica Nacional) | Servicios/descarga IGN |

Cada endpoint concreto, licencia y version se registran en
`config/endpoints.yaml` + `LICENSE.yaml` antes de usarse. Si una fuente no
tiene licencia declarada o acceso reproducible verificado, **no se activa** y
su gate es INCONCLUSIVE (precedente: CSN en G0-B).

## 5. Corpus preregistrado (24 propiedades)

Seleccion outcome-blind: se fija **antes** de consultar SIU/NCSE/BTN. Ninguna
propiedad se anade o elimina despues de observar un resultado.

**Bloque A — 10 refcats ya conocidos (congelados):**

| # | Autoridad | refcat |
|---|-----------|--------|
| 1 | DGC | `1707903VK4810F` |
| 2 | DGC | `0343302VK4704C` |
| 3 | Gipuzkoa | `8297093` |
| 4 | Araba | `59590687` |
| 5 | Bizkaia | `48.020.1619.04006` |
| 6 | Gipuzkoa | `8594149` |
| 7 | Navarra | `001010001` |
| 8 | Araba | `64010007` |
| 9 | DGC | `0244604VK4704C` |
| 10 | Bizkaia | `48.001.1055.99082` |

**Bloque B — 14 direcciones fijas** (a resolver a refcat con CartoCiudad +
proveedor en la fase de materializacion, **antes** de consultar SIU/NCSE/BTN).
Orden fijo; si una direccion no geocodifica, se usa la siguiente de la lista
hasta completar 14. La lista de direcciones, no los refcats resultantes, es lo
que se congela aqui:

```text
Calle Mayor 1, Vigo
Calle Mayor 1, A Coruna
Calle Mayor 1, Oviedo
Calle Mayor 1, Santander
Calle Mayor 1, Valladolid
Calle Mayor 1, Zaragoza
Calle Mayor 1, Sevilla
Calle Mayor 1, Murcia
Calle Mayor 1, Cadiz
Calle Mayor 1, Granada
Calle Mayor 1, Toledo
Calle Mayor 1, Badajoz
Calle Mayor 1, Caceres
Calle Mayor 1, Palma
```

Regla de materializacion: los 10 refcats de A y los resultantes de B se
condensan en `corpus` (codigo) y **se commitean antes de la primera consulta a
SIU/NCSE/BTN**. A partir de ahi el corpus es inmutable.

## 6. Controles positivos fuera del corpus

Independientes del corpus, para validar deteccion aunque el corpus salga
"aburrido":

- SIU: una ubicacion con clasificacion urbanistica conocida y documentada.
- NCSE-02: una ubicacion con peligrosidad sismica conocida y documentada.
- BTN: una infraestructura deliberadamente seleccionada.

Se fijan y justifican en el momento de verificar cada fuente, con evidencia
oficial, y no alteran el corpus.

## 7. Gates por fuente

Cada fuente se evalua por separado:

- **PASS** si: (a) hay control positivo que detecta; (b) hay al menos un caso de
  ausencia/`UNAVAILABLE` correctamente clasificado; (c) la cobertura se acredita
  de forma explicita; (d) test offline en verde.
- **INCONCLUSIVE** si no puede verificarse licencia/acceso/cobertura/schema/CRS
  de forma suficiente.
- **FAIL** si hay error reproducible o clasificacion incorrecta.

Ninguna fuente puede emitir OBSERVED-ausencia sin prueba de cobertura.

## 8. Aceptacion del motor

- Semantica de cobertura aplicada sin ambiguedad; `0 features` nunca se
  convierte en "sin afecciones".
- `source_crs` + `operational_crs` en cada hallazgo; sin EPSG:25830 nacional.
- Provenance suficiente para explicar cada resultado.
- Replay determinista: misma propiedad + misma version de fuente + misma regla
  = mismos hallazgos.
- Sin fuga de geometria en salida publica.

## 9. Veredicto global

`G0-C = PASS / FAIL / INCONCLUSIVE`, derivado de los gates reales. No se
declara PASS por tener los tests verdes.

## 10. Riesgos y supuestos

- SIU/NCSE-02/BTN pueden no publicar OGC; se valida con metadatos antes de
  codificar.
- La cobertura de SIU es probablemente municipal/autonomica: disenar el gate
  para UNAVAILABLE honesto, no para forzar un resultado.
- Riesgo de confundir "capa global" con "capa que cubre esta zona": se exige
  prueba de cobertura explicita.

## 11. Prohibiciones

No adelantar G0-D. No introducir scores, informes, riesgo normativo ni visor.
No promover CSN por esta via. No incorporar IS-47 como sustituto.

## 12. Artefactos esperados

- `src/habitalens/sources/{siu,ncse02,btn}/` con `LICENSE.yaml`.
- `src/habitalens/evidence/coverage.py` (o equivalente) para acreditar cobertura.
- `tests/` contrato + golden + determinismo por fuente + controles.
- `docs/decisions.md`, `docs/probe-evidence.md` actualizados.

## 13. Enmiendas

- **E1 (2026-09-14).** Lista final del bloque B tras activar la desambiguacion
  **estricta por localidad** en CartoCiudad (evita devolver la parcela de otra
  ciudad cuando la calle es ambigua) y comprobar geocodabilidad. Sustituciones,
  decididas **antes** de consultar SIU/NCSE-02/BTN y sin mirar resultados de
  esas fuentes: `A Coruna` pasa a "Calle Real 1"; `Cadiz` a "Calle Colon 1";
  `Badajoz` a "Avenida de Huelva 1"; `Toledo` a "Calle Comercio 1"; se retiran
  `Vigo` y `Palma` (no geocodifican de forma fiable o resuelven a municipio
  distinto) y se anaden `Logrono` y `Salamanca`. El bloque A (10 refcats) no
  cambia. La seleccion sigue siendo outcome-blind y por diversidad
  administrativa.

