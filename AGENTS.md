# AGENTS.md — Recursive Execution Harness Lab

This document captures conventions for all contributors and AI coding agents.

## 1. Project DNA

**This is a research harness, not a product.** The goal is experimental comparison of two agent architectures. Keep code simple, readable, and falsifiable. Do not over-engineer.

**Core rule:** Every implementation decision should make the benchmark reproducible and the comparison credible. If something doesn't serve that goal, it's scope creep.

## 2. Code Organization

- `src/rxh/` — single flat package. Do NOT create nested subpackages in v1.
- `tests/` — mirrors `src/rxh/` structure: `tests/test_models.py`, `tests/test_ingest.py`, etc.
- `benchmarks/` — task YAML files and sample corpora
- `data/` — raw document corpora for ingestion
- `docs/` — architecture docs, benchmark reports
- `runs/` — output directory (gitignored)

## 3. Python Conventions

- Python 3.12, `from __future__ import annotations` in every module
- Pydantic v2 with `model_config = {"extra": "forbid"}` for all models that go through LLM structured output — Gemini rejects `additionalProperties`. For internal-only models, relax to `"ignore"`.
- Use `datetime.now(UTC)` not `datetime.utcnow()` (deprecated in 3.12)
- Use `Field(default_factory=...)` for mutable defaults, never bare `[]` or `{}`
- Use `Path` not `str` for file paths
- Import order: stdlib, third-party, first-party (ruff I001)
- No `src/__init__.py` — use `src/rxh/__init__.py` only

## 4. Data Models

All models live in `models.py`. They are the single source of truth.

Naming conventions for IDs:
- `doc_NNNN` — documents
- `item_NNN` — plan items
- `ev_item_NNN_NNN` — evidence cards
- `evt_<uuid>` — trace events

Every model MUST have a `model_config` dict.

## 5. LLM Provider Abstraction

- Keep the provider layer THIN. One abstract class, one OpenAI-compatible implementation.
- Use `httpx` directly, not `openai` SDK.
- Always return `LLMResponse` with `text`, `input_tokens`, `output_tokens`.
- `MockProvider` for tests: takes a list of response strings, pops one per call, tracks all calls.
- API key from `OPENAI_API_KEY` env var, base URL from `OPENAI_BASE_URL` env var.

## 6. Prompt Design

- Every LLM call uses `temperature=0.0` or `0.1` for structured output, `0.2` for synthesis.
- JSON responses MUST be parsed via `extract_json_object()` in `json_utils.py` — finds `{` to `}` boundaries.
- System prompts are short and directive ("Return valid JSON only", "You are a strict verifier").
- All prompts are f-strings or triple-quoted strings in the relevant module — no external prompt files.

## 7. Trace Writer

- JSONL format: one `TraceEvent` per line.
- `TraceWriter(path)` constructor. `emit(stage, event_type, actor, ...)` method.
- Required trace events per run:
  - `run_started`, `run_completed`
  - (recursive only) `planning_started`, `planning_completed`, `worker_started`, `worker_completed`, `synthesis_started`, `synthesis_completed`, `verification_started`, `verification_completed`
- Include `token_usage` on every LLM call event.
- Include `input_refs` and `output_refs` on every event that touches documents or evidence cards.

## 8. File I/O Conventions

- JSONL files: write one JSON object per line via `model_dump_json() + "\n"`
- Single JSON files: write via `model_dump_json(indent=2)`
- Always create parent directories before writing: `path.parent.mkdir(parents=True, exist_ok=True)`
- Read with explicit `encoding="utf-8"`

## 9. Error Handling

- `extract_json_object()` raises `ValueError` if no JSON found — caller handles.
- Provider `complete()` raises `httpx.HTTPStatusError` on non-2xx — caller handles.
- Worker failures are recorded in `WorkerResult.failures`, not raised.
- Missing documents are skipped silently in worker (the planner assigned a ref that doesn't exist).

## 10. Testing

- NEVER call real LLM APIs in tests. Use `MockProvider`.
- Test cases per module:
  - `test_models.py`: serialization round-trip for all models
  - `test_ingest.py`: stable IDs, correct hash, char count
  - `test_trace.py`: valid JSONL output, required fields present
  - `test_planner.py`: parses valid plan JSON, handles malformed response
  - `test_worker.py`: produces evidence cards from mock LLM response
  - `test_synthesizer.py`: produces final answer from evidence cards
  - `test_verifier.py`: detects unsupported claims, passes valid answers
  - `test_long_context.py`: builds prompt within char limit
  - `test_recursive.py`: full pipeline writes expected output files
  - `test_compare.py`: handles missing recursive-only files gracefully

## 11. CLI Design

- Typer app at `rxh.cli:app`, entry point `rxh` in pyproject.toml
- Commands: `run`, `compare`, `inspect-trace`
- `run` takes `--task`, `--corpus`, `--mode`, `--model`, `--out`
- `compare` takes two positional args: `run_a`, `run_b`
- Rich tables for comparison output
- Exit with non-zero on failures

## 12. Architecture Non-Negotiables

1. Every run writes the same output shape regardless of mode (empty files for unused artifacts).
2. The verifier is a separate LLM call, not a heuristic.
3. Evidence cards always link to source documents via `source_ref`.
4. The recursive runner calls: planner → workers → synthesizer → verifier, in that order, sequentially.
5. No parallel execution in v1.
6. No database in v1 — filesystem is source of truth.
7. No web app, no distributed execution, no fine-tuning.

## 13. Repository

- GitHub: `rmax-ai/recursive-execution-harness-lab`
- Public, MIT license
- Branching: direct to `main` for solo dev
