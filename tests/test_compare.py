from __future__ import annotations

import json
from pathlib import Path

from rxh.compare import compare_runs


def test_compare_runs_handles_missing_verification_json_gracefully(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    out = tmp_path / "report.md"
    run_a.mkdir()
    run_b.mkdir()
    (run_a / "trace.jsonl").write_text(
        '\n'.join(
            [
                json.dumps(
                    {
                        "event_type": "run_started",
                        "metadata": {"mode": "long-context"},
                    }
                ),
                json.dumps({"event_type": "run_completed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_b / "trace.jsonl").write_text(
        '\n'.join(
            [
                json.dumps(
                    {
                        "event_type": "run_started",
                        "metadata": {"mode": "long-context"},
                    }
                ),
                json.dumps({"event_type": "run_completed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = compare_runs(run_a, run_b, out)

    assert (
        "Verification verdict | not evaluated (missing verification.json) | "
        "not evaluated (missing verification.json)"
    ) in report
    assert (
        "Policy decision | not evaluated (missing policy_decision.json) | "
        "not evaluated (missing policy_decision.json)"
    ) in report
    assert "| Unsupported claims | not evaluated | not evaluated |" in report
    assert "| Source attribution errors | not evaluated | not evaluated |" in report
    assert "- Run A was not evaluated because verifier output is missing " in report
    assert "- Run B was not evaluated because verifier output is missing " in report
    assert out.read_text(encoding="utf-8") == report


def test_compare_runs_uses_trace_metrics_and_coverage_in_report(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    out = tmp_path / "report.md"
    run_a.mkdir()
    run_b.mkdir()

    (run_a / "documents.jsonl").write_text(
        '\n'.join(
            [
                json.dumps({"id": "doc_0001"}),
                json.dumps({"id": "doc_0002"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_b / "documents.jsonl").write_text(
        json.dumps({"id": "doc_0001"}) + "\n",
        encoding="utf-8",
    )
    (run_a / "plan.json").write_text(
        json.dumps(
            {
                "items": [
                    {"assigned_refs": ["doc_0001"]},
                    {"assigned_refs": ["doc_0002"]},
                ]
            }
        ),
        encoding="utf-8",
    )
    (run_b / "plan.json").write_text(
        json.dumps({"items": []}),
        encoding="utf-8",
    )
    (run_a / "evidence_cards.jsonl").write_text('{"id":"ev1"}\n', encoding="utf-8")
    (run_b / "evidence_cards.jsonl").write_text(
        '{"id":"ev1"}\n{"id":"ev2"}\n',
        encoding="utf-8",
    )
    (run_a / "trace.jsonl").write_text(
        '\n'.join(
            [
                json.dumps(
                    {
                        "event_type": "run_started",
                        "metadata": {"mode": "recursive"},
                    }
                ),
                json.dumps(
                    {
                        "event_type": "recursive_run_started",
                        "token_usage": {"input": 11, "output": 2},
                    }
                ),
                json.dumps(
                    {
                        "event_type": "planning_started",
                        "token_usage": {"input": 3, "output": 0},
                    }
                ),
                json.dumps({"event_type": "planning_completed"}),
                json.dumps({"event_type": "worker_started"}),
                json.dumps(
                    {
                        "event_type": "worker_completed",
                        "token_usage": {"input": 5, "output": 7},
                    }
                ),
                json.dumps({"event_type": "synthesis_started"}),
                json.dumps({"event_type": "synthesis_completed"}),
                json.dumps({"event_type": "verification_started"}),
                json.dumps({"event_type": "verification_completed"}),
                json.dumps({"event_type": "policy_started"}),
                json.dumps({"event_type": "policy_completed"}),
                json.dumps({"event_type": "recursive_run_completed"}),
                json.dumps({"event_type": "run_completed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_b / "trace.jsonl").write_text(
        '\n'.join(
            [
                json.dumps(
                    {
                        "event_type": "run_started",
                        "metadata": {"mode": "long-context"},
                    }
                ),
                json.dumps(
                    {
                        "event_type": "prompt_build_started",
                        "token_usage": {"input": 2, "output": 0},
                    }
                ),
                json.dumps({"event_type": "policy_started"}),
                json.dumps({"event_type": "run_completed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_a / "verification.json").write_text(
        json.dumps(
            {
                "verdict": "pass",
                "unsupported_claims": [],
                "source_attribution_errors": [],
            }
        ),
        encoding="utf-8",
    )
    (run_b / "verification.json").write_text(
        json.dumps(
            {
                "verdict": "partial",
                "unsupported_claims": ["claim"],
                "source_attribution_errors": ["citation"],
            }
        ),
        encoding="utf-8",
    )
    (run_a / "policy_decision.json").write_text(
        json.dumps(
            {
                "decision": "allow",
                "rationale": "No policy issues found.",
                "required_changes": [],
                "blocked_claims": [],
            }
        ),
        encoding="utf-8",
    )
    (run_b / "policy_decision.json").write_text(
        json.dumps(
            {
                "decision": "revise",
                "rationale": "Verifier found correctable issues.",
                "required_changes": ["Fix claim."],
                "blocked_claims": ["claim"],
            }
        ),
        encoding="utf-8",
    )

    report = compare_runs(run_a, run_b, out)

    assert "| Detected mode | recursive | long-context |" in report
    assert "| Trace input tokens | 19 | 2 |" in report
    assert "| Trace output tokens | 9 | 0 |" in report
    assert "| Trace total tokens | 28 | 2 |" in report
    assert "| Trace completeness | 14/14 | 4/9 |" in report
    assert "| Assigned-ref coverage | 2/2 | 0/1 |" in report
    assert "| Verification verdict | pass | partial |" in report
    assert "| Policy decision | allow | revise |" in report
    assert "- Run A has a more complete required trace surface." in report
    assert "- Run B consumed fewer traced tokens than Run A." in report
    assert "- Policy gate decisions differ between the two runs." in report


def test_compare_runs_reports_missing_required_events_for_detected_mode(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    out = tmp_path / "report.md"
    run_a.mkdir()
    run_b.mkdir()
    (run_a / "trace.jsonl").write_text(
        '\n'.join(
            [
                json.dumps(
                    {
                        "event_type": "run_started",
                        "metadata": {"mode": "long-context"},
                    }
                ),
                json.dumps({"event_type": "prompt_build_started"}),
                json.dumps({"event_type": "prompt_built"}),
                json.dumps({"event_type": "model_completed"}),
                json.dumps({"event_type": "verification_started"}),
                json.dumps({"event_type": "verification_completed"}),
                json.dumps({"event_type": "policy_started"}),
                json.dumps({"event_type": "policy_completed"}),
                json.dumps({"event_type": "run_completed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (run_b / "trace.jsonl").write_text(
        '\n'.join(
            [
                json.dumps(
                    {
                        "event_type": "run_started",
                        "metadata": {"mode": "recursive"},
                    }
                ),
                json.dumps({"event_type": "recursive_run_started"}),
                json.dumps({"event_type": "planning_started"}),
                json.dumps({"event_type": "policy_started"}),
                json.dumps({"event_type": "run_completed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = compare_runs(run_a, run_b, out)

    assert "- Run A missing events: none" in report
    assert "Run B missing events:" in report
    assert "planning_completed" in report
    assert "recursive_run_completed" in report
    assert "policy_completed" in report
    assert "synthesis_completed" in report
    assert "verification_completed" in report


def test_compare_runs_writes_to_specified_output_path(tmp_path: Path) -> None:
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    out = tmp_path / "nested" / "report.md"
    run_a.mkdir()
    run_b.mkdir()

    compare_runs(run_a, run_b, out)

    assert out.exists()
