"""Public repository contract tests for Budget decisions and authorizations."""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
import tempfile
import unittest

from ai_course_factory.artifacts import ArtifactCommitBoundary
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetAuthorizationRepository,
    BudgetDecisionOutcome,
    BudgetFailure,
    BudgetModule,
    PriceLineItem,
    RetryPolicy,
    SQLiteBudgetAuthorizationRepository,
)

from tests.production.test_budget import fixture_snapshot, production_request_parts


def committed_budget():
    request_reference, request = production_request_parts()
    artifacts = ArtifactCommitBoundary()
    candidate = BudgetModule.estimate(
        request_reference,
        request,
        price_snapshot=fixture_snapshot(request_reference),
        retry_policy=RetryPolicy(2),
        budget_identity="budget:contract",
        budget_commit_id="budget-commit:contract",
    )
    budget_reference = artifacts.commit(candidate)
    return request_reference, request, budget_reference, artifacts.get(budget_reference)


def approved_outcome():
    request_reference, request, budget_reference, budget = committed_budget()
    result = BudgetAuthorizationBoundary().decide(
        request_reference,
        request,
        budget_reference,
        budget,
        decision_id="decision:contract",
        authorization_id="authorization:contract",
        task_id="task:contract",
        thread_id="thread:contract",
        creator_id="creator:contract",
        decided_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        action="approve",
        maximum_approved_amount_micros=6_000,
        maximum_attempts=2,
    )
    assert isinstance(result, BudgetDecisionOutcome)
    return result


