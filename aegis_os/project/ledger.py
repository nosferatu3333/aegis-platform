"""Bounded revision and decision ledger contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .models import ProjectState


class LedgerRecordType(str, Enum):
    """Bounded ledger record classification."""

    REVISION = "REVISION"
    DECISION = "DECISION"


@dataclass(frozen=True, slots=True)
class LedgerRecord:
    """Immutable historical project record."""

    record_id: str
    project_ref: str
    record_type: LedgerRecordType
    summary: str
    rationale: str
    affected_state_ref: str
    sequence: int

    def __post_init__(self) -> None:
        for name, value in (
            ("record_id", self.record_id),
            ("project_ref", self.project_ref),
            ("summary", self.summary),
            ("affected_state_ref", self.affected_state_ref),
        ):
            if not isinstance(value, str) or not value.strip():
                raise TypeError(f"{name} must be a non-empty string")

        if not isinstance(self.rationale, str):
            raise TypeError("rationale must be a string")

        if not isinstance(self.record_type, LedgerRecordType):
            raise TypeError("record_type must be a LedgerRecordType")

        if (
            isinstance(self.sequence, bool)
            or not isinstance(self.sequence, int)
            or self.sequence < 1
        ):
            raise TypeError("sequence must be an integer >= 1")

    def to_dict(self) -> dict[str, object]:
        """Return deterministic serialization."""
        return {
            "record_id": self.record_id,
            "project_ref": self.project_ref,
            "record_type": self.record_type.value,
            "summary": self.summary,
            "rationale": self.rationale,
            "affected_state_ref": self.affected_state_ref,
            "sequence": self.sequence,
        }


class ProjectLedger:
    """Bounded in-memory append-only project ledger."""

    def __init__(self, project_ref: str) -> None:
        if not isinstance(project_ref, str) or not project_ref.strip():
            raise TypeError("project_ref must be a non-empty string")

        self._project_ref = project_ref
        self._records: tuple[LedgerRecord, ...] = ()

    @property
    def project_ref(self) -> str:
        return self._project_ref

    @property
    def records(self) -> tuple[LedgerRecord, ...]:
        return self._records

    def append(
        self,
        *,
        record_id: str,
        record_type: LedgerRecordType,
        summary: str,
        rationale: str,
        affected_state: ProjectState,
    ) -> LedgerRecord:
        """Append one immutable record without mutating project state."""
        if not isinstance(affected_state, ProjectState):
            raise TypeError("affected_state must be a ProjectState")

        if affected_state.project_id != self._project_ref:
            raise ValueError("affected_state project_id must match ledger project_ref")

        if not isinstance(record_type, LedgerRecordType):
            raise TypeError("record_type must be a LedgerRecordType")

        if any(record.record_id == record_id for record in self._records):
            raise ValueError("record_id must be unique within a project ledger")

        sequence = len(self._records) + 1

        record = LedgerRecord(
            record_id=record_id,
            project_ref=self._project_ref,
            record_type=record_type,
            summary=summary,
            rationale=rationale,
            affected_state_ref=affected_state.project_id,
            sequence=sequence,
        )

        self._records = (*self._records, record)

        return record
