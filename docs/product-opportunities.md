# Product opportunities (post-P0-RD, sin abrir gates)

Contexto: el motor, los 5 proveedores, la semantica de cobertura y el informe
estan **probados** (G0-A..D). P0-RD apunta a **FAIL de utilidad** con el set de
fuentes actual. La pregunta ya no es GIS, es **que informacion cambia de verdad
la decision del comprador**.

Este documento es investigacion, no implementacion. No abre gate ni anade fuente.

## Criterios

Una dimension entra en la shortlist solo si: (a) genera una **accion concreta**
antes de ofertar; (b) su dato es **oficial o contrastable**; (c) no depende del
canal de anuncios bloqueado.

## Dimensiones candidatas

| Dimension | Accion que provoca | Dato | Estado | Esfuerzo |
|-----------|--------------------|------|--------|----------|
| **Discrepancia superficie anunciada vs oficial** | Contrastar con Catastro; renegociar/verificar | Superficie oficial ya la tenemos (`Parcel.area_m2`, DNPRC) + superficie del anuncio (input) | Datos ya disponibles (falta input) | **Bajo** |
| **ITE/IEE (estado/antiguedad del edificio)** | Pedir informe; inspeccion; presupuesto de obra | Municipal, heterogeneo, poco abierto | Nuevo; requiere preflight de disponibilidad | Medio-alto |
| **Limitaciones urbanisticas** (reformas/usos) | Consultar planeamiento municipal | SIU da clase de suelo; el planeamiento fino es municipal | Parcial (SIU ya integrado) | Medio |
| **Inundacion real** | Seguro; cota; obra | SNCZI (ya integrado) | Integrado; aparece poco | Bajo (ya) |
| **Ruido / infraestructura muy proxima** | Verificar en visita; alegaciones | Mapas de ruido municipal + OSM (`osmnx`, MIT) + BTN | BTN ya integrado; ruido nuevo | Medio |
| **CEE (certificado energetico)** | Pedir CEE; presupuesto eficiencia | Registros autonomicos fragmentados | Nuevo; sin API comun | Alto |
| **Costes/fiscalidad** | Presupuestar ITP/IBI/plusvalia | Computable por region; requiere precio | Depende de precio (canal bloqueado) | Medio |
| **Contexto de precio** | Negociar | Datos de mercado (portales) | Canal bloqueado (P0/idealista18 degradado) | Alto |

## Hipotesis

El valor no esta en peligrosidad sismica ni en una instalacion E-PRTR a 2 km.
Estara en lo **pegado a la operacion**: discrepancia de superficie, estado/ITE,
limitaciones urbanisticas, inundacion real, ruido/infraestructura no evidente,
CEE y situacion documental.

## Recomendacion (2 capacidades)

1. **Discrepancia de superficie anunciada vs oficial** (bajo esfuerzo, dato ya
   disponible): solo falta el campo "superficie anunciada". No requiere fuente
   nueva externa; es el mejor candidato para mover la aguja.
2. **ITE/IEE + estado del edificio** (alto valor): primero un **preflight** de
   disponibilidad/licencia por municipio; si no hay dato abierto, se descarta sin
   construir nada.

`osmnx`/`trece` quedan como herramientas para la dimension ruido/infraestructura,
a evaluar en spike aislado solo si esa dimension se prioriza.

## Regla de gestion

No se implementa ninguna de estas hasta: (a) cerrar P0-RD con revision humana; y
(b) elegir **2-3 dimensiones** por valor esperado, con preflight de dato y
licencia. Nada de "anadir fuentes a ciegas".
