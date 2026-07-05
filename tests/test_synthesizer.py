from __future__ import annotations

from pathlib import Path

from rxh.models import ClaimCheck, EvidenceCard, Plan, PlanItem, VerificationResult
from rxh.providers import MockProvider
from rxh.synthesizer import (
    revise_answer,
    revision_prompt,
    synthesis_prompt,
    synthesize_answer,
)
from rxh.trace import TraceWriter


def test_synthesis_prompt_includes_evidence_cards_and_task_question(
    sample_task,
) -> None:
    plan = Plan(
        strategy="Synthesize evidence by theme",
        items=[
            PlanItem(
                id="item_001",
                subquestion="What is the main finding?",
                assigned_refs=["doc_0001"],
            )
        ],
        verification_strategy="Check each claim against evidence",
    )
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

    prompt = synthesis_prompt(sample_task, plan, evidence_cards)

    assert sample_task.question in prompt
    assert "Evidence ID: ev_item_001_000" in prompt
    assert "Source: doc_0001" in prompt
    assert "Alpha supports bounded execution." in prompt


def test_synthesize_answer_calls_provider_writes_file_and_emits_trace_events(
    sample_task, tmp_path: Path
) -> None:
    plan = Plan(
        strategy="Synthesize evidence by theme",
        items=[
            PlanItem(
                id="item_001",
                subquestion="What is the main finding?",
                assigned_refs=["doc_0001"],
            )
        ],
        verification_strategy="Check each claim against evidence",
    )
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
    provider = MockProvider(["# Final Answer\n\nSupported claim [ev_item_001_000]."])
    trace_path = tmp_path / "trace.jsonl"
    trace = TraceWriter(run_id="run_001", path=trace_path)

    result = synthesize_answer(
        task=sample_task,
        plan=plan,
        evidence_cards=evidence_cards,
        provider=provider,
        model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result == "# Final Answer\n\nSupported claim [ev_item_001_000]."
    assert (tmp_path / "final_answer.md").read_text(encoding="utf-8") == result
    assert len(provider.calls) == 1
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert "synthesis_started" in lines[0]
    assert "synthesis_completed" in lines[1]


def test_revision_prompt_includes_verifier_feedback(sample_task) -> None:
    verification = VerificationResult(
        verdict="partial",
        checks=[
            ClaimCheck(
                claim="Unsupported claim",
                supported=False,
                evidence_ids=[],
                issue="No support found.",
            )
        ],
        unsupported_claims=["Unsupported claim"],
        source_attribution_errors=[],
    )

    prompt = revision_prompt(
        task=sample_task,
        evidence_cards=[],
        final_answer="Unsupported claim",
        verification=verification,
    )

    assert "Verification verdict:" in prompt
    assert "Unsupported claim" in prompt
    assert "Remove or rewrite unsupported claims." in prompt


def test_revise_answer_writes_final_answer_and_emits_trace_events(
    sample_task, tmp_path: Path
) -> None:
    provider = MockProvider(["# Final Answer\n\nRevised supported answer."])
    verification = VerificationResult(
        verdict="partial",
        checks=[],
        unsupported_claims=["Unsupported claim"],
        source_attribution_errors=[],
    )
    trace_path = tmp_path / "trace.jsonl"
    trace = TraceWriter(run_id="run_001", path=trace_path)

    result = revise_answer(
        task=sample_task,
        evidence_cards=[],
        final_answer="Unsupported claim",
        verification=verification,
        provider=provider,
        model="gpt-test",
        out_dir=tmp_path,
        trace=trace,
    )

    assert result == "# Final Answer\n\nRevised supported answer."
    assert (tmp_path / "final_answer.md").read_text(encoding="utf-8") == result
    lines = trace_path.read_text(encoding="utf-8").splitlines()
    assert "revision_started" in lines[0]
    assert "revision_completed" in lines[1]
