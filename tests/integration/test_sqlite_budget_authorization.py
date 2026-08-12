"""Durable Budget decision and Authorization integration evidence."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
import sqlite3
import tempfile
from pathlib import Path
from threading import Barrier
import unittest

from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetAuthorizationRecord,
    BudgetDecisionOutcome,
    BudgetFailure,
    SQLiteBudgetAuthorizationRepository,
)

from tests.integration import test_budget_authorization


def committed_budget():
    return test_budget_authorization.BudgetAuthorizationIntegrationTests()._committed_budget()


class SQLiteBudgetAuthorizationIntegrationTests(unittest.TestCase):
    def _approve(self, repository, values, decision_id="decision:integration", authorization_id="authorization:integration"):
        _artifacts, request_reference, request, budget_reference, budget = values
        return BudgetAuthorizationBoundary(repository).decide(
            request_reference, request, budget_reference, budget,
            decision_id=decision_id, authorization_id=authorization_id,
            task_id="task:integration", thread_id="thread:integration", creator_id="creator:integration",
            decided_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc), action="approve",
            maximum_approved_amount_micros=6_000, maximum_attempts=2,
        )

    def test_close_reopen_preserves_approval_replay_conflict_and_rejection(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "budget.sqlite3"
            repository = SQLiteBudgetAuthorizationRepository(database)
            approved = self._approve(repository, values)
            self.assertIsInstance(approved, BudgetDecisionOutcome)
            _artifacts, request_reference, request, budget_reference, budget = values
            rejected = BudgetAuthorizationBoundary(repository).decide(
                request_reference, request, budget_reference, budget,
                decision_id="decision:reject", authorization_id=None,
                task_id="task:integration", thread_id="thread:integration", creator_id="creator:integration",
                decided_at=datetime(2026, 8, 12, 12, 1, tzinfo=timezone.utc), action="reject",
                decision_context="Creator requested a smaller scope.",
            )
            self.assertIsInstance(rejected, BudgetDecisionOutcome)
            repository.close()

            reopened = SQLiteBudgetAuthorizationRepository(database)
            try:
                boundary = BudgetAuthorizationBoundary(reopened)
                self.assertEqual(boundary.get_decision("decision:integration"), approved.decision)
                self.assertEqual(boundary.get_authorization("authorization:integration"), approved.authorization)
                self.assertEqual(boundary.get_decision("decision:reject"), rejected.decision)
                self.assertEqual(boundary.get_authorization("missing:authorization").code, "AUTHORIZATION_NOT_FOUND")
                self.assertEqual(self._approve(reopened, values), approved)
                conflict = self._approve(reopened, values, authorization_id="authorization:integration")
                self.assertEqual(conflict, approved)
                changed = BudgetAuthorizationBoundary(reopened).decide(
                    request_reference, request, budget_reference, budget,
                    decision_id="decision:integration", authorization_id="authorization:integration",
                    task_id="task:integration", thread_id="thread:integration", creator_id="creator:integration",
                    decided_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc), action="approve",
                    maximum_approved_amount_micros=7_000, maximum_attempts=2,
                )
                self.assertIsInstance(changed, BudgetFailure)
                self.assertEqual(changed.code, "DECISION_CONFLICT")
                reused = self._approve(reopened, values, decision_id="decision:other")
                self.assertIsInstance(reused, BudgetFailure)
                self.assertEqual(reused.code, "AUTHORIZATION_CONFLICT")
                self.assertEqual(boundary.get_decision("decision:other").code, "DECISION_NOT_FOUND")
            finally:
                reopened.close()

    def test_approve_dual_write_rolls_back_when_authorization_insert_fails(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteBudgetAuthorizationRepository(Path(directory) / "budget.sqlite3")
            try:
                repository._connection.execute(
                    """
                    CREATE TRIGGER fail_budget_authorization
                    BEFORE INSERT ON budget_authorizations
                    BEGIN SELECT RAISE(ABORT, 'forced authorization failure'); END
                    """
                )
                repository._connection.commit()
                result = self._approve(repository, values, "decision:atomic", "authorization:atomic")
                self.assertIsInstance(result, BudgetFailure)
                self.assertEqual(result.kind, "execution")
                self.assertEqual(result.code, "BUDGET_AUTHORIZATION_FAILED")
                self.assertEqual(repository.get_decision("decision:atomic").code, "DECISION_NOT_FOUND")
                self.assertEqual(repository.get_authorization("authorization:atomic").code, "AUTHORIZATION_NOT_FOUND")
            finally:
                repository.close()

    def test_two_open_instances_share_replay_conflicts_and_preserve_original(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "budget.sqlite3"
            first = SQLiteBudgetAuthorizationRepository(database)
            second = SQLiteBudgetAuthorizationRepository(database)
            try:
                outcome = self._approve(first, values, "decision:two-open", "authorization:two-open")
                self.assertIsInstance(outcome, BudgetDecisionOutcome)
                self.assertEqual(second.get_decision("decision:two-open"), outcome.decision)
                self.assertEqual(self._approve(second, values, "decision:two-open", "authorization:two-open"), outcome)
                conflict = BudgetAuthorizationBoundary(second).decide(
                    values[1], values[2], values[3], values[4],
                    decision_id="decision:two-open", authorization_id="authorization:two-open",
                    task_id="task:integration", thread_id="thread:integration", creator_id="creator:integration",
                    decided_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc), action="approve",
                    maximum_approved_amount_micros=7_000, maximum_attempts=2,
                )
                self.assertIsInstance(conflict, BudgetFailure)
                self.assertEqual(conflict.code, "DECISION_CONFLICT")
                self.assertEqual(first.get_authorization("authorization:two-open"), outcome.authorization)
            finally:
                first.close()
                second.close()

    def test_concurrent_two_instance_approval_has_one_winner_and_one_conflict(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "budget.sqlite3"
            for index in range(10):
                barrier = Barrier(2)
                decision_id = f"decision:race:{index}"
                authorization_id = f"authorization:race:{index}"

                def attempt(amount):
                    repository = SQLiteBudgetAuthorizationRepository(database)
                    try:
                        barrier.wait(timeout=5)
                        return self._approve(
                            repository,
                            values,
                            decision_id=decision_id,
                            authorization_id=authorization_id,
                        ) if amount == 6_000 else BudgetAuthorizationBoundary(repository).decide(
                            values[1], values[2], values[3], values[4],
                            decision_id=decision_id, authorization_id=authorization_id,
                            task_id="task:integration", thread_id="thread:integration", creator_id="creator:integration",
                            decided_at=datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc), action="approve",
                            maximum_approved_amount_micros=amount, maximum_attempts=2,
                        )
                    finally:
                        repository.close()

                with ThreadPoolExecutor(max_workers=2) as executor:
                    results = list(executor.map(attempt, (6_000, 7_000)))
                winners = [result for result in results if isinstance(result, BudgetDecisionOutcome)]
                conflicts = [result for result in results if isinstance(result, BudgetFailure) and result.code == "DECISION_CONFLICT"]
                self.assertEqual(len(winners), 1)
                self.assertEqual(len(conflicts), 1)
                repository = SQLiteBudgetAuthorizationRepository(database)
                try:
                    self.assertEqual(repository.get_decision(decision_id), winners[0].decision)
                    self.assertEqual(repository.get_authorization(authorization_id), winners[0].authorization)
                finally:
                    repository.close()

    def test_corrupt_rows_future_schema_and_closed_lifecycle_fail_safely(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "budget.sqlite3"
            repository = SQLiteBudgetAuthorizationRepository(database)
            self.assertIsInstance(self._approve(repository, values), BudgetDecisionOutcome)
            repository.close()
            self.assertEqual(repository.get_decision("decision:integration").code, "BUDGET_AUTHORIZATION_FAILED")

            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE budget_authorizations SET snapshot_line_items_json = ? WHERE authorization_id = ?",
                    ("{bad-json}", "authorization:integration"),
                )
                connection.commit()
            corrupted = SQLiteBudgetAuthorizationRepository(database)
            try:
                result = corrupted.get_authorization("authorization:integration")
                self.assertIsInstance(result, BudgetFailure)
                self.assertEqual(result.kind, "execution")
                self.assertEqual(result.code, "BUDGET_AUTHORIZATION_FAILED")
                self.assertNotIn("bad-json", result.message)
            finally:
                corrupted.close()

            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE budget_authorizations SET snapshot_line_items_json = ? WHERE authorization_id = ?",
                    (
                        '[{"scene_id":"scene-1","operation":"visual","unit":"per_scene","quantity":true,"unit_price_micros":1000}]',
                        "authorization:integration",
                    ),
                )
                connection.commit()
            malformed_json = SQLiteBudgetAuthorizationRepository(database)
            try:
                result = malformed_json.get_authorization("authorization:integration")
                self.assertIsInstance(result, BudgetFailure)
                self.assertEqual(result.code, "BUDGET_AUTHORIZATION_FAILED")
            finally:
                malformed_json.close()

            future = Path(directory) / "future.sqlite3"
            with sqlite3.connect(future) as connection:
                connection.execute("CREATE TABLE budget_authorization_schema (singleton INTEGER PRIMARY KEY, version INTEGER NOT NULL)")
                connection.execute("INSERT INTO budget_authorization_schema VALUES (1, 999)")
                connection.commit()
            unsupported = SQLiteBudgetAuthorizationRepository(future)
            try:
                failure = unsupported.get_decision("anything")
                self.assertIsInstance(failure, BudgetFailure)
                self.assertEqual(failure.code, "BUDGET_AUTHORIZATION_FAILED")
            finally:
                unsupported.close()

            unopened = SQLiteBudgetAuthorizationRepository(Path(directory) / "missing" / "budget.sqlite3")
            self.assertEqual(unopened.get_decision("anything").code, "BUDGET_AUTHORIZATION_FAILED")
            unopened.close()

    def test_direct_cross_record_mismatch_and_invalid_integer_never_mutate(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteBudgetAuthorizationRepository(Path(directory) / "budget.sqlite3")
            try:
                valid = self._approve(repository, values, "decision:direct", "authorization:direct")
                self.assertIsInstance(valid, BudgetDecisionOutcome)
                repository.close()
                repository = SQLiteBudgetAuthorizationRepository(Path(directory) / "budget.sqlite3")
                forged = replace(
                    valid,
                    authorization=replace(valid.authorization, decision_id="different-decision"),
                )
                mismatch = repository.save(forged)
                self.assertIsInstance(mismatch, BudgetFailure)
                self.assertEqual(mismatch.code, "BUDGET_OUTCOME_MISMATCH")
                bad_int = replace(
                    valid,
                    decision=replace(
                        valid.decision,
                        decision_id="decision:bad-int",
                        authorization_id="authorization:bad-int",
                        maximum_attempts=True,
                    ),
                    authorization=replace(
                        valid.authorization,
                        decision_id="decision:bad-int",
                        authorization_id="authorization:bad-int",
                        maximum_attempts=True,
                    ),
                )
                invalid = repository.save(bad_int)
                self.assertIsInstance(invalid, BudgetFailure)
                self.assertEqual(invalid.code, "INVALID_MAXIMUM_ATTEMPTS")
                self.assertEqual(repository.get_decision("decision:bad-int").code, "DECISION_NOT_FOUND")
            finally:
                repository.close()

    def test_valid_persisted_pair_mismatch_fails_both_lookup_directions_safely(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "budget.sqlite3"
            repository = SQLiteBudgetAuthorizationRepository(database)
            try:
                self.assertIsInstance(self._approve(repository, values), BudgetDecisionOutcome)
            finally:
                repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE budget_decisions SET creator_id = ? WHERE decision_id = ?",
                    ("another-valid-creator", "decision:integration"),
                )
                connection.commit()
            corrupted = SQLiteBudgetAuthorizationRepository(database)
            try:
                decision = corrupted.get_decision("decision:integration")
                authorization = corrupted.get_authorization("authorization:integration")
                self.assertIsInstance(decision, BudgetFailure)
                self.assertIsInstance(authorization, BudgetFailure)
                self.assertEqual(decision.code, "BUDGET_AUTHORIZATION_FAILED")
                self.assertEqual(authorization.code, "BUDGET_AUTHORIZATION_FAILED")
                self.assertNotIn("another-valid-creator", decision.message)
                self.assertNotIn("another-valid-creator", authorization.message)
            finally:
                corrupted.close()

    def test_corrupt_pair_replay_fails_storage_before_conflict_classification(self):
        values = committed_budget()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "budget.sqlite3"
            repository = SQLiteBudgetAuthorizationRepository(database)
            try:
                original = self._approve(repository, values)
            finally:
                repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE budget_decisions SET creator_id = ? WHERE decision_id = ?",
                    ("replay-corrupted", "decision:integration"),
                )
                connection.commit()
            corrupted = SQLiteBudgetAuthorizationRepository(database)
            try:
                result = corrupted.save(original)
                self.assertIsInstance(result, BudgetFailure)
                self.assertEqual(result.kind, "execution")
                self.assertEqual(result.code, "BUDGET_AUTHORIZATION_FAILED")
                self.assertNotIn("replay-corrupted", result.message)
            finally:
                corrupted.close()


if __name__ == "__main__":
    unittest.main()
