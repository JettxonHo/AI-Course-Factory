"""Public behavior tests for the claim-gated Production Orchestrator."""

import unittest
from dataclasses import fields, replace
from datetime import datetime, timezone

from ai_course_factory.artifacts import ArtifactCommitBoundary, ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetDecisionOutcome,
    BudgetModule,
    MediaGenerationResult,
    PriceSnapshot,
    ProductionExecutionResult,
    ProductionMediaFailure,
    ProviderAttemptClaim,
    ProviderAttemptFailure,
    ProviderAttemptLedger,
    ProviderAttemptOutcome,
    ProviderAttemptRecord,
    ProviderAttemptReservation,
    RetryPolicy,
    VisualGenerationTask,
    VoiceSynthesisTask,
    ProductionOrchestrator,
)

from tests.production.test_budget import fixture_snapshot, production_request_parts


def _authorization_and_request(*, task_id="task:orchestrator"):
    request_reference, request = production_request_parts()
    artifacts = ArtifactCommitBoundary()
    candidate = BudgetModule().estimate(
        request_reference,
        request,
        price_snapshot=fixture_snapshot(request_reference),
        retry_policy=RetryPolicy(2),
        budget_identity="budget:orchestrator",
        budget_commit_id="budget-commit:orchestrator",
    )
    budget_reference = artifacts.commit(candidate)
    budget = artifacts.get(budget_reference)
    decision = BudgetAuthorizationBoundary().decide(
        request_reference,
        request,
        budget_reference,
        budget,
        decision_id="decision:orchestrator",
        authorization_id="authorization:orchestrator",
        task_id=task_id,
        thread_id="thread:orchestrator",
        creator_id="creator:orchestrator",
        decided_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        action="approve",
        maximum_approved_amount_micros=6_000,
        maximum_attempts=2,
    )
    assert isinstance(decision, BudgetDecisionOutcome)
    assert decision.authorization is not None
    return request_reference, request, decision.authorization


def _reservation(authorization, *, attempt_id="attempt:visual", operation="visual", provider="fake-visual-v1", scene_id="scene-1"):
    return ProviderAttemptReservation(
        attempt_id,
        authorization.task_id,
        authorization.authorization_id,
        scene_id,
        operation,
        provider,
        f"key:{attempt_id}",
        WorkspaceFileReference(authorization.task_id, "provider-records", f"{attempt_id.replace(':', '-')}.json"),
        datetime(2026, 8, 12, tzinfo=timezone.utc),
    )


def _visual_task(reference, reservation, *, output_name="scene-1.visual.json", **changes):
    task = VisualGenerationTask(
        reservation.task_id,
        reservation.attempt_id,
        reference,
        reservation.scene_id,
        "9:16",
        30.0,
        "展示小土豆。",
        "挥手。",
        WorkspaceFileReference(reservation.task_id, "media", output_name),
    )
    return replace(task, **changes)


def _voice_task(reference, reservation, *, output_name="scene-1.voice.json", **changes):
    task = VoiceSynthesisTask(
        reservation.task_id,
        reservation.attempt_id,
        reference,
        reservation.scene_id,
        "zh-CN",
        30.0,
        "你好。",
        WorkspaceFileReference(reservation.task_id, "media", output_name),
    )
    return replace(task, **changes)


def _record(reference, reservation, *, status="started", output_references=(), result_code=None, completed_at=None, charged=None):
    return ProviderAttemptRecord(
        reservation.attempt_id,
        reservation.task_id,
        reservation.authorization_id,
        reference,
        ArtifactReference("production_budget", "budget:orchestrator", 1),
        reservation.scene_id,
        reservation.operation,
        reservation.provider,
        1,
        reservation.idempotency_key,
        reservation.request_record_reference,
        "USD",
        1_000 if reservation.operation == "visual" else 500,
        status,
        reservation.reserved_at,
        completed_at,
        charged,
        result_code,
        None,
        tuple(output_references),
    )


class _SpyLedger:
    def __init__(self, claim):
        self.claim_result = claim
        self.claim_calls = 0
        self.complete_calls = []

    def claim(self, reservation):
        self.claim_calls += 1
        return self.claim_result

    def complete(self, outcome):
        self.complete_calls.append(outcome)
        record = self.claim_result.record
        return replace(
            record,
            status=outcome.status,
            completed_at=outcome.completed_at,
            charged_amount_micros=outcome.charged_amount_micros,
            result_code=outcome.result_code,
            response_record_reference=outcome.response_record_reference,
            output_references=outcome.output_references,
        )


class _CountingVisual:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def generate(self, task):
        self.calls.append(task)
        return self.result(task) if callable(self.result) else self.result


class _CountingVoice:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def synthesize(self, task):
        self.calls.append(task)
        return self.result(task) if callable(self.result) else self.result


