# Phase 5: CLI + Sample Corpus + Benchmark Task

**Project:** `~/src/recursive-execution-harness-lab`
**Context:** All modules through compare.py exist and import. Now build the CLI and sample data.
**Read AGENTS.md first.**

---

## File 1: `src/rxh/cli.py`

Typer CLI with `rxh run` and `rxh compare` commands.

```python
from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import typer
import yaml
from rich.console import Console
from rich.table import Table

from .compare import compare_runs
from .ingest import ingest_corpus
from .long_context import run_long_context
from .models import TaskSpec
from .providers import OpenAICompatibleProvider
from .recursive import run_recursive
from .trace import TraceWriter

app = typer.Typer()
console = Console()


@app.command()
def run(
    task: Path = typer.Option(..., help="Path to task YAML file"),
    corpus: Path = typer.Option(..., help="Path to corpus directory"),
    mode: str = typer.Option(..., help="Execution mode: 'long-context' or 'recursive'"),
    model: str = typer.Option("gpt-5.5-thinking", help="Model name"),
    verifier_model: str = typer.Option("gpt-5.5-thinking", help="Verifier model name"),
    out: Path = typer.Option(..., help="Output directory for this run"),
):
    """Run a benchmark task."""
    run_id = f"run_{uuid4().hex[:8]}"
    out.mkdir(parents=True, exist_ok=True)

    task_spec = TaskSpec.model_validate(yaml.safe_load(task.read_text(encoding="utf-8")))
    (out / "task.yaml").write_text(task.read_text(encoding="utf-8"), encoding="utf-8")

    trace = TraceWriter(run_id=run_id, path=out / "trace.jsonl")
    provider = OpenAICompatibleProvider()

    trace.emit(
        stage="run",
        event_type="run_started",
        actor="cli",
        metadata={"mode": mode, "model": model, "document_count": 0},
    )

    docs = ingest_corpus(corpus, out / "documents.jsonl")

    if mode == "long-context":
        run_long_context(
            run_id=run_id,
            task=task_spec,
            docs=docs,
            provider=provider,
            model=model,
            out_dir=out,
            trace=trace,
        )
    elif mode == "recursive":
        run_recursive(
            run_id=run_id,
            task=task_spec,
            docs=docs,
            provider=provider,
            model=model,
            verifier_model=verifier_model,
            out_dir=out,
            trace=trace,
        )
    else:
        raise typer.BadParameter("mode must be 'long-context' or 'recursive'")

    trace.emit(stage="run", event_type="run_completed", actor="cli")
    console.print(f"[green]Run written to {out}[/green]")


@app.command()
def compare(
    run_a: Path = typer.Argument(..., help="Path to first run directory"),
    run_b: Path = typer.Argument(..., help="Path to second run directory"),
    out: Path = typer.Option(None, help="Output path for report (default: stdout)"),
):
    """Compare two benchmark runs."""
    report = compare_runs(run_a, run_b, out or Path("/dev/stdout"))
    if not out:
        console.print(report)
    else:
        console.print(f"[green]Report written to {out}[/green]")


@app.command()
def inspect_trace(
    run_dir: Path = typer.Argument(..., help="Path to run directory"),
):
    """Inspect trace events from a run."""
    trace_path = run_dir / "trace.jsonl"
    if not trace_path.exists():
        console.print("[red]No trace.jsonl found in run directory.[/red]")
        raise typer.Exit(1)

    events = []
    with trace_path.open("r", encoding="utf-8") as f:
        for line in f:
            events.append(json.loads(line))

    table = Table(title=f"Trace Events — {run_dir.name}")
    table.add_column("Stage", style="cyan")
    table.add_column("Event", style="green")
    table.add_column("Actor", style="yellow")
    table.add_column("Tokens (in/out)", style="magenta")

    for e in events:
        tokens = e.get("token_usage", {})
        token_str = f"{tokens.get('input', 0)}/{tokens.get('output', 0)}"
        table.add_row(e["stage"], e["event_type"], e["actor"], token_str)

    console.print(table)


if __name__ == "__main__":
    app()
```

