import json

import pytest

from aegis_benchmark.loader import (
    BenchmarkLoadError,
    load_benchmark_directory,
    load_benchmark_file,
)


def payload(case_id="case-1", enabled=True):
    return {
        "cases": [
            {
                "id": case_id,
                "title": "Case",
                "category": "research",
                "difficulty": "easy",
                "mission": "Research systems",
                "expected": {"primary_intent": "research"},
                "enabled": enabled,
            }
        ]
    }


def test_loads_valid_file_and_skips_disabled_cases(workspace_tmp):
    source = workspace_tmp / "cases.json"
    source.write_text(
        json.dumps(
            {
                "cases": payload("enabled")["cases"]
                + payload("disabled", False)["cases"]
            }
        ),
        encoding="utf-8",
    )

    cases = load_benchmark_file(source)

    assert [case.id for case in cases] == ["enabled"]


def test_directory_loading_is_deterministic(workspace_tmp):
    (workspace_tmp / "z.json").write_text(
        json.dumps(payload("z-case")),
        encoding="utf-8",
    )
    (workspace_tmp / "a.json").write_text(
        json.dumps(payload("a-case")),
        encoding="utf-8",
    )

    cases = load_benchmark_directory(workspace_tmp)

    assert [case.id for case in cases] == ["a-case", "z-case"]


def test_duplicate_ids_across_files_are_rejected(workspace_tmp):
    for name in ("a.json", "b.json"):
        (workspace_tmp / name).write_text(
            json.dumps(payload("duplicate")),
            encoding="utf-8",
        )

    with pytest.raises(BenchmarkLoadError, match="Duplicate benchmark ID"):
        load_benchmark_directory(workspace_tmp)


@pytest.mark.parametrize(
    "data",
    [
        {"cases": [{"id": "incomplete"}]},
        {"cases": ["not-an-object"]},
        {"unexpected": []},
    ],
)
def test_malformed_cases_are_rejected(workspace_tmp, data):
    source = workspace_tmp / "bad.json"
    source.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(BenchmarkLoadError):
        load_benchmark_file(source)
