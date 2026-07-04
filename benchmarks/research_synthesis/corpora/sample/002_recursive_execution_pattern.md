# Recursive Execution as an Alternative Architecture

<!-- Source: https://www.anthropic.com/research/computer-use -->

## Summary

Recursive execution is a pattern in which an agent decomposes a large task into smaller subproblems, dispatches bounded workers to investigate each subproblem, collects the results, synthesizes an answer, and verifies it before returning. This is the opposite of the single monolithic prompt, where the model is asked to do everything at once.

## Key Excerpts

> "Claude's computer-use experiments show that breaking a long task into discrete steps and letting the model inspect intermediate results improves reliability."

> "SWE-agent separates planning, execution, and observation into a loop, so that the model does not have to hold the entire codebase in working memory."

> "Externalizing state reduces the model's cognitive load because it can look things up instead of remembering them."

## Notes

Recursive execution mirrors how human teams operate: a lead splits the work, specialists dig into the details, and a coordinator assembles the final artifact. The architecture places limits on each step. A worker is given a narrow subquestion, a bounded set of documents, and a clear output format. The synthesizer is not allowed to hallucinate unsupported facts because the verification stage will check claims against the evidence store.

The pattern is especially useful when the task is too large for a single context window, when the answer must be traceable to source material, and when the cost of a mistake is high enough to justify a verification step.
