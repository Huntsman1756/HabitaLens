"""G0-A.1: probe de remediacion DGC (stored queries, DNPRC, ATOM municipal)."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

TMP = Path(r"C:\Users\rome_\AppData\Local\Temp\opencode")


def main() -> None:
    bu = (TMP / "bu_1707903VK4810F.gml").read_text(encoding="ISO-8859-1")
    tags = re.findall(r"<([A-Za-z0-9_]+):([A-Za-z0-9_]+)[ >]", bu)
    print("BU prefixes:", Counter(prefix for prefix, _ in tags).most_common(10))
    for match in re.finditer(r"<[A-Za-z0-9_]+:(Building|BuildingPart)[ >]", bu):
        print("BU feature:", bu[match.start() : match.start() + 140].replace("\n", " "))

    for match in re.finditer(r"Building", bu):
        snippet = bu[max(0, match.start() - 60) : match.start() + 60].replace("\n", " ")
        if "<" in snippet:
            print("BU ref:", snippet)

    feed = (TMP / "dgc_atom_28.xml").read_text(encoding="utf-8", errors="ignore")
    codes = re.findall(r"A\.ES\.SDGC\.CP\.(\d{5})\.zip", feed)
    print("zip codes:", len(codes), "min/max:", min(codes, default="-"), max(codes, default="-"))
    print("has 28079:", "28079" in codes)
    print("around 28079:", [c for c in codes if c.startswith("2807") or c.startswith("2808")])


if __name__ == "__main__":
    main()
