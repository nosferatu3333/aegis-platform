from datetime import UTC, datetime

import pytest

from aegis_core.contracts import CompletionState, EvidenceState, ExecutionStatus as CoreStatus
from aegis_os.execution.execution_engine import ExecutionEngine
from aegis_os.execution.models import ExecutionRequest, ExecutionStatus
from aegis_os.execution.reconciliation import (
    ExecutionResultReconciler,
    ReconciliationOutcome,
)

NOW = datetime(2026, 8, 2, 16, 0, tzinfo=UTC)


def request(*descriptions):
    return ExecutionRequest(
        request_id="req_1234567890abcdef",
        mission="Perform bounded work",
        selected_agent="Execution Agent",
        workflow_steps=[
            {
                "order": index,
                "step_id": f"stp_{index:016d}",
                "title": f"Step {index}",
                "description": description,
            }
            for index, description in enumerate(descriptions or ("Do work",), 1)
        ],
        metadata={"canonical_plan_id": "pln_1234567890abcdef"},
    )


def reconcile(*descriptions):
    receipt = ExecutionEngine(clock=lambda: NOW).execute(request(*descriptions))
    return ExecutionResultReconciler(clock=lambda: NOW).reconcile(receipt)


def test_completed_receipt_creates_verified_result_evidence_and_trace():
    reconciled = reconcile("First", "Second")

    assert reconciled.outcome is ReconciliationOutcome.COMPLETE
    assert reconciled.result.completion_state is CompletionState.COMPLETE
    assert reconciled.result.evidence_state is EvidenceState.VERIFIED
    assert len(reconciled.evidence) == 3
    assert reconciled.trace.is_complete_result_trace is True
    assert set(reconciled.result.evidence_ids) == set(reconciled.trace.evidence_ids)
    assert all(item.status is CoreStatus.SUCCEEDED for item in reconciled.step_results)


def test_simulated_result_preserves_real_world_limitation():
    reconciled = reconcile("Do work")

    assert any("simulated" in item.lower() for item in reconciled.result.limitations)
    assert all(item.verification_state.value == "verified" for item in reconciled.evidence)


def test_failed_receipt_never_reconciles_as_complete():
    reconciled = reconcile("First", "[simulate-failure]", "Never")

    assert reconciled.outcome is ReconciliationOutcome.FAILED
    assert reconciled.result.completion_state is CompletionState.FAILED
    assert [item.status for item in reconciled.step_results] == [
        CoreStatus.SUCCEEDED,
        CoreStatus.FAILED,
        CoreStatus.SKIPPED,
    ]
    assert reconciled.result.limitations


def test_receipt_preserves_canonical_step_ids_and_plan_lineage():
    receipt = ExecutionEngine(clock=lambda: NOW).execute(request("Do work"))

    assert receipt.steps[0].step_id == "stp_0000000000000001"
    assert receipt.metadata["canonical_plan_id"] == "pln_1234567890abcdef"


def test_non_terminal_receipt_is_rejected():
    receipt = ExecutionEngine(clock=lambda: NOW).execute(request("Do work"))
    receipt.status = ExecutionStatus.RUNNING

    with pytest.raises(ValueError, match="terminal"):
        ExecutionResultReconciler().reconcile(receipt)


def test_missing_plan_lineage_is_rejected():
    receipt = ExecutionEngine(clock=lambda: NOW).execute(request("Do work"))
    receipt.metadata.clear()

    with pytest.raises(ValueError, match="canonical_plan_id"):
        ExecutionResultReconciler().reconcile(receipt)
