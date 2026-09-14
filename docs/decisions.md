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
| DGC | **Si** (stored query `GetParcel`) | **Si** (orden `lat,lon`) | **Si** (stored query `GetBuildingByParcel`) |
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

### 3.1 DGC: remediacion (G0-A.1)

Una primera version de G0-A concluyo (de forma erronea) que `refcat -> parcela`
estaba roto en la DGC. La causa real fue doble:

1. **Mecanismo equivocado.** La DGC no expone la busqueda por RC mediante
   `filter`/`resourceId`, sino mediante **stored queries**:
   `STOREDQUERY_ID=GetParcel&refcat=<RC>` (CP) y
   `STOREDQUERY_ID=GetBuildingByParcel&refcat=<RC>` (BU). Verificado en
   `ListStoredQueries` de ambos servicios.
2. **Suposicion invalida de municipio.** La RC urbana **no** codifica el
   municipio en sus primeros caracteres. Se asumio que `1707903VK4810F`
   pertenecia a Fortia (17/079) por empezar por `17079`, y en realidad
   pertenece a **Madrid (28/079)**. Lo confirma `Consulta_DNPRC`
   (`cp=28 cm=79 np=nm=MADRID`, `PS CASTELLANA 255`, sfc 564). El
   ATOM de Fortia jamas podia contener esa parcela.

**Estado corregido (verificado):**

- `GetParcel` devuelve exactamente `1707903VK4810F` (519 m2, EPSG:4326) y
  `0343302VK4704C`; el control negativo `0000000XX0000X` devuelve
  `No se ha encontrado la parcela ...` (resultado distinto).
- `GetBuildingByParcel` devuelve el edificio
  `ES.SDGC.BU.1707903VK4810F` (EPSG:25830).
- `Consulta_DNPRC` corrobora existencia, provincia/municipio oficiales, area y
  uso (`Almacen-Estacionamiento`).

**Hallazgo adicional (no bloqueante):** el feed ATOM de la provincia 28
(Madrid) **omite el municipio 28079 (Madrid capital)**; por eso el ATOM
municipal no sirve como via de resolucion para esta RC. La via oficial de
resolucion por RC son las stored queries.

**Fallback conservado:** `get_parcel_near` (BBOX `lat,lon` sobre `wfsCP.aspx`)
se mantiene para direccion -> localizacion -> parcela, y como respaldo cuando
no se dispone de RC. Verificado: `Calle Mayor 1, Madrid` -> parcela
`0343302VK4704C` (area 1179 m2).

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

## 8. G0-B: evidencia espacial

### 8.1 Taxonomia (sin ambiguedad)

`OBSERVED` (la fuente intersecta/aplica) · `DERIVED` (calculado) ·
`UNAVAILABLE` (fuente disponible pero sin cobertura/dato) · `INCONCLUSIVE`
(no verificable). Las fuentes no activadas o con error se emiten como
INCONCLUSIVE; nunca se degradan a UNAVAILABLE.

### 8.2 Acceso verificado por fuente

| Fuente | Acceso | CRS fuente | Licencia | Verificado |
|--------|--------|-----------|----------|------------|
| SNCZI | WFS 2.0 `gis.miteco.gob.es/geoserver/agua/wfs` | EPSG:4258 (acepta 4326) | CC BY 4.0 | si |
| E-PRTR | ArcGIS REST `.../arcgis/rest/services/Air/IED_SiteMap/MapServer/0/query` (GeoJSON) | EPSG:4326 | CC BY 4.0 | si |
| CSN radon | sin OGC; GDB + JSON de webmap | EPSG:4326 (WebMercator embedido) | **sin licencia abierta declarada** | si |

### 8.3 Decision CSN

CSN **no se activa** como fuente productora: no hay servicio OGC verificado y
no declara licencia abierta. Conforme a "licencia y acceso antes que parsing",
solo aporta un hallazgo `INCONCLUSIVE`. Se reconsiderara si publica licencia
declarada y acceso reproducible.

### 8.4 Politica CRS operacional

`source_crs` se conserva en cada evidencia. Toda operacion de interseccion o
distancia se hace en un CRS operacional explicito: zona UTM ETRS89
(25829/25830/25831) elegida por la longitud del centroide. No se asume
EPSG:25830 nacional. Los CRS compuestos se reducen a su componente horizontal
(`EPSG:5730 -> EPSG:25830`) para operaciones 2D.

### 8.5 Determinismo

Clave de cache por fuente = `fuente:kind:clave:hash(url+params)`; cambiar bbox,
radio o capa nunca reutiliza una respuesta obsoleta. Regla de replay: misma
propiedad + misma version de fuente + misma regla = mismos hallazgos.

## 9. Cache y provenance

- Cache cruda + GeoParquet bajo `~/.habitalens/cache/` (configurable con
  `HABITALENS_CACHE`).
- Metadatos por entrada: proveedor, fecha de captura, version, CRS, procedencia
  y `sha256`.
- Refetch explicito con `--refresh`.
- Provenance append-only en `~/.habitalens/provenance/provenance.jsonl`,
  registrando la version/esquema realmente observado.
