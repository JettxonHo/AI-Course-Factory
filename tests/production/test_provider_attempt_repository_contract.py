"""Public repository contract tests for Provider-attempt persistence."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, fields, replace
from datetime import datetime, timezone
import unittest

from ai_course_factory.artifacts import ArtifactCommitBoundary, ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetDecisionOutcome,
    BudgetFailure,
    BudgetModule,
    ProviderAttemptClaim,
    ProviderAttemptFailure,
    ProviderAttemptLedger,
    ProviderAttemptOutcome,
    ProviderAttemptRecord,
    ProviderAttemptRepository,
    ProviderAttemptReservation,
    PriceLineItem,
    RetryPolicy,
)

from tests.production.test_budget import fixture_snapshot, production_request_parts


def approved_authorization(*, authorization_id="authorization:contract", task_id="task:contract", maximum=6_000, attempts=2):
    request_reference, request = production_request_parts()
    artifacts = ArtifactCommitBoundary()
    candidate = BudgetModule.estimate(
        request_reference,
        request,
        price_snapshot=fixture_snapshot(request_reference),
        retry_policy=RetryPolicy(attempts),
        budget_identity="budget:contract",
        budget_commit_id="budget-commit:contract",
    )
    budget_reference = artifacts.commit(candidate)
    budget = artifacts.get(budget_reference)
    result = BudgetAuthorizationBoundary().decide(
        request_reference,
        request,
        budget_reference,
        budget,
        decision_id=f"decision:{authorization_id}",
        authorization_id=authorization_id,
        task_id=task_id,
        thread_id="thread:contract",
        creator_id="creator:contract",
        decided_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        action="approve",
        maximum_approved_amount_micros=maximum,
        maximum_attempts=attempts,
    )
    assert isinstance(result, BudgetDecisionOutcome)
    return result.authorization


def reservation(attempt_id="attempt:contract", *, authorization_id="authorization:contract", task_id="task:contract", scene_id="scene-1", operation="visual", provider="fake", key=None, when=None):
    return ProviderAttemptReservation(
        attempt_id,
        task_id,
        authorization_id,
        scene_id,
        operation,
        provider,
        key or f"key:{attempt_id}",
        WorkspaceFileReference(task_id, "provider-records", f"{attempt_id.replace(':', '-')}.json"),
        when or datetime(2026, 8, 12, tzinfo=timezone.utc),
    )


class ProviderAttemptRepositoryContractTests(unittest.TestCase):
    def test_protocol_is_runtime_checkable_for_attempt_ledger_storage(self):
        class InMemoryRepository:
            def claim(self, reservation, authorization):
                return reservation

            def reserve(self, reservation, authorization):
                return reservation

            def complete(self, outcome):
                return outcome

            def get(self, attempt_id):
                return attempt_id

            def list_for_authorization(self, authorization_id):
                return (authorization_id,)

        self.assertIsInstance(InMemoryRepository(), ProviderAttemptRepository)

    def test_default_ledger_derives_exact_authorization_fields_and_reserves(self):
        authorization = approved_authorization()
        result = ProviderAttemptLedger(lambda _id: authorization).reserve(reservation())
        self.assertIsInstance(result, ProviderAttemptRecord)
        self.assertEqual(result.production_request_reference, authorization.production_request_reference)
        self.assertEqual(result.budget_reference, authorization.budget_reference)
        self.assertEqual(result.currency, "USD")
        self.assertEqual(result.reserved_amount_micros, 1_000)
        self.assertEqual(result.status, "started")
        self.assertIsNone(result.completed_at)

    def test_claim_returns_created_signal_and_replays_exact_record(self):
        authorization = approved_authorization()
        ledger = ProviderAttemptLedger(lambda _id: authorization)
        first = ledger.claim(reservation())
        self.assertIsInstance(first, ProviderAttemptClaim)
        self.assertIs(first.created, True)
        self.assertEqual(first.record.status, "started")
        replay = ledger.claim(reservation())
        self.assertIsInstance(replay, ProviderAttemptClaim)
        self.assertIs(replay.created, False)
        self.assertEqual(replay.record, first.record)

    def test_claim_replays_terminal_record_with_created_false(self):
        authorization = approved_authorization()
        ledger = ProviderAttemptLedger(lambda _id: authorization)
        first = ledger.claim(reservation())
        self.assertIsInstance(first, ProviderAttemptClaim)
        completed = ledger.complete(ProviderAttemptOutcome("attempt:contract", "failed", datetime(2026, 8, 12, 1, tzinfo=timezone.utc), 0, "TIMEOUT", None, ()))
        self.assertIsInstance(completed, ProviderAttemptRecord)
        replay = ledger.claim(reservation())
        self.assertIsInstance(replay, ProviderAttemptClaim)
        self.assertIs(replay.created, False)
        self.assertEqual(replay.record, completed)

    def test_memory_cross_authorization_idempotency_conflict_preserves_both_groups(self):
        authorization_a = approved_authorization(authorization_id="authorization:a", task_id="task:a")
        authorization_b = approved_authorization(authorization_id="authorization:b", task_id="task:b")
        ledger = ProviderAttemptLedger({authorization_a.authorization_id: authorization_a, authorization_b.authorization_id: authorization_b})
        first_a = ledger.claim(reservation("attempt:a", authorization_id=authorization_a.authorization_id, task_id=authorization_a.task_id, key="key:a"))
        first_b = ledger.claim(reservation("attempt:b", authorization_id=authorization_b.authorization_id, task_id=authorization_b.task_id, key="key:b"))
        self.assertIsInstance(first_a, ProviderAttemptClaim)
        self.assertIsInstance(first_b, ProviderAttemptClaim)

        collision = ledger.claim(reservation("attempt:a:collision", authorization_id=authorization_a.authorization_id, task_id=authorization_a.task_id, key="key:b"))
        self.assertEqual(collision, ProviderAttemptFailure("validation", "IDEMPOTENCY_CONFLICT", "idempotency key was already used with different input"))
        self.assertEqual(ledger.get(first_a.record.attempt_id), first_a.record)
        self.assertEqual(ledger.get(first_b.record.attempt_id), first_b.record)
        self.assertEqual(ledger.list_for_authorization(authorization_a.authorization_id), (first_a.record,))
        self.assertEqual(ledger.list_for_authorization(authorization_b.authorization_id), (first_b.record,))

    def test_lookup_validation_happens_before_repository_mutation(self):
        class SpyRepository:
            def __init__(self):
                self.calls = 0

            def reserve(self, *_args):
                self.calls += 1
                return ProviderAttemptFailure("execution", "unexpected", "unexpected")

            def complete(self, outcome):
                self.calls += 1
                return outcome

            def get(self, attempt_id):
                self.calls += 1
                return attempt_id

            def list_for_authorization(self, authorization_id):
                self.calls += 1
                return ()

        spy = SpyRepository()
        malformed = ProviderAttemptLedger(lambda _id: object(), spy).reserve(reservation())
        self.assertIsInstance(malformed, ProviderAttemptFailure)
        self.assertEqual(malformed.code, "INVALID_AUTHORIZATION")
        self.assertEqual(spy.calls, 0)

        authorization = approved_authorization()
        mismatched = ProviderAttemptLedger(lambda _id: replace(authorization, task_id="task:other"), spy).reserve(reservation())
        self.assertEqual(mismatched.code, "AUTHORIZATION_MISMATCH")
        self.assertEqual(spy.calls, 0)

        mismatched_authorization = ProviderAttemptLedger(lambda _id: replace(authorization, authorization_id="authorization:other"), spy).reserve(reservation())
        self.assertEqual(mismatched_authorization.code, "AUTHORIZATION_MISMATCH")
        self.assertEqual(spy.calls, 0)

        reversed_snapshot = replace(authorization.price_snapshot, line_items=tuple(reversed(authorization.price_snapshot.line_items)))
        malformed_snapshot = replace(authorization, price_snapshot=reversed_snapshot)
        reversed_result = ProviderAttemptLedger(lambda _id: malformed_snapshot, spy).reserve(reservation())
        self.assertEqual(reversed_result.code, "INVALID_AUTHORIZATION")
        self.assertEqual(spy.calls, 0)

    def test_exact_reservation_replays_and_changed_input_conflicts(self):
        authorization = approved_authorization()
        ledger = ProviderAttemptLedger(lambda _id: authorization)
        first = ledger.reserve(reservation())
        self.assertIsInstance(first, ProviderAttemptRecord)
        self.assertEqual(ledger.reserve(reservation()), first)
        changed = ledger.reserve(reservation(provider="other-provider"))
        self.assertEqual(changed.code, "ATTEMPT_CONFLICT")
        for field, value in (("decision_id", "decision:changed"), ("thread_id", "thread:changed"), ("creator_id", "creator:changed"), ("maximum_approved_amount_micros", 5_000)):
            changed_auth = replace(authorization, **{field: value})
            lookup_values = iter((authorization, changed_auth))
            replay_with_changed_auth = ProviderAttemptLedger(lambda _id: next(lookup_values))
            replay_with_changed_auth.reserve(reservation(f"attempt:auth:{field}", key=f"key:auth:{field}"))
            changed_auth_result = replay_with_changed_auth.reserve(reservation(f"attempt:auth:{field}", key=f"key:auth:{field}"))
            self.assertEqual(changed_auth_result.code, "ATTEMPT_CONFLICT")

    def test_started_blocks_scope_and_failed_terminal_allows_bounded_retry(self):
        authorization = approved_authorization(maximum=6_000)
        ledger = ProviderAttemptLedger(lambda _id: authorization)
        first = ledger.reserve(reservation())
        self.assertIsInstance(first, ProviderAttemptRecord)
        blocked = ledger.reserve(reservation("attempt:blocked", key="key:blocked"))
        self.assertEqual(blocked.code, "ATTEMPT_IN_PROGRESS")
        failed = ledger.complete(ProviderAttemptOutcome("attempt:contract", "failed", datetime(2026, 8, 12, 1, tzinfo=timezone.utc), 0, "TIMEOUT", None, ()))
        self.assertEqual(failed.status, "failed")
        retry = ledger.reserve(reservation("attempt:retry", key="key:retry"))
        self.assertIsInstance(retry, ProviderAttemptRecord)
        self.assertEqual(retry.attempt_number, 2)

        capped_auth = replace(approved_authorization(authorization_id="authorization:cap", maximum=6_000), maximum_approved_amount_micros=3_000)
        capped_ledger = ProviderAttemptLedger(lambda _id: capped_auth)
        for index, (scene_id, operation) in enumerate((("scene-1", "visual"), ("scene-1", "voice"), ("scene-2", "visual"), ("scene-2", "voice"))):
            capped = capped_ledger.reserve(reservation(f"attempt:cap:{index}", authorization_id="authorization:cap", scene_id=scene_id, operation=operation, key=f"key:cap:{index}"))
            self.assertIsInstance(capped, ProviderAttemptRecord)
        capped_ledger.complete(ProviderAttemptOutcome("attempt:cap:0", "failed", datetime(2026, 8, 12, 1, tzinfo=timezone.utc), 0, "TIMEOUT", None, ()))
        over = capped_ledger.reserve(reservation("attempt:cap:retry", authorization_id="authorization:cap", key="key:cap:retry"))
        self.assertEqual(over.code, "BUDGET_LIMIT")

    def test_failed_attempt_cannot_retry_with_changed_authorization_identity(self):
        authorization = approved_authorization(authorization_id="authorization:retry-identity")
        current = [authorization]
        ledger = ProviderAttemptLedger(lambda _id: current[0])
        first = ledger.reserve(reservation(authorization_id=authorization.authorization_id))
        self.assertIsInstance(first, ProviderAttemptRecord)
        failed = ledger.complete(ProviderAttemptOutcome(first.attempt_id, "failed", datetime(2026, 8, 12, 1, tzinfo=timezone.utc), 0, "TIMEOUT", None, ()))
        self.assertIsInstance(failed, ProviderAttemptRecord)
        current[0] = replace(authorization, creator_id="creator:changed")
        retry = ledger.reserve(reservation("attempt:retry-identity", authorization_id=authorization.authorization_id, key="key:retry-identity"))
        self.assertEqual(retry.code, "ATTEMPT_CONFLICT")

    def test_terminal_transition_requires_valid_media_and_replays_exactly(self):
        authorization = approved_authorization()
        ledger = ProviderAttemptLedger(lambda _id: authorization)
        ledger.reserve(reservation())
        completed_at = datetime(2026, 8, 12, 1, tzinfo=timezone.utc)
        outcome = ProviderAttemptOutcome("attempt:contract", "succeeded", completed_at, 1_000, "SUCCESS", WorkspaceFileReference("task:contract", "provider-records", "response.json"), (WorkspaceFileReference("task:contract", "media", "scene-1.mp4"),))
        result = ledger.complete(outcome)
        self.assertIsInstance(result, ProviderAttemptRecord)
        self.assertEqual(ledger.complete(outcome), result)
        conflict = ledger.complete(replace(outcome, charged_amount_micros=999))
        self.assertEqual(conflict.code, "ATTEMPT_OUTCOME_CONFLICT")
        self.assertEqual(ledger.reserve(reservation()), result)

    def test_public_records_are_frozen_slotted_and_have_frozen_fields(self):
        expected = {
            ProviderAttemptReservation: ("attempt_id", "task_id", "authorization_id", "scene_id", "operation", "provider", "idempotency_key", "request_record_reference", "reserved_at"),
            ProviderAttemptOutcome: ("attempt_id", "status", "completed_at", "charged_amount_micros", "result_code", "response_record_reference", "output_references"),
            ProviderAttemptRecord: ("attempt_id", "task_id", "authorization_id", "production_request_reference", "budget_reference", "scene_id", "operation", "provider", "attempt_number", "idempotency_key", "request_record_reference", "currency", "reserved_amount_micros", "status", "reserved_at", "completed_at", "charged_amount_micros", "result_code", "response_record_reference", "output_references"),
            ProviderAttemptFailure: ("kind", "code", "message"),
            ProviderAttemptClaim: ("record", "created"),
        }
        for record, names in expected.items():
            self.assertEqual(tuple(field.name for field in fields(record)), names)
            self.assertTrue(hasattr(record, "__slots__"))
        authorization = approved_authorization()
        ledger = ProviderAttemptLedger(lambda _id: authorization)
        result = ledger.reserve(reservation())
        claim = ProviderAttemptLedger(lambda _id: authorization).claim(reservation("attempt:claim", key="key:claim"))
        records = (result, claim, ProviderAttemptOutcome("attempt:failure", "failed", datetime(2026, 8, 12, tzinfo=timezone.utc), 0, "TIMEOUT", None, ()), ProviderAttemptFailure("validation", "CODE", "message"))
        for record in records:
            with self.assertRaises(FrozenInstanceError):
                record.__class__.__setattr__(record, fields(record.__class__)[0].name, None)

    def test_ledger_rejects_mismatched_repository_successes(self):
        authorization = approved_authorization()
        valid = ProviderAttemptLedger(lambda _id: authorization).reserve(reservation("attempt:seed", key="key:seed"))

        class MismatchedRepository:
            def reserve(self, _reservation, _authorization):
                return replace(valid, status="failed")

            def complete(self, _outcome):
                return replace(valid, attempt_id="attempt:other")

            def get(self, _attempt_id):
                return valid

            def list_for_authorization(self, _authorization_id):
                return (valid,)

        repository = MismatchedRepository()
        reserve_result = ProviderAttemptLedger(lambda _id: authorization, repository).reserve(reservation())
        self.assertEqual(reserve_result.code, "ATTEMPT_STORAGE_FAILED")
        complete_result = ProviderAttemptLedger(lambda _id: authorization, repository).complete(ProviderAttemptOutcome("attempt:seed", "failed", datetime(2026, 8, 12, 1, tzinfo=timezone.utc), 0, "TIMEOUT", None, ()))
        self.assertEqual(complete_result.code, "ATTEMPT_STORAGE_FAILED")

        class StaticLineageMutationRepository(MismatchedRepository):
            def complete(self, _outcome):
                return replace(valid, production_request_reference=ArtifactReference("production_request", "request:forged", 1))

        lineage_result = ProviderAttemptLedger(lambda _id: authorization, StaticLineageMutationRepository()).complete(ProviderAttemptOutcome("attempt:seed", "failed", datetime(2026, 8, 12, 1, tzinfo=timezone.utc), 0, "TIMEOUT", None, ()))
        self.assertEqual(lineage_result.code, "ATTEMPT_STORAGE_FAILED")

    def test_ledger_rejects_forged_claim_types_and_terminal_creation(self):
        authorization = approved_authorization()
        valid = ProviderAttemptLedger(lambda _id: authorization).reserve(reservation("attempt:seed", key="key:seed"))

        class ClaimRepository:
            def __init__(self, claim):
                self._claim = claim

            def claim(self, _reservation, _authorization):
                return self._claim

            def reserve(self, _reservation, _authorization):
                return valid

            def complete(self, _outcome):
                return valid

            def get(self, _attempt_id):
                return valid

            def list_for_authorization(self, _authorization_id):
                return (valid,)

        storage_failure = ProviderAttemptFailure("execution", "ATTEMPT_STORAGE_FAILED", "provider attempt persistence failed")
        forged = ProviderAttemptLedger(lambda _id: authorization, ClaimRepository(ProviderAttemptClaim(valid, 1))).claim(reservation("attempt:seed", key="key:seed"))
        self.assertEqual(forged, storage_failure)

        class CorruptFailureRepository(ClaimRepository):
            def claim(self, _reservation, _authorization):
                return ProviderAttemptFailure("validation", "ATTEMPT_STORAGE_FAILED", "raw storage detail")

        normalized = ProviderAttemptLedger(lambda _id: authorization, CorruptFailureRepository(None)).claim(reservation("attempt:seed", key="key:seed"))
        self.assertEqual(normalized, storage_failure)

        terminal = replace(valid, status="failed", completed_at=datetime(2026, 8, 12, 1, tzinfo=timezone.utc), charged_amount_micros=0, result_code="TIMEOUT")
        result = ProviderAttemptLedger(lambda _id: authorization, ClaimRepository(ProviderAttemptClaim(terminal, True))).claim(reservation("attempt:seed", key="key:seed"))
        self.assertEqual(result, storage_failure)

    def test_default_memory_repository_serializes_same_scope_race(self):
        authorization = approved_authorization()
        ledger = ProviderAttemptLedger(lambda _id: authorization)

        def reserve(index):
            return ledger.reserve(reservation(f"attempt:race:{index}", key=f"key:race:{index}"))

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(executor.map(reserve, (1, 2)))
        successes = [item for item in results if isinstance(item, ProviderAttemptRecord)]
        blocked = [item for item in results if isinstance(item, ProviderAttemptFailure) and item.code == "ATTEMPT_IN_PROGRESS"]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(blocked), 1)


if __name__ == "__main__":
    unittest.main()
