from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from aegis_os.release_candidate import (
    RC_NAME,
    ReleaseCandidateError,
    build_external_release_candidate,
)


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    (root / "README.md").write_text("AEGIS\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
    return root


def test_builds_complete_verified_external_release_candidate(tmp_path: Path) -> None:
    result = build_external_release_candidate(
        tmp_path / "out",
        private_key=tmp_path / "secure" / "private.pem",
        public_key=tmp_path / "secure" / "public.pem",
        root=_repository(tmp_path),
        generate_key=True,
    )

    candidate = Path(result.output_directory)
    assert result.status == "verified"
    assert candidate.name == RC_NAME
    assert Path(result.bundle).is_file()
    assert Path(result.attestation).is_file()
    assert Path(result.signature).is_file()
    assert Path(result.public_key).is_file()
    assert Path(result.trust_policy).is_file()
    assert Path(result.transparency_ledger).is_file()
    assert Path(result.trust_report).is_file()
    assert Path(result.acceptance_report).is_file()
    assert (candidate / "RELEASE_CANDIDATE_MANIFEST.json").is_file()


def test_private_key_is_never_published(tmp_path: Path) -> None:
    private_key = tmp_path / "secure" / "private.pem"
    result = build_external_release_candidate(
        tmp_path / "out",
        private_key=private_key,
        public_key=tmp_path / "secure" / "public.pem",
        root=_repository(tmp_path),
        generate_key=True,
    )

    candidate = Path(result.output_directory)
    assert private_key.is_file()
    assert not any("private" in path.name.lower() for path in candidate.rglob("*"))


def test_manifest_binds_provenance_and_bounded_claims(tmp_path: Path) -> None:
    result = build_external_release_candidate(
        tmp_path / "out",
        private_key=tmp_path / "private.pem",
        public_key=tmp_path / "public.pem",
        root=_repository(tmp_path),
        generate_key=True,
    )

    manifest = json.loads(
        (Path(result.output_directory) / "RELEASE_CANDIDATE_MANIFEST.json").read_text()
    )
    assert manifest["source_commit"]
    assert manifest["source_tree"]
    assert manifest["bundle_sha256"]
    assert manifest["execution_mode"] == "deterministic simulation only"
    assert manifest["real_world_effects_verified"] is False


def test_refuses_missing_signing_key_without_generation(tmp_path: Path) -> None:
    with pytest.raises(ReleaseCandidateError, match="key pair is required"):
        build_external_release_candidate(
            tmp_path / "out",
            private_key=tmp_path / "missing-private.pem",
            public_key=tmp_path / "missing-public.pem",
            root=_repository(tmp_path),
        )


def test_refuses_to_overwrite_existing_candidate(tmp_path: Path) -> None:
    output = tmp_path / "out"
    root = _repository(tmp_path)
    build_external_release_candidate(
        output,
        private_key=tmp_path / "private.pem",
        public_key=tmp_path / "public.pem",
        root=root,
        generate_key=True,
    )

    with pytest.raises(ReleaseCandidateError, match="Refusing to overwrite"):
        build_external_release_candidate(
            output,
            private_key=tmp_path / "private.pem",
            public_key=tmp_path / "public.pem",
            root=root,
        )
