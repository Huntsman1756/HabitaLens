"""CEE Cataluna: consulta por refcat, ausencia INCONCLUSIVE y licencia."""

from __future__ import annotations

from pathlib import Path

import pytest

import habitalens.cee.catalunya as catalunya_pkg
from habitalens.cache import CacheStore
from habitalens.cee import CeeStatus
from habitalens.cee.catalunya.provider import CatalunyaCeeProvider
from habitalens.licensing import LicensingNotDeclaredError, load_license
from habitalens.net import FixtureSource
from habitalens.provenance import ProvenanceRecorder

DATA = Path(__file__).parent / "fixtures" / "data"
FOUND = "9533603DG4393S0001LT"
MISSING = "00000000000000000000"


def _provider(tmp_path: Path, refcat: str, fixture: str) -> CatalunyaCeeProvider:
    source = FixtureSource({f"cee_catalunya:lookup:{refcat}": DATA / fixture})
    return CatalunyaCeeProvider(
        source=source, cache=CacheStore(tmp_path), provenance=ProvenanceRecorder(tmp_path)
    )


def test_lookup_found(tmp_path) -> None:
    provider = _provider(tmp_path, FOUND, "cee_catalunya_found.json")
    result = provider.lookup(FOUND)
    assert result.status == CeeStatus.FOUND
    assert result.record is not None
    assert result.record.rating == "E"
    assert result.record.built_m2 == 62.81
    assert result.record.region == "catalunya"


def test_lookup_absent_is_inconclusive(tmp_path) -> None:
    provider = _provider(tmp_path, MISSING, "cee_catalunya_notfound.json")
    result = provider.lookup(MISSING)
    assert result.status == CeeStatus.INCONCLUSIVE
    assert result.record is None
    assert result.note


def test_lookup_rejects_unsafe_refcat(tmp_path) -> None:
    # El refcat se interpola en el $where de Socrata: caracteres fuera del
    # formato catastral no deben llegar a la consulta.
    provider = _provider(tmp_path, "x' OR '1'='1", "cee_catalunya_notfound.json")
    result = provider.lookup("x' OR '1'='1")
    assert result.status == CeeStatus.INCONCLUSIVE
    assert result.record is None


def test_catalunya_declares_license() -> None:
    declaration = load_license(Path(catalunya_pkg.__file__).parent)
    assert declaration.license_url.startswith("http")
    assert declaration.verified_on


def test_provider_cannot_init_without_license(tmp_path, monkeypatch) -> None:
    package = tmp_path / "catalunya_no_license"
    package.mkdir()
    monkeypatch.setattr(
        "habitalens.cee.base.inspect.getfile",
        lambda _cls: str(package / "provider.py"),
    )
    with pytest.raises(LicensingNotDeclaredError):
        CatalunyaCeeProvider()
