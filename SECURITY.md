# Politica de seguridad

## Como reportar una vulnerabilidad

No abras un issue publico para vulnerabilidades. Usa la funcion de reporte
privado de GitHub:

<https://github.com/Huntsman1756/HabitaLens/security/advisories/new>

Incluye una descripcion del problema, pasos para reproducirlo y el impacto
esperado. Se acusa recibo lo antes posible y se comunica el resultado de la
evaluacion.

## Alcance

HabitaLens es una CLI/libreria que consulta servicios publicos (OGC/WFS,
ArcGIS REST) y cachea respuestas en `~/.habitalens/`. Tienen interes de
seguridad, entre otros:

- Exposicion de geometria catastral en salidas publicas (el proyecto la
  trata como dato interno; ver guardas de no-fuga en `tests/`).
- Credenciales, tokens o datos personales en el repositorio o en artefactos.
- Parseo inseguro de respuestas XML/JSON de terceros.
- Escritura de ficheros fuera de la cache o del directorio de salida.

## Versiones soportadas

Solo la rama `main` recibe correcciones de seguridad.
