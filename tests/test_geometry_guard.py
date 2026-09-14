"""Ningun objeto publico puede exponer geometria catastral."""

from __future__ import annotations

from habitalens.property.models import (
    FORBIDDEN_FIELD_TOKENS,
    Address,
    Building,
    Parcel,
    Property,
    RefCat,
    TerritoryMask,
)
from tests.conftest import make_provider


def _fields(model) -> list[str]:
    return list(model.model_fields.keys())


def test_public_models_have_no_geometry_fields() -> None:
    for model in (Address, Building, Parcel, Property, RefCat, TerritoryMask):
        for field in _fields(model):
            assert not any(token in field.lower() for token in FORBIDDEN_FIELD_TOKENS), (
                f"{model.__name__}.{field} parece geometria"
            )


def test_resolved_parcel_serialization_has_no_geometry(tmp_path) -> None:
    parcel = make_provider("gipuzkoa", tmp_path).resolve_reference("8594149")
    payload = parcel.model_dump_json().lower()
    for token in (
        "poslist",
        "polygon",
        "multisurface",
        "geojson",
        "__geo_interface__",
        "coordinates",
        "shape",
    ):
        assert token not in payload


def test_public_models_do_not_implement_geo_interface() -> None:
    for model in (Address, Building, Parcel, Property, RefCat, TerritoryMask):
        assert not hasattr(model, "__geo_interface__")
