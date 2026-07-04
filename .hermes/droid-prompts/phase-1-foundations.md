# Phase 1: Foundational Modules — models, providers, json_utils, trace, ingest

You are implementing the first 5 foundational modules for the Recursive Execution Harness Lab. These are pure infrastructure — no LLM calls, no orchestration. Just data models and I/O utilities.

**Project:** `~/src/recursive-execution-harness-lab`
**Python:** 3.12
**Deps installed:** `uv sync --extra dev` already run
**Read AGENTS.md first** — it's at the project root and defines all conventions.

---

## Files to Create

### 1. `src/rxh/models.py` — All Pydantic v2 data models

Use `from __future__ import annotations` at top.

Helper functions:
```python
from datetime import datetime, timezone
from uuid import uuid4

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"
```

Models (all with `model_config = {"extra": "forbid"}`):

**TaskSpec:**
- id: str
- title: str
- question: str
- expected_output_type: Literal["article", "report", "answer", "plan"] = "report"
- success_criteria: list[str] = Field(default_factory=list)
- constraints: list[str] = Field(default_factory=list)
- evaluation_questions: list[str] = Field(default_factory=list)

**DocumentRef:**
- id: str
- source_path: str
- title: str | None = None
- content_hash: str
- char_count: int
- metadata: dict[str, Any] = Field(default_factory=dict)

**EvidenceCard:**
- id: str
- source_ref: str
- quote_or_excerpt: str
- summary: str
- claim_supported: str
- confidence: Literal["low", "medium", "high"] = "medium"
- worker_id: str
- created_at: datetime = Field(default_factory=now_utc)

**PlanItem:**
- id: str
- subquestion: str
- assigned_refs: list[str]
- expected_evidence: list[str] = Field(default_factory=list)

**Plan:**
- id: str = Field(default_factory=lambda: new_id("plan"))
- strategy: str
- items: list[PlanItem]
- verification_strategy: str

**WorkerResult:**
- worker_id: str
- plan_item_id: str
- subquestion: str
- assigned_refs: list[str]
- findings: list[EvidenceCard]
- open_questions: list[str] = Field(default_factory=list)
- failures: list[str] = Field(default_factory=list)

**ClaimCheck:**
- claim: str
- supported: bool
- evidence_ids: list[str] = Field(default_factory=list)
- issue: str | None = None

**VerificationResult:**
- id: str = Field(default_factory=lambda: new_id("verify"))
- verdict: Literal["pass", "partial", "fail"]
- checks: list[ClaimCheck]
- unsupported_claims: list[str] = Field(default_factory=list)
- source_attribution_errors: list[str] = Field(default_factory=list)

**TraceEvent:**
- run_id: str
- event_id: str = Field(default_factory=lambda: new_id("evt"))
- timestamp: datetime = Field(default_factory=now_utc)
- stage: str
- event_type: str
- actor: str
- input_refs: list[str] = Field(default_factory=list)
- output_refs: list[str] = Field(default_factory=list)
- token_usage: dict[str, int] = Field(default_factory=dict)
- metadata: dict[str, Any] = Field(default_factory=dict)

**RunMetrics:**
- run_id: str
- mode: Literal["long-context", "recursive"]
- token_input_estimate: int = 0
- token_output_estimate: int = 0
- wall_clock_seconds: float = 0
- document_count: int = 0
- evidence_card_count: int = 0
- unsupported_claim_count: int = 0
- source_attribution_error_count: int = 0
- verification_verdict: str | None = None

### 2. `src/rxh/providers.py` — LLM provider abstraction

