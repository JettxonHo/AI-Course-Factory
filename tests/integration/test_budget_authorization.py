"""Offline integration evidence for Budget Candidate and Creator authorization."""

import unittest
from dataclasses import replace
from datetime import datetime, timezone

from ai_course_factory.artifacts import ArtifactCommitBoundary, ArtifactReference, CommitConflictError
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetAuthorizationRecord,
    BudgetDecisionOutcome,
    BudgetDecisionRecord,
    BudgetFailure,
    BudgetModule,
    PriceLineItem,
    RetryPolicy,
)

from tests.production.test_budget import fixture_snapshot, production_request_parts


class BudgetAuthorizationIntegrationTests(unittest.TestCase):
    def _committed_budget(self, *, request_version=None):
        request_reference, request = production_request_parts()
        if request_version is not None:
            request_reference, request = request_version
        artifact_boundary = ArtifactCommitBoundary()
        budget_candidate = BudgetModule.estimate(
            request_reference,
            request,
            price_snapshot=fixture_snapshot(request_reference),
            retry_policy=RetryPolicy(2),
            budget_identity=f"budget:{request_reference.version}",
            budget_commit_id=f"budget-commit:{request_reference.version}",
        )
        budget_reference = artifact_boundary.commit(budget_candidate)
        return artifact_boundary, request_reference, request, budget_reference, artifact_boundary.get(budget_reference)

    def test_budget_candidate_commit_replays_and_changed_estimate_conflicts_without_mutating_version(self):
        artifacts, request_reference, request, _budget_reference, _budget = self._committed_budget()
        candidate = BudgetModule.estimate(
            request_reference,
            request,
            price_snapshot=fixture_snapshot(request_reference),
            retry_policy=RetryPolicy(2),
            budget_identity="budget:replay",
            budget_commit_id="budget-commit:replay",
        )
        first = artifacts.commit(candidate)
        replay_candidate = BudgetModule.estimate(
            request_reference,
            request,
            price_snapshot=fixture_snapshot(request_reference),
            retry_policy=RetryPolicy(2),
            budget_identity="budget:replay",
            budget_commit_id="budget-commit:replay",
        )
        self.assertEqual(artifacts.commit(replay_candidate), first)
        changed_items = list(fixture_snapshot(request_reference).line_items)
        changed_items[0] = PriceLineItem("scene-1", "visual", "per_scene", 1, 1_001)
        changed_candidate = BudgetModule.estimate(
            request_reference,
            request,
            price_snapshot=replace(fixture_snapshot(request_reference), line_items=tuple(changed_items)),
            retry_policy=RetryPolicy(2),
            budget_identity="budget:replay",
            budget_commit_id="budget-commit:replay",
        )
        with self.assertRaises(CommitConflictError):
            artifacts.commit(changed_candidate)
        committed = artifacts.get(first)
        self.assertEqual(
            committed.payload["price_snapshot"]["line_items"][0]["unit_price_micros"],
            1_000,
        )

    def test_exact_candidate_commit_approval_and_replay_create_independent_authorization(self):
        artifacts, request_reference, request, budget_reference, budget = self._committed_budget()
        boundary = BudgetAuthorizationBoundary()
        decided_at = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
        result = boundary.decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="budget-decision-1",
            authorization_id="budget-auth-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=decided_at,
            action="approve",
            maximum_approved_amount_micros=7_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(result, BudgetDecisionOutcome)
        self.assertIsInstance(result.decision, BudgetDecisionRecord)
        self.assertIsInstance(result.authorization, BudgetAuthorizationRecord)
        self.assertEqual(result.decision.gate_kind, "budget_review")
        self.assertEqual(result.decision.production_request_reference, request_reference)
        self.assertEqual(result.decision.budget_reference, budget_reference)
        self.assertEqual(result.authorization.price_snapshot.production_request_reference, request_reference)
        self.assertEqual(result.authorization.currency, "USD")
        self.assertIs(boundary.get_decision("budget-decision-1"), result.decision)
        self.assertIs(boundary.get_authorization("budget-auth-1"), result.authorization)
        replay = boundary.decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="budget-decision-1",
            authorization_id="budget-auth-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=decided_at,
            action="approve",
            maximum_approved_amount_micros=7_000,
            maximum_attempts=2,
        )
        self.assertIs(replay.decision, result.decision)
        self.assertIs(replay.authorization, result.authorization)
        conflict = boundary.decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="budget-decision-1",
            authorization_id="budget-auth-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=decided_at,
            action="approve",
            maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(conflict, BudgetFailure)
        self.assertEqual(conflict.code, "DECISION_CONFLICT")
        self.assertIs(boundary.get_decision("budget-decision-1"), result.decision)

    def test_rejection_requires_context_and_creates_no_authorization(self):
        _artifacts, request_reference, request, budget_reference, budget = self._committed_budget()
        boundary = BudgetAuthorizationBoundary()
        rejected = boundary.decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="budget-reject-1",
            authorization_id=None,
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=datetime.now(timezone.utc),
            action="reject",
            decision_context="Creator lowered the episode scope.",
        )
        self.assertIsInstance(rejected, BudgetDecisionOutcome)
        self.assertIsNone(rejected.authorization)
        self.assertEqual(rejected.decision.action, "reject")
        self.assertEqual(boundary.get_authorization("missing-auth").code, "AUTHORIZATION_NOT_FOUND")
        missing_context = boundary.decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="budget-reject-2",
            authorization_id=None,
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=datetime.now(timezone.utc),
            action="reject",
        )
        self.assertEqual(missing_context.code, "INVALID_DECISION_CONTEXT")
        self.assertEqual(boundary.get_decision("budget-reject-2").code, "DECISION_NOT_FOUND")

    def test_underfunded_over_attempt_and_budget_mutations_fail_atomically(self):
        artifacts, request_reference, request, budget_reference, budget = self._committed_budget()
        boundary = BudgetAuthorizationBoundary()
        common = {
            "production_request_reference": request_reference,
            "resolved_production_request": request,
            "budget_reference": budget_reference,
            "resolved_budget": budget,
            "task_id": "task-1",
            "thread_id": "thread-1",
            "creator_id": "creator-1",
            "decided_at": datetime.now(timezone.utc),
            "action": "approve",
        }
        underfunded = boundary.decide(
            **common,
            decision_id="underfunded",
            authorization_id="underfunded-auth",
            maximum_approved_amount_micros=5_999,
            maximum_attempts=2,
        )
        self.assertEqual(underfunded.code, "UNDERFUNDED_AUTHORIZATION")
        self.assertEqual(boundary.get_decision("underfunded").code, "DECISION_NOT_FOUND")
        over_attempt = boundary.decide(
            **common,
            decision_id="over-attempt",
            authorization_id="over-attempt-auth",
            maximum_approved_amount_micros=10_000,
            maximum_attempts=3,
        )
        self.assertEqual(over_attempt.code, "INVALID_MAXIMUM_ATTEMPTS")
        mutated = replace(
            budget,
            payload={
                **budget.payload,
                "estimate": {
                    **budget.payload["estimate"],
                    "per_attempt_amount_micros": 1,
                },
            },
        )
        malformed = boundary.decide(
            **{**common, "resolved_budget": mutated},
            decision_id="mutated-budget",
            authorization_id="mutated-budget-auth",
            maximum_approved_amount_micros=10_000,
            maximum_attempts=1,
        )
        self.assertEqual(malformed.code, "INVALID_BUDGET_ESTIMATE")
        self.assertEqual(boundary.get_authorization("mutated-budget-auth").code, "AUTHORIZATION_NOT_FOUND")
        type_mutated = replace(
            budget,
            payload={
                **budget.payload,
                "estimate": {
                    **budget.payload["estimate"],
                    "per_attempt_amount_micros": float(
                        budget.payload["estimate"]["per_attempt_amount_micros"]
                    ),
                },
            },
        )
        type_failure = boundary.decide(
            **{**common, "resolved_budget": type_mutated},
            decision_id="type-mutated-budget",
            authorization_id="type-mutated-budget-auth",
            maximum_approved_amount_micros=10_000,
            maximum_attempts=1,
        )
        self.assertEqual(type_failure.code, "INVALID_BUDGET_ESTIMATE")

    def test_authorization_identity_cannot_be_reused_by_another_decision(self):
        _artifacts, request_reference, request, budget_reference, budget = self._committed_budget()
        boundary = BudgetAuthorizationBoundary()
        common = {
            "production_request_reference": request_reference,
            "resolved_production_request": request,
            "budget_reference": budget_reference,
            "resolved_budget": budget,
            "task_id": "task-1",
            "thread_id": "thread-1",
            "creator_id": "creator-1",
            "decided_at": datetime.now(timezone.utc),
            "action": "approve",
            "maximum_approved_amount_micros": 6_000,
            "maximum_attempts": 2,
            "authorization_id": "shared-auth",
        }
        first = boundary.decide(**common, decision_id="decision-one")
        self.assertIsInstance(first, BudgetDecisionOutcome)
        reused = boundary.decide(**common, decision_id="decision-two")
        self.assertIsInstance(reused, BudgetFailure)
        self.assertEqual(reused.code, "AUTHORIZATION_CONFLICT")
        self.assertEqual(boundary.get_decision("decision-two").code, "DECISION_NOT_FOUND")
        self.assertIs(boundary.get_authorization("shared-auth"), first.authorization)

    def test_budget_payload_request_reference_mutation_fails_without_decision_or_authorization(self):
        _artifacts, request_reference, request, budget_reference, budget = self._committed_budget()
        boundary = BudgetAuthorizationBoundary()
        foreign_reference = ArtifactReference("production_request", "foreign", 1)
        mutated_budget = replace(
            budget,
            payload={
                **budget.payload,
                "production_request_reference": foreign_reference,
            },
        )
        result = boundary.decide(
            request_reference,
            request,
            budget_reference,
            mutated_budget,
            decision_id="mutated-request-reference",
            authorization_id="mutated-request-reference-auth",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=datetime.now(timezone.utc),
            action="approve",
            maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(result, BudgetFailure)
        self.assertEqual(result.code, "BUDGET_LINEAGE_MISMATCH")
        self.assertEqual(boundary.get_decision("mutated-request-reference").code, "DECISION_NOT_FOUND")
        self.assertEqual(
            boundary.get_authorization("mutated-request-reference-auth").code,
            "AUTHORIZATION_NOT_FOUND",
        )

    def test_unexpected_request_payload_exception_is_safe_and_atomic(self):
        class ExplodingPayload(dict):
            def __iter__(self):
                raise RuntimeError("secret provider detail")

        _artifacts, request_reference, request, budget_reference, budget = self._committed_budget()
        boundary = BudgetAuthorizationBoundary()
        malformed_request = replace(request, payload=ExplodingPayload())
        result = boundary.decide(
            request_reference,
            malformed_request,
            budget_reference,
            budget,
            decision_id="unexpected-request",
            authorization_id="unexpected-auth",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=datetime.now(timezone.utc),
            action="approve",
            maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(result, BudgetFailure)
        self.assertEqual(result.kind, "execution")
        self.assertEqual(result.code, "BUDGET_AUTHORIZATION_FAILED")
        self.assertNotIn("secret provider detail", result.message)
        self.assertEqual(boundary.get_decision("unexpected-request").code, "DECISION_NOT_FOUND")

    def test_new_request_version_requires_new_budget_and_authorization(self):
        artifacts, request_reference, request, budget_reference, budget = self._committed_budget()
        auth_boundary = BudgetAuthorizationBoundary()
        first = auth_boundary.decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="v1-decision",
            authorization_id="v1-auth",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=datetime.now(timezone.utc),
            action="approve",
            maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(first, BudgetDecisionOutcome)
        revised_reference = ArtifactReference("production_request", "episode-1", 2)
        revised = replace(request, reference=revised_reference)
        stale = auth_boundary.decide(
            revised_reference,
            revised,
            budget_reference,
            budget,
            decision_id="v2-stale-budget",
            authorization_id="v2-stale-auth",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=datetime.now(timezone.utc),
            action="approve",
            maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertEqual(stale.code, "BUDGET_LINEAGE_MISMATCH")
        self.assertIs(auth_boundary.get_authorization("v1-auth"), first.authorization)
        new_artifacts, _ref, _req, new_budget_reference, new_budget = self._committed_budget(
            request_version=(revised_reference, revised)
        )
        self.assertEqual(new_budget_reference.version, 1)
        self.assertNotEqual(new_budget_reference, budget_reference)
        self.assertEqual(new_budget.dependencies, (revised_reference,))


if __name__ == "__main__":
    unittest.main()
