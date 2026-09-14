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

## G0-B: evidencia espacial (2026-09-14)

Comandos:

```bash
uv run python scripts/capture_g0b.py     # captura live -> fixtures + resultados
uv run python scripts/probe_g0b.py       # probe live por fuente + replay corpus
uv run pytest                            # replay offline determinista
```

Fuentes y accesos verificados:

| Fuente | Endpoint | Resultado |
|--------|----------|-----------|
| SNCZI | `gis.miteco.gob.es/geoserver/agua/wfs` (`agua:Zi_laminas_q100`, `agua:DPH_Deslindado`) | WFS 200; control Ebro Q100=True |
| E-PRTR | `air.discomap.eea.europa.eu/arcgis/rest/services/Air/IED_SiteMap/MapServer/0/query` (GeoJSON) | 200; control Bilbao-ELMET `0.0 m` |
| CSN | (sin OGC; solo GDB/PNG) | INCONCLUSIVE: sin licencia abierta declarada |

Carga por fuente (5 km de radio para E-PRTR). Resultados live:

| Propiedad | source_crs -> op | SNCZI q100 | SNCZI DPH | E-PRTR inst. | dist. min (m) | CSN |
|-----------|------------------|-----------|-----------|--------------|----------------|-----|
| p01 Madrid Castellana | 4326 -> 25830 | off | off | off | - | INCONCLUSIVE |
| p02 Madrid Mayor | 4326 -> 25830 | off | off | on | 3858.7 | INCONCLUSIVE |
| p03 Donostia Mayor | 4258 -> 25830 | off | off | on | 474.0 | INCONCLUSIVE |
| p04 Vitoria Postas | 25830 -> 25830 | off | off | on | 933.2 | INCONCLUSIVE |
| p05 Bilbao Gran Via | 4258 -> 25830 | off | off | on | 2857.3 | INCONCLUSIVE |
| p06 Gipuzkoa periurbana | 4258 -> 25830 | off | off | on | 1619.4 | INCONCLUSIVE |
| p07 Navarra urbana | 4258 -> 25830 | off | off | on | 1105.4 | INCONCLUSIVE |
| p08 Araba rustica | 25830 -> 25830 | off | off | off | - | INCONCLUSIVE |

Controles positivos (fuera del corpus): `control_ebro_flood` -> SNCZI q100
`True`; `control_bilbao_plant` -> E-PRTR instalacion `on`, distancia `0.0 m`.

Nota: las 8 propiedades no intersectan Q100 ni DPH. Es un resultado valido del
corpus preregistrado (seleccion por diversidad, no por resultado), no un fallo
de la fuente.

## G0-C: cobertura (2026-09-14)

Corpus de 24 propiedades materializado y congelado **antes** de consultar
SIU/NCSE-02/BTN (`corpus_g0c.json`, commit `b907509`).

Comandos:

```bash
uv run python scripts/materialize_g0c_corpus.py   # 24 propiedades
uv run python scripts/capture_g0c.py             # captura live -> fixtures
uv run python scripts/probe_g0c.py               # gates + casos duros
uv run pytest                                    # replay offline
```

Accesos: SIU `mapas.fomento.gob.es/.../SIU/Servicios_OGC/MapServer/15/query`
(RISP); NCSE-02 `www.ign.es/wms-inspire/geofisica` capa `HazardArea2002.NCSE-02`
(CC BY 4.0); BTN `servicios.idee.es/wfs-inspire/transportes` `tn-ro:RoadLink` +
`tn-ra:RailwayLink` (CC BY 4.0 compatible).

Resultados live (24 propiedades):

```text
SIU:     observed 23 | inconclusive 1        (g0c07 Navarra: 0 features -> NO ausencia)
NCSE-02: observed  8 | unavailable 16        (Madrid/Bilbao/Zaragoza: null dentro de cobertura)
BTN:     observed 48 | derived 20            (carretera + ferrocarril; distancias)
```

Controles positivos (fuera del corpus):

| Control | Fuente | Resultado |
|---------|--------|-----------|
| Granada | NCSE-02 | OBSERVED `aceleracion=0.23 g` |
| Madrid centro | NCSE-02 | UNAVAILABLE (null dentro de cobertura) |
| Madrid carretera | BTN | OBSERVED `RoadLink`, distancia `~0 m` |
| Madrid centro | SIU | OBSERVED `ClaseSuelo` |

Casos duros verificados: `0 features` de SIU -> INCONCLUSIVE (nunca ausencia);
`aceleracion` null de NCSE dentro de cobertura -> UNAVAILABLE (no OBSERVED, no
fuera de cobertura); ausencia BTN dentro de cobertura declarada -> OBSERVED
`observed=false`.

## G0-D: informe (2026-09-14)

Comandos:

```bash
uv run python scripts/build_reports.py                 # 24 propiedades -> informes
uv run habitalens report <manifest.json> --out report  # desde un manifest
uv run pytest                                          # 144 tests offline
```

Artefactos generados (fixtures offline de G0-C) en `reports/g0c-corpus/`:

```text
report.html              # render desde el ReportViewModel
report.pdf               # 6 paginas, fpdf2 + Helvetica core
provenance_manifest.json # fuente unica de verdad + hashes de artefactos
```

Guardas verificadas:

- **Disclaimers**: disclaimer oficial + atribucion por fuente presentes en HTML
  y en el texto canonico del PDF.
- **Cero score**: el guard detecta `overall_score`, `risk_score`, `rating`,
  `grade`, `overall_status`, `traffic_light`, `recommendation`,
  `property_score`, `valoracion_global`, `semaforo`, etc.; inyectar uno en un
  hallazgo hace fallar la generacion.
- **Estado explicito**: SIU Navarra se muestra `INCONCLUSIVE`, NCSE null
  Madrid `UNAVAILABLE`.
- **Geometria**: HTML/PDF/manifest sin `posList`, `coordinates`, `POINT(`,
  `geojson` ni claves de geometria.
- **Determinismo**: mismo manifest -> mismo HTML (sha), mismo contenido canonico
  de PDF (sha) y mismo numero de paginas.
