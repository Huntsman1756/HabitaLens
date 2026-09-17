# Contribuir a HabitaLens

Gracias por tu interes. Esta guia explica como montar el entorno, ejecutar las
verificaciones y proponer cambios.

## Requisitos

- Python 3.12 o superior.
- [`uv`](https://docs.astral.sh/uv/) para gestionar dependencias y el entorno.

## Puesta en marcha

```bash
git clone https://github.com/Huntsman1756/HabitaLens.git
cd HabitaLens
uv sync --extra dev
```

## Verificaciones

```bash
uv run pytest        # suite completa, 100% offline (fixtures congeladas)
uv run ruff check    # lint
uv run ruff format --check   # formato (opcional)
uv build             # verifica que el paquete construye
```

Reglas que la CI y los tests hacen cumplir:

- **Ningun test toca la red.** Las respuestas live se capturan una vez y se
  congelan como fixtures en `tests/fixtures/`; el replay es determinista.
- **Determinismo**: misma entrada + misma version de fixture = mismo resultado.
- **Sin geometria en salidas publicas**: los modelos publicos no exponen
  coordenadas ni GeoJSON; la geometria vive solo en `~/.habitalens/cache/`.
- **Guarda de licencias**: cada proveedor/fuente necesita un `LICENSE.yaml`
  valido en su paquete o no puede inicializarse
  (`tests/test_licensing_guard.py`).
- **Cero score global**: ningun artefacto puede emitir `overall_score`,
  `rating`, `semaforo`, `recommendation` ni equivalentes
  (`src/habitalens/report/guard.py`).

## Semantica de cobertura

La regla dura del proyecto: `0 features` **no** equivale a ausencia. Para
emitir `OBSERVED`-ausencia hay que acreditar cobertura; si no, el resultado es
`UNAVAILABLE` o `INCONCLUSIVE`. Ver `docs/decisions.md` y los preregistros en
`docs/` antes de tocar `src/habitalens/sources/` o `src/habitalens/evidence/`.

## Flujo de trabajo

1. Abre un issue o comenta uno existente antes de cambios grandes.
2. Crea una rama, haz cambios pequenos y con tests.
3. `uv run pytest` y `uv run ruff check` en verde antes del PR.
4. Describe el *por que* del cambio en el PR, no solo el *que*.

## Estilo

- Codigo y comentarios en castellano sin acentos forzados por ASCII
  (convencion existente del proyecto).
- Lineas de 100 caracteres (`ruff`), tipado estricto donde sea practico.
- Preferir soluciones simples y explicitas sobre abstracciones.
