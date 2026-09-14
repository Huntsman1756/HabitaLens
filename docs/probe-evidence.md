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
| DGC | `ovc.catastro.meh.es/INSPIRE/wfs{CP,BU,AD}.aspx` | `cp:CadastralParcel`, `bu:Building`, `ad:Address` | EPSG:4326 | jerarquico provincia -> municipio |
| Navarra | `idena.navarra.es/ogc/inspire/wfs` (CP) + `/ogc/wfs` (CATAST_) | `CP:CadastralParcel`, `IDENA:CATAST_Pol_Edificacion`, `IDENA:CATAST_Txt_Portal` | EPSG:4258 / 25830 | no INSPIRE |
| Bizkaia | ArcGIS `.../Catastro/Annex1/...` + `.../Buildings/...` | `cp:CadastralParcel`, `ad:Address`, `bu-core2d:Building` | EPSG:4258 | `apli.bizkaia.eus/.../ES.BFA.CP|BU|AD.<mun>.zip` |
| Gipuzkoa | `b5m.gipuzkoa.eus/inspire/wfs/gipuzkoa_wfs_{cp,bu,ad}` | `cp:CadastralParcel`, `bu-ext2d:Building`, `ad:Address` | EPSG:4258 | `b5m.gipuzkoa.eus/inspire/download/*.xml` |
| Araba | `geo.araba.eus/WFS_INSPIRE_{CP,BU}` | `INSPIRE_CP:CP.CadastralParcel`, `INSPIRE_BU:BU.Building` | EPSG:25830 | `geo.araba.eus/atom/{CP,BU}/*.atom` |

CartoCiudad: `cartociudad.es/geocoder/api/geocoder/{candidates,find,reverseGeocode}`.

## Resultado live por proveedor (probe_live)

| Proveedor | refcat caso | parcela | area_m2 | CRS | edificios | version | estado |
|-----------|-------------|---------|---------|-----|-----------|---------|--------|
| DGC | 1707903VK4810F | no | - | EPSG:4326 | - | 2.0.0 | INCONCLUSIVE (refcat no resoluble WFS+ATOM) |
| Navarra | 001010001 | si | 101.28 | EPSG:4258 | 3 | 2.0.0 | PASS |
| Bizkaia | 48.020.1619.04006 | si | 2804.43 | EPSG:4258 | 6 | 1.1.0 | PASS |
| Gipuzkoa | 8594149 | si | 13201.0 | EPSG:4258 | 5 | 2.0.0 | PASS |
| Araba | 64010007 | si | 10830.82 | EPSG:25830 | 0 (rustico) | 2.0.0 | PASS |

Suplementario urbano Araba: `Calle Postas 1, Vitoria-Gasteiz` -> parcela
`59590687` (777.56 m2, EPSG:25830) + 7 edificios.

DGC por localizacion (fallback): `get_parcel_near(40.416461, -3.704658)` ->
parcela `0343302VK4704C`, area 1179 m2, EPSG:4326. Edificios DGC:
INCONCLUSIVE (el WFS BU no acepta BBOX live).

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

## Reproduccion del muro DGC

- WFS CP con `filter` por `cp:nationalCadastralReference=1707903VK4810F` y con
  `resourceId` devuelve 83 parcelas fijas (`1707903..`, `1707904..`, ...);
  un refcat inexistente devuelve lo mismo.
- ATOM de Fortia (17079): 1.539 parcelas, refcats `0003001...`; 0 coincidencias
  con `1707903VK4810F`.
- `p-rubi/cadastre-pipeline` indexa esas 1.539 parcelas y tampoco encuentra
  `1707903VK4810F` (ver `docs/spike-cadastre-pipeline.md`).