class _AlwaysEqual:
    """Mutation sentinel that must never satisfy an exact value check."""

    def __eq__(self, _other):
        return True

    def __ne__(self, _other):
        return False


class ProductionOrchestratorTests(unittest.TestCase):
    def test_execution_result_is_frozen_slotted_and_has_exact_public_shape(self):
        self.assertTrue(ProductionExecutionResult.__dataclass_params__.frozen)
        self.assertTrue(hasattr(ProductionExecutionResult, "__slots__"))
        self.assertEqual(
            tuple(field.name for field in fields(ProductionExecutionResult)),
            (
                "task_id",
                "attempt_id",
                "production_request_reference",
                "scene_id",
                "operation",
                "provider",
                "output_reference",
                "result_code",
            ),
        )

    def test_execute_claims_once_invokes_only_matching_visual_generator_and_completes_zero_charge(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        started = _record(reference, reservation)
        visual = _CountingVisual(
            lambda value: MediaGenerationResult(
                value.attempt_id,
                value.scene_id,
                "visual",
                reservation.provider,
                value.output_reference,
                "application/x-fixture",
                value.duration_seconds,
                "SUCCESS",
            )
        )
        voice = _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run"))
        ledger = _SpyLedger(ProviderAttemptClaim(started, True))
        result = ProductionOrchestrator(
            ledger,
            visual,
            voice,
            clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, task)

        self.assertEqual(
            result,
            ProductionExecutionResult(
                reservation.task_id,
                reservation.attempt_id,
                reference,
                reservation.scene_id,
                "visual",
                reservation.provider,
                task.output_reference,
                "SUCCESS",
            ),
        )
        self.assertEqual(ledger.claim_calls, 1)
        self.assertEqual(len(ledger.complete_calls), 1)
        self.assertEqual(ledger.complete_calls[0].charged_amount_micros, 0)
        self.assertEqual(ledger.complete_calls[0].status, "succeeded")
        self.assertEqual(visual.calls, [task])
        self.assertEqual(voice.calls, [])

    def test_validation_happens_before_claim_for_mismatched_visual_scene(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        ledger = _SpyLedger(ProviderAttemptClaim(_record(reference, reservation), True))
        visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "should not run"))
        result = ProductionOrchestrator(
            ledger,
            visual,
            _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run")),
            clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, _visual_task(reference, reservation, visual_intent="changed"))

        self.assertEqual(result.code, "MEDIA_TASK_MISMATCH")
        self.assertEqual(ledger.claim_calls, 0)
        self.assertEqual(visual.calls, [])

    def test_voice_operation_selects_voice_generator_and_never_visual(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(
            authorization,
            attempt_id="attempt:voice",
            operation="voice",
            provider="fake-voice-v1",
        )
        task = _voice_task(reference, reservation)
        started = _record(reference, reservation)
        visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "should not run"))
        voice = _CountingVoice(
            lambda value: MediaGenerationResult(
                value.attempt_id,
                value.scene_id,
                "voice",
                reservation.provider,
                value.output_reference,
                "application/x-fixture",
                value.duration_seconds,
                "SUCCESS",
            )
        )
        ledger = _SpyLedger(ProviderAttemptClaim(started, True))
        result = ProductionOrchestrator(
            ledger,
            visual,
            voice,
            clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, task)

        self.assertIsInstance(result, ProductionExecutionResult)
        self.assertEqual(result.operation, "voice")
        self.assertEqual(visual.calls, [])
        self.assertEqual(voice.calls, [task])

    def test_started_terminal_replays_never_invoke_an_adapter(self):
        reference, request, authorization = _authorization_and_request()
        for status, expected_code, output in (
            ("started", "ATTEMPT_IN_PROGRESS", ()),
            ("failed", "GENERATION_FAILED", ()),
        ):
            with self.subTest(status=status):
                reservation = _reservation(authorization, attempt_id=f"attempt:{status}")
                task = _visual_task(reference, reservation, output_name=f"{status}.json")
                if status == "failed":
                    record = _record(
                        reference,
                        reservation,
                        status="failed",
                        result_code="TIMEOUT",
                        charged=0,
                        completed_at=datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                    )
                else:
                    record = _record(reference, reservation)
                visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "should not run"))
                ledger = _SpyLedger(ProviderAttemptClaim(record, False))
                result = ProductionOrchestrator(
                    ledger,
                    visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                ).execute(reference, request, reservation, task)
                self.assertEqual(result.code, expected_code)
                self.assertEqual(visual.calls, [])
                self.assertEqual(ledger.complete_calls, [])

    def test_succeeded_terminal_replays_exact_result_without_adapter(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        record = _record(
            reference,
            reservation,
            status="succeeded",
            result_code="SUCCESS",
            charged=0,
            completed_at=datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
            output_references=(task.output_reference,),
        )
        visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "should not run"))
        result = ProductionOrchestrator(
            _SpyLedger(ProviderAttemptClaim(record, False)),
            visual,
            _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run")),
            clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, task)

        self.assertEqual(result, ProductionExecutionResult(
            reservation.task_id,
            reservation.attempt_id,
            reference,
            reservation.scene_id,
            "visual",
            reservation.provider,
            task.output_reference,
            "SUCCESS",
        ))
        self.assertEqual(visual.calls, [])

    def test_adapter_failure_is_terminal_zero_charge_and_replay_is_generic_safe(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        ledger = _SpyLedger(ProviderAttemptClaim(_record(reference, reservation), True))
        visual = _CountingVisual(ProductionMediaFailure("execution", "MEDIA_STORAGE_FAILED", "raw path must not escape"))
        result = ProductionOrchestrator(
            ledger,
            visual,
            _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run")),
            clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, task)

        self.assertEqual(result, ProductionMediaFailure("execution", "GENERATION_FAILED", "media generation failed"))
        self.assertEqual(ledger.complete_calls[0].status, "failed")
        self.assertEqual(ledger.complete_calls[0].charged_amount_micros, 0)
        self.assertEqual(ledger.complete_calls[0].result_code, "MEDIA_STORAGE_FAILED")
        self.assertEqual(ledger.complete_calls[0].output_references, ())
        self.assertNotIn("raw path", result.message)

    def test_malformed_claim_and_adapter_result_fail_without_adapter_or_false_success(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        for claim in (
            ProviderAttemptFailure("execution", "ATTEMPT_STORAGE_FAILED", "raw storage"),
            object(),
            ProviderAttemptClaim(_record(reference, reservation, status="succeeded", result_code="SUCCESS", charged=1), True),
        ):
            with self.subTest(claim=claim):
                visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "should not run"))
                ledger = _SpyLedger(claim)
                result = ProductionOrchestrator(
                    ledger,
                    visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                ).execute(reference, request, reservation, task)
                self.assertIn(result.code, {"ATTEMPT_STORAGE_FAILED", "GENERATION_FAILED"})
                self.assertEqual(visual.calls, [])
                self.assertEqual(ledger.complete_calls, [])

    def test_always_equal_media_task_values_fail_before_claim_or_adapter(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        for field in (
            "task_id",
            "attempt_id",
            "production_request_reference",
            "scene_id",
            "aspect_ratio",
            "duration_seconds",
            "visual_intent",
            "character_action",
            "output_reference",
        ):
            with self.subTest(field=field):
                visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "must not run"))
                ledger = _SpyLedger(ProviderAttemptClaim(_record(reference, reservation), True))
                forged = replace(task, **{field: _AlwaysEqual()})
                result = ProductionOrchestrator(
                    ledger,
                    visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "must not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                ).execute(reference, request, reservation, forged)
                self.assertEqual(result.kind, "validation")
                self.assertEqual(ledger.claim_calls, 0)
                self.assertEqual(visual.calls, [])

    def test_always_equal_claim_record_values_fail_before_adapter(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        started = _record(reference, reservation)
        for field in (
            "attempt_id",
            "production_request_reference",
            "status",
            "operation",
            "attempt_number",
            "currency",
            "reserved_amount_micros",
            "output_references",
        ):
            with self.subTest(field=field):
                forged = replace(started, **{field: _AlwaysEqual()})
                visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "must not run"))
                ledger = _SpyLedger(ProviderAttemptClaim(forged, True))
                result = ProductionOrchestrator(
                    ledger,
                    visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "must not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                ).execute(reference, request, reservation, task)
                self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(ledger.claim_calls, 1)
                self.assertEqual(ledger.complete_calls, [])
                self.assertEqual(visual.calls, [])

    def test_noncanonical_claim_reference_fails_before_adapter(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        for identity in ("bad\nidentity", "x" * 257, " latest "):
            with self.subTest(identity=identity):
                forged = replace(
                    _record(reference, reservation),
                    budget_reference=ArtifactReference("production_budget", identity, 1),
                )
                visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "must not run"))
                ledger = _SpyLedger(ProviderAttemptClaim(forged, True))
                result = ProductionOrchestrator(
                    ledger,
                    visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "must not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                ).execute(reference, request, reservation, task)
                self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(visual.calls, [])
                self.assertEqual(ledger.complete_calls, [])

    def test_forged_media_result_is_failed_without_output_and_replays_generically(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        started = _record(reference, reservation)
        valid_result = MediaGenerationResult(
            reservation.attempt_id,
            reservation.scene_id,
            "visual",
            reservation.provider,
            task.output_reference,
            "application/x-fixture",
            task.duration_seconds,
            "SUCCESS",
        )
        for field in (
            "attempt_id",
            "scene_id",
            "operation",
            "provider",
            "output_reference",
            "media_type",
            "duration_seconds",
            "result_code",
        ):
            with self.subTest(field=field):
                forged = replace(valid_result, **{field: _AlwaysEqual()})
                visual = _CountingVisual(forged)
                ledger = _SpyLedger(ProviderAttemptClaim(started, True))
                orchestrator = ProductionOrchestrator(
                    ledger,
                    visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "must not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                )
                result = orchestrator.execute(reference, request, reservation, task)
                self.assertEqual(result, ProductionMediaFailure("execution", "GENERATION_FAILED", "media generation failed"))
                self.assertEqual(visual.calls, [task])
                self.assertEqual(ledger.complete_calls[0].status, "failed")
                self.assertEqual(ledger.complete_calls[0].charged_amount_micros, 0)
                self.assertEqual(ledger.complete_calls[0].output_references, ())

                failed = replace(
                    started,
                    status="failed",
                    completed_at=ledger.complete_calls[0].completed_at,
                    charged_amount_micros=0,
                    result_code="GENERATION_FAILED",
                )
                replay_visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "must not run"))
                replay = ProductionOrchestrator(
                    _SpyLedger(ProviderAttemptClaim(failed, False)),
                    replay_visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "must not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 2, tzinfo=timezone.utc),
                ).execute(reference, request, reservation, task)
                self.assertEqual(replay, result)
                self.assertEqual(replay_visual.calls, [])

    def test_nonzero_terminal_charge_replay_is_storage_failure_without_adapter(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        for status, result_code, outputs in (
            ("failed", "FAIL", ()),
            ("succeeded", "SUCCESS", (task.output_reference,)),
        ):
            with self.subTest(status=status):
                record = _record(
                    reference,
                    reservation,
                    status=status,
                    result_code=result_code,
                    charged=999,
                    completed_at=datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
                    output_references=outputs,
                )
                visual = _CountingVisual(ProductionMediaFailure("execution", "UNEXPECTED", "must not run"))
                ledger = _SpyLedger(ProviderAttemptClaim(record, False))
                result = ProductionOrchestrator(
                    ledger,
                    visual,
                    _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "must not run")),
                    clock=lambda: datetime(2026, 8, 12, 0, 0, 2, tzinfo=timezone.utc),
                ).execute(reference, request, reservation, task)
                self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(visual.calls, [])
                self.assertEqual(ledger.complete_calls, [])

    def test_forged_completed_record_is_storage_failure_without_false_success(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        visual = _CountingVisual(
            MediaGenerationResult(
                reservation.attempt_id,
                reservation.scene_id,
                "visual",
                reservation.provider,
                task.output_reference,
                "application/x-fixture",
                task.duration_seconds,
                "SUCCESS",
            )
        )

        class ForgedCompletedLedger(_SpyLedger):
            def complete(self, outcome):
                completed = super().complete(outcome)
                return replace(completed, result_code=_AlwaysEqual())

        ledger = ForgedCompletedLedger(ProviderAttemptClaim(_record(reference, reservation), True))
        result = ProductionOrchestrator(
            ledger,
            visual,
            _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "must not run")),
            clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, task)
        self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
        self.assertEqual(visual.calls, [task])
        self.assertEqual(len(ledger.complete_calls), 1)

    def test_clock_or_terminal_persistence_failure_returns_safe_failure(self):
        reference, request, authorization = _authorization_and_request()
        reservation = _reservation(authorization)
        task = _visual_task(reference, reservation)
        visual = _CountingVisual(
            MediaGenerationResult(
                reservation.attempt_id,
                reservation.scene_id,
                "visual",
                reservation.provider,
                task.output_reference,
                "application/x-fixture",
                task.duration_seconds,
                "SUCCESS",
            )
        )
        ledger = _SpyLedger(ProviderAttemptClaim(_record(reference, reservation), True))
        result = ProductionOrchestrator(
            ledger,
            visual,
            _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run")),
            clock=lambda: datetime(2026, 8, 11, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, task)
        self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
        self.assertEqual(ledger.complete_calls, [])

        class MismatchedLedger(_SpyLedger):
            def complete(self, outcome):
                self.complete_calls.append(outcome)
                return replace(super().complete(outcome), result_code="FORGED")

        mismatched = MismatchedLedger(ProviderAttemptClaim(_record(reference, reservation), True))
        result = ProductionOrchestrator(
            mismatched,
            visual,
            _CountingVoice(ProductionMediaFailure("execution", "UNEXPECTED", "should not run")),
            clock=lambda: datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc),
        ).execute(reference, request, reservation, task)
        self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")


if __name__ == "__main__":
    unittest.main()
