"""Command-line entry point for the AEGIS Platform release candidate."""

from __future__ import annotations

import argparse
import subprocess
import sys

from pathlib import Path

from aegis_os.attestation import (
    generate_signing_key,
    sign_distribution_bundle,
    verify_distribution_attestation,
)
from aegis_os.distribution import build_distribution_bundle, verify_distribution_bundle
from aegis_os.operator import build_operator_readiness
from aegis_os.trust import (
    initialize_trust_policy,
    revoke_trust_key,
    rotate_trust_key,
    verify_attestation_with_trust_policy,
)
from aegis_os.release import build_diagnostic_report


def _doctor(json_output: bool) -> int:
    report = build_diagnostic_report()
    if json_output:
        print(report.to_json())
    else:
        print(f"AEGIS Platform {report.platform_version}: {report.status}")
        print(f"Python: {report.python_version}")
        print(f"Interpreter: {report.interpreter}")
        for check in report.checks:
            print(f"[{check.status.upper()}] {check.name}: {check.detail}")
    return 0 if report.status == "ready" else 2


def _serve(host: str, port: int, reload: bool) -> int:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "aegis_os.api.app:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        command.append("--reload")
    return subprocess.call(command)


def _ready(host: str, port: int, json_output: bool) -> int:
    readiness = build_operator_readiness(host, port)
    if json_output:
        print(readiness.to_json())
    else:
        print(f"AEGIS Platform {readiness.platform_version}: {readiness.status}")
        print(f"Endpoint: {readiness.endpoint}")
        for limitation in readiness.limitations:
            print(f"LIMITATION: {limitation}")
    return 0 if readiness.status == "ready" else 2


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m aegis_os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Validate the local runtime.")
    doctor.add_argument("--json", action="store_true", dest="json_output")

    ready = subparsers.add_parser("ready", help="Check operator launch readiness.")
    ready.add_argument("--host", default="127.0.0.1")
    ready.add_argument("--port", default=8000, type=int)
    ready.add_argument("--json", action="store_true", dest="json_output")

    package = subparsers.add_parser("package", help="Build a verified distribution bundle.")
    package.add_argument("--output-dir", type=Path, default=Path("dist"))

    verify_package = subparsers.add_parser(
        "verify-package", help="Verify a distribution bundle."
    )
    verify_package.add_argument("bundle", type=Path)
    verify_package.add_argument("--json", action="store_true", dest="json_output")


    keygen = subparsers.add_parser("keygen", help="Generate an Ed25519 release signing key pair.")
    keygen.add_argument("--private-key", type=Path, required=True)
    keygen.add_argument("--public-key", type=Path, required=True)
    keygen.add_argument("--overwrite", action="store_true")

    sign_package = subparsers.add_parser("sign-package", help="Sign and attest a verified distribution bundle.")
    sign_package.add_argument("bundle", type=Path)
    sign_package.add_argument("--private-key", type=Path, required=True)
    sign_package.add_argument("--output-dir", type=Path)

    verify_attestation = subparsers.add_parser("verify-attestation", help="Verify a signed distribution attestation.")
    verify_attestation.add_argument("bundle", type=Path)
    verify_attestation.add_argument("--attestation", type=Path, required=True)
    verify_attestation.add_argument("--signature", type=Path, required=True)
    verify_attestation.add_argument("--public-key", type=Path, required=True)

    trust_init = subparsers.add_parser("trust-init", help="Create a signing-key trust policy.")
    trust_init.add_argument("--public-key", type=Path, required=True)
    trust_init.add_argument("--policy", type=Path, required=True)
    trust_init.add_argument("--overwrite", action="store_true")

    trust_rotate = subparsers.add_parser("trust-rotate", help="Rotate the active trusted signing key.")
    trust_rotate.add_argument("--policy", type=Path, required=True)
    trust_rotate.add_argument("--new-public-key", type=Path, required=True)
    trust_rotate.add_argument("--effective-at")

    trust_revoke = subparsers.add_parser("trust-revoke", help="Revoke a trusted signing key.")
    trust_revoke.add_argument("--policy", type=Path, required=True)
    trust_revoke.add_argument("--key-id", required=True)
    trust_revoke.add_argument("--reason", required=True)
    trust_revoke.add_argument("--revoked-at")
    trust_revoke.add_argument("--future-only", action="store_true")

    verify_trusted = subparsers.add_parser("verify-trusted-attestation", help="Verify an attestation against a trust policy.")
    verify_trusted.add_argument("bundle", type=Path)
    verify_trusted.add_argument("--attestation", type=Path, required=True)
    verify_trusted.add_argument("--signature", type=Path, required=True)
    verify_trusted.add_argument("--policy", type=Path, required=True)

    serve = subparsers.add_parser("serve", help="Start the local API and dashboard.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--reload", action="store_true")

    arguments = parser.parse_args()
    if arguments.command == "doctor":
        return _doctor(arguments.json_output)
    if arguments.command == "ready":
        return _ready(arguments.host, arguments.port, arguments.json_output)
    if arguments.command == "package":
        bundle = build_distribution_bundle(arguments.output_dir)
        result = verify_distribution_bundle(bundle)
        print(result.to_json())
        return 0 if result.status == "verified" else 2
    if arguments.command == "verify-package":
        result = verify_distribution_bundle(arguments.bundle)
        print(result.to_json() if arguments.json_output else f"Distribution: {result.status}")
        return 0 if result.status == "verified" else 2
    if arguments.command == "keygen":
        key_id = generate_signing_key(arguments.private_key, arguments.public_key, overwrite=arguments.overwrite)
        print(f"Generated release signing key: {key_id}")
        return 0
    if arguments.command == "sign-package":
        attestation, signature = sign_distribution_bundle(arguments.bundle, arguments.private_key, output_directory=arguments.output_dir)
        print(f"Attestation: {attestation}")
        print(f"Signature: {signature}")
        return 0
    if arguments.command == "verify-attestation":
        result = verify_distribution_attestation(arguments.bundle, arguments.attestation, arguments.signature, arguments.public_key)
        print(result.to_json())
        return 0 if result.status == "verified" else 2
    if arguments.command == "trust-init":
        policy = initialize_trust_policy(arguments.public_key, arguments.policy, overwrite=arguments.overwrite)
        print(policy.to_json(), end="")
        return 0
    if arguments.command == "trust-rotate":
        policy = rotate_trust_key(arguments.policy, arguments.new_public_key, effective_at=arguments.effective_at)
        print(policy.to_json(), end="")
        return 0
    if arguments.command == "trust-revoke":
        policy = revoke_trust_key(
            arguments.policy, arguments.key_id, arguments.reason,
            revoked_at=arguments.revoked_at,
            revoke_all_signatures=not arguments.future_only,
        )
        print(policy.to_json(), end="")
        return 0
    if arguments.command == "verify-trusted-attestation":
        result = verify_attestation_with_trust_policy(
            arguments.bundle, arguments.attestation, arguments.signature, arguments.policy
        )
        print(result.to_json())
        return 0 if result.status == "verified" else 2
    return _serve(arguments.host, arguments.port, arguments.reload)


if __name__ == "__main__":
    raise SystemExit(main())
