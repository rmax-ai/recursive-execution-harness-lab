from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
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
    task: Annotated[Path, typer.Option(help="Path to task YAML file")],
    corpus: Annotated[Path, typer.Option(help="Path to corpus directory")],
    mode: Annotated[
        str, typer.Option(help="Execution mode: 'long-context' or 'recursive'")
    ],
    out: Annotated[Path, typer.Option(help="Output directory for this run")],
    model: Annotated[str, typer.Option(help="Model name")] = "gpt-5.4-mini",
    verifier_model: Annotated[
        str, typer.Option(help="Verifier model name")
    ] = "gpt-5.4-mini",
):
    """Run a benchmark task."""
    run_id = f"run_{uuid4().hex[:8]}"
    out.mkdir(parents=True, exist_ok=True)

    task_spec = TaskSpec.model_validate(
        yaml.safe_load(task.read_text(encoding="utf-8"))
    )
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
    run_a: Annotated[Path, typer.Argument(help="Path to first run directory")],
    run_b: Annotated[Path, typer.Argument(help="Path to second run directory")],
    out: Annotated[
        Path | None, typer.Option(help="Output path for report (default: stdout)")
    ] = None,
):
    """Compare two benchmark runs."""
    if out:
        report = compare_runs(run_a, run_b, out)
        console.print(f"[green]Report written to {out}[/green]")
    else:
        report = compare_runs(run_a, run_b, Path("/dev/null"))
        console.print(report)


@app.command()
def inspect_trace(
    run_dir: Annotated[Path, typer.Argument(help="Path to run directory")],
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
