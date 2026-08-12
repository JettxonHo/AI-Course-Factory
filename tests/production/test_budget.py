"""Public behavior tests for deterministic Production Budget estimation."""

import unittest
from dataclasses import fields, replace

from ai_course_factory.artifacts import ArtifactCommitBoundary, ArtifactReference, ArtifactVersion
from ai_course_factory.production import BudgetAuthorizationRecord, BudgetDecisionOutcome, BudgetDecisionRecord, BudgetFailure, BudgetModule, PriceLineItem, PriceSnapshot, RetryPolicy


def production_request_parts():
    request_reference = ArtifactReference("production_request", "episode-1", 1)
    dependencies = (
        ArtifactReference("script", "episode-1", 1),
        ArtifactReference("character", "episode-1", 1),
        ArtifactReference("storyboard", "episode-1", 1),
        ArtifactReference("timeline", "episode-1", 1),
    )
    request = ArtifactVersion(
        reference=request_reference,
        payload={
            "script_reference": dependencies[0],
            "approval_decision_id": "script-approval-1",
            "character_reference": dependencies[1],
            "storyboard_reference": dependencies[2],
            "storyboard_decision_id": "storyboard-approval-1",
            "timeline_reference": dependencies[3],
            "production_request": {
                "language": "zh-CN",
                "aspect_ratio": "9:16",
                "duration_seconds": 60.0,
                "scenes": (
                    {
                        "scene_id": "scene-1",
                        "start_seconds": 0.0,
                        "duration_seconds": 30.0,
                        "end_seconds": 30.0,
                        "narration": "你好。",
                        "visual_intent": "展示小土豆。",
                        "character_action": "挥手。",
                        "continuity_notes": ("保持围巾可见。",),
                    },
                    {
                        "scene_id": "scene-2",
                        "start_seconds": 30.0,
                        "duration_seconds": 30.0,
                        "end_seconds": 60.0,
                        "narration": "再见。",
                        "visual_intent": "小土豆离开。",
                        "character_action": "转身。",
                        "continuity_notes": ("保持围巾可见。",),
                    },
                ),
            },
        },
        provenance=(),
        dependencies=dependencies,
        commit_id="request-commit-1",
    )
    return request_reference, request


def fixture_snapshot(reference, *, duplicate=False, foreign=False):
    line_items = [
        PriceLineItem("scene-1", "visual", "per_scene", 1, 1_000),
        PriceLineItem("scene-1", "voice", "per_scene", 1, 500),
        PriceLineItem("scene-2", "visual", "per_scene", 1, 1_000),
        PriceLineItem("scene-2", "voice", "per_scene", 1, 500),
    ]
    if duplicate:
        line_items[-1] = line_items[-2]
    if foreign:
        line_items[-1] = PriceLineItem("scene-x", "voice", "per_scene", 1, 500)
    return PriceSnapshot(
        snapshot_id="fixture-prices-v1",
        source="local-fixture",
        currency="USD",
        production_request_reference=reference,
        line_items=tuple(line_items),
    )


