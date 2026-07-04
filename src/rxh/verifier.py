from __future__ import annotations

from pathlib import Path

from .json_utils import extract_json_object
from .models import EvidenceCard, VerificationResult
from .providers import LLMProvider
from .trace import TraceWriter


def verification_prompt(final_answer: str, evidence_cards: list[EvidenceCard]) -> str:
    evidence_text = "\n".join(
        f"{e.id} | source={e.source_ref} | claim={e.claim_supported}"
        f" | summary={e.summary}"
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
    evidence_ids = [e.id for e in evidence_cards]
    trace.emit(
        stage="verification",
        event_type="verification_started",
        actor="verifier",
        input_refs=evidence_ids,
    )

    response = provider.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a strict evidence verifier. Return JSON only.",
            },
            {
                "role": "user",
                "content": verification_prompt(final_answer, evidence_cards),
            },
        ],
        temperature=0.0,
    )

    raw = extract_json_object(response.text)
    result = VerificationResult.model_validate(raw)

    out_dir.mkdir(parents=True, exist_ok=True)
    verification_path = out_dir / "verification.json"
    verification_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    trace.emit(
        stage="verification",
        event_type="verification_completed",
        actor="verifier",
        input_refs=evidence_ids,
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
        metadata={
            "verdict": result.verdict,
            "unsupported_claims": len(result.unsupported_claims),
            "source_attribution_errors": len(result.source_attribution_errors),
        },
    )

    return result
