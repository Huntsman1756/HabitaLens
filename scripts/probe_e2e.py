"""Probe E2E live: CartoCiudad -> TerritoryRouter -> proveedor -> parcela."""

from __future__ import annotations

import json
import traceback

from habitalens.cadastre_providers import get_provider
from habitalens.resolver import PropertyResolver

ADDRESSES = [
    "Calle Mayor 1, Madrid",
    "Calle Mayor 1, Donostia",
]


def main() -> None:
    results = {}

    # DGC por localizacion (bbox) usando la coordenada del geocoder.
    try:
        dgc = get_provider("dgc")
        parcel = dgc.get_parcel_near(40.416461059323886, -3.7046584169537073)
        results["dgc_near"] = {
            "status": "PASS",
            "refcat": parcel.refcat,
            "area_m2": parcel.area_m2,
            "crs": parcel.crs,
        }
        try:
            buildings = dgc.get_buildings(parcel.refcat)
            results["dgc_near"]["buildings"] = len(buildings)
        except Exception as exc:
            results["dgc_near"]["buildings"] = f"INCONCLUSIVE: {exc}"
    except Exception as exc:
        results["dgc_near"] = {"status": "FAIL", "error": str(exc)}
        traceback.print_exc()

    for address in ADDRESSES:
        try:
            property_ = PropertyResolver().resolve(address)
            results[address] = {
                "status": "PASS",
                "territory": property_.territory.value,
                "refcat": property_.parcel.refcat,
                "provider": property_.parcel.provider,
                "crs": property_.parcel.crs,
                "buildings": len(property_.buildings),
            }
        except Exception as exc:
            results[address] = {"status": "INCONCLUSIVE", "error": str(exc)}
            traceback.print_exc()

    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
