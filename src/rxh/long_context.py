from __future__ import annotations

from pathlib import Path

from .ingest import load_document_text
from .models import DocumentRef, Plan, TaskSpec
from .policy import apply_policy_gate
from .providers import LLMProvider
from .synthesizer import revise_answer
from .trace import TraceWriter
from .verifier import verify_answer


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


def write_baseline_artifacts(task: TaskSpec, out_dir: Path) -> None:
    """Write empty baseline artifacts so both modes share the same output shape."""
    del task
    plan = Plan(
        strategy="Long-context baseline: answer in one prompt without decomposition.",
        items=[],
        verification_strategy=(
            "Verify the single baseline answer against the original task and corpus."
        ),
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "plan.json").write_text(plan.model_dump_json(indent=2), encoding="utf-8")
    (out_dir / "worker_results.jsonl").write_text("", encoding="utf-8")
    (out_dir / "evidence_cards.jsonl").write_text("", encoding="utf-8")


def run_long_context(
    *,
    run_id: str,
    task: TaskSpec,
    docs: list[DocumentRef],
    provider: LLMProvider,
    model: str,
    verifier_model: str,
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
    write_baseline_artifacts(task, out_dir)
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

    final_answer = response.text
    verification = verify_answer(
        final_answer=final_answer,
        evidence_cards=[],
        source_documents=docs,
        provider=provider,
        model=verifier_model,
        out_dir=out_dir,
        trace=trace,
    )

    if verification.verdict != "pass":
        final_answer = revise_answer(
            task=task,
            evidence_cards=[],
            final_answer=final_answer,
            verification=verification,
            provider=provider,
            model=model,
            out_dir=out_dir,
            trace=trace,
        )
        verification = verify_answer(
            final_answer=final_answer,
            evidence_cards=[],
            source_documents=docs,
            provider=provider,
            model=verifier_model,
            out_dir=out_dir,
            trace=trace,
        )

    apply_policy_gate(
        task=task,
        final_answer=final_answer,
        verification=verification,
        out_dir=out_dir,
        trace=trace,
    )

    return final_answer
