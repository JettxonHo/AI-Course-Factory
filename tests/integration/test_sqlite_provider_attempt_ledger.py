"""Durable SQLite Provider-attempt ledger integration evidence."""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import sqlite3
import tempfile
from pathlib import Path
from threading import Barrier
import unittest

from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileRecord, WorkspaceFileReference
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetDecisionOutcome,
    BudgetFailure,
    ProviderAttemptFailure,
    ProviderAttemptLedger,
    ProviderAttemptOutcome,
    ProviderAttemptRecord,
    ProviderAttemptReservation,
    SQLiteBudgetAuthorizationRepository,
    SQLiteProviderAttemptRepository,
)

from tests.integration import test_budget_authorization as _budget_fixture


class SQLiteProviderAttemptLedgerIntegrationTests(unittest.TestCase):
    _reserved_at = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)

    def _fixture(self, directory: str, authorization_id: str = "authorization:integration"):
        artifacts, request_reference, request, budget_reference, budget = _budget_fixture.BudgetAuthorizationIntegrationTests()._committed_budget()
        database = Path(directory) / "factory.sqlite3"
        budget_repository = SQLiteBudgetAuthorizationRepository(database)
        decision = BudgetAuthorizationBoundary(budget_repository).decide(
            request_reference, request, budget_reference, budget,
            decision_id=f"decision:{authorization_id}", authorization_id=authorization_id,
            task_id="task:integration", thread_id="thread:integration", creator_id="creator:integration",
            decided_at=self._reserved_at, action="approve", maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(decision, BudgetDecisionOutcome)
        authorization = decision.authorization
        workspace = FilesystemWorkspace(Path(directory) / "workspace")
        self.assertEqual(workspace.prepare("task:integration").task_id, "task:integration")
        request_file = WorkspaceFileReference("task:integration", "provider-records", "request.json")
        self.assertIsInstance(workspace.commit(request_file, b"request"), WorkspaceFileRecord)
        reservation = ProviderAttemptReservation(
            "attempt:integration", "task:integration", authorization_id, "scene-1", "visual", "fake",
            "key:integration", request_file, self._reserved_at,
        )
        return database, budget_repository, authorization, workspace, reservation

    def test_restart_recovers_started_and_terminal_success_with_exact_workspace_refs(self):
        with tempfile.TemporaryDirectory() as directory:
            database, budget_repository, authorization, workspace, reservation = self._fixture(directory)
            attempt_repository = SQLiteProviderAttemptRepository(database)
            ledger = ProviderAttemptLedger(lambda _id: authorization, attempt_repository)
            started = ledger.reserve(reservation)
            self.assertIsInstance(started, ProviderAttemptRecord)
            attempt_repository.close(); budget_repository.close()

            reopened_budget = SQLiteBudgetAuthorizationRepository(database)
            reopened_attempt = SQLiteProviderAttemptRepository(database)
            try:
                recovered = ProviderAttemptLedger(reopened_budget, reopened_attempt)
                self.assertEqual(recovered.get(reservation.attempt_id), started)
                self.assertEqual(recovered.reserve(reservation), started)
                changed = replace(reservation, provider="other-provider")
                self.assertEqual(recovered.reserve(changed).code, "ATTEMPT_CONFLICT")
                reused_key = replace(reservation, attempt_id="attempt:reused-key", request_record_reference=WorkspaceFileReference("task:integration", "provider-records", "reused-key.json"))
                self.assertEqual(recovered.reserve(reused_key).code, "IDEMPOTENCY_CONFLICT")

                retry_one = replace(reservation, attempt_id="attempt:retry:1", idempotency_key="key:retry:1", scene_id="scene-2", request_record_reference=WorkspaceFileReference("task:integration", "provider-records", "retry-1.json"))
                retry_one_started = recovered.reserve(retry_one)
                self.assertIsInstance(retry_one_started, ProviderAttemptRecord)
                retry_one_failed = recovered.complete(ProviderAttemptOutcome("attempt:retry:1", "failed", self._reserved_at + timedelta(seconds=1), 0, "TIMEOUT", None, ()))
                self.assertIsInstance(retry_one_failed, ProviderAttemptRecord)
                retry_two = replace(retry_one, attempt_id="attempt:retry:2", idempotency_key="key:retry:2", request_record_reference=WorkspaceFileReference("task:integration", "provider-records", "retry-2.json"))
                retry_two_started = recovered.reserve(retry_two)
                self.assertIsInstance(retry_two_started, ProviderAttemptRecord)
                retry_two_failed = recovered.complete(ProviderAttemptOutcome("attempt:retry:2", "failed", self._reserved_at + timedelta(seconds=2), 0, "TIMEOUT", None, ()))
                self.assertIsInstance(retry_two_failed, ProviderAttemptRecord)
                before_block = recovered.list_for_authorization(reservation.authorization_id)
                retry_three = replace(retry_one, attempt_id="attempt:retry:3", idempotency_key="key:retry:3", request_record_reference=WorkspaceFileReference("task:integration", "provider-records", "retry-3.json"))
                self.assertEqual(recovered.reserve(retry_three).code, "ATTEMPT_LIMIT")
                self.assertEqual(recovered.list_for_authorization(reservation.authorization_id), before_block)
                response = WorkspaceFileReference("task:integration", "provider-records", "response.json")
                output = WorkspaceFileReference("task:integration", "media", "scene-1.mp4")
                workspace.commit(response, b"response")
                workspace.commit(output, b"media")
                outcome = ProviderAttemptOutcome(
                    reservation.attempt_id, "succeeded", self._reserved_at + timedelta(seconds=1),
                    1_000, "SUCCESS", response, (output,),
                )
                terminal = recovered.complete(outcome)
                self.assertIsInstance(terminal, ProviderAttemptRecord)
            finally:
                reopened_attempt.close(); reopened_budget.close()

            final_attempt = SQLiteProviderAttemptRepository(database)
            try:
                self.assertEqual(final_attempt.get(reservation.attempt_id), terminal)
                self.assertEqual(final_attempt.list_for_authorization(reservation.authorization_id), (terminal, retry_one_failed, retry_two_failed))
            finally:
                final_attempt.close()

    def test_two_sqlite_instances_serialize_same_scope_reservations(self):
        with tempfile.TemporaryDirectory() as directory:
            database, budget_repository, authorization, _workspace, reservation = self._fixture(directory, "authorization:race")
            first = SQLiteProviderAttemptRepository(database)
            second = SQLiteProviderAttemptRepository(database)
            barrier = Barrier(2)

            def reserve(index):
                barrier.wait(timeout=5)
                attempt = replace(reservation, attempt_id=f"attempt:race:{index}", idempotency_key=f"key:race:{index}", request_record_reference=WorkspaceFileReference("task:integration", "provider-records", f"race-{index}.json"))
                return ProviderAttemptLedger(lambda _id: authorization, first if index == 1 else second).reserve(attempt)

            try:
                with ThreadPoolExecutor(max_workers=2) as executor:
                    results = list(executor.map(reserve, (1, 2)))
                self.assertEqual(len([item for item in results if isinstance(item, ProviderAttemptRecord)]), 1)
                self.assertEqual(len([item for item in results if isinstance(item, ProviderAttemptFailure) and item.code == "ATTEMPT_IN_PROGRESS"]), 1)
                self.assertTrue(any(isinstance(first.get(item), ProviderAttemptRecord) for item in ("attempt:race:1", "attempt:race:2")))
            finally:
                first.close(); second.close(); budget_repository.close()

    def test_atomic_insert_and_update_failures_leave_previous_state_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            database, budget_repository, authorization, _workspace, reservation = self._fixture(directory, "authorization:atomic")
            repository = SQLiteProviderAttemptRepository(database)
            ledger = ProviderAttemptLedger(lambda _id: authorization, repository)
            try:
                repository._connection.execute("CREATE TRIGGER fail_provider_attempt_insert BEFORE INSERT ON provider_attempts BEGIN SELECT RAISE(ABORT, 'forced'); END")
                repository._connection.commit()
                failed_insert = ledger.reserve(reservation)
                self.assertEqual(failed_insert.code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(repository.get(reservation.attempt_id).code, "ATTEMPT_NOT_FOUND")
                repository._connection.execute("DROP TRIGGER fail_provider_attempt_insert")
                repository._connection.commit()
                started = ledger.reserve(reservation)
                self.assertIsInstance(started, ProviderAttemptRecord)
                repository._connection.execute("CREATE TRIGGER fail_provider_attempt_update BEFORE UPDATE ON provider_attempts BEGIN SELECT RAISE(ABORT, 'forced'); END")
                repository._connection.commit()
                outcome = ProviderAttemptOutcome(reservation.attempt_id, "failed", self._reserved_at + timedelta(seconds=1), 0, "TIMEOUT", None, ())
                failed_update = ledger.complete(outcome)
                self.assertEqual(failed_update.code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(repository.get(reservation.attempt_id).status, "started")
            finally:
                repository.close(); budget_repository.close()

    def test_terminal_validation_corruption_future_schema_and_closed_lifecycle_fail_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            broken_directory = Path(directory) / "not-a-database"
            broken_directory.mkdir()
            broken = SQLiteProviderAttemptRepository(broken_directory)
            self.assertEqual(broken.get("attempt:broken").code, "ATTEMPT_STORAGE_FAILED")
            broken.close()
            database, budget_repository, authorization, workspace, reservation = self._fixture(directory, "authorization:safety")
            repository = SQLiteProviderAttemptRepository(database)
            try:
                ledger = ProviderAttemptLedger(lambda _id: authorization, repository)
                started = ledger.reserve(reservation)
                self.assertIsInstance(started, ProviderAttemptRecord)
                output = WorkspaceFileReference("task:integration", "media", "scene-1.mp4")
                bad = ledger.complete(ProviderAttemptOutcome(reservation.attempt_id, "succeeded", self._reserved_at + timedelta(seconds=1), 1_000, "SUCCESS", None, (output, output)))
                self.assertEqual(bad.code, "INVALID_OUTPUT_REFERENCES")
                repository.close()
                self.assertEqual(repository.get(reservation.attempt_id).code, "ATTEMPT_STORAGE_FAILED")
            finally:
                budget_repository.close()

            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE provider_attempts SET attempt_number = 2 WHERE attempt_id = ?", (reservation.attempt_id,))
                connection.commit()
            corrupted = SQLiteProviderAttemptRepository(database)
            try:
                corrupted_ledger = ProviderAttemptLedger(lambda _id: authorization, corrupted)
                self.assertEqual(corrupted.get(reservation.attempt_id).code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(corrupted.list_for_authorization(reservation.authorization_id).code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(corrupted_ledger.reserve(reservation).code, "ATTEMPT_STORAGE_FAILED")
                next_reservation = replace(reservation, attempt_id="attempt:safety:next", idempotency_key="key:safety:next", request_record_reference=WorkspaceFileReference("task:integration", "provider-records", "safety-next.json"))
                self.assertEqual(corrupted_ledger.reserve(next_reservation).code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(corrupted_ledger.complete(ProviderAttemptOutcome(reservation.attempt_id, "failed", self._reserved_at + timedelta(seconds=1), 0, "TIMEOUT", None, ())).code, "ATTEMPT_STORAGE_FAILED")
            finally:
                corrupted.close()
            with sqlite3.connect(database) as connection:
                self.assertEqual(connection.execute("SELECT attempt_number FROM provider_attempts WHERE attempt_id = ?", (reservation.attempt_id,)).fetchone()[0], 2)
                connection.execute("UPDATE provider_attempts SET attempt_number = 1 WHERE attempt_id = ?", (reservation.attempt_id,))
                connection.commit()
            restored_group = SQLiteProviderAttemptRepository(database)
            try:
                self.assertEqual(restored_group.get(reservation.attempt_id), started)
            finally:
                restored_group.close()

            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE provider_attempts SET request_identity = ? WHERE attempt_id = ?", ("request:forged", reservation.attempt_id))
                connection.commit()
            corrupted = SQLiteProviderAttemptRepository(database)
            try:
                result = corrupted.get(reservation.attempt_id)
                self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
            finally:
                corrupted.close()

            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE provider_attempts SET request_identity = ? WHERE attempt_id = ?", (started.production_request_reference.identity, reservation.attempt_id))
                connection.commit()
            restored = SQLiteProviderAttemptRepository(database)
            try:
                self.assertEqual(restored.get(reservation.attempt_id), started)
            finally:
                restored.close()

            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE provider_attempts SET authorization_fingerprint_json = ? WHERE attempt_id = ?", ("{bad}", reservation.attempt_id))
                connection.commit()
            corrupted = SQLiteProviderAttemptRepository(database)
            try:
                result = corrupted.get(reservation.attempt_id)
                self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
            finally:
                corrupted.close()

            future = Path(directory) / "future.sqlite3"
            with sqlite3.connect(future) as connection:
                connection.execute("CREATE TABLE provider_attempt_schema (singleton INTEGER PRIMARY KEY, version INTEGER NOT NULL)")
                connection.execute("INSERT INTO provider_attempt_schema VALUES (1, 999)")
                connection.commit()
            unsupported = SQLiteProviderAttemptRepository(future)
            try:
                self.assertEqual(unsupported.get("anything").code, "ATTEMPT_STORAGE_FAILED")
            finally:
                unsupported.close()

    def test_full_authorization_fingerprint_changed_after_restart_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            database, budget_repository, authorization, _workspace, reservation = self._fixture(directory, "authorization:fingerprint")
            repository = SQLiteProviderAttemptRepository(database)
            try:
                ledger = ProviderAttemptLedger(lambda _id: authorization, repository)
                started = ledger.reserve(reservation)
                self.assertIsInstance(started, ProviderAttemptRecord)
                failed = ledger.complete(ProviderAttemptOutcome(reservation.attempt_id, "failed", self._reserved_at + timedelta(seconds=1), 0, "TIMEOUT", None, ()))
                self.assertIsInstance(failed, ProviderAttemptRecord)
            finally:
                repository.close(); budget_repository.close()
            changed = replace(authorization, creator_id="creator:changed")
            reopened = SQLiteProviderAttemptRepository(database)
            try:
                changed_ledger = ProviderAttemptLedger(lambda _id: changed, reopened)
                result = changed_ledger.reserve(reservation)
                self.assertEqual(result.code, "ATTEMPT_CONFLICT")
                retry = replace(reservation, attempt_id="attempt:fingerprint:retry", idempotency_key="key:fingerprint:retry", request_record_reference=WorkspaceFileReference("task:integration", "provider-records", "fingerprint-retry.json"))
                retry_result = changed_ledger.reserve(retry)
                self.assertEqual(retry_result.code, "ATTEMPT_CONFLICT")
            finally:
                reopened.close()

    def test_oversized_output_json_is_rejected_without_update_or_restart_loss(self):
        with tempfile.TemporaryDirectory() as directory:
            database, budget_repository, authorization, _workspace, reservation = self._fixture(directory, "authorization:json-cap")
            repository = SQLiteProviderAttemptRepository(database)
            try:
                ledger = ProviderAttemptLedger(lambda _id: authorization, repository)
                started = ledger.reserve(reservation)
                self.assertIsInstance(started, ProviderAttemptRecord)
                outputs = tuple(WorkspaceFileReference("task:integration", "media", f"output-{index}-{'x' * 100}.mp4") for index in range(400))
                oversized = ProviderAttemptOutcome(reservation.attempt_id, "succeeded", self._reserved_at + timedelta(seconds=1), 1_000, "SUCCESS", None, outputs)
                result = ledger.complete(oversized)
                self.assertEqual(result.code, "ATTEMPT_STORAGE_FAILED")
                self.assertEqual(repository.get(reservation.attempt_id).status, "started")
            finally:
                repository.close(); budget_repository.close()
            reopened = SQLiteProviderAttemptRepository(database)
            try:
                self.assertEqual(reopened.get(reservation.attempt_id).status, "started")
            finally:
                reopened.close()


if __name__ == "__main__":
    unittest.main()
