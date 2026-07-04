from __future__ import annotations

from rxh.models import (
    ClaimCheck,
    DocumentRef,
    EvidenceCard,
    Plan,
    PlanItem,
    RunMetrics,
    TaskSpec,
    TraceEvent,
    VerificationResult,
    WorkerResult,
)


def test_task_spec_round_trip_with_all_fields() -> None:
    task = TaskSpec(
        id="task_001",
        title="Test task",
        question="What happened?",
        expected_output_type="answer",
        success_criteria=["Use sources"],
        constraints=["No speculation"],
        evaluation_questions=["Is it supported?"],
    )

    restored = TaskSpec.model_validate_json(task.model_dump_json())

    assert restored == task


def test_document_ref_round_trip_json() -> None:
    doc = DocumentRef(
        id="doc_0001",
        source_path="/tmp/doc.md",
        title="Doc",
        content_hash="abc123",
        char_count=42,
        metadata={"kind": "note"},
    )

    restored = DocumentRef.model_validate_json(doc.model_dump_json())

    assert restored == doc


def test_evidence_card_created_at_auto_populated() -> None:
    evidence = EvidenceCard(
        id="ev_item_001_000",
        source_ref="doc_0001",
        quote_or_excerpt="quoted text",
        summary="summary",
        claim_supported="claim",
        worker_id="worker_item_001",
    )

    assert evidence.created_at is not None


def test_plan_with_nested_items_serializes() -> None:
    plan = Plan(
        strategy="Split the question by theme",
        items=[
            PlanItem(
                id="item_001",
                subquestion="What does doc one say?",
                assigned_refs=["doc_0001"],
                expected_evidence=["A key excerpt"],
            )
        ],
        verification_strategy="Cross-check citations",
    )

    restored = Plan.model_validate_json(plan.model_dump_json())

    assert restored == plan


def test_worker_result_with_nested_evidence_cards() -> None:
    result = WorkerResult(
        worker_id="worker_item_001",
        plan_item_id="item_001",
        subquestion="What does doc one say?",
        assigned_refs=["doc_0001"],
        findings=[
            EvidenceCard(
                id="ev_item_001_000",
                source_ref="doc_0001",
                quote_or_excerpt="excerpt",
                summary="summary",
                claim_supported="claim",
                worker_id="worker_item_001",
            )
        ],
        open_questions=["What is missing?"],
        failures=[],
    )

    restored = WorkerResult.model_validate_json(result.model_dump_json())

    assert restored == result


def test_claim_check_with_issue_none() -> None:
    check = ClaimCheck(claim="Supported claim", supported=True, issue=None)

    assert check.issue is None


def test_verification_result_supports_pass_and_fail_verdicts() -> None:
    passing = VerificationResult(
        verdict="pass",
        checks=[ClaimCheck(claim="A", supported=True)],
    )
    failing = VerificationResult(
        verdict="fail",
        checks=[ClaimCheck(claim="B", supported=False, issue="Missing evidence")],
        unsupported_claims=["B"],
    )

    assert passing.verdict == "pass"
    assert failing.verdict == "fail"


def test_trace_event_default_factory_fields_populated() -> None:
    event = TraceEvent(
        run_id="run_001",
        stage="planning",
        event_type="planning_started",
        actor="planner",
    )

    assert event.event_id.startswith("evt_")
    assert event.timestamp is not None
    assert event.input_refs == []
    assert event.output_refs == []
    assert event.token_usage == {}
    assert event.metadata == {}


def test_run_metrics_defaults_all_zero() -> None:
    metrics = RunMetrics(run_id="run_001", mode="recursive")

    assert metrics.token_input_estimate == 0
    assert metrics.token_output_estimate == 0
    assert metrics.wall_clock_seconds == 0
    assert metrics.document_count == 0
    assert metrics.evidence_card_count == 0
    assert metrics.unsupported_claim_count == 0
    assert metrics.source_attribution_error_count == 0
