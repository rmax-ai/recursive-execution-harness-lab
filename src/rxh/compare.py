from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> dict:
    """Load a JSON file, returning an empty dict when the file is missing."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    """Count records in a JSONL file, returning zero when the file is missing."""
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as file_obj:
        return sum(1 for _ in file_obj)


def compare_runs(run_a: Path, run_b: Path, out: Path) -> str:
    """Build a simple markdown report comparing two run directories."""
    verify_a = load_json(run_a / "verification.json")
    verify_b = load_json(run_b / "verification.json")

    evidence_a = count_jsonl(run_a / "evidence_cards.jsonl")
    evidence_b = count_jsonl(run_b / "evidence_cards.jsonl")

    trace_a = count_jsonl(run_a / "trace.jsonl")
    trace_b = count_jsonl(run_b / "trace.jsonl")
    unsupported_a = len(verify_a.get("unsupported_claims", []))
    unsupported_b = len(verify_b.get("unsupported_claims", []))
    attribution_a = len(verify_a.get("source_attribution_errors", []))
    attribution_b = len(verify_b.get("source_attribution_errors", []))
    verdict_a = verify_a.get("verdict", "n/a")
    verdict_b = verify_b.get("verdict", "n/a")

    report = f"""
# Run Comparison

## Inputs

- Run A: `{run_a}`
- Run B: `{run_b}`

## Metrics

| Metric | Run A | Run B |
|---|---:|---:|
| Evidence cards | {evidence_a} | {evidence_b} |
| Trace events | {trace_a} | {trace_b} |
| Unsupported claims | {unsupported_a} | {unsupported_b} |
| Source attribution errors | {attribution_a} | {attribution_b} |
| Verification verdict | {verdict_a} | {verdict_b} |

## Interpretation

Add qualitative analysis here.
""".strip()

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    return report
