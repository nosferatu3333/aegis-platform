"""Generate keys, sign, or verify AEGIS distribution attestations."""
from __future__ import annotations
import argparse
from pathlib import Path
from aegis_os.attestation import (
    AttestationError,
    generate_signing_key,
    sign_distribution_bundle,
    verify_distribution_attestation,
)

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    keygen = sub.add_parser("keygen")
    keygen.add_argument("--private-key", type=Path, required=True)
    keygen.add_argument("--public-key", type=Path, required=True)
    keygen.add_argument("--overwrite", action="store_true")
    sign = sub.add_parser("sign")
    sign.add_argument("bundle", type=Path)
    sign.add_argument("--private-key", type=Path, required=True)
    sign.add_argument("--output-dir", type=Path)
    verify = sub.add_parser("verify")
    verify.add_argument("bundle", type=Path)
    verify.add_argument("--attestation", type=Path, required=True)
    verify.add_argument("--signature", type=Path, required=True)
    verify.add_argument("--public-key", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "keygen":
            print(generate_signing_key(args.private_key, args.public_key, overwrite=args.overwrite))
        elif args.command == "sign":
            for path in sign_distribution_bundle(args.bundle, args.private_key, output_directory=args.output_dir):
                print(path)
        else:
            result = verify_distribution_attestation(args.bundle, args.attestation, args.signature, args.public_key)
            print(result.to_json())
            return 0 if result.status == "verified" else 2
    except AttestationError as error:
        print(f"ERROR: {error}")
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
