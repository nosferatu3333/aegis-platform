import json
import subprocess
from pathlib import Path

import pytest

from aegis_os.attestation import (
    AttestationError,
    generate_signing_key,
    sign_distribution_bundle,
    verify_distribution_attestation,
)
from aegis_os.distribution import build_distribution_bundle


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


def test_sign_and_verify_distribution(tmp_path: Path):
    private_key = tmp_path / "release-private.pem"
    public_key = tmp_path / "release-public.pem"
    key_id = generate_signing_key(private_key, public_key)
    bundle = build_distribution_bundle(tmp_path / "dist", root=_repository(tmp_path))
    attestation, signature = sign_distribution_bundle(bundle, private_key)

    result = verify_distribution_attestation(
        bundle, attestation, signature, public_key
    )

    assert result.status == "verified"
    assert result.signer_key_id == key_id
    payload = json.loads(attestation.read_text())
    assert payload["bundle_sha256"] == result.bundle_sha256
    assert payload["source_commit"]
    assert payload["source_tree"]


def test_tampered_bundle_fails_attestation(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    generate_signing_key(private_key, public_key)
    bundle = build_distribution_bundle(tmp_path / "dist", root=_repository(tmp_path))
    attestation, signature = sign_distribution_bundle(bundle, private_key)
    with bundle.open("ab") as stream:
        stream.write(b"tampered")

    result = verify_distribution_attestation(bundle, attestation, signature, public_key)

    assert result.status == "invalid"
    assert "bundle-sha256" in result.errors or "bundle-size" in result.errors


def test_tampered_attestation_signature_fails(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    generate_signing_key(private_key, public_key)
    bundle = build_distribution_bundle(tmp_path / "dist", root=_repository(tmp_path))
    attestation, signature = sign_distribution_bundle(bundle, private_key)
    attestation.write_bytes(attestation.read_bytes() + b" ")

    result = verify_distribution_attestation(bundle, attestation, signature, public_key)

    assert result.status == "invalid"


def test_wrong_public_key_fails(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    wrong_private = tmp_path / "wrong-private.pem"
    wrong_public = tmp_path / "wrong-public.pem"
    generate_signing_key(private_key, public_key)
    generate_signing_key(wrong_private, wrong_public)
    bundle = build_distribution_bundle(tmp_path / "dist", root=_repository(tmp_path))
    attestation, signature = sign_distribution_bundle(bundle, private_key)

    result = verify_distribution_attestation(bundle, attestation, signature, wrong_public)

    assert result.status == "invalid"


def test_key_generation_refuses_overwrite(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    generate_signing_key(private_key, public_key)

    with pytest.raises(AttestationError):
        generate_signing_key(private_key, public_key)
