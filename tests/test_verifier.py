from __future__ import annotations

import json
from pathlib import Path

from rxh.models import DocumentRef, EvidenceCard
from rxh.providers import MockProvider
from rxh.trace import TraceWriter
from rxh.verifier import verification_prompt, verify_answer


def test_verification_prompt_includes_final_answer_text(tmp_path: Path) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text("Alpha supports bounded execution.", encoding="utf-8")
    source_documents = [
        DocumentRef(
            id="doc_0001",
            source_path=str(doc_path),
            title="Doc1",
            content_hash="hash1",
            char_count=len("Alpha supports bounded execution."),
        )
    ]
    evidence_cards = [
        EvidenceCard(
            id="ev_item_001_000",
            source_ref="doc_0001",
            quote_or_excerpt="Alpha supports bounded execution.",
            summary="The document ties alpha to bounded execution.",
            claim_supported="Bounded execution improves reliability.",
            confidence="high",
            worker_id="worker_item_001",
        )
    ]

    prompt = verification_prompt("Final answer text.", evidence_cards, source_documents)

    assert "Final answer text." in prompt
    assert "ev_item_001_000 | source=doc_0001" in prompt
    assert "Evidence to source map:" in prompt
    assert "ev_item_001_000 -> doc_0001" in prompt
    assert "Source snippets by reference:" in prompt
    assert "doc_0001:" in prompt
    assert "excerpt: Alpha supports bounded execution." in prompt
    assert "excerpt=Alpha supports bounded execution." in prompt
    assert "Source snippets:" in prompt
    assert "Source: doc_0001" in prompt


def test_verify_answer_returns_pass_verdict_and_writes_verification_json(
    tmp_path: Path,
) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text("Alpha supports bounded execution.", encoding="utf-8")
    source_documents = [
        DocumentRef(
            id="doc_0001",
            source_path=str(doc_path),
            title="Doc1",
            content_hash="hash1",
            char_count=len("Alpha supports bounded execution."),
        )
    ]
    evidence_cards = [
        EvidenceCard(
            id="ev_item_001_000",
            source_ref="doc_0001",
            quote_or_excerpt="Alpha supports bounded execution.",
            summary="The document ties alpha to bounded execution.",
            claim_supported="Bounded execution improves reliability.",
            confidence="high",
            worker_id="worker_item_001",
        )
    ]
    provider = MockProvider(
        [
            json.dumps(
                {
                    "verdict": "pass",
                    "checks": [
                        {
                            "claim": "Bounded execution improves reliability.",
                            "supported": True,
                            "evidence_ids": ["ev_item_001_000"],
                            "issue": None,
                        }
                    ],
                    "unsupported_claims": [],
                    "source_attribution_errors": [],
                }
            )
        ]
    )
    trace = TraceWriter(run_id="run_001", path=tmp_path / "trace.jsonl")

    result = verify_answer(
        final_answer="Supported claim [ev_item_001_000].",
        evidence_cards=evidence_cards,
        source_documents=source_documents,
        provider=provider,
        model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result.verdict == "pass"
    saved = json.loads((tmp_path / "verification.json").read_text(encoding="utf-8"))
    assert saved["verdict"] == "pass"


def test_verify_answer_returns_fail_verdict_with_unsupported_claims(
    tmp_path: Path,
) -> None:
    doc_path = tmp_path / "doc1.md"
    doc_path.write_text("Alpha supports bounded execution.", encoding="utf-8")
    source_documents = [
        DocumentRef(
            id="doc_0001",
            source_path=str(doc_path),
            title="Doc1",
            content_hash="hash1",
            char_count=len("Alpha supports bounded execution."),
        )
    ]
    evidence_cards = [
        EvidenceCard(
            id="ev_item_001_000",
            source_ref="doc_0001",
            quote_or_excerpt="Alpha supports bounded execution.",
            summary="The document ties alpha to bounded execution.",
            claim_supported="Bounded execution improves reliability.",
            confidence="high",
            worker_id="worker_item_001",
        )
    ]
    provider = MockProvider(
        [
            json.dumps(
                {
                    "verdict": "fail",
                    "checks": [
                        {
                            "claim": "Beta guarantees correctness.",
                            "supported": False,
                            "evidence_ids": [],
                            "issue": "No supporting evidence provided.",
                        }
                    ],
                    "unsupported_claims": ["Beta guarantees correctness."],
                    "source_attribution_errors": [],
                }
            )
        ]
    )
    trace = TraceWriter(run_id="run_001", path=tmp_path / "trace.jsonl")

    result = verify_answer(
        final_answer="Beta guarantees correctness.",
        evidence_cards=evidence_cards,
        source_documents=source_documents,
        provider=provider,
        model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result.verdict == "fail"
    assert result.unsupported_claims == ["Beta guarantees correctness."]
