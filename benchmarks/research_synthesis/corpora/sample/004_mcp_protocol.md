# Model Context Protocol and Tool Governance

<!-- Source: https://www.anthropic.com/news/model-context-protocol -->

## Summary

The Model Context Protocol (MCP) is a proposed standard for how agents connect to tools, data sources, and other services. It addresses the problem of ad-hoc tool integrations by introducing scope, permissions, and policy enforcement. Governed tool access prevents runaway agent behavior by defining what an agent is allowed to do and how it may do it.

## Key Excerpts

> "MCP provides a standard interface so that an agent can discover tools and the policies that govern them."

> "Without governance, an agent can issue a tool call that is technically valid but semantically unsafe."

> "Policy enforcement belongs between the agent and the tool, not only in the prompt."

## Notes

Prompt-based safety is fragile. A model can misread, ignore, or be jailbroken out of a restriction. Runtime policy gates are harder to bypass because they execute outside the model and can deny a request before it reaches a tool. MCP's design emphasizes that tool access should be scoped, audited, and revocable.

Governance layers can reject actions that exceed a session's scope, require human approval for high-risk operations, and log every tool invocation for later review. This is a necessary complement to recursive execution, because recursion multiplies the number of tool calls and model decisions that must be supervised.
