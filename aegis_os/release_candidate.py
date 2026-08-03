"""Build a complete, verifiable external AEGIS MVP release candidate."""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from aegis_os.attestation import (
    generate_signing_key,
    public_key_id,
    sign_distribution_bundle,
)
from aegis_os.distribution import build_distribution_bundle, verify_distribution_bundle
from aegis_os.release import PLATFORM_VERSION, REPOSITORY_ROOT
from aegis_os.transparency import append_transparency_event, build_trust_report
from aegis_os.trust import initialize_trust_policy
from cryptography.hazmat.primitives import serialization

from scripts.release_acceptance import run_acceptance

RC_SCHEMA_VERSION = "1.0"
RC_NAME = f"aegis-platform-{PLATFORM_VERSION}-rc1"


class ReleaseCandidateError(RuntimeError):
    """Raised when an external release candidate cannot be assembled."""


@dataclass(frozen=True)
class ReleaseCandidateResult:
    schema_version: str
    status: str
    release_candidate: str
    platform_version: str
    output_directory: str
    bundle: str
    bundle_sha256: str
    attestation: str
    signature: str
    public_key: str
    signer_key_id: str
    trust_policy: str
    transparency_ledger: str
    trust_report: str
    acceptance_report: str
    verified_files: int
    source_commit: str
    source_tree: str
    source_branch: str
    execution_mode: str = "deterministic simulation only"
    real_world_effects_verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _key_id(public_key_path: Path) -> str:
    key = serialization.load_pem_public_key(public_key_path.read_bytes())
    return public_key_id(key)  # type: ignore[arg-type]


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def build_external_release_candidate(
    output_directory: Path,
    *,
    private_key: Path,
    public_key: Path,
    root: Path = REPOSITORY_ROOT,
    generate_key: bool = False,
) -> ReleaseCandidateResult:
    """Build, sign, trust, record, and verify one external MVP release candidate."""

    root = root.resolve()
    output_directory = output_directory.resolve()
    candidate_directory = output_directory / RC_NAME
    if candidate_directory.exists():
        raise ReleaseCandidateError(
            f"Refusing to overwrite existing release candidate: {candidate_directory}"
        )

    if generate_key:
        generate_signing_key(private_key, public_key)
    elif not private_key.is_file() or not public_key.is_file():
        raise ReleaseCandidateError(
            "An existing Ed25519 private/public key pair is required unless --generate-key is used."
        )

    candidate_directory.mkdir(parents=True)
    try:
        bundle = build_distribution_bundle(candidate_directory, root=root)
        distribution = verify_distribution_bundle(bundle)
        if distribution.status != "verified":
            raise ReleaseCandidateError(
                "Distribution verification failed: " + ", ".join(distribution.errors)
            )

        attestation, signature = sign_distribution_bundle(
            bundle, private_key, output_directory=candidate_directory
        )
        published_public_key = candidate_directory / "aegis-release-public.pem"
        shutil.copy2(public_key, published_public_key)

        trust_policy = candidate_directory / "aegis-signing-trust-policy.json"
        initialize_trust_policy(published_public_key, trust_policy)

        ledger = candidate_directory / "release-transparency.jsonl"
        append_transparency_event(
            ledger,
            "release-candidate-published",
            bundle.name,
            {
                "platform_version": PLATFORM_VERSION,
                "bundle_sha256": _sha256(bundle),
                "source_commit": distribution.source_commit,
                "source_tree": distribution.source_tree,
                "source_branch": distribution.source_branch,
                "execution_mode": "deterministic simulation only",
                "real_world_effects_verified": False,
            },
        )

        trust_report = build_trust_report(
            bundle, attestation, signature, trust_policy, ledger
        )
        if trust_report.overall_verdict != "TRUSTED":
            raise ReleaseCandidateError(
                "Release trust verification failed: " + ", ".join(trust_report.reasons)
            )
        trust_report_path = candidate_directory / "TRUST_REPORT.json"
        trust_report_path.write_text(
            trust_report.to_json() + "\n", encoding="utf-8", newline="\n"
        )

        acceptance = run_acceptance()
        if not acceptance["accepted"]:
            raise ReleaseCandidateError("Governed release acceptance scenarios failed.")
        acceptance_path = candidate_directory / "ACCEPTANCE_REPORT.json"
        _write_json(acceptance_path, acceptance)

        result = ReleaseCandidateResult(
            schema_version=RC_SCHEMA_VERSION,
            status="verified",
            release_candidate=RC_NAME,
            platform_version=PLATFORM_VERSION,
            output_directory=str(candidate_directory),
            bundle=str(bundle),
            bundle_sha256=_sha256(bundle),
            attestation=str(attestation),
            signature=str(signature),
            public_key=str(published_public_key),
            signer_key_id=_key_id(published_public_key),
            trust_policy=str(trust_policy),
            transparency_ledger=str(ledger),
            trust_report=str(trust_report_path),
            acceptance_report=str(acceptance_path),
            verified_files=distribution.verified_files,
            source_commit=distribution.source_commit or "unknown",
            source_tree=distribution.source_tree or "unknown",
            source_branch=distribution.source_branch or "unknown",
        )
        manifest_path = candidate_directory / "RELEASE_CANDIDATE_MANIFEST.json"
        _write_json(manifest_path, result.to_dict())
        return result
    except Exception:
        shutil.rmtree(candidate_directory, ignore_errors=True)
        raise
