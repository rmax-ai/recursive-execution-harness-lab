# Phase 4: Long-context Baseline + Recursive Runner Orchestration

**Project:** `~/src/recursive-execution-harness-lab`
**Context:** All modules through verifier exist and import cleanly.
**Read AGENTS.md first.**

---

## File 1: `src/rxh/long_context.py`

Baseline runner that stuffs documents into a single prompt.

```python
from __future__ import annotations

from pathlib import Path

from .ingest import load_document_text
from .models import DocumentRef, TaskSpec
from .providers import LLMProvider
from .trace import TraceWriter


def build_long_context_prompt(task: TaskSpec, docs: list[DocumentRef], max_chars: int = 300_000) -> str:
    """Concatenate documents until char budget, format as prompt."""
    chunks = []
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
{chr(10).join("- " + x for x in task.success_criteria)}

Constraints:
{chr(10).join("- " + x for x in task.constraints)}

Use document IDs when citing evidence.

Documents:
{''.join(chunks)}

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
    trace.emit(stage="baseline", event_type="prompt_build_started", actor="long_context_runner")
    prompt = build_long_context_prompt(task, docs)
    trace.emit(
        stage="baseline",
        event_type="prompt_built",
        actor="long_context_runner",
        input_refs=[d.id for d in docs],
        metadata={"prompt_chars": len(prompt)},
    )

    response = provider.complete(
        model=model,
        messages=[
            {"role": "system", "content": "You are a rigorous technical research assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    trace.emit(
        stage="baseline",
        event_type="model_completed",
        actor="llm",
        token_usage={"input": response.input_tokens, "output": response.output_tokens},
    )

    final_path = out_dir / "final_answer.md"
    final_path.write_text(response.text, encoding="utf-8")

    return response.text
```

---

## File 2: `src/rxh/recursive.py`

Orchestrates the full recursive pipeline: planner → workers → synthesizer → verifier.

```python
from __future__ import annotations

from pathlib import Path

from .models import DocumentRef, TaskSpec
from .planner import create_plan
from .providers import LLMProvider
from .synthesizer import synthesize_answer
from .trace import TraceWriter
from .verifier import verify_answer
from .worker import run_worker


def write_worker_results(results, out_dir: Path) -> None:
    """Write worker results as JSONL."""
    with (out_dir / "worker_results.jsonl").open("w", encoding="utf-8") as f:
        for result in results:
            f.write(result.model_dump_json() + "\n")


def write_evidence_cards(cards, out_dir: Path) -> None:
    """Write evidence cards as JSONL."""
    with (out_dir / "evidence_cards.jsonl").open("w", encoding="utf-8") as f:
        for card in cards:
            f.write(card.model_dump_json() + "\n")


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
    docs_by_id = {d.id: d for d in docs}

    trace.emit(stage="run", event_type="recursive_run_started", actor="runner")

    # 1. Plan
    plan = create_plan(
        task=task,
        docs=docs,
        provider=provider,
        model=model,
        out_dir=out_dir,
        trace=trace,
    )

    # 2. Workers (sequential, not parallel)
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

    # 3. Collect evidence
    evidence_cards = [card for result in worker_results for card in result.findings]
    write_worker_results(worker_results, out_dir)
    write_evidence_cards(evidence_cards, out_dir)

    # 4. Synthesize
    final_answer = synthesize_answer(
        task=task,
        plan=plan,
        evidence_cards=evidence_cards,
        provider=provider,
        model=model,
        out_dir=out_dir,
        trace=trace,
    )

    # 5. Verify
    verify_answer(
        final_answer=final_answer,
        evidence_cards=evidence_cards,
        provider=provider,
        model=verifier_model,
        out_dir=out_dir,
        trace=trace,
    )

    trace.emit(stage="run", event_type="recursive_run_completed", actor="runner")

    return final_answer
```

---

## File 3: `src/rxh/compare.py`

```python
from __future__ import annotations

import json
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.open("r", encoding="utf-8"))


def compare_runs(run_a: Path, run_b: Path, out: Path) -> str:
    verify_a = load_json(run_a / "verification.json")
    verify_b = load_json(run_b / "verification.json")

    evidence_a = count_jsonl(run_a / "evidence_cards.jsonl")
    evidence_b = count_jsonl(run_b / "evidence_cards.jsonl")

    trace_a = count_jsonl(run_a / "trace.jsonl")
    trace_b = count_jsonl(run_b / "trace.jsonl")

    report = f"""
# Run Comparison

## Inputs

- Run A: `{run_a}`
- Run B: `{run_b}`

## Metrics

| Metric | Run A | Run B |
|---|---:|---:|
| Evidence cards | {evidence_a} | {evidence_b} |
| Trace events | {trace_a} | {trace_b} |
| Unsupported claims | {len(verify_a.get("unsupported_claims", []))} | {len(verify_b.get("unsupported_claims", []))} |
| Source attribution errors | {len(verify_a.get("source_attribution_errors", []))} | {len(verify_b.get("source_attribution_errors", []))} |
| Verification verdict | {verify_a.get("verdict", "n/a")} | {verify_b.get("verdict", "n/a")} |

## Interpretation

Add qualitative analysis here.
""".strip()

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    return report
```

---

## Acceptance Criteria

```bash
cd ~/src/recursive-execution-harness-lab
uv run ruff check src/rxh/long_context.py src/rxh/recursive.py src/rxh/compare.py
uv run ruff format src/rxh/long_context.py src/rxh/recursive.py src/rxh/compare.py
uv run python3 -c "from rxh.long_context import build_long_context_prompt, run_long_context; print('long_context OK')"
uv run python3 -c "from rxh.recursive import run_recursive, write_worker_results, write_evidence_cards; print('recursive OK')"
uv run python3 -c "from rxh.compare import compare_runs, load_json, count_jsonl; print('compare OK')"
```
