# Evidence Tracing and Provenance in Agent Workflows

<!-- Source: https://www.nature.com/articles/s41586-024-07443-6 -->

## Summary

Evidence provenance matters for trust in any system that produces claims from source material. In a recursive agent, every worker can produce evidence cards that link a specific claim to a specific document. This creates a chain of provenance from the source document to the final answer.

## Key Excerpts

> "Every agent claim should link to source evidence so that a human or another model can verify it."

> "Trace-based verification records not only what the agent concluded, but also which sources were used at each step."

> "Provenance is the antidote to plausible-sounding but unsupported outputs."

## Notes

A synthesizer that writes a final answer without citations is asking the user to trust an opaque process. Evidence cards change that dynamic. Each card contains a quote or excerpt, the source document reference, and a confidence judgment. A separate verifier can then check whether the final answer overstates the evidence, introduces unsupported claims, or misattributes a quote.

Tracing also supports debugging. When a final answer is wrong, the trace points to the worker or the document that introduced the error. Without provenance, the only remedy is to rerun the entire pipeline and hope for a different result.
