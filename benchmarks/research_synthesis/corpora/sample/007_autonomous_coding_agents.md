# Autonomous Coding Agents and Their Failure Modes

<!-- Source: https://www.swebench.com/ -->

## Summary

Autonomous coding agents have made progress on benchmarks such as SWE-bench, but they also exhibit recurring failure modes. Some tasks are solved quickly, while others fail because the agent loses track of the original objective, changes code that is unrelated to the bug, or fails to verify that the fix works.

## Key Excerpts

> "SWE-bench results show that coding agents can succeed on isolated issues but struggle on tasks that require reasoning across many files and long sessions."

> "The biggest failure mode is context drift over long sessions: the agent forgets the original goal and starts optimizing for a proxy objective."

> "Agents that do not test their changes often produce plausible-looking but incorrect patches."

## Notes

Coding agents are a useful microcosm of long-running agents generally. They interact with a large environment, a long history of actions, and a subtle specification. The longer the session, the more the original context is diluted by new observations. This is exactly the context-window problem described in earlier documents, but it is compounded by the fact that every action changes the environment.

To remain effective, coding agents need externalized plans, durable checkpoints, and verification gates that confirm whether a proposed change actually satisfies the original issue. Without these controls, they wander.
