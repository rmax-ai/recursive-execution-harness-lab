from __future__ import annotations

from pathlib import Path

from rxh.trace import TraceWriter


def test_trace_writer_creates_directory(tmp_path: Path) -> None:
    trace_path = tmp_path / "nested" / "trace.jsonl"

    TraceWriter(run_id="run_001", path=trace_path)

    assert trace_path.parent.exists()


def test_emit_writes_valid_jsonl_line_and_returns_event(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    writer = TraceWriter(run_id="run_001", path=trace_path)

    event = writer.emit(
        stage="planning", event_type="planning_started", actor="planner"
    )

    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert event.run_id == "run_001"
    assert event.stage == "planning"
    assert "planning_started" in lines[0]


def test_two_emits_produce_two_lines(tmp_path: Path) -> None:
    trace_path = tmp_path / "trace.jsonl"
    writer = TraceWriter(run_id="run_001", path=trace_path)

    writer.emit(stage="planning", event_type="planning_started", actor="planner")
    writer.emit(stage="planning", event_type="planning_completed", actor="planner")

    assert len(trace_path.read_text(encoding="utf-8").splitlines()) == 2
