from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

import aegis_os.system as system_package
from aegis_os.intent import (
    IntentAmbiguity,
    IntentInterpretation,
    IntentRequest,
    IntentType,
    OutcomeModeler,
)
from aegis_os.project import ProjectState, ProjectStateManager, ProjectStatus
from aegis_os.reasoning import (
    AdaptiveCycleResult,
    AdaptiveReasoningCycle,
    CandidateEvaluation,
    CandidateEvaluator,
    CandidatePath,
    CandidatePathGenerator,
    ConvergenceController,
    ConvergenceResult,
    ConvergenceStatus,
    EscalationDecision,
    ReasoningMode,
)
from aegis_os.system import (
    CognitiveCycle,
    CognitiveCycleRequest,
    CognitiveCycleResult,
    CycleDisposition,
    NextInteraction,
    ProjectContext,
    ProjectContextMode,
    ReasoningHandoffResult,
)

EXPECTED_EXPORTS = [
    "CognitiveCycle",
    "CognitiveCycleRequest",
    "CognitiveCycleResult",
    "CycleDisposition",
    "NextInteraction",
    "ProjectContext",
    "ProjectContextMode",
    "ReasoningHandoffResult",
]


class RecordingIntentInterpreter:
    def __init__(self, interpretation: IntentInterpretation) -> None:
        self.interpretation = interpretation
        self.calls: list[IntentRequest] = []

    def interpret(self, request: IntentRequest) -> IntentInterpretation:
        self.calls.append(request)
        return self.interpretation


class RecordingOutcomeModeler:
    def __init__(self) -> None:
        self.calls: list[tuple[IntentInterpretation, dict[str, object]]] = []

    def model(
        self,
        interpretation: IntentInterpretation,
        **kwargs: object,
    ):
        self.calls.append((interpretation, kwargs))
        return OutcomeModeler().model(interpretation, **kwargs)


class RecordingProjectStateManager:
    def __init__(self) -> None:
        self.calls: list[tuple[object, str]] = []

    def create(self, outcome: object, *, project_id: str) -> ProjectState:
        self.calls.append((outcome, project_id))
        return ProjectStateManager().create(outcome, project_id=project_id)


class RecordingReasoningCycle:
    def __init__(self, result: AdaptiveCycleResult) -> None:
        self.result = result
        self.calls = []

    def run(self, request):
        self.calls.append(request)
        return self.result


def interpretation(
    *,
    inferred_constraints: tuple[str, ...] = ("inferred",),
    clarification_required: bool = False,
) -> IntentInterpretation:
    ambiguities = (
        (
            IntentAmbiguity(
                code="MISSING_TARGET",
                description="A target is required.",
                blocking=True,
                question="Which target should be used?",
            ),
        )
        if clarification_required
        else ()
    )
    return IntentInterpretation(
        raw_request="Create a bounded plan",
        interpreted_intent="Create a bounded plan",
        intent_type=IntentType.CREATE,
        explicit_constraints=("explicit", "shared"),
        inferred_constraints=inferred_constraints,
        ambiguities=ambiguities,
        clarification_required=clarification_required,
        clarification_questions=("Which target should be used?",)
        if clarification_required
        else (),
    )


def existing_state(status: ProjectStatus = ProjectStatus.BLOCKED) -> ProjectState:
    return ProjectState(
        project_id="project-1",
        outcome_ref="intent-1",
        status=status,
        current_state="Awaiting bounded input.",
        active_constraints=("shared", "project-only"),
        unresolved_issues=("outcome-uncertainty", "project-issue"),
    )


def cycle_request(
    context: ProjectContext | None = None,
) -> CognitiveCycleRequest:
    return CognitiveCycleRequest(
        cycle_id="cycle-1",
        reasoning_request_id="reasoning-1",
        intent_ref="intent-1",
        intent_request=IntentRequest(
            raw_request="Create a bounded plan",
            explicit_constraints=("explicit", "shared"),
        ),
        project_context=context or ProjectContext(mode=ProjectContextMode.TRANSIENT),
        success_conditions=("bounded result",),
        outcome_uncertainties=("outcome-uncertainty",),
        risk_signals=("risk",),
        requested_depth=2,
        budget=3,
    )


