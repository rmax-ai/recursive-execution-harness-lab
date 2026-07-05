from __future__ import annotations

from pathlib import Path

from .models import PolicyDecision, TaskSpec, VerificationResult
from .trace import TraceWriter


def policy_prompt(
    *,
    task: TaskSpec,
    final_answer: str,
    verification: VerificationResult,
) -> str:
    checks_text = "\n".join(
        (
            f"- claim={check.claim} | supported={check.supported} "
            f"| evidence_ids={check.evidence_ids} | issue={check.issue}"
        )
        for check in verification.checks
    )

    return f"""
You are a strict post-verification policy gate.

Task:
{task.question}

Task constraints:
{chr(10).join("- " + constraint for constraint in task.constraints)}

Verification verdict:
{verification.verdict}

Unsupported claims:
{chr(10).join("- " + claim for claim in verification.unsupported_claims) or "none"}

Source attribution errors:
{chr(10).join("- " + issue for issue in verification.source_attribution_errors)
or "none"}

Verification checks:
{checks_text or "none"}

Final answer:
{final_answer}

Return JSON with this shape:
{{
  "decision": "allow|revise|deny",
  "rationale": "...",
  "required_changes": ["..."],
  "blocked_claims": ["..."]
}}

Rules:
- Use the verifier output as the primary safety signal.
- Choose "allow" only when the answer is safe to publish as-is.
- Choose "revise" when the answer could be repaired by removing or correcting
  specific claims.
- Choose "deny" when the answer should not be delivered without human review.
- When there are unsupported claims or source attribution errors, identify the
  affected claims in blocked_claims.
- Return valid JSON only.
""".strip()


def apply_policy_gate(
    *,
    task: TaskSpec,
    final_answer: str,
    verification: VerificationResult,
    out_dir: Path,
    trace: TraceWriter,
) -> PolicyDecision:
    trace.emit(
        stage="policy",
        event_type="policy_started",
        actor="policy_gate",
        input_refs=["final_answer.md", verification.id],
        metadata={"verification_verdict": verification.verdict},
    )

    blocked_claims = list(
        dict.fromkeys(
            [
                *verification.unsupported_claims,
                *verification.source_attribution_errors,
            ]
        )
    )
    required_changes: list[str] = []
    rationale_parts: list[str] = []

    if verification.verdict == "fail":
        decision_name = "deny"
        rationale_parts.append("Verifier returned fail.")
    elif verification.source_attribution_errors:
        decision_name = "revise"
        rationale_parts.append("Source attribution errors must be corrected.")
    elif verification.unsupported_claims:
        decision_name = "revise"
        rationale_parts.append("Unsupported claims must be removed or revised.")
    else:
        decision_name = "allow"
        rationale_parts.append("Verifier found no blocking issues.")

    if verification.unsupported_claims:
        required_changes.append("Remove or repair unsupported claims.")
    if verification.source_attribution_errors:
        required_changes.append("Correct source attribution errors.")

    if any(
        constraint.lower() in final_answer.lower()
        for constraint in task.constraints
    ):
        rationale_parts.append("Final answer repeats task constraints verbatim.")

    decision = PolicyDecision(
        decision=decision_name,
        rationale=" ".join(rationale_parts),
        required_changes=required_changes,
        blocked_claims=blocked_claims,
    )

    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / "policy_decision.json"
    path.write_text(decision.model_dump_json(indent=2), encoding="utf-8")

    trace.emit(
        stage="policy",
        event_type="policy_completed",
        actor="policy_gate",
        input_refs=["final_answer.md", verification.id],
        output_refs=["policy_decision.json"],
        metadata={
            "decision": decision.decision,
            "blocked_claims": len(decision.blocked_claims),
            "required_changes": len(decision.required_changes),
        },
    )

    return decision
