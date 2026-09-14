"""Contrato CadastreProvider: 5 casos reales, offline con fixtures congeladas."""

from __future__ import annotations

import pytest

from habitalens.property.models import FORBIDDEN_FIELD_TOKENS
from tests.conftest import CONTRACT_CASES, make_provider


@pytest.mark.parametrize("provider_id,refcat", CONTRACT_CASES)
def test_provider_contract(provider_id: str, refcat: str, tmp_path) -> None:
    provider = make_provider(provider_id, tmp_path)

    parcel = provider.resolve_reference(refcat)

    assert parcel.refcat.upper() == refcat.upper()
    assert parcel.provider == provider_id
    assert parcel.territory.value == provider_id
    assert parcel.crs.startswith("EPSG:")
    assert parcel.area_m2 is not None and parcel.area_m2 > 0
    assert parcel.source_version
    assert parcel.provenance_id

    buildings = provider.get_buildings(refcat)
    assert isinstance(buildings, list)
    assert all(building.provider == provider_id for building in buildings)
    assert all(building.crs.startswith("EPSG:") for building in buildings)

    coverage = provider.coverage()
    assert coverage.territory == parcel.territory
    assert coverage.codes


@pytest.mark.parametrize("provider_id,refcat", CONTRACT_CASES)
def test_provider_does_not_expose_geometry(provider_id: str, refcat: str, tmp_path) -> None:
    provider = make_provider(provider_id, tmp_path)
    parcel = provider.resolve_reference(refcat)

    dumped_fields = list(parcel.model_dump().keys())
    for field in dumped_fields:
        assert not any(token in field.lower() for token in FORBIDDEN_FIELD_TOKENS)
    dumped_text = parcel.model_dump_json().lower()
    for token in ("poslist", "polygon", "multisurface", "geojson", "__geo_interface__"):
        assert token not in dumped_text
    assert not hasattr(parcel, "__geo_interface__")
    assert not hasattr(parcel, "geometry")


def test_no_provider_implements_resolve_address() -> None:
    from habitalens.cadastre_providers import get_provider

    # La geocodificacion es exclusiva de CartoCiudad + TerritoryRouter.
    assert not hasattr(get_provider("dgc"), "resolve_address")
    assert not hasattr(get_provider("navarra"), "resolve_address")


def test_geometry_is_persisted_internally(tmp_path) -> None:
    provider_id = "gipuzkoa"
    provider = make_provider(provider_id, tmp_path)
    provider.resolve_reference("8594149")

    cache = provider._cache
    geo_dir = cache.root / "cache" / "geo" / provider_id
    assert geo_dir.exists()
    assert any(geo_dir.iterdir())
    meta = cache.read_meta(provider_id, "geo_parcel:8594149")
    assert meta is not None
    assert meta["crs"].startswith("EPSG:")
    assert meta["source_version"]