def adaptive_result(mode: ReasoningMode) -> AdaptiveCycleResult:
    return AdaptiveCycleResult(
        mode=mode,
        candidates=(),
        evaluations=(),
        convergence=None,
        reason=f"{mode.value} bounded result",
    )


def branch_result(status: ConvergenceStatus) -> AdaptiveCycleResult:
    candidates = tuple(
        CandidatePath(
            candidate_id=f"candidate-{index}",
            intent_ref="intent-1",
            outcome_ref="intent-1",
            label="Direct-Outcome",
            summary=f"Candidate {index}",
            primary_objective="Produce a bounded result.",
            assumptions=(),
            constraints_acknowledged=(),
            evidence_needs=(),
            known_uncertainty=(),
        )
        for index in (1, 2)
    )
    evaluations = tuple(
        CandidateEvaluation(
            candidate_id=candidate.candidate_id,
            constraint_alignment=2,
            evidence_readiness=2,
            uncertainty_exposure=2,
            risk_exposure=2,
            dependency_burden=2,
            directness=2,
            aggregate_score=12,
            strengths=(),
            limitations=(),
        )
        for candidate in candidates
    )
    preferred = "candidate-1" if status is ConvergenceStatus.RESOLVED else None
    eligible = (
        ("candidate-1",)
        if status is not ConvergenceStatus.TIED
        else (
            "candidate-1",
            "candidate-2",
        )
    )
    return AdaptiveCycleResult(
        mode=ReasoningMode.BRANCH,
        candidates=candidates,
        evaluations=evaluations,
        convergence=ConvergenceResult(
            status=status,
            preferred_candidate_id=preferred,
            eligible_candidate_ids=eligible,
            reason="Bounded convergence result.",
        ),
        reason="One bounded branch pass.",
    )


def configured_cycle(
    *,
    result: AdaptiveCycleResult | None = None,
    interpreted: IntentInterpretation | None = None,
):
    intent = RecordingIntentInterpreter(interpreted or interpretation())
    outcome = RecordingOutcomeModeler()
    project = RecordingProjectStateManager()
    reasoning = RecordingReasoningCycle(result or adaptive_result(ReasoningMode.DIRECT))
    cycle = CognitiveCycle(
        intent_interpreter=intent,
        outcome_modeler=outcome,
        project_state_manager=project,
        reasoning_cycle=reasoning,
    )
    return cycle, intent, outcome, project, reasoning


def test_package_exports_are_exact_and_ordered() -> None:
    assert system_package.__all__ == EXPECTED_EXPORTS
    assert all(hasattr(system_package, name) for name in EXPECTED_EXPORTS)


def test_frozen_enum_values_are_exact() -> None:
    assert [mode.value for mode in ProjectContextMode] == [
        "TRANSIENT",
        "CREATE_NEW",
        "EXISTING",
    ]
    assert [item.value for item in CycleDisposition] == [
        "CLARIFICATION_REQUIRED",
        "TRANSIENT_REASONING_RESULT",
        "PROJECT_REASONING_RESULT",
        "REASONING_TIED",
        "REASONING_INSUFFICIENT",
        "SEARCH_REQUIRED_SIGNAL",
        "VERIFY_REQUIRED_SIGNAL",
    ]
    assert [item.value for item in NextInteraction] == [
        "NONE",
        "USER_CLARIFICATION",
        "USER_DECISION",
        "EVIDENCE_COORDINATION",
        "SEARCH_COORDINATION",
    ]


def test_dataclass_field_order_is_frozen() -> None:
    assert [field.name for field in fields(CognitiveCycleRequest)] == [
        "cycle_id",
        "reasoning_request_id",
        "intent_ref",
        "intent_request",
        "project_context",
        "success_conditions",
        "outcome_uncertainties",
        "risk_signals",
        "requested_depth",
        "budget",
    ]
    assert [field.name for field in fields(ProjectContext)] == [
        "mode",
        "new_project_id",
        "existing_state",
    ]
    assert [field.name for field in fields(ReasoningHandoffResult)] == [
        "reasoning_request_id",
        "adaptive_result",
    ]
    assert [field.name for field in fields(CognitiveCycleResult)] == [
        "cycle_id",
        "intent_ref",
        "disposition",
        "interpretation",
        "clarification_required",
        "clarification_questions",
        "outcome",
        "project_context_mode",
        "current_project_state",
        "reasoning_request",
        "reasoning",
        "next_interaction",
    ]


