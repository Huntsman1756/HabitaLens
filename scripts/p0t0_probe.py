"""P0-T0: probe del CSV oficial de Subastas Judiciales (solo esquema/licencia).

No consulta capas de riesgo, no selecciona manualmente y no scrapea: descarga la
cabecera del CSV publico y comprueba si contiene direccion/referencia suficiente
para resolver la finca.
"""

from __future__ import annotations

import csv
import io
import urllib.request

CSV_URL = "https://catalogodatos.justicia.es/csv/Subastas_Judiciales.csv"
HEAD_BYTES = 200_000

ADDRESS_HINTS = ("direccion", "dirección", "address", "refcat", "catastral", "localidad", "municipio", "provincia")


def fetch_head() -> str:
    request = urllib.request.Request(CSV_URL, headers={"Range": f"bytes=0-{HEAD_BYTES}"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="ignore")


def main() -> None:
    text = fetch_head()
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = next(reader)
    rows = [row for _, row in zip(range(20), reader, strict=False)]
    print("columns:", header)
    lowered = [column.lower() for column in header]
    address_columns = [c for c in lowered if any(h in c for h in ADDRESS_HINTS)]
    print("address/reference columns:", address_columns)
    print("sample rows:", len(rows))
    resolvable = bool(address_columns)
    print("P0-T0 verdict:", "PASS" if resolvable else "FAIL (sin direccion/referencia)")


if __name__ == "__main__":
    main()
