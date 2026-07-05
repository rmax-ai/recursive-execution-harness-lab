from __future__ import annotations

import json
from pathlib import Path

from rxh.models import DocumentRef
from rxh.providers import MockProvider
from rxh.recursive import run_recursive
from rxh.trace import TraceWriter


def test_run_recursive_with_mock_provider_completes_full_pipeline(
    sample_task, tmp_path: Path
) -> None:
    doc1_path = tmp_path / "doc1.md"
    doc2_path = tmp_path / "doc2.md"
    doc1_path.write_text("Alpha evidence.", encoding="utf-8")
    doc2_path.write_text("Beta evidence.", encoding="utf-8")
    docs = [
        DocumentRef(
            id="doc_0001",
            source_path=str(doc1_path),
            title="Doc1",
            content_hash="hash1",
            char_count=len("Alpha evidence."),
        ),
        DocumentRef(
            id="doc_0002",
            source_path=str(doc2_path),
            title="Doc2",
            content_hash="hash2",
            char_count=len("Beta evidence."),
        ),
    ]
    provider = MockProvider(
        [
            json.dumps(
                {
                    "strategy": "Split evidence collection by document.",
                    "items": [
                        {
                            "id": "item_001",
                            "subquestion": "What does the first document support?",
                            "assigned_refs": ["doc_0001"],
                            "expected_evidence": ["Alpha evidence"],
                        },
                        {
                            "id": "item_002",
                            "subquestion": "What does the second document support?",
                            "assigned_refs": ["doc_0002"],
                            "expected_evidence": ["Beta evidence"],
                        },
                    ],
                    "verification_strategy": "Check every final claim.",
                }
            ),
            json.dumps(
                {
                    "findings": [
                        {
                            "source_ref": "doc_0001",
                            "quote_or_excerpt": "Alpha evidence.",
                            "summary": "The first document provides alpha evidence.",
                            "claim_supported": "Alpha is supported.",
                            "confidence": "high",
                        }
                    ],
                    "open_questions": [],
                    "failures": [],
                }
            ),
            json.dumps(
                {
                    "findings": [
                        {
                            "source_ref": "doc_0002",
                            "quote_or_excerpt": "Beta evidence.",
                            "summary": "The second document provides beta evidence.",
                            "claim_supported": "Beta is supported.",
                            "confidence": "high",
                        }
                    ],
                    "open_questions": [],
                    "failures": [],
                }
            ),
            (
                "# Final Answer\n\nAlpha is supported [ev_item_001_000]. "
                "Beta is supported [ev_item_002_000]."
            ),
            json.dumps(
                {
                    "verdict": "partial",
                    "checks": [
                        {
                            "claim": "Alpha is supported.",
                            "supported": True,
                            "evidence_ids": ["ev_item_001_000"],
                            "issue": None,
                        },
                        {
                            "claim": "Beta is supported.",
                            "supported": True,
                            "evidence_ids": ["ev_item_002_000"],
                            "issue": None,
                        },
                        {
                            "claim": "Beta is comprehensive.",
                            "supported": False,
                            "evidence_ids": [],
                            "issue": "Overgeneralized.",
                        },
                    ],
                    "unsupported_claims": ["Beta is comprehensive."],
                    "source_attribution_errors": [],
                }
            ),
            (
                "# Final Answer\n\nAlpha is supported [ev_item_001_000]. "
                "Beta is supported [ev_item_002_000]."
            ),
            json.dumps(
                {
                    "verdict": "pass",
                    "checks": [
                        {
                            "claim": "Alpha is supported.",
                            "supported": True,
                            "evidence_ids": ["ev_item_001_000"],
                            "issue": None,
                        },
                        {
                            "claim": "Beta is supported.",
                            "supported": True,
                            "evidence_ids": ["ev_item_002_000"],
                            "issue": None,
                        },
                    ],
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
    trace_path = tmp_path / "trace.jsonl"
    trace = TraceWriter(run_id="run_001", path=trace_path)

    result = run_recursive(
        run_id="run_001",
        task=sample_task,
        docs=docs,
        provider=provider,
        model="gpt-test",
        verifier_model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result.startswith("# Final Answer")
    assert (tmp_path / "plan.json").exists()
    assert (tmp_path / "worker_results.jsonl").exists()
    assert (tmp_path / "evidence_cards.jsonl").exists()
    assert (tmp_path / "final_answer.md").exists()
    assert (tmp_path / "verification.json").exists()
    assert (tmp_path / "policy_decision.json").exists()

    trace_lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert any('"stage":"planning"' in line for line in trace_lines)
    assert any('"stage":"worker"' in line for line in trace_lines)
    assert any('"stage":"synthesis"' in line for line in trace_lines)
    assert any('"stage":"verification"' in line for line in trace_lines)
    assert any('"stage":"revision"' in line for line in trace_lines)
    assert any('"stage":"policy"' in line for line in trace_lines)
    assert any('"stage":"run"' in line for line in trace_lines)

    policy = json.loads((tmp_path / "policy_decision.json").read_text(encoding="utf-8"))
    assert policy["decision"] == "allow"
    revision_prompt = provider.calls[-2]["messages"][1]["content"]
    assert "Unsupported claims:" in revision_prompt
    verification_prompt = provider.calls[-3]["messages"][1]["content"]
    assert "Source snippets:" in verification_prompt
    assert "Source: doc_0001" in verification_prompt
    assert "Source: doc_0002" in verification_prompt
    assert "excerpt=Alpha evidence." in verification_prompt
