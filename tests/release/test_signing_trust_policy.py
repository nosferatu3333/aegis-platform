import json
import subprocess
from pathlib import Path

import pytest

from aegis_os.attestation import generate_signing_key, sign_distribution_bundle
from aegis_os.distribution import build_distribution_bundle
from aegis_os.trust import (
    SigningKeyState,
    TrustPolicyError,
    initialize_trust_policy,
    load_trust_policy,
    revoke_trust_key,
    rotate_trust_key,
    verify_attestation_with_trust_policy,
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


def _signed_bundle(tmp_path: Path, private_key: Path):
    bundle = build_distribution_bundle(tmp_path / "dist", root=_repository(tmp_path))
    attestation, signature = sign_distribution_bundle(bundle, private_key)
    return bundle, attestation, signature


def test_initialize_policy_and_verify_trusted_attestation(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    key_id = generate_signing_key(private_key, public_key)
    policy_path = tmp_path / "trust-policy.json"
    policy = initialize_trust_policy(public_key, policy_path)
    bundle, attestation, signature = _signed_bundle(tmp_path, private_key)

    result = verify_attestation_with_trust_policy(bundle, attestation, signature, policy_path)

    assert policy.keys[0].key_id == key_id
    assert result.status == "verified"
    assert result.key_state == "active"


def test_rotation_preserves_historical_signature_and_changes_active_key(tmp_path: Path):
    old_private = tmp_path / "old-private.pem"
    old_public = tmp_path / "old-public.pem"
    new_private = tmp_path / "new-private.pem"
    new_public = tmp_path / "new-public.pem"
    old_id = generate_signing_key(old_private, old_public)
    new_id = generate_signing_key(new_private, new_public)
    policy_path = tmp_path / "policy.json"
    initialize_trust_policy(old_public, policy_path)
    bundle, attestation, signature = _signed_bundle(tmp_path, old_private)
    issued_at = json.loads(attestation.read_text())["issued_at"]

    policy = rotate_trust_key(policy_path, new_public, effective_at=issued_at)
    result = verify_attestation_with_trust_policy(bundle, attestation, signature, policy_path)

    assert policy.key(old_id).state == SigningKeyState.RETIRING
    assert policy.key(old_id).successor_key_id == new_id
    assert policy.key(new_id).state == SigningKeyState.ACTIVE
    assert result.status == "verified"


def test_revocation_blocks_all_signatures_by_default(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    key_id = generate_signing_key(private_key, public_key)
    policy_path = tmp_path / "policy.json"
    initialize_trust_policy(public_key, policy_path)
    bundle, attestation, signature = _signed_bundle(tmp_path, private_key)

    revoke_trust_key(policy_path, key_id, "key compromise")
    result = verify_attestation_with_trust_policy(bundle, attestation, signature, policy_path)

    assert result.status == "invalid"
    assert "signing-key-revoked" in result.errors


def test_future_only_revocation_preserves_older_signature(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    key_id = generate_signing_key(private_key, public_key)
    policy_path = tmp_path / "policy.json"
    initialize_trust_policy(public_key, policy_path)
    bundle, attestation, signature = _signed_bundle(tmp_path, private_key)

    revoke_trust_key(
        policy_path,
        key_id,
        "routine retirement",
        revoked_at="2999-01-01T00:00:00Z",
        revoke_all_signatures=False,
    )
    result = verify_attestation_with_trust_policy(bundle, attestation, signature, policy_path)

    assert result.status == "verified"
    assert result.key_state == "revoked"


def test_untrusted_signer_is_rejected(tmp_path: Path):
    trusted_private = tmp_path / "trusted-private.pem"
    trusted_public = tmp_path / "trusted-public.pem"
    other_private = tmp_path / "other-private.pem"
    other_public = tmp_path / "other-public.pem"
    generate_signing_key(trusted_private, trusted_public)
    generate_signing_key(other_private, other_public)
    policy_path = tmp_path / "policy.json"
    initialize_trust_policy(trusted_public, policy_path)
    bundle, attestation, signature = _signed_bundle(tmp_path, other_private)

    result = verify_attestation_with_trust_policy(bundle, attestation, signature, policy_path)

    assert result.status == "invalid"
    assert "untrusted-signer" in result.errors


def test_policy_refuses_overwrite_and_duplicate_rotation(tmp_path: Path):
    private_key = tmp_path / "private.pem"
    public_key = tmp_path / "public.pem"
    generate_signing_key(private_key, public_key)
    policy_path = tmp_path / "policy.json"
    initialize_trust_policy(public_key, policy_path)

    with pytest.raises(TrustPolicyError):
        initialize_trust_policy(public_key, policy_path)
    with pytest.raises(TrustPolicyError):
        rotate_trust_key(policy_path, public_key)

    assert load_trust_policy(policy_path).policy_version == 1
