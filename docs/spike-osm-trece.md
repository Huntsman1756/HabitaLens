# Spike aislado — `osmnx` y `trece` (Fase 2)

- Fecha: 2026-09-14. Aislado; **no toca el core**.
- Pregunta unica: la proximidad a vias principales / ferrocarril, anade algo a
  BTN (ya integrado) y cambia la accion del comprador?
- Script reproducible: `scripts/spike_osm.py`.

## osmnx (MIT, 5.843★, activo)

Version usada: `osmnx 2.1.1`. Punto de prueba: parcela DGC de G0-A
(Paseo de la Castellana 255, Madrid; `40.474018, -3.687913`), radio 800 m.

Resultado real:

```text
features (LineString): 391
nearest distance: 4.5 m  -> railway=subway, name="Linea 1"
major_roads nearest: 28.0 m
```

**Comparacion con BTN:** en ese mismo punto, la capa BTN INSPIRE
(`tn-ro:RoadLink`/`tn-ra:RailwayLink`) **no** devolvio proximidad util (BTN no
incluye metro urbano ni vias menores con ese encuadre). Es decir, **OSM aporta
senal que BTN no tiene** (metro a 4,5 m).

**Veredicto: ADOPT-CANDIDATE.** Candidato claro para la dimension de producto
"infraestructura/transporte proximo no evidente". Entra en fase de producto, en
spike aislado, no en el core todavia.

## trece (Apache-2.0, 4★, 2025-05)

CLI verificado: `trece download --province <PROV> --output <DIR>`. Descarga el
GeoPackage de CartoCiudad (IGN) por provincia con capas de **portales**
(`nombre_via`, `numero`, `cod_postal`, `dgc_via`, ...), viales y limites.
Dato subyacente: CartoCiudad / IGN (CC BY 4.0).

**Veredicto: REFERENCE / ADOPT-CANDIDATE.** Util como base de direcciones/viales
oficial y para contrastar direccion/superficie; requiere `LICENSE.yaml` propio
(CartoCiudad/IGN) antes de usarse. No se integra ahora.

## Conclusion

- `osmnx` responde a la pregunta con evidencia medible y complementa a BTN.
- `trece` es un acelerador de datos oficiales, no un sustituto del geocoder.
- Ninguno se incorpora al core en esta fase; ambos quedan como candidatos con
  licencia declarada para cuando la dimension de producto correspondiente se
  priorice.
