from __future__ import annotations

import json
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
    provider = MockProvider(
        [
            "# Baseline Answer\n\nAnswer from long context.",
            json.dumps(
                {
                    "verdict": "partial",
                    "checks": [
                        {
                            "claim": "Unsupported claim.",
                            "supported": False,
                            "evidence_ids": [],
                            "issue": "No support found.",
                        }
                    ],
                    "unsupported_claims": ["Unsupported claim."],
                    "source_attribution_errors": [],
                }
            ),
            "# Baseline Answer\n\nRevised answer from long context.",
            json.dumps(
                {
                    "verdict": "pass",
                    "checks": [],
                    "unsupported_claims": [],
                    "source_attribution_errors": [],
                }
            ),
            json.dumps(
                {
                    "decision": "allow",
                    "rationale": "Verifier found no blocking issues.",
                    "required_changes": [],
                    "blocked_claims": [],
                }
            ),
        ]
    )
    trace = TraceWriter(run_id="run_001", path=tmp_path / "trace.jsonl")

    result = run_long_context(
        run_id="run_001",
        task=sample_task,
        docs=docs,
        provider=provider,
        model="gpt-test",
        verifier_model="gpt-verify",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result == "# Baseline Answer\n\nRevised answer from long context."
    assert (tmp_path / "final_answer.md").read_text(encoding="utf-8") == result
    assert (tmp_path / "plan.json").exists()
    assert (tmp_path / "worker_results.jsonl").read_text(encoding="utf-8") == ""
    assert (tmp_path / "evidence_cards.jsonl").read_text(encoding="utf-8") == ""
    policy = json.loads((tmp_path / "policy_decision.json").read_text(encoding="utf-8"))
    assert policy["decision"] == "allow"

    verification = json.loads(
        (tmp_path / "verification.json").read_text(encoding="utf-8")
    )
    assert verification["verdict"] == "pass"

    plan = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    assert plan["items"] == []
    assert "Long-context baseline" in plan["strategy"]

    trace_lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    assert any('"stage":"verification"' in line for line in trace_lines)
    assert any('"stage":"revision"' in line for line in trace_lines)
    assert any('"stage":"policy"' in line for line in trace_lines)
    assert len(provider.calls) == 4
    assert provider.calls[1]["model"] == "gpt-verify"
    verifier_prompt = provider.calls[1]["messages"][1]["content"]
    assert "Evidence to source map:" in verifier_prompt
    assert "none" in verifier_prompt
    assert "Source snippets by reference:" in verifier_prompt
    assert "doc_0001:" in verifier_prompt
    assert "Source snippets:" in verifier_prompt
    assert "Source: doc_0001" in verifier_prompt
    assert "Excerpt: Document body" in verifier_prompt
    revision_prompt = provider.calls[2]["messages"][1]["content"]
    assert "Unsupported claims:" in revision_prompt
    policy = json.loads((tmp_path / "policy_decision.json").read_text(encoding="utf-8"))
    assert policy["decision"] == "allow"
