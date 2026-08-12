"""Durable Script decision and application-order integration evidence."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ai_course_factory.artifacts import (
    ScriptDecisionBoundary,
    ScriptDecisionFailure,
    ScriptDecisionRecord,
    SQLiteScriptDecisionRepository,
)
from ai_course_factory.application.script_review import ScriptReviewApplicationService
from ai_course_factory.workflow import InMemoryCheckpointAdapter, ScriptReviewWorkflow

from tests.application.test_script_review_service import (
    RecordingWorkflow,
    committed_lineage,
)
from tests.artifacts.test_script_decision import valid_versions


class ResumeCountingWorkflow(ScriptReviewWorkflow):
    """Observe whether an application attempts resume after storage failure."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resume_calls = 0

    def resume(self, command):
        self.resume_calls += 1
        return super().resume(command)


class MismatchedSuccessRepository:
    """Mutation seam: report a different successful record than requested."""

    def save(self, record):
        return replace(record, decision_id="different-decision")

    def get(self, decision_id):
        return ScriptDecisionFailure(
            "validation", "DECISION_NOT_FOUND", "decision record does not exist"
        )


class SQLiteScriptDecisionRepositoryIntegrationTests(unittest.TestCase):
    @staticmethod
    def _assess(boundary: ScriptDecisionBoundary):
        values = valid_versions()
        (
            _,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
            script_reference,
            script_version,
        ) = values
        return boundary.assess(
            script_reference,
            script_version,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
        )

    def test_close_reopen_preserves_exact_record_and_conflict_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            first_repository = SQLiteScriptDecisionRepository(database)
            first_boundary = ScriptDecisionBoundary(first_repository)
            assessment = self._assess(first_boundary)
            record = first_boundary.decide(
                assessment,
                decision_id="decision-restart-1",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="revise",
                decision_context="Ground scene two in the source claim.",
            )
            self.assertIsInstance(record, ScriptDecisionRecord)
            first_repository.close()

            reopened_repository = SQLiteScriptDecisionRepository(database)
            try:
                reopened_boundary = ScriptDecisionBoundary(reopened_repository)
                reopened_assessment = self._assess(reopened_boundary)
                restored = reopened_boundary.get("decision-restart-1")
                self.assertEqual(restored, record)
                replay = reopened_boundary.decide(
                    reopened_assessment,
                    decision_id="decision-restart-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="revise",
                    decision_context="Ground scene two in the source claim.",
                )
                self.assertEqual(replay, record)
                self.assertIsNot(replay, record)
                conflict = reopened_boundary.decide(
                    reopened_assessment,
                    decision_id="decision-restart-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="revise",
                    decision_context="Use a different revision instruction.",
                )
                self.assertIsInstance(conflict, ScriptDecisionFailure)
                self.assertEqual(conflict.code, "DECISION_CONFLICT")
                self.assertEqual(reopened_boundary.get("decision-restart-1"), record)
            finally:
                reopened_repository.close()

    def test_two_open_instances_observe_idempotency_and_conflicts(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            first_repository = SQLiteScriptDecisionRepository(database)
            second_repository = SQLiteScriptDecisionRepository(database)
            try:
                first_boundary = ScriptDecisionBoundary(first_repository)
                second_boundary = ScriptDecisionBoundary(second_repository)
                first_assessment = self._assess(first_boundary)
                second_assessment = self._assess(second_boundary)
                first = first_boundary.decide(
                    first_assessment,
                    decision_id="decision-two-open-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="approve",
                )
                self.assertIsInstance(first, ScriptDecisionRecord)
                self.assertEqual(second_boundary.get("decision-two-open-1"), first)
                replay = second_boundary.decide(
                    second_assessment,
                    decision_id="decision-two-open-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="approve",
                )
                self.assertEqual(replay, first)
                conflict = second_boundary.decide(
                    second_assessment,
                    decision_id="decision-two-open-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="reject",
                    decision_context="Reject this exact Script version.",
                )
                self.assertIsInstance(conflict, ScriptDecisionFailure)
                self.assertEqual(conflict.code, "DECISION_CONFLICT")
                self.assertEqual(first_repository.get("decision-two-open-1"), first)
            finally:
                first_repository.close()
                second_repository.close()

    def test_application_persists_before_resume_and_replays_after_repository_restart(self):
        store, _, _, _, script_reference = committed_lineage()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteScriptDecisionRepository(database)
            decisions = ScriptDecisionBoundary(repository)
            checkpoints = InMemoryCheckpointAdapter()
            workflow = RecordingWorkflow(
                store,
                checkpoints,
                decision_boundary=decisions,
            )
            service = ScriptReviewApplicationService(store, decisions, workflow)
            try:
                started = service.start("task-1", "thread-order", script_reference)
                self.assertEqual(started.status, "pending")
                result = service.decide(
                    "task-1",
                    "thread-order",
                    "decision-order-1",
                    "creator-1",
                    "revise",
                    script_reference,
                    decision_context="Make scene two more concrete.",
                )
                self.assertEqual(result.status, "success")
                self.assertEqual(workflow.observed_decision, result.decision_record)
                self.assertIsInstance(result.decision_record, ScriptDecisionRecord)
            finally:
                repository.close()

            reopened = SQLiteScriptDecisionRepository(database)
            try:
                restarted_decisions = ScriptDecisionBoundary(reopened)
                restarted_service = ScriptReviewApplicationService(
                    store,
                    restarted_decisions,
                    ScriptReviewWorkflow(store, checkpoints),
                )
                replay = restarted_service.decide(
                    "task-1",
                    "thread-order",
                    "decision-order-1",
                    "creator-1",
                    "revise",
                    script_reference,
                    decision_context="Make scene two more concrete.",
                )
                self.assertEqual(replay.status, "success")
                self.assertEqual(replay.decision_record, result.decision_record)
                self.assertEqual(
                    restarted_decisions.get("decision-order-1"),
                    result.decision_record,
                )
            finally:
                reopened.close()

    def test_storage_failure_leaves_script_review_checkpoint_pending(self):
        store, _, _, _, script_reference = committed_lineage()
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteScriptDecisionRepository(Path(directory) / "decisions.sqlite3")
            decisions = ScriptDecisionBoundary(repository)
            checkpoints = InMemoryCheckpointAdapter()
            workflow = ResumeCountingWorkflow(store, checkpoints)
            service = ScriptReviewApplicationService(store, decisions, workflow)
            try:
                started = service.start("task-1", "thread-failure", script_reference)
                self.assertEqual(started.status, "pending")
                repository.close()
                result = service.decide(
                    "task-1",
                    "thread-failure",
                    "decision-failure-1",
                    "creator-1",
                    "approve",
                    script_reference,
                )
                self.assertEqual(result.status, "failure")
                self.assertEqual(result.error_code, "SCRIPT_DECISION_FAILED")
                self.assertEqual(workflow.resume_calls, 0)
                self.assertEqual(
                    workflow.snapshot("thread-failure").pending_gate,
                    "script_review",
                )
            finally:
                repository.close()

    def test_mismatched_success_record_fails_before_workflow_resume(self):
        store, _, _, _, script_reference = committed_lineage()
        decisions = ScriptDecisionBoundary(MismatchedSuccessRepository())
        checkpoints = InMemoryCheckpointAdapter()
        workflow = ResumeCountingWorkflow(store, checkpoints)
        service = ScriptReviewApplicationService(store, decisions, workflow)

        started = service.start("task-1", "thread-mismatch", script_reference)
        self.assertEqual(started.status, "pending")
        result = service.decide(
            "task-1",
            "thread-mismatch",
            "decision-mismatch-1",
            "creator-1",
            "approve",
            script_reference,
        )

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error_code, "SCRIPT_DECISION_FAILED")
        self.assertEqual(workflow.resume_calls, 0)
        self.assertEqual(
            workflow.snapshot("thread-mismatch").pending_gate,
            "script_review",
        )

    def test_malformed_row_future_schema_and_closed_lifecycle_fail_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteScriptDecisionRepository(database)
            boundary = ScriptDecisionBoundary(repository)
            assessment = self._assess(boundary)
            record = boundary.decide(
                assessment,
                decision_id="decision-corrupt-1",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="approve",
            )
            self.assertIsInstance(record, ScriptDecisionRecord)
            repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE script_decisions SET action = ? WHERE decision_id = ?",
                    ("publish", "decision-corrupt-1"),
                )
                connection.commit()
            reopened = SQLiteScriptDecisionRepository(database)
            try:
                malformed = reopened.get("decision-corrupt-1")
                self.assertIsInstance(malformed, ScriptDecisionFailure)
                self.assertEqual(malformed.kind, "execution")
                self.assertEqual(malformed.code, "SCRIPT_DECISION_FAILED")
                self.assertNotIn("publish", malformed.message)
                self.assertNotIn("sqlite", malformed.message.lower())
            finally:
                reopened.close()

            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE script_decision_schema SET version = ? WHERE singleton = 1",
                    (999,),
                )
                connection.commit()
            future = SQLiteScriptDecisionRepository(database)
            try:
                failure = future.get("decision-corrupt-1")
                self.assertIsInstance(failure, ScriptDecisionFailure)
                self.assertEqual(failure.kind, "execution")
                self.assertEqual(failure.code, "SCRIPT_DECISION_FAILED")
            finally:
                future.close()

    def test_sqlite_open_failure_returns_safe_execution_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteScriptDecisionRepository(directory)
            try:
                failure = repository.get("decision-open-failure")
                self.assertIsInstance(failure, ScriptDecisionFailure)
                self.assertEqual(failure.kind, "execution")
                self.assertEqual(failure.code, "SCRIPT_DECISION_FAILED")
                self.assertEqual(failure.message, "script decision persistence failed")
            finally:
                repository.close()


if __name__ == "__main__":
    unittest.main()
