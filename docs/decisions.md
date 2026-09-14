# Decisiones de G0-A

Registro de decisiones tecnicas del gate **G0-A (adquisicion y legal)** de
HabitaLens. Toda decision se apoya en evidencia ejecutada (ver
`docs/probe-evidence.md`).

## 1. Composicion: geocodificacion separada de adquisicion

```text
direccion -> CartoCiudad -> localizacion / refcat candidato
          -> TerritoryRouter -> CadastreProvider -> parcela + edificios
```

`CadastreProvider` no geocodifica; ningun proveedor implementa
`resolve_address()` (verificado por test). CartoCiudad se implementa como
cliente propio (`geocoding/cartociudad.py`); no se usa `pycartociudad`.

## 2. Estrategia de routing (decision elegida)

**Decision:** encaminar por el **territorio devuelto por el geocoder**
(codigo de provincia INE) y, cuando existe, usar la **localizacion**
(coordenadas) como metodo de adquisicion preferente. El patron/prefijo del
refcat se usa como corroboracion o cuando no hay geocoder.

**Evidencia:**

- `Calle Mayor 1, Madrid` -> CartoCiudad `provinceCode=28` + refcat
  `0343302VK4704C` -> `TerritoryRouter` -> `dgc` -> parcela
  `0343302VK4704C` (via BBOX localizado) -> PASS.
- `Calle Mayor 1, Donostia` -> CartoCiudad `provinceCode=20` ->
  `TerritoryRouter` -> `gipuzkoa` -> parcela `8297093` + 4 edificios -> PASS.
- Un refcat foral de CartoCiudad no es directamente el refcat del proveedor
  (p.ej. Donostia `0698297362` no coincide con el `nationalCadastralReference`
  de Gipuzkoa). Por eso la **localizacion** es mas fiable que el refcat.

**Desambiguacion:** CartoCiudad puede devolver coincidencias de otras
provincias; `CartoCiudadClient.geocode` desambigua por localidad de la
consulta antes de aceptar un candidato.

## 3. Adquisicion por proveedor: capacidades verificadas

| Proveedor | Filtro de atributo (refcat) | BBOX (localizacion) | Edificios |
|-----------|-----------------------------|---------------------|-----------|
| DGC | **No** (WFS ignora `filter`/`resourceId`) | **Si** (orden `lat,lon`) | BBOX no soportado live |
| Navarra | Si (`nationalCadastralReference`, sin prefijo) | Si | Si (`IDENA:CATAST_Pol_Edificacion`) |
| Bizkaia | **No** (ArcGIS ignora FES/CQL) | Si (orden `lat,lon`) | Si (`bu-core2d:Building`) |
| Gipuzkoa | Si (`cp:nationalCadastralReference`) | Si (orden `lat,lon`) | Si (`bu-ext2d:Building`) |
| Araba | Si (`INSPIRE_CP:nationalCadastralReference`) | Si (proyectado 25830) | Si (`BU.Building`) |

Notas de implementacion:

- El orden de eje del BBOX es heterogeneo. Se configura por proveedor
  (`bbox_axis_buildings`, `bbox_crs_style_buildings`) segun evidencia:
  Gipuzkoa/Navarra usan `lon,lat` y `EPSG:xxxx`; Bizkaia/Araba usan `lat,lon`
  y URN `urn:ogc:def:crs:EPSG::xxxx`.
- DGC y Bizkaia no permiten resolver por refcat con WFS. Bizkaia se resuelve
  por **ATOM municipal** (feed -> ZIP por municipio -> filtrado local por
  refcat); verificado con `48.020.1619.04006`.

### 3.1 DGC: hallazgo y fallback

El caso preregistrado DGC `1707903VK4810F` **no puede resolverse por refcat**
con las fuentes WFS+ATOM:

1. El WFS de la DGC ignora los filtros ad-hoc (devuelve una pagina fija de 83
   parcelas; un refcat inexistente devuelve el mismo resultado).
2. El ATOM municipal de Fortia (municipio 17079) codifica sus parcelas como
   `0003001...`, que **no** es el refcat `1707903VK4810F` devuelto por el WFS
   y por CartoCiudad (0 coincidencias de 1539 parcelas).
3. El servicio BU no acepta BBOX live.

**Fallback documentado (aplicado):** resolver la parcela DGC por
**localizacion** (BBOX `lat,lon` sobre `wfsCP.aspx`) usando las coordenadas
que CartoCiudad ya devuelve para la direccion. Verificado:
`Calle Mayor 1, Madrid` -> parcela `0343302VK4704C` (area 1179 m2).

## 4. CartoCiudad

- Endpoints en `config/endpoints.yaml` (`candidates`, `find`, `reverse`).
- `find` puede devolver coincidencias de otra provincia; se desambigua con
  `candidates` por localidad.
- Si CartoCiudad no devuelve refcat suficiente para un territorio foral, **no
  se marca FAIL**: la resolucion usa la localizacion (coordenadas) contra el
  proveedor enrutado y, si tampoco es posible, la CLI devuelve
  `INCONCLUSIVE` (exit code 2).

## 5. CRS

- La adquisicion conserva el **CRS original** del proveedor; se registra en
  cache y provenance (`EPSG:4326` DGC, `EPSG:4258` Navarra/Gipuzkoa/Bizkaia,
  `EPSG:25830` Araba).
- No se reproyecta para analisis espacial. La unica reproyeccion es
  operativa: el BBOX de una consulta por localizacion cuando el servicio usa
  CRS proyectada (Araba).
- EPSG:25830 solo aparece como CRS nativo de Araba y como simplificacion de
  fixtures; **no** es una invariancia nacional.

## 6. Geometria (guarda de no exposicion)

- Los objetos publicos (`Parcel`, `Building`, `Property`, `Address`, `RefCat`,
  `TerritoryMask`) no contienen geometria ni coordenadas.
- La geometria se escribe exclusivamente en cache GeoParquet local
  (`~/.habitalens/cache/geo/<provider>/`).
- Hay tests que verifican que ningun campo publico usa tokens de geometria y
  que la serializacion no contiene `posList`, `Polygon`, `MultiSurface`,
  `geojson` ni `__geo_interface__`.

## 7. Licencias

- Cada paquete `cadastre_providers/*/` lleva `LICENSE.yaml` con autoridad,
  licencia, URL, fecha de verificacion y version aplicable.
- `licensing.audit_providers()` recorre los paquetes; `CadastreProvider.__init__`
  carga la licencia ANTES de cualquier operacion y lanza
  `LicensingNotDeclaredError` si falta, esta vacio o le faltan campos.
- El guard no se desactiva, mockea ni relaja en ningun test.

## 8. Cache y provenance

- Cache cruda + GeoParquet bajo `~/.habitalens/cache/` (configurable con
  `HABITALENS_CACHE`).
- Metadatos por entrada: proveedor, fecha de captura, version, CRS, procedencia
  y `sha256`.
- Refetch explicito con `--refresh`.
- Provenance append-only en `~/.habitalens/provenance/provenance.jsonl`,
  registrando la version/esquema realmente observado.