class BudgetModuleTests(unittest.TestCase):
    def test_estimate_returns_deterministic_budget_candidate_from_fixture_snapshot(self):
        request_reference = ArtifactReference("production_request", "episode-1", 1)
        request = ArtifactVersion(
            reference=request_reference,
            payload={
                "script_reference": ArtifactReference("script", "episode-1", 1),
                "approval_decision_id": "script-approval-1",
                "character_reference": ArtifactReference("character", "episode-1", 1),
                "storyboard_reference": ArtifactReference("storyboard", "episode-1", 1),
                "storyboard_decision_id": "storyboard-approval-1",
                "timeline_reference": ArtifactReference("timeline", "episode-1", 1),
                "production_request": {
                    "language": "zh-CN",
                    "aspect_ratio": "9:16",
                    "duration_seconds": 60.0,
                    "scenes": (
                        {
                            "scene_id": "scene-1",
                            "start_seconds": 0.0,
                            "duration_seconds": 60.0,
                            "end_seconds": 60.0,
                            "narration": "你好。",
                            "visual_intent": "展示小土豆。",
                            "character_action": "挥手。",
                            "continuity_notes": ("保持围巾可见。",),
                        },
                    ),
                },
            },
            provenance=(),
            dependencies=(
                ArtifactReference("script", "episode-1", 1),
                ArtifactReference("character", "episode-1", 1),
                ArtifactReference("storyboard", "episode-1", 1),
                ArtifactReference("timeline", "episode-1", 1),
            ),
            commit_id="request-commit-1",
        )
        snapshot = PriceSnapshot(
            snapshot_id="fixture-prices-v1",
            source="local-fixture",
            currency="USD",
            production_request_reference=request_reference,
            line_items=(
                PriceLineItem("scene-1", "visual", "per_scene", 1, 1_000),
                PriceLineItem("scene-1", "voice", "per_scene", 1, 500),
            ),
        )

        candidate = BudgetModule().estimate(
            request_reference,
            request,
            price_snapshot=snapshot,
            retry_policy=RetryPolicy(2),
            budget_identity="budget:episode-1",
            budget_commit_id="budget-commit-1",
        )

        self.assertEqual(candidate.artifact_type, "production_budget")
        self.assertEqual(candidate.payload["estimate"]["per_attempt_amount_micros"], 1_500)
        self.assertEqual(candidate.payload["estimate"]["policy_maximum_amount_micros"], 3_000)

    def test_estimate_normalizes_snapshot_order_and_commits_immutably(self):
        reference, request = production_request_parts()
        snapshot = fixture_snapshot(reference)
        candidate = BudgetModule().estimate(
            reference,
            request,
            price_snapshot=PriceSnapshot(
                snapshot.snapshot_id,
                snapshot.source,
                snapshot.currency,
                snapshot.production_request_reference,
                tuple(reversed(snapshot.line_items)),
            ),
            retry_policy=RetryPolicy(3),
            budget_identity="budget:episode-1",
            budget_commit_id="budget-commit-1",
        )
        self.assertEqual(candidate.dependencies, (reference,))
        self.assertTrue(candidate.validated)
        self.assertIsNone(candidate.prior_reference)
        artifact_boundary = ArtifactCommitBoundary()
        budget_reference = artifact_boundary.commit(candidate)
        committed = artifact_boundary.get(budget_reference)
        self.assertEqual(committed.payload["production_request_reference"], reference)
        self.assertEqual(
            tuple((item["scene_id"], item["operation"]) for item in committed.payload["price_snapshot"]["line_items"]),
            (("scene-1", "visual"), ("scene-1", "voice"), ("scene-2", "visual"), ("scene-2", "voice")),
        )

    def test_invalid_snapshot_coverage_types_and_request_lineage_fail_before_candidate(self):
        reference, request = production_request_parts()
        cases = (
            (request, fixture_snapshot(reference, duplicate=True), "DUPLICATE_PRICE_LINE_ITEM"),
            (request, fixture_snapshot(reference, foreign=True), "INVALID_PRICE_SNAPSHOT_COVERAGE"),
            (
                replace(request, dependencies=(request.dependencies[1], request.dependencies[0], *request.dependencies[2:])),
                fixture_snapshot(reference),
                "PRODUCTION_REQUEST_LINEAGE_MISMATCH",
            ),
            (
                request,
                replace(
                    fixture_snapshot(reference),
                    line_items=(
                        PriceLineItem("scene-1", "visual", "per_scene", True, 1_000),
                        *fixture_snapshot(reference).line_items[1:],
                    ),
                ),
                "INVALID_PRICE_LINE_ITEM",
            ),
        )
        for target_request, snapshot, expected in cases:
            result = BudgetModule().estimate(
                reference,
                target_request,
                price_snapshot=snapshot,
                retry_policy=RetryPolicy(1),
                budget_identity=f"invalid-{expected}",
                budget_commit_id=f"invalid-{expected}-commit",
            )
            self.assertIsInstance(result, BudgetFailure)
            self.assertEqual(result.code, expected)

    def test_retry_policy_and_price_values_are_exact_positive_integers(self):
        reference, request = production_request_parts()
        snapshot = fixture_snapshot(reference)
        for policy in (RetryPolicy(0), RetryPolicy(4), RetryPolicy(True)):
            result = BudgetModule().estimate(
                reference,
                request,
                price_snapshot=snapshot,
                retry_policy=policy,
                budget_identity=f"bad-policy-{policy.maximum_attempts}",
                budget_commit_id=f"bad-policy-{policy.maximum_attempts}-commit",
            )
            self.assertEqual(result.code, "INVALID_MAXIMUM_ATTEMPTS")

        for index, value in enumerate((1.5, True, 0, -1)):
            items = list(snapshot.line_items)
            items[0] = replace(items[0], unit_price_micros=value)
            result = BudgetModule().estimate(
                reference,
                request,
                price_snapshot=replace(snapshot, line_items=tuple(items)),
                retry_policy=RetryPolicy(1),
                budget_identity=f"bad-price-{index}",
                budget_commit_id=f"bad-price-{index}-commit",
            )
            self.assertIsInstance(result, BudgetFailure)
            self.assertEqual(result.code, "INVALID_PRICE_LINE_ITEM")

    def test_public_records_are_frozen_and_approval_is_not_a_budget_module_side_effect(self):
        expected_fields = {
            PriceLineItem: ("scene_id", "operation", "unit", "quantity", "unit_price_micros"),
            PriceSnapshot: (
                "snapshot_id",
                "source",
                "currency",
                "production_request_reference",
                "line_items",
            ),
            RetryPolicy: ("maximum_attempts",),
            BudgetFailure: ("kind", "code", "message"),
            BudgetDecisionRecord: (
                "decision_id",
                "task_id",
                "thread_id",
                "creator_id",
                "gate_kind",
                "production_request_reference",
                "budget_reference",
                "action",
                "authorization_id",
                "maximum_approved_amount_micros",
                "maximum_attempts",
                "decided_at",
                "decision_context",
            ),
            BudgetAuthorizationRecord: (
                "authorization_id",
                "decision_id",
                "task_id",
                "thread_id",
                "creator_id",
                "production_request_reference",
                "budget_reference",
                "price_snapshot",
                "currency",
                "maximum_approved_amount_micros",
                "maximum_attempts",
                "decided_at",
            ),
            BudgetDecisionOutcome: ("decision", "authorization"),
        }
        for value_type, names in expected_fields.items():
            with self.subTest(value_type=value_type.__name__):
                self.assertEqual(tuple(field.name for field in fields(value_type)), names)
                self.assertTrue(getattr(value_type, "__dataclass_params__").frozen)
                self.assertTrue(hasattr(value_type, "__slots__"))


if __name__ == "__main__":
    unittest.main()
