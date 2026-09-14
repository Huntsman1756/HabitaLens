"""Implementacion de la guarda de licencias (sin mocks ni relajaciones)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

LICENSE_FILENAME = "LICENSE.yaml"

# Campos obligatorios que debe contener cada LICENSE.yaml.
REQUIRED_FIELDS: tuple[str, ...] = (
    "source_authority",
    "license_name",
    "license_url",
    "verified_on",
    "applicable_version",
)


class LicensingNotDeclaredError(RuntimeError):
    """El proveedor no declara licencia suficiente para poder inicializarse."""


@dataclass(frozen=True)
class LicenseDeclaration:
    source_authority: str
    license_name: str
    license_url: str
    verified_on: str
    applicable_version: str
    reuse_conditions: str | None = None

    @classmethod
    def from_mapping(cls, data: dict) -> LicenseDeclaration:
        return cls(
            source_authority=str(data["source_authority"]),
            license_name=str(data["license_name"]),
            license_url=str(data["license_url"]),
            verified_on=str(data["verified_on"]),
            applicable_version=str(data["applicable_version"]),
            reuse_conditions=(
                str(data["reuse_conditions"]) if data.get("reuse_conditions") else None
            ),
        )


def validate_license(data: object, origin: Path) -> LicenseDeclaration:
    """Valida un mapping de licencia. Lanza si falta cualquier campo obligatorio."""

    if not isinstance(data, dict):
        raise LicensingNotDeclaredError(
            f"{origin}: {LICENSE_FILENAME} vacio o no es un mapping valido"
        )
    missing = [
        field
        for field in REQUIRED_FIELDS
        if not str(data.get(field, "")).strip()
    ]
    if missing:
        raise LicensingNotDeclaredError(
            f"{origin}: {LICENSE_FILENAME} carece de campos obligatorios: "
            + ", ".join(missing)
        )
    return LicenseDeclaration.from_mapping(data)


def load_license(package_dir: Path) -> LicenseDeclaration:
    """Carga y valida el LICENSE.yaml de un paquete de proveedor."""

    package_dir = Path(package_dir)
    path = package_dir / LICENSE_FILENAME
    if not path.is_file():
        raise LicensingNotDeclaredError(
            f"{package_dir.name}: falta {LICENSE_FILENAME}; el proveedor no puede "
            "inicializarse."
        )
    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        raise LicensingNotDeclaredError(
            f"{package_dir.name}: {LICENSE_FILENAME} esta vacio."
        )
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:  # pragma: no cover - defensive
        raise LicensingNotDeclaredError(
            f"{package_dir.name}: {LICENSE_FILENAME} no es YAML valido: {exc}"
        ) from exc
    return validate_license(data, path)


def provider_package_dirs(providers_root: Path | None = None) -> list[Path]:
    """Devuelve los directorios de proveedores bajo cadastre_providers/*/."""

    if providers_root is None:
        import habitalens.cadastre_providers as providers_pkg

        providers_root = Path(providers_pkg.__file__).parent
    root = Path(providers_root)
    return sorted(
        child
        for child in root.iterdir()
        if child.is_dir() and not child.name.startswith("__")
    )


def audit_providers(providers_root: Path | None = None) -> dict[str, LicenseDeclaration]:
    """Recorre cadastre_providers/*/ y valida cada LICENSE.yaml.

    Lanza :class:`LicensingNotDeclaredError` para el primer incumplimiento.
    """

    result: dict[str, LicenseDeclaration] = {}
    for package_dir in provider_package_dirs(providers_root):
        result[package_dir.name] = load_license(package_dir)
    return result
