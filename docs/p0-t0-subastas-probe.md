# P0-T0 — Probe: Subastas Judiciales (Justicia)

- Fecha: 2026-09-14.
- Fuente: `https://catalogodatos.justicia.es/csv/Subastas_Judiciales.csv`
  (datos.gob.es `e05228601-subastas-judiciales`).
- Alcance: solo esquema/licencia/resolubilidad. Sin capas de riesgo, sin
  seleccion manual, sin scraping.
- Script reproducible: `scripts/p0t0_probe.py`.

## 1. Licencia / condiciones

`https://datos.justicia.es/aviso-legal` (200): reutilizacion conforme a la
**Ley 37/2007 y RD 1495/2011** (RISP), con obligaciones de cita. No declara una
licencia CC explicita. Apta para reutilizacion con atribucion.

## 2. Esquema real (cabecera)

```text
CantidadReclamada; TipoSubasta; Procedimiento; principalReclamado;
importeSubasta; importeTasacion; Estado; Fecha_Estado; Fecha_Publicada;
Inmuebles; Muebles; Vehiculos; Acreedores; Representantes
```

- `Inmuebles`, `Muebles`, `Vehiculos` son **recuentos** (0/1/...), no detalles.
- **No hay** columna de direccion, localidad, municipio, provincia ni referencia
  catastral.

## 3. Comprobaciones

| # | Check | Resultado |
|---|-------|-----------|
| 1 | Licencia/condiciones | OK (RISP, cita obligatoria; sin CC explicita) |
| 2 | Schema real | 14 columnas; **sin** direccion/referencia |
| 3 | Presencia de inmuebles/viviendas | Solo recuento (`Inmuebles`) |
| 4 | Direccion o referencia para `PropertyResolver` | **NO** |
| 5 | % de registros resolubles inequivocamente | **0%** con este CSV |

## 4. Veredicto

```text
P0-T0   FAIL
```

El CSV nacional semanal **no contiene el detalle del bien** necesario para
identificar la finca; las direcciones/refcat viven en la ficha de cada subasta,
no en el CSV. No se prerregistra P0-T con este recurso tal cual.

## 5. Posible via futura (no ejecutada)

Si se quiere una cohorte transaccional real, habria que comprobar si existe una
**segunda descarga oficial con detalle del bien** (o una ficha/API por subasta
con direccion), o un ATOM/CSV ampliado. Hasta disponer de direccion/referencia
inequivoca, P0-T no es viable. No se hace scraping ni evasion.

## 6. Sin cambios en el alcance

No se anaden fuentes de riesgo ni se modifican umbrales de P0.
