"""La guarda de licencias no se desactiva, mockea ni relaja."""

from __future__ import annotations

import pytest

from habitalens.cadastre_providers.dgc.provider import DgcProvider
from habitalens.licensing import (
    LICENSE_FILENAME,
    REQUIRED_FIELDS,
    LicensingNotDeclaredError,
    audit_providers,
    load_license,
)


def test_real_providers_declare_valid_license() -> None:
    declarations = audit_providers()
    assert set(declarations) == {"dgc", "navarra", "bizkaia", "gipuzkoa", "araba"}
    for declaration in declarations.values():
        assert declaration.license_url.startswith("http")
        assert declaration.verified_on
        assert declaration.applicable_version


def test_missing_license_file_raises(tmp_path) -> None:
    package = tmp_path / "nolicense"
    package.mkdir()
    with pytest.raises(LicensingNotDeclaredError):
        load_license(package)


def test_empty_license_file_raises(tmp_path) -> None:
    package = tmp_path / "empty"
    package.mkdir()
    (package / LICENSE_FILENAME).write_text("", encoding="utf-8")
    with pytest.raises(LicensingNotDeclaredError):
        load_license(package)


def test_license_with_missing_fields_raises(tmp_path) -> None:
    package = tmp_path / "partial"
    package.mkdir()
    (package / LICENSE_FILENAME).write_text(
        'source_authority: "X"\nlicense_name: "Y"\n', encoding="utf-8"
    )
    with pytest.raises(LicensingNotDeclaredError) as excinfo:
        load_license(package)
    for field in REQUIRED_FIELDS:
        if field not in {"source_authority", "license_name"}:
            assert field in str(excinfo.value)


def test_audit_providers_detects_missing_yaml(tmp_path) -> None:
    providers_root = tmp_path / "cadastre_providers"
    (providers_root / "broken").mkdir(parents=True)
    with pytest.raises(LicensingNotDeclaredError):
        audit_providers(providers_root)


def test_provider_cannot_initialize_without_license(tmp_path, monkeypatch) -> None:
    package = tmp_path / "dgc_without_license"
    package.mkdir()
    monkeypatch.setattr(
        "habitalens.cadastre_providers.base.inspect.getfile",
        lambda _cls: str(package / "provider.py"),
    )
    with pytest.raises(LicensingNotDeclaredError):
        DgcProvider(persist=False)
