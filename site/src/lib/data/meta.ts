export const PROJECT_VERSION = "v0.1.0";
export const TEST_COUNT = 38;
export const LICENSE = "MIT";
export const REPO_URL = "https://github.com/rmax-ai/recursive-execution-harness-lab";
export const DOCS_URL = "https://github.com/rmax-ai/recursive-execution-harness-lab/blob/main/docs/ARCHITECTURE.md";

export const STACK = [
  "Python 3.12+",
  "Typer CLI",
  "Pydantic v2",
  "httpx",
  "JSONL traces",
  "Local filesystem",
  "OpenAI-compatible providers",
];

export const METRICS = [
  { label: "Claim Support Rate", desc: "Fraction of major claims backed by evidence cards" },
  { label: "Unsupported Claims", desc: "Claims the verifier flags as lacking source evidence" },
  { label: "Source Attribution Errors", desc: "Citations that don't match actual documents" },
  { label: "Evidence Coverage", desc: "Cited sources / relevant sources in the corpus" },
  { label: "Token Usage", desc: "Total input + output across all LLM calls" },
  { label: "Trace Completeness", desc: "Required trace events present / total required" },
];

export const REFERENCE = {
  title: "Continual Learning for Long-Running Agents",
  speaker: "Jackman Ong",
  role: "Founding Research Engineer @ Prime Intellect",
  venue: "NVIDIA GTC 2026",
  url: "https://youtu.be/SVWmuJx0hHM",
  summary:
    "Makes the case for Recursive Language Models (RLMs): agents that pass references into context instead of raw text, write code to access data programmatically, and delegate to sub-agents via control flow. Documents 'context rot' — 1M-token models that lose ~50% reasoning capability. Frames RLMs as 'the next thinking': what chain-of-thought was to 2022, programmatic context manipulation will be to agent architectures.",
  concepts: [
    {
      concept: "Context Rot",
      insight:
        "Models drop from ~80% → ~36% on information retrieval as context grows to 1M tokens (MRCR benchmark)",
      manifestation:
        "The long-context baseline mode demonstrates this degradation",
    },
    {
      concept: "Reference-Based Execution",
      insight:
        "Pass variables/handles, not raw text — like Jupyter notebook exploratory data analysis",
      manifestation:
        "ReferenceStore + EvidenceCard.source_ref — workers fetch by reference",
    },
    {
      concept: "Compaction Avoidance",
      insight:
        '"Every time you end up with a compaction, the agent gets lost"',
      manifestation:
        "Recursive mode delegates to bounded sub-agents; no compaction needed",
    },
    {
      concept: "Programmatic Control Flow",
      insight:
        "Use for loops for 10,000 docs instead of 10,000 sequential tool calls",
      manifestation:
        "Planner → parallel workers → synthesizer pipeline",
    },
    {
      concept: "Verification Gates",
      insight:
        "LLM-as-judge on trajectories; detect unsupported claims",
      manifestation:
        "Separate verifier LLM call gates every answer",
    },
    {
      concept: "Continual Learning",
      insight:
        "Harvest traces + feedback → train models on their specific harness",
      manifestation:
        "JSONL trace output captures every LLM call for future training loops",
    },
  ],
};

export const THREATS = [
  "The verifier is model-based and may share blind spots with the generator.",
  "The corpus may favor one architecture over another.",
  "Recursive execution uses more explicit scaffolding — prompt clarity may improve independently of architecture.",
  "The baseline may be disadvantaged if context limits force document truncation.",
  "Results from research synthesis may not generalize to coding, customer support, or enterprise workflows.",
  "Token cost may vary by provider and caching strategy.",
  "Better long-context models may reduce the observed gap.",
];
