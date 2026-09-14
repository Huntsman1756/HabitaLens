"""P0-R (E1): materializa el pool residencial DGC de forma determinista.

Solo datos catastrales DGC autorizados en G0-A. No consulta capas de riesgo.
Muestreo sistematico de municipios sobre la lista nacional de ZIP BU.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "p0r"
UA = {"User-Agent": "HabitaLens/0.0 (P0-R frame materialization; research)"}
INDEX = "https://www.catastro.hacienda.gob.es/INSPIRE/buildings/ES.SDGC.BU.atom.xml"
MUNICIPALITIES = 8
SOURCE_VERSION = "DGC INSPIRE ATOM buildings (BU) verificado 2026-09-14"


def _get(url: str, timeout: int = 120) -> bytes:
    import urllib.parse

    safe_url = urllib.parse.quote(url, safe=":/?=&%")
    return urllib.request.urlopen(urllib.request.Request(safe_url, headers=UA), timeout=timeout).read()


def _province_feeds() -> list[str]:
    index = _get(INDEX).decode("utf-8", "ignore")
    return sorted(set(re.findall(r'href="([^"]+atom_\d+\.xml)"', index)))


def _municipality_zips(feeds: list[str]) -> list[str]:
    zips: set[str] = set()
    for feed in feeds:
        try:
            text = _get(feed, timeout=90).decode("utf-8", "ignore")
        except Exception:
            continue
        zips.update(re.findall(r'href="(https?://[^"]+A\.ES\.SDGC\.BU\.\d{5}\.zip)"', text))
    return sorted(zips, key=lambda u: re.search(r"BU\.(\d{5})\.zip", u).group(1))


def _systematic(items: list[str], count: int) -> list[str]:
    if len(items) <= count:
        return items
    step = (len(items) - 1) / (count - 1)
    return [items[round(i * step)] for i in range(count)]


def _residential(gml: str) -> list[dict]:
    pattern = re.compile(
        r'<bu-ext2d:Building[^>]*gml:id="[^"]*?([0-9A-Z]{13,14})"[\s\S]*?'
        r"<bu-ext2d:currentUse>([^<]+)</bu-ext2d:currentUse>[\s\S]*?"
        r"<bu-ext2d:numberOfDwellings>([^<]*)</bu-ext2d:numberOfDwellings>"
    )
    rows = []
    for refcat, use, dwellings in pattern.findall(gml):
        value = (dwellings or "").strip()
        if use == "1_residential" and value.isdigit() and int(value) >= 1:
            rows.append({"stable_property_id": refcat, "residential_eligibility": "1_residential", "numberOfDwellings": int(value)})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    feeds = _province_feeds()
    print("province feeds:", len(feeds))
    zips = _municipality_zips(feeds)
    print("municipality BU zips:", len(zips))
    sample = _systematic(zips, MUNICIPALITIES)
    print("sampled municipalities:", len(sample))

    pool: list[dict] = []
    for url in sample:
        code = re.search(r"BU\.(\d{5})\.zip", url).group(1)
        try:
            payload = _get(url)
        except Exception as exc:  # noqa: BLE001
            print(f"  {code}: ERROR {exc}")
            continue
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            building = next((n for n in archive.namelist() if n.endswith(".building.gml")), None)
            if building is None:
                continue
            gml = archive.read(building).decode("utf-8", "ignore")
        rows = _residential(gml)
        for row in rows:
            pool.append({"provider": "dgc", **row})
        print(f"  {code}: {len(rows)} residenciales (pool={len(pool)})")

    payload = json.dumps(
        {"provider": "dgc", "source_version": SOURCE_VERSION, "candidates": pool},
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    (OUT / "p0r_pool_dgc.json").write_text(payload, encoding="utf-8")
    manifest = {
        "provider": "dgc",
        "residential_candidates": len(pool),
        "pool_sha256": digest,
        "source_version": SOURCE_VERSION,
        "procedure": (
            "DGC INSPIRE ATOM buildings: enumerate 52 province feeds, collect "
            "A.ES.SDGC.BU.<mun>.zip, systematic sample of 8 municipalities, parse "
            "bu-ext2d:Building with currentUse=1_residential and numberOfDwellings>=1"
        ),
        "municipalities_sampled": [re.search(r"BU\.(\d{5})\.zip", u).group(1) for u in sample],
    }
    (OUT / "p0r_pool_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("pool candidates:", len(pool), "sha256:", digest)


if __name__ == "__main__":
    main()
