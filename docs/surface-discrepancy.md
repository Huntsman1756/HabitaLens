# Capacidad — Discrepancia de superficie anunciada vs oficial (Fase 3)

- Fecha: 2026-09-14.
- Modulo: `src/habitalens/evidence/surface.py`. Tests:
  `tests/test_surface_discrepancy.py`.
- Entrada: la superficie **anunciada** (m2). No requiere fuente externa; la
  superficie oficial ya la aporta el proveedor (`Parcel.area_m2`, o DNPRC).

## Que hace

```text
compare_surface(advertised_m2, official_m2, tolerance=0.05)
  -> diferencia absoluta (m2) y relativa ((anunciada - oficial) / oficial)
  -> exceeds_tolerance (|relativa| > tolerancia)

surface_finding(...) -> EvidenceFinding DERIVED (kindsurface.discrepancy_m2)
```

Sin geometria y sin score: es un hallazgo `DERIVED` con valor en m2 y nota con
las cifras y la tolerancia.

## CLI

```bash
habitalens surface <refcat> --advertised 90 [--tolerance 0.05]
```

Resuelve la parcela con el motor actual, toma la superficie oficial y compara.
Salida: refcat, superficie oficial, superficie anunciada, diferencia (m2 y %),
y si excede la tolerancia. Disclaimer incluido. Si la fuente no expone
superficie -> `INCONCLUSIVE` (no se inventa).

## Encaje

- Es la dimension de **mayor valor/dato** de `docs/product-opportunities.md`:
  accion concreta (contrastar/renegociar) y dato ya disponible.
- El CEE de Cataluna (`docs/preflight-ite-cee.md`) aporta ademas
  `metres_cadastre`, otra via oficial de superficie.
- No se integra aun en el informe G0-D (requiere el campo "superficie
  anunciada" en el flujo de entrada); queda como modulo y comando listos para
  conectarse cuando exista ese campo.
