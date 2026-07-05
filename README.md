# Recursive Execution Harness Lab

A research harness for comparing long-context agent execution against recursive, reference-indexed bounded execution on multi-document research synthesis tasks.

## Research Question

When does recursive, reference-indexed bounded execution outperform naive long-context prompting for long-running agent tasks?

## Architecture

```mermaid
flowchart TD
    A[Task Spec] --> B[Corpus Ingestion]
    B --> C[Document Refs]
    C --> D[Planner]
    D --> E[Plan Items]
    E --> F1[Bounded Worker 1]
    E --> F2[Bounded Worker 2]
    F1 --> S[Source Slices]
    F2 --> S
    S --> G[Evidence Store]
    G --> H[Synthesizer]
    H --> I[Verifier]
    I --> J[Revision (if needed)]
    J --> K[Verifier]
    K --> L[Deterministic Policy Gate]
    L --> M[Final Answer]
```

## Current Execution Behavior

- Recursive mode runs `planner -> bounded workers -> synthesizer -> verifier`.
- When verification returns `partial` or `fail`, the harness performs one
  revision pass and then re-verifies the revised answer.
- Policy is deterministic code over verifier output, not another LLM call.
- Worker findings are rejected when they cite unassigned document refs or quote
  excerpts that do not appear in the retrieved source slices.

## Quickstart

```bash
# Install
git clone https://github.com/rmax-ai/recursive-execution-harness-lab
cd recursive-execution-harness-lab
uv sync --extra dev

# If `uv` is unavailable on PATH after setup, use `.venv/bin/rxh` instead of `uv run rxh`.

# Run baseline (defaults to gpt-5.4-mini)
uv run rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode long-context --out runs/baseline

# Run recursive
uv run rxh run --task benchmarks/research_synthesis/tasks/recursive_execution.yaml \
  --corpus benchmarks/research_synthesis/corpora/sample \
  --mode recursive --out runs/recursive

# Compare
uv run rxh compare runs/baseline runs/recursive

# Run tests
uv run pytest tests/ -v
```

## Project Structure

```text
src/rxh/          — core package
benchmarks/       — task specs and sample corpora
tests/            — pytest tests (MockProvider only)
docs/             — architecture docs
```

## Limitations and Threats to Validity

1. The verifier is model-based and may share blind spots with the generator.
2. The corpus may favor one architecture over another.
3. Recursive execution uses more explicit scaffolding, which may improve prompt clarity independently of architecture.
4. The baseline may be disadvantaged if context limits force document truncation, even though both modes now use the same verifier step.
5. Results from research synthesis may not generalize to coding, customer support, or enterprise workflows.
6. The revision loop is currently capped at one pass, so some fixable answers
   may still end in `revise` or `deny`.
7. Token cost may vary by provider and caching strategy.
8. Better long-context models may reduce the observed gap.

## Research Contribution Statement

This project does not propose a new foundation model or a new agent framework.
It proposes a measurement harness for an architectural question:
When should long-running agents rely on larger context, and when should they
externalize state into recursive execution, bounded source slicing, evidence
stores, explicit verification, and runtime policy gates?

## Inspiration & References

This project is informed by the emerging consensus that long-running agents need
architectural patterns beyond raw context scaling. Key influences:

- **[Jackman Ong — Continual Learning for Long-Running Agents](https://youtu.be/SVWmuJx0hHM)** (NVIDIA GTC 2026, Prime Intellect). Lays out the case for **Recursive Language Models (RLMs)**: agents that pass *references* into context instead of raw text, write code to access/slice data programmatically, and delegate messy work to sub-agents via control flow rather than sequential tool calls. Documents the "context rot" phenomenon where 1M-token models lose ~50% of their reasoning capability. Introduces the **Mismanaged Genius Hypothesis**: LLMs are capable but poorly orchestrated — let them code their own harnesses. Frames RLMs as "the next thinking" — what chain-of-thought was to 2022, programmatic context manipulation will be to agent architectures.

Key concepts from the talk that directly inform this harness:

| Concept | Talk Insight | Manifestation in This Project |
|---|---|---|
| **Context Rot** | Models drop from ~80% → ~36% on information retrieval as context grows to 1M tokens (MRCR benchmark) | The `long-context` baseline mode measures a single-prompt workflow under a fixed budget; it does not prove degradation by itself |
| **Reference-Indexed Execution** | Pass document IDs through the workflow instead of assigning the whole corpus to every step | Planner-assigned refs drive bounded source-slice retrieval, and `EvidenceCard.source_ref` preserves provenance back to the original document |
| **Compaction Avoidance** | "Every time you end up with a compaction, the agent gets lost" | Recursive mode delegates to bounded workers; no compaction needed |
| **Programmatic Control Flow** | Use `for` loops for 10,000 docs instead of 10,000 sequential tool calls | Planner → sequential bounded workers → synthesizer → verifier → optional revision |
| **Verification Gates** | LLM-as-judge on trajectories; detect unsupported claims | Both baseline and recursive runs are verified against source snippets keyed by `source_ref`, and failing answers get one revision pass before final policy |
| **Runtime Policy Gates** | Evaluate whether a verified answer is safe to deliver | Both modes now write a post-verification `policy_decision.json` artifact, but the decision itself is deterministic code over verifier output |
| **Continual Learning** | Harvest traces, feedback, train on harness | JSONL trace output captures every LLM call for future training loops |

## License

MIT
