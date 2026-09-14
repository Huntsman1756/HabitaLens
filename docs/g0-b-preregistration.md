# G0-B — Preregistro (congelado antes de ejecutar fuentes nuevas)

Estado: **preregistrado**. Referencia de partida: G0-A `PASS`, etiqueta
`g0-a-pass` (commit `b0b63d0d920f167c1c2140006c8c22ee2e7ffffd`).

Este documento fija alcance, hipotesis, fuentes, propiedades, metodo y
criterios de aceptacion **antes** de ejecutar ninguna fuente nueva. Cualquier
cambio posterior debe registrarse como enmienda explicita (seccion 13).

## 0. Pregunta del gate

> Podemos convertir geometria de propiedad + fuentes oficiales heterogeneas en
> hallazgos espaciales deterministas, reproducibles y correctamente
> distinguidos entre OBSERVED, DERIVED y UNAVAILABLE?

No es un gate de "descargar datasets", sino de **evidencia espacial**.

## 1. Principios congelados heredados de G0-A

1. **DGC no se modela alrededor de ATOM.** Resolucion puntual por stored
   queries `GetParcel`/`GetBuildingByParcel`; `Consulta_DNPRC` como
   corroboracion. ATOM es capacidad auxiliar/bulk y no se asume completo
   territorialmente (Madrid capital 28079 esta ausente del feed).
2. **Routing: territorio/localizacion primero**; el refcat identifica la
   autoridad, no es clave territorial universal (formatos forales distintos).
3. **Capability matrix por proveedor** (seccion 2): no se fuerza uniformidad
   INSPIRE.
4. **CRS:** se conserva `source_crs`; toda operacion de distancia/interseccion
   se hace en un **CRS operacional explicito** adecuado al territorio; no se
   asume EPSG:25830 nacional.
5. **Ninguna salida publica serializa geometria.** La geometria vive en
   cache/DB local.
6. **Offline por fixtures**; captura live separada y reproducible.

## 2. Capability matrix asumida

```text
DGC       CP si   BU si    AD si   ATOM parcial (no completo)
Navarra   CP si   BU local AD local
Bizkaia   CP si   BU si    AD si   ATOM si
Gipuzkoa  CP si   BU si    AD segun servicio
Araba     CP si   BU si    AD no
```

## 3. Alcance de G0-B

- **Spatial evidence core**: modelo comun de hallazgo espacial + motor
  determinista de interseccion/distancia sobre geometria de propiedad
  (interna) contra capas oficiales.
- **Fuentes nuevas (3):** SNCZI, CSN radon, E-PRTR.
- **6–8 propiedades preregistradas** (seccion 5).
- Taxonomia OBSERVED / DERIVED / UNAVAILABLE / INCONCLUSIVE.
- Fixtures congeladas + tests offline + evidencia live separada.

Fuera de alcance (no se implementa en G0-B): reglas de riesgo y umbrales
normativos, scores, informes, HTML/PDF, visor web, IA, usuarios, pagos,
historico inmobiliario, reproyeccion como fin en si mismo.

## 4. Fuentes G0-B (hipotesis a verificar; endpoints NO ejecutados aun)

| Fuente | Que se busca | Hipotesis de acceso (a validar en G0-B) |
|--------|--------------|-----------------------------------------|
| SNCZI | Zonas inundables (MITECO) | Servicios OGC descarga/WMS/WFS del MITECO; capas de peligrosidad/dominio publico hidraulico |
| CSN radon | Potencial de radon / zonas | Cartografia de radiacion natural del CSN / visor institucional |
| E-PRTR | Emisiones/instalaciones industriales | E-PRTR (EIONET/AEMA) y/o nodo nacional MITECO |

Cada endpoint concreto, licencia y version se registraran en
`config/endpoints.yaml` + `LICENSE.yaml` antes de usarse, igual que en G0-A.

## 5. Propiedades preregistradas (seleccion por diversidad, NO por resultado)

La seleccion se hace por diversidad territorial y de contexto (urbano,
costero, fluvial, industrial, rural). **No se afirma** que alguna de ellas
este dentro/fuera de una zona de inundacion, radon o emision; eso es
precisamente lo que el gate debe medir.

