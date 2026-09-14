# Decision de progresion G0-B -> G0-C

- Fecha: 2026-09-14 (decision puntual, no retroactiva).
- G0-B: `INCONCLUSIVE` (etiqueta `g0-b-inconclusive`, commit
  `37dfbc169a6631a20f9b7f59a5d36e4701c0b494`).
- G0-B.1: `INCONCLUSIVE / CLOSED` (dependencia externa de licencia/publicacion).

## Texto de la decision

```text
G0-B remains INCONCLUSIVE.

Progression to G0-C is permitted because:
- the unresolved CSN gate is an external licensing/access dependency;
- G0-C does not depend on CSN for its implementation or acceptance;
- no CSN evidence may be promoted to OBSERVED/DERIVED in G0-C;
- CSN remains explicitly INCONCLUSIVE until independently remediated.

This progression decision does not amend or upgrade the G0-B verdict.
```

## Efectos

- El veredicto `G0-B = INCONCLUSIVE` no se modifica ni se reinterpreta como
  PASS. La progresion es una decision operativa, acotada y fechada.
- CSN queda como **dependencia externa diferida**. Su hallazgo permanece
  `INCONCLUSIVE`; ningun resultado de CSN puede ascender a OBSERVED/DERIVED.
- La IS-47 (2025) **no** se incorpora ahora ni sustituye a la cartografia de
  radon; en su caso sera un adaptador distinto (`csn_radon_priority_municipal`)
  con su propio preregistro.
- G0-C se ejecuta con su propio preregistro congelado antes de tocar
  SIU, NCSE-02 o BTN: `docs/g0-c-preregistration.md`.
