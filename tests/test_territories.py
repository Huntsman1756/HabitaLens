"""El fixture territorios.yaml debe cubrir exactamente los proveedores G0-A."""

from __future__ import annotations

import re

import yaml

from habitalens.cadastre_providers import provider_ids
from habitalens.property import RefCat, infer_territory
from tests.conftest import DATA


def _territories() -> dict:
    path = DATA.parent / "territories.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))["provider_territories"]


def test_territories_match_registry() -> None:
    assert set(_territories()) == set(provider_ids())


def test_refcat_patterns_are_consistent_with_router() -> None:
    samples = {
        "dgc": "1707903VK4810F",
        "navarra": "001010001",
        "bizkaia": "48.001.1055.99082",
        "gipuzkoa": "8594149",
        "araba": "64010007",
    }
    for provider_id, sample in samples.items():
        data = _territories()[provider_id]
        assert any(re.match(pattern, sample) for pattern in data["refcat_patterns"]), (
            f"el patron de {provider_id} no reconoce {sample}"
        )
        assert infer_territory(sample).value == provider_id
        assert RefCat.parse(sample).territory.value == provider_id
