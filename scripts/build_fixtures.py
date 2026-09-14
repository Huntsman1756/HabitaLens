"""Construye fixtures congeladas a partir de capturas live (probe).

No forma parte del paquete. Lee la cache del probe y escribe fixtures pequenas
en tests/fixtures/data/ para los tests offline.
"""

from __future__ import annotations

import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBE_RAW = ROOT / ".habitalens-probe" / "cache" / "raw"
FIXTMP = ROOT / ".fixtmp"
OUT = ROOT / "tests" / "fixtures" / "data"


def copy(src: Path, name: str) -> None:
    dst = OUT / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    print(f"wrote {dst.relative_to(ROOT)} ({dst.stat().st_size} bytes)")


def trim_feed(src: Path, name: str, contains: str) -> None:
    text = src.read_text(encoding="utf-8", errors="ignore")
    entries = re.findall(r"<entry[\s\S]*?</entry>", text)
    kept = [e for e in entries if contains in e]
    if not kept:
        raise SystemExit(f"no entry containing {contains!r} in {src}")
    start = re.search(r"<(?![?!])", text).start()
    root_open = text[start : text.find(">", start) + 1]
    feed = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        + root_open
        + "\n"
        + "\n".join(kept)
        + "\n</feed>\n"
    )
    dst = OUT / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(feed, encoding="utf-8")
    print(f"wrote {dst.relative_to(ROOT)} ({len(kept)} entry)")


def extract_feature(zip_path: Path, refcat: str, name: str) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        payload = None
        for member in archive.namelist():
            if member.lower().endswith((".gml", ".xml")) and "MD" not in member:
                payload = archive.read(member)
                break
    assert payload is not None, "sin GML en el zip"
    text = payload.decode("utf-8", errors="ignore")
    index = text.find(refcat)
    if index < 0:
        raise SystemExit(f"feature {refcat} no encontrada en {zip_path}")
    start = text.rfind("<cp:CadastralParcel", 0, index)
    end = text.find("</cp:CadastralParcel>", index) + len("</cp:CadastralParcel>")
    if start < 0 or end <= start:
        raise SystemExit(f"delimitadores de feature no encontrados para {refcat}")
    feature = text[start:end]
    root_start = re.search(r"<(?![?!])", text).start()
    root_open = text[root_start : text.find(">", root_start) + 1]
    root_name = root_open[1:].split(" ", 1)[0].rstrip(">")
    document = (
        root_open
        + f'<wfs:member xmlns:wfs="http://www.opengis.net/wfs/2.0">{feature}</wfs:member>'
        + f"</{root_name}>"
    )
    dst = OUT / name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(document, encoding="utf-8")
    print(f"wrote {dst.relative_to(ROOT)} (feature {refcat})")


def main() -> None:
    copy(PROBE_RAW / "dgc" / "capabilities.xml", "dgc_capabilities.xml")
    trim_feed(
        PROBE_RAW / "dgc" / "atom-index_https_www.catastro.hacienda.gob.es_INSPIRE_CadastralParcels_ES.SDGC.CP.atom.xml.xml",
        "dgc_atom_index.xml",
        "atom_17.xml",
    )
    trim_feed(
        PROBE_RAW / "dgc" / "atom-province_17.xml",
        "dgc_atom_province_17.xml",
        "A.ES.SDGC.CP.17079.zip",
    )
    copy(FIXTMP / "dgc_parcel.gml", "dgc_parcel.gml")
    copy(FIXTMP / "bucount.gml", "dgc_buildings.gml")

    copy(PROBE_RAW / "navarra" / "capabilities.xml", "navarra_capabilities.xml")
    copy(PROBE_RAW / "navarra" / "parcel_001010001.xml", "navarra_parcel.xml")
    copy(PROBE_RAW / "navarra" / "building_001010001.xml", "navarra_buildings.xml")

    copy(PROBE_RAW / "bizkaia" / "capabilities.xml", "bizkaia_capabilities.xml")
    copy(PROBE_RAW / "bizkaia" / "atom-index_https_apli.bizkaia.eus_apps_Danok_INSPIRE_cadastralparcels.xml.xml", "bizkaia_atom_index.xml")
    extract_feature(
        PROBE_RAW / "bizkaia" / "atom-zip_parcel_020.zip",
        "48.020.1619.04006",
        "bizkaia_parcel.gml",
    )
    copy(PROBE_RAW / "bizkaia" / "building_48.020.1619.04006.xml", "bizkaia_buildings.xml")

    copy(PROBE_RAW / "gipuzkoa" / "capabilities.xml", "gipuzkoa_capabilities.xml")
    copy(PROBE_RAW / "gipuzkoa" / "parcel_8594149.xml", "gipuzkoa_parcel.xml")
    copy(PROBE_RAW / "gipuzkoa" / "building_8594149.xml", "gipuzkoa_buildings.xml")

    copy(PROBE_RAW / "araba" / "capabilities.xml", "araba_capabilities.xml")
    copy(PROBE_RAW / "araba" / "parcel_64010007.xml", "araba_parcel.xml")
    copy(PROBE_RAW / "araba" / "building_64010007.xml", "araba_buildings.xml")

    copy(PROBE_RAW / "cartociudad" / "find.json", "cartociudad_find.json")
    copy(FIXTMP / "cc_candidates.json", "cartociudad_candidates.json")


if __name__ == "__main__":
    main()
