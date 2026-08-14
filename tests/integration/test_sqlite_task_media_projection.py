"""Durable SQLite evidence for the additive Task media projection."""

from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import threading
import unittest

from ai_course_factory.application import (
    SQLiteTaskMediaRepository,
    SQLiteTaskRepository,
    TaskMediaProjectionChange,
    TaskMediaProjectionService,
    TaskProjectionChange,
    TaskSnapshot,
)

from tests.application.test_task_media_projection import _fixture, _media


class SQLiteTaskMediaProjectionIntegrationTests(unittest.TestCase):
    def test_batch_impact_is_additive_and_replays_after_sqlite_restart(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "factory.sqlite3"
            artifacts, request, timeline, scenes = _fixture()
            refs = _media(artifacts, request, timeline, scenes)
            repository = SQLiteTaskMediaRepository(database)
            service = TaskMediaProjectionService(artifacts, repository)
            self.assertEqual(service.create("batch-task", "batch-create", request).status, "success")
            selections = tuple(
                (scene["scene_id"], role, refs[(scene["scene_id"], role)])
                for scene in scenes
                for role in ("scene_clip", "scene_audio")
            )
            selected = service.select_batch(
                "batch-task",
                "batch-select",
                1,
                selections,
                (("subtitle", refs["subtitle"]), ("master_audio", refs["master_audio"]), ("video", refs["video"])),
            )
            self.assertEqual(selected.status, "success")
            self.assertEqual(type(selected.impact).__name__, "TaskMediaBatchImpact")
            repository.close()

            reopened = SQLiteTaskMediaRepository(database)
            restored = reopened.get("batch-task")
            self.assertEqual(restored.revision, 2)
            replay = reopened.save(TaskMediaProjectionChange("batch-task", "batch-select", 1, selected.snapshot, selected.impact))
            self.assertEqual(replay.snapshot, selected.snapshot)
            self.assertEqual(type(replay.impact).__name__, "TaskMediaBatchImpact")
            reopened.close()

    def test_coexists_with_planning_rows_and_survives_history_replay(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "factory.sqlite3"
            artifacts, request, timeline, scenes = _fixture()
            refs = _media(artifacts, request, timeline, scenes)

            planning = SQLiteTaskRepository(database)
            planning_change = TaskProjectionChange(
                "planning-task", "planning-create", None,
                TaskSnapshot("planning-task", 1, "created", (), "planning-create"),
            )
            self.assertEqual(planning.save(planning_change).status, "success")
            media_repository = SQLiteTaskMediaRepository(database)
            service = TaskMediaProjectionService(artifacts, media_repository)
            created = service.create("media-task", "media-create", request)
            self.assertEqual(created.status, "success")
            selected = service.select_scene(
                "media-task", "media-scene-2", 1, "scene-2", "scene_clip", refs[("scene-2", "scene_clip")]
            )
            self.assertEqual(selected.status, "success")
            self.assertEqual(service.inspect("media-task", 1).snapshot.revision, 1)
            replay = media_repository.save(
                # Reusing the exact immutable change is an idempotent replay.
                TaskMediaProjectionChange(
                    "media-task", "media-scene-2", 1, selected.snapshot, selected.impact
                )
            )
            self.assertEqual(replay, selected)

            media_repository.close()
            planning.close()
            reopened_planning = SQLiteTaskRepository(database)
            reopened_media = SQLiteTaskMediaRepository(database)
            self.assertEqual(reopened_planning.get("planning-task").revision, 1)
            restored = reopened_media.get("media-task")
            self.assertEqual(restored, selected.snapshot)
            self.assertEqual(reopened_media.get("media-task", 1).revision, 1)
            reopened_planning.close()
            reopened_media.close()

    def test_two_instances_serialize_competing_revision_and_closed_failure_is_safe(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "factory.sqlite3"
            artifacts, request, timeline, scenes = _fixture()
            refs = _media(artifacts, request, timeline, scenes)
            first_repo = SQLiteTaskMediaRepository(database)
            second_repo = SQLiteTaskMediaRepository(database)
            first = TaskMediaProjectionService(artifacts, first_repo)
            second = TaskMediaProjectionService(artifacts, second_repo)
            self.assertEqual(first.create("race-task", "race-create", request).status, "success")
            barrier = threading.Barrier(2)
            results = []

            def select(service, command):
                barrier.wait()
                results.append(service.select_scene("race-task", "race-" + command, 1, "scene-1", "scene_audio", refs[("scene-1", "scene_audio")]))

            threads = [threading.Thread(target=select, args=(first, "one")), threading.Thread(target=select, args=(second, "two"))]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
            self.assertEqual(sorted(result.status for result in results), ["failure", "success"])
            self.assertEqual(sum(result.error_code == "TASK_MEDIA_REVISION_CONFLICT" for result in results), 1)
            first_repo.close()
            self.assertEqual(first_repo.get("race-task").code, "TASK_MEDIA_REPOSITORY_FAILED")
            second_repo.close()

    def test_corrupt_snapshot_and_future_schema_fail_closed_without_raw_details(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "factory.sqlite3"
            artifacts, request, _timeline, _scenes = _fixture()
            repository = SQLiteTaskMediaRepository(database)
            self.assertEqual(TaskMediaProjectionService(artifacts, repository).create("safe-task", "safe-create", request).status, "success")
            repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE task_media_revisions SET snapshot_json=?", ("{bad",))
                connection.commit()
            corrupted = SQLiteTaskMediaRepository(database)
            failure = corrupted.get("safe-task")
            self.assertEqual(failure.code, "TASK_MEDIA_REPOSITORY_FAILED")
            self.assertNotIn("snapshot_json", failure.message)
            corrupted.close()
            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE task_media_schema SET version=999 WHERE singleton=1")
                connection.commit()
            future = SQLiteTaskMediaRepository(database)
            self.assertEqual(future.get("safe-task").code, "TASK_MEDIA_REPOSITORY_FAILED")
            future.close()

    def test_trigger_rollback_leaves_revision_unchanged_and_schema_stores_no_media_payload_or_path(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "factory.sqlite3"
            artifacts, request, timeline, scenes = _fixture()
            refs = _media(artifacts, request, timeline, scenes)
            repository = SQLiteTaskMediaRepository(database)
            service = TaskMediaProjectionService(artifacts, repository)
            self.assertEqual(service.create("atomic-task", "atomic-create", request).status, "success")
            with sqlite3.connect(database) as connection:
                connection.execute("""
                    CREATE TRIGGER task_media_abort BEFORE INSERT ON task_media_commands
                    BEGIN SELECT RAISE(ABORT, 'forced rollback'); END
                """)
                connection.commit()
            failed = service.select_scene("atomic-task", "atomic-scene", 1, "scene-1", "scene_clip", refs[("scene-1", "scene_clip")])
            self.assertEqual(failed.error_code, "TASK_MEDIA_REPOSITORY_FAILED")
            self.assertEqual(service.inspect("atomic-task").snapshot.revision, 1)
            with sqlite3.connect(database) as connection:
                columns = {
                    row[1] for row in connection.execute("PRAGMA table_info(task_media_revisions)")
                } | {
                    row[1] for row in connection.execute("PRAGMA table_info(task_media_commands)")
                }
                self.assertNotIn("media_payload", columns)
                self.assertNotIn("filesystem_path", columns)
                self.assertNotIn("output_path", columns)
            repository.close()

    def test_open_failure_is_safe_and_does_not_leak_sql_or_path(self):
        with TemporaryDirectory() as directory:
            repository = SQLiteTaskMediaRepository(Path(directory))
            failure = repository.get("task")
            self.assertEqual(failure.code, "TASK_MEDIA_REPOSITORY_FAILED")
            self.assertNotIn("sqlite", failure.message.lower())
            self.assertNotIn(str(Path(directory)), failure.message)
            repository.close()

    def test_command_revision_link_corruption_fails_closed(self):
        with TemporaryDirectory() as directory:
            database = Path(directory) / "factory.sqlite3"
            artifacts, request, _timeline, _scenes = _fixture()
            repository = SQLiteTaskMediaRepository(database)
            self.assertEqual(TaskMediaProjectionService(artifacts, repository).create("link-task", "link-create", request).status, "success")
            repository.close()
            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE task_media_commands SET task_id='foreign-task' WHERE command_id='link-create'")
                connection.commit()
            corrupted = SQLiteTaskMediaRepository(database)
            failure = corrupted.get("link-task")
            self.assertEqual(failure.code, "TASK_MEDIA_REPOSITORY_FAILED")
            self.assertEqual(failure.message, "task media repository operation failed")
            corrupted.close()


if __name__ == "__main__":
    unittest.main()
