"""Offline cross-slice proof from an approved Script to Authorization."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
import unittest

from ai_course_factory.artifacts import ScriptDecisionRecord, StoryboardDecisionRecord
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetAuthorizationRecord,
    BudgetDecisionOutcome,
    BudgetDecisionRecord,
    BudgetFailure,
    BudgetModule,
    PriceLineItem,
    PriceSnapshot,
    RetryPolicy,
)

from tests.integration.test_production_request_planning import (
    committed_upstreams,
    request_candidate,
)


class AuthorizedProductionRequestIntegrationTests(unittest.TestCase):
    @staticmethod
    def _fixture_snapshot(request_reference, request_version):
        scenes = request_version.payload["production_request"]["scenes"]
        line_items = tuple(
            PriceLineItem(
                scene["scene_id"],
                operation,
                "per_scene",
                1,
                1_000 if operation == "visual" else 500,
            )
            for scene in scenes
            for operation in ("visual", "voice")
        )
        return PriceSnapshot(
            snapshot_id="fixture-prices-v1",
            source="local-fixture",
            currency="USD",
            production_request_reference=request_reference,
            line_items=line_items,
        )

    def _budget_candidate(self, result):
        if isinstance(result, BudgetFailure):
            self.fail(f"Budget estimation failed: {result.code}")
        return result

    def _committed_chain(self):
        inputs = committed_upstreams()
        (
            artifacts,
            runtime,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            timeline_reference,
            timeline_version,
        ) = inputs
        self.assertIsInstance(script_decision, ScriptDecisionRecord)
        self.assertEqual(script_decision.action, "approve")
        self.assertEqual(script_decision.script_reference, script_reference)
        self.assertEqual(script_decision.assessment_disposition, "pass")
        self.assertIsInstance(storyboard_decision, StoryboardDecisionRecord)
        self.assertTrue(storyboard_decision.review_enabled)
        self.assertEqual(storyboard_decision.action, "approve")

        request = request_candidate(inputs)
        request_reference = artifacts.commit(request)
        request_version = artifacts.get(request_reference)

        price_snapshot = self._fixture_snapshot(request_reference, request_version)
        retry_policy = RetryPolicy(2)
        budget_candidate = self._budget_candidate(
            BudgetModule.estimate(
                request_reference,
                request_version,
                price_snapshot=price_snapshot,
                retry_policy=retry_policy,
                budget_identity="budget:episode-1",
                budget_commit_id="budget-commit-1",
            )
        )
        budget_reference = artifacts.commit(budget_candidate)
        budget_version = artifacts.get(budget_reference)

        return {
            "artifacts": artifacts,
            "runtime": runtime,
            "script_reference": script_reference,
            "script_version": script_version,
            "script_decision": script_decision,
            "character_reference": character_reference,
            "character_version": character_version,
            "storyboard_reference": storyboard_reference,
            "storyboard_version": storyboard_version,
            "storyboard_decision": storyboard_decision,
            "timeline_reference": timeline_reference,
            "timeline_version": timeline_version,
            "request_reference": request_reference,
            "request_version": request_version,
            "price_snapshot": price_snapshot,
            "retry_policy": retry_policy,
            "budget_reference": budget_reference,
            "budget_version": budget_version,
        }

    def test_exact_approved_script_reaches_authorized_request_with_full_lineage(self):
        values = self._committed_chain()
        script_reference = values["script_reference"]
        script_decision = values["script_decision"]
        character_reference = values["character_reference"]
        character_version = values["character_version"]
        storyboard_reference = values["storyboard_reference"]
        storyboard_version = values["storyboard_version"]
        storyboard_decision = values["storyboard_decision"]
        timeline_reference = values["timeline_reference"]
        timeline_version = values["timeline_version"]
        request_reference = values["request_reference"]
        request_version = values["request_version"]
        budget_reference = values["budget_reference"]
        budget_version = values["budget_version"]

        self.assertEqual(values["script_version"].artifact_type, "script")
        self.assertEqual(character_reference.artifact_type, "character")
        self.assertEqual(character_version.dependencies, (script_reference,))
        self.assertEqual(character_version.payload["script_reference"], script_reference)
        self.assertEqual(
            character_version.payload["approval_decision_id"], script_decision.decision_id
        )

        self.assertEqual(storyboard_reference.artifact_type, "storyboard")
        self.assertEqual(
            storyboard_version.dependencies, (script_reference, character_reference)
        )
        self.assertEqual(storyboard_version.payload["script_reference"], script_reference)
        self.assertEqual(
            storyboard_version.payload["character_reference"], character_reference
        )
        self.assertEqual(
            storyboard_version.payload["approval_decision_id"], script_decision.decision_id
        )
        self.assertEqual(
            storyboard_decision.script_approval_decision_id, script_decision.decision_id
        )
        self.assertEqual(storyboard_decision.storyboard_reference, storyboard_reference)

        self.assertEqual(timeline_reference.artifact_type, "timeline")
        self.assertEqual(
            timeline_version.dependencies,
            (script_reference, character_reference, storyboard_reference),
        )
        self.assertEqual(timeline_version.payload["script_reference"], script_reference)
        self.assertEqual(
            timeline_version.payload["character_reference"], character_reference
        )
        self.assertEqual(
            timeline_version.payload["storyboard_reference"], storyboard_reference
        )
        self.assertEqual(
            timeline_version.payload["approval_decision_id"], script_decision.decision_id
        )
        self.assertEqual(
            timeline_version.payload["storyboard_decision_id"], storyboard_decision.decision_id
        )

        self.assertEqual(request_reference.artifact_type, "production_request")
        self.assertEqual(
            request_version.dependencies,
            (
                script_reference,
                character_reference,
                storyboard_reference,
                timeline_reference,
            ),
        )
        self.assertEqual(request_version.payload["script_reference"], script_reference)
        self.assertEqual(
            request_version.payload["character_reference"], character_reference
        )
        self.assertEqual(
            request_version.payload["storyboard_reference"], storyboard_reference
        )
        self.assertEqual(request_version.payload["timeline_reference"], timeline_reference)
        self.assertEqual(
            request_version.payload["approval_decision_id"], script_decision.decision_id
        )
        self.assertEqual(
            request_version.payload["storyboard_decision_id"], storyboard_decision.decision_id
        )

        request_scene_ids = tuple(
            scene["scene_id"] for scene in request_version.payload["production_request"]["scenes"]
        )
        self.assertEqual(
            request_scene_ids,
            tuple(scene["scene_id"] for scene in values["script_version"].payload["scenes"]),
        )
        self.assertEqual(len(request_scene_ids), 6)

        self.assertEqual(budget_reference.artifact_type, "production_budget")
        self.assertEqual(budget_version.dependencies, (request_reference,))
        self.assertEqual(
            budget_version.payload["production_request_reference"], request_reference
        )
        snapshot_payload = budget_version.payload["price_snapshot"]
        self.assertEqual(snapshot_payload["production_request_reference"], request_reference)
        self.assertEqual(snapshot_payload["currency"], "USD")
        line_item_keys = tuple(
            (item["scene_id"], item["operation"])
            for item in snapshot_payload["line_items"]
        )
        expected_line_item_keys = tuple(
            (scene_id, operation)
            for scene_id in request_scene_ids
            for operation in ("visual", "voice")
        )
        self.assertEqual(line_item_keys, expected_line_item_keys)

        runtime_purposes = tuple(request.purpose for request in values["runtime"].requests)
        expected_purposes = (
            "character_planning",
            "storyboard_planning",
            "timeline_planning",
            "production_request_planning",
        )
        self.assertEqual(runtime_purposes, expected_purposes)

        decided_at = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
        authorization_boundary = BudgetAuthorizationBoundary()
        approved_amount = budget_version.payload["estimate"]["policy_maximum_amount_micros"]
        approved = authorization_boundary.decide(
            request_reference,
            request_version,
            budget_reference,
            budget_version,
            decision_id="budget-decision-1",
            authorization_id="budget-auth-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=decided_at,
            action="approve",
            maximum_approved_amount_micros=approved_amount,
            maximum_attempts=values["retry_policy"].maximum_attempts,
        )
        self.assertIsInstance(approved, BudgetDecisionOutcome)
        self.assertIsInstance(approved.decision, BudgetDecisionRecord)
        self.assertIsInstance(approved.authorization, BudgetAuthorizationRecord)
        self.assertIsNot(approved.decision, approved.authorization)
        self.assertIs(
            authorization_boundary.get_decision("budget-decision-1"), approved.decision
        )
        self.assertIs(
            authorization_boundary.get_authorization("budget-auth-1"),
            approved.authorization,
        )

        decision = approved.decision
        authorization = approved.authorization
        self.assertEqual(decision.production_request_reference, request_reference)
        self.assertEqual(decision.budget_reference, budget_reference)
        self.assertEqual(decision.action, "approve")
        self.assertEqual(decision.authorization_id, "budget-auth-1")
        self.assertEqual(decision.maximum_approved_amount_micros, approved_amount)
        self.assertEqual(decision.maximum_attempts, 2)
        self.assertEqual(decision.task_id, "task-1")
        self.assertEqual(decision.thread_id, "thread-1")
        self.assertEqual(decision.creator_id, "creator-1")
        self.assertEqual(decision.decided_at, decided_at)

        self.assertEqual(authorization.production_request_reference, request_reference)
        self.assertEqual(authorization.budget_reference, budget_reference)
        self.assertEqual(authorization.currency, "USD")
        self.assertEqual(authorization.price_snapshot, values["price_snapshot"])
        self.assertEqual(authorization.task_id, "task-1")
        self.assertEqual(authorization.thread_id, "thread-1")
        self.assertEqual(authorization.creator_id, "creator-1")
        self.assertEqual(authorization.decision_id, "budget-decision-1")
        self.assertEqual(authorization.authorization_id, "budget-auth-1")
        self.assertEqual(authorization.decided_at, decided_at)
        self.assertEqual(authorization.maximum_approved_amount_micros, approved_amount)
        self.assertEqual(authorization.maximum_attempts, 2)

        with self.assertRaises(FrozenInstanceError):
            decision.action = "reject"
        with self.assertRaises(FrozenInstanceError):
            authorization.currency = "EUR"

        replay = authorization_boundary.decide(
            request_reference,
            request_version,
            budget_reference,
            budget_version,
            decision_id="budget-decision-1",
            authorization_id="budget-auth-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=decided_at,
            action="approve",
            maximum_approved_amount_micros=approved_amount,
            maximum_attempts=values["retry_policy"].maximum_attempts,
        )
        self.assertIsInstance(replay, BudgetDecisionOutcome)
        self.assertIs(replay.decision, decision)
        self.assertIs(replay.authorization, authorization)

    def test_reject_and_underfunded_approvals_are_atomic_for_same_request_and_budget(self):
        values = self._committed_chain()
        request_reference = values["request_reference"]
        request_version = values["request_version"]
        budget_reference = values["budget_reference"]
        budget_version = values["budget_version"]
        authorization_boundary = BudgetAuthorizationBoundary()
        decided_at = datetime(2026, 8, 12, 12, 5, tzinfo=timezone.utc)

        rejected = authorization_boundary.decide(
            request_reference,
            request_version,
            budget_reference,
            budget_version,
            decision_id="budget-reject-1",
            authorization_id=None,
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=decided_at,
            action="reject",
            decision_context="Creator lowered the episode scope.",
        )
        self.assertIsInstance(rejected, BudgetDecisionOutcome)
        self.assertIsInstance(rejected.decision, BudgetDecisionRecord)
        self.assertIsNone(rejected.authorization)
        self.assertEqual(rejected.decision.action, "reject")
        self.assertIs(
            authorization_boundary.get_decision("budget-reject-1"), rejected.decision
        )
        missing_rejection_auth = authorization_boundary.get_authorization(
            "budget-reject-auth"
        )
        self.assertIsInstance(missing_rejection_auth, BudgetFailure)
        self.assertEqual(missing_rejection_auth.code, "AUTHORIZATION_NOT_FOUND")

        estimate = budget_version.payload["estimate"]
        selected_attempts = 2
        required_amount = estimate["per_attempt_amount_micros"] * selected_attempts
        underfunded = authorization_boundary.decide(
            request_reference,
            request_version,
            budget_reference,
            budget_version,
            decision_id="budget-underfunded-1",
            authorization_id="budget-underfunded-auth-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            decided_at=decided_at,
            action="approve",
            maximum_approved_amount_micros=required_amount - 1,
            maximum_attempts=selected_attempts,
        )
        self.assertIsInstance(underfunded, BudgetFailure)
        self.assertEqual(underfunded.code, "UNDERFUNDED_AUTHORIZATION")
        missing_underfunded_decision = authorization_boundary.get_decision(
            "budget-underfunded-1"
        )
        self.assertIsInstance(missing_underfunded_decision, BudgetFailure)
        self.assertEqual(missing_underfunded_decision.code, "DECISION_NOT_FOUND")
        missing_underfunded_auth = authorization_boundary.get_authorization(
            "budget-underfunded-auth-1"
        )
        self.assertIsInstance(missing_underfunded_auth, BudgetFailure)
        self.assertEqual(missing_underfunded_auth.code, "AUTHORIZATION_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