| # | Fuente de la parcela | refcat | Contexto |
|---|----------------------|--------|----------|
| 1 | DGC | `1707903VK4810F` | Madrid, eje Castellana (urbano denso) |
| 2 | DGC | `0343302VK4704C` | Madrid, casco historico |
| 3 | DGC | `8297093` | Donostia, urbano costero |
| 4 | DGC | `59590687` | Vitoria-Gasteiz, urbano interior |
| 5 | Bizkaia | `48.020.1619.04006` | Bilbao, urbano industrial-portuario |
| 6 | Gipuzkoa | `8594149` | Gipuzkoa, parcela amplia periurbana |
| 7 | Navarra | `001010001` | Navarra, urbano (posible entorno fluvial) |
| 8 | Araba | `64010007` | Araba, rustico interior |

## 6. Taxonomia de hallazgos

Cada hallazgo se clasifica en exactamente uno de:

- **OBSERVED**: la fuente oficial contiene una entidad que intersecta/aplica a
  la geometria de la propiedad, con metodo y version documentados.
- **DERIVED**: resultado calculado por HabitaLens a partir de una o mas
  entidades observadas (p. ej. distancia a una instalacion).
- **UNAVAILABLE**: la fuente no cubre la propiedad o no existe capa aplicable
  en su ambito (no es error).
- **INCONCLUSIVE**: la fuente no pudo descargarse/verificarse de forma
  suficiente. Nunca se convierte en UNAVAILABLE ni se inventan datos.

## 7. Politica CRS (primer asunto tecnico de G0-B)

- Cada evidencia guarda `source_crs` y `operational_crs`.
- Operaciones de distancia/interseccion en el CRS operacional explicito del
  territorio (zonas UTM ETRS89 coherentes: 29/30/31 segun area), nunca por
  asumir EPSG:25830 nacional.
- El hallazgo G0-A de Gipuzkoa (`EPSG:5730`, compuesto/vertical) se trata
  explicitamente: para operaciones 2D se usa la componente horizontal y se
  documenta la vertical; si no puede separarse, se marca INCONCLUSIVE.

## 8. Determinismo y reproducibilidad

- Regla: misma entrada + misma version de fixture = mismo resultado.
- Tests offline con fixtures congeladas; nada de red en CI.
- Captura live separada (`--refresh` explicito), provenance append-only con
  version/esquema observado.

## 9. Determinismo de evidencia (formato publico, sin geometria)

Cada hallazgo expone: `property_id`, `source`, `source_version`, `kind`,
`status` (OBSERVED/DERIVED/UNAVAILABLE/INCONCLUSIVE), `source_crs`,
`operational_crs`, `method`, `inputs`, `provenance_id`, y valores numericos
derivados (p. ej. distancia en unidades explicitas). Sin coordenadas ni
geometria catastral.

## 10. Criterios de aceptacion

Por fuente:

- **PASS** si para al menos las propiedades cubiertas se obtiene OBSERVED (o
  DERIVED correctamente justificado) con evidencia live positiva y el
  correspondiente test offline; y existe control negativo (propiedad fuera de
  cobertura/entidad) con resultado distinto.
- **INCONCLUSIVE** si no puede verificarse de forma suficiente.
- **FAIL** si hay error reproducible o resultado incorrecto.

Core:

- Interseccion/distancia deterministas y trazables; taxonomia aplicada sin
  ambiguedad; ningun dato inventado; sin geometria en salida publica.

Global G0-B: PASS / FAIL / INCONCLUSIVE derivado de los gates reales.

## 11. Artefactos esperados

- `src/habitalens/evidence/` (modelo + motor).
- `src/habitalens/sources/{snczi,csn_radon,eprtr}/` con `LICENSE.yaml`.
- `tests/` contract + golden + determinism por fuente.
- `docs/decisions.md`, `docs/probe-evidence.md` actualizados.

## 12. Riesgos y supuestos

- SNCZI/CSN/E-PRTR pueden requerir formatos/geoservicios no estandar; se
  valida con `GetCapabilities`/metadatos antes de codificar.
- Cobertura heterogenea (estatal/autonomica/local) que obliga a UNAVAILABLE
  honesto.
- El CRS compuesto de algunos proveedores forales exige disciplina 2D/3D.

## 13. Enmiendas

Cualquier cambio de alcance, fuente, propiedad o criterio se anade aqui con
fecha y justificacion, antes de ejecutar la fuente afectada.

- (sin enmiendas)
