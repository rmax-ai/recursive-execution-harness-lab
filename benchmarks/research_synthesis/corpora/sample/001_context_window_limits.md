# Context Window Limits in Long-Running Agents

<!-- Source: https://www.anthropic.com/research/long-context-attention -->

## Summary

Large language models advertise ever-larger context windows, but empirical research shows that simply stuffing more tokens into a single prompt does not scale linearly with comprehension. Performance degrades once contexts exceed roughly 128,000 tokens, and the degradation is not uniform: it is hardest for fine-grained retrieval and for reasoning over distant dependencies.

## Key Excerpts

> "Long-context retrieval accuracy falls as the distance between a target fact and the end of the prompt grows."

> "Needle-in-a-haystack tests demonstrate that retrieval accuracy drops sharply after the 100,000-token mark, even for models that nominally support 200,000 tokens or more."

## Notes

Anthropic and Google have both published studies showing that attention becomes diluted across very long contexts. Models may "see" every token, but they are less likely to use the middle and early portions of the prompt when forming an answer. This limits the practical depth of long-context agent sessions and suggests that a naive "put everything in the prompt" strategy will fail for long-running workflows.

For agents that must operate across thousands of documents, hours of work, or weeks of asynchronous activity, context windows become a scarce resource rather than an unlimited canvas. The result is context drift, repeated computation, and missed constraints that were stated early in the session.
