from __future__ import annotations

from pathlib import Path

from .ingest import load_document_text
from .models import DocumentRef, TaskSpec
from .providers import LLMProvider
from .trace import TraceWriter


def build_long_context_prompt(
    task: TaskSpec, docs: list[DocumentRef], max_chars: int = 300_000
) -> str:
    """Concatenate document text into a single prompt within a character budget."""
    chunks: list[str] = []
    used = 0

    for doc in docs:
        text = load_document_text(doc)
        block = f"\n\n--- DOCUMENT {doc.id}: {doc.title or doc.source_path} ---\n{text}"
        if used + len(block) > max_chars:
            break
        chunks.append(block)
        used += len(block)

    return f"""
You are answering a research task using the provided documents.

Task:
{task.question}

Success criteria:
{chr(10).join("- " + criterion for criterion in task.success_criteria)}

Constraints:
{chr(10).join("- " + constraint for constraint in task.constraints)}

Use document IDs when citing evidence.

Documents:
{"".join(chunks)}

Return a complete answer with:
1. Main answer
2. Key claims
3. Sources used
4. Uncertainties and gaps
""".strip()


def run_long_context(
    *,
    run_id: str,
    task: TaskSpec,
    docs: list[DocumentRef],
    provider: LLMProvider,
    model: str,
    out_dir: Path,
    trace: TraceWriter,
) -> str:
    """Run the baseline single-prompt workflow across the provided documents."""
    del run_id

    doc_ids = [doc.id for doc in docs]
    trace.emit(
        stage="baseline",
        event_type="prompt_build_started",
        actor="long_context_runner",
        input_refs=doc_ids,
        metadata={"task_id": task.id},
    )
    prompt = build_long_context_prompt(task, docs)
    trace.emit(
        stage="baseline",
        event_type="prompt_built",
        actor="long_context_runner",
        input_refs=doc_ids,
        metadata={"prompt_chars": len(prompt), "task_id": task.id},
    )

    response = provider.complete(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a rigorous technical research assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    trace.emit(
        stage="baseline",
        event_type="model_completed",
        actor="llm",
        input_refs=doc_ids,
        output_refs=["final_answer.md"],
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
    )

    final_path = out_dir / "final_answer.md"
    final_path.parent.mkdir(parents=True, exist_ok=True)
    final_path.write_text(response.text, encoding="utf-8")

    return response.text
