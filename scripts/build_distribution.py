"""Build or verify the canonical AEGIS Platform distribution bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from aegis_os.distribution import (
    DistributionError,
    build_distribution_bundle,
    verify_distribution_bundle,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--verify", type=Path)
    parser.add_argument("--json", action="store_true", dest="json_output")
    arguments = parser.parse_args()

    try:
        bundle = arguments.verify or build_distribution_bundle(arguments.output_dir)
        result = verify_distribution_bundle(bundle)
    except DistributionError as error:
        print(f"ERROR: {error}")
        return 2

    if arguments.json_output:
        print(result.to_json())
    else:
        print(f"Distribution: {result.status}")
        print(f"Bundle: {result.bundle}")
        print(f"Version: {result.platform_version}")
        print(f"Commit: {result.source_commit}")
        print(f"Verified files: {result.verified_files}")
        for error in result.errors:
            print(f"ERROR: {error}")
    return 0 if result.status == "verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
