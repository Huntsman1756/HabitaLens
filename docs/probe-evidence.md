# Evidencia del probe G0-A

Fecha: 2026-09-14. Python 3.12 (uv). Windows. Endpoints publicos anonimos.

## Comandos reproducibles

```bash
# Tests offline (sin red)
uv run pytest
uv run ruff check

# Probe live por proveedor (5 casos) + CartoCiudad
$env:HABITALENS_CACHE="$PWD/.habitalens-probe"
uv run python scripts/probe_live.py

# Probe live E2E (direccion -> CartoCiudad -> router -> proveedor -> parcela)
uv run python scripts/probe_e2e.py

# Reconstruir fixtures congeladas desde las capturas live
uv run python scripts/build_fixtures.py
```

## Endpoints verificados (config/endpoints.yaml)

| Proveedor | WFS | Tipos | CRS por defecto | ATOM |
|-----------|-----|-------|-----------------|------|
| DGC | `ovc.catastro.meh.es/INSPIRE/wfs{CP,BU,AD}.aspx` (stored queries) + `Consulta_DNPRC` REST | `cp:CadastralParcel`, `bu-ext2d:Building`, `ad:Address` | EPSG:4326 | jerarquico provincia -> municipio |
| Navarra | `idena.navarra.es/ogc/inspire/wfs` (CP) + `/ogc/wfs` (CATAST_) | `CP:CadastralParcel`, `IDENA:CATAST_Pol_Edificacion`, `IDENA:CATAST_Txt_Portal` | EPSG:4258 / 25830 | no INSPIRE |
| Bizkaia | ArcGIS `.../Catastro/Annex1/...` + `.../Buildings/...` | `cp:CadastralParcel`, `ad:Address`, `bu-core2d:Building` | EPSG:4258 | `apli.bizkaia.eus/.../ES.BFA.CP|BU|AD.<mun>.zip` |
| Gipuzkoa | `b5m.gipuzkoa.eus/inspire/wfs/gipuzkoa_wfs_{cp,bu,ad}` | `cp:CadastralParcel`, `bu-ext2d:Building`, `ad:Address` | EPSG:4258 | `b5m.gipuzkoa.eus/inspire/download/*.xml` |
| Araba | `geo.araba.eus/WFS_INSPIRE_{CP,BU}` | `INSPIRE_CP:CP.CadastralParcel`, `INSPIRE_BU:BU.Building` | EPSG:25830 | `geo.araba.eus/atom/{CP,BU}/*.atom` |

CartoCiudad: `cartociudad.es/geocoder/api/geocoder/{candidates,find,reverseGeocode}`.

## Resultado live por proveedor (probe_live)

| Proveedor | refcat caso | parcela | area_m2 | CRS | edificios | version | estado |
|-----------|-------------|---------|---------|-----|-----------|---------|--------|
| DGC | 1707903VK4810F | si | 519.0 | EPSG:4326 | 1 | 2.0.0 | PASS (G0-A.1) |
| Navarra | 001010001 | si | 101.28 | EPSG:4258 | 3 | 2.0.0 | PASS |
| Bizkaia | 48.020.1619.04006 | si | 2804.43 | EPSG:4258 | 6 | 1.1.0 | PASS |
| Gipuzkoa | 8594149 | si | 13201.0 | EPSG:4258 | 5 | 2.0.0 | PASS |
| Araba | 64010007 | si | 10830.82 | EPSG:25830 | 0 (rustico) | 2.0.0 | PASS |

Suplementario urbano Araba: `Calle Postas 1, Vitoria-Gasteiz` -> parcela
`59590687` (777.56 m2, EPSG:25830) + 7 edificios.

DGC por localizacion (fallback): `get_parcel_near(40.416461, -3.704658)` ->
parcela `0343302VK4704C`, area 1179 m2, EPSG:4326.

## Resultado live E2E (probe_e2e)

| Direccion | territorio | refcat parcela | CRS | edificios | estado |
|-----------|------------|----------------|-----|-----------|--------|
| Calle Mayor 1, Madrid | dgc | 0343302VK4704C | EPSG:4326 | 0 (BU sin BBOX) | PASS (parcela) |
| Calle Mayor 1, Donostia | gipuzkoa | 8297093 | EPSG:4258 | 4 | PASS |
| Gran Via 1, Bilbao | bizkaia | 48.020.1619.04006 | EPSG:4258 | 6 | PASS |
| Calle Postas 1, Vitoria-Gasteiz | araba | 59590687 | EPSG:25830 | 7 | PASS |

## Fixtures congeladas

`tests/fixtures/data/` contiene capturas reales (recortadas a la evidencia
necesaria) de: capabilities, respuestas de parcela y edificio de los cinco
proveedores, feeds ATOM (DGC y Bizkaia) y respuestas de CartoCiudad. Los tests
offline no realizan llamadas de red.

## G0-A.1: evidencia DGC corregida

Stored queries (verificadas con `ListStoredQueries`):

```text
CP: GetParcel, GetZoning, GetFeatureById, GetNeighbourParcel, GetParcelsByZoning
BU: GetBuildingByParcel, GetBuildingPartByParcel, GetOtherBuildingByParcel,
    GetAllConstructionByParcel, GetFeatureById
```

| Prueba | Comando (resumen) | Resultado |
|--------|-------------------|-----------|
| GetParcel positivo | `wfsCP.aspx?...STOREDQUERY_ID=GetParcel&refcat=1707903VK4810F` | `nationalCadastralReference=1707903VK4810F`, 2919 B |
| GetParcel positivo 2 | `...&refcat=0343302VK4704C` | `nationalCadastralReference=0343302VK4704C`, 3001 B |
| GetParcel negativo | `...&refcat=0000000XX0000X` | `No se ha encontrado la parcela ...` (distinto) |
| GetBuildingByParcel | `wfsBU.aspx?...STOREDQUERY_ID=GetBuildingByParcel&refcat=1707903VK4810F` | `ES.SDGC.BU.1707903VK4810F`, 6057 B |
| DNPRC positivo | `COVCCallejero.svc/rest/Consulta_DNPRC?RefCat=1707903VK4810F` | `cp=28 cm=79 MADRID`, `PS CASTELLANA 255`, sfc 564 |
| DNPRC negativo | `...RefCat=0000000XX0000X` | `NO EXISTE NINGUN INMUEBLE ...` |
| RCCOOR | `COVCCoordenadas.svc/...` (lon,lat Madrid) | `pc1=0343302 pc2=VK4704C` |

Correccion de la suposicion: `1707903VK4810F` es de **Madrid (28/079)**, no de
Fortia (17/079). El feed ATOM de la provincia 28 omite el municipio 28079
(`A.ES.SDGC.CP.28079.zip` ausente; `...28080.zip` presente), por lo que el
ATOM municipal no aplica a esa RC. La via oficial es la stored query.
