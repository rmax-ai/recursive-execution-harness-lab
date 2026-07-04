# Phase 2: Recursive Planner + Evidence Worker

You are implementing two LLM-calling components for the Recursive Execution Harness Lab.

**Project:** `~/src/recursive-execution-harness-lab`
**Context:** Phase 1 (foundational modules) is complete. `src/rxh/models.py`, `providers.py`, `json_utils.py`, `trace.py`, `ingest.py` all exist and pass import checks.
**Read AGENTS.md first** — it's at the project root and defines all conventions.

---

## File 1: `src/rxh/planner.py`

The planner takes a TaskSpec and document metadata (NOT full document text) and creates a decomposition plan.

```python
from __future__ import annotations

from pathlib import Path

from .json_utils import extract_json_object
from .models import DocumentRef, Plan, PlanItem, TaskSpec
from .providers import LLMProvider
from .trace import TraceWriter


def plan_prompt(task: TaskSpec, docs: list[DocumentRef]) -> str:
    """Build a prompt for the planner from document metadata only."""
    doc_lines = "\n".join(
        f"- {d.id}: {d.title or d.source_path} ({d.char_count} chars)"
        for d in docs
    )

    return f"""
You are planning a recursive research workflow.

You receive only document metadata, not full contents.

Task:
{task.question}

Success criteria:
{chr(10).join("- " + x for x in task.success_criteria)}

Constraints:
{chr(10).join("- " + x for x in task.constraints)}

Documents:
{doc_lines}

Create a plan with bounded subquestions. Assign document IDs to each subquestion.

Return JSON with this shape:
{{
  "strategy": "...",
  "items": [
    {{
      "id": "item_001",
      "subquestion": "...",
      "assigned_refs": ["doc_0001"],
      "expected_evidence": ["..."]
    }}
  ],
  "verification_strategy": "..."
}}

Rules:
- Do not assign every document to every worker.
- Prefer 2 to 6 documents per worker.
- Cover all success criteria.
- Do not answer the task.
""".strip()


def create_plan(
    *,
    task: TaskSpec,
    docs: list[DocumentRef],
    provider: LLMProvider,
    model: str,
    out_dir: Path,
    trace: TraceWriter,
) -> Plan:
    """Create a plan using the LLM provider."""
    trace.emit(stage="planning", event_type="planning_started", actor="planner")

    response = provider.complete(
        model=model,
        messages=[
            {"role": "system", "content": "You are a strict workflow planner. Return valid JSON."},
            {"role": "user", "content": plan_prompt(task, docs)},
        ],
        temperature=0.1,
    )

    raw = extract_json_object(response.text)
    plan = Plan.model_validate(raw)

    (out_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    trace.emit(
        stage="planning",
        event_type="planning_completed",
        actor="planner",
        output_refs=[plan.id],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
        metadata={"plan_items": len(plan.items)},
    )

    return plan
```

Key behaviors:
- Calls `extract_json_object()` to parse LLM output
- Uses `Plan.model_validate()` for Pydantic validation
- Writes `plan.json` to the run output directory
- Emits trace events before and after

---

## File 2: `src/rxh/worker.py`

The evidence worker reads ONLY its assigned documents and extracts evidence cards.

```python
from __future__ import annotations

from .ingest import load_document_text
from .json_utils import extract_json_object
from .models import DocumentRef, EvidenceCard, PlanItem, TaskSpec, WorkerResult
from .providers import LLMProvider
from .trace import TraceWriter


def worker_prompt(task: TaskSpec, item: PlanItem, assigned_docs: list[DocumentRef]) -> str:
    """Build a prompt for the evidence worker with full document text."""
    docs_text = []

    for doc in assigned_docs:
        text = load_document_text(doc)
        docs_text.append(f"\n\n--- DOCUMENT {doc.id}: {doc.title or doc.source_path} ---\n{text}")

    return f"""
You are a bounded evidence worker.

Original task:
{task.question}

Your subquestion:
{item.subquestion}

Expected evidence:
{chr(10).join("- " + x for x in item.expected_evidence)}

Assigned documents:
{''.join(docs_text)}

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
    assigned_docs = [docs_by_id[doc_id] for doc_id in item.assigned_refs if doc_id in docs_by_id]

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
            {"role": "system", "content": "You extract evidence. Return valid JSON only."},
            {"role": "user", "content": worker_prompt(task, item, assigned_docs)},
        ],
        temperature=0.1,
    )

    raw = extract_json_object(response.text)

    findings = [
        EvidenceCard(
            id=f"ev_{item.id}_{i:03d}",
            worker_id=worker_id,
            source_ref=finding["source_ref"],
            quote_or_excerpt=finding["quote_or_excerpt"],
            summary=finding["summary"],
            claim_supported=finding["claim_supported"],
            confidence=finding.get("confidence", "medium"),
        )
        for i, finding in enumerate(raw.get("findings", []))
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
        output_refs=[e.id for e in findings],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
        metadata={
            "evidence_cards": len(findings),
            "open_questions": len(result.open_questions),
            "failures": len(result.failures),
        },
    )

    return result
```

Key behaviors:
- Looks up assigned documents from `docs_by_id` dict
- Silently skips missing doc IDs (planner may reference docs that don't exist)
- Calls `extract_json_object()` to parse worker output
- Creates EvidenceCard objects with proper IDs (`ev_{item.id}_{i:03d}`)
- Returns WorkerResult with findings, open_questions, failures

---

## Acceptance Criteria

After creating both files, run:

```bash
cd ~/src/recursive-execution-harness-lab
uv run ruff check src/rxh/planner.py src/rxh/worker.py
uv run ruff format src/rxh/planner.py src/rxh/worker.py
uv run python3 -c "from rxh.planner import plan_prompt, create_plan; print('planner OK')"
uv run python3 -c "from rxh.worker import worker_prompt, run_worker; print('worker OK')"
```

All must pass. Fix issues before reporting completion.
