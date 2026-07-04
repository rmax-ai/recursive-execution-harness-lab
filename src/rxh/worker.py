from __future__ import annotations

from .ingest import load_document_text
from .json_utils import extract_json_object
from .models import DocumentRef, EvidenceCard, PlanItem, TaskSpec, WorkerResult
from .providers import LLMProvider
from .trace import TraceWriter


def worker_prompt(
    task: TaskSpec, item: PlanItem, assigned_docs: list[DocumentRef]
) -> str:
    """Build a prompt for the evidence worker with full document text."""
    docs_text: list[str] = []

    for doc in assigned_docs:
        text = load_document_text(doc)
        docs_text.append(
            f"\n\n--- DOCUMENT {doc.id}: {doc.title or doc.source_path} ---\n{text}"
        )

    return f"""
You are a bounded evidence worker.

Original task:
{task.question}

Your subquestion:
{item.subquestion}

Expected evidence:
{chr(10).join("- " + evidence for evidence in item.expected_evidence)}

Assigned documents:
{"".join(docs_text)}

Return JSON with this shape:
{{
  "findings": [
    {{
      "source_ref": "doc_0001",
      "quote_or_excerpt": "short exact or near-exact excerpt",
      "summary": "what this evidence says",
      "claim_supported": "the claim this evidence supports",
      "confidence": "low|medium|high"
    }}
  ],
  "open_questions": ["..."],
  "failures": ["..."]
}}

Rules:
- Use only assigned documents.
- Do not write the final answer.
- Keep excerpts short.
- Do not invent sources.
- Mark uncertainty explicitly.
""".strip()


def run_worker(
    *,
    task: TaskSpec,
    item: PlanItem,
    docs_by_id: dict[str, DocumentRef],
    provider: LLMProvider,
    model: str,
    trace: TraceWriter,
) -> WorkerResult:
    """Run a single bounded evidence worker."""
    worker_id = f"worker_{item.id}"
    assigned_docs = [
        docs_by_id[doc_id] for doc_id in item.assigned_refs if doc_id in docs_by_id
    ]

    trace.emit(
        stage="worker",
        event_type="worker_started",
        actor=worker_id,
        input_refs=item.assigned_refs,
        metadata={"subquestion": item.subquestion},
    )

    response = provider.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You extract evidence. Return valid JSON only.",
            },
            {"role": "user", "content": worker_prompt(task, item, assigned_docs)},
        ],
        temperature=0.1,
    )

    raw = extract_json_object(response.text)
    findings = [
        EvidenceCard(
            id=f"ev_{item.id}_{index:03d}",
            worker_id=worker_id,
            source_ref=finding["source_ref"],
            quote_or_excerpt=finding["quote_or_excerpt"],
            summary=finding["summary"],
            claim_supported=finding["claim_supported"],
            confidence=finding.get("confidence", "medium"),
        )
        for index, finding in enumerate(raw.get("findings", []))
    ]

    result = WorkerResult(
        worker_id=worker_id,
        plan_item_id=item.id,
        subquestion=item.subquestion,
        assigned_refs=item.assigned_refs,
        findings=findings,
        open_questions=raw.get("open_questions", []),
        failures=raw.get("failures", []),
    )

    trace.emit(
        stage="worker",
        event_type="worker_completed",
        actor=worker_id,
        input_refs=item.assigned_refs,
        output_refs=[evidence.id for evidence in findings],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
        metadata={
            "evidence_cards": len(findings),
            "open_questions": len(result.open_questions),
            "failures": len(result.failures),
        },
    )

    return result
