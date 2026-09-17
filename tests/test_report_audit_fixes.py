"""Regresiones de frontera del informe: validacion, hash, staging y limpieza."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import date
from pathlib import Path

import pytest

from habitalens.licensing import (
    LICENSE_FILENAME,
    LicensingNotDeclaredError,
    load_license,
    validate_license,
)
from habitalens.report import generate_report
from habitalens.report.guard import ScoreGuardError
from habitalens.report.manifest import validate_manifest
from tests.conftest import make_report_manifest

ARTIFACT_NAMES = ("report.html", "report.pdf", "provenance_manifest.json")


def _digest(entry: dict) -> tuple:
    return (
        entry["property_id"],
        entry["source_crs"],
        entry["operational_crs"],
        tuple(
            (f["source"], f["kind"], f["method"], tuple(f["inputs"]))
            for f in entry["findings"]
        ),
    )


def test_valid_manifest_passes_boundary_validation(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    assert validate_manifest(manifest) is None


def test_unknown_top_level_key_is_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["extra"] = {}
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_inconsistent_property_identity_is_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["properties"][0]["findings"][0]["property_id"] = "other"
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_duplicate_finding_is_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    findings = manifest["properties"][0]["findings"]
    findings.append(copy.deepcopy(findings[0]))
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_status_value_invariants_are_enforced(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    observed_finding = next(
        f for f in manifest["properties"][0]["findings"] if f["observed"] is not None
    )
    observed_finding["status"] = "unavailable"
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_version_mismatch_is_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["properties"][0]["findings"][0]["source_version"] = "other"
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_missing_inventory_source_is_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["sources"] = manifest["sources"][:1]
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_extra_inventory_source_is_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    first = manifest["sources"][0]
    manifest["sources"].append({**first, "source": "snczi"})
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_generated_at_must_be_timestamp(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["generated_at"] = "not-a-date"
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_disclaimer_must_be_preserved(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["disclaimer"] = "otro texto"
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_partial_artifacts_are_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["artifacts"] = {"html": {"sha256": "0" * 64}}
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_artifact_digest_must_be_sha256(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["artifacts"] = {"html": {"sha256": "nope"}, "pdf": {"canonical_sha256": "0" * 64, "pages": 1, "engine": "fpdf2", "font_stack": "Helvetica"}}
    with pytest.raises(ValueError):
        validate_manifest(manifest)


def test_artifacts_before_first_render_are_optional(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    manifest["artifacts"] = {}
    validate_manifest(manifest)


def test_invalid_manifest_leaves_existing_output_intact(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    out = tmp_path / "out"
    generate_report(manifest, out)
    before = {name: (out / name).read_bytes() for name in ARTIFACT_NAMES}
    broken = copy.deepcopy(manifest)
    broken["properties"][0]["findings"][0]["source_version"] = "other"
    with pytest.raises(ValueError):
        generate_report(broken, out)
    after = {name: (out / name).read_bytes() for name in ARTIFACT_NAMES}
    assert after == before


def test_render_failure_preserves_existing_output_and_cleans_stage(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    out = tmp_path / "out"
    generate_report(manifest, out)
    before = {name: (out / name).read_bytes() for name in ARTIFACT_NAMES}
    broken = copy.deepcopy(manifest)
    broken["properties"][0]["findings"][0]["note"] = "overall_score: 8"
    with pytest.raises(ScoreGuardError):
        generate_report(broken, out)
    after = {name: (out / name).read_bytes() for name in ARTIFACT_NAMES}
    assert after == before
    assert not [p for p in out.parent.iterdir() if p.name.startswith(".habitalens-stage-")]


def test_html_hash_matches_file_bytes(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    artifacts = generate_report(manifest, tmp_path / "out")
    on_disk = hashlib.sha256(artifacts.html_path.read_bytes()).hexdigest()
    assert artifacts.html_sha256 == on_disk
    stored = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))["artifacts"]["html"]["sha256"]
    assert stored == on_disk
    assert artifacts.html_path.read_bytes().count(b"\r\n") == 0


def test_invalid_out_dir_rejected(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    out = tmp_path / "out"
    out.mkdir()
    (out / "report.html").mkdir()
    with pytest.raises(ValueError):
        generate_report(manifest, out)


def test_generated_artifacts_are_consistent(tmp_path) -> None:
    manifest = make_report_manifest(tmp_path, property_ids={"g0c01"})
    artifacts = generate_report(manifest, tmp_path / "out")
    html = artifacts.html_path.read_text(encoding="utf-8")
    assert f"plantilla: {manifest['template_version']}" in html
    entry = manifest["properties"][0]
    for finding in entry["findings"]:
        assert finding["source_version"] in html
        assert "; ".join(finding["inputs"]) in html


def test_license_rejects_null_required_fields() -> None:
    data = {field: None for field in (
        "source_authority", "license_name", "license_url", "verified_on", "applicable_version"
    )}
    with pytest.raises(LicensingNotDeclaredError):
        validate_license(data, Path("LICENSE.yaml"))


def test_license_rejects_wrong_types() -> None:
    data = {
        "source_authority": ["X"],
        "license_name": "Y",
        "license_url": "https://example.com",
        "verified_on": date(2026, 9, 14),
        "applicable_version": "v1",
    }
    with pytest.raises(LicensingNotDeclaredError):
        validate_license(data, Path("LICENSE.yaml"))


def test_license_accepts_date_object_and_preserves_strings(tmp_path) -> None:
    package = tmp_path / "provider"
    package.mkdir()
    (package / LICENSE_FILENAME).write_text(
        'source_authority: "X"\n'
        'license_name: "Y"\n'
        'license_url: "https://example.com"\n'
        'verified_on: 2026-09-14\n'
        'applicable_version: "v1"\n',
        encoding="utf-8",
    )
    declaration = load_license(package)
    assert declaration.verified_on == "2026-09-14"


def test_license_rejects_empty_reuse_conditions(tmp_path) -> None:
    data = {
        "source_authority": "X",
        "license_name": "Y",
        "license_url": "https://example.com",
        "verified_on": "2026-09-14",
        "applicable_version": "v1",
        "reuse_conditions": "   ",
    }
    with pytest.raises(LicensingNotDeclaredError):
        validate_license(data, Path("LICENSE.yaml"))
