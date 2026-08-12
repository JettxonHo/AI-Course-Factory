"""Public contract test for Storyboard decision repositories."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ai_course_factory.artifacts import (
    ArtifactReference,
    StoryboardDecisionBoundary,
    StoryboardDecisionFailure,
    StoryboardDecisionRecord,
    StoryboardDecisionRepository,
    SQLiteStoryboardDecisionRepository,
)

from tests.artifacts.test_storyboard_decision import storyboard_version


class StoryboardDecisionRepositoryContractTests(unittest.TestCase):
    def test_sqlite_repository_is_runtime_checkable_and_round_trips_record(self):
        record = StoryboardDecisionRecord(
            decision_id="decision-contract-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            gate_kind="storyboard_review",
            storyboard_reference=ArtifactReference("storyboard", "storyboard:episode-1", 1),
            script_reference=ArtifactReference("script", "script:episode-1", 1),
            character_reference=ArtifactReference("character", "character:potato-v1", 1),
            script_approval_decision_id="script-approval-1",
            review_enabled=True,
            action="revise",
            decision_context="Make scene two more concrete.",
        )

        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteStoryboardDecisionRepository(Path(directory) / "decisions.sqlite3")
            try:
                self.assertIsInstance(repository, StoryboardDecisionRepository)
                self.assertEqual(repository.save(record), record)
                self.assertEqual(repository.get(record.decision_id), record)
            finally:
                repository.close()

    def test_default_and_sqlite_boundaries_preserve_replay_conflict_and_exact_get(self):
        repositories = [None]
        with tempfile.TemporaryDirectory() as directory:
            repositories.append(
                SQLiteStoryboardDecisionRepository(Path(directory) / "decisions.sqlite3")
            )
            for repository in repositories:
                with self.subTest(repository=type(repository).__name__ if repository else "memory"):
                    storyboard_reference, storyboard, _script_reference, _character_reference = (
                        storyboard_version()
                    )
                    boundary = StoryboardDecisionBoundary(repository)
                    record = boundary.decide(
                        storyboard_reference,
                        storyboard,
                        review_enabled=True,
                        decision_id="decision-shared-1",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action="approve",
                    )
                    self.assertIsInstance(record, StoryboardDecisionRecord)
                    self.assertEqual(boundary.get("decision-shared-1"), record)
                    replay = boundary.decide(
                        storyboard_reference,
                        storyboard,
                        review_enabled=True,
                        decision_id="decision-shared-1",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action="approve",
                    )
                    self.assertEqual(replay, record)
                    conflict = boundary.decide(
                        storyboard_reference,
                        storyboard,
                        review_enabled=True,
                        decision_id="decision-shared-1",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action="revise",
                        decision_context="Change scene two.",
                    )
                    self.assertIsInstance(conflict, StoryboardDecisionFailure)
                    self.assertEqual(conflict.code, "DECISION_CONFLICT")
                    self.assertEqual(boundary.get("decision-shared-1"), record)
            repositories[1].close()

    def test_enabled_and_disabled_modes_remain_explicit_for_sqlite(self):
        storyboard_reference, storyboard, _script_reference, _character_reference = storyboard_version()
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteStoryboardDecisionRepository(Path(directory) / "decisions.sqlite3")
            try:
                boundary = StoryboardDecisionBoundary(repository)
                approved = boundary.decide(
                    storyboard_reference,
                    storyboard,
                    review_enabled=True,
                    decision_id="decision-enabled-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="approve",
                )
                self.assertIsInstance(approved, StoryboardDecisionRecord)
                self.assertIs(approved.review_enabled, True)

                skipped = boundary.decide(
                    storyboard_reference,
                    storyboard,
                    review_enabled=False,
                    decision_id="decision-disabled-1",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="skip",
                )
                self.assertIsInstance(skipped, StoryboardDecisionRecord)
                self.assertIs(skipped.review_enabled, False)
                self.assertEqual(skipped.action, "skip")
                restored_skipped = boundary.get("decision-disabled-1")
                self.assertEqual(restored_skipped, skipped)
                self.assertIs(restored_skipped.review_enabled, False)

                invalid_enabled = boundary.decide(
                    storyboard_reference,
                    storyboard,
                    review_enabled=True,
                    decision_id="decision-enabled-skip",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="skip",
                )
                self.assertEqual(invalid_enabled.code, "INVALID_DECISION_ACTION")
                invalid_disabled = boundary.decide(
                    storyboard_reference,
                    storyboard,
                    review_enabled=False,
                    decision_id="decision-disabled-approve",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="approve",
                )
                self.assertEqual(invalid_disabled.code, "INVALID_DECISION_ACTION")
                self.assertEqual(boundary.get("decision-enabled-skip").code, "DECISION_NOT_FOUND")
                self.assertEqual(boundary.get("decision-disabled-approve").code, "DECISION_NOT_FOUND")
            finally:
                repository.close()

    def test_sqlite_direct_save_rejects_malformed_records_atomically(self):
        record = StoryboardDecisionRecord(
            decision_id="decision-forged-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            gate_kind="storyboard_review",
            storyboard_reference=ArtifactReference("storyboard", "storyboard:episode-1", 1),
            script_reference=ArtifactReference("script", "script:episode-1", 1),
            character_reference=ArtifactReference("character", "character:potato-v1", 1),
            script_approval_decision_id="script-approval-1",
            review_enabled=True,
            action="approve",
            decision_context="",
        )
        malformed_records = (
            replace(record, action="skip"),
            replace(record, review_enabled=1),
            replace(record, storyboard_reference=ArtifactReference("storyboard", "latest", 1)),
            replace(record, decision_context="\n"),
            replace(record, gate_kind="other_gate"),
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteStoryboardDecisionRepository(Path(directory) / "decisions.sqlite3")
            try:
                for index, malformed in enumerate(malformed_records):
                    malformed = replace(malformed, decision_id=f"decision-forged-{index}")
                    with self.subTest(index=index):
                        result = repository.save(malformed)
                        self.assertIsInstance(result, StoryboardDecisionFailure)
                        self.assertIn(
                            result.code,
                            {
                                "INVALID_DECISION_ACTION",
                                "INVALID_REVIEW_ENABLED",
                                "INVALID_STORYBOARD_REFERENCE",
                                "INVALID_DECISION_CONTEXT",
                                "INVALID_DECISION_RECORD",
                            },
                        )
                        self.assertIsInstance(
                            repository.get(malformed.decision_id), StoryboardDecisionFailure
                        )
            finally:
                repository.close()


if __name__ == "__main__":
    unittest.main()
