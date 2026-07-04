# Policy-as-Code for Agent Governance

<!-- Source: https://www.openpolicyagent.org/docs/latest/philosophy/ -->

## Summary

Policy-as-Code frameworks such as Open Policy Agent (OPA) and Rego allow an organization to express rules in a declarative language that can be evaluated at runtime. For agents, this means that permission models, audit requirements, and safety constraints can be enforced outside the model rather than embedded in a prompt.

## Key Excerpts

> "Agents need runtime policy gates, not just prompt instructions."

> "Policy-as-Code separates the definition of what is allowed from the enforcement of those rules."

> "Audit trails make it possible to explain why a request was allowed or denied."

## Notes

Prompt instructions are opaque to the rest of the system. A policy engine, by contrast, can be versioned, tested, and reviewed by security teams. It can evaluate a proposed action against a set of rules that include identity, resource ownership, data classification, and business constraints. The engine returns a clear allow or deny decision that can be logged.

In a recursive agent, policy gates are useful at every boundary: when a worker is assigned a subquestion, when a worker wants to use a tool, when the synthesizer wants to include a claim, and when the verifier wants to change a verdict. The gates do not replace reasoning; they provide a safety net around it.
