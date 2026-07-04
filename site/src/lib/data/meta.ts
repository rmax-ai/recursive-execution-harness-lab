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

export const THREATS = [
  "The verifier is model-based and may share blind spots with the generator.",
  "The corpus may favor one architecture over another.",
  "Recursive execution uses more explicit scaffolding — prompt clarity may improve independently of architecture.",
  "The baseline may be disadvantaged if context limits force document truncation.",
  "Results from research synthesis may not generalize to coding, customer support, or enterprise workflows.",
  "Token cost may vary by provider and caching strategy.",
  "Better long-context models may reduce the observed gap.",
];
