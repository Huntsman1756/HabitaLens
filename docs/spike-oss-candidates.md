# Spike — candidatos OSS (aislado, sin tocar el core)

- Fecha: 2026-09-14. Metadatos via `gh repo view` (estrellas/licencia/ultimo push).
- Objetivo: mapear OSS publico a los problemas **abiertos reales**, sin integrar
  nada en el core (regla: no anadir fuentes a ciegas, no abrir gates).

| Repo | Licencia | ★ | Ultimo push | Que aporta | Veredicto |
|------|----------|---|-------------|------------|-----------|
| `gboeing/osmnx` | MIT | 5.843 | 2026-07 | Redes viarias y features de OSM (infraestructura, landuse) | **ADOPT-CANDIDATE** (fase producto) |
| `ernestofgonzalez/trece` | Apache-2.0 | 4 | 2025-05 | CLI que descarga datos oficiales de CartoCiudad (portales, viales, limites) en GeoPackage | **REFERENCE/ADOPT-CANDIDATE** |
| `IDEESpain/Cartociudad` | EUPL-1.2 | 5 | 2026-07 | Servicio REST oficial de CartoCiudad (geocoder) | **REFERENCE** |
| `paezha/idealista18` | ODbL-1.0 | 58 | 2024-11 | Anuncios Idealista 2018 (coords **alteradas** por privacidad) | **REFERENCE** (no parcelario) |
| `rOpenSpain/caRtociudad` | sin licencia | 25 | 2022-06 | Cliente R | **DISCARD** (sin licencia, sin mantenimiento) |
| `PyLadiesMadrid/pycartociudad` | GPL-3.0 | 4 | 2020-12 | Cliente Python | **DISCARD** (GPL-3, abandonado; ya tenemos cliente propio) |
| `gala1234/iberplot` | sin licencia | 0 | 2026-02 | PropTech SNCZI/planeamiento | **DISCARD** (licencia nula, 0★, no auditable) |
| `juanzotes/costa-del-sol-flood-risk`, `MapGuru3910/spain-flood` | other/sin licencia | 0 | — | Pipelines SNCZI | **DISCARD** (no auditables) |

## Conclusiones

1. **No hay bala de plata.** El nicho cadastral espanol en OSS es escaso; G0-A ya
   implementa lo que estas librerias ofrecen (`pycartociudad`/`caRtociudad` solo
   envuelven la API; ya tenemos cliente propio y sin GPL).
2. **Candidato 1 (producto): `osmnx` (MIT).** Para la dimension "infraestructura
   /ruido proximo no evidente" y contexto de barrio, sin depender de portales.
   Entra en la fase de producto, no antes.
3. **Candidato 2 (datos): `trece` (Apache-2.0).** Empaqueta datos oficiales de
   CartoCiudad en GeoPackage (portales con `num`, `cod_postal`, `dgc_via`,
   viales). Util para: (a) acelerar descargas forales/direcciones; (b) base de
   contraste para la discrepancia de superficie/direccion. Requiere `LICENSE.yaml`
   propio (dato subyacente IGN/CartoCiudad) antes de usarse.
4. **Nada se integra en el core** por este spike. Cualquier adopcion requiere
   preregistro con su `LICENSE.yaml` y su gate.

## Uso recomendado (cuando toque)

- `osmnx` y `trece` se evaluarian en **spike aislado** con una sola pregunta de
  producto (p. ej. "distancia a vias principales y ferrocarril"), midiendo si
  cambia la accion del comprador, no por completitud de fuentes.
