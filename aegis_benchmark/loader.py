from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aegis_benchmark.models import BenchmarkCase, BenchmarkExpectation


class BenchmarkLoadError(ValueError):
    pass


def load_benchmark_file(path: str | Path) -> list[BenchmarkCase]:
    source = Path(path)
    try:
        payload = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise BenchmarkLoadError(f"Cannot load {source}: {error}") from error

    raw_cases = payload.get("cases") if isinstance(payload, dict) else payload
    if not isinstance(raw_cases, list):
        raise BenchmarkLoadError(
            f"{source} must contain a JSON list or an object with 'cases'."
        )

    cases = [_parse_case(item, source) for item in raw_cases]
    _reject_duplicates(cases)
    return sorted(
        (case for case in cases if case.enabled),
        key=lambda case: case.id,
    )


def load_benchmark_directory(path: str | Path) -> list[BenchmarkCase]:
    directory = Path(path)
    if not directory.is_dir():
        raise BenchmarkLoadError(f"Benchmark directory not found: {directory}")

    cases: list[BenchmarkCase] = []
    for source in sorted(directory.glob("*.json"), key=lambda item: item.name):
        cases.extend(load_benchmark_file(source))
    _reject_duplicates(cases)
    return sorted(cases, key=lambda case: case.id)


def load_benchmarks(path: str | Path) -> list[BenchmarkCase]:
    source = Path(path)
    if source.is_dir():
        return load_benchmark_directory(source)
    return load_benchmark_file(source)


def _parse_case(raw: Any, source: Path) -> BenchmarkCase:
    if not isinstance(raw, dict):
        raise BenchmarkLoadError(f"Malformed case in {source}: object required.")

    required = {"id", "title", "category", "difficulty", "mission", "expected"}
    missing = sorted(required - raw.keys())
    if missing:
        raise BenchmarkLoadError(
            f"Malformed case in {source}: missing {', '.join(missing)}."
        )
    if not all(
        isinstance(raw[key], str) and raw[key].strip()
        for key in required - {"expected"}
    ):
        raise BenchmarkLoadError(
            f"Malformed case in {source}: text fields cannot be empty."
        )
    if not isinstance(raw["expected"], dict):
        raise BenchmarkLoadError(
            f"Malformed case {raw['id']} in {source}: expected must be an object."
        )

    allowed_expectations = set(BenchmarkExpectation.__dataclass_fields__)
    unknown = sorted(set(raw["expected"]) - allowed_expectations)
    if unknown:
        raise BenchmarkLoadError(
            f"Malformed case {raw['id']}: unknown expectations {', '.join(unknown)}."
        )
    tags = raw.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
        raise BenchmarkLoadError(f"Malformed case {raw['id']}: invalid tags.")
    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise BenchmarkLoadError(
            f"Malformed case {raw['id']}: enabled must be boolean."
        )

    try:
        expectation = BenchmarkExpectation(**raw["expected"])
    except TypeError as error:
        raise BenchmarkLoadError(
            f"Malformed expectations for case {raw['id']}: {error}"
        ) from error
    if expectation.required_capabilities is not None and not isinstance(
        expectation.required_capabilities, list
    ):
        raise BenchmarkLoadError(
            f"Malformed case {raw['id']}: required_capabilities must be a list."
        )

    return BenchmarkCase(
        id=raw["id"].strip(),
        title=raw["title"].strip(),
        category=raw["category"].strip(),
        difficulty=raw["difficulty"].strip(),
        mission=raw["mission"].strip(),
        expected=expectation,
        tags=list(tags),
        enabled=enabled,
    )


def _reject_duplicates(cases: list[BenchmarkCase]) -> None:
    seen: set[str] = set()
    for case in cases:
        if case.id in seen:
            raise BenchmarkLoadError(f"Duplicate benchmark ID: {case.id}")
        seen.add(case.id)