def test_request_context_and_result_are_immutable() -> None:
    request = cycle_request()
    with pytest.raises(FrozenInstanceError):
        request.cycle_id = "changed"
    with pytest.raises(FrozenInstanceError):
        request.project_context.mode = ProjectContextMode.EXISTING

    result = configured_cycle()[0].run(request)
    with pytest.raises(FrozenInstanceError):
        result.disposition = CycleDisposition.REASONING_TIED


@pytest.mark.parametrize(
    "field_name", ["cycle_id", "reasoning_request_id", "intent_ref"]
)
@pytest.mark.parametrize("invalid", ["", "   ", None, 3])
def test_request_rejects_invalid_ids(field_name: str, invalid: object) -> None:
    with pytest.raises(TypeError):
        replace(cycle_request(), **{field_name: invalid})


@pytest.mark.parametrize(
    ("field_name", "invalid"),
    [
        ("success_conditions", ["condition"]),
        ("success_conditions", ("",)),
        ("outcome_uncertainties", (1,)),
        ("risk_signals", "risk"),
    ],
)
def test_request_rejects_invalid_string_tuples(
    field_name: str,
    invalid: object,
) -> None:
    with pytest.raises(TypeError):
        replace(cycle_request(), **{field_name: invalid})


@pytest.mark.parametrize("invalid", [True, 1.5, "1"])
def test_request_rejects_non_integer_depth(invalid: object) -> None:
    with pytest.raises(TypeError):
        replace(cycle_request(), requested_depth=invalid)


def test_request_rejects_negative_depth() -> None:
    with pytest.raises(ValueError):
        replace(cycle_request(), requested_depth=-1)


@pytest.mark.parametrize("invalid", [False, 1.5, "1"])
def test_request_rejects_non_integer_budget(invalid: object) -> None:
    with pytest.raises(TypeError):
        replace(cycle_request(), budget=invalid)


def test_request_rejects_budget_below_one() -> None:
    with pytest.raises(ValueError):
        replace(cycle_request(), budget=0)


def test_request_has_no_inferred_constraint_or_prohibited_control_fields() -> None:
    names = {field.name for field in fields(CognitiveCycleRequest)}
    assert "inferred_constraints" not in names
    assert not names.intersection(
        {
            "authority",
            "execution_permission",
            "memory",
            "project_change",
            "tool_permission",
        }
    )
    with pytest.raises(TypeError):
        CognitiveCycleRequest(
            **cycle_request().to_dict(),
            inferred_constraints=("caller-inference",),
        )


@pytest.mark.parametrize(
    "context",
    [
        ProjectContext(mode=ProjectContextMode.TRANSIENT),
        ProjectContext(
            mode=ProjectContextMode.CREATE_NEW,
            new_project_id="new-project",
        ),
        ProjectContext(
            mode=ProjectContextMode.EXISTING,
            existing_state=existing_state(),
        ),
    ],
)
def test_exact_project_context_forms_are_valid(context: ProjectContext) -> None:
    assert context.mode in ProjectContextMode


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": ProjectContextMode.TRANSIENT, "new_project_id": "new"},
        {"mode": ProjectContextMode.TRANSIENT, "existing_state": existing_state()},
        {"mode": ProjectContextMode.CREATE_NEW},
        {"mode": ProjectContextMode.CREATE_NEW, "new_project_id": " "},
        {
            "mode": ProjectContextMode.CREATE_NEW,
            "new_project_id": "new",
            "existing_state": existing_state(),
        },
        {"mode": ProjectContextMode.EXISTING},
        {
            "mode": ProjectContextMode.EXISTING,
            "new_project_id": "new",
            "existing_state": existing_state(),
        },
    ],
)
def test_project_context_rejects_contradictory_combinations(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        ProjectContext(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"mode": "TRANSIENT"},
        {"mode": ProjectContextMode.CREATE_NEW, "new_project_id": 3},
        {"mode": ProjectContextMode.EXISTING, "existing_state": object()},
    ],
)
def test_project_context_rejects_wrong_types(kwargs: dict) -> None:
    with pytest.raises(TypeError):
        ProjectContext(**kwargs)


