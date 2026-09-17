"""CEE Euskadi: consulta por refcat foral, ausencia INCONCLUSIVE y licencia."""

from __future__ import annotations

from pathlib import Path

import pytest

import habitalens.cee.euskadi as euskadi_pkg
from habitalens.cache import CacheStore
from habitalens.cee import CeeStatus
from habitalens.cee.euskadi.provider import EuskadiCeeProvider
from habitalens.licensing import LicensingNotDeclaredError, load_license
from habitalens.net import FixtureSource
from habitalens.provenance import ProvenanceRecorder

DATA = Path(__file__).parent / "fixtures" / "data"
FOUND = "4774399"  # Bergara (Gipuzkoa): referencia foral numerica
MISSING = "ZZZZZZZZ999"


def _provider(tmp_path: Path, refcat: str, fixture: str) -> EuskadiCeeProvider:
    source = FixtureSource({f"cee_euskadi:lookup:{refcat}": DATA / fixture})
    return EuskadiCeeProvider(
        source=source, cache=CacheStore(tmp_path), provenance=ProvenanceRecorder(tmp_path)
    )


def test_lookup_found(tmp_path) -> None:
    provider = _provider(tmp_path, FOUND, "cee_euskadi_found.json")
    result = provider.lookup(FOUND)
    assert result.status == CeeStatus.FOUND
    assert result.record is not None
    assert result.record.rating == "F"
    assert result.record.refcat == "4774399"
    assert result.record.region == "euskadi"
    assert "Bergara" in (result.record.address or "")


def test_lookup_absent_is_inconclusive(tmp_path) -> None:
    # La API omite `items` cuando totalItems es 0: respuesta vacia valida.
    provider = _provider(tmp_path, MISSING, "cee_euskadi_notfound.json")
    result = provider.lookup(MISSING)
    assert result.status == CeeStatus.INCONCLUSIVE
    assert result.record is None
    assert result.note


def test_lookup_rejects_unsafe_refcat(tmp_path) -> None:
    provider = _provider(tmp_path, "x'; DROP", "cee_euskadi_notfound.json")
    result = provider.lookup("x'; DROP")
    assert result.status == CeeStatus.INCONCLUSIVE
    assert result.record is None


def test_euskadi_declares_license() -> None:
    declaration = load_license(Path(euskadi_pkg.__file__).parent)
    assert declaration.license_url.startswith("http")
    assert declaration.verified_on


def test_provider_cannot_init_without_license(tmp_path, monkeypatch) -> None:
    package = tmp_path / "euskadi_no_license"
    package.mkdir()
    monkeypatch.setattr(
        "habitalens.cee.base.inspect.getfile",
        lambda _cls: str(package / "provider.py"),
    )
    with pytest.raises(LicensingNotDeclaredError):
        EuskadiCeeProvider()
