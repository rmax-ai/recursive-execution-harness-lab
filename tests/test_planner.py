from __future__ import annotations

import json
from pathlib import Path

from rxh.planner import create_plan, plan_prompt
from rxh.providers import MockProvider
from rxh.trace import TraceWriter


def test_plan_prompt_includes_task_question_and_doc_metadata(
    sample_task, sample_docs
) -> None:
    prompt = plan_prompt(sample_task, sample_docs)

    assert sample_task.question in prompt
    assert "doc_0001: Doc1 (200 chars)" in prompt
    assert "doc_0002: Doc2 (300 chars)" in prompt


def test_create_plan_returns_plan_writes_file_and_emits_trace_events(
    sample_task, sample_docs, tmp_path: Path
) -> None:
    provider = MockProvider(
        [
            json.dumps(
                {
                    "strategy": "Break work into two subquestions",
                    "items": [
                        {
                            "id": "item_001",
                            "subquestion": "What does Doc1 say?",
                            "assigned_refs": ["doc_0001"],
                            "expected_evidence": ["A citation from Doc1"],
                        }
                    ],
                    "verification_strategy": "Check each claim against evidence",
                }
            )
        ]
    )
    trace_path = tmp_path / "trace.jsonl"
    trace = TraceWriter(run_id="run_001", path=trace_path)

    plan = create_plan(
        task=sample_task,
        docs=sample_docs,
        provider=provider,
        model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert plan.strategy == "Break work into two subquestions"
    assert (tmp_path / "plan.json").exists()
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "planning_started" in lines[0]
    assert "planning_completed" in lines[1]
