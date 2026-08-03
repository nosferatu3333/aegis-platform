from __future__ import annotations

import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from aegis_os.distribution import (
    DistributionError,
    build_distribution_bundle,
    verify_distribution_bundle,
)


def _repository(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=root,
        check=True,
    )
    subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
    (root / "README.md").write_text("AEGIS\n", encoding="utf-8")
    (root / "module.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
    return root


def test_distribution_bundle_is_reproducible_and_verified(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    first = build_distribution_bundle(tmp_path / "one", root=root)
    second = build_distribution_bundle(tmp_path / "two", root=root)

    assert first.read_bytes() == second.read_bytes()
    verification = verify_distribution_bundle(first)
    assert verification.status == "verified"
    assert verification.verified_files == 2


def test_distribution_manifest_preserves_source_provenance(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    bundle = build_distribution_bundle(tmp_path / "dist", root=root)
    commit = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=root, text=True
    ).strip()

    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("aegis-platform/DISTRIBUTION_MANIFEST.json"))
    assert manifest["source_commit"] == commit
    assert manifest["platform_version"]
    assert manifest["real_world_effects_verified"] is False


def test_distribution_verifier_detects_tampering(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    bundle = build_distribution_bundle(tmp_path / "dist", root=root)
    tampered = tmp_path / "tampered.zip"

    with zipfile.ZipFile(bundle) as source, zipfile.ZipFile(tampered, "w") as target:
        for info in source.infolist():
            payload = source.read(info.filename)
            if info.filename == "aegis-platform/README.md":
                payload = b"tampered\n"
            target.writestr(info, payload)

    verification = verify_distribution_bundle(tampered)
    assert verification.status == "invalid"
    assert any("README.md" in error for error in verification.errors)


def test_distribution_refuses_dirty_repository(tmp_path: Path) -> None:
    root = _repository(tmp_path)
    (root / "README.md").write_text("changed\n", encoding="utf-8")

    with pytest.raises(DistributionError, match="dirty repository"):
        build_distribution_bundle(tmp_path / "dist", root=root)


def test_distribution_cli_commands_are_registered() -> None:
    from aegis_os.__main__ import main

    assert callable(main)
