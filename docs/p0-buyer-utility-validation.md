# P0 — Buyer Utility Validation (preregistro congelado; NO ejecutado)

Estado: **preregistrado**. No se ejecuta todavia.

Referencias: `g0-a-pass`, `g0-b-inconclusive`, `g0-c-pass`, `g0-d-pass`
(`a47182384c6230cd3533db5554d4e9f6cb119a44`).

P0 **no es un gate tecnico** ni anade fuentes. Responde a una unica pregunta de
producto:

> El informe actual de HabitaLens, sobre una muestra **aleatoria** de viviendas,
> aporta informacion accionable para un comprador, sin perder semantica ni
> fabricar certeza?

## 1. Que se evalua (y que no)

- Se evalua HabitaLens **con las capacidades actuales** (G0-A..G0-D), sin nuevas
  fuentes ni reglas de riesgo.
- Se usa el informe HTML/PDF + manifest de G0-D.
- **No** se evalua mercado, historicos, ITE/IEE, CEE, DANA, incendios, ruido, UI
  compleja, ni scoring (sigue prohibido por el guard de G0-D).

## 2. Muestra preregistrada (outcome-blind)

- **Marco**: un portal inmobiliario publico y una consulta **fijos** (municipios
  y filtros definidos en el momento del GO y registrados literalmente).
- **Seleccion aleatoria reproducible**: ordenar por identificador de anuncio
  ascendente y tomar cada `k`-esimo hasta 10, con `k = ceil(N/10)`.
- Se captura una **instantanea cruda** (fecha, consulta, IDs, direcciones) para
  reproducibilidad.
- **No** se selecciona ninguna propiedad por "parecer interesante". Si una
  direccion no resuelve, se sustituye por la siguiente de la lista fija.
- Entrada a HabitaLens: solo direccion/refcat. El contenido del anuncio no se
  redistribuye.

## 3. Controles positivos independientes (fuera de la muestra)

Conjunto fijo conocido, para medir deteccion y certeza falsa:

| Control | Condicion conocida | Esperado |
|---------|--------------------|----------|
| Ebro-Zaragoza | Zona inundable Q100 (SNCZI) | OBSERVED presente |
| Granada | Peligrosidad sismica 0.23 g (NCSE-02) | OBSERVED `0.23 g` |
| Madrid carretera | Infraestructura BTN | OBSERVED presente |
| Madrid centro | Clase de suelo SIU | OBSERVED |
| Madrid/Bilbao | NCSE `null` dentro de cobertura | **UNAVAILABLE** |
| Navarra SIU `g0c07` | SIU sin cobertura acreditada | **INCONCLUSIVE** |

Los dos ultimos son **controles de certeza falsa**: si se presentan como
"ausencia" o "sin afeccion", es fallo.

## 4. Revision humana ciega

- El revisor recibe **solo el informe** (id de propiedad anonimizado) y una
  checklist; no sabe que hay controles ni cual es cual.
- Por propiedad registra: (a) si hay al menos un hallazgo accionable y cual;
  (b) la respuesta a: "Despues de leer este informe, se que deberia comprobar
  antes de comprar esta vivienda?" (escala 1-5).
- Segundo revisor opcional para desacuerdos; se registra.

## 5. Metricas y umbrales (preregistrados)

```text
actionable_finding_rate = propiedades con >=1 hallazgo accionable / 10
known_condition_recall  = controles verdaderos detectados / controles verdaderos
false_certainty_rate    = hallazgos presentados con certeza indebida / total hallazgos
source_traceability     = hallazgos OBSERVED+DERIVED con provenance resoluble / total
```

| Metrica | PASS |
|---------|------|
| `actionable_finding_rate` | >= 0.5 (>= 5/10) |
| `known_condition_recall` | >= 0.75 (>= 3/4 controles verdaderos) |
| `false_certainty_rate` | <= 0.02 y **cero** ocurrencias en el set de control |
| `source_traceability` | = 1.0 |

## 6. Veredicto

```text
P0   PASS | FAIL | INCONCLUSIVE
```

- **PASS** si las cuatro metricas cumplen.
- **FAIL** si `false_certainty_rate` incumple o `source_traceability < 1.0`.
- **INCONCLUSIVE** si la muestra no puede obtenerse de forma reproducible
  (portal inaccesible, cambio de marco) o la revision ciega no puede completarse.

Un `actionable_finding_rate` bajo **no** es fallo tecnico: es una senal de
producto. La decision derivada seria reconsiderar el valor de las fuentes
actuales, **no** anadir fuentes a ciegas.

## 7. Regla de alcance

No se anaden fuentes ni funcionalidad durante P0. Si el producto actual no
aporta informacion accionable en una muestra aleatoria, ampliar alcance
produciria un sistema mas grande, no necesariamente mejor.

## 8. Legal / etica

- No se redistribuye contenido de anuncios; solo se usan direcciones como
  entrada. Se respetan terminos de uso y `robots.txt`.
- Sin datos personales de anunciantes; sin perfiles de usuarios.
- El informe conserva disclaimers y no emite opinion agregada.

## 9. Entregables

- `docs/p0-report.md` con instantanea, metricas, tabla por propiedad y veredicto.
- Evidencia cruda de la seleccion (IDs/fechas) para reproducibilidad.

## 10. Riesgos

- Portales que cambian o bloquean; mitigado con marco fijo y sustitucion
  preregistrada.
- Ambiguedad de direcciones; mitigado con sustitucion por orden fijo.
- Sesgo del revisor; mitigado con ceguera y checklist.

## 11. Enmiendas

- **P0-E1 — sampling constants (2026-09-14).** Aplicada antes de observar
  cualquier vivienda.

```text
Portal: Idealista
Consulta: vivienda de segunda mano en venta, Espana, sin filtros adicionales.
Snapshot: captura unica de los resultados publicos obtenidos en el GO.
Orden interno: listing/property ID ascendente.
offset: 0
k: 3
Seleccion: eligible[offset::k][:10]

Elegible:
- anuncio individual de vivienda;
- direccion/localizacion suficiente para intentar resolverla;
- ID estable disponible.

Si una seleccionada no puede resolverse:
- aplicar exclusivamente la regla de sustitucion preregistrada;
- no escoger manualmente una alternativa "interesante".

Si no hay 10 elegibles en la captura prevista:
- continuar paginas/resultados en el orden predeterminado;
- mantener k=3 y offset=0.
```

  La muestra se denomina **"muestreo sistematico reproducible"**, no "muestra
  aleatoria representativa de Espana". Seleccionar cada `k`-esimo elemento es
  muestreo sistematico; no se sobredescribe lo que demuestra.

  **Definicion operativa de `actionable finding`** (congelada aqui): cuenta solo
  cuando el revisor considera que el hallazgo justificaria, **antes de ofertar**,
  al menos una accion concreta: pedir documentacion, comprobar una fuente,
  preguntar al vendedor/agencia, consultar a un profesional, comprobarlo durante
  la visita o investigar antes de decidir. "Es interesante" **no** cuenta.

  Los umbrales de la seccion 5 no cambian. Un `actionable_finding_rate` de 4/10
  es **FAIL**, aunque los controles positivos se detecten perfectamente. No se
  anade ninguna fuente ni se modifican reglas durante la ejecucion.