def test_clarification_gate_blocks_all_downstream_calls() -> None:
    cycle, intent, outcome, project, reasoning = configured_cycle(
        interpreted=interpretation(clarification_required=True)
    )
    result = cycle.run(cycle_request())

    assert len(intent.calls) == 1
    assert outcome.calls == []
    assert project.calls == []
    assert reasoning.calls == []
    assert result.disposition is CycleDisposition.CLARIFICATION_REQUIRED
    assert result.next_interaction is NextInteraction.USER_CLARIFICATION
    assert result.clarification_required is True
    assert result.clarification_questions == ("Which target should be used?",)
    assert result.outcome is None
    assert result.current_project_state is None
    assert result.reasoning_request is None
    assert result.reasoning is None


def test_constraint_provenance_and_reasoning_mapping_are_exact() -> None:
    cycle, intent, outcome, project, reasoning = configured_cycle(
        interpreted=interpretation(inferred_constraints=("inferred", "shared"))
    )
    original = existing_state()
    request = cycle_request(
        ProjectContext(
            mode=ProjectContextMode.EXISTING,
            existing_state=original,
        )
    )
    result = cycle.run(request)

    assert len(intent.calls) == 1
    assert len(outcome.calls) == 1
    assert outcome.calls[0][1]["inferred_constraints"] == (
        "inferred",
        "shared",
    )
    assert project.calls == []
    assert len(reasoning.calls) == 1
    mapped = reasoning.calls[0]
    assert mapped.reasoning_request_id == request.reasoning_request_id
    assert mapped.intent_ref == request.intent_ref
    assert mapped.outcome_ref == request.intent_ref
    assert mapped.project_context_ref == original.project_id
    assert mapped.uncertainty_signals == (
        "outcome-uncertainty",
        "project-issue",
    )
    assert mapped.risk_signals == ("risk",)
    assert mapped.constraints == (
        "explicit",
        "shared",
        "inferred",
        "project-only",
    )
    assert mapped.requested_depth == 2
    assert mapped.budget == 3
    assert result.reasoning.reasoning_request_id == request.reasoning_request_id


@pytest.mark.parametrize(
    ("explicit_constraints", "expected"),
    [
        (("x", " x "), ("x",)),
        (("x ", "x"), ("x",)),
        (("a", " b ", "a", "b"), ("a", "b")),
    ],
)
def test_constraint_union_normalizes_before_stable_deduplication(
    explicit_constraints: tuple[str, ...],
    expected: tuple[str, ...],
) -> None:
    interpreted = replace(
        interpretation(inferred_constraints=()),
        explicit_constraints=explicit_constraints,
    )
    cycle, _, _, _, reasoning = configured_cycle(interpreted=interpreted)

    cycle.run(cycle_request())

    assert reasoning.calls[0].constraints == expected


def test_uncertainty_union_normalizes_before_stable_deduplication() -> None:
    cycle, _, _, _, reasoning = configured_cycle()
    request = replace(
        cycle_request(),
        outcome_uncertainties=("u", " u "),
    )

    cycle.run(request)

    assert reasoning.calls[0].uncertainty_signals == ("u",)


def test_mixed_union_preserves_first_normalized_occurrence_order() -> None:
    interpreted = replace(
        interpretation(inferred_constraints=("a", "b", " c ")),
        explicit_constraints=("b", " a ", "b"),
    )
    cycle, _, _, _, reasoning = configured_cycle(interpreted=interpreted)

    cycle.run(cycle_request())

    assert reasoning.calls[0].constraints == ("b", "a", "c")


def test_transient_routes_without_project_creation_or_identity() -> None:
    cycle, _, _, project, reasoning = configured_cycle()
    request = cycle_request()
    result = cycle.run(request)

    assert project.calls == []
    assert result.current_project_state is None
    assert reasoning.calls[0].project_context_ref == request.cycle_id
    assert result.disposition is CycleDisposition.TRANSIENT_REASONING_RESULT


