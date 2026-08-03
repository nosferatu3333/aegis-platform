import json
import socket

from aegis_os.trial import OperatorTrialReport, TrialCheck, run_operator_trial, write_trial_report


def test_trial_runs_governed_scenarios_and_port_control(monkeypatch):
    monkeypatch.setattr("aegis_os.trial.build_diagnostic_report", lambda: type("R", (), {"status": "ready", "to_dict": lambda self: {"status": "ready"}})())
    monkeypatch.setattr("aegis_os.trial.build_operator_readiness", lambda host, port: type("R", (), {"status": "ready", "to_json": lambda self: json.dumps({"status": "ready", "port": port})})())
    report = run_operator_trial(port=0)
    names = {check.name for check in report.checks}
    assert "governed-acceptance-scenarios" in names
    assert "occupied-port-blocking" in names
    assert any("Trust verification was not exercised" in item for item in report.friction)


def test_incomplete_trust_arguments_fail_explicitly(monkeypatch, tmp_path):
    monkeypatch.setattr("aegis_os.trial._diagnostic_check", lambda: (True, "ready", {}))
    monkeypatch.setattr("aegis_os.trial._readiness_check", lambda host, port: (True, "ready", {}))
    report = run_operator_trial(bundle=tmp_path / "bundle.zip")
    check = next(item for item in report.checks if item.name == "release-trust-verification")
    assert check.status == "failed"
    assert report.overall_status == "failed"


def test_trusted_release_check_is_included(monkeypatch, tmp_path):
    monkeypatch.setattr("aegis_os.trial._diagnostic_check", lambda: (True, "ready", {}))
    monkeypatch.setattr("aegis_os.trial._readiness_check", lambda host, port: (True, "ready", {}))
    monkeypatch.setattr("aegis_os.trial._trust_check", lambda *args: (True, "TRUSTED", {"overall_verdict": "TRUSTED"}))
    report = run_operator_trial(
        bundle=tmp_path / "bundle.zip",
        attestation=tmp_path / "attestation.json",
        signature=tmp_path / "signature.sig",
        policy=tmp_path / "policy.json",
    )
    check = next(item for item in report.checks if item.name == "release-trust-verification")
    assert check.status == "passed"


def test_report_writer_creates_json_audit_record(tmp_path):
    report = OperatorTrialReport(
        schema_version="1.0", platform_version="1.3.0", overall_status="passed",
        started_at_epoch_ms=1, duration_ms=2, environment={"python": "3.14"},
        checks=(TrialCheck("example", "passed", 1, "ok", {}),),
        friction=(), recovery_commands=("python -m aegis_os doctor",),
    )
    output = tmp_path / "trial" / "report.json"
    write_trial_report(report, output)
    payload = json.loads(output.read_text())
    assert payload["overall_status"] == "passed"
    assert payload["checks"][0]["name"] == "example"


def test_occupied_port_is_observable():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        assert listener.getsockname()[1] > 0
