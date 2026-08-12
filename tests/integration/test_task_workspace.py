"""Offline Task projection and task-scoped workspace composition evidence."""

from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest

from ai_course_factory.application import SQLiteTaskRepository, TaskProjectionService
from ai_course_factory.artifacts import ArtifactCandidate, ArtifactCommitBoundary
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFailure, WorkspaceFileRecord, WorkspaceFileReference


class TaskWorkspaceIntegrationTests(unittest.TestCase):
    def test_task_and_fixture_blob_survive_adapter_reconstruction(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            artifact_store = ArtifactCommitBoundary()
            source = artifact_store.commit(ArtifactCandidate(
                artifact_type="source", identity="source:workspace", payload={"fixture": True},
                provenance=("fixture",), dependencies=(), validated=True, commit_id="source-workspace-v1",
            ))
            task_database = base / "task.sqlite3"
            workspace_root = base / "workspace"
            repository = SQLiteTaskRepository(task_database)
            workspace = FilesystemWorkspace(workspace_root)
            try:
                service = TaskProjectionService(artifact_store, repository)
                self.assertEqual(service.create("task-workspace", "create-workspace").status, "success")
                selected = service.select("task-workspace", "select-workspace", 1, "source", source)
                self.assertEqual(selected.status, "success", selected)
                self.assertEqual(workspace.prepare("task-workspace").task_id, "task-workspace")
                reference = WorkspaceFileReference("task-workspace", "provider-records", "fixture.json")
                record = workspace.commit(reference, b"opaque-fixture")
                self.assertEqual(record, WorkspaceFileRecord(reference, 14))
            finally:
                repository.close()

            reopened_repository = SQLiteTaskRepository(task_database)
            reopened_workspace = FilesystemWorkspace(workspace_root)
            try:
                restored = TaskProjectionService(artifact_store, reopened_repository).inspect("task-workspace")
                self.assertEqual(restored.snapshot, selected.snapshot)
                self.assertEqual(reopened_workspace.read(reference), b"opaque-fixture")
            finally:
                reopened_repository.close()

    def test_reconstructed_adapters_racing_different_bytes_have_one_winner(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            setup = FilesystemWorkspace(root)
            self.assertEqual(setup.prepare("task-race").task_id, "task-race")
            reference = WorkspaceFileReference("task-race", "media", "same.bin")
            barrier = threading.Barrier(2)
            outcomes: list[object] = []
            errors: list[BaseException] = []
            lock = threading.Lock()

            def race(content: bytes) -> None:
                adapter = FilesystemWorkspace(root)
                try:
                    barrier.wait(timeout=5)
                    result = adapter.commit(reference, content)
                    with lock:
                        outcomes.append(result)
                except BaseException as exc:
                    with lock:
                        errors.append(exc)

            threads = [threading.Thread(target=race, args=(content,)) for content in (b"left", b"right")]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertFalse(errors, errors)
            self.assertEqual(len(outcomes), 2)
            self.assertEqual(sum(isinstance(result, WorkspaceFileRecord) for result in outcomes), 1)
            self.assertEqual(sum(isinstance(result, WorkspaceFailure) and result.code == "WORKSPACE_FILE_CONFLICT" for result in outcomes), 1)
            winner = FilesystemWorkspace(root).read(reference)
            self.assertIn(winner, (b"left", b"right"))
            self.assertEqual(list((root / "tasks" / "task-race" / "media").glob(".workspace-*")), [])

    def test_reconstructed_adapters_racing_equal_bytes_replay_safely(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            self.assertEqual(FilesystemWorkspace(root).prepare("task-equal").task_id, "task-equal")
            reference = WorkspaceFileReference("task-equal", "exports", "same.bin")
            barrier = threading.Barrier(2)
            outcomes: list[object] = []
            errors: list[BaseException] = []
            lock = threading.Lock()

            def race() -> None:
                adapter = FilesystemWorkspace(root)
                try:
                    barrier.wait(timeout=5)
                    result = adapter.commit(reference, b"same")
                    with lock:
                        outcomes.append(result)
                except BaseException as exc:
                    with lock:
                        errors.append(exc)

            threads = [threading.Thread(target=race) for _ in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertFalse(errors, errors)
            self.assertEqual(outcomes, [WorkspaceFileRecord(reference, 4), WorkspaceFileRecord(reference, 4)])
            self.assertEqual(FilesystemWorkspace(root).read(reference), b"same")
