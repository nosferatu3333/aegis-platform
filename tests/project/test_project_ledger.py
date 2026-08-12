from __future__ import annotations

from dataclasses import FrozenInstanceError, fields

import pytest

from aegis_os.intent import IntentInterpreter, IntentRequest, OutcomeModeler
from aegis_os.project import (
    LedgerRecord,
    LedgerRecordType,
    ProjectLedger,
    ProjectStateManager,
)


def _project():
    interpretation = IntentInterpreter().interpret(
        IntentRequest(
            raw_request="Create a one-page proposal.",
            explicit_constraints=("one page",),
        )
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-ledger",
    )

    return ProjectStateManager().create(
        outcome,
        project_id="project-ledger",
    )


def test_ledger_record_has_exact_seven_dimensions() -> None:
    assert tuple(field.name for field in fields(LedgerRecord)) == (
        "record_id",
        "project_ref",
        "record_type",
        "summary",
        "rationale",
        "affected_state_ref",
        "sequence",
    )


def test_ledger_record_type_has_exact_two_values() -> None:
    assert tuple(item.value for item in LedgerRecordType) == (
        "REVISION",
        "DECISION",
    )


def test_first_record_sequence_is_one() -> None:
    project = _project()
    ledger = ProjectLedger(project.project_id)

    record = ledger.append(
        record_id="record-001",
        record_type=LedgerRecordType.REVISION,
        summary="Initial project state recorded.",
        rationale="Establish bounded project history.",
        affected_state=project,
    )

    assert record.sequence == 1
    assert ledger.records == (record,)


def test_sequence_is_monotonic() -> None:
    project = _project()
    ledger = ProjectLedger(project.project_id)

    first = ledger.append(
        record_id="record-001",
        record_type=LedgerRecordType.REVISION,
        summary="Initial project state recorded.",
        rationale="Initial history.",
        affected_state=project,
    )

    second = ledger.append(
        record_id="record-002",
        record_type=LedgerRecordType.DECISION,
        summary="Proceed with architecture review.",
        rationale="Architecture review is the next bounded step.",
        affected_state=project,
    )

    assert first.sequence == 1
    assert second.sequence == 2
    assert ledger.records == (first, second)


def test_records_are_immutable() -> None:
    project = _project()
    ledger = ProjectLedger(project.project_id)

    record = ledger.append(
        record_id="record-001",
        record_type=LedgerRecordType.REVISION,
        summary="Initial state.",
        rationale="History.",
        affected_state=project,
    )

    with pytest.raises(FrozenInstanceError):
        record.summary = "Changed"  # type: ignore[misc]


def test_append_does_not_mutate_project_state() -> None:
    project = _project()
    before = project.to_dict()

    ledger = ProjectLedger(project.project_id)

    ledger.append(
        record_id="record-001",
        record_type=LedgerRecordType.DECISION,
        summary="Retain current project state.",
        rationale="No state mutation is authorized.",
        affected_state=project,
    )

    assert project.to_dict() == before


def test_duplicate_record_id_is_rejected() -> None:
    project = _project()
    ledger = ProjectLedger(project.project_id)

    ledger.append(
        record_id="record-001",
        record_type=LedgerRecordType.REVISION,
        summary="Initial record.",
        rationale="History.",
        affected_state=project,
    )

    with pytest.raises(ValueError, match="unique"):
        ledger.append(
            record_id="record-001",
            record_type=LedgerRecordType.DECISION,
            summary="Duplicate identifier.",
            rationale="Should fail.",
            affected_state=project,
        )


def test_cross_project_state_is_rejected() -> None:
    project = _project()

    interpretation = IntentInterpreter().interpret(
        IntentRequest(raw_request="Create another proposal.")
    )

    outcome = OutcomeModeler().model(
        interpretation,
        intent_ref="intent-other",
    )

    other = ProjectStateManager().create(
        outcome,
        project_id="project-other",
    )

    ledger = ProjectLedger(project.project_id)

    with pytest.raises(ValueError, match="match ledger project_ref"):
        ledger.append(
            record_id="record-001",
            record_type=LedgerRecordType.REVISION,
            summary="Wrong project.",
            rationale="Should fail.",
            affected_state=other,
        )


def test_record_serialization_contains_no_authority_or_execution() -> None:
    project = _project()
    ledger = ProjectLedger(project.project_id)

    record = ledger.append(
        record_id="record-001",
        record_type=LedgerRecordType.DECISION,
        summary="Proceed with review.",
        rationale="Review is appropriate.",
        affected_state=project,
    )

    payload = record.to_dict()

    forbidden = {
        "authority",
        "approval",
        "execution_permission",
        "governed_verdict",
        "reasoning_mode",
        "candidate_paths",
        "lifecycle_transition",
        "transition_allowed",
        "execution_result",
        "tool",
        "memory",
    }

    assert forbidden.isdisjoint(payload)


def test_ledger_is_deterministic_for_same_inputs() -> None:
    project = _project()

    def build():
        ledger = ProjectLedger(project.project_id)

        first = ledger.append(
            record_id="record-001",
            record_type=LedgerRecordType.REVISION,
            summary="Initial state.",
            rationale="History.",
            affected_state=project,
        )

        second = ledger.append(
            record_id="record-002",
            record_type=LedgerRecordType.DECISION,
            summary="Proceed with review.",
            rationale="Bounded next decision.",
            affected_state=project,
        )

        return tuple(record.to_dict() for record in (first, second))

    baseline = build()

    for _ in range(100):
        assert build() == baseline
