from __future__ import annotations

from pathlib import Path

from rxh.long_context import build_long_context_prompt, run_long_context
from rxh.models import DocumentRef
from rxh.providers import MockProvider
from rxh.trace import TraceWriter


def test_build_long_context_prompt_stays_within_max_chars_budget(
    sample_task, tmp_path: Path
) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text("A" * 500, encoding="utf-8")
    docs = [
        DocumentRef(
            id="doc_0001",
            source_path=str(doc_path),
            title="Large Doc",
            content_hash="hash1",
            char_count=500,
        )
    ]

    prompt = build_long_context_prompt(sample_task, docs, max_chars=120)

    assert len(prompt) < 500
    assert "--- DOCUMENT doc_0001: Large Doc ---" not in prompt


def test_build_long_context_prompt_includes_task_question_and_success_criteria(
    sample_task, tmp_path: Path
) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text("Document body", encoding="utf-8")
    docs = [
        DocumentRef(
            id="doc_0001",
            source_path=str(doc_path),
            title="Doc1",
            content_hash="hash1",
            char_count=len("Document body"),
        )
    ]

    prompt = build_long_context_prompt(sample_task, docs, max_chars=10_000)

    assert sample_task.question in prompt
    assert "Success criteria:" in prompt
    assert "- Use sources" in prompt


def test_run_long_context_calls_provider_and_writes_final_answer(
    sample_task, tmp_path: Path
) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text("Document body", encoding="utf-8")
    docs = [
        DocumentRef(
            id="doc_0001",
            source_path=str(doc_path),
            title="Doc1",
            content_hash="hash1",
            char_count=len("Document body"),
        )
    ]
    provider = MockProvider(["# Baseline Answer\n\nAnswer from long context."])
    trace = TraceWriter(run_id="run_001", path=tmp_path / "trace.jsonl")

    result = run_long_context(
        run_id="run_001",
        task=sample_task,
        docs=docs,
        provider=provider,
        model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result == "# Baseline Answer\n\nAnswer from long context."
    assert (tmp_path / "final_answer.md").read_text(encoding="utf-8") == result
    assert len(provider.calls) == 1
