import json

from aegis_benchmark.cli import main
from aegis_benchmark.models import BenchmarkResult
from aegis_benchmark.report import write_json_report, write_markdown_report
from aegis_benchmark.scoring import calculate_summary


def test_json_and_markdown_reports_are_generated(workspace_tmp):
    summary = calculate_summary(
        [BenchmarkResult("case-1", "Case One", "research", True, 100.0)]
    )
    json_path = write_json_report(summary, workspace_tmp / "report.json")
    markdown_path = write_markdown_report(
        summary,
        workspace_tmp / "report.md",
    )

    assert json.loads(json_path.read_text(encoding="utf-8"))[
        "overall_score"
    ] == 0.0
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# AEGIS Benchmark Suite v0.1" in markdown
    assert "## Category breakdown" in markdown
    assert "## Metric breakdown" in markdown
    assert "## Failed cases" in markdown
    assert "## Per-case results" in markdown


def test_cli_returns_zero_and_writes_reports(workspace_tmp):
    json_output = workspace_tmp / "latest.json"
    markdown_output = workspace_tmp / "latest.md"

    exit_code = main(
        [
            "--path",
            "benchmarks/missions",
            "--case",
            "research-001",
            "--json-output",
            str(json_output),
            "--markdown-output",
            str(markdown_output),
        ]
    )

    assert exit_code == 0
    assert json_output.exists()
    assert markdown_output.exists()


def test_cli_returns_nonzero_when_loading_fails(workspace_tmp):
    assert main(["--path", str(workspace_tmp / "missing")]) != 0
