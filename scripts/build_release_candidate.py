"""Build the signed external AEGIS MVP release candidate."""

from __future__ import annotations

import argparse
from pathlib import Path

from aegis_os.release_candidate import (
    ReleaseCandidateError,
    build_external_release_candidate,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("release-candidate"))
    parser.add_argument("--private-key", type=Path, required=True)
    parser.add_argument("--public-key", type=Path, required=True)
    parser.add_argument("--generate-key", action="store_true")
    args = parser.parse_args()

    try:
        result = build_external_release_candidate(
            args.output_dir,
            private_key=args.private_key,
            public_key=args.public_key,
            generate_key=args.generate_key,
        )
    except ReleaseCandidateError as error:
        print(f"ERROR: {error}")
        return 2

    print(result.to_json())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
