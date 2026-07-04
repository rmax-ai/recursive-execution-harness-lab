from __future__ import annotations

from pathlib import Path

from .models import TraceEvent


class TraceWriter:
    """Writes trace events as JSONL to a file."""

    def __init__(self, run_id: str, path: Path):
        self.run_id = run_id
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def emit(
        self,
        *,
        stage: str,
        event_type: str,
        actor: str,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None,
        token_usage: dict[str, int] | None = None,
        metadata: dict | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            run_id=self.run_id,
            stage=stage,
            event_type=event_type,
            actor=actor,
            input_refs=input_refs or [],
            output_refs=output_refs or [],
            token_usage=token_usage or {},
            metadata=metadata or {},
        )
        with self.path.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")
        return event
