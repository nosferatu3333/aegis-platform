"""Tests for AEGIS RC1 Domain F functional proof."""

from __future__ import annotations

import hashlib
import json
import os
import zipfile
from pathlib import Path

import pytest

from aegis_os.proof.domain_f import (
    OVERALL_PASS_VERDICT,
    SINGLE_PASS_VERDICT,
    DomainFProofError,
    _safe_extract,
    load_domain_f_definition,
    run_domain_f,
)

EXPECTED_IDS = {
    "AEGIS-RC1-S19",
    "AEGIS-RC1-S20",
}


def _official_release() -> Path:
    configured = os.environ.get("AEGIS_RC1_RELEASE_PATH", "").strip()
    if not configured:
        pytest.fail("AEGIS_RC1_RELEASE_PATH is required for Domain F tests.")
    path = Path(configured).expanduser().resolve()
    if not path.is_file():
        pytest.fail(f"Official RC1 release ZIP is missing: {path}")
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _result(directory: Path, scenario_id: str) -> dict:
    return json.loads(
        (directory / f"{scenario_id}.json").read_text(encoding="utf-8")
    )



def test_safe_extract_normalizes_windows_paths_and_rejects_traversal(
    tmp_path: Path,
):
    archive_path = tmp_path / "windows-paths.zip"

    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            r"candidate\RELEASE_CANDIDATE_MANIFEST.json",
            "{}",
        )

    output = tmp_path / "normalized"
    output.mkdir()

    _safe_extract(archive_path, output)

    manifest = (
        output
        / "candidate"
        / "RELEASE_CANDIDATE_MANIFEST.json"
    )

    assert manifest.is_file()
    assert manifest.read_text(encoding="utf-8") == "{}"

    unsafe_archive = tmp_path / "unsafe.zip"

    with zipfile.ZipFile(
        unsafe_archive,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        archive.writestr(
            r"..\outside.txt",
            "must-not-escape",
        )

    unsafe_output = tmp_path / "unsafe-output"
    unsafe_output.mkdir()

    with pytest.raises(
        DomainFProofError,
        match="Unsafe release archive path",
    ):
        _safe_extract(
            unsafe_archive,
            unsafe_output,
        )

    assert not (tmp_path / "outside.txt").exists()

def test_definitions_are_complete_unique_and_bound_to_exact_rc1():
    payload = load_domain_f_definition()
    identifiers = [item["scenario_id"] for item in payload["scenarios"]]
    profile = payload["expected_release_profile"]

    assert set(identifiers) == EXPECTED_IDS
    assert len(identifiers) == len(set(identifiers))
    assert profile["platform_version"] == "1.7.0"
    assert len(profile["outer_sha256"]) == 64
    assert len(profile["bundle_sha256"]) == 64
    assert profile["verified_files"] == 262


@pytest.mark.parametrize("scenario_id", sorted(EXPECTED_IDS))
def test_each_scenario_passes(scenario_id: str, tmp_path: Path):
    aggregate, directory = run_domain_f(
        scenario_id=scenario_id,
        output_root=tmp_path,
        release_zip=_official_release(),
    )
    assert aggregate["scenarios_executed"] == 1
    assert aggregate["passed"] == 1
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == SINGLE_PASS_VERDICT
    result = _result(directory, scenario_id)
    assert result["passed"] is True
    assert all(item["passed"] for item in result["assertions"])


def test_s19_verifies_official_signed_rc1_with_public_material_only(
    tmp_path: Path,
):
    release = _official_release()
    before = _sha256(release)
    _, directory = run_domain_f(
        scenario_id="AEGIS-RC1-S19",
        output_root=tmp_path,
        release_zip=release,
    )
    result = _result(directory, "AEGIS-RC1-S19")
    evidence = result["evidence"]

    assert result["actual_canonical_outcome"] == "signed_rc1_verified"
    assert evidence["distribution_verification"]["status"] == "verified"
    assert evidence["attestation_verification"]["status"] == "verified"
    assert (
        evidence["trusted_attestation_verification"]["status"]
        == "verified"
    )
    assert evidence["transparency_verification"]["status"] == "verified"
    assert evidence["recomputed_trust_report"]["overall_verdict"] == "TRUSTED"
    assert evidence["prohibited_private_material_names"] == []
    assert evidence["private_signing_material_accessed"] is False
    assert evidence["signing_operation_performed"] is False
    assert evidence["official_release_modified"] is False
    assert _sha256(release) == before


def test_s20_rejects_temporary_tampered_copy_and_preserves_official(
    tmp_path: Path,
):
    release = _official_release()
    before = _sha256(release)
    _, directory = run_domain_f(
        scenario_id="AEGIS-RC1-S20",
        output_root=tmp_path,
        release_zip=release,
    )
    result = _result(directory, "AEGIS-RC1-S20")
    evidence = result["evidence"]

    assert (
        result["actual_canonical_outcome"]
        == "tampered_distribution_rejected"
    )
    assert evidence["distribution_verification"]["status"] == "invalid"
    assert evidence["attestation_verification"]["status"] == "invalid"
    assert (
        evidence["trusted_attestation_verification"]["status"]
        == "invalid"
    )
    assert evidence["recomputed_trust_report"]["overall_verdict"] == "REJECTED"
    assert evidence["transparency_verification"]["status"] == "verified"
    assert evidence["temporary_copy_only"] is True
    assert evidence["temporary_copy_exists_after_cleanup"] is False
    assert evidence["private_signing_material_accessed"] is False
    assert evidence["signing_operation_performed"] is False
    assert evidence["official_release_modified"] is False
    assert _sha256(release) == before


def test_aggregate_report_passes(tmp_path: Path):
    aggregate, directory = run_domain_f(
        output_root=tmp_path,
        release_zip=_official_release(),
    )
    assert aggregate["scenarios_executed"] == 2
    assert aggregate["passed"] == 2
    assert aggregate["failed"] == 0
    assert aggregate["blocked"] == 0
    assert aggregate["overall_domain_verdict"] == OVERALL_PASS_VERDICT
    assert aggregate["private_signing_material_accessed"] is False
    assert aggregate["signing_operation_performed"] is False
    assert aggregate["official_release_modified"] is False
    assert (directory / "DOMAIN_F_REPORT.json").exists()
    assert (directory / "DOMAIN_F_SUMMARY.txt").exists()


def test_generated_evidence_uses_no_private_material_filenames(tmp_path: Path):
    _, directory = run_domain_f(
        output_root=tmp_path,
        release_zip=_official_release(),
    )
    prohibited = [
        path
        for path in directory.rglob("*")
        if path.is_file()
        and any(
            token in path.name.lower()
            for token in ("private", "secret", "signing-key")
        )
    ]
    assert prohibited == []
