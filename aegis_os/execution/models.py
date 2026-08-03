from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

EXECUTION_SCHEMA_VERSION = "1.0"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionMode(str, Enum):
    SIMULATED = "simulated"


class ExecutionStepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionRequest:
    request_id: str
    mission: str
    selected_agent: str
    execution_mode: ExecutionMode = ExecutionMode.SIMULATED
    required_capabilities: list[str] = field(default_factory=list)
    workflow_steps: list[Any] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "mission": self.mission,
            "selected_agent": self.selected_agent,
            "execution_mode": self.execution_mode.value,
            "required_capabilities": list(self.required_capabilities),
            "workflow_steps": [
                step.to_dict() if hasattr(step, "to_dict") else step
                for step in self.workflow_steps
            ],
            "constraints": list(self.constraints),
            "permissions": list(self.permissions),
            "metadata": dict(self.metadata),
        }


@dataclass
class ExecutionStep:
    step_id: str
    order: int
    description: str
    status: ExecutionStepStatus = ExecutionStepStatus.PENDING
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["status"] = self.status.value
        return payload


@dataclass
class ExecutionReceipt:
    request_id: str
    mission: str
    selected_agent: str
    execution_mode: ExecutionMode = ExecutionMode.SIMULATED
    status: ExecutionStatus = ExecutionStatus.PENDING
    steps: list[ExecutionStep] = field(default_factory=list)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    completed_steps: int = 0
    failed_steps: int = 0
    logs: list[str] = field(default_factory=list)
    simulated: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    schema_version: str = EXECUTION_SCHEMA_VERSION

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "request_id": self.request_id,
            "mission": self.mission,
            "selected_agent": self.selected_agent,
            "execution_mode": self.execution_mode.value,
            "status": self.status.value,
            "steps": [step.to_dict() for step in self.steps],
            "started_at": (self.started_at.isoformat() if self.started_at else None),
            "finished_at": (self.finished_at.isoformat() if self.finished_at else None),
            "completed_steps": self.completed_steps,
            "failed_steps": self.failed_steps,
            "logs": list(self.logs),
            "simulated": self.simulated,
            "schema_version": self.schema_version,
        }
        return payload
