from __future__ import annotations

from pathlib import Path

from .models import EvidenceCard, Plan, TaskSpec
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