class BudgetAuthorizationRepositoryContractTests(unittest.TestCase):
    def test_protocol_is_runtime_checkable_for_atomic_budget_outcome_storage(self):
        class InMemoryRepository:
            def save(self, outcome):
                return outcome

            def get_decision(self, decision_id):
                return decision_id

            def get_authorization(self, authorization_id):
                return authorization_id

        self.assertIsInstance(InMemoryRepository(), BudgetAuthorizationRepository)

    def test_sqlite_repository_is_runtime_checkable_and_round_trips_reject(self):
        request_reference, request, budget_reference, budget = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteBudgetAuthorizationRepository(Path(directory) / "budget.sqlite3")
            try:
                self.assertIsInstance(repository, BudgetAuthorizationRepository)
                boundary = BudgetAuthorizationBoundary(repository)
                result = boundary.decide(
                    request_reference, request, budget_reference, budget,
                    decision_id="decision:reject", authorization_id=None,
                    task_id="task:contract", thread_id="thread:contract",
                    creator_id="creator:contract", decided_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
                    action="reject", decision_context="Creator requested a smaller scope.",
                )
                self.assertIsInstance(result, BudgetDecisionOutcome)
                self.assertIsNone(result.authorization)
                self.assertEqual(repository.get_decision("decision:reject"), result.decision)
                self.assertEqual(repository.get_authorization("missing:authorization").code, "AUTHORIZATION_NOT_FOUND")
            finally:
                repository.close()

    def test_default_and_sqlite_boundaries_preserve_replay_conflict_and_get(self):
        request_reference, request, budget_reference, budget = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            repositories = [None, SQLiteBudgetAuthorizationRepository(Path(directory) / "budget.sqlite3")]
            try:
                for repository in repositories:
                    with self.subTest(repository=type(repository).__name__ if repository else "memory"):
                        boundary = BudgetAuthorizationBoundary(repository)
                        result = boundary.decide(
                            request_reference, request, budget_reference, budget,
                            decision_id="decision:replay", authorization_id="authorization:replay",
                            task_id="task:contract", thread_id="thread:contract", creator_id="creator:contract",
                            decided_at=datetime(2026, 8, 12, tzinfo=timezone.utc), action="approve",
                            maximum_approved_amount_micros=6_000, maximum_attempts=2,
                        )
                        self.assertIsInstance(result, BudgetDecisionOutcome)
                        replay = boundary.decide(
                            request_reference, request, budget_reference, budget,
                            decision_id="decision:replay", authorization_id="authorization:replay",
                            task_id="task:contract", thread_id="thread:contract", creator_id="creator:contract",
                            decided_at=datetime(2026, 8, 12, tzinfo=timezone.utc), action="approve",
                            maximum_approved_amount_micros=6_000, maximum_attempts=2,
                        )
                        self.assertEqual(replay, result)
                        conflict = boundary.decide(
                            request_reference, request, budget_reference, budget,
                            decision_id="decision:replay", authorization_id="authorization:replay",
                            task_id="task:contract", thread_id="thread:contract", creator_id="creator:contract",
                            decided_at=datetime(2026, 8, 12, tzinfo=timezone.utc), action="approve",
                            maximum_approved_amount_micros=7_000, maximum_attempts=2,
                        )
                        self.assertIsInstance(conflict, BudgetFailure)
                        self.assertEqual(conflict.code, "DECISION_CONFLICT")
                        self.assertEqual(boundary.get_decision("decision:replay"), result.decision)
            finally:
                repositories[1].close()

    def test_direct_save_rejects_forged_outcomes_without_mutation(self):
        outcome = approved_outcome()
        reversed_snapshot = replace(
            outcome.authorization.price_snapshot,
            line_items=tuple(reversed(outcome.authorization.price_snapshot.line_items)),
        )
        def approved_variant(decision_id, authorization_id):
            return replace(
                outcome,
                decision=replace(
                    outcome.decision,
                    decision_id=decision_id,
                    authorization_id=authorization_id,
                ),
                authorization=replace(
                    outcome.authorization,
                    decision_id=decision_id,
                    authorization_id=authorization_id,
                ),
            )

        bad_line_items = list(outcome.authorization.price_snapshot.line_items)
        bad_line_items[0] = replace(bad_line_items[0], unit_price_micros=True)
        bad_currency = approved_variant("decision:forged-currency", "authorization:forged-currency")
        bad_currency = replace(
            bad_currency,
            authorization=replace(bad_currency.authorization, currency="EUR"),
        )
        bad_bool = approved_variant("decision:forged-bool", "authorization:forged-bool")
        bad_bool = replace(
            bad_bool,
            decision=replace(bad_bool.decision, maximum_attempts=True),
            authorization=replace(bad_bool.authorization, maximum_attempts=True),
        )
        bad_line_item = approved_variant("decision:forged-line-item", "authorization:forged-line-item")
        bad_line_item = replace(
            bad_line_item,
            authorization=replace(
                bad_line_item.authorization,
                price_snapshot=replace(
                    bad_line_item.authorization.price_snapshot,
                    line_items=tuple(bad_line_items),
                ),
            ),
        )
        bad_too_many = approved_variant("decision:forged-too-many", "authorization:forged-too-many")
        bad_too_many = replace(
            bad_too_many,
            decision=replace(bad_too_many.decision, maximum_attempts=4),
            authorization=replace(bad_too_many.authorization, maximum_attempts=4),
        )
        bad_reversed = approved_variant("decision:forged-reversed", "authorization:forged-reversed")
        bad_reversed = replace(
            bad_reversed,
            authorization=replace(
                bad_reversed.authorization,
                price_snapshot=replace(
                    bad_reversed.authorization.price_snapshot,
                    line_items=reversed_snapshot.line_items,
                ),
            ),
        )
        malformed = (
            (
                replace(
                    outcome,
                    decision=replace(
                        outcome.decision,
                        decision_id="decision:forged-reject",
                        action="reject",
                        authorization_id=None,
                        maximum_approved_amount_micros=None,
                        maximum_attempts=None,
                        decision_context="Creator requested a smaller scope.",
                    ),
                ),
                "INVALID_BUDGET_OUTCOME",
            ),
            (bad_currency, "INVALID_AUTHORIZATION_RECORD"),
            (bad_bool, "INVALID_MAXIMUM_ATTEMPTS"),
            (bad_line_item, "INVALID_PRICE_LINE_ITEM"),
            (bad_too_many, "INVALID_MAXIMUM_ATTEMPTS"),
            (bad_reversed, "INVALID_PRICE_SNAPSHOT_COVERAGE"),
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteBudgetAuthorizationRepository(Path(directory) / "budget.sqlite3")
            try:
                for forged, expected_code in malformed:
                    result = repository.save(forged)
                    self.assertIsInstance(result, BudgetFailure)
                    self.assertEqual(result.code, expected_code)
                    self.assertIsInstance(repository.get_decision(forged.decision.decision_id), BudgetFailure)
            finally:
                repository.close()

    def test_request_ordered_nonlex_snapshot_is_accepted_but_oversized_is_rejected(self):
        outcome = approved_outcome()
        items = tuple(
            PriceLineItem(scene_id, operation, "per_scene", 1, 1)
            for scene_id in ("scene-z", "scene-a")
            for operation in ("visual", "voice")
        )
        ordered = replace(
            outcome,
            decision=replace(
                outcome.decision,
                decision_id="decision:nonlex",
                authorization_id="authorization:nonlex",
            ),
            authorization=replace(
                outcome.authorization,
                authorization_id="authorization:nonlex",
                decision_id="decision:nonlex",
                price_snapshot=replace(outcome.authorization.price_snapshot, line_items=items),
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteBudgetAuthorizationRepository(Path(directory) / "budget.sqlite3")
            try:
                self.assertEqual(repository.save(ordered), ordered)
                huge = tuple(
                    PriceLineItem(f"s{index}", operation, "u" * 128, 1, 1)
                    for index in range(300)
                    for operation in ("visual", "voice")
                )
                oversized = replace(
                    outcome,
                    decision=replace(
                        outcome.decision,
                        decision_id="decision:oversized",
                        authorization_id="authorization:oversized",
                    ),
                    authorization=replace(
                        outcome.authorization,
                        authorization_id="authorization:oversized",
                        decision_id="decision:oversized",
                        price_snapshot=replace(outcome.authorization.price_snapshot, line_items=huge),
                    ),
                )
                result = repository.save(oversized)
                self.assertIsInstance(result, BudgetFailure)
                self.assertIsInstance(repository.get_decision("decision:oversized"), BudgetFailure)
            finally:
                repository.close()

    def test_boundary_rejects_mismatched_repository_success_before_observing_approval(self):
        outcome = approved_outcome()

        class MismatchedRepository:
            def save(self, requested):
                return replace(requested, decision=replace(requested.decision, decision_id="other"))

            def get_decision(self, decision_id):
                return BudgetFailure("validation", "DECISION_NOT_FOUND", "decision record does not exist")

            def get_authorization(self, authorization_id):
                return BudgetFailure("validation", "AUTHORIZATION_NOT_FOUND", "authorization record does not exist")

        request_reference, request, budget_reference, budget = committed_budget()
        result = BudgetAuthorizationBoundary(MismatchedRepository()).decide(
            request_reference, request, budget_reference, budget,
            decision_id=outcome.decision.decision_id, authorization_id=outcome.authorization.authorization_id,
            task_id=outcome.decision.task_id, thread_id=outcome.decision.thread_id,
            creator_id=outcome.decision.creator_id, decided_at=outcome.decision.decided_at,
            action="approve", maximum_approved_amount_micros=6_000, maximum_attempts=2,
        )
        self.assertIsInstance(result, BudgetFailure)
        self.assertEqual(result.kind, "execution")
        self.assertEqual(result.code, "BUDGET_AUTHORIZATION_FAILED")


if __name__ == "__main__":
    unittest.main()
