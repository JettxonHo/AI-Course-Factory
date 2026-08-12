"""Public contract tests for Script decision repositories."""

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from ai_course_factory.artifacts import (
    ArtifactReference,
    ScriptDecisionBoundary,
    ScriptDecisionFailure,
    ScriptDecisionRecord,
    ScriptDecisionRepository,
    SQLiteScriptDecisionRepository,
)

from tests.artifacts.test_script_decision import valid_versions


class ScriptDecisionRepositoryContractTests(unittest.TestCase):
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
        assessment = boundary.assess(
            script_reference,
            script_version,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
        )
        return assessment

    def test_sqlite_repository_is_runtime_checkable_and_round_trips_record(self):
        record = ScriptDecisionRecord(
            decision_id="decision-contract-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            gate_kind="script_review",
            script_reference=ArtifactReference("script", "script:episode-1", 1),
            knowledge_reference=ArtifactReference("knowledge", "knowledge:episode-1", 1),
            course_plan_reference=ArtifactReference("content_plan", "course:episode-1", 1),
            episode_plan_reference=ArtifactReference("content_plan", "episode:episode-1", 1),
            assessment_disposition="pass",
            finding_codes=(),
            action="approve",
            decision_context="",
        )

        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteScriptDecisionRepository(Path(directory) / "decisions.sqlite3")
            try:
                self.assertIsInstance(repository, ScriptDecisionRepository)
                self.assertEqual(repository.save(record), record)
                self.assertEqual(repository.get(record.decision_id), record)
            finally:
                repository.close()

    def test_default_and_sqlite_boundaries_preserve_replay_conflict_and_exact_get(self):
        repositories = [None]
        with tempfile.TemporaryDirectory() as directory:
            repositories.append(SQLiteScriptDecisionRepository(Path(directory) / "decisions.sqlite3"))
            for repository in repositories:
                with self.subTest(repository=type(repository).__name__ if repository else "memory"):
                    boundary = ScriptDecisionBoundary(repository)
                    assessment = self._assess(boundary)
                    record = boundary.decide(
                        assessment,
                        decision_id="decision-shared-1",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action="approve",
                    )
                    self.assertIsInstance(record, ScriptDecisionRecord)
                    self.assertEqual(boundary.get("decision-shared-1"), record)
                    replay = boundary.decide(
                        assessment,
                        decision_id="decision-shared-1",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action="approve",
                    )
                    self.assertEqual(replay, record)
                    conflict = boundary.decide(
                        assessment,
                        decision_id="decision-shared-1",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action="revise",
                        decision_context="Change scene two.",
                    )
                    self.assertIsInstance(conflict, ScriptDecisionFailure)
                    self.assertEqual(conflict.code, "DECISION_CONFLICT")
                    self.assertEqual(boundary.get("decision-shared-1"), record)
            if repositories[1] is not None:
                repositories[1].close()

    def test_repository_save_never_allows_hard_block_approval(self):
        repositories = [None]
        with tempfile.TemporaryDirectory() as directory:
            repositories.append(SQLiteScriptDecisionRepository(Path(directory) / "decisions.sqlite3"))
            values = list(valid_versions())
            script_reference = values[7]
            script_version = values[8]
            values[8] = script_version.__class__(
                reference=script_version.reference,
                payload={
                    **script_version.payload,
                    "scenes": (
                        {
                            **script_version.payload["scenes"][0],
                            "knowledge_claim_ids": ("foreign",),
                        },
                        *script_version.payload["scenes"][1:],
                    ),
                },
                provenance=script_version.provenance,
                dependencies=script_version.dependencies,
                commit_id=script_version.commit_id,
                prior_reference=script_version.prior_reference,
            )
            for repository in repositories:
                with self.subTest(repository=type(repository).__name__ if repository else "memory"):
                    boundary = ScriptDecisionBoundary(repository)
                    assessment = self._assess_with_values(boundary, tuple(values))
                    self.assertEqual(assessment.disposition, "hard_block")
                    result = boundary.decide(
                        assessment,
                        decision_id="decision-hard-block-shared",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action="approve",
                    )
                    self.assertIsInstance(result, ScriptDecisionFailure)
                    self.assertEqual(result.code, "HARD_BLOCK_APPROVAL_FORBIDDEN")
            if repositories[1] is not None:
                repositories[1].close()

    def test_sqlite_direct_save_rejects_forged_or_malformed_records_atomically(self):
        record = ScriptDecisionRecord(
            decision_id="decision-forged-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            gate_kind="script_review",
            script_reference=ArtifactReference("script", "script:episode-1", 1),
            knowledge_reference=ArtifactReference("knowledge", "knowledge:episode-1", 1),
            course_plan_reference=ArtifactReference("content_plan", "course:episode-1", 1),
            episode_plan_reference=ArtifactReference("content_plan", "episode:episode-1", 1),
            assessment_disposition="pass",
            finding_codes=(),
            action="approve",
            decision_context="",
        )
        malformed_records = (
            replace(record, finding_codes=("FORGED_FINDING",)),
            replace(record, finding_codes=["not-a-tuple"]),
            replace(record, script_reference=ArtifactReference("script", "latest", 1)),
            replace(record, decision_context="\n"),
            replace(
                record,
                assessment_disposition="hard_block",
                finding_codes=("HARD_BLOCK",),
                action="approve",
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteScriptDecisionRepository(Path(directory) / "decisions.sqlite3")
            try:
                for index, malformed in enumerate(malformed_records):
                    malformed = replace(malformed, decision_id=f"decision-forged-{index}")
                    with self.subTest(index=index):
                        result = repository.save(malformed)
                        self.assertIsInstance(result, ScriptDecisionFailure)
                        self.assertIn(
                            result.code,
                            {
                                "INVALID_DECISION_RECORD",
                                "INVALID_SCRIPT_REFERENCE",
                                "INVALID_DECISION_CONTEXT",
                                "HARD_BLOCK_APPROVAL_FORBIDDEN",
                            },
                        )
                        self.assertIsInstance(repository.get(malformed.decision_id), ScriptDecisionFailure)
            finally:
                repository.close()

    @staticmethod
    def _assess_with_values(boundary: ScriptDecisionBoundary, values):
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


if __name__ == "__main__":
    unittest.main()
