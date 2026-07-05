from __future__ import annotations

from pathlib import Path

from .ingest import load_document_text
from .json_utils import extract_json_object
from .models import DocumentRef, EvidenceCard, VerificationResult
from .providers import LLMProvider
from .trace import TraceWriter

SOURCE_SNIPPET_CHARS = 1_200


def build_source_snippets(source_documents: list[DocumentRef]) -> str:
    snippets: list[str] = []

    for doc in source_documents:
        excerpt = load_document_text(doc)[:SOURCE_SNIPPET_CHARS].strip()
        snippets.append(
            "\n".join(
                [
                    f"Source: {doc.id}",
                    f"Title: {doc.title or doc.source_path}",
                    f"Excerpt: {excerpt}",
                ]
            )
        )

    return "\n\n".join(snippets)


def verification_prompt(
    final_answer: str,
    evidence_cards: list[EvidenceCard],
    source_documents: list[DocumentRef],
) -> str:
    evidence_text = "\n".join(
        f"{e.id} | source={e.source_ref} | claim={e.claim_supported}"
        f" | excerpt={e.quote_or_excerpt} | summary={e.summary}"
        for e in evidence_cards
    )
    source_text = build_source_snippets(source_documents)

    return f"""
You are a strict verifier.

Final answer:
{final_answer}

Evidence cards:
{evidence_text}

Source snippets:
{source_text}

Check whether the final answer is supported by the evidence cards and source snippets.

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
- Use source snippets as the ground truth when judging support and attribution.
- Evidence cards are intermediate summaries, not authoritative by themselves.
- A claim is unsupported if it does not map to the provided source material.
- Mark overgeneralization as unsupported or partially supported.
- Do not reward plausible but uncited claims.
""".strip()


def verify_answer(
    *,
    final_answer: str,
    evidence_cards: list[EvidenceCard],
    source_documents: list[DocumentRef],
    provider: LLMProvider,
    model: str,
    out_dir: Path,
    trace: TraceWriter,
) -> VerificationResult:
    evidence_ids = [e.id for e in evidence_cards]
    source_ids = [doc.id for doc in source_documents]
    trace.emit(
        stage="verification",
        event_type="verification_started",
        actor="verifier",
        input_refs=[*source_ids, *evidence_ids],
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
                "content": verification_prompt(
                    final_answer,
                    evidence_cards,
                    source_documents,
                ),
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
        input_refs=[*source_ids, *evidence_ids],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
        metadata={
            "verdict": result.verdict,
            "unsupported_claims": len(result.unsupported_claims),
            "source_attribution_errors": len(result.source_attribution_errors),
        },
    )

    return result
