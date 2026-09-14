# Preflight — ITE/IEE y CEE (disponibilidad y licencia)

- Fase 1. Fecha: 2026-09-14. Solo investigacion; no se construye ni integra nada.
- Metodo: catalogo nacional `datos.gob.es` (API `apidata/catalog/dataset/title/...`)
  y portales autonomicos.

## ITE / IEE (Inspeccion Tecnica de Edificios / Informe de Evaluacion)

- `datos.gob.es` `title/inspeccion tecnica edificios` -> **0 resultados**.
- `datos.gob.es` `title/informe evaluacion edificio` -> **0 resultados**.
- El dato es **municipal** y heterogeneo; no hay conjunto abierto consolidado.

**Veredicto: NOT AVAILABLE** como fuente lista. Requeriria trabajo municipal
caso a caso (alto esfuerzo, licencia incierta). No se prioriza.

## CEE (Certificado de Eficiencia Energetica)

`datos.gob.es` `title/certificado energetico` -> 0; `title/eficiencia energetica`
-> 2: un indicador agregado de Euskadi y un registro de Cantabria. Es decir, no
hay API nacional; el dato es **autonomico**.

| Region | Recurso | Formato | Contenido | Licencia |
|--------|---------|---------|-----------|----------|
| Cataluna | Socrata `analisi.transparenciacatalunya.cat` dataset `j6ii-t3w2` "Certificats d'eficiència energètica d'edificis" | JSON/CSV (Socrata) | **por edificio**: `referencia_cadastral`, `metres_cadastre`, `adre_a`, `qualificaci_de_consum_d`, `cost_anual_aproximat_d_energia`, ... | "See Terms of Use" (portal catalan) |
| Cantabria | `dgicc.cantabria.es` `DATOS_RCEEC-...` | CSV / XLSX / ZIP | Registro de certificados | no especificada en catalogo |
| Euskadi | `opendata.euskadi.eus` | indicador | **agregado municipal** (no por edificio) | — |
| Nacional | — | — | no existe API nacional | — |

Ejemplo real (Cataluna, primera fila):

```text
referencia_cadastral = 9533603DG4393S0001LT
metres_cadastre      = 62.81
qualificaci_de_consum_d = E
cost_anual_aproximat_d_energia = 2054.66
adre_a = Carrer Pietat, 17406 Viladrau
```

**Veredicto: PARTIAL / PROMISING (regional).** No hay fuente nacional; el CEE de
Cataluna es rico (refcat + superficie oficial + calificacion + coste) y ademas
habilita la **discrepancia de superficie** sin fuente nueva. Cantabria aporta CSV.
Euskadi solo agregado. Cualquier adopcion exige un adaptador por region con su
`LICENSE.yaml` y su gate.

## Implicacion para producto

- **CEE (Cataluna)** es la dimension con mejor relacion valor/dato: accion
  concreta (calificacion, coste anual) y dato por edificio con refcat.
- **ITE/IEE** no es viable como fuente abierta hoy: se descarta sin construir.
- El CEE Cataluna tambien alimenta la capacidad de **discrepancia de superficie**
  (`metres_cadastre` oficial).
