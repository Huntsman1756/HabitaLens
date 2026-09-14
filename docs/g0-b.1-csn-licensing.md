# G0-B.1 — CSN licensing remediation

- Estado: **cerrado como INCONCLUSIVE**; el gate `g0-b-inconclusive` se mantiene.
- Alcance: **solo comprobacion juridica/acceso**. No se modifica el motor de
  evidencia ni los adaptadores. CSN sigue `usable=false` y sigue emitiendo
  únicamente `INCONCLUSIVE`.
- Fecha: 2026-09-14.

## Objetivo

Determinar si el *Mapa del Potencial de Radón de España* (CSN, 2017) esta
formalmente catalogado como dato abierto/reutilizable, o si procede una consulta
formal al CSN. No se cambia el criterio preregistrado "licencia y acceso antes
que parsing".

## Evidencia verificada

| Comprobacion | Resultado | Evidencia (raw) |
|--------------|-----------|-----------------|
| Se publica shapefile | SI | sede/mapa: "Descargar datos como shapefile para ArcGIS" |
| El CSN contempla su uso | SI | "Cuando se utilicen datos de esta cartografía deberá citarse de la siguiente forma: **Mapa del Potencial de Radón de España CSN, 2017**" |
| Atribucion exigida | SI | texto de cita anterior |
| Licencia abierta inequivoca | **NO PROBADA** | no hay `licencia`/CC/notice junto al producto |
| Entrada en catalogo de datos abiertos | **NO ENCONTRADA** | `datos.gob.es/apidata/catalog/dataset/title/radon` -> solo un registro de contratos ajeno ("Buradón"); `.../publisher/EA0042629` -> sin datasets; `sede.csn.gob.es/.../datos-abiertos` -> 404 |
| Servicio OGC/versionado reproducible | NO | sin WFS/WMS/FeatureServer (G0-B recon) |

Aviso legal del CSN (texto literal relevante):

> "...queda totalmente prohibida salvo que medie autorización expresa del CSN.
> No obstante, los contenidos que sean considerados como **datos abiertos en la
> Sede Electrónica y publicados según lo previsto en el RD 1495/2011**, de 24 de
> octubre ... podrán ser objeto de reproducción siempre que los contenidos
> permanezcan íntegros y sea citada la fuente."

URLs verificadas: `https://www.csn.es/documents/10182/1983267/aviso+legal`
(PDF, 47.123 B), `https://sede.csn.gob.es/es/web/portal-csn/mapa-del-potencial-de-radon-en-espana`
(200), `https://www.csn.es/mapa-del-potencial-de-radon-en-espana` (200).

## Veredicto

```text
CSN publica shapefile             SI
CSN cuenta con su uso             SI (con cita obligatoria)
Atribucion requerida              SI
Licencia abierta inequivoca       NO PROBADA
Catalogo de datos abiertos        NO ENCONTRADO
Acceso OGC/versionado             NO
Gate preregistrado                INCONCLUSIVE
```

Aceptar `PASS` seria rebajar el criterio despues de observar el resultado. El
aviso legal condiciona la reutilizacion a que el contenido este "considerado
dato abierto en la Sede y publicado segun RD 1495/2011", y esa consideracion no
se ha podido verificar para la cartografia de radon. **CSN permanece
INCONCLUSIVE.**

## Acciones propuestas (no ejecutadas)

1. **Consulta formal al CSN** (plantilla abajo) sobre condiciones de
   reutilizacion y licencia aplicable al shapefile de potencial de radon.
2. Buscar en la Sede un **Catalogo de Informacion Publica** con entrada
   especifica para este producto (no localizado hoy).
3. Si el CSN confirma dato abierto reutilizable y publica un acceso
   reproducible/versionado, reconsiderar el gate en una enmienda fechada.

### Plantilla de consulta al CSN

> Asunto: Condiciones de reutilizacion del "Mapa del Potencial de Radon de
> Espana (CSN, 2017)" (shapefile)
>
> Buenos dias: desarrollamos un proyecto de codigo abierto (HabitaLens) que
> genera analisis derivados a partir de fuentes publicas, con cita de la fuente.
> Deseamos incorporar la cartografia de potencial de radon publicada en
> `sede.csn.gob.es` (descarga "shapefile para ArcGIS"). Solicitamos:
> (1) si ese conjunto esta considerado "dato abierto" conforme al RD 1495/2011
> y publicado en la Sede; (2) la licencia/condiciones de reutilizacion
> aplicables; (3) si es admisible su reutilizacion en un producto derivado de
> codigo abierto manteniendo la cita "Mapa del Potencial de Radon de Espana CSN,
> 2017" y sin sugerir caracter oficial. Gracias.

## Nota sobre la IS-47 (2025)

La Instruccion IS-47 (BOE-A-2025-8734) aprueba el listado de **terminos
municipales de actuacion prioritaria** frente al radon. Es una fuente
administrativa/normativa **distinta** de la cartografia preregistrada. No se usa
para sustituir silenciosamente el producto de radon; si en el futuro se
incorpora, sera como fuente nueva con su propio preregistro y `LICENSE.yaml`.
