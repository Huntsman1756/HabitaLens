"""Golden tests del resolver: misma entrada + misma fixture = mismo resultado."""

from __future__ import annotations

from habitalens.geocoding import CartoCiudadClient
from habitalens.net import FixtureSource
from habitalens.resolver import PropertyResolver, TerritoryRouter
from habitalens.resolver.territory_router import TerritoryRoutingError
from tests.conftest import DATA, make_provider


def _cartociudad_client(query: str = "Calle Mayor 1, Madrid") -> CartoCiudadClient:
    source = FixtureSource(
        {
            f"cartociudad:{CartoCiudadClient._key('find', query)}": DATA / "cartociudad_find.json",
            f"cartociudad:{CartoCiudadClient._key('candidates', query)}": DATA
            / "cartociudad_candidates.json",
        }
    )
    return CartoCiudadClient(source=source)


def test_cartociudad_routes_madrid_to_dgc() -> None:
    client = _cartociudad_client()
    candidate = client.geocode("Calle Mayor 1, Madrid")

    assert candidate is not None
    assert candidate.refcat == "0343302VK4704C"
    assert candidate.territory_hint is not None
    assert TerritoryRouter().route_address(candidate.to_address()) == "dgc"


def test_unknown_refcat_is_not_routed() -> None:
    try:
        TerritoryRouter().route_refcat("sin-formato")
    except TerritoryRoutingError:
        pass
    else:  # pragma: no cover
        raise AssertionError("un refcat invalido no debe encaminarse")


def test_resolver_e2e_address_to_dgc_parcel(tmp_path) -> None:
    dgc = make_provider(
        "dgc",
        tmp_path,
        extra={
            "dgc:parcel-near:near:40.41646,-3.70466": DATA / "dgc_madrid_parcel.gml",
            "dgc:building:0343302VK4704C": DATA / "dgc_buildings.gml",
        },
    )
    resolver = PropertyResolver(
        providers={"dgc": dgc}, geocoder=_cartociudad_client()
    )

    property_ = resolver.resolve("Calle Mayor 1, Madrid")

    assert property_.territory.value == "dgc"
    assert property_.parcel.refcat == "0343302VK4704C"
    assert property_.parcel.provider == "dgc"
    assert property_.parcel.crs.startswith("EPSG:")
    assert len(property_.buildings) >= 1
    assert property_.address is not None
    assert property_.address.refcat_candidate == "0343302VK4704C"


def test_resolver_refcat_to_foral_provider(tmp_path) -> None:
    gipuzkoa = make_provider("gipuzkoa", tmp_path)
    resolver = PropertyResolver(providers={"gipuzkoa": gipuzkoa})

    property_ = resolver.resolve("8594149")

    assert property_.parcel.provider == "gipuzkoa"
    assert property_.parcel.refcat == "8594149"
    assert property_.parcel.crs == "EPSG:4258"
    assert len(property_.buildings) == 5
    assert property_.address is None


def test_determinism_same_input_same_result(tmp_path) -> None:
    resolver = PropertyResolver(providers={"gipuzkoa": make_provider("gipuzkoa", tmp_path)})
    first = resolver.resolve("8594149")
    second = resolver.resolve("8594149")

    def fingerprint(property_):
        return {
            "territory": property_.territory.value,
            "parcel": (
                property_.parcel.refcat,
                property_.parcel.area_m2,
                property_.parcel.land_use,
                property_.parcel.crs,
                property_.parcel.source_version,
                property_.parcel.provider,
            ),
            "buildings": tuple(
                (b.building_id, b.area_m2, b.crs, b.refcat)
                for b in property_.buildings
            ),
        }

    assert fingerprint(first) == fingerprint(second)
