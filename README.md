# HabitaLens

Motor OSS de analisis reproducible de inmuebles a partir de fuentes publicas.

> **HabitaLens es un proyecto independiente. Genera analisis derivados a partir de
> fuentes publicas y no representa ni sustituye a la Direccion General del Catastro
> ni a ninguna otra administracion publica. Sus resultados no tienen caracter
> oficial ni fehaciente.**

## Estado del proyecto

Este repositorio implementa exclusivamente el gate **G0-A (adquisicion y legal)**:
adquisicion y normalizacion de informacion basica de inmueble/parcela/edificio
desde cinco proveedores catastrales, geocodificacion con CartoCiudad, encaminamiento
territorial, cache, provenance y guarda de licencias.

No se implementa (fuera de alcance G0-A): SNCZI, CSN, E-PRTR, SIU, NCSE-02, BTN,
DANA, reglas de riesgo, scores, informes, HTML/PDF, visor web, IA, usuarios, pagos,
historico inmobiliario ni reproyeccion para analisis espacial.

- Proyecto: `HabitaLens`
- Distribucion Python / import / CLI: `habitalens`
- Cache local: `~/.habitalens/`
- Python 3.12+, gestionado con `uv`; lint con `ruff`; tests con `pytest`.

## Arquitectura

```text
direccion
    -> CartoCiudad Geocoder
    -> localizacion / refcat candidato
    -> TerritoryRouter
    -> CadastreProvider correspondiente (DGC | Navarra | Bizkaia | Gipuzkoa | Araba)
    -> parcela + edificios
```

`CadastreProvider` no hace geocodificacion y ningun proveedor implementa
`resolve_address()`. Contrato minimo:

```python
resolve_reference(refcat) -> Parcel
get_parcel(refcat) -> Parcel
get_buildings(refcat) -> list[Building]
source_version() -> str
coverage() -> TerritoryMask
```

## Uso

```bash
habitalens resolve 1707903VK4810F      # referencia catastral
habitalens resolve "Calle Mayor 1, Madrid"   # direccion
habitalens resolve <refcat|direccion> --refresh   # fuerza refetch
habitalens resolve <refcat|direccion> --json      # salida JSON sin geometria
habitalens --help
```

La salida no incluye geometria catastral: solo refcat, superficie, uso (si la
fuente lo expone), territorio, version de fuente y CRS fuente.

## Regla de geometria

La adquisicion conserva el **CRS original** del proveedor (registrado en cache y en
provenance). En G0-A no se reproyecta para analisis espacial. EPSG:25830 solo se
usa como simplificacion de fixtures de probe, nunca como invariancia nacional.

Ninguna salida publica serializa geometria catastral. Los objetos publicos no
exponen coordenadas, GeoJSON catastral, `__geo_interface__` ni geometrias
reconstruibles: la geometria vive exclusivamente en cache local (`~/.habitalens/cache/`).

## Cache y provenance

- GeoParquet por proveedor/municipio bajo `~/.habitalens/cache/`.
- Metadatos: proveedor, fecha de captura, version, CRS y procedencia.
- El refetch es explicito con `--refresh`.
- Provenance append-only en `~/.habitalens/provenance/provenance.jsonl` con la
  version/esquema realmente observado por proveedor.

## Licencias

Cada paquete en `src/habitalens/cadastre_providers/*/` incluye su `LICENSE.yaml`
(autoridad, licencia, URL, fecha de verificacion, version aplicable). Si falta,
esta vacio o le faltan campos obligatorios, el proveedor no puede inicializarse y
se lanza `LicensingNotDeclaredError` (`tests/test_licensing_guard.py`).

## Testing

```bash
uv run pytest          # tests offline con fixtures congeladas (sin red)
uv run ruff check      # lint
```

Regla de determinismo: misma entrada + misma version de fixture = mismo resultado.

## Resultados del gate G0-A

Evidencia live (2026-09-14) y fixtures offline en `tests/`:

| Proveedor | Estado | Nota |
|-----------|--------|------|
| DGC | PASS | Stored queries `GetParcel` / `GetBuildingByParcel` + corroboracion `Consulta_DNPRC` (G0-A.1). Tambien resuelve por localizacion (BBOX). |
| Navarra | PASS | Parcela + 3 edificios (EPSG:4258). |
| Bizkaia | PASS | Parcela + 6 edificios (EPSG:4258). |
| Gipuzkoa | PASS | Parcela + 5 edificios (EPSG:4258). |
| Araba | PASS | Parcela (EPSG:25830); 7 edificios en caso urbano. |
| CartoCiudad E2E | PASS | Madrid -> DGC (parcela) y Donostia -> Gipuzkoa (parcela + edificios). |
| Licensing guard | PASS | `tests/test_licensing_guard.py` en verde. |
| cadastre-pipeline | DISCARD | Ver `docs/spike-cadastre-pipeline.md`. |

## Gate G0-B (evidencia espacial)

Nucleo de evidencia que convierte geometria de propiedad + fuentes oficiales en
hallazgos deterministas `OBSERVED` / `DERIVED` / `UNAVAILABLE` / `INCONCLUSIVE`.

