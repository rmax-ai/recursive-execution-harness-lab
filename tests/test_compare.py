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
    (run_a / "trace.jsonl").write_text('{"event":"a"}\n', encoding="utf-8")
    (run_b / "trace.jsonl").write_text('{"event":"b"}\n', encoding="utf-8")

    report = compare_runs(run_a, run_b, out)

    assert "Verification verdict | n/a | n/a" in report
    assert out.read_text(encoding="utf-8") == report


def test_compare_runs_with_two_valid_run_dirs_produces_markdown_report(
    tmp_path: Path,
) -> None:
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    out = tmp_path / "report.md"
    run_a.mkdir()
    run_b.mkdir()
    (run_a / "evidence_cards.jsonl").write_text('{"id":"ev1"}\n', encoding="utf-8")
    (run_b / "evidence_cards.jsonl").write_text(
        '{"id":"ev1"}\n{"id":"ev2"}\n', encoding="utf-8"
    )
    (run_a / "trace.jsonl").write_text('{"event":"a"}\n', encoding="utf-8")
    (run_b / "trace.jsonl").write_text(
        '{"event":"a"}\n{"event":"b"}\n', encoding="utf-8"
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

    report = compare_runs(run_a, run_b, out)

    assert report.startswith("# Run Comparison")
    assert "| Evidence cards | 1 | 2 |" in report
    assert "| Verification verdict | pass | partial |" in report


def test_compare_runs_writes_to_specified_output_path(tmp_path: Path) -> None:
    run_a = tmp_path / "run_a"
    run_b = tmp_path / "run_b"
    out = tmp_path / "nested" / "report.md"
    run_a.mkdir()
    run_b.mkdir()

    compare_runs(run_a, run_b, out)

    assert out.exists()
