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
    verify_path_a = run_a / "verification.json"
    verify_path_b = run_b / "verification.json"
    has_verify_a = verify_path_a.exists()
    has_verify_b = verify_path_b.exists()
    verify_a = load_json(verify_path_a)
    verify_b = load_json(verify_path_b)

    evidence_a = count_jsonl(run_a / "evidence_cards.jsonl")
    evidence_b = count_jsonl(run_b / "evidence_cards.jsonl")

    trace_a = count_jsonl(run_a / "trace.jsonl")
    trace_b = count_jsonl(run_b / "trace.jsonl")
    unsupported_a_count = (
        len(verify_a.get("unsupported_claims", [])) if has_verify_a else None
    )
    unsupported_b_count = (
        len(verify_b.get("unsupported_claims", [])) if has_verify_b else None
    )
    attribution_a_count = (
        len(verify_a.get("source_attribution_errors", [])) if has_verify_a else None
    )
    attribution_b_count = (
        len(verify_b.get("source_attribution_errors", [])) if has_verify_b else None
    )
    unsupported_a = (
        unsupported_a_count if unsupported_a_count is not None else "not evaluated"
    )
    unsupported_b = (
        unsupported_b_count if unsupported_b_count is not None else "not evaluated"
    )
    attribution_a = (
        attribution_a_count if attribution_a_count is not None else "not evaluated"
    )
    attribution_b = (
        attribution_b_count if attribution_b_count is not None else "not evaluated"
    )
    verdict_a = (
        verify_a.get("verdict", "n/a")
        if has_verify_a
        else "not evaluated (missing verification.json)"
    )
    verdict_b = (
        verify_b.get("verdict", "n/a")
        if has_verify_b
        else "not evaluated (missing verification.json)"
    )

    interpretation_lines: list[str] = []
    if evidence_a == evidence_b:
        interpretation_lines.append(
            f"Both runs produced the same number of evidence cards ({evidence_a})."
        )
    elif evidence_a > evidence_b:
        interpretation_lines.append(
            f"Run A produced more evidence cards ({evidence_a} vs {evidence_b})."
        )
    else:
        interpretation_lines.append(
            f"Run B produced more evidence cards ({evidence_b} vs {evidence_a})."
        )

    if trace_a == trace_b:
        interpretation_lines.append(f"Both runs emitted the same trace volume ({trace_a}).")
    elif trace_a > trace_b:
        interpretation_lines.append(
            f"Run A emitted more trace events ({trace_a} vs {trace_b})."
        )
    else:
        interpretation_lines.append(
            f"Run B emitted more trace events ({trace_b} vs {trace_a})."
        )

    if has_verify_a and has_verify_b:
        if unsupported_a_count != unsupported_b_count:
            if unsupported_a_count is not None and unsupported_b_count is not None:
                if unsupported_a_count < unsupported_b_count:
                    interpretation_lines.append(
                        "Run A has fewer unsupported claims than Run B."
                    )
                else:
                    interpretation_lines.append(
                        "Run B has fewer unsupported claims than Run A."
                    )
        else:
            interpretation_lines.append(
                f"Both runs have the same unsupported-claim count ({unsupported_a_count})."
            )

        if attribution_a_count != attribution_b_count:
            if attribution_a_count is not None and attribution_b_count is not None:
                if attribution_a_count < attribution_b_count:
                    interpretation_lines.append(
                        "Run A has fewer source attribution errors than Run B."
                    )
                else:
                    interpretation_lines.append(
                        "Run B has fewer source attribution errors than Run A."
                    )
        else:
            interpretation_lines.append(
                f"Both runs have the same attribution-error count ({attribution_a_count})."
            )
    else:
        if not has_verify_a:
            interpretation_lines.append(
                "Run A was not evaluated because verifier output is missing (verification.json)."
            )
        if not has_verify_b:
            interpretation_lines.append(
                "Run B was not evaluated because verifier output is missing (verification.json)."
            )
        interpretation_lines.append(
            "Unsupported claims and attribution errors cannot be compared for runs without verifier output."
        )

    interpretation = "\n".join(f"- {line}" for line in interpretation_lines)

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

{interpretation}
""".strip()

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    return report
