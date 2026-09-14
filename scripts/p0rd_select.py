"""P0-RD: seleccion determinista de 10 viviendas DGC resolubles.

Usa el pool DGC congelado. NO consulta ninguna capa de riesgo. Escribe
p0rd/p0rd_frame.json para commitear antes de ejecutar el motor de evidencia.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.cadastre_providers import get_provider
from habitalens.provenance import ProvenanceRecorder

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "p0r" / "p0r_pool_dgc.json.gz"
EXPECTED_SHA = "33b709872bd0af04a5e2b89f523b2a365729525d8c1c784ca8311b89c7e96fec"
OUT = ROOT / "p0rd"
TAKE = 10


def _score(stable_id: str) -> str:
    return hashlib.sha256(f"habitalens-p0rd-v1|{stable_id}".encode()).hexdigest()


def main() -> None:
    raw = gzip.decompress(POOL.read_bytes())
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA:
        raise SystemExit(f"pool SHA mismatch: {sha} != {EXPECTED_SHA}")
    pool = json.loads(raw)["candidates"]
    ranked = sorted(pool, key=lambda row: _score(row["stable_property_id"]))
    print("pool candidates:", len(ranked), "sha256 ok")

    cache = CacheStore(ROOT / ".habitalens-g0c")
    provenance = ProvenanceRecorder(ROOT / ".habitalens-g0c")
    provider = get_provider("dgc", cache=cache, provenance=provenance)

    selected = []
    substitutions = []
    for row in ranked:
        if len(selected) >= TAKE:
            break
        refcat = row["stable_property_id"]
        try:
            parcel = provider.resolve_reference(refcat)
            _geometry, crs = provider._parcel_geometry(parcel.refcat)
        except Exception as exc:
            substitutions.append({"stable_property_id": refcat, "reason": str(exc)[:160]})
            continue
        selected.append(
            {
                "property_id": f"p0rd{len(selected) + 1:02d}",
                "stable_property_id": refcat,
                "score": _score(refcat),
                "provider": "dgc",
                "resolved_refcat": parcel.refcat,
                "source_crs": crs,
                "numberOfDwellings": row.get("numberOfDwellings"),
            }
        )
        print(f"  selected {parcel.refcat} (score {_score(refcat)[:10]})")

    OUT.mkdir(parents=True, exist_ok=True)
    frame = {
        "pilot": "P0-RD",
        "pool_sha256": EXPECTED_SHA,
        "selection": 'SHA256("habitalens-p0rd-v1|"+stable_property_id), ascending, first 10 resolvable',
        "selected": selected,
        "substitutions": substitutions,
    }
    (OUT / "p0rd_frame.json").write_text(json.dumps(frame, indent=2, ensure_ascii=False), encoding="utf-8")
    print("selected:", len(selected), "substitutions:", len(substitutions))
    print("frame ->", OUT / "p0rd_frame.json")


if __name__ == "__main__":
    main()
