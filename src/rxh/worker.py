from __future__ import annotations

import re

from .ingest import load_document_text
from .json_utils import extract_json_object
from .models import DocumentRef, EvidenceCard, PlanItem, TaskSpec, WorkerResult
from .providers import LLMProvider
from .trace import TraceWriter

MAX_SOURCE_SLICE_CHARS = 1_200
MAX_SLICES_PER_DOC = 2
CHUNK_OVERLAP_CHARS = 160
CHUNK_SIZE_CHARS = 900


def query_terms(task: TaskSpec, item: PlanItem) -> set[str]:
    """Build a simple lexical query for source-slice selection."""
    text = " ".join(
        [
            task.question,
            item.subquestion,
            *item.expected_evidence,
        ]
    )
    return {
        term
        for term in re.findall(r"[a-z0-9]{4,}", text.lower())
        if term not in {"with", "this", "that", "from", "what", "does", "have"}
    }


def chunk_text(text: str, size: int = CHUNK_SIZE_CHARS) -> list[str]:
    """Split text into overlapping chunks for bounded retrieval."""
    stripped = text.strip()
    if not stripped:
        return []
    if len(stripped) <= size:
        return [stripped]

    chunks: list[str] = []
    start = 0
    while start < len(stripped):
        end = min(len(stripped), start + size)
        chunks.append(stripped[start:end].strip())
        if end == len(stripped):
            break
        start = max(end - CHUNK_OVERLAP_CHARS, start + 1)
    return chunks


def score_chunk(chunk: str, terms: set[str]) -> tuple[int, int]:
    """Score chunks by lexical overlap, breaking ties by shorter excerpts."""
    lowered = chunk.lower()
    overlap = sum(1 for term in terms if term in lowered)
    return overlap, -len(chunk)


def select_source_slices(
    task: TaskSpec,
    item: PlanItem,
    assigned_docs: list[DocumentRef],
) -> list[tuple[DocumentRef, int, str]]:
    """Retrieve bounded source slices keyed by source_ref for worker input."""
    terms = query_terms(task, item)
    selected: list[tuple[DocumentRef, int, str]] = []

    for doc in assigned_docs:
        chunks = chunk_text(load_document_text(doc))
        if not chunks:
            continue

        scored = sorted(
            enumerate(chunks, start=1),
            key=lambda pair: score_chunk(pair[1], terms),
            reverse=True,
        )
        for index, chunk in scored[:MAX_SLICES_PER_DOC]:
            selected.append((doc, index, chunk[:MAX_SOURCE_SLICE_CHARS].strip()))

    return selected


def normalize_excerpt(text: str) -> str:
    return " ".join(text.split()).strip().lower()


def validate_findings(
    findings: list[dict],
    item: PlanItem,
    source_slices: list[tuple[DocumentRef, int, str]],
) -> tuple[list[EvidenceCard], list[str]]:
    allowed_refs = set(item.assigned_refs)
    normalized_slices_by_ref: dict[str, list[str]] = {}
    for doc, _, chunk in source_slices:
        normalized_slices_by_ref.setdefault(doc.id, []).append(normalize_excerpt(chunk))

    validated: list[EvidenceCard] = []
    failures: list[str] = []
    worker_id = f"worker_{item.id}"

    for index, finding in enumerate(findings):
        source_ref = finding["source_ref"]
        excerpt = finding["quote_or_excerpt"]

        if source_ref not in allowed_refs:
            failures.append(
                f"Rejected finding {index}: source_ref {source_ref} was not assigned."
            )
            continue

        normalized_excerpt = normalize_excerpt(excerpt)
        source_chunks = normalized_slices_by_ref.get(source_ref, [])
        if normalized_excerpt and not any(
            normalized_excerpt in chunk for chunk in source_chunks
        ):
            failures.append(
                f"Rejected finding {index}: excerpt for {source_ref} "
                "was not found in retrieved source slices."
            )
            continue

        validated.append(
            EvidenceCard(
                id=f"ev_{item.id}_{index:03d}",
                worker_id=worker_id,
                source_ref=source_ref,
                quote_or_excerpt=excerpt,
                summary=finding["summary"],
                claim_supported=finding["claim_supported"],
                confidence=finding.get("confidence", "medium"),
            )
        )

    return validated, failures


def worker_prompt(
    task: TaskSpec,
    item: PlanItem,
    assigned_docs: list[DocumentRef],
    source_slices: list[tuple[DocumentRef, int, str]],
) -> str:
    """Build a prompt for the evidence worker with bounded source slices."""
    docs_text = "\n".join(
        (
            f"\n\n--- SOURCE SLICE {doc.id}#{slice_index}: "
            f"{doc.title or doc.source_path} ---\n{chunk}"
        )
        for doc, slice_index, chunk in source_slices
    )

    return f"""
You are a bounded evidence worker.

Original task:
{task.question}

Your subquestion:
{item.subquestion}

Expected evidence:
{chr(10).join("- " + evidence for evidence in item.expected_evidence)}

Assigned document refs:
{chr(10).join("- " + doc.id for doc in assigned_docs) or "none"}

Retrieved source slices:
{docs_text or "none"}

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
- Use only the provided source slices from the assigned document refs.
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
    source_slices = select_source_slices(task, item, assigned_docs)

    trace.emit(
        stage="worker",
        event_type="worker_started",
        actor=worker_id,
        input_refs=item.assigned_refs,
        metadata={
            "subquestion": item.subquestion,
            "source_slices": len(source_slices),
        },
    )

    response = provider.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You extract evidence. Return valid JSON only.",
            },
            {
                "role": "user",
                "content": worker_prompt(task, item, assigned_docs, source_slices),
            },
        ],
        temperature=0.1,
    )

    raw = extract_json_object(response.text)
    findings, validation_failures = validate_findings(
        raw.get("findings", []), item, source_slices
    )

    result = WorkerResult(
        worker_id=worker_id,
        plan_item_id=item.id,
        subquestion=item.subquestion,
        assigned_refs=item.assigned_refs,
        findings=findings,
        open_questions=raw.get("open_questions", []),
        failures=[*raw.get("failures", []), *validation_failures],
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
