"""Utilidades para feeds ATOM de descarga (resolucion municipal de refcat).

Se usan como estrategia de fallback verificada para proveedores cuyo WFS no
soporta filtros ad-hoc (DGC y Bizkaia).
"""

from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from habitalens.cadastre_providers.inspire import localname

ATOM_NS = "http://www.w3.org/2005/Atom"


@dataclass(frozen=True)
class AtomEntry:
    title: str
    href: str
    type: str | None = None


def parse_atom_entries(content: bytes) -> list[AtomEntry]:
    root = ET.fromstring(content)
    entries: list[AtomEntry] = []
    for entry in root.iter():
        if localname(entry.tag) != "entry":
            continue
        title = ""
        for child in entry.iter():
            if localname(child.tag) == "title" and child.text:
                title = child.text.strip()
                break
        for child in entry.iter():
            if localname(child.tag) == "link" and child.attrib.get("href"):
                entries.append(
                    AtomEntry(
                        title=title,
                        href=child.attrib["href"],
                        type=child.attrib.get("type"),
                    )
                )
    return entries


_MUNICIPALITY_RE = re.compile(r"(\d{2,5})")


def find_municipality_zip(
    entries: list[AtomEntry], municipality_code: str, *, suffix: str = ".zip"
) -> str | None:
    """Busca el enclosure .zip de un municipio en un feed (formato Bizkaia)."""

    for entry in entries:
        if municipality_code in entry.href and entry.href.lower().endswith(suffix):
            return entry.href
    for entry in entries:
        match = _MUNICIPALITY_RE.search(entry.title)
        if match and match.group(1) == municipality_code and entry.href.endswith(suffix):
            return entry.href
    return None


def extract_zip_text(content: bytes, *, suffix: str = ".gml") -> list[bytes]:
    """Extrae el contenido de los ficheros GML/XML de un ZIP en memoria.

    Si el payload no es un ZIP (fixtures offline pueden inyectar GML directo),
    se devuelve tal cual para no forzar el empaquetado en los tests.
    """

    if not zipfile.is_zipfile(io.BytesIO(content)):
        return [content]
    results: list[bytes] = []
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        for name in archive.namelist():
            if name.lower().endswith(suffix) or name.lower().endswith(".xml"):
                results.append(archive.read(name))
    return results


def municipality_from_refcat_bizkaia(refcat: str) -> str:
    """Formato 48.NNN.MMMM.PPPPP: municipio = segundo bloque de 3 digitos."""

    parts = refcat.split(".")
    if len(parts) >= 2:
        return parts[1]
    return ""
