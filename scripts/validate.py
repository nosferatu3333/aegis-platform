"""Run the canonical, non-mutating AEGIS repository validation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

MINIMUM_PYTHON = (3, 11)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _verify_interpreter(allow_external: bool) -> int:
    executable = Path(sys.executable).resolve()
    print(f"Repository: {REPOSITORY_ROOT}", flush=True)
    print(f"Python: {sys.version.split()[0]}", flush=True)
    print(f"Interpreter: {executable}", flush=True)

    if sys.version_info < MINIMUM_PYTHON:
        required = ".".join(str(part) for part in MINIMUM_PYTHON)
        print(f"ERROR: AEGIS requires Python {required} or newer.", file=sys.stderr)
        return 2

    repository_environments = [
        path.resolve()
        for path in (REPOSITORY_ROOT / "env", REPOSITORY_ROOT / ".venv")
        if path.is_dir()
    ]
    uses_repository_environment = any(
        _is_within(executable, environment) for environment in repository_environments
    )
    if (
        repository_environments
        and not uses_repository_environment
        and not allow_external
    ):
        expected = " or ".join(str(path) for path in repository_environments)
        print(
            "ERROR: Python resolves outside the repository environment.\n"
            f"Expected an interpreter under: {expected}\n"
            "Invoke the repository interpreter explicitly, or use "
            "--allow-external-interpreter only for an isolated CI/test environment.",
            file=sys.stderr,
        )
        return 2

    declared_environment = os.environ.get("VIRTUAL_ENV")
    if declared_environment:
        declared = Path(declared_environment).resolve()
        if not _is_within(executable, declared):
            print(
                "WARNING: VIRTUAL_ENV does not match the selected interpreter: "
                f"{declared}",
                file=sys.stderr,
            )
    return 0


def _run(label: str, command: list[str], environment: dict[str, str]) -> int:
    print(f"\n==> {label}", flush=True)
    print(" ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        env=environment,
        check=False,
    )
    if completed.returncode:
        print(
            f"ERROR: {label} failed with exit code {completed.returncode}.",
            file=sys.stderr,
        )
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--allow-external-interpreter",
        action="store_true",
        help="Allow a verified isolated interpreter outside the repository.",
    )
    arguments = parser.parse_args()

    interpreter_result = _verify_interpreter(arguments.allow_external_interpreter)
    if interpreter_result:
        return interpreter_result

    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    commands = [
        ("Dependency integrity", [sys.executable, "-m", "pip", "check"]),
        ("Release diagnostics", [sys.executable, "-m", "aegis_os", "doctor"]),
        (
            "Governed release acceptance",
            [sys.executable, "scripts/release_acceptance.py"],
        ),
        (
            "Pre-commit configuration",
            [sys.executable, "-m", "pre_commit", "validate-config"],
        ),
        (
            "Ruff lint",
            [sys.executable, "-m", "ruff", "check", "--no-cache", "."],
        ),
        (
            "Ruff format verification",
            [
                sys.executable,
                "-m",
                "ruff",
                "format",
                "--check",
                "--no-cache",
                ".",
            ],
        ),
        (
            "Pytest",
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
            ],
        ),
        ("Git whitespace validation", ["git", "diff", "--check", "HEAD", "--"]),
    ]

    for label, command in commands:
        result = _run(label, command, environment)
        if result:
            return result

    print("\nRepository validation passed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
