"""HabitaLens - motor OSS de analisis reproducible de inmuebles a partir de fuentes publicas.

Este paquete implementa exclusivamente el gate G0-A (adquisicion y legal): modelos
minimos de inmueble/parcela/edificio, adaptadores de proveedores catastrales,
geocodificacion con CartoCiudad, encaminamiento territorial, cache, provenance y
guardas de licencia. No implementa analisis espacial, riesgo, scores ni informes.
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