def test_create_new_routes_once_through_cmp04_and_preserves_returned_identity() -> None:
    cycle, _, _, project, reasoning = configured_cycle()
    context = ProjectContext(
        mode=ProjectContextMode.CREATE_NEW,
        new_project_id="new-project",
    )
    result = cycle.run(cycle_request(context))

    assert len(project.calls) == 1
    assert project.calls[0][1] == "new-project"
    assert result.current_project_state is not None
    assert result.current_project_state.project_id == "new-project"
    assert reasoning.calls[0].project_context_ref == "new-project"
    assert result.disposition is CycleDisposition.PROJECT_REASONING_RESULT


def test_existing_uses_exact_state_identity_without_mutation_or_creation() -> None:
    cycle, _, _, project, _ = configured_cycle()
    state = existing_state(ProjectStatus.BLOCKED)
    before = state.to_dict()
    result = cycle.run(
        cycle_request(
            ProjectContext(
                mode=ProjectContextMode.EXISTING,
                existing_state=state,
            )
        )
    )

    assert project.calls == []
    assert result.current_project_state is state
    assert state.to_dict() == before
    assert state.status is ProjectStatus.BLOCKED


@pytest.mark.parametrize(
    ("result", "context", "disposition", "interaction"),
    [
        (
            adaptive_result(ReasoningMode.DIRECT),
            ProjectContext(mode=ProjectContextMode.TRANSIENT),
            CycleDisposition.TRANSIENT_REASONING_RESULT,
            NextInteraction.NONE,
        ),
        (
            adaptive_result(ReasoningMode.DIRECT),
            ProjectContext(
                mode=ProjectContextMode.EXISTING,
                existing_state=existing_state(),
            ),
            CycleDisposition.PROJECT_REASONING_RESULT,
            NextInteraction.NONE,
        ),
        (
            adaptive_result(ReasoningMode.VERIFY),
            ProjectContext(mode=ProjectContextMode.TRANSIENT),
            CycleDisposition.VERIFY_REQUIRED_SIGNAL,
            NextInteraction.EVIDENCE_COORDINATION,
        ),
        (
            adaptive_result(ReasoningMode.SEARCH),
            ProjectContext(mode=ProjectContextMode.TRANSIENT),
            CycleDisposition.SEARCH_REQUIRED_SIGNAL,
            NextInteraction.SEARCH_COORDINATION,
        ),
        (
            branch_result(ConvergenceStatus.RESOLVED),
            ProjectContext(mode=ProjectContextMode.TRANSIENT),
            CycleDisposition.TRANSIENT_REASONING_RESULT,
            NextInteraction.USER_DECISION,
        ),
        (
            branch_result(ConvergenceStatus.RESOLVED),
            ProjectContext(
                mode=ProjectContextMode.EXISTING,
                existing_state=existing_state(),
            ),
            CycleDisposition.PROJECT_REASONING_RESULT,
            NextInteraction.USER_DECISION,
        ),
        (
            branch_result(ConvergenceStatus.TIED),
            ProjectContext(mode=ProjectContextMode.TRANSIENT),
            CycleDisposition.REASONING_TIED,
            NextInteraction.USER_DECISION,
        ),
        (
            branch_result(ConvergenceStatus.INSUFFICIENT),
            ProjectContext(mode=ProjectContextMode.TRANSIENT),
            CycleDisposition.REASONING_INSUFFICIENT,
            NextInteraction.EVIDENCE_COORDINATION,
        ),
    ],
)
def test_reasoning_modes_and_structural_results_map_exactly(
    result: AdaptiveCycleResult,
    context: ProjectContext,
    disposition: CycleDisposition,
    interaction: NextInteraction,
) -> None:
    cycle, _, _, _, reasoning = configured_cycle(result=result)
    cycle_result = cycle.run(cycle_request(context))

    assert len(reasoning.calls) == 1
    assert cycle_result.reasoning.adaptive_result is result
    assert cycle_result.disposition is disposition
    assert cycle_result.next_interaction is interaction


