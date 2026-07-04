from __future__ import annotations

from pathlib import Path

from .models import DocumentRef, EvidenceCard, TaskSpec, WorkerResult
from .planner import create_plan
from .providers import LLMProvider
from .synthesizer import synthesize_answer
from .trace import TraceWriter
from .verifier import verify_answer
from .worker import run_worker


def write_worker_results(results: list[WorkerResult], out_dir: Path) -> None:
    """Write worker results as JSONL."""
    path = out_dir / "worker_results.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file_obj:
        for result in results:
            file_obj.write(result.model_dump_json() + "\n")


def write_evidence_cards(cards: list[EvidenceCard], out_dir: Path) -> None:
    """Write evidence cards as JSONL."""
    path = out_dir / "evidence_cards.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file_obj:
        for card in cards:
            file_obj.write(card.model_dump_json() + "\n")


def run_recursive(
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
    """Run the planner, workers, synthesizer, and verifier sequentially."""
    del run_id

    docs_by_id = {doc.id: doc for doc in docs}
    doc_ids = [doc.id for doc in docs]

    trace.emit(
        stage="run",
        event_type="recursive_run_started",
        actor="runner",
        input_refs=doc_ids,
        metadata={"task_id": task.id},
    )

    plan = create_plan(
        task=task,
        docs=docs,
        provider=provider,
        model=model,
        out_dir=out_dir,
        trace=trace,
    )

    worker_results = [
        run_worker(
            task=task,
            item=item,
            docs_by_id=docs_by_id,
            provider=provider,
            model=model,
            trace=trace,
        )
        for item in plan.items
    ]

    evidence_cards = [card for result in worker_results for card in result.findings]
    write_worker_results(worker_results, out_dir)
    write_evidence_cards(evidence_cards, out_dir)

    final_answer = synthesize_answer(
        task=task,
        plan=plan,
        evidence_cards=evidence_cards,
        provider=provider,
        model=model,
        out_dir=out_dir,
        trace=trace,
    )

    verify_answer(
        final_answer=final_answer,
        evidence_cards=evidence_cards,
        provider=provider,
        model=verifier_model,
        out_dir=out_dir,
        trace=trace,
    )

    trace.emit(
        stage="run",
        event_type="recursive_run_completed",
        actor="runner",
        input_refs=doc_ids,
        output_refs=["final_answer.md", "verification.json"],
        metadata={
            "plan_id": plan.id,
            "worker_results": len(worker_results),
            "evidence_cards": len(evidence_cards),
        },
    )

    return final_answer
