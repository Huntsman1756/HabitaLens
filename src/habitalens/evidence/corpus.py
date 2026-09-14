"""Corpus preregistrado de 8 propiedades (docs/g0-b-preregistration.md seccion 5).

Seleccion por diversidad de contexto, NO por resultado esperado. La autoridad
de las filas 3 y 4 se corrige en la enmienda E1 (Gipuzkoa y Araba).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CorpusProperty:
    id: str
    provider_id: str
    refcat: str
    label: str
    territory: str
    context: str


CORPUS: tuple[CorpusProperty, ...] = (
    CorpusProperty(
        "p01_madrid_castellana",
        "dgc",
        "1707903VK4810F",
        "Madrid, Paseo de la Castellana 255",
        "dgc",
        "urbano denso interior",
    ),
    CorpusProperty(
        "p02_madrid_mayor",
        "dgc",
        "0343302VK4704C",
        "Madrid, Calle Mayor 1",
        "dgc",
        "casco historico",
    ),
    CorpusProperty(
        "p03_donostia_mayor",
        "gipuzkoa",
        "8297093",
        "Donostia, Calle Mayor",
        "gipuzkoa",
        "urbano costero",
    ),
    CorpusProperty(
        "p04_vitoria_postas",
        "araba",
        "59590687",
        "Vitoria-Gasteiz, Calle Postas 1",
        "araba",
        "urbano interior",
    ),
    CorpusProperty(
        "p05_bilbao_granvia",
        "bizkaia",
        "48.020.1619.04006",
        "Bilbao, Gran Via 1",
        "bizkaia",
        "urbano industrial-portuario",
    ),
    CorpusProperty(
        "p06_gipuzkoa_periurbana",
        "gipuzkoa",
        "8594149",
        "Gipuzkoa, parcela periurbana",
        "gipuzkoa",
        "periurbano amplio",
    ),
    CorpusProperty(
        "p07_navarra_urbana",
        "navarra",
        "001010001",
        "Navarra, urbano",
        "navarra",
        "urbano, posible entorno fluvial",
    ),
    CorpusProperty(
        "p08_araba_rustica",
        "araba",
        "64010007",
        "Araba, rustico interior",
        "araba",
        "rustico interior",
    ),
)


def property_by_id(property_id: str) -> CorpusProperty:
    for item in CORPUS:
        if item.id == property_id:
            return item
    raise KeyError(f"propiedad fuera del corpus preregistrado: {property_id}")
