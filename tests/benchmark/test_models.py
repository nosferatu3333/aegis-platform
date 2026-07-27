from aegis_benchmark.models import (
    BenchmarkActual,
    BenchmarkCase,
    BenchmarkExpectation,
)


def test_valid_models_construct_and_serialize():
    case = BenchmarkCase(
        id="case-1",
        title="Case",
        category="research",
        difficulty="easy",
        mission="Research systems",
        expected=BenchmarkExpectation(primary_intent="research"),
    )
    actual = BenchmarkActual(
        primary_intent="research",
        required_capabilities=["research"],
        selected_agent="Research Agent",
        workflow_step_count=5,
        workflow_orders=[1, 2, 3, 4, 5],
        workflow_order_valid=True,
        analysis_status="ready",
    )

    assert case.to_dict()["expected"] == {"primary_intent": "research"}
    assert actual.to_dict()["workflow_order_valid"] is True


def test_model_mutable_defaults_are_not_shared():
    first = BenchmarkCase(
        "one",
        "One",
        "research",
        "easy",
        "Research one",
        BenchmarkExpectation(),
    )
    second = BenchmarkCase(
        "two",
        "Two",
        "research",
        "easy",
        "Research two",
        BenchmarkExpectation(),
    )
    first.tags.append("changed")

    assert second.tags == []
