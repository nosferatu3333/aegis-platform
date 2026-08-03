"""Executable Domain F functional proof scenarios.

Domain F verifies release integrity and publisher trust for the preserved
AEGIS Platform 1.7.0 RC1 distribution.

S19 reads the official outer release ZIP, extracts it only into temporary
storage, and uses the production distribution, attestation, trust-policy,
transparency, and trust-report verifiers. It does not sign, rebuild, publish,
or modify a release.

S20 creates a temporary copy of the signed inner distribution and changes one
payload file while leaving the original attestation, signature, policy, and
ledger untouched. The production verifiers must reject the modified copy.
The official release and preserved evidence remain unchanged.

A valid result proves integrity and publisher provenance within the published
trust policy. It does not prove broad software safety, production readiness,
real-world effects, or absence of undiscovered defects.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Iterable

SUITE_VERSION = "1.0"
RELEASE_VERSION = "1.7.0-rc1"
DOMAIN = "F"
OVERALL_PASS_VERDICT = "DOMAIN F FUNCTIONALLY VERIFIED"
SINGLE_PASS_VERDICT = "SCENARIO FUNCTIONALLY VERIFIED"


class DomainFProofError(RuntimeError):
    """Raised when the preserved RC1 proof input is missing or ambiguous."""


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _definition_path() -> Path:
    return Path(__file__).resolve().parent / "scenarios" / "domain_f.json"


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _serialize(value: Any) -> Any:
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _serialize(value.to_dict())
    if is_dataclass(value) and not isinstance(value, type):
        return _serialize(asdict(value))
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def load_domain_f_definition() -> dict[str, Any]:
    payload = json.loads(_definition_path().read_text(encoding="utf-8-sig"))
    identifiers = [item["scenario_id"] for item in payload["scenarios"]]
    expected = {"AEGIS-RC1-S19", "AEGIS-RC1-S20"}
    if set(identifiers) != expected:
        raise ValueError("Domain F must define exactly S19 and S20.")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Domain F scenario identifiers must be unique.")

    profile = payload.get("expected_release_profile")
    required = {
        "outer_sha256",
        "bundle_sha256",
        "bundle_size",
        "platform_version",
        "source_branch",
        "source_commit",
        "source_tree",
        "signer_key_id",
        "verified_files",
    }
    if not isinstance(profile, dict) or set(profile) != required:
        raise ValueError(
            "Domain F expected_release_profile must define the exact RC1 identity."
        )
    return payload


def _resolve_release_zip(explicit: Path | None = None) -> Path:
    if explicit is not None:
        candidate = explicit
    else:
        configured = os.environ.get("AEGIS_RC1_RELEASE_PATH", "").strip()
        if not configured:
            raise DomainFProofError(
                "AEGIS_RC1_RELEASE_PATH is required for Domain F proof."
            )
        candidate = Path(configured)

    candidate = candidate.expanduser().resolve()
    if not candidate.is_file():
        raise DomainFProofError(f"Official RC1 release ZIP does not exist: {candidate}")
    return candidate


def _base(definition: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "suite_version": SUITE_VERSION,
        "release_version": RELEASE_VERSION,
        "domain": DOMAIN,
        "scenario_id": definition["scenario_id"],
        "title": definition["title"],
        "expected_canonical_outcome": definition[
            "expected_canonical_outcome"
        ],
        "actual_canonical_outcome": None,
        "started_at": _utc_now(),
        "completed_at": None,
        "passed": False,
        "assertions": [],
        "evidence": {},
        "failure_reason": None,
        "execution_requested": False,
        "execution_performed": False,
        "declared_boundary": {
            "verification_only": True,
            "private_signing_material_accessed": False,
            "signing_operation_performed": False,
            "release_build_performed": False,
            "official_release_modified": False,
            "temporary_tampering_only": definition["scenario_id"]
            == "AEGIS-RC1-S20",
            "real_world_effects_verified": False,
            "production_readiness_claimed": False,
            "absence_of_undiscovered_defects_claimed": False,
        },
    }


def _check(
    result: dict[str, Any],
    name: str,
    condition: bool,
    detail: str,
) -> None:
    result["assertions"].append(
        {
            "name": name,
            "passed": bool(condition),
            "detail": detail,
        }
    )


def _finish(result: dict[str, Any]) -> dict[str, Any]:
    result["passed"] = bool(result["assertions"]) and all(
        item["passed"] for item in result["assertions"]
    )
    if not result["passed"]:
        failed = [
            item["name"]
            for item in result["assertions"]
            if not item["passed"]
        ]
        result["failure_reason"] = "Failed assertions: " + ", ".join(failed)
    result["completed_at"] = _utc_now()
    return result


def _safe_extract(archive_path: Path, output_directory: Path) -> None:
    output_root = output_directory.resolve()
    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            destination = (output_root / member.filename).resolve()
            try:
                destination.relative_to(output_root)
            except ValueError as error:
                raise DomainFProofError(
                    f"Unsafe release archive path: {member.filename}"
                ) from error
        archive.extractall(output_root)


def _unique_named_file(root: Path, name: str) -> Path:
    matches = [path for path in root.rglob(name) if path.is_file()]
    if len(matches) != 1:
        raise DomainFProofError(
            f"Expected exactly one {name} in release; found {len(matches)}."
        )
    return matches[0]


def _locate_candidate(root: Path) -> dict[str, Path]:
    names = {
        "manifest": "RELEASE_CANDIDATE_MANIFEST.json",
        "bundle": "aegis-platform-1.7.0.zip",
        "attestation": "aegis-platform-1.7.0.zip.attestation.json",
        "signature": "aegis-platform-1.7.0.zip.attestation.sig",
        "public_key": "aegis-release-public.pem",
        "trust_policy": "aegis-signing-trust-policy.json",
        "transparency_ledger": "release-transparency.jsonl",
        "trust_report": "TRUST_REPORT.json",
        "acceptance_report": "ACCEPTANCE_REPORT.json",
    }
    artifacts = {
        key: _unique_named_file(root, filename)
        for key, filename in names.items()
    }
    parents = {path.parent.resolve() for path in artifacts.values()}
    if len(parents) != 1:
        raise DomainFProofError(
            "Release candidate artifacts do not share one candidate directory."
        )
    artifacts["candidate_directory"] = next(iter(parents))
    return artifacts


def _candidate_inventory(candidate_directory: Path) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(candidate_directory).as_posix(),
            "size": path.stat().st_size,
            "sha256": _sha256_file(path),
        }
        for path in sorted(candidate_directory.rglob("*"))
        if path.is_file()
    ]


def _private_material_names(candidate_directory: Path) -> list[str]:
    prohibited: list[str] = []
    for path in candidate_directory.rglob("*"):
        if not path.is_file():
            continue
        name = path.name.lower()
        if "private" in name or "secret" in name or name.endswith(".key"):
            prohibited.append(path.relative_to(candidate_directory).as_posix())
    return sorted(prohibited)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DomainFProofError(f"Expected a JSON object: {path.name}")
    return payload


def _verification_snapshot(
    artifacts: dict[str, Path],
) -> dict[str, Any]:
    from aegis_os.attestation import (
        public_key_id,
        verify_distribution_attestation,
    )
    from aegis_os.distribution import verify_distribution_bundle
    from aegis_os.transparency import (
        build_trust_report,
        verify_transparency_ledger,
    )
    from aegis_os.trust import (
        load_trust_policy,
        verify_attestation_with_trust_policy,
    )
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey,
    )

    bundle = artifacts["bundle"]
    attestation = artifacts["attestation"]
    signature = artifacts["signature"]
    public_key_path = artifacts["public_key"]
    policy_path = artifacts["trust_policy"]
    ledger_path = artifacts["transparency_ledger"]

    distribution = verify_distribution_bundle(bundle)
    attestation_verification = verify_distribution_attestation(
        bundle,
        attestation,
        signature,
        public_key_path,
    )
    trusted_attestation = verify_attestation_with_trust_policy(
        bundle,
        attestation,
        signature,
        policy_path,
    )
    transparency = verify_transparency_ledger(ledger_path)
    trust_report = build_trust_report(
        bundle,
        attestation,
        signature,
        policy_path,
        ledger_path,
    )
    policy = load_trust_policy(policy_path)
    loaded_public = serialization.load_pem_public_key(
        public_key_path.read_bytes()
    )
    if not isinstance(loaded_public, Ed25519PublicKey):
        raise DomainFProofError("Published release key is not Ed25519.")

    return {
        "distribution": distribution,
        "attestation_verification": attestation_verification,
        "trusted_attestation": trusted_attestation,
        "transparency": transparency,
        "trust_report": trust_report,
        "trust_policy": policy,
        "published_public_key_id": public_key_id(loaded_public),
    }


def _scenario_s19(
    definition: dict[str, Any],
    release_zip: Path,
    expected: dict[str, Any],
) -> dict[str, Any]:
    result = _base(definition)
    outer_before = _sha256_file(release_zip)

    with tempfile.TemporaryDirectory(prefix="aegis-domain-f-s19-") as temp:
        extraction_root = Path(temp) / "release"
        extraction_root.mkdir(parents=True, exist_ok=False)
        _safe_extract(release_zip, extraction_root)
        artifacts = _locate_candidate(extraction_root)
        candidate_directory = artifacts["candidate_directory"]

        manifest = _read_json(artifacts["manifest"])
        attestation_data = _read_json(artifacts["attestation"])
        stored_trust_report = _read_json(artifacts["trust_report"])
        acceptance = _read_json(artifacts["acceptance_report"])
        snapshot = _verification_snapshot(artifacts)
        inventory = _candidate_inventory(candidate_directory)
        prohibited_names = _private_material_names(candidate_directory)

        distribution = snapshot["distribution"]
        attestation_verification = snapshot["attestation_verification"]
        trusted_attestation = snapshot["trusted_attestation"]
        transparency = snapshot["transparency"]
        trust_report = snapshot["trust_report"]
        policy = snapshot["trust_policy"]
        bundle_hash = _sha256_file(artifacts["bundle"])

        result["actual_canonical_outcome"] = (
            "signed_rc1_verified"
            if (
                outer_before == expected["outer_sha256"]
                and distribution.status == "verified"
                and attestation_verification.status == "verified"
                and trusted_attestation.status == "verified"
                and transparency.status == "verified"
                and trust_report.overall_verdict == "TRUSTED"
            )
            else "release_trust_not_established"
        )
        result["evidence"] = {
            "official_release_path": str(release_zip),
            "official_outer_sha256": outer_before,
            "candidate_directory_name": candidate_directory.name,
            "candidate_inventory": inventory,
            "candidate_file_count": len(inventory),
            "prohibited_private_material_names": prohibited_names,
            "manifest": manifest,
            "attestation": attestation_data,
            "stored_trust_report": stored_trust_report,
            "acceptance_report": acceptance,
            "bundle_sha256": bundle_hash,
            "bundle_size": artifacts["bundle"].stat().st_size,
            "published_public_key_id": snapshot[
                "published_public_key_id"
            ],
            "distribution_verification": _serialize(distribution),
            "attestation_verification": _serialize(
                attestation_verification
            ),
            "trusted_attestation_verification": _serialize(
                trusted_attestation
            ),
            "transparency_verification": _serialize(transparency),
            "recomputed_trust_report": _serialize(trust_report),
            "trust_policy": _serialize(policy),
            "manifest_paths_rebound_to_extracted_artifacts": True,
            "private_signing_material_accessed": False,
            "signing_operation_performed": False,
            "release_build_performed": False,
            "official_release_modified": False,
        }

        _check(
            result,
            "official_outer_release_identity_matches",
            outer_before == expected["outer_sha256"],
            f"Outer SHA-256: {outer_before}",
        )
        _check(
            result,
            "complete_public_release_artifact_set_present",
            len(inventory) == 9
            and {item["path"] for item in inventory}
            == {
                "ACCEPTANCE_REPORT.json",
                "RELEASE_CANDIDATE_MANIFEST.json",
                "TRUST_REPORT.json",
                "aegis-platform-1.7.0.zip",
                "aegis-platform-1.7.0.zip.attestation.json",
                "aegis-platform-1.7.0.zip.attestation.sig",
                "aegis-release-public.pem",
                "aegis-signing-trust-policy.json",
                "release-transparency.jsonl",
            },
            f"Candidate files: {[item['path'] for item in inventory]}",
        )
        _check(
            result,
            "private_signing_material_not_published",
            prohibited_names == [],
            f"Prohibited names: {prohibited_names}",
        )
        _check(
            result,
            "release_manifest_binds_expected_identity",
            manifest.get("status") == "verified"
            and manifest.get("platform_version")
            == expected["platform_version"]
            and manifest.get("bundle_sha256")
            == expected["bundle_sha256"]
            and manifest.get("source_branch")
            == expected["source_branch"]
            and manifest.get("source_commit")
            == expected["source_commit"]
            and manifest.get("source_tree") == expected["source_tree"]
            and manifest.get("signer_key_id")
            == expected["signer_key_id"]
            and manifest.get("verified_files")
            == expected["verified_files"],
            json.dumps(manifest, sort_keys=True),
        )
        _check(
            result,
            "signed_bundle_identity_matches",
            bundle_hash == expected["bundle_sha256"]
            and artifacts["bundle"].stat().st_size
            == expected["bundle_size"],
            (
                f"Bundle SHA-256: {bundle_hash}; "
                f"size: {artifacts['bundle'].stat().st_size}"
            ),
        )
        _check(
            result,
            "embedded_distribution_inventory_verified",
            distribution.status == "verified"
            and distribution.verified_files == expected["verified_files"]
            and distribution.platform_version
            == expected["platform_version"]
            and distribution.source_branch == expected["source_branch"]
            and distribution.source_commit == expected["source_commit"]
            and distribution.source_tree == expected["source_tree"]
            and not distribution.errors,
            json.dumps(_serialize(distribution), sort_keys=True),
        )
        _check(
            result,
            "detached_signature_and_attestation_verified",
            attestation_verification.status == "verified"
            and attestation_verification.signer_key_id
            == expected["signer_key_id"]
            and attestation_verification.bundle_sha256
            == expected["bundle_sha256"]
            and not attestation_verification.errors,
            json.dumps(
                _serialize(attestation_verification), sort_keys=True
            ),
        )
        _check(
            result,
            "published_key_matches_attestation_and_policy",
            snapshot["published_public_key_id"]
            == expected["signer_key_id"]
            and policy.policy_version == 1
            and len(policy.keys) == 1
            and policy.keys[0].key_id == expected["signer_key_id"]
            and policy.keys[0].state.value == "active",
            (
                f"Published key: {snapshot['published_public_key_id']}; "
                f"policy version: {policy.policy_version}"
            ),
        )
        _check(
            result,
            "trust_policy_verification_succeeds",
            trusted_attestation.status == "verified"
            and trusted_attestation.key_state == "active"
            and trusted_attestation.policy_version == 1
            and trusted_attestation.cryptographic_status == "verified"
            and not trusted_attestation.errors,
            json.dumps(_serialize(trusted_attestation), sort_keys=True),
        )
        _check(
            result,
            "transparency_ledger_verified",
            transparency.status == "verified"
            and transparency.event_count == 1
            and bool(transparency.head_hash)
            and not transparency.errors,
            json.dumps(_serialize(transparency), sort_keys=True),
        )
        _check(
            result,
            "recomputed_trust_report_is_trusted",
            trust_report.overall_verdict == "TRUSTED"
            and trust_report.release_integrity == "verified"
            and trust_report.signature == "verified"
            and trust_report.signer == expected["signer_key_id"]
            and trust_report.signing_key_state == "active"
            and trust_report.attestation == "verified"
            and trust_report.transparency == "verified"
            and trust_report.policy_version == 1
            and trust_report.source_commit == expected["source_commit"]
            and not trust_report.reasons,
            json.dumps(_serialize(trust_report), sort_keys=True),
        )
        _check(
            result,
            "published_trust_report_matches_recomputation",
            stored_trust_report == _serialize(trust_report),
            (
                "Stored and recomputed trust reports are "
                f"equal: {stored_trust_report == _serialize(trust_report)}"
            ),
        )
        _check(
            result,
            "acceptance_claims_remain_bounded",
            acceptance.get("accepted") is True
            and acceptance.get("scenario_count") == 5
            and acceptance.get("execution_mode")
            == "deterministic simulation only"
            and acceptance.get("real_world_effects_verified") is False
            and all(
                item.get("passed") is True
                for item in acceptance.get("scenarios", [])
            ),
            json.dumps(acceptance, sort_keys=True),
        )
        _check(
            result,
            "verification_performed_without_signing_or_execution",
            result["execution_performed"] is False
            and result["evidence"]["private_signing_material_accessed"]
            is False
            and result["evidence"]["signing_operation_performed"] is False
            and result["evidence"]["release_build_performed"] is False,
            "S19 is read-only verification of published public artifacts.",
        )

    outer_after = _sha256_file(release_zip)
    result["evidence"]["official_outer_sha256_after"] = outer_after
    result["evidence"]["official_release_modified"] = outer_after != outer_before
    _check(
        result,
        "official_release_remains_unchanged",
        outer_after == outer_before == expected["outer_sha256"],
        f"Before: {outer_before}; after: {outer_after}",
    )
    return _finish(result)


def _tamper_bundle(
    source_bundle: Path,
    target_bundle: Path,
) -> tuple[str, str, str]:
    with zipfile.ZipFile(source_bundle) as source:
        manifest = json.loads(
            source.read("aegis-platform/DISTRIBUTION_MANIFEST.json")
        )
        entries = manifest.get("files", [])
        if not entries:
            raise DomainFProofError(
                "Distribution manifest contains no payload files to test."
            )
        target_path = str(entries[0]["path"])
        before_payload = source.read(target_path)

        with zipfile.ZipFile(target_bundle, "w") as target:
            for info in source.infolist():
                payload = source.read(info.filename)
                if info.filename == target_path:
                    payload += b"\nAEGIS-DOMAIN-F-CONTROLLED-TAMPER\n"
                target.writestr(info, payload)

    after_payload: bytes
    with zipfile.ZipFile(target_bundle) as tampered:
        after_payload = tampered.read(target_path)
    return (
        target_path,
        hashlib.sha256(before_payload).hexdigest(),
        hashlib.sha256(after_payload).hexdigest(),
    )


def _scenario_s20(
    definition: dict[str, Any],
    release_zip: Path,
    expected: dict[str, Any],
) -> dict[str, Any]:
    result = _base(definition)
    outer_before = _sha256_file(release_zip)

    with tempfile.TemporaryDirectory(prefix="aegis-domain-f-s20-") as temp:
        temp_root = Path(temp)
        extraction_root = temp_root / "release"
        extraction_root.mkdir(parents=True, exist_ok=False)
        _safe_extract(release_zip, extraction_root)
        artifacts = _locate_candidate(extraction_root)
        original_bundle = artifacts["bundle"]
        original_bundle_before = _sha256_file(original_bundle)

        tampered_bundle = temp_root / "controlled-tampered-distribution.zip"
        target_path, payload_hash_before, payload_hash_after = _tamper_bundle(
            original_bundle,
            tampered_bundle,
        )

        tampered_artifacts = dict(artifacts)
        tampered_artifacts["bundle"] = tampered_bundle
        snapshot = _verification_snapshot(tampered_artifacts)

        distribution = snapshot["distribution"]
        attestation_verification = snapshot["attestation_verification"]
        trusted_attestation = snapshot["trusted_attestation"]
        transparency = snapshot["transparency"]
        trust_report = snapshot["trust_report"]
        tampered_hash = _sha256_file(tampered_bundle)
        original_bundle_after = _sha256_file(original_bundle)

        rejection_signals = {
            "distribution_invalid": distribution.status == "invalid",
            "attestation_invalid": attestation_verification.status
            == "invalid",
            "trusted_attestation_invalid": trusted_attestation.status
            == "invalid",
            "trust_report_rejected": trust_report.overall_verdict
            == "REJECTED",
        }
        result["actual_canonical_outcome"] = (
            "tampered_distribution_rejected"
            if all(rejection_signals.values())
            else "tampered_distribution_not_fully_rejected"
        )
        result["evidence"] = {
            "official_release_path": str(release_zip),
            "official_outer_sha256": outer_before,
            "original_bundle_sha256_before": original_bundle_before,
            "original_bundle_sha256_after": original_bundle_after,
            "tampered_copy_filename": tampered_bundle.name,
            "tampered_copy_sha256": tampered_hash,
            "tampered_payload_path": target_path,
            "tampered_payload_sha256_before": payload_hash_before,
            "tampered_payload_sha256_after": payload_hash_after,
            "temporary_copy_only": True,
            "temporary_copy_exists_during_verification": (
                tampered_bundle.is_file()
            ),
            "distribution_verification": _serialize(distribution),
            "attestation_verification": _serialize(
                attestation_verification
            ),
            "trusted_attestation_verification": _serialize(
                trusted_attestation
            ),
            "transparency_verification": _serialize(transparency),
            "recomputed_trust_report": _serialize(trust_report),
            "rejection_signals": rejection_signals,
            "private_signing_material_accessed": False,
            "signing_operation_performed": False,
            "release_build_performed": False,
            "official_release_modified": False,
        }

        _check(
            result,
            "official_outer_release_identity_matches",
            outer_before == expected["outer_sha256"],
            f"Outer SHA-256: {outer_before}",
        )
        _check(
            result,
            "controlled_copy_is_materially_changed",
            tampered_hash != original_bundle_before
            and payload_hash_after != payload_hash_before,
            (
                f"Original bundle: {original_bundle_before}; "
                f"tampered copy: {tampered_hash}"
            ),
        )
        _check(
            result,
            "embedded_distribution_verifier_rejects_tampering",
            distribution.status == "invalid"
            and any(
                target_path in error
                for error in distribution.errors
            ),
            json.dumps(_serialize(distribution), sort_keys=True),
        )
        _check(
            result,
            "detached_attestation_rejects_changed_bundle",
            attestation_verification.status == "invalid"
            and any(
                error in {"bundle-sha256", "bundle-size"}
                for error in attestation_verification.errors
            ),
            json.dumps(
                _serialize(attestation_verification), sort_keys=True
            ),
        )
        _check(
            result,
            "trust_policy_verifier_fails_closed",
            trusted_attestation.status == "invalid"
            and trusted_attestation.cryptographic_status == "invalid"
            and bool(trusted_attestation.errors),
            json.dumps(_serialize(trusted_attestation), sort_keys=True),
        )
        _check(
            result,
            "composed_trust_report_rejects_tampered_copy",
            trust_report.overall_verdict == "REJECTED"
            and trust_report.release_integrity == "invalid"
            and trust_report.signature == "invalid"
            and trust_report.attestation == "invalid"
            and bool(trust_report.reasons),
            json.dumps(_serialize(trust_report), sort_keys=True),
        )
        _check(
            result,
            "unchanged_transparency_does_not_override_rejection",
            transparency.status == "verified"
            and trust_report.transparency == "verified"
            and trust_report.overall_verdict == "REJECTED",
            (
                f"Transparency: {transparency.status}; "
                f"overall: {trust_report.overall_verdict}"
            ),
        )
        _check(
            result,
            "original_signed_bundle_remains_unchanged",
            original_bundle_before
            == original_bundle_after
            == expected["bundle_sha256"],
            (
                f"Original before: {original_bundle_before}; "
                f"after: {original_bundle_after}"
            ),
        )
        _check(
            result,
            "tampering_is_temporary_and_non_signing",
            result["execution_performed"] is False
            and result["evidence"]["temporary_copy_only"] is True
            and result["evidence"]["private_signing_material_accessed"]
            is False
            and result["evidence"]["signing_operation_performed"] is False
            and result["evidence"]["release_build_performed"] is False,
            "S20 modifies only an ephemeral copy and performs no signing.",
        )

    result["evidence"]["temporary_copy_exists_after_cleanup"] = False
    outer_after = _sha256_file(release_zip)
    result["evidence"]["official_outer_sha256_after"] = outer_after
    result["evidence"]["official_release_modified"] = outer_after != outer_before
    _check(
        result,
        "official_release_remains_unchanged",
        outer_after == outer_before == expected["outer_sha256"],
        f"Before: {outer_before}; after: {outer_after}",
    )
    return _finish(result)


ScenarioRunner = Callable[
    [dict[str, Any], Path, dict[str, Any]],
    dict[str, Any],
]

SCENARIO_RUNNERS: dict[str, ScenarioRunner] = {
    "AEGIS-RC1-S19": _scenario_s19,
    "AEGIS-RC1-S20": _scenario_s20,
}


def _selected_definitions(
    payload: dict[str, Any],
    scenario_id: str | None,
) -> Iterable[dict[str, Any]]:
    if scenario_id is None:
        return payload["scenarios"]
    selected = [
        item
        for item in payload["scenarios"]
        if item["scenario_id"] == scenario_id
    ]
    if not selected:
        raise ValueError(f"Unknown Domain F scenario: {scenario_id}")
    return selected


def run_domain_f(
    *,
    scenario_id: str | None = None,
    output_root: Path | None = None,
    release_zip: Path | None = None,
) -> tuple[dict[str, Any], Path]:
    payload = load_domain_f_definition()
    started_at = _utc_now()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = (
        Path(output_root)
        if output_root is not None
        else _root()
        / "artifacts"
        / "functional-proof"
        / "domain-f"
    )
    directory = root / stamp
    suffix = 1
    while directory.exists():
        directory = root / f"{stamp}-{suffix}"
        suffix += 1
    directory.mkdir(parents=True, exist_ok=False)

    expected = payload["expected_release_profile"]
    resolved_release: Path | None = None
    release_resolution_error: Exception | None = None
    try:
        resolved_release = _resolve_release_zip(release_zip)
    except Exception as error:
        release_resolution_error = error

    results: list[dict[str, Any]] = []
    for definition in _selected_definitions(payload, scenario_id):
        try:
            if release_resolution_error is not None:
                raise release_resolution_error
            if resolved_release is None:
                raise DomainFProofError("Official release path was not resolved.")
            scenario_result = SCENARIO_RUNNERS[
                definition["scenario_id"]
            ](definition, resolved_release, expected)
        except Exception as error:
            scenario_result = _base(definition)
            scenario_result["actual_canonical_outcome"] = "blocked"
            scenario_result["failure_reason"] = (
                f"{type(error).__name__}: {error}"
            )
            scenario_result["completed_at"] = _utc_now()

        (directory / f"{definition['scenario_id']}.json").write_text(
            json.dumps(
                scenario_result,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        results.append(scenario_result)

    passed = sum(1 for item in results if item["passed"])
    blocked = sum(
        1
        for item in results
        if item["actual_canonical_outcome"] == "blocked"
    )
    failed = len(results) - passed - blocked
    all_passed = passed == len(results) and failed == 0 and blocked == 0

    aggregate = {
        "schema_version": "1.0",
        "suite_version": SUITE_VERSION,
        "release_version": RELEASE_VERSION,
        "domain": DOMAIN,
        "domain_title": payload["domain_title"],
        "started_at": started_at,
        "completed_at": _utc_now(),
        "scenarios_executed": len(results),
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "scenario_summaries": [
            {
                "scenario_id": item["scenario_id"],
                "actual_canonical_outcome": item[
                    "actual_canonical_outcome"
                ],
                "passed": item["passed"],
                "failure_reason": item["failure_reason"],
            }
            for item in results
        ],
        "overall_domain_verdict": (
            (
                OVERALL_PASS_VERDICT
                if scenario_id is None
                else SINGLE_PASS_VERDICT
            )
            if all_passed
            else "DOMAIN F VERIFICATION FAILED"
        ),
        "repository_commit": _git_value("rev-parse", "HEAD"),
        "repository_tree": _git_value("rev-parse", "HEAD^{tree}"),
        "official_release_path": (
            str(resolved_release) if resolved_release is not None else None
        ),
        "expected_release_profile": expected,
        "generated_output_is_signed_release": False,
        "private_signing_material_included": False,
        "private_signing_material_accessed": False,
        "signing_operation_performed": False,
        "official_release_modified": False,
        "declared_boundary": payload["declared_boundary"],
    }

    (directory / "DOMAIN_F_REPORT.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "============================================================",
        "AEGIS DOMAIN F FUNCTIONAL PROOF",
        "============================================================",
        f"Scenarios executed: {aggregate['scenarios_executed']}",
        f"Passed: {passed}",
        f"Failed: {failed}",
        f"Blocked: {blocked}",
        f"Verdict: {aggregate['overall_domain_verdict']}",
        f"Evidence: {directory}",
        "",
    ]
    for item in results:
        marker = "PASS" if item["passed"] else "FAIL"
        lines.append(
            f"[{marker}] {item['scenario_id']} - "
            f"{item['actual_canonical_outcome']}"
        )

    (directory / "DOMAIN_F_SUMMARY.txt").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return aggregate, directory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run AEGIS RC1 Domain F functional proofs."
    )
    parser.add_argument(
        "--scenario",
        choices=sorted(SCENARIO_RUNNERS),
    )
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--release-zip", type=Path)
    args = parser.parse_args(argv)
    aggregate, directory = run_domain_f(
        scenario_id=args.scenario,
        output_root=args.output_root,
        release_zip=args.release_zip,
    )
    print("============================================================")
    print("AEGIS DOMAIN F FUNCTIONAL PROOF")
    print("============================================================")
    print(f"Scenarios executed: {aggregate['scenarios_executed']}")
    print(f"Passed: {aggregate['passed']}")
    print(f"Failed: {aggregate['failed']}")
    print(f"Blocked: {aggregate['blocked']}")
    print(f"Verdict: {aggregate['overall_domain_verdict']}")
    print(f"Evidence: {directory}")
    return (
        0
        if aggregate["passed"] == aggregate["scenarios_executed"]
        and aggregate["failed"] == 0
        and aggregate["blocked"] == 0
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
