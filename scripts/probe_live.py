"""Probe live G0-A (no forma parte del paquete). Captura evidencia reproducible."""

from __future__ import annotations

import json
import traceback

from habitalens.cadastre_providers import get_provider
from habitalens.geocoding import CartoCiudadClient

CASES = [
    ("dgc", "1707903VK4810F"),
    ("navarra", "001010001"),
    ("bizkaia", "48.020.1619.04006"),
    ("gipuzkoa", "8594149"),
    ("araba", "64010007"),
]


def main() -> None:
    results = {}
    for provider_id, refcat in CASES:
        print("=" * 70)
        print(f"{provider_id} :: {refcat}")
        entry = {"refcat": refcat}
        try:
            provider = get_provider(provider_id, persist=True)
            parcel = provider.resolve_reference(refcat)
            entry["parcel"] = parcel.model_dump(mode="json")
            buildings = provider.get_buildings(refcat)
            entry["building_count"] = len(buildings)
            entry["buildings"] = [b.model_dump(mode="json") for b in buildings[:3]]
            entry["source_version"] = provider.source_version()
            entry["coverage"] = provider.coverage().model_dump(mode="json")
            entry["status"] = "PASS"
            print("PARCEL", parcel.refcat, parcel.area_m2, parcel.crs)
            print("BUILDINGS", len(buildings))
            print("VERSION", entry["source_version"])
        except Exception as exc:
            entry["status"] = "FAIL"
            entry["error"] = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
        results[provider_id] = entry

    print("=" * 70)
    print("CARTO CIUDAD")
    try:
        client = CartoCiudadClient()
        candidate = client.geocode("Calle Mayor 1, Madrid")
        results["cartociudad"] = {
            "status": "PASS" if candidate else "FAIL",
            "candidate": candidate.__dict__ if candidate else None,
        }
        print(candidate)
    except Exception as exc:
        results["cartociudad"] = {"status": "FAIL", "error": str(exc)}
        traceback.print_exc()

    print(json.dumps(results, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
