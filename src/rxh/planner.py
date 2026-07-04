from __future__ import annotations

from pathlib import Path

from .json_utils import extract_json_object
from .models import DocumentRef, Plan, TaskSpec
from .providers import LLMProvider
from .trace import TraceWriter


def plan_prompt(task: TaskSpec, docs: list[DocumentRef]) -> str:
    """Build a prompt for the planner from document metadata only."""
    doc_lines = "\n".join(
        f"- {doc.id}: {doc.title or doc.source_path} ({doc.char_count} chars)"
        for doc in docs
    )

    return f"""
You are planning a recursive research workflow.

You receive only document metadata, not full contents.

Task:
{task.question}

Success criteria:
{chr(10).join("- " + criterion for criterion in task.success_criteria)}

Constraints:
{chr(10).join("- " + constraint for constraint in task.constraints)}

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
    doc_ids = [doc.id for doc in docs]
    trace.emit(
        stage="planning",
        event_type="planning_started",
        actor="planner",
        input_refs=doc_ids,
        metadata={"task_id": task.id},
    )

    response = provider.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a strict workflow planner. Return valid JSON.",
            },
            {"role": "user", "content": plan_prompt(task, docs)},
        ],
        temperature=0.1,
    )

    raw = extract_json_object(response.text)
    plan = Plan.model_validate(raw)

    plan_path = out_dir / "plan.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    trace.emit(
        stage="planning",
        event_type="planning_completed",
        actor="planner",
        input_refs=doc_ids,
        output_refs=[plan.id],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
        metadata={"plan_items": len(plan.items), "task_id": task.id},
    )

    return plan
