from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class TaskComplexity(str, Enum):
    """Estimated structural complexity of an incoming mission."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskLevel(str, Enum):
    """Initial operational risk estimate."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PipelineStatus(str, Enum):
    """Current state of a cognitive request."""

    RECEIVED = "received"
    ANALYZED = "analyzed"
    READY = "ready"
    FAILED = "failed"


@dataclass(frozen=True)
class IntentAnalysis:
    """Structured interpretation of an incoming mission."""

    primary_intent: str
    secondary_intents: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    detected_concepts: tuple[str, ...] = ()
    complexity: TaskComplexity = TaskComplexity.LOW
    risk: RiskLevel = RiskLevel.LOW
    requires_planning: bool = False
    requires_execution: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityMatch:
    """Serializable representation of a capability-selection result."""

    capability_id: str
    name: str
    confidence: float
    score: float
    reasons: tuple[str, ...] = ()
    matched_tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Capability confidence must be between 0.0 and 1.0.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WorkflowStep:
    """One visible step in the proposed execution workflow."""

    order: int
    title: str
    description: str
    capability_id: str | None = None
    status: str = "pending"

    def __post_init__(self) -> None:
        if self.order < 1:
            raise ValueError("Workflow step order must begin at 1.")

        if not self.title.strip():
            raise ValueError("Workflow step title cannot be empty.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CognitiveRequestResult:
    """Stable response contract returned by the request pipeline."""

    task: str
    intent: IntentAnalysis
    capability: CapabilityMatch
    workflow: list[WorkflowStep] = field(default_factory=list)
    status: PipelineStatus = PipelineStatus.READY
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task": self.task,
            "intent": self.intent.to_dict(),
            "capability": self.capability.to_dict(),
            "workflow": [step.to_dict() for step in self.workflow],
            "status": self.status.value,
            "metadata": self.metadata,
        }
