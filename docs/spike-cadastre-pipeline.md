# Spike: `p-rubi/cadastre-pipeline`

- Repo: <https://github.com/p-rubi/cadastre-pipeline>
- Commit evaluado: `c0b945e2cf671b252c8bbf7af5c46fcbb39cb5b3`
- Licencia: MIT
- Fecha del spike: 2026-09-14
- Aislamiento: clonado y ejecutado fuera del core (`%TEMP%\cadastre-pipeline-spike`).
  Ningun codigo del spike se incorpora al core durante G0-A.

## Que es

Pipeline Python (3.10+, `requests`/`lxml`/`tqdm`) que descarga por ATOM los
temas INSPIRE **CP** (parcelas + zoning) y **BU** (edificios + partes) para las
provincias de Cataluna (08, 17, 25, 43), descomprime los ZIP municipales, indexa
REFCAT -> GML, extrae una geometria por refcat y agrega un CSV con coordenadas.

## Verificacion del caso preregistrado

Caso objetivo: `municipio real -> ATOM -> CP/BU/AD -> refcat -> geometria`.

Se ejecuto el spike real contra la captura live del municipio DGC preregistrado
(Fortia, 17079) extraida de
`.../INSPIRE/CadastralParcels/17/17079-FORTIA/A.ES.SDGC.CP.17079.zip`.

Resultado de `cadastre index`:

```text
GML files found: 1
Total parcels   : 1,539
index_refcat.csv:
refcat,mun_code,province,file_path
000300100EG07E,17079,Girona,data/02_parcels_gml/Girona/A.ES.SDGC.CP.17079.cadastralparcel.gml
000300200EG07E,17079,Girona,...
```

Resultado de `cadastre query` para el refcat preregistrado `1707903VK4810F`:

```text
REFCATs to look up: 1
[MISS] Not found in the index: 1707903VK4810F
Extracted successfully : 0
Not in the index       : 1
```

Resultado de `cadastre query` para un refcat nativo del ATOM
(`000300100EG07E`):

```text
[OK] Saved: 000300100EG07E_v20160422.gml
Extracted successfully : 1
```

`cadastre aggregate` genera el CSV con coordenadas correctamente.

## Evidencia tecnica

1. **No reproduce el caso preregistrado por refcat.** El ATOM municipal de la
   DGC codifica las parcelas con refcats `0003001...`, mientras que el WFS y
   CartoCiudad devuelven `1707903VK4810F`. El indice del spike contiene 1.539
   parcelas pero **ninguna** coincide con el refcat preregistrado. Es
   exactamente el mismo muro que encontro HabitaLens (ver
   `docs/decisions.md` seccion 3.1).
2. **Cobertura incompleta del caso `CP/BU/AD`.** Solo implementa CP y BU; no
   hay tema **AD** (direcciones), que el caso preregistrado DGC menciona.
3. **Solo Cataluna.** `PROVINCES` cubre 08/17/25/43; no hay arquitectura
   multi-proveedor (Navarra, Bizkaia, Gipuzkoa, Araba) ni CartoCiudad.
4. **Modelo de datos distinto.** Es un pipeline *bulk* (millones de ficheros,
   `data/01_raw_zips` + `data/02_*_gml` + `data/03_*_gml`), no una resolucion
   por inmueble con cache/provenance/licensing. Integrarlo en HabitaLens
   implicaria un segundo stack HTTP (`requests`) y una segunda jerarquia de
   cache.
5. **Instalacion rota con setuptools actual.**
   `pip install -e .` falla con
   `configuration error: project.authors must be array`
   (`authors = "github.com/p-rubi"` en `pyproject.toml`). El propio README
   documenta `pip install -e .` como via soportada.
6. **A favor:** codigo bien estructurado y testeado offline; utilidades de
   valor (iterparse endurecido contra XXE/entity-expansion, unzip anti
   zip-slip, descarga atomica con verificacion de `Content-Length`, plantillas
   GML cp/4.0 y bu-ext2d). Pero son referencias, no una dependencia que
   justifique un fork.

## Veredicto

**DISCARD.**

No se elige FORK aunque el proyecto tenga licencia MIT: no reproduce el caso
DGC preregistrado por refcat, no cubre AD, es Cataluna-only y su arquitectura
bulk no encaja con la resolucion por inmueble de HabitaLens. HabitaLens ya
resuelve el caso DGC por localizacion (BBOX) de forma verificada, que es el
fallback correcto ante el muro del refcat.

Se conservan como referencias (sin copiar codigo): el endurecimiento XML
(`lxml.iterparse` con limpieza y proteccion XXE) y la verificacion atomica de
descargas.
