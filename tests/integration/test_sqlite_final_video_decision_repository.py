"""Durable Final Video Review decision persistence evidence."""

from __future__ import annotations

import sqlite3
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ai_course_factory.artifacts import (
    FinalVideoDecisionBoundary,
    FinalVideoDecisionFailure,
    FinalVideoDecisionRecord,
    SQLiteFinalVideoDecisionRepository,
)

from tests.artifacts.test_final_video_decision_repository_contract import valid_video_version


class MismatchedSuccessRepository:
    def save(self, record):
        return replace(record, decision_id="different-decision")

    def get(self, decision_id):
        return FinalVideoDecisionFailure(
            "validation", "DECISION_NOT_FOUND", "decision record does not exist"
        )


class EvilString(str):
    def __eq__(self, other):
        return True


class EvilSuccessRepository:
    def save(self, record):
        return replace(record, decision_id=EvilString(record.decision_id))

    def get(self, decision_id):
        return FinalVideoDecisionFailure(
            "validation", "DECISION_NOT_FOUND", "decision record does not exist"
        )


class InvalidGetRepository:
    def __init__(self, record):
        self._record = record

    def save(self, record):
        return record

    def get(self, decision_id):
        return replace(self._record, gate_kind="wrong_gate")


class SQLiteFinalVideoDecisionRepositoryIntegrationTests(unittest.TestCase):
    @staticmethod
    def _assess(boundary: FinalVideoDecisionBoundary):
        reference, version = valid_video_version()
        return boundary.assess(reference, version)

    def test_close_reopen_preserves_exact_record_and_conflict_semantics(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteFinalVideoDecisionRepository(database)
            boundary = FinalVideoDecisionBoundary(repository)
            assessment = self._assess(boundary)
            record = boundary.decide(
                assessment,
                decision_id="decision-restart-1",
                task_id="task:episode-1",
                thread_id="thread:episode-1",
                creator_id="creator-1",
                action="revise",
                decision_context="Replace the final scene transition.",
            )
            self.assertIsInstance(record, FinalVideoDecisionRecord)
            repository.close()

            reopened = SQLiteFinalVideoDecisionRepository(database)
            try:
                restarted = FinalVideoDecisionBoundary(reopened)
                self.assertEqual(restarted.get("decision-restart-1"), record)
                replay = restarted.decide(
                    self._assess(restarted),
                    decision_id="decision-restart-1",
                    task_id="task:episode-1",
                    thread_id="thread:episode-1",
                    creator_id="creator-1",
                    action="revise",
                    decision_context="Replace the final scene transition.",
                )
                self.assertEqual(replay, record)
                self.assertIsNot(replay, record)
                conflict = restarted.decide(
                    self._assess(restarted),
                    decision_id="decision-restart-1",
                    task_id="task:episode-1",
                    thread_id="thread:episode-1",
                    creator_id="creator-1",
                    action="reject",
                    decision_context="Reject the final video.",
                )
                self.assertIsInstance(conflict, FinalVideoDecisionFailure)
                self.assertEqual(conflict.code, "DECISION_CONFLICT")
            finally:
                reopened.close()

    def test_two_open_instances_observe_exact_replay_and_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            first = SQLiteFinalVideoDecisionRepository(database)
            second = SQLiteFinalVideoDecisionRepository(database)
            try:
                first_boundary = FinalVideoDecisionBoundary(first)
                second_boundary = FinalVideoDecisionBoundary(second)
                saved = first_boundary.decide(
                    self._assess(first_boundary),
                    decision_id="decision-two-open-1",
                    task_id="task:episode-1",
                    thread_id="thread:episode-1",
                    creator_id="creator-1",
                    action="approve",
                )
                self.assertIsInstance(saved, FinalVideoDecisionRecord)
                self.assertEqual(second_boundary.get("decision-two-open-1"), saved)
                self.assertEqual(
                    second_boundary.decide(
                        self._assess(second_boundary),
                        decision_id="decision-two-open-1",
                        task_id="task:episode-1",
                        thread_id="thread:episode-1",
                        creator_id="creator-1",
                        action="approve",
                    ),
                    saved,
                )
                conflict = second_boundary.decide(
                    self._assess(second_boundary),
                    decision_id="decision-two-open-1",
                    task_id="task:episode-1",
                    thread_id="thread:episode-1",
                    creator_id="creator-1",
                    action="reject",
                    decision_context="Reject this exact version.",
                )
                self.assertEqual(conflict.code, "DECISION_CONFLICT")
            finally:
                first.close()
                second.close()

    def test_malformed_direct_records_and_mismatched_repository_success_fail_closed(self):
        reference, _version = valid_video_version()
        valid = FinalVideoDecisionRecord(
            decision_id="decision-forged-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            gate_kind="final_video_review",
            video_reference=reference,
            assessment_disposition="pass",
            finding_codes=(),
            action="approve",
            decision_context="",
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteFinalVideoDecisionRepository(Path(directory) / "decisions.sqlite3")
            try:
                invalid = replace(valid, finding_codes=("FORGED",))
                result = repository.save(invalid)
                self.assertIsInstance(result, FinalVideoDecisionFailure)
                self.assertEqual(result.code, "INVALID_DECISION_RECORD")
                self.assertEqual(repository.get(invalid.decision_id).code, "DECISION_NOT_FOUND")
            finally:
                repository.close()

        boundary = FinalVideoDecisionBoundary(MismatchedSuccessRepository())
        result = boundary.decide(
            self._assess(boundary),
            decision_id="decision-mismatch-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(result, FinalVideoDecisionFailure)
        self.assertEqual(result.code, "FINAL_VIDEO_DECISION_FAILED")

        evil_boundary = FinalVideoDecisionBoundary(EvilSuccessRepository())
        evil_result = evil_boundary.decide(
            self._assess(evil_boundary),
            decision_id="decision-evil-success-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(evil_result, FinalVideoDecisionFailure)
        self.assertEqual(evil_result.code, "FINAL_VIDEO_DECISION_FAILED")

        reference, _version = valid_video_version()
        stored = FinalVideoDecisionRecord(
            decision_id="decision-invalid-get-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            gate_kind="final_video_review",
            video_reference=reference,
            assessment_disposition="pass",
            finding_codes=(),
            action="approve",
            decision_context="",
        )
        invalid_get = FinalVideoDecisionBoundary(InvalidGetRepository(stored)).get(
            "decision-invalid-get-1"
        )
        self.assertIsInstance(invalid_get, FinalVideoDecisionFailure)
        self.assertEqual(invalid_get.code, "FINAL_VIDEO_DECISION_FAILED")

    def test_direct_record_finding_codes_have_a_finite_bound(self):
        reference, _version = valid_video_version()
        record = FinalVideoDecisionRecord(
            decision_id="decision-too-many-findings-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            gate_kind="final_video_review",
            video_reference=reference,
            assessment_disposition="hard_block",
            finding_codes=tuple(f"FINDING_{index}" for index in range(10)),
            action="reject",
            decision_context="The video has too many findings.",
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteFinalVideoDecisionRepository(Path(directory) / "decisions.sqlite3")
            try:
                result = repository.save(record)
                self.assertIsInstance(result, FinalVideoDecisionFailure)
                self.assertEqual(result.code, "INVALID_DECISION_RECORD")
                self.assertEqual(repository.get(record.decision_id).code, "DECISION_NOT_FOUND")
            finally:
                repository.close()

    def test_malformed_row_future_schema_and_closed_lifecycle_are_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteFinalVideoDecisionRepository(database)
            boundary = FinalVideoDecisionBoundary(repository)
            record = boundary.decide(
                self._assess(boundary),
                decision_id="decision-corrupt-1",
                task_id="task:episode-1",
                thread_id="thread:episode-1",
                creator_id="creator-1",
                action="approve",
            )
            self.assertIsInstance(record, FinalVideoDecisionRecord)
            repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE final_video_decisions SET action = ? WHERE decision_id = ?",
                    ("publish", "decision-corrupt-1"),
                )
                connection.commit()
            malformed = SQLiteFinalVideoDecisionRepository(database)
            try:
                failure = malformed.get("decision-corrupt-1")
                self.assertEqual(failure.code, "FINAL_VIDEO_DECISION_FAILED")
                self.assertNotIn("publish", failure.message)
            finally:
                malformed.close()
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE final_video_decision_schema SET version = ? WHERE singleton = 1",
                    (999,),
                )
                connection.commit()
            future = SQLiteFinalVideoDecisionRepository(database)
            try:
                self.assertEqual(future.get("decision-corrupt-1").code, "FINAL_VIDEO_DECISION_FAILED")
            finally:
                future.close()

            closed = SQLiteFinalVideoDecisionRepository(database)
            closed.close()
            self.assertEqual(closed.get("decision-corrupt-1").code, "FINAL_VIDEO_DECISION_FAILED")

    def test_schema_stores_decision_fields_only_and_open_failure_is_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "decisions.sqlite3"
            repository = SQLiteFinalVideoDecisionRepository(database)
            try:
                pass
            finally:
                repository.close()
            with sqlite3.connect(database) as connection:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(final_video_decisions)")}
                self.assertEqual(
                    columns,
                    {
                        "decision_id", "task_id", "thread_id", "creator_id", "gate_kind",
                        "video_artifact_type", "video_identity", "video_version",
                        "assessment_disposition", "finding_codes_json", "action", "decision_context",
                    },
                )
            failed = SQLiteFinalVideoDecisionRepository(directory)
            try:
                result = failed.get("decision-open-failure")
                self.assertEqual(result.kind, "execution")
                self.assertEqual(result.code, "FINAL_VIDEO_DECISION_FAILED")
                self.assertEqual(result.message, "final video decision persistence failed")
            finally:
                failed.close()


if __name__ == "__main__":
    unittest.main()
