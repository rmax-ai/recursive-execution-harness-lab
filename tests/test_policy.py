from __future__ import annotations

import json
from pathlib import Path

from rxh.models import ClaimCheck, PolicyDecision, VerificationResult
from rxh.policy import apply_policy_gate, policy_prompt
from rxh.trace import TraceWriter


def test_policy_prompt_includes_verification_summary(sample_task) -> None:
    verification = VerificationResult(
        verdict="partial",
        checks=[
            ClaimCheck(
                claim="Claim A",
                supported=False,
                evidence_ids=[],
                issue="Unsupported.",
            )
        ],
        unsupported_claims=["Claim A"],
        source_attribution_errors=["Bad citation"],
    )

    prompt = policy_prompt(
        task=sample_task,
        final_answer="Claim A",
        verification=verification,
    )

    assert "Verification verdict:" in prompt
    assert "Unsupported claims:" in prompt
    assert "Source attribution errors:" in prompt
    assert "Claim A" in prompt


def test_apply_policy_gate_writes_artifact_and_trace(
    sample_task,
    tmp_path: Path,
) -> None:
    verification = VerificationResult(
        verdict="pass",
        checks=[ClaimCheck(claim="Claim A", supported=True, evidence_ids=["ev_1"])],
    )
    trace = TraceWriter(run_id="run_001", path=tmp_path / "trace.jsonl")

    decision = apply_policy_gate(
        task=sample_task,
        final_answer="Claim A [ev_1]",
        verification=verification,
        out_dir=tmp_path,
        trace=trace,
    )

    assert isinstance(decision, PolicyDecision)
    assert decision.decision == "allow"
    saved = json.loads((tmp_path / "policy_decision.json").read_text(encoding="utf-8"))
    assert saved["decision"] == "allow"
    lines = (tmp_path / "trace.jsonl").read_text(encoding="utf-8").splitlines()
    assert "policy_started" in lines[0]
    assert "policy_completed" in lines[1]


def test_apply_policy_gate_requires_revision_for_unsupported_claims(
    sample_task,
    tmp_path: Path,
) -> None:
    verification = VerificationResult(
        verdict="partial",
        checks=[],
        unsupported_claims=["Claim B"],
        source_attribution_errors=[],
    )
    trace = TraceWriter(run_id="run_001", path=tmp_path / "trace.jsonl")

    decision = apply_policy_gate(
        task=sample_task,
        final_answer="Claim B",
        verification=verification,
        out_dir=tmp_path,
        trace=trace,
    )

    assert decision.decision == "revise"
    assert "Claim B" in decision.blocked_claims
