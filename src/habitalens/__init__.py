"""HabitaLens - motor OSS de analisis reproducible de inmuebles a partir de fuentes publicas.

Adquisicion catastral multi-proveedor (G0-A), motor de evidencia espacial con
semantica de cobertura estricta (G0-B/G0-C), informes con manifest de
procedencia (G0-D) y consultas de superficie/CEE (P1). No implementa scores,
valoraciones globales ni geometria en salidas publicas.
"""

from __future__ import annotations

__version__ = "0.0.1"

DISTRIBUTION_NAME = "habitalens"
IMPORT_NAME = "habitalens"
CLI_NAME = "habitalens"

DISCLAIMER = (
    "HabitaLens es un proyecto independiente. Genera analisis derivados a partir de "
    "fuentes publicas y no representa ni sustituye a la Direccion General del Catastro "
    "ni a ninguna otra administracion publica. Sus resultados no tienen caracter oficial "
    "ni fehaciente."
)

__all__ = ["CLI_NAME", "DISCLAIMER", "DISTRIBUTION_NAME", "IMPORT_NAME", "__version__"]
