"""Durability and concurrency evidence for the Task projection."""

import json
import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from ai_course_factory.application import (
    SQLiteTaskRepository,
    TaskArtifactSelection,
    TaskImpact,
    TaskOperationResult,
    TaskProjectionChange,
    TaskProjectionService,
    TaskRepository,
    TaskSnapshot,
)
from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    ArtifactReference,
    SQLiteArtifactRepository,
)


def _source_store() -> tuple[ArtifactCommitBoundary, object]:
    store = ArtifactCommitBoundary()
    reference = store.commit(ArtifactCandidate(
        artifact_type="source", identity="source:sqlite", payload={"url": "https://example.test"},
        provenance=("fixture",), dependencies=(), validated=True, commit_id="source-sqlite-v1",
    ))
    return store, reference


class SQLiteTaskProjectionIntegrationTests(unittest.TestCase):
    def test_close_reopen_preserves_current_history_and_command_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact_database = Path(directory) / "artifacts.sqlite3"
            database = Path(directory) / "task.sqlite3"
            store = SQLiteArtifactRepository(artifact_database)
            source = store.commit(ArtifactCandidate(
                artifact_type="source", identity="source:sqlite", payload={"url": "https://example.test"},
                provenance=("fixture",), dependencies=(), validated=True, commit_id="source-sqlite-v1",
            ))
            repository = SQLiteTaskRepository(database)
            self.assertIsInstance(repository, TaskRepository)
            service = TaskProjectionService(store, repository)
            self.assertEqual(service.create("task-sqlite", "create-sqlite").status, "success")
            selected = service.select("task-sqlite", "select-sqlite", 1, "source", source)
            self.assertEqual(selected.status, "success", selected)
            with sqlite3.connect(database) as connection:
                schema = " ".join(
                    row[0] for row in connection.execute(
                        "SELECT sql FROM sqlite_master WHERE type='table' AND name LIKE 'task_%'"
                    )
                ).lower()
                stored = " ".join(
                    row[0] for row in connection.execute("SELECT snapshot_json FROM task_revisions")
                )
            self.assertNotIn("payload", schema)
            self.assertNotIn("https://example.test", stored)
            repository.close()
            store.close()

            reopened = SQLiteTaskRepository(database)
            reopened_store = SQLiteArtifactRepository(artifact_database)
            try:
                restored = TaskProjectionService(reopened_store, reopened)
                self.assertEqual(restored.inspect("task-sqlite").snapshot, selected.snapshot)
                self.assertEqual(restored.inspect("task-sqlite", 1).snapshot.revision, 1)
                self.assertEqual(
                    restored.select("task-sqlite", "select-sqlite", 1, "source", source), selected
                )
            finally:
                reopened.close()
                reopened_store.close()

    def test_two_instances_concurrently_serialize_one_expected_revision_winner(self):
        store, source = _source_store()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "task.sqlite3"
            setup = SQLiteTaskRepository(database)
            try:
                setup_service = TaskProjectionService(store, setup)
                self.assertEqual(setup_service.create("task-race", "create-race").status, "success")
            finally:
                setup.close()

            barrier = threading.Barrier(2)
            outcomes: list[TaskOperationResult] = []
            errors: list[BaseException] = []
            lock = threading.Lock()

            def race(command_id: str) -> None:
                repository = SQLiteTaskRepository(database)
                try:
                    service = TaskProjectionService(store, repository)
                    self.assertEqual(service.inspect("task-race").snapshot.revision, 1)
                    barrier.wait(timeout=5)
                    result = service.select("task-race", command_id, 1, "source", source)
                    with lock:
                        outcomes.append(result)
                except BaseException as exc:
                    with lock:
                        errors.append(exc)
                finally:
                    repository.close()

            threads = [threading.Thread(target=race, args=(command,)) for command in ("race-a", "race-b")]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertFalse(errors, errors)
            self.assertEqual(len(outcomes), 2)
            self.assertEqual(sum(result.status == "success" for result in outcomes), 1)
            self.assertEqual(sum(result.error_code == "TASK_REVISION_CONFLICT" for result in outcomes), 1)
            final = SQLiteTaskRepository(database)
            try:
                self.assertEqual(TaskProjectionService(store, final).inspect("task-race").snapshot.revision, 2)
            finally:
                final.close()

    def test_replay_of_original_command_returns_original_impact_after_later_revision(self):
        store, source = _source_store()
        replacement = store.commit(ArtifactCandidate(
            artifact_type="source", identity="source:sqlite", payload={"revision": 2},
            provenance=("fixture",), dependencies=(), validated=True,
            commit_id="source-sqlite-v2", prior_reference=source,
        ))
        replacement_again = store.commit(ArtifactCandidate(
            artifact_type="source", identity="source:sqlite", payload={"revision": 3},
            provenance=("fixture",), dependencies=(), validated=True,
            commit_id="source-sqlite-v3", prior_reference=replacement,
        ))
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteTaskRepository(Path(directory) / "task.sqlite3")
            try:
                service = TaskProjectionService(store, repository)
                service.create("task-replay", "create-replay")
                first = service.select("task-replay", "first-selection", 1, "source", source)
                later = service.select("task-replay", "second-selection", 2, "source", replacement)
                self.assertEqual(later.status, "success", later)
                latest = service.select("task-replay", "third-selection", 3, "source", replacement_again)
                self.assertEqual(latest.status, "success", latest)
                replay = service.select("task-replay", "second-selection", 2, "source", replacement)
                self.assertEqual(replay, later)
                self.assertEqual(replay.impact.previous_reference, source)
                self.assertEqual(replay.snapshot.revision, 3)
                self.assertNotEqual(first.snapshot, replay.snapshot)
            finally:
                repository.close()

    def test_revision_snapshot_command_link_mutation_fails_but_prior_revision_recovers(self):
        store, source = _source_store()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "task.sqlite3"
            repository = SQLiteTaskRepository(database)
            service = TaskProjectionService(store, repository)
            service.create("task-command-link", "create-command-link")
            service.select("task-command-link", "select-command-link", 1, "source", source)
            repository.close()
            with sqlite3.connect(database) as connection:
                raw = connection.execute(
                    "SELECT snapshot_json FROM task_revisions WHERE task_id=? AND revision=?",
                    ("task-command-link", 2),
                ).fetchone()[0]
                snapshot = json.loads(raw)
                snapshot["last_command_id"] = "other-valid-command"
                connection.execute(
                    "UPDATE task_revisions SET snapshot_json=? WHERE task_id=? AND revision=?",
                    (json.dumps(snapshot, separators=(",", ":"), sort_keys=True), "task-command-link", 2),
                )
                connection.commit()
            reopened = SQLiteTaskRepository(database)
            try:
                self.assertEqual(reopened.get("task-command-link").code, "TASK_REPOSITORY_FAILED")
                self.assertEqual(reopened.get("task-command-link", 1).revision, 1)
            finally:
                reopened.close()

    def test_sqlite_direct_transition_rejects_forged_prior_and_disjoint_change_atomically(self):
        store, source = _source_store()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "task-transition.sqlite3"
            repository = SQLiteTaskRepository(database)
            service = TaskProjectionService(store, repository)
            self.assertEqual(service.create("task-transition", "create-transition").status, "success")
            self.assertEqual(service.select("task-transition", "select-v1", 1, "source", source).status, "success")
            forged_v2 = ArtifactReference("source", "source:sqlite", 2)
            forged_v3 = ArtifactReference("source", "source:sqlite", 3)
            wrong_prior = TaskProjectionChange(
                "task-transition", "wrong-prior", 2,
                TaskSnapshot(
                    "task-transition", 3, "source_ready",
                    (TaskArtifactSelection("source", forged_v3, "current"),), "wrong-prior",
                ),
                TaskImpact("task-transition", "source", forged_v2, forged_v3, (), ()),
            )
            self.assertEqual(repository.save(wrong_prior).error_code, "TASK_REPOSITORY_FAILED")
            disjoint = TaskProjectionChange(
                "task-transition", "disjoint-change", 2,
                TaskSnapshot(
                    "task-transition", 3, "knowledge_ready",
                    (
                        TaskArtifactSelection("source", forged_v2, "current"),
                        TaskArtifactSelection("knowledge", ArtifactReference("knowledge", "knowledge:foreign", 1), "current"),
                    ), "disjoint-change",
                ),
                TaskImpact("task-transition", "source", source, forged_v2, (), ()),
            )
            self.assertEqual(repository.save(disjoint).error_code, "TASK_REPOSITORY_FAILED")
            self.assertEqual(service.inspect("task-transition").snapshot.revision, 2)
            repository.close()

    def test_sqlite_reopen_preserves_replacement_lifecycle_with_unrelated_later_current(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact_database = Path(directory) / "branch-artifacts.sqlite3"
            task_database = Path(directory) / "branch-task.sqlite3"
            artifacts = SQLiteArtifactRepository(artifact_database)

            def commit(artifact_type, identity, dependencies=(), payload=None, commit_id=None, prior_reference=None):
                return artifacts.commit(ArtifactCandidate(
                    artifact_type=artifact_type,
                    identity=identity,
                    payload=payload or {"identity": identity},
                    provenance=("fixture",),
                    dependencies=dependencies,
                    validated=True,
                    commit_id=commit_id or f"{identity}-v1",
                    prior_reference=prior_reference,
                ))

            source = commit("source", "source:branch", payload={"url": "https://example.test"})
            knowledge = commit("knowledge", "knowledge:branch", (source,))
            course = commit("content_plan", "plan:branch-course", (knowledge,), {"role": "course"})
            episode = commit("content_plan", "plan:branch-episode", (knowledge,), {"role": "episode"})
            script = commit("script", "script:branch", (knowledge, course, episode))
            request = commit("production_request", "request:unrelated")
            budget = commit("production_budget", "budget:unrelated", (request,))
            replacement = commit(
                "knowledge", "knowledge:branch", (source,), {"revision": 2},
                "knowledge:branch-v2", knowledge,
            )
            repository = SQLiteTaskRepository(task_database)
            service = TaskProjectionService(artifacts, repository)
            self.assertEqual(service.create("task-branch-sqlite", "create-branch").status, "success")
            revision = 1
            for index, (slot, reference) in enumerate(
                (("source", source), ("knowledge", knowledge), ("course_plan", course),
                 ("episode_plan", episode), ("script", script), ("production_request", request),
                 ("production_budget", budget)), start=1
            ):
                self.assertEqual(
                    service.select("task-branch-sqlite", f"branch-{index}", revision, slot, reference).status,
                    "success",
                )
                revision += 1
            result = service.select("task-branch-sqlite", "replace-branch", revision, "knowledge", replacement)
            self.assertEqual(result.status, "success", result)
            self.assertEqual(result.snapshot.lifecycle_state, "knowledge_ready")
            repository.close()
            artifacts.close()

            reopened_artifacts = SQLiteArtifactRepository(artifact_database)
            reopened_repository = SQLiteTaskRepository(task_database)
            try:
                restored = TaskProjectionService(reopened_artifacts, reopened_repository).inspect("task-branch-sqlite")
                self.assertEqual(restored.status, "success", restored)
                self.assertEqual(restored.snapshot.lifecycle_state, "knowledge_ready")
                self.assertEqual(
                    next(item.status for item in restored.snapshot.selections if item.slot == "production_budget"),
                    "current",
                )
            finally:
                reopened_repository.close()
                reopened_artifacts.close()

    def test_open_directory_and_triggered_command_write_fail_without_partial_revision(self):
        store, source = _source_store()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "task-trigger.sqlite3"
            repository = SQLiteTaskRepository(database)
            service = TaskProjectionService(store, repository)
            self.assertEqual(service.create("task-trigger", "create-trigger").status, "success")
            repository.close()
            directory_repository = SQLiteTaskRepository(Path(directory))
            self.assertEqual(directory_repository.get("task-trigger").code, "TASK_REPOSITORY_FAILED")
            directory_repository.close()

            repository = SQLiteTaskRepository(database)
            service = TaskProjectionService(store, repository)
            with sqlite3.connect(database) as connection:
                connection.execute("""
                    CREATE TRIGGER fail_task_command_insert
                    BEFORE INSERT ON task_commands
                    BEGIN SELECT RAISE(ABORT, 'deterministic trigger failure'); END
                """)
                connection.commit()
            failed = service.select("task-trigger", "select-trigger", 1, "source", source)
            self.assertEqual(failed.error_code, "TASK_REPOSITORY_FAILED")
            self.assertEqual(service.inspect("task-trigger").snapshot.revision, 1)
            repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute("DROP TRIGGER fail_task_command_insert")
                connection.commit()
            reopened = SQLiteTaskRepository(database)
            try:
                restored = TaskProjectionService(store, reopened)
                self.assertEqual(restored.inspect("task-trigger").snapshot.revision, 1)
                self.assertEqual(restored.select("task-trigger", "select-trigger", 1, "source", source).status, "success")
            finally:
                reopened.close()

    def test_corrupt_typed_rows_future_schema_and_closed_repository_fail_safely(self):
        store, source = _source_store()
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "task.sqlite3"
            repository = SQLiteTaskRepository(database)
            service = TaskProjectionService(store, repository)
            service.create("task-corrupt", "create-corrupt")
            service.select("task-corrupt", "select-corrupt", 1, "source", source)
            repository.close()
            closed = repository.get("task-corrupt")
            self.assertEqual(closed.code, "TASK_REPOSITORY_FAILED")

            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE task_revisions SET snapshot_json=? WHERE task_id=? AND revision=?",
                    ("{\"task_id\":\"task-corrupt\",\"revision\":true}", "task-corrupt", 2),
                )
                connection.commit()
            reopened = SQLiteTaskRepository(database)
            try:
                failure = reopened.get("task-corrupt")
                self.assertEqual(failure.code, "TASK_REPOSITORY_FAILED")
                self.assertNotIn(str(database), failure.message)
            finally:
                reopened.close()

            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE task_schema SET version=999 WHERE singleton=1")
                connection.commit()
            future = SQLiteTaskRepository(database)
            self.assertEqual(future.get("task-corrupt").code, "TASK_REPOSITORY_FAILED")
            future.close()


if __name__ == "__main__":
    unittest.main()
