"""Signing-key lifecycle and trust-policy enforcement for AEGIS releases."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from tempfile import NamedTemporaryFile

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from aegis_os.attestation import (
    AttestationError,
    AttestationVerification,
    _load_public,
    public_key_id,
    verify_distribution_attestation,
)

TRUST_POLICY_TYPE = "https://aegis.dev/trust/signing-policy/v1"


class TrustPolicyError(RuntimeError):
    """Raised when a trust policy or key lifecycle transition is invalid."""


class SigningKeyState(StrEnum):
    ACTIVE = "active"
    RETIRING = "retiring"
    REVOKED = "revoked"


@dataclass(frozen=True)
class TrustedSigningKey:
    key_id: str
    public_key_pem: str
    state: SigningKeyState
    valid_from: str
    valid_until: str | None = None
    predecessor_key_id: str | None = None
    successor_key_id: str | None = None
    revoked_at: str | None = None
    revocation_reason: str | None = None
    revoke_all_signatures: bool = True

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["state"] = self.state.value
        return data


@dataclass(frozen=True)
class SigningTrustPolicy:
    policy_type: str
    product: str
    policy_version: int
    updated_at: str
    keys: tuple[TrustedSigningKey, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "policy_type": self.policy_type,
            "product": self.product,
            "policy_version": self.policy_version,
            "updated_at": self.updated_at,
            "keys": [key.to_dict() for key in self.keys],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True) + "\n"

    def key(self, key_id: str) -> TrustedSigningKey | None:
        return next((key for key in self.keys if key.key_id == key_id), None)


@dataclass(frozen=True)
class TrustedAttestationVerification:
    status: str
    signer_key_id: str | None
    key_state: str | None
    policy_version: int | None
    cryptographic_status: str
    errors: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise TrustPolicyError(f"Invalid UTC timestamp: {value}") from error
    if parsed.tzinfo is None:
        raise TrustPolicyError(f"Timestamp must include timezone: {value}")
    return parsed.astimezone(UTC)


def _public_key_pem(path: Path) -> tuple[str, str]:
    key = _load_public(path)
    pem = key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return public_key_id(key), pem


def _validate_policy(policy: SigningTrustPolicy) -> None:
    if policy.policy_type != TRUST_POLICY_TYPE:
        raise TrustPolicyError("Unsupported trust-policy type.")
    if policy.policy_version < 1:
        raise TrustPolicyError("policy_version must be positive.")
    ids = [key.key_id for key in policy.keys]
    if len(ids) != len(set(ids)):
        raise TrustPolicyError("Duplicate signing key identifiers are forbidden.")
    if sum(key.state == SigningKeyState.ACTIVE for key in policy.keys) > 1:
        raise TrustPolicyError("Only one signing key may be active.")
    for key in policy.keys:
        loaded = serialization.load_pem_public_key(key.public_key_pem.encode("ascii"))
        if not isinstance(loaded, Ed25519PublicKey) or public_key_id(loaded) != key.key_id:
            raise TrustPolicyError(f"Public key does not match key identifier {key.key_id}.")
        start = _parse_time(key.valid_from)
        if key.valid_until and _parse_time(key.valid_until) < start:
            raise TrustPolicyError("valid_until cannot precede valid_from.")
        if key.state == SigningKeyState.REVOKED:
            if not key.revoked_at or not key.revocation_reason:
                raise TrustPolicyError("Revoked keys require time and reason.")
        if key.successor_key_id and key.successor_key_id not in ids:
            raise TrustPolicyError("Unknown successor key identifier.")
        if key.predecessor_key_id and key.predecessor_key_id not in ids:
            raise TrustPolicyError("Unknown predecessor key identifier.")


def load_trust_policy(path: Path) -> SigningTrustPolicy:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        policy = SigningTrustPolicy(
            policy_type=data["policy_type"],
            product=data["product"],
            policy_version=int(data["policy_version"]),
            updated_at=data["updated_at"],
            keys=tuple(
                TrustedSigningKey(
                    key_id=item["key_id"],
                    public_key_pem=item["public_key_pem"],
                    state=SigningKeyState(item["state"]),
                    valid_from=item["valid_from"],
                    valid_until=item.get("valid_until"),
                    predecessor_key_id=item.get("predecessor_key_id"),
                    successor_key_id=item.get("successor_key_id"),
                    revoked_at=item.get("revoked_at"),
                    revocation_reason=item.get("revocation_reason"),
                    revoke_all_signatures=bool(item.get("revoke_all_signatures", True)),
                )
                for item in data["keys"]
            ),
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise TrustPolicyError(f"Invalid trust policy: {error}") from error
    _validate_policy(policy)
    return policy


def write_trust_policy(policy: SigningTrustPolicy, path: Path, *, overwrite: bool = False) -> None:
    _validate_policy(policy)
    if path.exists() and not overwrite:
        raise TrustPolicyError("Refusing to overwrite an existing trust policy.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(policy.to_json(), encoding="utf-8", newline="\n")


def initialize_trust_policy(public_key_path: Path, output_path: Path, *, overwrite: bool = False) -> SigningTrustPolicy:
    key_id, pem = _public_key_pem(public_key_path)
    timestamp = _now()
    policy = SigningTrustPolicy(
        policy_type=TRUST_POLICY_TYPE,
        product="AEGIS Platform",
        policy_version=1,
        updated_at=timestamp,
        keys=(TrustedSigningKey(key_id, pem, SigningKeyState.ACTIVE, timestamp),),
    )
    write_trust_policy(policy, output_path, overwrite=overwrite)
    return policy


def rotate_trust_key(policy_path: Path, new_public_key_path: Path, *, effective_at: str | None = None) -> SigningTrustPolicy:
    policy = load_trust_policy(policy_path)
    timestamp = effective_at or _now()
    _parse_time(timestamp)
    active = next((key for key in policy.keys if key.state == SigningKeyState.ACTIVE), None)
    if active is None:
        raise TrustPolicyError("Key rotation requires one active signing key.")
    new_id, new_pem = _public_key_pem(new_public_key_path)
    if policy.key(new_id):
        raise TrustPolicyError("The replacement key already exists in the policy.")
    updated = tuple(
        replace(key, state=SigningKeyState.RETIRING, valid_until=timestamp, successor_key_id=new_id)
        if key.key_id == active.key_id else key
        for key in policy.keys
    )
    updated += (TrustedSigningKey(
        key_id=new_id,
        public_key_pem=new_pem,
        state=SigningKeyState.ACTIVE,
        valid_from=timestamp,
        predecessor_key_id=active.key_id,
    ),)
    rotated = replace(policy, policy_version=policy.policy_version + 1, updated_at=timestamp, keys=updated)
    write_trust_policy(rotated, policy_path, overwrite=True)
    return rotated


def revoke_trust_key(
    policy_path: Path,
    key_id: str,
    reason: str,
    *,
    revoked_at: str | None = None,
    revoke_all_signatures: bool = True,
) -> SigningTrustPolicy:
    if not reason.strip():
        raise TrustPolicyError("Revocation reason is required.")
    policy = load_trust_policy(policy_path)
    timestamp = revoked_at or _now()
    _parse_time(timestamp)
    target = policy.key(key_id)
    if target is None:
        raise TrustPolicyError("Signing key is not present in the trust policy.")
    if target.state == SigningKeyState.REVOKED:
        raise TrustPolicyError("Signing key is already revoked.")
    keys = tuple(
        replace(
            key,
            state=SigningKeyState.REVOKED,
            revoked_at=timestamp,
            revocation_reason=reason.strip(),
            revoke_all_signatures=revoke_all_signatures,
            valid_until=key.valid_until or timestamp,
        ) if key.key_id == key_id else key
        for key in policy.keys
    )
    revoked = replace(policy, policy_version=policy.policy_version + 1, updated_at=timestamp, keys=keys)
    write_trust_policy(revoked, policy_path, overwrite=True)
    return revoked


def verify_attestation_with_trust_policy(
    bundle: Path,
    attestation_path: Path,
    signature_path: Path,
    policy_path: Path,
) -> TrustedAttestationVerification:
    errors: list[str] = []
    signer_id: str | None = None
    state: str | None = None
    crypto = AttestationVerification("invalid", str(bundle), str(attestation_path), None, None, ("not-run",))
    try:
        policy = load_trust_policy(policy_path)
        data = json.loads(attestation_path.read_text(encoding="utf-8"))
        signer_id = data.get("signer_key_id")
        key = policy.key(signer_id) if signer_id else None
        if key is None:
            errors.append("untrusted-signer")
        else:
            state = key.state.value
            issued_at = _parse_time(data["issued_at"])
            valid_from = _parse_time(key.valid_from)
            if issued_at < valid_from:
                errors.append("signature-before-key-validity")
            if key.valid_until and issued_at > _parse_time(key.valid_until):
                errors.append("signature-after-key-validity")
            if key.state == SigningKeyState.REVOKED:
                revoked_at = _parse_time(key.revoked_at or key.valid_from)
                if key.revoke_all_signatures or issued_at >= revoked_at:
                    errors.append("signing-key-revoked")
            with NamedTemporaryFile("w", suffix=".pem", delete=False, encoding="ascii") as temp:
                temp.write(key.public_key_pem)
                temp_path = Path(temp.name)
            try:
                crypto = verify_distribution_attestation(bundle, attestation_path, signature_path, temp_path)
            finally:
                temp_path.unlink(missing_ok=True)
            if crypto.status != "verified":
                errors.extend(crypto.errors)
        return TrustedAttestationVerification(
            status="verified" if not errors else "invalid",
            signer_key_id=signer_id,
            key_state=state,
            policy_version=policy.policy_version,
            cryptographic_status=crypto.status,
            errors=tuple(dict.fromkeys(errors)),
        )
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, TrustPolicyError, AttestationError) as error:
        errors.append(str(error))
        return TrustedAttestationVerification(
            status="invalid",
            signer_key_id=signer_id,
            key_state=state,
            policy_version=None,
            cryptographic_status=crypto.status,
            errors=tuple(errors),
        )
