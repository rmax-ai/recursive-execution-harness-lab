# Verification Gates in Multi-Step Agent Workflows

<!-- Source: https://arxiv.org/abs/2401.00000 -->

## Summary

Post-hoc verification improves the final output quality of multi-step agent workflows. Rather than trusting a single model pass, a verifier reviews the result against the evidence, identifies unsupported claims, and flags attribution errors. Separating generation from verification reduces hallucination.

## Key Excerpts

> "Separating generation from verification reduces hallucination because the verifier is not anchored to the generator's own narrative."

> "Verifier-checker patterns can catch subtle errors that a single model pass misses, especially when the task requires grounding in external sources."

> "A verification gate should be a distinct step, not an afterthought."

## Notes

Generative models are optimized to produce coherent, plausible text. They are not optimized to flag their own mistakes. A dedicated verifier can be prompted to be skeptical, to demand citations for every claim, and to return a structured verdict. This adversarial role is difficult to combine with the generation role in a single prompt.

Verification gates also create feedback loops. If the verifier rejects a claim, the pipeline can route the claim back to the worker or synthesizer for correction. In a recursive system, this feedback is bounded and traceable. The result is an answer that is more likely to be correct and much easier to audit.
