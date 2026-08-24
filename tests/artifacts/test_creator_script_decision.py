from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    CreatorScriptDecisionBoundary,
    CreatorScriptDecisionFailure,
    CreatorScriptDecisionRecord,
    SQLiteArtifactRepository,
    SQLiteCreatorScriptDecisionRepository,
)


class CreatorScriptDecisionRepositoryTests(unittest.TestCase):
    def test_creator_decision_durable_replay_and_conflict_are_exact(self) -> None:
        with TemporaryDirectory() as directory:
            database = Path(directory) / "factory.sqlite3"
            artifacts = SQLiteArtifactRepository(database)
            source = artifacts.commit(
                ArtifactCandidate(
                    "source_record", "source:episode-1", {"source_kind": "github", "units": ()},
                    dependencies=(), validated=True, commit_id="source-1",
                )
            )
            script = artifacts.commit(
                ArtifactCandidate(
                    "script", "script:episode-1",
                    {"script_package": {"schema": "ai-course-factory.creator-script-package", "version": 1, "script_package_id": "p-1"}},
                    dependencies=(source,), validated=True, commit_id="script-1",
                )
            )
            repository = SQLiteCreatorScriptDecisionRepository(database)
            boundary = CreatorScriptDecisionBoundary(repository)
            first = boundary.decide(
                script, artifacts.get(script), source_reference=source,
                decision_id="decision:creator-script:v1:approve", task_id="task-1", thread_id="thread-1",
                creator_id="creator-1", action="approve", decision_context="",
            )
            self.assertIsInstance(first, CreatorScriptDecisionRecord)
            replay = boundary.get(first.decision_id)
            self.assertEqual(replay, first)
            conflict = boundary.decide(
                script, artifacts.get(script), source_reference=source,
                decision_id="decision:creator-script:v1:approve", task_id="task-1", thread_id="thread-1",
                creator_id="creator-1", action="reject", decision_context="not good",
            )
            self.assertIsInstance(conflict, CreatorScriptDecisionFailure)
            self.assertEqual(conflict.code, "DECISION_CONFLICT")
            self.assertEqual(repository.count(), 1)


if __name__ == "__main__":
    unittest.main()
