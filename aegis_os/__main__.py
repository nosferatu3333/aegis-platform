"""Command-line entry point for the AEGIS Platform release candidate."""

from __future__ import annotations

import argparse
import subprocess
import sys

from aegis_os.release import build_diagnostic_report


def _doctor(json_output: bool) -> int:
    report = build_diagnostic_report()
    if json_output:
        print(report.to_json())
    else:
        print(f"AEGIS Platform {report.platform_version}: {report.status}")
        print(f"Python: {report.python_version}")
        print(f"Interpreter: {report.interpreter}")
        for check in report.checks:
            print(f"[{check.status.upper()}] {check.name}: {check.detail}")
    return 0 if report.status == "ready" else 2


def _serve(host: str, port: int, reload: bool) -> int:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "aegis_os.api.app:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if reload:
        command.append("--reload")
    return subprocess.call(command)


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m aegis_os")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Validate the local runtime.")
    doctor.add_argument("--json", action="store_true", dest="json_output")

    serve = subparsers.add_parser("serve", help="Start the local API and dashboard.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", default=8000, type=int)
    serve.add_argument("--reload", action="store_true")

    arguments = parser.parse_args()
    if arguments.command == "doctor":
        return _doctor(arguments.json_output)
    return _serve(arguments.host, arguments.port, arguments.reload)


if __name__ == "__main__":
    raise SystemExit(main())
