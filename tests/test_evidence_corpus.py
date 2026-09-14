"""El corpus preregistrado no cambia por resultados (incluidas enmiendas)."""

from __future__ import annotations

from habitalens.cadastre_providers import provider_ids
from habitalens.evidence import CORPUS, property_by_id


def test_corpus_has_eight_properties() -> None:
    assert len(CORPUS) == 8
    assert len({item.id for item in CORPUS}) == 8
    refcats = [item.refcat for item in CORPUS]
    assert len(set(refcats)) == 8


def test_corpus_providers_are_registered() -> None:
    for item in CORPUS:
        assert item.provider_id in provider_ids()


def test_amendment_e1_authorities() -> None:
    # Enmienda E1: filas 3 y 4 pertenecen a Gipuzkoa y Araba respectivamente.
    assert property_by_id("p03_donostia_mayor").provider_id == "gipuzkoa"
    assert property_by_id("p04_vitoria_postas").provider_id == "araba"
    assert property_by_id("p06_gipuzkoa_periurbana").provider_id == "gipuzkoa"
    assert property_by_id("p08_araba_rustica").provider_id == "araba"
