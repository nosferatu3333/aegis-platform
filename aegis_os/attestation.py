"""Cryptographic signing and provenance attestation for AEGIS distributions."""
from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

ATTESTATION_TYPE = "https://aegis.dev/attestation/distribution/v1"

class AttestationError(RuntimeError):
    """Raised when signing or attestation verification fails."""

@dataclass(frozen=True)
class ProvenanceAttestation:
    attestation_type: str
    product: str
    platform_version: str
    bundle_name: str
    bundle_sha256: str
    bundle_size: int
    source_commit: str
    source_tree: str
    source_branch: str
    signer_key_id: str
    issued_at: str
    execution_mode: str = "deterministic simulation only"
    real_world_effects_verified: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def canonical_bytes(self) -> bytes:
        return (json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":")) + "\n").encode()

@dataclass(frozen=True)
class AttestationVerification:
    status: str
    bundle: str
    attestation: str
    signer_key_id: str | None
    bundle_sha256: str | None
    errors: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def public_key_id(public_key: Ed25519PublicKey) -> str:
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return "ed25519:" + hashlib.sha256(raw).hexdigest()[:32]

def generate_signing_key(private_key_path: Path, public_key_path: Path, *, overwrite: bool = False) -> str:
    if not overwrite and (private_key_path.exists() or public_key_path.exists()):
        raise AttestationError("Refusing to overwrite an existing signing key.")
    private_key = Ed25519PrivateKey.generate()
    private_key_path.parent.mkdir(parents=True, exist_ok=True)
    public_key_path.parent.mkdir(parents=True, exist_ok=True)
    private_key_path.write_bytes(private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ))
    public_key = private_key.public_key()
    public_key_path.write_bytes(public_key.public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    try:
        private_key_path.chmod(0o600)
    except OSError:
        pass
    return public_key_id(public_key)

def _load_private(path: Path) -> Ed25519PrivateKey:
    key = serialization.load_pem_private_key(path.read_bytes(), password=None)
    if not isinstance(key, Ed25519PrivateKey):
        raise AttestationError("Signing key is not an Ed25519 private key.")
    return key

def _load_public(path: Path) -> Ed25519PublicKey:
    key = serialization.load_pem_public_key(path.read_bytes())
    if not isinstance(key, Ed25519PublicKey):
        raise AttestationError("Verification key is not an Ed25519 public key.")
    return key

def sign_distribution_bundle(bundle: Path, private_key_path: Path, *, output_directory: Path | None = None) -> tuple[Path, Path]:
    from aegis_os.distribution import verify_distribution_bundle
    verification = verify_distribution_bundle(bundle)
    if verification.status != "verified":
        raise AttestationError("Refusing to sign an invalid distribution bundle.")
    private_key = _load_private(private_key_path)
    public_key = private_key.public_key()
    output_directory = output_directory or bundle.parent
    output_directory.mkdir(parents=True, exist_ok=True)
    attestation = ProvenanceAttestation(
        attestation_type=ATTESTATION_TYPE,
        product="AEGIS Platform",
        platform_version=verification.platform_version or "unknown",
        bundle_name=bundle.name,
        bundle_sha256=sha256_file(bundle),
        bundle_size=bundle.stat().st_size,
        source_commit=verification.source_commit or "unknown",
        source_tree=verification.source_tree or "unknown",
        source_branch=verification.source_branch or "unknown",
        signer_key_id=public_key_id(public_key),
        issued_at=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    payload = attestation.canonical_bytes()
    attestation_path = output_directory / f"{bundle.name}.attestation.json"
    signature_path = output_directory / f"{bundle.name}.attestation.sig"
    attestation_path.write_bytes(payload)
    signature_path.write_text(base64.b64encode(private_key.sign(payload)).decode() + "\n", encoding="ascii")
    return attestation_path, signature_path

def verify_distribution_attestation(bundle: Path, attestation_path: Path, signature_path: Path, public_key_path: Path) -> AttestationVerification:
    errors: list[str] = []
    key_id: str | None = None
    bundle_digest: str | None = None
    try:
        public_key = _load_public(public_key_path)
        key_id = public_key_id(public_key)
        payload = attestation_path.read_bytes()
        signature = base64.b64decode(signature_path.read_text(encoding="ascii").strip(), validate=True)
        public_key.verify(signature, payload)
        data = json.loads(payload)
        bundle_digest = sha256_file(bundle)
        checks = {
            "attestation-type": data.get("attestation_type") == ATTESTATION_TYPE,
            "bundle-name": data.get("bundle_name") == bundle.name,
            "bundle-sha256": data.get("bundle_sha256") == bundle_digest,
            "bundle-size": data.get("bundle_size") == bundle.stat().st_size,
            "signer-key-id": data.get("signer_key_id") == key_id,
        }
        errors.extend(name for name, valid in checks.items() if not valid)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, InvalidSignature, AttestationError) as error:
        errors.append(type(error).__name__ if isinstance(error, InvalidSignature) else str(error))
    return AttestationVerification(
        status="verified" if not errors else "invalid",
        bundle=str(bundle.resolve()),
        attestation=str(attestation_path.resolve()),
        signer_key_id=key_id,
        bundle_sha256=bundle_digest,
        errors=tuple(errors),
    )
