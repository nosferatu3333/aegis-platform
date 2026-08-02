"""Release compatibility and environment diagnostics for AEGIS Platform."""

from __future__ import annotations

import importlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from packaging.specifiers import SpecifierSet
from packaging.version import Version

PLATFORM_VERSION = "0.8.0"
CORE_VERSION_SPEC = SpecifierSet(">=0.3.0,<0.4.0")
MINIMUM_PYTHON = (3, 11)
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class DiagnosticCheck:
    name: str
    status: str
    detail: str


@dataclass(frozen=True)
class DiagnosticReport:
    status: str
    platform_version: str
    python_version: str
    interpreter: str
    checks: tuple[DiagnosticCheck, ...]

    def to_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["checks"] = [asdict(check) for check in self.checks]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


def _distribution_version(name: str) -> str | None:
    try:
        return version(name)
    except PackageNotFoundError:
        return None


def build_diagnostic_report() -> DiagnosticReport:
    checks: list[DiagnosticCheck] = []

    python_ok = sys.version_info >= MINIMUM_PYTHON
    checks.append(
        DiagnosticCheck(
            name="python",
            status="pass" if python_ok else "fail",
            detail=f"{platform.python_version()} (requires >=3.11)",
        )
    )

    core_version = _distribution_version("aegis-core")
    core_importable = False
    core_location = "unavailable"
    try:
        core_package = importlib.import_module("aegis_core")
        core_module = importlib.import_module("aegis_core.contracts")
        core_importable = True
        core_location = str(Path(core_module.__file__ or "unknown").resolve())
        core_version = getattr(core_package, "__version__", core_version)
    except (ImportError, AttributeError) as error:
        core_location = str(error)

    core_version_ok = bool(
        core_version and Version(core_version) in CORE_VERSION_SPEC
    )
    checks.append(
        DiagnosticCheck(
            name="aegis-core",
            status="pass" if core_importable and core_version_ok else "fail",
            detail=(
                f"version={core_version or 'missing'}; "
                f"required={CORE_VERSION_SPEC}; location={core_location}"
            ),
        )
    )

    platform_version = _distribution_version("aegis-os") or PLATFORM_VERSION
    platform_ok = platform_version == PLATFORM_VERSION
    checks.append(
        DiagnosticCheck(
            name="aegis-platform",
            status="pass" if platform_ok else "fail",
            detail=f"version={platform_version}; expected={PLATFORM_VERSION}",
        )
    )

    required_modules = ("fastapi", "uvicorn", "httpx", "pytest")
    missing: list[str] = []
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
        except ImportError:
            missing.append(module_name)
    checks.append(
        DiagnosticCheck(
            name="runtime-dependencies",
            status="pass" if not missing else "fail",
            detail="all available" if not missing else f"missing={','.join(missing)}",
        )
    )

    overall = "ready" if all(check.status == "pass" for check in checks) else "blocked"
    return DiagnosticReport(
        status=overall,
        platform_version=PLATFORM_VERSION,
        python_version=platform.python_version(),
        interpreter=str(Path(sys.executable).resolve()),
        checks=tuple(checks),
    )
