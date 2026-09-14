"""Guarda de licencias de los proveedores catastrales.

Cada paquete bajo ``cadastre_providers/*/`` debe declarar un ``LICENSE.yaml``
con los campos obligatorios. Si falta, esta vacio o le faltan campos, el
proveedor no puede inicializarse: se lanza :class:`LicensingNotDeclaredError`.
"""

from __future__ import annotations

from habitalens.licensing.guard import (
    LICENSE_FILENAME,
    REQUIRED_FIELDS,
    LicenseDeclaration,
    LicensingNotDeclaredError,
    audit_providers,
    load_license,
    validate_license,
)

__all__ = [
    "LICENSE_FILENAME",
    "REQUIRED_FIELDS",
    "LicenseDeclaration",
    "LicensingNotDeclaredError",
    "audit_providers",
    "load_license",
    "validate_license",
]
