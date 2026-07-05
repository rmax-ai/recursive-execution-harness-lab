export const PROJECT_VERSION = "v0.1.0";
export const TEST_COUNT = 50;
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
  { label: "Policy Decision", desc: "Post-verification allow, revise, or deny decision" },
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
        "The long-context baseline mode measures a single-prompt workflow under a fixed budget; it does not prove degradation by itself",
    },
    {
      concept: "Reference-Indexed Execution",
      insight:
        "Pass document identifiers through the workflow instead of assigning the whole corpus to every step",
      manifestation:
        "Planner-assigned refs drive bounded source-slice retrieval, and EvidenceCard.source_ref preserves provenance back to the original document",
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
        "Planner → sequential bounded workers → synthesizer → verifier → optional revision",
    },
    {
      concept: "Verification Gates",
      insight:
        "LLM-as-judge on trajectories; detect unsupported claims",
      manifestation:
        "Both baseline and recursive runs are verified against source snippets keyed by source_ref, and failing answers get one revision pass before final policy",
    },
    {
      concept: "Runtime Policy Gates",
      insight:
        "Evaluate whether a verified answer is still safe to deliver",
      manifestation:
        "Both modes write a post-verification policy_decision.json artifact, but the decision itself is deterministic code over verifier output",
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
  "The baseline may be disadvantaged if context limits force document truncation, even though both modes now use the same verifier step.",
  "The revision loop is currently capped at one pass, so some fixable answers may still end in revise or deny.",
  "Results from research synthesis may not generalize to coding, customer support, or enterprise workflows.",
  "Token cost may vary by provider and caching strategy.",
  "Better long-context models may reduce the observed gap.",
];
