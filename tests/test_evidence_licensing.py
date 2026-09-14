"""Licencia y acceso antes que parsing: guarda de fuentes G0-B."""

from __future__ import annotations

from pathlib import Path

import pytest

import habitalens.sources as sources_package
from habitalens.licensing import (
    LICENSE_FILENAME,
    LicensingNotDeclaredError,
    load_license,
)
from habitalens.sources import source_ids
from habitalens.sources.snczi.source import SncziSource


def test_all_sources_declare_valid_license() -> None:
    root = Path(sources_package.__file__).parent
    for source_id in source_ids():
        declaration = load_license(root / source_id)
        assert declaration.license_url.startswith("http")
        assert declaration.verified_on
        assert declaration.applicable_version


def test_missing_license_raises(tmp_path) -> None:
    package = tmp_path / "no_license"
    package.mkdir()
    with pytest.raises(LicensingNotDeclaredError):
        load_license(package)


def test_source_cannot_initialize_without_license(tmp_path, monkeypatch) -> None:
    package = tmp_path / "snczi_no_license"
    package.mkdir()
    (package / LICENSE_FILENAME).write_text("", encoding="utf-8")
    monkeypatch.setattr(
        "habitalens.sources.base.inspect.getfile",
        lambda _cls: str(package / "source.py"),
    )
    with pytest.raises(LicensingNotDeclaredError):
        SncziSource()
