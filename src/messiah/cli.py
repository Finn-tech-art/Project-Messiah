"""Command-line entry point for Project Messiah."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import cast

from messiah.dashboard import launch_dashboard
from messiah.models import MessiahState
from messiah.pipeline import run_pipeline


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="messiah",
        description="Run the Project Messiah dry-run pipeline on a local job brief.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a job through the pipeline.")
    run_parser.add_argument("input", type=Path, help="Path to a JSON job brief.")
    run_parser.add_argument(
        "--no-langgraph",
        action="store_true",
        help="Use the plain Python workflow runner instead of LangGraph.",
    )
    run_parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Open the local dashboard after the pipeline finishes.",
    )

    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="Run a job through the pipeline and open the dashboard.",
    )
    dashboard_parser.add_argument("input", type=Path, help="Path to a JSON job brief.")
    dashboard_parser.add_argument(
        "--no-langgraph",
        action="store_true",
        help="Use the plain Python workflow runner instead of LangGraph.",
    )

    return parser


def _build_initial_state(path: Path) -> MessiahState:
    return cast(
        MessiahState,
        {
            "input_path": str(path),
            "messages": [],
            "errors": [],
        },
    )


def _print_summary(state: MessiahState) -> None:
    job = state.get("job_brief")
    qualification = state.get("qualification")
    estimate = state.get("estimate")
    execution_plan = state.get("execution_plan")
    checklist = state.get("delivery_checklist")
    status = state.get("job_status")

    print()
    print("Project Messiah Dry Run")
    print("=======================")
    print(f"Job ID: {job.job_id if job else '-'}")
    print(f"Title: {job.title if job else '-'}")
    print(f"Status: {status.value if status else '-'}")
    print(
        "Service line: "
        f"{qualification.service_line.value if qualification and qualification.service_line else '-'}"
    )
    print(f"Job type: {qualification.job_type.value if qualification and qualification.job_type else '-'}")

    if qualification is not None:
        print(f"Qualified: {qualification.qualified}")
        print(f"Qualification confidence: {qualification.confidence:.2f}")
        print(
            "Risk flags: "
            + (
                ", ".join(flag.value for flag in qualification.risk_flags)
                if qualification.risk_flags
                else "none"
            )
        )

    if estimate is not None:
        band = estimate.price_band
        print(f"Price band: {band.currency} {band.minimum:.2f} - {band.maximum:.2f}")
        print(
            "Estimated hours: "
            f"{estimate.estimated_hours_low:.1f} - {estimate.estimated_hours_high:.1f}"
        )
        print(f"Estimate confidence: {estimate.confidence:.2f}")
        print(f"Effort tier: {estimate.effort_tier.value}")
        print(f"Margin note: {estimate.likely_margin_note}")

    if execution_plan is not None:
        print(f"Execution steps: {len(execution_plan.steps)}")

    if checklist is not None:
        print(f"Checklist items: {len(checklist.items)}")

    messages = state.get("messages", [])
    if messages:
        print()
        print("Messages")
        print("--------")
        for message in messages:
            print(f"- {message}")


def _run(args: argparse.Namespace, *, open_dashboard: bool) -> int:
    input_path = args.input.resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Job brief not found: {input_path}")

    state = _build_initial_state(input_path)
    result = run_pipeline(state, prefer_langgraph=not args.no_langgraph)
    _print_summary(result)

    if open_dashboard:
        return launch_dashboard(result)
    return 0


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if args.command == "run":
        raise SystemExit(_run(args, open_dashboard=args.dashboard))

    if args.command == "dashboard":
        raise SystemExit(_run(args, open_dashboard=True))

    raise SystemExit(2)


if __name__ == "__main__":
    main()
