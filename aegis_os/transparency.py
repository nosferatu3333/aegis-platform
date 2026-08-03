"""Release transparency ledger and human-readable trust reporting."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aegis_os.trust import load_trust_policy, verify_attestation_with_trust_policy

LEDGER_TYPE = "https://aegis.dev/transparency/release-ledger/v1"
GENESIS_HASH = "0" * 64


class TransparencyError(RuntimeError):
    """Raised when the transparency ledger is malformed or inconsistent."""


@dataclass(frozen=True)
class TransparencyEvent:
    sequence: int
    event_type: str
    occurred_at: str
    subject: str
    details: dict[str, Any]
    previous_hash: str
    event_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TransparencyVerification:
    status: str
    event_count: int
    head_hash: str | None
    errors: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


@dataclass(frozen=True)
class TrustReport:
    overall_verdict: str
    release_integrity: str
    signature: str
    signer: str
    signing_key_state: str
    attestation: str
    transparency: str
    policy_version: int | None
    source_commit: str | None
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_text(self) -> str:
        lines = [
            f"Overall verdict: {self.overall_verdict}",
            f"Release integrity: {self.release_integrity}",
            f"Signature: {self.signature}",
            f"Signer: {self.signer}",
            f"Signing key: {self.signing_key_state}",
            f"Attestation: {self.attestation}",
            f"Transparency: {self.transparency}",
            f"Policy version: {self.policy_version if self.policy_version is not None else 'unknown'}",
            f"Source commit: {self.source_commit or 'unknown'}",
        ]
        lines.extend(f"Reason: {reason}" for reason in self.reasons)
        return "\n".join(lines)


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_event_payload(sequence: int, event_type: str, occurred_at: str, subject: str, details: dict[str, Any], previous_hash: str) -> bytes:
    return json.dumps({
        "ledger_type": LEDGER_TYPE,
        "sequence": sequence,
        "event_type": event_type,
        "occurred_at": occurred_at,
        "subject": subject,
        "details": details,
        "previous_hash": previous_hash,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_transparency_ledger(path: Path) -> tuple[TransparencyEvent, ...]:
    if not path.exists():
        return ()
    events: list[TransparencyEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            data = json.loads(line)
            events.append(TransparencyEvent(
                sequence=int(data["sequence"]), event_type=data["event_type"],
                occurred_at=data["occurred_at"], subject=data["subject"],
                details=dict(data["details"]), previous_hash=data["previous_hash"],
                event_hash=data["event_hash"],
            ))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise TransparencyError(f"Invalid ledger event at line {line_number}: {error}") from error
    return tuple(events)


def verify_transparency_ledger(path: Path) -> TransparencyVerification:
    errors: list[str] = []
    try:
        events = load_transparency_ledger(path)
    except TransparencyError as error:
        return TransparencyVerification("invalid", 0, None, (str(error),))
    previous = GENESIS_HASH
    for expected_sequence, event in enumerate(events, 1):
        if event.sequence != expected_sequence:
            errors.append(f"sequence-mismatch:{expected_sequence}")
        if event.previous_hash != previous:
            errors.append(f"previous-hash-mismatch:{event.sequence}")
        expected_hash = hashlib.sha256(_canonical_event_payload(
            event.sequence, event.event_type, event.occurred_at,
            event.subject, event.details, event.previous_hash,
        )).hexdigest()
        if event.event_hash != expected_hash:
            errors.append(f"event-hash-mismatch:{event.sequence}")
        previous = event.event_hash
    return TransparencyVerification("verified" if not errors else "invalid", len(events), previous if events else None, tuple(errors))


def append_transparency_event(path: Path, event_type: str, subject: str, details: dict[str, Any], *, occurred_at: str | None = None) -> TransparencyEvent:
    verification = verify_transparency_ledger(path)
    if verification.status != "verified":
        raise TransparencyError("Refusing to append to an invalid transparency ledger.")
    events = load_transparency_ledger(path)
    sequence = len(events) + 1
    previous_hash = events[-1].event_hash if events else GENESIS_HASH
    timestamp = occurred_at or _now()
    event_hash = hashlib.sha256(_canonical_event_payload(sequence, event_type, timestamp, subject, details, previous_hash)).hexdigest()
    event = TransparencyEvent(sequence, event_type, timestamp, subject, details, previous_hash, event_hash)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":")) + "\n")
    return event


def build_trust_report(bundle: Path, attestation: Path, signature: Path, policy: Path, ledger: Path | None = None) -> TrustReport:
    trusted = verify_attestation_with_trust_policy(bundle, attestation, signature, policy)
    ledger_result = verify_transparency_ledger(ledger) if ledger else TransparencyVerification("not-provided", 0, None, ())
    reasons = list(trusted.errors)
    if ledger and ledger_result.status != "verified":
        reasons.extend(ledger_result.errors or ("transparency-ledger-invalid",))
    try:
        attestation_data = json.loads(attestation.read_text(encoding="utf-8"))
        source_commit = attestation_data.get("source_commit")
    except (OSError, json.JSONDecodeError):
        source_commit = None
    policy_data = load_trust_policy(policy)
    overall = "TRUSTED" if trusted.status == "verified" and (not ledger or ledger_result.status == "verified") else "REJECTED"
    return TrustReport(
        overall_verdict=overall,
        release_integrity="verified" if trusted.cryptographic_status == "verified" else "invalid",
        signature=trusted.cryptographic_status,
        signer=trusted.signer_key_id or "unknown",
        signing_key_state=trusted.key_state or "unknown",
        attestation=trusted.status,
        transparency=ledger_result.status,
        policy_version=policy_data.policy_version,
        source_commit=source_commit,
        reasons=tuple(dict.fromkeys(reasons)),
    )
