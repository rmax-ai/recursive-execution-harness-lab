from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

TRACE_REQUIRED_EVENTS: dict[str, set[str]] = {
    "long-context": {
        "run_started",
        "prompt_build_started",
        "prompt_built",
        "model_completed",
        "verification_started",
        "verification_completed",
        "run_completed",
    },
    "recursive": {
        "run_started",
        "recursive_run_started",
        "planning_started",
        "planning_completed",
        "worker_started",
        "worker_completed",
        "synthesis_started",
        "synthesis_completed",
        "verification_started",
        "verification_completed",
        "recursive_run_completed",
        "run_completed",
    },
}


@dataclass(frozen=True)
class TraceSummary:
    mode: str | None
    event_types: set[str]
    input_tokens: int
    output_tokens: int

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass(frozen=True)
class CoverageSummary:
    assigned_refs: int | None
    total_docs: int

    @property
    def display(self) -> str:
        if self.assigned_refs is None:
            return "n/a"
        if self.total_docs == 0:
            return "0/0"
        return f"{self.assigned_refs}/{self.total_docs}"


@dataclass(frozen=True)
class RunSummary:
    path: Path
    mode: str | None
    evidence_count: int
    trace_event_count: int
    trace_input_tokens: int
    trace_output_tokens: int
    verification_verdict: str
    unsupported_claims: str | int
    attribution_errors: str | int
    trace_completeness: str
    missing_events: list[str]
    present_events: list[str]
    assigned_ref_coverage: str


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON file, returning an empty dict when the file is missing."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load JSONL records, returning an empty list when the file is missing."""
    if not path.exists():
        return []

    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file_obj:
        for line in file_obj:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def count_jsonl(path: Path) -> int:
    """Count records in a JSONL file, returning zero when the file is missing."""
    return len(load_jsonl(path))


def detect_mode(events: list[dict[str, Any]]) -> str | None:
    """Infer run mode from trace metadata or event types."""
    for event in events:
        mode = event.get("metadata", {}).get("mode")
        if mode in TRACE_REQUIRED_EVENTS:
            return mode

    event_types = {event.get("event_type") for event in events}
    if "recursive_run_started" in event_types or "planning_started" in event_types:
        return "recursive"
    if "prompt_build_started" in event_types or "model_completed" in event_types:
        return "long-context"
    return None


def summarize_trace(events: list[dict[str, Any]]) -> TraceSummary:
    """Summarize trace mode, observed events, and token totals."""
    input_tokens = 0
    output_tokens = 0
    event_types: set[str] = set()

    for event in events:
        event_type = event.get("event_type")
        if isinstance(event_type, str):
            event_types.add(event_type)

        token_usage = event.get("token_usage", {})
        input_tokens += int(token_usage.get("input", 0) or 0)
        output_tokens += int(token_usage.get("output", 0) or 0)

    return TraceSummary(
        mode=detect_mode(events),
        event_types=event_types,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )


def summarize_completeness(
    mode: str | None,
    event_types: set[str],
) -> tuple[str, list[str], list[str]]:
    """Summarize required trace event completeness for the detected mode."""
    if mode is None:
        return "unknown mode", [], sorted(event_types)

    required = TRACE_REQUIRED_EVENTS[mode]
    present = sorted(required & event_types)
    missing = sorted(required - event_types)
    return f"{len(present)}/{len(required)}", missing, present


def summarize_coverage(run_dir: Path) -> CoverageSummary:
    """Compute assigned-ref coverage against ingested documents when feasible."""
    documents = load_jsonl(run_dir / "documents.jsonl")
    plan = load_json(run_dir / "plan.json")

    total_docs = len(documents)
    items = plan.get("items")
    if not isinstance(items, list):
        return CoverageSummary(assigned_refs=None, total_docs=total_docs)

    assigned_refs = {
        ref
        for item in items
        if isinstance(item, dict)
        for ref in item.get("assigned_refs", [])
        if isinstance(ref, str)
    }
    return CoverageSummary(assigned_refs=len(assigned_refs), total_docs=total_docs)


def summarize_run(run_dir: Path) -> RunSummary:
    """Build the metrics used by the markdown comparison report."""
    trace_events = load_jsonl(run_dir / "trace.jsonl")
    trace = summarize_trace(trace_events)
    trace_completeness, missing_events, present_events = summarize_completeness(
        trace.mode,
        trace.event_types,
    )

    verification = load_json(run_dir / "verification.json")
    has_verification = bool(verification)
    verdict = (
        verification.get("verdict", "n/a")
        if has_verification
        else "not evaluated (missing verification.json)"
    )
    unsupported_claims: str | int = (
        len(verification.get("unsupported_claims", []))
        if has_verification
        else "not evaluated"
    )
    attribution_errors: str | int = (
        len(verification.get("source_attribution_errors", []))
        if has_verification
        else "not evaluated"
    )
    coverage = summarize_coverage(run_dir)

    return RunSummary(
        path=run_dir,
        mode=trace.mode,
        evidence_count=count_jsonl(run_dir / "evidence_cards.jsonl"),
        trace_event_count=len(trace_events),
        trace_input_tokens=trace.input_tokens,
        trace_output_tokens=trace.output_tokens,
        verification_verdict=verdict,
        unsupported_claims=unsupported_claims,
        attribution_errors=attribution_errors,
        trace_completeness=trace_completeness,
        missing_events=missing_events,
        present_events=present_events,
        assigned_ref_coverage=coverage.display,
    )


