"""Operator-facing lifecycle helpers for the AEGIS Platform distribution."""

from __future__ import annotations

import json
import socket
from dataclasses import asdict, dataclass
from pathlib import Path

from aegis_os.release import PLATFORM_VERSION, build_diagnostic_report


@dataclass(frozen=True)
class OperatorReadiness:
    status: str
    platform_version: str
    host: str
    port: int
    endpoint: str
    diagnostics: dict[str, object]
    limitations: tuple[str, ...]

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, sort_keys=True)


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        try:
            probe.bind((host, port))
        except OSError:
            return False
    return True


def build_operator_readiness(host: str = "127.0.0.1", port: int = 8000) -> OperatorReadiness:
    diagnostics = build_diagnostic_report()
    available = port_available(host, port)
    status = "ready" if diagnostics.status == "ready" and available else "blocked"
    limitations = (
        "Execution is deterministic simulation only.",
        "Real-world side effects are not verified by this release.",
    )
    return OperatorReadiness(
        status=status,
        platform_version=PLATFORM_VERSION,
        host=host,
        port=port,
        endpoint=f"http://{host}:{port}",
        diagnostics=diagnostics.to_dict(),
        limitations=limitations,
    )


def repository_root() -> Path:
    return Path(__file__).resolve().parents[1]
