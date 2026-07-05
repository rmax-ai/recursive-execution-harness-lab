from __future__ import annotations

import json
from pathlib import Path

from rxh.models import DocumentRef, PlanItem
from rxh.providers import MockProvider
from rxh.trace import TraceWriter
from rxh.worker import run_worker, worker_prompt


def test_worker_prompt_includes_subquestion_and_bounded_source_slices(
    sample_task, tmp_path: Path
) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text(
        "Overview section.\n\nTarget evidence about bounded execution.\n\n"
        "Tail section.",
        encoding="utf-8",
    )
    doc = DocumentRef(
        id="doc_0001",
        source_path=str(doc_path),
        title="Doc1",
        content_hash="hash1",
        char_count=len(doc_path.read_text(encoding="utf-8")),
    )
    item = PlanItem(
        id="item_001",
        subquestion="What supports bounded execution?",
        assigned_refs=["doc_0001"],
        expected_evidence=["bounded execution"],
    )
    source_slices = [(doc, 1, "Target evidence about bounded execution.")]

    prompt = worker_prompt(sample_task, item, [doc], source_slices)

    assert item.subquestion in prompt
    assert "Target evidence about bounded execution." in prompt
    assert "--- SOURCE SLICE doc_0001#1: Doc1 ---" in prompt
    assert "Assigned document refs:" in prompt
    assert "Use only the provided source slices" in prompt


def test_run_worker_returns_worker_result_and_emits_trace_events(
    sample_task, tmp_path: Path
) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text("Alpha fact.", encoding="utf-8")
    doc = DocumentRef(
        id="doc_0001",
        source_path=str(doc_path),
        title="Doc1",
        content_hash="hash1",
        char_count=len("Alpha fact."),
    )
    item = PlanItem(
        id="item_001",
        subquestion="What fact is present?",
        assigned_refs=["doc_0001"],
        expected_evidence=["The stated fact"],
    )
    provider = MockProvider(
        [
            json.dumps(
                {
                    "findings": [
                        {
                            "source_ref": "doc_0001",
                            "quote_or_excerpt": "Alpha fact.",
                            "summary": "The document states Alpha fact.",
                            "claim_supported": "Alpha fact is present.",
                            "confidence": "high",
                        }
                    ],
                    "open_questions": [],
                    "failures": [],
                }
            )
        ]
    )
    trace_path = tmp_path / "trace.jsonl"
    trace = TraceWriter(run_id="run_001", path=trace_path)

    result = run_worker(
        task=sample_task,
        item=item,
        docs_by_id={"doc_0001": doc},
        provider=provider,
        model="gpt-test",
        trace=trace,
    )

    assert result.worker_id == "worker_item_001"
    assert len(result.findings) == 1
    assert result.findings[0].source_ref == "doc_0001"
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "worker_started" in lines[0]
    assert "worker_completed" in lines[1]
    worker_prompt_text = provider.calls[0]["messages"][1]["content"]
    assert "Retrieved source slices:" in worker_prompt_text


def test_run_worker_handles_missing_doc_refs_gracefully(
    sample_task, tmp_path: Path
) -> None:
    item = PlanItem(
        id="item_002",
        subquestion="What evidence is available?",
        assigned_refs=["doc_9999"],
        expected_evidence=[],
    )
    provider = MockProvider(
        [
            json.dumps(
                {
                    "findings": [],
                    "open_questions": ["No assigned documents were available."],
                    "failures": [],
                }
            )
        ]
    )
    trace = TraceWriter(run_id="run_001", path=tmp_path / "trace.jsonl")

    result = run_worker(
        task=sample_task,
        item=item,
        docs_by_id={},
        provider=provider,
        model="gpt-test",
        trace=trace,
    )

    assert result.assigned_refs == ["doc_9999"]
    assert result.findings == []
    assert result.open_questions == ["No assigned documents were available."]
