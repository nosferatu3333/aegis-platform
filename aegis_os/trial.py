"""Fresh-machine operator-trial orchestration and evidence reporting."""

from __future__ import annotations

import json
import platform
import socket
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from aegis_os.operator import build_operator_readiness
from aegis_os.release import PLATFORM_VERSION, build_diagnostic_report
from aegis_os.transparency import build_trust_report
from scripts.release_acceptance import run_acceptance

TRIAL_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class TrialCheck:
    name: str
    status: str
    duration_ms: int
    detail: str
    evidence: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OperatorTrialReport:
    schema_version: str
    platform_version: str
    overall_status: str
    started_at_epoch_ms: int
    duration_ms: int
    environment: dict[str, str]
    checks: tuple[TrialCheck, ...]
    friction: tuple[str, ...]
    recovery_commands: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return self.overall_status == "passed"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["checks"] = [check.to_dict() for check in self.checks]
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_text(self) -> str:
        lines = [
            f"AEGIS Platform {self.platform_version} operator trial: {self.overall_status.upper()}",
            f"Duration: {self.duration_ms} ms",
        ]
        for check in self.checks:
            lines.append(
                f"[{check.status.upper()}] {check.name} ({check.duration_ms} ms): {check.detail}"
            )
        for item in self.friction:
            lines.append(f"FRICTION: {item}")
        return "\n".join(lines)


def _timed_check(name: str, operation: Callable[[], tuple[bool, str, dict[str, Any]]]) -> TrialCheck:
    started = time.perf_counter_ns()
    try:
        passed, detail, evidence = operation()
        status = "passed" if passed else "failed"
    except Exception as error:  # operator report must preserve failure evidence
        status = "failed"
        detail = f"{type(error).__name__}: {error}"
        evidence = {"exception_type": type(error).__name__}
    duration_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)
    return TrialCheck(name, status, duration_ms, detail, evidence)


def _diagnostic_check() -> tuple[bool, str, dict[str, Any]]:
    report = build_diagnostic_report()
    return report.status == "ready", report.status, report.to_dict()


def _readiness_check(host: str, port: int) -> tuple[bool, str, dict[str, Any]]:
    report = build_operator_readiness(host, port)
    return report.status == "ready", report.status, json.loads(report.to_json())


def _governed_scenarios_check() -> tuple[bool, str, dict[str, Any]]:
    report = run_acceptance()
    detail = f"{report['scenario_count']} governed scenarios"
    return bool(report["accepted"]), detail, report


def _occupied_port_check(host: str) -> tuple[bool, str, dict[str, Any]]:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind((host, 0))
        listener.listen(1)
        port = int(listener.getsockname()[1])
        readiness = build_operator_readiness(host, port)
    passed = readiness.status == "blocked"
    return passed, f"occupied port {port} produced {readiness.status}", json.loads(readiness.to_json())


def _trust_check(
    bundle: Path,
    attestation: Path,
    signature: Path,
    policy: Path,
    ledger: Path | None,
) -> tuple[bool, str, dict[str, Any]]:
    report = build_trust_report(bundle, attestation, signature, policy, ledger)
    return report.overall_verdict == "TRUSTED", report.overall_verdict, report.to_dict()


def run_operator_trial(
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
    bundle: Path | None = None,
    attestation: Path | None = None,
    signature: Path | None = None,
    policy: Path | None = None,
    ledger: Path | None = None,
) -> OperatorTrialReport:
    """Run deterministic deployment-rehearsal checks and return auditable evidence."""

    started_epoch_ms = int(time.time() * 1000)
    started = time.perf_counter_ns()
    checks = [
        _timed_check("runtime-diagnostics", _diagnostic_check),
        _timed_check("operator-readiness", lambda: _readiness_check(host, port)),
        _timed_check("governed-acceptance-scenarios", _governed_scenarios_check),
        _timed_check("occupied-port-blocking", lambda: _occupied_port_check(host)),
    ]

    trust_arguments = (bundle, attestation, signature, policy)
    if any(value is not None for value in trust_arguments):
        if not all(value is not None for value in trust_arguments):
            checks.append(
                TrialCheck(
                    "release-trust-verification",
                    "failed",
                    0,
                    "bundle, attestation, signature, and policy must be supplied together",
                    {},
                )
            )
        else:
            checks.append(
                _timed_check(
                    "release-trust-verification",
                    lambda: _trust_check(
                        bundle, attestation, signature, policy, ledger  # type: ignore[arg-type]
                    ),
                )
            )

    failed = [check.name for check in checks if check.status != "passed"]
    friction: list[str] = []
    diagnostics = checks[0]
    if diagnostics.status != "passed":
        friction.append("Runtime dependencies or Core compatibility require remediation.")
    readiness = checks[1]
    if readiness.status != "passed":
        friction.append(f"Requested launch endpoint {host}:{port} is not ready.")
    if "release-trust-verification" not in {check.name for check in checks}:
        friction.append("Trust verification was not exercised because release artifacts were not supplied.")

    duration_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)
    return OperatorTrialReport(
        schema_version=TRIAL_SCHEMA_VERSION,
        platform_version=PLATFORM_VERSION,
        overall_status="passed" if not failed else "failed",
        started_at_epoch_ms=started_epoch_ms,
        duration_ms=duration_ms,
        environment={
            "python": platform.python_version(),
            "platform": platform.platform(),
            "interpreter": str(Path(sys.executable).resolve()),
        },
        checks=tuple(checks),
        friction=tuple(friction),
        recovery_commands=(
            "python -m aegis_os doctor",
            f"python -m aegis_os ready --host {host} --port {port}",
            "python -m pytest",
        ),
    )


def write_trial_report(report: OperatorTrialReport, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.to_json() + "\n", encoding="utf-8", newline="\n")
