# Durable Workflows and State Externalization

<!-- Source: https://docs.temporal.io/concepts/what-is-a-durable-workflow -->

## Summary

Long-running agents need durable state outside the model context. Workflow engines such as Temporal, Prefect, and similar systems have demonstrated that durable execution is possible when state is persisted, checkpoints are taken, and operations are retried idempotently. These lessons can be applied to agentic systems.

## Key Excerpts

> "A durable workflow records every step so that it can survive process crashes and resume exactly where it left off."

> "Idempotency means that executing the same operation twice produces the same observable result, which is essential for retries."

> "Checkpointing converts volatile model state into durable, queryable state."

## Notes

If an agent session is interrupted, the model's context is lost. The only way to resume is to reconstruct that context from external storage. Workflow engines solve this by treating the context as a log of events rather than a transient memory buffer. The agent can then rehydrate from the log, and a new model instance can continue where the previous one stopped.

For agents, durable state means evidence cards, plan items, verification results, and trace events. These artifacts live on disk or in an event store, not in the model's context window. They are the agent's memory.
