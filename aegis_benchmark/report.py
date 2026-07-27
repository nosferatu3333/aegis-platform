from __future__ import annotations

import json
from pathlib import Path

from aegis_benchmark.models import BenchmarkRunSummary


def write_json_report(
    summary: BenchmarkRunSummary,
    path: str | Path = "benchmarks/reports/latest.json",
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def write_markdown_report(
    summary: BenchmarkRunSummary,
    path: str | Path = "benchmarks/reports/latest.md",
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(_render_markdown(summary), encoding="utf-8")
    return destination


def _render_markdown(summary: BenchmarkRunSummary) -> str:
    lines = [
        f"# {summary.suite} v{summary.version}",
        "",
        "## Run summary",
        "",
        f"- Total cases: {summary.total_cases}",
        f"- Passed cases: {summary.passed_cases}",
        f"- Failed cases: {summary.failed_cases}",
        f"- Overall score: {summary.overall_score:.2f}%",
        "",
        "## Category breakdown",
        "",
        "| Category | Cases | Passed | Failed | Score |",
        "|---|---:|---:|---:|---:|",
    ]
    for category, values in summary.category_breakdown.items():
        lines.append(
            f"| {category} | {values['total_cases']} | "
            f"{values['passed_cases']} | {values['failed_cases']} | "
            f"{values['score']:.2f}% |"
        )

    lines.extend(
        [
            "",
            "## Metric breakdown",
            "",
            "| Metric | Accuracy |",
            "|---|---:|",
            f"| Intent | {summary.intent_accuracy:.2f}% |",
            f"| Capability | {summary.capability_accuracy:.2f}% |",
            f"| Agent selection | "
            f"{summary.agent_selection_accuracy:.2f}% |",
            f"| Workflow | {summary.workflow_accuracy:.2f}% |",
            f"| Analysis status | "
            f"{summary.analysis_status_accuracy:.2f}% |",
            f"| Execution | {summary.execution_accuracy:.2f}% |",
            f"| Simulation compliance | "
            f"{summary.simulation_compliance_accuracy:.2f}% |",
            "",
            "## Failed cases",
            "",
        ]
    )
    failed = [result for result in summary.results if not result.passed]
    lines.extend(
        [f"- `{result.case_id}` — {result.title}" for result in failed]
        or ["None."]
    )
    lines.extend(
        [
            "",
            "## Per-case results",
            "",
            "| Case | Category | Result | Score |",
            "|---|---|---|---:|",
        ]
    )
    for result in summary.results:
        status = "PASS" if result.passed else "FAIL"
        lines.append(
            f"| `{result.case_id}` | {result.category} | {status} | "
            f"{result.score:.2f}% |"
        )
    lines.append("")
    return "\n".join(lines)