---

## Files 2-9: Sample Corpus (8 Markdown files)

Create `benchmarks/research_synthesis/corpora/sample/` with these 8 files. Each file should be 150-400 words with a title, source URL comment, short summary, relevant excerpts, and notes.

### `001_context_window_limits.md`
Title: Context Window Limits in Long-Running Agents
- Explains that stuffing everything into context degrades performance beyond ~128K tokens
- Research from Anthropic and Google shows attention dilution in long contexts
- Key claim: "needle-in-haystack" tests show retrieval accuracy drops after 100K tokens

### `002_recursive_execution_pattern.md`
Title: Recursive Execution as an Alternative Architecture
- Describes the pattern: decompose, dispatch, collect, synthesize, verify
- References Claude's computer use and SWE-agent architectures
- Key claim: externalizing state reduces the model's cognitive load

### `003_durable_workflows.md`
Title: Durable Workflows and State Externalization
- Temporal, Prefect, and workflow engines as inspirations
- Key claim: long-running agents need durable state outside the model context
- Describes checkpointing, retry, and idempotency

### `004_mcp_protocol.md`
Title: Model Context Protocol and Tool Governance
- MCP as a standard for agent-tool communication
- Key claim: governed tool access prevents runaway agent behavior
- Describes scope, permissions, and policy enforcement

### `005_evidence_tracing.md`
Title: Evidence Tracing and Provenance in Agent Workflows
- Why evidence provenance matters for trust
- Key claim: every agent claim should link to source evidence
- Describes trace-based verification

### `006_policy_as_code.md`
Title: Policy-as-Code for Agent Governance
- OPA, Rego, and policy enforcement for agents
- Key claim: agents need runtime policy gates, not just prompt instructions
- Describes permission models and audit trails

### `007_autonomous_coding_agents.md`
Title: Autonomous Coding Agents and Their Failure Modes
- SWE-bench results, coding agents that succeed and fail
- Key claim: the biggest failure mode is context drift over long sessions
- Describes how agents lose track of objectives

### `008_verification_gates.md`
Title: Verification Gates in Multi-Step Agent Workflows
- Why post-hoc verification improves final output quality
- Key claim: separating generation from verification reduces hallucination
- Describes verifier-checker patterns

---

## File 10: `benchmarks/research_synthesis/tasks/recursive_execution.yaml`

```yaml
id: recursive_execution_article
title: Recursive Execution for Long-Running Agents
question: >
  Write a technical synthesis explaining why long-running AI agents need
  recursive execution, externalized state, and verification gates rather than
  relying only on larger context windows.
expected_output_type: article
success_criteria:
  - Explain failure modes of long-context agent execution
  - Explain recursive execution using references, bounded workers, and evidence stores
  - Discuss durable execution and policy gates
  - Include counterarguments and limitations
  - Ground major claims in the provided documents
constraints:
  - Do not make unsupported vendor claims
  - Distinguish evidence from speculation
  - Prefer primary sources when present
evaluation_questions:
  - Are major claims supported by source evidence?
  - Does the answer avoid overgeneralization?
  - Does it explain trade-offs?
  - Does it identify remaining failure modes?
```

---

## Acceptance Criteria

```bash
cd ~/src/recursive-execution-harness-lab
uv run ruff check src/rxh/cli.py
uv run ruff format src/rxh/cli.py
uv run python3 -c "from rxh.cli import app; print('cli OK')"
# Verify corpus files exist
ls benchmarks/research_synthesis/corpora/sample/*.md | wc -l  # should be 8
# Verify task YAML loads
uv run python3 -c "import yaml; from rxh.models import TaskSpec; t = TaskSpec.model_validate(yaml.safe_load(open('benchmarks/research_synthesis/tasks/recursive_execution.yaml'))); print(f'task loaded: {t.id}')"
```