```python
from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass
class LLMResponse:
    text: str
    input_tokens: int = 0
    output_tokens: int = 0


class LLMProvider:
    """Abstract base class for LLM providers."""
    def complete(self, *, model: str, messages: list[dict], temperature: float = 0.2) -> LLMResponse:
        raise NotImplementedError


class OpenAICompatibleProvider(LLMProvider):
    """OpenAI-compatible chat completions provider."""
    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key or os.environ["OPENAI_API_KEY"]
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/")

    def complete(self, *, model: str, messages: list[dict], temperature: float = 0.2) -> LLMResponse:
        payload = {"model": model, "messages": messages, "temperature": temperature}
        with httpx.Client(timeout=120) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        text = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
        )


class MockProvider(LLMProvider):
    """Mock provider for tests. Returns predefined responses in order."""
    def __init__(self, responses: list[str]):
        self.responses = responses
        self.calls: list[dict] = []

    def complete(self, *, model: str, messages: list[dict], temperature: float = 0.2) -> LLMResponse:
        self.calls.append({"model": model, "messages": messages, "temperature": temperature})
        text = self.responses.pop(0)
        return LLMResponse(text=text, input_tokens=100, output_tokens=50)
```

### 3. `src/rxh/json_utils.py` — JSON extraction utility

```python
from __future__ import annotations

import json


def extract_json_object(text: str) -> dict:
    """Extract the first complete JSON object from text.
    
    Finds the first '{' and last '}' and parses the content between them.
    Raises ValueError if no JSON object is found.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response.")
    return json.loads(text[start : end + 1])
```

### 4. `src/rxh/trace.py` — JSONL trace writer

```python
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
```

### 5. `src/rxh/ingest.py` — Corpus ingestion

```python
from __future__ import annotations

import hashlib
from pathlib import Path

from .models import DocumentRef

SUPPORTED_EXTENSIONS = {".md", ".txt"}


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def ingest_corpus(corpus_path: Path, out_path: Path) -> list[DocumentRef]:
    """Walk corpus directory, read .md/.txt files, produce DocumentRef list and JSONL output."""
    docs: list[DocumentRef] = []
    out_path.parent.mkdir(parents=True, exist_ok=True)

    for i, path in enumerate(sorted(corpus_path.rglob("*"))):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        doc = DocumentRef(
            id=f"doc_{i:04d}",
            source_path=str(path),
            title=path.stem,
            content_hash=hash_text(text),
            char_count=len(text),
            metadata={"extension": path.suffix.lower()},
        )
        docs.append(doc)

    with out_path.open("w", encoding="utf-8") as f:
        for doc in docs:
            f.write(doc.model_dump_json() + "\n")

    return docs


def load_document_text(doc: DocumentRef) -> str:
    """Read the full text of a document from its source path."""
    return Path(doc.source_path).read_text(encoding="utf-8", errors="ignore")


def load_documents_jsonl(path: Path) -> list[DocumentRef]:
    """Load DocumentRef objects from a JSONL file."""
    docs = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            docs.append(DocumentRef.model_validate_json(line))
    return docs
```

---

## Acceptance Criteria

After creating all 5 files, run these verification commands IN ORDER:

```bash
cd ~/src/recursive-execution-harness-lab
uv run ruff check src/rxh/models.py src/rxh/providers.py src/rxh/json_utils.py src/rxh/trace.py src/rxh/ingest.py
uv run ruff format src/rxh/models.py src/rxh/providers.py src/rxh/json_utils.py src/rxh/trace.py src/rxh/ingest.py
uv run python3 -c "from rxh.models import TaskSpec, DocumentRef, EvidenceCard, PlanItem, Plan, WorkerResult, ClaimCheck, VerificationResult, TraceEvent, RunMetrics; print('models OK')"
uv run python3 -c "from rxh.providers import LLMProvider, OpenAICompatibleProvider, MockProvider, LLMResponse; print('providers OK')"
uv run python3 -c "from rxh.json_utils import extract_json_object; print('json_utils OK')"
uv run python3 -c "from rxh.trace import TraceWriter; print('trace OK')"
uv run python3 -c "from rxh.ingest import ingest_corpus, load_document_text, load_documents_jsonl; print('ingest OK')"
```

All must pass with zero errors. Fix any issues before reporting completion.
