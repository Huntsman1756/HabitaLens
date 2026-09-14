"""Manifest G0-D: esquema, fuentes y guarda de geometria."""

from __future__ import annotations

import pytest

from habitalens import DISCLAIMER
from habitalens.report.manifest import assert_no_geometry_keys, build_manifest
from tests.conftest import make_report_manifest


def test_manifest_schema_and_sources(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c07", "g0c01"})
    assert manifest["schema_version"] == "1"
    assert manifest["report_id"] == "test-report"
    assert manifest["disclaimer"] == DISCLAIMER
    assert manifest["properties"]
    sources = {source["source"] for source in manifest["sources"]}
    assert sources == {"siu", "ncse02", "btn"}
    for source in manifest["sources"]:
        assert source["source_version"]
        assert source["attribution"]


def test_manifest_findings_have_status_and_crs(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c07"})
    for entry in manifest["properties"]:
        assert entry["source_crs"].startswith("EPSG:")
        assert entry["operational_crs"].startswith("EPSG:")
        assert entry["findings"]
        for finding in entry["findings"]:
            assert finding["status"] in {"observed", "derived", "unavailable", "inconclusive"}
            assert "provenance_id" in finding


def test_manifest_rejects_geometry_keys() -> None:
    with pytest.raises(ValueError):
        assert_no_geometry_keys({"properties": [{"geometry": "POINT(0 0)"}]})
    with pytest.raises(ValueError):
        assert_no_geometry_keys({"coordinates": [1, 2]})


def test_build_manifest_requires_generated_at() -> None:
    manifest = build_manifest(report_id="x", entries=[], generated_at="2026-01-01T00:00:00Z")
    assert manifest["generated_at"] == "2026-01-01T00:00:00Z"
    assert manifest["properties"] == []
