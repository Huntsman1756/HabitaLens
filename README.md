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
| DGC | INCONCLUSIVE | Parcela por refcat no resoluble (WFS ignora filtros; ATOM usa otro refcat). Resuelve por localizacion (BBOX) via CartoCiudad. |
| Navarra | PASS | Parcela + 3 edificios (EPSG:4258). |
| Bizkaia | PASS | Parcela + 6 edificios (EPSG:4258). |
| Gipuzkoa | PASS | Parcela + 5 edificios (EPSG:4258). |
| Araba | PASS | Parcela (EPSG:25830); 7 edificios en caso urbano. |
| CartoCiudad E2E | PASS | Madrid -> DGC (parcela) y Donostia -> Gipuzkoa (parcela + edificios). |
| Licensing guard | PASS | `tests/test_licensing_guard.py` en verde. |
| cadastre-pipeline | DISCARD | Ver `docs/spike-cadastre-pipeline.md`. |

## Decisiones y evidencia

- `docs/decisions.md` — routing, CRS, geometria, licencias, cache/provenance.
- `docs/probe-evidence.md` — endpoints verificados y resultados de los probes.
- `docs/spike-cadastre-pipeline.md` — veredicto razonado del spike.
