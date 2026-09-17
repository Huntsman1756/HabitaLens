# Changelog

Todos los cambios relevantes del proyecto. Formato basado en
[Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

## [Unreleased]

### Added

- **Radon (csn_radon)**: fuente activada. El Mapa del Potencial de Radon de
  Espana (CSN, 2017) es consultable via la capa ArcGIS `SIU/Potencial_riesgo_de_radon`
  (MIVAU). Interseccion parcela-zona verificada por el servidor; OBSERVED con la
  peor categoria P90 que toca la parcela. Atribucion obligatoria CSN 2017.
- **CEE Euskadi**: consulta por referencia catastral via API REST de Open Data
  Euskadi (`api.euskadi.eus/energy-efficiency`, CC BY, OpenAPI 3.0).
- Paginacion WFS (`next`) y ArcGIS (`resultOffset`) en el cliente de fuentes:
  respuestas paginadas se completan en vez de rechazarse (BTN recupera el
  conjunto completo de segmentos).
- CI: type check con mypy, lint con ruff, tests offline y build del paquete
  en Linux/Windows. Workflow de release por tag.
- `.pre-commit-config.yaml` (ruff + higiene basica), `.python-version` (3.12),
  LICENSE MIT, CONTRIBUTING, SECURITY, plantillas de issue/PR.

### Changed

- **SIU**: la consulta envia la geometria de la parcela por POST con
  `spatialRel=intersects`; las clases devueltas intersectan de verdad ->
  OBSERVED verificado (antes INCONCLUSIVE por BBOX sin geometria).
- **SNCZI**: 0 intersecciones -> INCONCLUSIVE (la cobertura autonomica no esta
  acreditada); geometrias reales con autointersecciones se reparan con
  `make_valid` en vez de rechazarse.
- Respuestas malformadas, paginadas sin seguir, con errores o con conteos
  inconsistentes se rechazan en vez de contarse parciales.
- Informes: manifiesto estricto (invariantes estado/valor, inventario de
  fuentes, guardas anti-score y anti-geometria) y publicacion atomica.
- DGC: seleccion exacta de unidad catastral en respuestas multi-unidad;
  el resolver por proximidad deja de devolver parcelas ajenas y permite el
  fallback por refcat.
- `pypdf` pasa a dependencia runtime; `duckdb` eliminada (sin uso);
  dependencias dev en `dependency-groups` (pytest, ruff, mypy).

### Fixed

- Conteos de BTN ya no se truncan silenciosamente en respuestas paginadas.
- `resolve` ya no aborta cuando el punto geocodificado cae fuera de las
  parcelas candidatas: se aplica el fallback por referencia.
