"""Durable Storyboard decision recovery and downstream integration evidence."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ai_course_factory.agents import ProductionAgent, ProductionAgentFailure
from ai_course_factory.artifacts import (
    StoryboardDecisionBoundary,
    StoryboardDecisionFailure,
    StoryboardDecisionRecord,
    SQLiteStoryboardDecisionRepository,
)

from tests.integration import test_timeline_planning


class MismatchedSuccessRepository:
    """Mutation seam: report a different successful record than requested."""

    def save(self, record):
        return replace(record, decision_id="different-decision")

    def get(self, decision_id):
        return StoryboardDecisionFailure(
            "validation", "DECISION_NOT_FOUND", "decision record does not exist"
        )


class SQLiteStoryboardDecisionRepositoryIntegrationTests(unittest.TestCase):
    @staticmethod
    def _committed_storyboard():
        return test_timeline_planning.TimelinePlanningIntegrationTests()._committed_storyboard()

    @staticmethod
    def _save_approved(repository, values, decision_id="storyboard-approve-1"):
        (
            _artifact_boundary,
            _script_reference,
            _script_version,
            _script_decision,
            _character_reference,
            _character_version,
            storyboard_reference,
            storyboard_version,
            _existing_decision,
            _runtime,
        ) = values
        return StoryboardDecisionBoundary(repository).decide(
            storyboard_reference,
            storyboard_version,
            review_enabled=True,
            decision_id=decision_id,
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )

    def test_close_reopen_preserves_exact_record_and_conflict_semantics(self):
        values = self._committed_storyboard()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            first_repository = SQLiteStoryboardDecisionRepository(database)
            record = self._save_approved(first_repository, values, "decision-restart-1")
            self.assertIsInstance(record, StoryboardDecisionRecord)
            first_repository.close()

            reopened_repository = SQLiteStoryboardDecisionRepository(database)
            try:
                boundary = StoryboardDecisionBoundary(reopened_repository)
                restored = boundary.get("decision-restart-1")
                self.assertEqual(restored, record)
                replay = self._save_approved(reopened_repository, values, "decision-restart-1")
                self.assertEqual(replay, record)
                conflict = StoryboardDecisionBoundary(reopened_repository).decide(
                    values[6],
                    values[7],
                    review_enabled=True,
                    decision_id="decision-restart-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="revise",
                    decision_context="Use a different revision instruction.",
                )
                self.assertIsInstance(conflict, StoryboardDecisionFailure)
                self.assertEqual(conflict.code, "DECISION_CONFLICT")
                self.assertEqual(boundary.get("decision-restart-1"), record)
            finally:
                reopened_repository.close()

    def test_two_open_instances_observe_replay_and_preserve_immutable_identity(self):
        values = self._committed_storyboard()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            first_repository = SQLiteStoryboardDecisionRepository(database)
            second_repository = SQLiteStoryboardDecisionRepository(database)
            try:
                first = self._save_approved(first_repository, values, "decision-two-open-1")
                self.assertIsInstance(first, StoryboardDecisionRecord)
                second_boundary = StoryboardDecisionBoundary(second_repository)
                self.assertEqual(second_boundary.get("decision-two-open-1"), first)
                replay = self._save_approved(second_repository, values, "decision-two-open-1")
                self.assertEqual(replay, first)
                conflict = second_boundary.decide(
                    values[6],
                    values[7],
                    review_enabled=True,
                    decision_id="decision-two-open-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="reject",
                    decision_context="Reject this exact Storyboard version.",
                )
                self.assertIsInstance(conflict, StoryboardDecisionFailure)
                self.assertEqual(conflict.code, "DECISION_CONFLICT")
                self.assertEqual(first_repository.get("decision-two-open-1"), first)
            finally:
                first_repository.close()
                second_repository.close()

    def test_restored_approved_decision_reaches_existing_timeline_behavior(self):
        values = self._committed_storyboard()
        (
            _artifact_boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            _existing_decision,
            runtime,
        ) = values
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteStoryboardDecisionRepository(database)
            decision = self._save_approved(repository, values, "decision-downstream-1")
            self.assertIsInstance(decision, StoryboardDecisionRecord)
            repository.close()

            reopened = SQLiteStoryboardDecisionRepository(database)
            try:
                restored = StoryboardDecisionBoundary(reopened).get("decision-downstream-1")
                self.assertEqual(restored, decision)
                before = len(runtime.requests)
                candidate = ProductionAgent(runtime).plan_timeline(
                    script_reference,
                    script_version,
                    script_decision,
                    character_reference,
                    character_version,
                    storyboard_reference,
                    storyboard_version,
                    restored,
                    timeline_identity="timeline:restored-storyboard-decision",
                    timeline_commit_id="timeline-commit-restored-storyboard-decision",
                )
                self.assertNotIsInstance(candidate, ProductionAgentFailure)
                self.assertEqual(candidate.payload["storyboard_decision_id"], "decision-downstream-1")
                self.assertEqual(len(runtime.requests), before + 1)
            finally:
                reopened.close()

    def test_failed_or_corrupt_storage_cannot_satisfy_timeline(self):
        values = self._committed_storyboard()
        (
            _artifact_boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            _existing_decision,
            runtime,
        ) = values
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteStoryboardDecisionRepository(database)
            decision = self._save_approved(repository, values, "decision-corrupt-1")
            self.assertIsInstance(decision, StoryboardDecisionRecord)
            repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE storyboard_decisions SET action = ? WHERE decision_id = ?",
                    ("publish", "decision-corrupt-1"),
                )
                connection.commit()

            corrupted_repository = SQLiteStoryboardDecisionRepository(database)
            try:
                corrupted = corrupted_repository.get("decision-corrupt-1")
                self.assertIsInstance(corrupted, StoryboardDecisionFailure)
                self.assertEqual(corrupted.kind, "execution")
                self.assertEqual(corrupted.code, "STORYBOARD_DECISION_FAILED")
                self.assertNotIn("publish", corrupted.message)
                before = len(runtime.requests)
                rejected = ProductionAgent(runtime).plan_timeline(
                    script_reference,
                    script_version,
                    script_decision,
                    character_reference,
                    character_version,
                    storyboard_reference,
                    storyboard_version,
                    corrupted,
                    timeline_identity="timeline:corrupt-storyboard-decision",
                    timeline_commit_id="timeline-commit-corrupt-storyboard-decision",
                )
                self.assertIsInstance(rejected, ProductionAgentFailure)
                self.assertEqual(len(runtime.requests), before)
                self.assertEqual(
                    [request.purpose for request in runtime.requests if request.purpose == "timeline_planning"],
                    [],
                )
            finally:
                corrupted_repository.close()

            closed_repository = SQLiteStoryboardDecisionRepository(database)
            closed_repository.close()
            closed = closed_repository.get("decision-corrupt-1")
            self.assertIsInstance(closed, StoryboardDecisionFailure)
            before = len(runtime.requests)
            rejected = ProductionAgent(runtime).plan_timeline(
                script_reference,
                script_version,
                script_decision,
                character_reference,
                character_version,
                storyboard_reference,
                storyboard_version,
                closed,
                timeline_identity="timeline:closed-storyboard-decision",
                timeline_commit_id="timeline-commit-closed-storyboard-decision",
            )
            self.assertIsInstance(rejected, ProductionAgentFailure)
            self.assertEqual(len(runtime.requests), before)
            self.assertEqual(
                [request.purpose for request in runtime.requests if request.purpose == "timeline_planning"],
                [],
            )

    def test_mismatched_success_record_is_rejected_before_timeline_use(self):
        values = self._committed_storyboard()
        (
            _artifact_boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            _existing_decision,
            runtime,
        ) = values
        boundary = StoryboardDecisionBoundary(MismatchedSuccessRepository())
        result = boundary.decide(
            storyboard_reference,
            storyboard_version,
            review_enabled=True,
            decision_id="decision-mismatch-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(result, StoryboardDecisionFailure)
        self.assertEqual(result.kind, "execution")
        self.assertEqual(result.code, "STORYBOARD_DECISION_FAILED")
        self.assertIsInstance(boundary.get("decision-mismatch-1"), StoryboardDecisionFailure)
        before = len(runtime.requests)
        rejected = ProductionAgent(runtime).plan_timeline(
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            result,
            timeline_identity="timeline:mismatched-storyboard-decision",
            timeline_commit_id="timeline-commit-mismatched-storyboard-decision",
        )
        self.assertIsInstance(rejected, ProductionAgentFailure)
        self.assertEqual(len(runtime.requests), before)
        self.assertEqual(
            [request.purpose for request in runtime.requests if request.purpose == "timeline_planning"],
            [],
        )

    def test_malformed_row_future_schema_and_open_failure_are_safe(self):
        values = self._committed_storyboard()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteStoryboardDecisionRepository(database)
            decision = self._save_approved(repository, values, "decision-schema-1")
            self.assertIsInstance(decision, StoryboardDecisionRecord)
            repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE storyboard_decisions SET review_enabled = ? WHERE decision_id = ?",
                    (3, "decision-schema-1"),
                )
                connection.commit()
            malformed = SQLiteStoryboardDecisionRepository(database)
            try:
                failure = malformed.get("decision-schema-1")
                self.assertIsInstance(failure, StoryboardDecisionFailure)
                self.assertEqual(failure.kind, "execution")
                self.assertEqual(failure.code, "STORYBOARD_DECISION_FAILED")
                self.assertNotIn("sqlite", failure.message.lower())
            finally:
                malformed.close()

            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE storyboard_decision_schema SET version = ? WHERE singleton = 1",
                    (999,),
                )
                connection.commit()
            future = SQLiteStoryboardDecisionRepository(database)
            try:
                failure = future.get("decision-schema-1")
                self.assertIsInstance(failure, StoryboardDecisionFailure)
                self.assertEqual(failure.kind, "execution")
                self.assertEqual(failure.code, "STORYBOARD_DECISION_FAILED")
            finally:
                future.close()

            open_failure = SQLiteStoryboardDecisionRepository(directory)
            try:
                failure = open_failure.get("decision-open-failure")
                self.assertIsInstance(failure, StoryboardDecisionFailure)
                self.assertEqual(failure.kind, "execution")
                self.assertEqual(failure.code, "STORYBOARD_DECISION_FAILED")
                self.assertEqual(failure.message, "storyboard decision persistence failed")
            finally:
                open_failure.close()


if __name__ == "__main__":
    unittest.main()