def test_branch_runs_generate_evaluate_and_converge_exactly_once() -> None:
    class BranchPolicy:
        calls = 0

        def select_mode(self, request):
            self.calls += 1
            return EscalationDecision(
                mode=ReasoningMode.BRANCH,
                reason="One bounded branch is required.",
            )

    class Generator:
        calls = 0

        def generate(self, request, *, mode, candidate_count):
            self.calls += 1
            return CandidatePathGenerator().generate(
                request,
                mode=mode,
                candidate_count=candidate_count,
            )

    class Evaluator:
        calls = 0

        def evaluate(self, request, candidates):
            self.calls += 1
            return CandidateEvaluator().evaluate(request, candidates)

    class Converger:
        calls = 0

        def converge(self, request, candidates, evaluations):
            self.calls += 1
            return ConvergenceController().converge(
                request,
                candidates,
                evaluations,
            )

    policy = BranchPolicy()
    generator = Generator()
    evaluator = Evaluator()
    converger = Converger()
    reasoning = AdaptiveReasoningCycle(
        escalation_policy=policy,
        candidate_generator=generator,
        candidate_evaluator=evaluator,
        convergence_controller=converger,
        branch_candidate_count=2,
    )
    _, intent, outcome, project, _ = configured_cycle()
    cycle = CognitiveCycle(
        intent_interpreter=intent,
        outcome_modeler=outcome,
        project_state_manager=project,
        reasoning_cycle=reasoning,
    )

    result = cycle.run(cycle_request())

    assert policy.calls == 1
    assert generator.calls == 1
    assert evaluator.calls == 1
    assert converger.calls == 1
    assert result.reasoning.adaptive_result.mode is ReasoningMode.BRANCH


def test_default_cycle_performs_one_repository_native_bounded_pass() -> None:
    result = CognitiveCycle().run(
        CognitiveCycleRequest(
            cycle_id="default-cycle",
            reasoning_request_id="default-reasoning",
            intent_ref="default-intent",
            intent_request=IntentRequest(raw_request="Explain bounded cognition"),
            project_context=ProjectContext(mode=ProjectContextMode.TRANSIENT),
        )
    )
    assert result.disposition is CycleDisposition.TRANSIENT_REASONING_RESULT
    assert result.reasoning.adaptive_result.mode is ReasoningMode.DIRECT


@pytest.mark.parametrize(
    ("dependency_name", "method_name", "expected_message"),
    [
        (
            "intent_interpreter",
            "interpret",
            "intent interpreter must return an IntentInterpretation",
        ),
        (
            "outcome_modeler",
            "model",
            "outcome modeler must return an OutcomeModel",
        ),
        (
            "project_state_manager",
            "create",
            "project state manager must return a ProjectState",
        ),
        (
            "reasoning_cycle",
            "run",
            "reasoning cycle must return an AdaptiveCycleResult",
        ),
    ],
)
def test_wrong_dependency_artifact_types_raise_explicit_type_errors(
    dependency_name: str,
    method_name: str,
    expected_message: str,
) -> None:
    class WrongDependency:
        def __getattr__(self, name: str):
            if name != method_name:
                raise AttributeError(name)
            return lambda *args, **kwargs: object()

    kwargs = {dependency_name: WrongDependency()}
    cycle = CognitiveCycle(**kwargs)
    context = (
        ProjectContext(
            mode=ProjectContextMode.CREATE_NEW,
            new_project_id="new-project",
        )
        if dependency_name == "project_state_manager"
        else ProjectContext(mode=ProjectContextMode.TRANSIENT)
    )

    with pytest.raises(TypeError, match=expected_message):
        cycle.run(cycle_request(context))


@pytest.mark.parametrize(
    "context",
    [
        ProjectContext(mode=ProjectContextMode.TRANSIENT),
        ProjectContext(
            mode=ProjectContextMode.CREATE_NEW,
            new_project_id="new-project",
        ),
        ProjectContext(
            mode=ProjectContextMode.EXISTING,
            existing_state=existing_state(),
        ),
    ],
)
def test_routing_is_structurally_deterministic_for_100_repetitions(
    context: ProjectContext,
) -> None:
    cycle, _, _, _, _ = configured_cycle()
    serialized = [cycle.run(cycle_request(context)).to_dict() for _ in range(100)]
    assert all(item == serialized[0] for item in serialized)


def test_clarification_is_structurally_deterministic_for_100_repetitions() -> None:
    cycle, _, _, _, _ = configured_cycle(
        interpreted=interpretation(clarification_required=True)
    )
    serialized = [cycle.run(cycle_request()).to_dict() for _ in range(100)]
    assert all(item == serialized[0] for item in serialized)