def compare_runs(run_a: Path, run_b: Path, out: Path) -> str:
    """Build a markdown report comparing two run directories."""
    summary_a = summarize_run(run_a)
    summary_b = summarize_run(run_b)
    total_tokens_a = summary_a.trace_input_tokens + summary_a.trace_output_tokens
    total_tokens_b = summary_b.trace_input_tokens + summary_b.trace_output_tokens
    present_events_a = (
        ", ".join(summary_a.present_events) if summary_a.present_events else "n/a"
    )
    missing_events_a = (
        ", ".join(summary_a.missing_events) if summary_a.missing_events else "none"
    )
    present_events_b = (
        ", ".join(summary_b.present_events) if summary_b.present_events else "n/a"
    )
    missing_events_b = (
        ", ".join(summary_b.missing_events) if summary_b.missing_events else "none"
    )

    interpretation_lines: list[str] = []
    if total_tokens_a == total_tokens_b:
        interpretation_lines.append(
            "Both runs consumed the same total traced tokens."
        )
    elif total_tokens_a < total_tokens_b:
        interpretation_lines.append("Run A consumed fewer traced tokens than Run B.")
    else:
        interpretation_lines.append("Run B consumed fewer traced tokens than Run A.")

    if summary_a.trace_completeness == summary_b.trace_completeness:
        interpretation_lines.append(
            "Both runs have the same trace completeness "
            f"({summary_a.trace_completeness})."
        )
    elif len(summary_a.missing_events) < len(summary_b.missing_events):
        interpretation_lines.append("Run A has a more complete required trace surface.")
    elif len(summary_b.missing_events) < len(summary_a.missing_events):
        interpretation_lines.append("Run B has a more complete required trace surface.")

    if (
        isinstance(summary_a.unsupported_claims, int)
        and isinstance(summary_b.unsupported_claims, int)
    ):
        if summary_a.unsupported_claims < summary_b.unsupported_claims:
            interpretation_lines.append(
                "Run A has fewer unsupported claims than Run B."
            )
        elif summary_b.unsupported_claims < summary_a.unsupported_claims:
            interpretation_lines.append(
                "Run B has fewer unsupported claims than Run A."
            )
        else:
            interpretation_lines.append(
                "Both runs have the same unsupported-claim count "
                f"({summary_a.unsupported_claims})."
            )
    else:
        if summary_a.verification_verdict.startswith("not evaluated"):
            interpretation_lines.append(
                "Run A was not evaluated because verifier output is missing "
                "(verification.json)."
            )
        if summary_b.verification_verdict.startswith("not evaluated"):
            interpretation_lines.append(
                "Run B was not evaluated because verifier output is missing "
                "(verification.json)."
            )
        interpretation_lines.append(
            "Unsupported claims and attribution errors cannot be compared "
            "for runs without verifier output."
        )

    if (
        isinstance(summary_a.attribution_errors, int)
        and isinstance(summary_b.attribution_errors, int)
    ):
        if summary_a.attribution_errors < summary_b.attribution_errors:
            interpretation_lines.append(
                "Run A has fewer source attribution errors than Run B."
            )
        elif summary_b.attribution_errors < summary_a.attribution_errors:
            interpretation_lines.append(
                "Run B has fewer source attribution errors than Run A."
            )
        else:
            interpretation_lines.append(
                "Both runs have the same attribution-error count "
                f"({summary_a.attribution_errors})."
            )

    interpretation = "\n".join(f"- {line}" for line in interpretation_lines)
    metrics_rows = "\n".join(
        [
            (
                "| Detected mode | "
                f"{summary_a.mode or 'unknown'} | {summary_b.mode or 'unknown'} |"
            ),
            (
                "| Evidence cards | "
                f"{summary_a.evidence_count} | {summary_b.evidence_count} |"
            ),
            (
                "| Trace events | "
                f"{summary_a.trace_event_count} | {summary_b.trace_event_count} |"
            ),
            (
                "| Trace input tokens | "
                f"{summary_a.trace_input_tokens} | {summary_b.trace_input_tokens} |"
            ),
            (
                "| Trace output tokens | "
                f"{summary_a.trace_output_tokens} | {summary_b.trace_output_tokens} |"
            ),
            f"| Trace total tokens | {total_tokens_a} | {total_tokens_b} |",
            (
                "| Trace completeness | "
                f"{summary_a.trace_completeness} | {summary_b.trace_completeness} |"
            ),
            (
                "| Assigned-ref coverage | "
                f"{summary_a.assigned_ref_coverage} | "
                f"{summary_b.assigned_ref_coverage} |"
            ),
            (
                "| Unsupported claims | "
                f"{summary_a.unsupported_claims} | {summary_b.unsupported_claims} |"
            ),
            (
                "| Source attribution errors | "
                f"{summary_a.attribution_errors} | {summary_b.attribution_errors} |"
            ),
            (
                "| Verification verdict | "
                f"{summary_a.verification_verdict} | "
                f"{summary_b.verification_verdict} |"
            ),
        ]
    )
    report = f"""
# Run Comparison

## Inputs

- Run A: `{run_a}`
- Run B: `{run_b}`

## Metrics

| Metric | Run A | Run B |
|---|---:|---:|
{metrics_rows}

## Trace Completeness Details

- Run A present events: {present_events_a}
- Run A missing events: {missing_events_a}
- Run B present events: {present_events_b}
- Run B missing events: {missing_events_b}

## Interpretation

{interpretation}
""".strip()

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    return report
