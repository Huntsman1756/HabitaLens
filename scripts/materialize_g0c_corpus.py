"""G0-C: materializa el corpus de 24 propiedades ANTES de consultar SIU/NCSE/BTN.

Bloque A: 10 refcats conocidos (congelados).
Bloque B: 14 direcciones fijas (se resuelven a refcat con CartoCiudad + proveedor).

Escribe fixtures internas (WKT + metadatos) y un manifiesto JSON que sera la
linea base del corpus. No consulta ninguna fuente de G0-C.
"""

from __future__ import annotations

import json
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.cadastre_providers import get_provider
from habitalens.geocoding import CartoCiudadClient
from habitalens.property import infer_territory
from habitalens.provenance import ProvenanceRecorder

ROOT = Path(__file__).resolve().parents[1]
CACHE_ROOT = ROOT / ".habitalens-g0c"
DATA = ROOT / "tests" / "fixtures" / "data" / "properties_g0c"
MANIFEST = ROOT / "src" / "habitalens" / "evidence" / "corpus_g0c.json"

BLOCK_A = [
    ("g0c01", "dgc", "1707903VK4810F", "Madrid Castellana 255", "urbano denso"),
    ("g0c02", "dgc", "0343302VK4704C", "Madrid Calle Mayor 1", "casco historico"),
    ("g0c03", "gipuzkoa", "8297093", "Donostia Calle Mayor", "urbano costero"),
    ("g0c04", "araba", "59590687", "Vitoria Postas 1", "urbano interior"),
    ("g0c05", "bizkaia", "48.020.1619.04006", "Bilbao Gran Via 1", "industrial-portuario"),
    ("g0c06", "gipuzkoa", "8594149", "Gipuzkoa periurbana", "periurbano"),
    ("g0c07", "navarra", "001010001", "Navarra urbana", "urbano"),
    ("g0c08", "araba", "64010007", "Araba rustica", "rustico"),
    ("g0c09", "dgc", "0244604VK4704C", "Madrid proximo", "urbano denso"),
    ("g0c10", "bizkaia", "48.001.1055.99082", "Bizkaia rustica", "rustico"),
]

#: Lista final tras la enmienda E1 de G0-C (desambiguacion estricta + geocodabilidad,
#: decidida antes de consultar SIU/NCSE/BTN).
BLOCK_B = [
    "Calle Mayor 1, Oviedo",
    "Calle Real 1, A Coruna",
    "Calle Mayor 1, Santander",
    "Calle Mayor 1, Valladolid",
    "Calle Mayor 1, Zaragoza",
    "Calle Mayor 1, Sevilla",
    "Calle Mayor 1, Murcia",
    "Calle Colon 1, Cadiz",
    "Calle Mayor 1, Granada",
    "Calle Comercio 1, Toledo",
    "Avenida de Huelva 1, Badajoz",
    "Calle Mayor 1, Caceres",
    "Calle Mayor 1, Logrono",
    "Calle Mayor 1, Salamanca",
]


def _geometry(provider, refcat):
    provider.get_parcel(refcat)
    return provider._parcel_geometry(refcat)


def main() -> None:
    DATA.mkdir(parents=True, exist_ok=True)
    cache = CacheStore(CACHE_ROOT)
    provenance = ProvenanceRecorder(CACHE_ROOT)
    geocoder = CartoCiudadClient(cache=cache, refresh=False)

    entries: list[dict] = []
    failures: list[str] = []

    for item_id, provider_id, refcat, label, context in BLOCK_A:
        provider = get_provider(provider_id, cache=cache, provenance=provenance)
        try:
            geometry, crs = _geometry(provider, refcat)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{item_id} {refcat}: {exc}")
            continue
        entries.append(
            {
                "id": item_id,
                "block": "A",
                "provider_id": provider_id,
                "refcat": refcat,
                "label": label,
                "context": context,
                "source_crs": crs,
            }
        )
        _write_geometry(item_id, geometry.wkt)
        print(f"{item_id} blockA {provider_id} {refcat} crs={crs}")

    for index, address in enumerate(BLOCK_B, start=11):
        item_id = f"g0c{index:02d}"
        candidate = geocoder.geocode(address)
        if candidate is None or not candidate.refcat:
            failures.append(f"{item_id} {address}: sin refcat de CartoCiudad")
            continue
        refcat = candidate.refcat
        territory = infer_territory(refcat)
        provider_id = territory.value if territory is not None else "dgc"
        try:
            provider = get_provider(provider_id, cache=cache, provenance=provenance)
            geometry, crs = _geometry(provider, refcat)
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{item_id} {address} -> {provider_id} {refcat}: {exc}")
            continue
        entries.append(
            {
                "id": item_id,
                "block": "B",
                "provider_id": provider_id,
                "refcat": refcat,
                "label": address,
                "context": f"geocodificada ({candidate.municipality})",
                "source_crs": crs,
            }
        )
        _write_geometry(item_id, geometry.wkt)
        print(f"{item_id} blockB {address} -> {provider_id} {refcat} crs={crs}")

    MANIFEST.write_text(
        json.dumps({"entries": entries, "failures": failures}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"\ncorpus materializado: {len(entries)}/24, fallos={len(failures)}")
    for failure in failures:
        print("  FAIL", failure)


def _write_geometry(item_id: str, wkt: str) -> None:
    (DATA / f"{item_id}.wkt").write_text(wkt, encoding="utf-8")


if __name__ == "__main__":
    main()
