from __future__ import annotations

import json
from pathlib import Path

from rxh.models import EvidenceCard
from rxh.providers import MockProvider
from rxh.trace import TraceWriter
from rxh.verifier import verification_prompt, verify_answer


def test_verification_prompt_includes_final_answer_text() -> None:
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

    prompt = verification_prompt("Final answer text.", evidence_cards)

    assert "Final answer text." in prompt
    assert "ev_item_001_000 | source=doc_0001" in prompt


def test_verify_answer_returns_pass_verdict_and_writes_verification_json(
    tmp_path: Path,
) -> None:
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
        provider=provider,
        model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result.verdict == "fail"
    assert result.unsupported_claims == ["Beta guarantees correctness."]
