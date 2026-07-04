# Phase 3: Synthesizer + Verifier

You are implementing the synthesis and verification components.

**Project:** `~/src/recursive-execution-harness-lab`
**Context:** Phases 1-2 complete. models.py, providers.py, json_utils.py, trace.py, ingest.py, planner.py, worker.py all exist.
**Read AGENTS.md first.**

---

## File 1: `src/rxh/synthesizer.py`

Synthesizes a final answer from evidence cards.

```python
from __future__ import annotations

from pathlib import Path

from .models import EvidenceCard, Plan, TaskSpec
from .providers import LLMProvider
from .trace import TraceWriter


def synthesis_prompt(task: TaskSpec, plan: Plan, evidence_cards: list[EvidenceCard]) -> str:
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
            {"role": "system", "content": "You synthesize strictly from provided evidence."},
            {"role": "user", "content": synthesis_prompt(task, plan, evidence_cards)},
        ],
        temperature=0.2,
    )

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
```

---

## File 2: `src/rxh/verifier.py`

Verifies that the final answer is supported by evidence cards.

```python
from __future__ import annotations

from pathlib import Path

from .json_utils import extract_json_object
from .models import EvidenceCard, VerificationResult
from .providers import LLMProvider
from .trace import TraceWriter


def verification_prompt(final_answer: str, evidence_cards: list[EvidenceCard]) -> str:
    evidence_text = "\n".join(
        f"{e.id} | source={e.source_ref} | claim={e.claim_supported} | summary={e.summary}"
        for e in evidence_cards
    )

    return f"""
You are a strict verifier.

Final answer:
{final_answer}

Evidence cards:
{evidence_text}

Check whether the final answer is supported by the evidence.

Return JSON with this shape:
{{
  "verdict": "pass|partial|fail",
  "checks": [
    {{
      "claim": "...",
      "supported": true,
      "evidence_ids": ["ev_..."],
      "issue": null
    }}
  ],
  "unsupported_claims": ["..."],
  "source_attribution_errors": ["..."]
}}

Rules:
- Be strict.
- A claim is unsupported if it does not map to evidence.
- Mark overgeneralization as unsupported or partially supported.
- Do not reward plausible but uncited claims.
""".strip()


def verify_answer(
    *,
    final_answer: str,
    evidence_cards: list[EvidenceCard],
    provider: LLMProvider,
    model: str,
    out_dir: Path,
    trace: TraceWriter,
) -> VerificationResult:
    trace.emit(stage="verification", event_type="verification_started", actor="verifier")

    response = provider.complete(
        model=model,
        messages=[
            {"role": "system", "content": "You are a strict evidence verifier. Return JSON only."},
            {"role": "user", "content": verification_prompt(final_answer, evidence_cards)},
        ],
        temperature=0.0,
    )

    raw = extract_json_object(response.text)
    result = VerificationResult.model_validate(raw)

    (out_dir / "verification.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")

    trace.emit(
        stage="verification",
        event_type="verification_completed",
        actor="verifier",
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
        metadata={
            "verdict": result.verdict,
            "unsupported_claims": len(result.unsupported_claims),
            "source_attribution_errors": len(result.source_attribution_errors),
        },
    )

    return result
```

---

## Acceptance Criteria

```bash
cd ~/src/recursive-execution-harness-lab
uv run ruff check src/rxh/synthesizer.py src/rxh/verifier.py
uv run ruff format src/rxh/synthesizer.py src/rxh/verifier.py
uv run python3 -c "from rxh.synthesizer import synthesis_prompt, synthesize_answer; print('synthesizer OK')"
uv run python3 -c "from rxh.verifier import verification_prompt, verify_answer; print('verifier OK')"
```
