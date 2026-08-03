from pathlib import Path


def test_release_requirements_include_bounded_cryptography():
    requirements = Path("requirements/release.txt").read_text(encoding="utf-8")
    assert "cryptography>=43,<47" in requirements


def test_project_and_release_dependency_surfaces_match_for_cryptography():
    project = Path("pyproject.toml").read_text(encoding="utf-8")
    release = Path("requirements/release.txt").read_text(encoding="utf-8")
    assert "cryptography>=43,<47" in project
    assert "cryptography>=43,<47" in release


def test_bootstrap_runs_dependency_consistency_check():
    bootstrap = Path("scripts/bootstrap.py").read_text(encoding="utf-8")
    assert '"pip", "check"' in bootstrap
    assert bootstrap.index('"pip", "check"') < bootstrap.index('"aegis_os", "doctor"')


def test_windows_trial_writes_partial_failure_report():
    script = Path("scripts/operator_trial.ps1").read_text(encoding="utf-8")
    assert "Write-FailureReport" in script
    assert 'overall_status = "failed"' in script
    assert "Partial failure report" in script


def test_windows_trial_can_build_temporary_policy_from_public_key():
    script = Path("scripts/operator_trial.ps1").read_text(encoding="utf-8")
    assert "[string]$PublicKey" in script
    assert "trust-init" in script
    assert "TemporaryPolicy" in script
