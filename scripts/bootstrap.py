"""Create a reproducible local AEGIS Platform development environment."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORE = ROOT.parent / "aegis-core"
ALTERNATE_CORE = ROOT.parent / "aegis-core-clean"


def _run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, cwd=ROOT, check=True)


def _resolve_core(explicit: str | None) -> Path:
    candidates = [Path(explicit).resolve()] if explicit else []
    candidates.extend((DEFAULT_CORE, ALTERNATE_CORE))
    for candidate in candidates:
        if (candidate / "pyproject.toml").is_file() and (
            candidate / "src" / "aegis_core"
        ).is_dir():
            return candidate.resolve()
    searched = ", ".join(str(path) for path in candidates)
    raise SystemExit(
        "Compatible AEGIS Core checkout not found. "
        f"Use --core-path. Searched: {searched}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-path", help="Path to the AEGIS Core repository.")
    parser.add_argument("--skip-tests", action="store_true")
    arguments = parser.parse_args()

    core_path = _resolve_core(arguments.core_path)
    print(f"Using AEGIS Core: {core_path}")
    _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    _run([sys.executable, "-m", "pip", "uninstall", "-y", "aegis-core"])
    _run([sys.executable, "-m", "pip", "install", "-e", str(core_path)])
    _run([sys.executable, "-m", "pip", "install", "-e", ".[test]", "--no-deps"])
    _run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            "requirements/release.txt",
        ]
    )
    _run([sys.executable, "-m", "pip", "check"])
    _run([sys.executable, "-m", "aegis_os", "doctor"])
    if not arguments.skip_tests:
        _run([sys.executable, "-m", "pytest", "-q"])
    print("AEGIS Platform release-candidate environment is ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
