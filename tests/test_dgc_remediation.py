"""G0-A.1: stored queries DGC + corroboracion DNPRC (offline, fixtures reales)."""

from __future__ import annotations

from habitalens.cadastre_providers.dgc.provider import parse_dnprc
from tests.conftest import DATA, make_provider


def test_dgc_getparcel_stored_query(tmp_path) -> None:
    provider = make_provider("dgc", tmp_path)
    parcel = provider.resolve_reference("1707903VK4810F")
    assert parcel.refcat == "1707903VK4810F"
    assert parcel.crs == "EPSG:4326"
    assert parcel.area_m2 is not None and parcel.area_m2 > 0


def test_dgc_getbuildingbyparcel_stored_query(tmp_path) -> None:
    provider = make_provider("dgc", tmp_path)
    buildings = provider.get_buildings("1707903VK4810F")
    assert len(buildings) >= 1
    assert buildings[0].refcat == "1707903VK4810F"
    assert buildings[0].crs == "EPSG:25830"


def test_dgc_stored_query_parameters_are_documented_operations(tmp_path) -> None:
    provider = make_provider("dgc", tmp_path)
    request = provider._stored_query_request("parcel", "1707903VK4810F")
    params = dict(request.params)
    assert params["STOREDQUERY_ID"] == "GetParcel"
    assert params["refcat"] == "1707903VK4810F"
    assert "filter" not in params and "resourceId" not in params

    building_request = provider._stored_query_request("building", "1707903VK4810F")
    assert dict(building_request.params)["STOREDQUERY_ID"] == "GetBuildingByParcel"


def test_dnprc_corroborates_reference_and_locates_real_municipality(tmp_path) -> None:
    provider = make_provider("dgc", tmp_path)
    data = provider.corroborate_reference("1707903VK4810F")

    assert data.exists
    assert data.refcat == "1707903VK4810F"
    # La RC urbana NO codifica el municipio en sus primeros caracteres:
    # 1707903VK4810F pertenece a Madrid (28/079), no a Fortia (17/079).
    assert (data.province_code, data.municipality_code) == ("28", "79")
    assert data.municipality_name == "MADRID"
    assert data.province_name == "MADRID"
    assert data.area_m2 == 564.0
    assert data.land_use == "Almacen-Estacionamiento"
    assert data.address and "CASTELLANA" in data.address


def test_dnprc_negative_control_differs(tmp_path) -> None:
    provider = make_provider("dgc", tmp_path)
    data = provider.corroborate_reference("0000000XX0000X")
    assert not data.exists
    assert data.error and "NO EXISTE" in data.error.upper()


def test_parse_dnprc_negative_fixture() -> None:
    data = parse_dnprc((DATA / "dgc_dnprc_negative.xml").read_bytes())
    assert not data.exists


def test_municipal_atom_feed_for_madrid_omits_capital() -> None:
    """Hallazgo documentado: el feed ATOM de la provincia 28 omite 28079 (Madrid)."""

    feed = (DATA / "dgc_atom_province_28.xml").read_text(encoding="utf-8", errors="ignore")
    assert "A.ES.SDGC.CP.28079.zip" not in feed
    assert "A.ES.SDGC.CP.28080.zip" in feed