| Gate | Estado | Nota |
|------|--------|------|
| SNCZI (zonas inundables) | PASS | WFS INSPIRE; control positivo Ebro Q100. |
| E-PRTR (instalaciones) | PASS | ArcGIS REST GeoJSON; distancia derivada; control ELMET 0 m. |
| CSN (radon) | INCONCLUSIVE | Sin servicio OGC y sin licencia abierta declarada: no se activa. |
| Evidence engine | PASS | Taxonomia, CRS operacional explicito, provenance, replay determinista. |
| Corpus 8 propiedades | PASS | Replay offline + controles; sin fuga de geometria. |

## Gate G0-C (cobertura)

Cobertura como ciudadano de primera clase: `0 features` no es ausencia.

| Gate | Estado | Nota |
|------|--------|------|
| SIU | PASS | 23 OBSERVED + 1 INCONCLUSIVE; 0 features nunca es ausencia; control Madrid. |
| NCSE-02 | PASS | 8 OBSERVED + 16 UNAVAILABLE (null dentro de cobertura); control Granada 0.23 g. |
| BTN | PASS | 48 OBSERVED + 20 DERIVED; ausencia dentro de cobertura declarada; control Madrid. |
| Coverage core | PASS | `evidence/coverage.py` + semantica UNAVAILABLE/INCONCLUSIVE estricta. |
| Corpus 24 | PASS | Materializado outcome-blind antes de consultar fuentes; replay offline. |
| CSN | INCONCLUSIVE | Dependencia externa (G0-B.1); no se promociona. |

## Gate G0-D (informe)

Producto: manifest de procedencia como fuente unica de verdad, render HTML/PDF,
disclaimers y **cero score global**.

| Gate | Estado | Nota |
|------|--------|------|
| Renderer HTML | PASS | Determinista; renderiza desde `ReportViewModel`. |
| Renderer PDF | PASS | `fpdf2` + Helvetica core; contenido canonico determinista. |
| Provenance manifest | PASS | Schema completo por hallazgo + hashes de artefactos; sin geometria. |
| Disclaimers | PASS | Oficial + atribucion por fuente en HTML y PDF. |
| No-global-score guard | PASS | Bloquea `overall_score`, `rating`, `semaforo`, `recommendation`, ... |
| Determinism | PASS | Mismo manifest -> mismo HTML/PDF canonico/manifest. |
| Geometry-leak guard | PASS | Sin geometria en HTML/PDF/JSON. |

## Decisiones y evidencia

- `docs/decisions.md` — routing, CRS, geometria, licencias, cache/provenance.
- `docs/probe-evidence.md` — endpoints verificados y resultados de los probes.
- `docs/spike-cadastre-pipeline.md` — veredicto razonado del spike.
- `docs/g0-b-preregistration.md` — preregistro congelado de G0-B.
- `docs/g0-b-progression-decision.md` — decision de progresion G0-B -> G0-C.
- `docs/g0-b.1-csn-licensing.md` — remediacion de licencia CSN (INCONCLUSIVE).
- `docs/g0-c-preregistration.md` — preregistro congelado de G0-C.
- `docs/g0-d-preregistration.md` — contrato congelado de G0-D.
- `docs/p0-buyer-utility-validation.md` — validación de utilidad (P0).
- `docs/p0-report.md` — ejecución P0: **INCONCLUSIVE** (muestra no obtenible + revisión humana pendiente).
- `docs/p0.1-sample-acquisition.md` — remediación P0.1 (snapshot por operador), **DEFERRED**.
- `docs/p0-r-residential-property-utility.md` — validación de utilidad residencial (marco catastral), congelada sin ejecutar.
- `docs/p0-t0-subastas-probe.md` — probe Subastas Judiciales: **FAIL** (sin dirección/referencia en el CSV).
- `docs/p0-r-report.md` — materialización del frame P0-R: **INCONCLUSIVE** (pool DGC congelado; forales pendientes).
- `docs/p0-rd-report.md` — piloto DGC residencial: **FAIL** (1/10 actionable; utilidad no probada con las fuentes actuales).
- `docs/spike-oss-candidates.md` — evaluación OSS aislada (`osmnx`, `trece`, idealista18…).
- `docs/product-opportunities.md` — hipótesis de valor de producto tras un probable P0-RD FAIL.
- `docs/preflight-ite-cee.md` — preflight ITE/IEE y CEE (Fase 1).
- `docs/spike-osm-trece.md` — spike aislado `osmnx`/`trece` (Fase 2).
- `docs/surface-discrepancy.md` — capacidad superficie anunciada vs oficial (Fase 3).
- `docs/p1-buyer-actionability-upgrade.md` — P1 (superficie con comparabilidad + CEE regional).

Estado: G0-A **PASS** (`g0-a-pass`), G0-B **INCONCLUSIVE**/CSN externo
(`g0-b-inconclusive`), G0-C **PASS** (`g0-c-pass`), G0-D **PASS** (`g0-d-pass`),
P0 **INCONCLUSIVE** (`p0-inconclusive`), P0.1 **DEFERRED**, P0-T0 **FAIL**
(`p0-t0-fail`), P0-R **INCONCLUSIVE**/frame incompleto (`p0-r-preregistered`),
P0-RD **FAIL** (1/10 actionable; `technical_validity: PROVEN`, `buyer_utility: NOT PROVEN`).
