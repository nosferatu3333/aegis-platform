from __future__ import annotations

import argparse
import sys

from aegis_benchmark.loader import BenchmarkLoadError, load_benchmarks
from aegis_benchmark.report import write_json_report, write_markdown_report
from aegis_benchmark.runner import BenchmarkRunner


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run AEGIS benchmarks.")
    parser.add_argument("--path", required=True)
    parser.add_argument("--category")
    parser.add_argument("--case", dest="case_id")
    parser.add_argument("--no-execution", action="store_true")
    parser.add_argument(
        "--json-output",
        default="benchmarks/reports/latest.json",
    )
    parser.add_argument(
        "--markdown-output",
        default="benchmarks/reports/latest.md",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cases = load_benchmarks(args.path)
    except BenchmarkLoadError as error:
        print(f"Benchmark loading failed: {error}", file=sys.stderr)
        return 2

    if args.category:
        cases = [case for case in cases if case.category == args.category]
    if args.case_id:
        cases = [case for case in cases if case.id == args.case_id]
    if not cases:
        print("No enabled benchmark cases matched.", file=sys.stderr)
        return 2

    summary = BenchmarkRunner(execute=not args.no_execution).run_suite(cases)
    json_path = write_json_report(summary, args.json_output)
    markdown_path = write_markdown_report(summary, args.markdown_output)
    print(
        f"AEGIS Benchmark Suite v{summary.version}: "
        f"{summary.passed_cases}/{summary.total_cases} passed, "
        f"score={summary.overall_score:.2f}%"
    )
    print(f"JSON: {json_path}")
    print(f"Markdown: {markdown_path}")
    return 0 if summary.failed_cases == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