def test_invalid_context_rejection_is_deterministic_for_100_repetitions() -> None:
    failures = []
    for _ in range(100):
        with pytest.raises(ValueError) as captured:
            ProjectContext(mode=ProjectContextMode.CREATE_NEW)
        failures.append((type(captured.value), str(captured.value)))
    assert all(item == failures[0] for item in failures)


@pytest.mark.parametrize(
    "adaptive",
    [
        adaptive_result(ReasoningMode.VERIFY),
        adaptive_result(ReasoningMode.SEARCH),
        branch_result(ConvergenceStatus.RESOLVED),
        branch_result(ConvergenceStatus.TIED),
        branch_result(ConvergenceStatus.INSUFFICIENT),
    ],
    ids=("verify", "search", "branch-resolved", "branch-tied", "branch-insufficient"),
)
def test_reasoning_dispositions_are_deterministic_for_100_repetitions(
    adaptive: AdaptiveCycleResult,
) -> None:
    cycle, _, _, _, _ = configured_cycle(result=adaptive)
    serialized = [cycle.run(cycle_request()).to_dict() for _ in range(100)]
    assert all(item == serialized[0] for item in serialized)


@pytest.mark.parametrize(
    ("interpreted", "cycle_input", "attribute", "expected"),
    [
        (
            replace(
                interpretation(inferred_constraints=()),
                explicit_constraints=("x", " x "),
            ),
            cycle_request(),
            "constraints",
            ("x",),
        ),
        (
            interpretation(),
            replace(
                cycle_request(),
                outcome_uncertainties=("u", " u "),
            ),
            "uncertainty_signals",
            ("u",),
        ),
        (
            replace(
                interpretation(inferred_constraints=("a", "b", " c ")),
                explicit_constraints=("b", " a ", "b"),
            ),
            cycle_request(),
            "constraints",
            ("b", "a", "c"),
        ),
    ],
    ids=("normalized-constraints", "normalized-uncertainty", "mixed-order"),
)
def test_normalized_deduplication_is_deterministic_for_100_repetitions(
    interpreted: IntentInterpretation,
    cycle_input: CognitiveCycleRequest,
    attribute: str,
    expected: tuple[str, ...],
) -> None:
    cycle, _, _, _, reasoning = configured_cycle(interpreted=interpreted)

    for _ in range(100):
        cycle.run(cycle_input)

    assert len(reasoning.calls) == 100
    assert all(getattr(item, attribute) == expected for item in reasoning.calls)


def test_verify_and_search_are_signals_without_external_action() -> None:
    for mode in (ReasoningMode.VERIFY, ReasoningMode.SEARCH):
        cycle, _, _, project, reasoning = configured_cycle(result=adaptive_result(mode))
        result = cycle.run(cycle_request())
        assert project.calls == []
        assert len(reasoning.calls) == 1
        assert result.reasoning.adaptive_result.mode is mode


def test_public_contract_has_no_project_change_authority_execution_or_memory() -> None:
    names = {
        field.name
        for contract in (
            CognitiveCycleRequest,
            ProjectContext,
            ReasoningHandoffResult,
            CognitiveCycleResult,
        )
        for field in fields(contract)
    }
    assert not names.intersection(
        {
            "approval",
            "authority",
            "execution",
            "governed_verdict",
            "memory",
            "project_change",
            "proposed_changes",
            "raw_chain_of_thought",
            "tool",
        }
    )


def test_system_implementation_has_only_frozen_dependencies_and_no_side_effects() -> (
    None
):
    system_dir = Path(system_package.__file__).parent
    imports: set[str] = set()
    names: set[str] = set()
    for path in system_dir.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names.update(node.id for node in ast.walk(tree) if isinstance(node, ast.Name))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.add(node.module)

    assert imports.issubset(
        {
            "__future__",
            "collections.abc",
            "dataclasses",
            "enum",
            "aegis_os.intent",
            "aegis_os.project",
            "aegis_os.reasoning",
            "models",
            "cycle",
        }
    )
    assert not names.intersection(
        {
            "ProjectLedger",
            "ProjectLifecycleManager",
            "ProjectChangeProposal",
            "asyncio",
            "httpx",
            "requests",
            "socket",
            "subprocess",
            "threading",
        }
    )
