# P0-R — Frame materialization status

- Fecha: 2026-09-14.
- Preregistro: `p0-r-preregistered` (`b43908a`) + **P0-R-E1**.
- **Veredicto actual: P0-R = INCONCLUSIVE** (frame de 10 celdas incompleto).

## 1. Lo ejecutado (antes de cualquier consulta de riesgo)

Materializacion determinista del pool **DGC** (`scripts/p0r_materialize.py`):

- Enumeracion de los 52 feeds ATOM BU de la DGC y de los **7.611** ZIP
  municipales `A.ES.SDGC.BU.<mun>.zip`.
- Muestreo sistematico de 8 municipios sobre la lista nacional ordenada por
  codigo.
- Parseo de `bu-ext2d:Building` con `currentUse=1_residential` y
  `numberOfDwellings>=1`.

Resultado (congelado):

```text
provider            dgc
candidates          36.180
pool_sha256         33b709872bd0af04a5e2b89f523b2a365729525d8c1c784ca8311b89c7e96fec
source_version      DGC INSPIRE ATOM buildings (BU) verificado 2026-09-14
artefactos          p0r/p0r_pool_manifest.json, p0r/p0r_pool_dgc.json.gz
municipios          02001, 08279, 16014, 22169, 29027, 40002, 45174, 56101
```

## 2. Lo que falta

Los estratos forales (Navarra 1, Bizkaia 1, Gipuzkoa 1, Alava 1) requieren un
**enumerador propio por proveedor**, verificado y deterministico, antes de poder
seleccionar por hash:

| Proveedor | Publicacion BU observada | Estado |
|-----------|--------------------------|--------|
| Bizkaia | ATOM con ZIP **por municipio** (`ES.BFA.BU.<mun>.zip`) | pendiente |
| Gipuzkoa | ZIP **de territorio completo** (`ES.GFA.BU.zip`) | pendiente |
| Alava | ZIP **de territorio completo** (`BU_<crs>_GML.zip`) | pendiente |
| Navarra | sin ATOM BU INSPIRE; capa local WFS `CATAST_Pol_Edificacion` | pendiente |

Sin esos pools no puede congelarse el frame de 10 celdas ni calcular los
`stable_property_id` del resto de estratos.

## 3. Cumplimiento de la regla de congelacion

- **No** se ha consultado ninguna capa de riesgo (SNCZI/SIU/NCSE/BTN/E-PRTR).
- **No** se ha calculado ningun `score` ni se ha seleccionado ninguna vivienda.
- **No** existe `p0r_frame.json`, por lo que no se ejecuta HabitaLens ni la
  revision.

## 4. Veredicto

```text
P0-R   INCONCLUSIVE
```

Motivo: el frame preregistrado de 10 celdas no puede completarse todavia de forma
determinista (faltan los enumeradores forales). No es FAIL: la parte medible del
procedimiento funciona (pool DGC congelado con hash).

## 5. Siguiente paso propuesto (P0-R-E2, no aplicada)

Congelar un **enumerador por proveedor** antes de continuar, con el mismo
esquema de fila (`provider`, `stable_property_id`, `residential_eligibility`,
`source_version`), y materializar los pools forales; despues, y solo despues,
hash + seleccion + commit de `p0r_frame.json`. Sin cambios de umbrales.
