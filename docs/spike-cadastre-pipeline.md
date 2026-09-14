# Spike: `p-rubi/cadastre-pipeline`

- Repo: <https://github.com/p-rubi/cadastre-pipeline>
- Commit evaluado: `c0b945e2cf671b252c8bbf7af5c46fcbb39cb5b3`
- Licencia: MIT
- Fecha del spike: 2026-09-14
- Aislamiento: clonado y ejecutado fuera del core
  (`%TEMP%\cadastre-pipeline-spike`). Ningun codigo del spike se incorpora al
  core durante G0-A.

## Que es

Pipeline Python (3.10+, `requests`/`lxml`/`tqdm`) que descarga por ATOM los
temas INSPIRE **CP** (parcelas + zoning) y **BU** (edificios + partes) para las
provincias de Cataluna (08, 17, 25, 43), descomprime los ZIP municipales, indexa
REFCAT -> GML, extrae una geometria por refcat y agrega un CSV con coordenadas.

## Verificacion funcional

Caso objetivo: `municipio real -> ATOM -> CP/BU/AD -> refcat -> geometria`.

Se ejecuto el spike real sobre la captura live del ATOM de Fortia (17079)
(`.../INSPIRE/CadastralParcels/17/17079-FORTIA/A.ES.SDGC.CP.17079.zip`).

**Prueba valida (refcat perteneciente al feed):** `000300100EG07E`

```text
cadastre index  -> Total parcels: 1,539 (refcats 0003001...)
cadastre query  -> [OK] Saved: 000300100EG07E_v20160422.gml
                   Extracted successfully : 1
cadastre aggregate -> Parcels aggregated : 1 (CSV con X/Y)
```

Reproduce correctamente `municipio -> ATOM -> CP -> refcat -> geometria` para
las referencias presentes en su feed.

**Prueba invalida (descartada):** `1707903VK4810F`. En una primera iteracion
se uso como caso negativo, asumiendo que pertenecia a Fortia. La G0-A.1
demostro con `Consulta_DNPRC` que esa RC es de **Madrid (28/079)**, no de
Fortia (17/079). Por tanto el feed de Fortia nunca debio contenerla: la
ausencia en el indice del spike no era un defecto del spike, sino un error de
nuestra hipotesis. Esa evidencia queda retirada.

## Evidencia tecnica (motivos independientes)

1. **Cobertura incompleta del caso `CP/BU/AD`.** Solo implementa CP y BU; no
   hay tema **AD** (direcciones).
2. **Solo Cataluna.** `PROVINCES` cubre 08/17/25/43; no hay arquitectura
   multi-proveedor (Navarra, Bizkaia, Gipuzkoa, Araba) ni CartoCiudad.
3. **Modelo de datos distinto.** Es un pipeline *bulk* (millones de ficheros,
   `data/01_raw_zips` + `data/02_*_gml` + `data/03_*_gml`), no una resolucion
   por inmueble con cache/provenance/licensing. Integrarlo implicaria un
   segundo stack HTTP (`requests`) y una segunda jerarquia de cache.
4. **Instalacion rota con setuptools actual.**
   `pip install -e .` falla con
   `configuration error: project.authors must be array`
   (`authors = "github.com/p-rubi"` en `pyproject.toml`), que el README
   documenta como via soportada.
5. **Relevancia reducida tras G0-A.1.** HabitaLens ya resuelve DGC por RC con
   las stored queries oficiales `GetParcel`/`GetBuildingByParcel` (mas ligero y
   sin descargas masivas). El caso de uso del spike (bulk ATOM) no es el de
   HabitaLens.
6. **A favor:** codigo bien estructurado y testeado offline; utilidades de
   valor (iterparse endurecido contra XXE/entity-expansion, unzip anti
   zip-slip, descarga atomica con verificacion de `Content-Length`, plantillas
   GML cp/4.0 y bu-ext2d). Son referencias, no una dependencia que justifique
   un fork.

## Veredicto

**DISCARD.**

No se elige FORK aunque tenga licencia MIT: no cubre AD, es Cataluna-only, su
arquitectura bulk no encaja con la resolucion por inmueble de HabitaLens y su
instalacion esta rota. La comparacion funcional se rehizo limpiamente con un
refcat propio de su feed, que si extrae correctamente; el veredicto no depende
de un caso negativo mal planteado.

Se conservan como referencias (sin copiar codigo): el endurecimiento XML
(`lxml.iterparse` con limpieza y proteccion XXE) y la verificacion atomica de
descargas.
