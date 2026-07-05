from __future__ import annotations

from pathlib import Path

from .models import EvidenceCard, Plan, TaskSpec, VerificationResult
from .providers import LLMProvider
from .trace import TraceWriter


def synthesis_prompt(
    task: TaskSpec, plan: Plan, evidence_cards: list[EvidenceCard]
) -> str:
    evidence_text = "\n".join(
        f"""
Evidence ID: {e.id}
Source: {e.source_ref}
Claim supported: {e.claim_supported}
Confidence: {e.confidence}
Excerpt: {e.quote_or_excerpt}
Summary: {e.summary}
""".strip()
        for e in evidence_cards
    )

    return f"""
You are synthesizing a final answer from an evidence store.

Original task:
{task.question}

Success criteria:
{chr(10).join("- " + x for x in task.success_criteria)}

Constraints:
{chr(10).join("- " + x for x in task.constraints)}

Plan strategy:
{plan.strategy}

Evidence cards:
{evidence_text}

Write the final answer in Markdown.

Rules:
- Every substantial claim must cite evidence IDs inline like [ev_xxx].
- Separate supported claims from hypotheses.
- Include gaps and uncertainties.
- Do not introduce claims not supported by evidence cards.
""".strip()


def synthesize_answer(
    *,
    task: TaskSpec,
    plan: Plan,
    evidence_cards: list[EvidenceCard],
    provider: LLMProvider,
    model: str,
    out_dir: Path,
    trace: TraceWriter,
) -> str:
    trace.emit(
        stage="synthesis",
        event_type="synthesis_started",
        actor="synthesizer",
        input_refs=[e.id for e in evidence_cards],
    )

    response = provider.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You synthesize strictly from provided evidence.",
            },
            {"role": "user", "content": synthesis_prompt(task, plan, evidence_cards)},
        ],
        temperature=0.2,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = out_dir / "final_answer.md"
    final_path.write_text(response.text, encoding="utf-8")

    trace.emit(
        stage="synthesis",
        event_type="synthesis_completed",
        actor="synthesizer",
        input_refs=[e.id for e in evidence_cards],
        output_refs=["final_answer.md"],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
    )

    return response.text


def revision_prompt(
    *,
    task: TaskSpec,
    evidence_cards: list[EvidenceCard],
    final_answer: str,
    verification: VerificationResult,
) -> str:
    evidence_text = "\n".join(
        f"{card.id} | source={card.source_ref} | claim={card.claim_supported}"
        f" | excerpt={card.quote_or_excerpt}"
        for card in evidence_cards
    )
    checks_text = "\n".join(
        f"- claim={check.claim} | supported={check.supported}"
        f" | evidence_ids={check.evidence_ids} | issue={check.issue}"
        for check in verification.checks
    )

    return f"""
You are revising a final answer after verification found issues.

Original task:
{task.question}

Constraints:
{chr(10).join("- " + x for x in task.constraints)}

Current answer:
{final_answer}

Evidence cards:
{evidence_text or "none"}

Verification verdict:
{verification.verdict}

Unsupported claims:
{chr(10).join("- " + claim for claim in verification.unsupported_claims) or "none"}

Source attribution errors:
{chr(10).join("- " + issue for issue in verification.source_attribution_errors)
or "none"}

Verification checks:
{checks_text or "none"}

Revise the answer in Markdown.

Rules:
- Remove or rewrite unsupported claims.
- Fix source attribution problems.
- Keep inline evidence citations like [ev_xxx] only for supported claims.
- Do not introduce new claims not grounded in the evidence cards.
- Include remaining uncertainty when evidence is incomplete.
""".strip()


def revise_answer(
    *,
    task: TaskSpec,
    evidence_cards: list[EvidenceCard],
    final_answer: str,
    verification: VerificationResult,
    provider: LLMProvider,
    model: str,
    out_dir: Path,
    trace: TraceWriter,
) -> str:
    evidence_ids = [e.id for e in evidence_cards]
    trace.emit(
        stage="revision",
        event_type="revision_started",
        actor="reviser",
        input_refs=["final_answer.md", verification.id, *evidence_ids],
        metadata={"verification_verdict": verification.verdict},
    )

    response = provider.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You revise answers strictly from evidence and verifier "
                    "feedback."
                ),
            },
            {
                "role": "user",
                "content": revision_prompt(
                    task=task,
                    evidence_cards=evidence_cards,
                    final_answer=final_answer,
                    verification=verification,
                ),
            },
        ],
        temperature=0.1,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    final_path = out_dir / "final_answer.md"
    final_path.write_text(response.text, encoding="utf-8")

    trace.emit(
        stage="revision",
        event_type="revision_completed",
        actor="reviser",
        input_refs=["final_answer.md", verification.id, *evidence_ids],
        output_refs=["final_answer.md"],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
    )

    return response.text
