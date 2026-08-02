from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from aegis_os.release import (
    CORE_VERSION_SPEC,
    PLATFORM_VERSION,
    build_diagnostic_report,
)

ROOT = Path(__file__).resolve().parents[2]


def test_release_manifest_matches_platform_version() -> None:
    manifest = json.loads((ROOT / "release-manifest.json").read_text())
    assert manifest["platform_version"] == PLATFORM_VERSION
    from packaging.specifiers import SpecifierSet

    assert SpecifierSet(manifest["core_compatibility"]) == CORE_VERSION_SPEC
    assert manifest["real_world_effects_verified"] is False


def test_diagnostics_report_ready_in_valid_environment() -> None:
    report = build_diagnostic_report()
    assert report.status == "ready"
    assert all(check.status == "pass" for check in report.checks)


def test_diagnostics_block_incompatible_core_version() -> None:
    def fake_version(name: str) -> str:
        return "9.0.0" if name == "aegis-core" else PLATFORM_VERSION

    import aegis_core

    with (
        patch("aegis_os.release._distribution_version", side_effect=fake_version),
        patch.object(aegis_core, "__version__", "9.0.0"),
    ):
        report = build_diagnostic_report()
    assert report.status == "blocked"
    core = next(check for check in report.checks if check.name == "aegis-core")
    assert core.status == "fail"


def test_bootstrap_and_release_documentation_exist() -> None:
    assert (ROOT / "scripts" / "bootstrap.py").is_file()
    assert (ROOT / "requirements" / "release.txt").is_file()
    assert (ROOT / "docs" / "release" / "MVP_RC1.md").is_file()
