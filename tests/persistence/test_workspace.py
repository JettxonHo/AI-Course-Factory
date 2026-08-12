"""Public behavior tests for the task-scoped filesystem workspace."""

import unittest
from dataclasses import fields
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
import os

from ai_course_factory.persistence import (
    FilesystemWorkspace,
    TaskWorkspace,
    WorkspaceAdapter,
    WorkspaceFailure,
    WorkspaceFileRecord,
    WorkspaceFileReference,
)


class WorkspacePublicContractTests(unittest.TestCase):
    def test_public_workspace_seam_exists(self):
        self.assertIsInstance(TaskWorkspace, type)

    def test_public_records_are_frozen_slotted_and_logical_prepare_commit_read(self):
        records = (TaskWorkspace, WorkspaceFileReference, WorkspaceFileRecord, WorkspaceFailure)
        for record in records:
            self.assertTrue(record.__dataclass_params__.frozen)
            self.assertTrue(hasattr(record, "__slots__"))
        self.assertEqual(tuple(field.name for field in fields(TaskWorkspace)), ("task_id", "areas"))
        self.assertEqual(tuple(field.name for field in fields(WorkspaceFileReference)), ("task_id", "area", "name"))
        self.assertEqual(tuple(field.name for field in fields(WorkspaceFileRecord)), ("reference", "size_bytes"))
        self.assertEqual(tuple(field.name for field in fields(WorkspaceFailure)), ("code", "message"))

        with TemporaryDirectory() as directory:
            adapter = FilesystemWorkspace(Path(directory) / "root")
            self.assertIsInstance(adapter, WorkspaceAdapter)
            prepared = adapter.prepare("task:demo")
            self.assertEqual(prepared, TaskWorkspace("task:demo", ("media", "provider-records", "exports")))
            reference = WorkspaceFileReference("task:demo", "media", "fixture.bin")
            committed = adapter.commit(reference, b"fixture")
            self.assertEqual(committed, WorkspaceFileRecord(reference, 7))
            self.assertEqual(adapter.read(reference), b"fixture")
            self.assertEqual(
                sorted(path.relative_to(Path(directory) / "root").as_posix() for path in (Path(directory) / "root").rglob("*")),
                ["tasks", "tasks/task:demo", "tasks/task:demo/exports", "tasks/task:demo/media", "tasks/task:demo/media/fixture.bin", "tasks/task:demo/provider-records"],
            )

    def test_path_component_area_content_and_reference_validation_is_safe(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            adapter = FilesystemWorkspace(root)
            valid = WorkspaceFileReference("task:demo", "media", "fixture.bin")
            self.assertEqual(adapter.prepare("task:demo").task_id, "task:demo")
            invalid_tasks = ("", ".", "..", "latest", "LATEST", "_leading", "-leading", ":leading",
                             "nested/name", "nested\\name", "é", "е", "a\x00b", "a" * 129)
            for task_id in invalid_tasks:
                result = adapter.prepare(task_id)
                self.assertIsInstance(result, WorkspaceFailure)
                self.assertEqual(result.code, "INVALID_WORKSPACE_TASK_ID")
            for reference, code in (
                (WorkspaceFileReference("task:demo", "wrong", "fixture.bin"), "INVALID_WORKSPACE_AREA"),
                (WorkspaceFileReference("task:demo", "media", "latest"), "INVALID_WORKSPACE_FILE_NAME"),
                (WorkspaceFileReference("task:demo", "media", "é"), "INVALID_WORKSPACE_FILE_NAME"),
                (WorkspaceFileReference("task:demo", "media", "nested/name"), "INVALID_WORKSPACE_FILE_NAME"),
                (WorkspaceFileReference("task:demo", "media", "_leading"), "INVALID_WORKSPACE_FILE_NAME"),
                (WorkspaceFileReference("task:demo", "media", "a" * 129), "INVALID_WORKSPACE_FILE_NAME"),
                (WorkspaceFileReference("latest", "media", "fixture.bin"), "INVALID_WORKSPACE_TASK_ID"),
            ):
                result = adapter.commit(reference, b"fixture")
                self.assertIsInstance(result, WorkspaceFailure)
                self.assertEqual(result.code, code)
            self.assertEqual(adapter.commit(None, b"fixture").code, "INVALID_WORKSPACE_REFERENCE")
            self.assertEqual(adapter.commit(valid, bytearray(b"fixture")).code, "INVALID_WORKSPACE_CONTENT")
            self.assertEqual(adapter.commit(valid, memoryview(b"fixture")).code, "INVALID_WORKSPACE_CONTENT")
            self.assertEqual(adapter.commit(valid, "fixture").code, "INVALID_WORKSPACE_CONTENT")
            self.assertEqual(adapter.read(valid).code, "WORKSPACE_FILE_NOT_FOUND")
            self.assertFalse((Path(directory) / "outside").exists())

    def test_symlinked_owned_components_and_file_are_rejected_without_following(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            outside = base / "outside"
            outside.mkdir()
            adapter = FilesystemWorkspace(root)
            reference = WorkspaceFileReference("task-demo", "media", "fixture.bin")
            self.assertEqual(adapter.prepare("task-demo").task_id, "task-demo")
            task = root / "tasks" / "task-demo"
            (task / "media").rename(task / "media-real")
            (task / "media").symlink_to(outside, target_is_directory=True)
            self.assertEqual(adapter.prepare("task-demo").code, "WORKSPACE_STORAGE_ERROR")

            (task / "media").unlink()
            (task / "media-real").rename(task / "media")
            target = task / "media" / reference.name
            target.symlink_to(outside / "outside.bin")
            self.assertEqual(adapter.commit(reference, b"fixture").code, "WORKSPACE_STORAGE_ERROR")
            self.assertEqual(adapter.read(reference).code, "WORKSPACE_STORAGE_ERROR")

            (task / "media").rename(task / "media-real")
            (task / "media").symlink_to(outside, target_is_directory=True)
            self.assertEqual(adapter.prepare("task-demo").code, "WORKSPACE_STORAGE_ERROR")

    def test_root_and_tasks_symlinks_are_rejected(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            outside = base / "outside"
            outside.mkdir()
            real_root = base / "real-root"
            adapter = FilesystemWorkspace(real_root)
            self.assertEqual(adapter.prepare("task-demo").task_id, "task-demo")
            linked_root = base / "linked-root"
            real_root.rename(linked_root)
            real_root.symlink_to(outside, target_is_directory=True)
            self.assertEqual(FilesystemWorkspace(real_root).prepare("new-task").code, "WORKSPACE_STORAGE_ERROR")

            root = base / "tasks-root"
            fresh = FilesystemWorkspace(root)
            self.assertEqual(fresh.prepare("task-demo").task_id, "task-demo")
            tasks = root / "tasks"
            tasks.rename(root / "tasks-real")
            tasks.symlink_to(outside, target_is_directory=True)
            self.assertEqual(fresh.prepare("task-demo").code, "WORKSPACE_STORAGE_ERROR")

    def test_nested_configured_root_is_created_without_exposing_a_path(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "nested" / "workspace-root"
            prepared = FilesystemWorkspace(root).prepare("task-demo")
            self.assertEqual(prepared, TaskWorkspace("task-demo", ("media", "provider-records", "exports")))
            self.assertTrue((root / "tasks" / "task-demo" / "media").is_dir())

    def test_atomic_no_replace_commit_replay_conflict_and_failure_cleanup(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            adapter = FilesystemWorkspace(root)
            adapter.prepare("task-demo")
            reference = WorkspaceFileReference("task-demo", "exports", "result.bin")
            area = root / "tasks" / "task-demo" / "exports"
            first = adapter.commit(reference, b"first-bytes")
            self.assertEqual(first, WorkspaceFileRecord(reference, 11))
            self.assertEqual(adapter.commit(reference, b"first-bytes"), first)
            conflict = adapter.commit(reference, b"different")
            self.assertEqual(conflict.code, "WORKSPACE_FILE_CONFLICT")
            self.assertEqual(adapter.read(reference), b"first-bytes")
            self.assertEqual(list(area.glob(".workspace-*")), [])

            second = WorkspaceFileReference("task-demo", "exports", "second.bin")
            with patch("ai_course_factory.persistence.workspace.os.write", side_effect=OSError("injected")):
                failed_write = adapter.commit(second, b"second")
            self.assertEqual(failed_write.code, "WORKSPACE_STORAGE_ERROR")
            self.assertFalse((area / second.name).exists())
            self.assertEqual(list(area.glob(".workspace-*")), [])

            third = WorkspaceFileReference("task-demo", "exports", "third.bin")
            with patch("ai_course_factory.persistence.workspace.os.link", side_effect=OSError("injected")):
                failed_link = adapter.commit(third, b"third")
            self.assertEqual(failed_link.code, "WORKSPACE_STORAGE_ERROR")
            self.assertFalse((area / third.name).exists())
            self.assertEqual(list(area.glob(".workspace-*")), [])

            with patch("ai_course_factory.persistence.workspace.os.link", side_effect=FileExistsError):
                # An injected race still resolves through the existing immutable target.
                replay = adapter.commit(reference, b"first-bytes")
            self.assertEqual(replay, first)

    def test_large_opaque_bytes_are_read_exactly_and_records_are_detached(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            first = FilesystemWorkspace(root)
            first.prepare("task-large")
            reference = WorkspaceFileReference("task-large", "media", "large.bin")
            content = bytes(range(256)) * 20000
            record = first.commit(reference, content)
            self.assertEqual(record, WorkspaceFileRecord(reference, len(content)))
            self.assertIsInstance(record.size_bytes, int)
            self.assertNotIsInstance(record.size_bytes, bool)
            self.assertEqual(first.read(reference), content)
            second = FilesystemWorkspace(root)
            self.assertEqual(second.read(reference), content)
            self.assertEqual(second.commit(reference, content), record)

    def test_partial_write_and_fsync_failure_are_exact_and_clean(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            adapter = FilesystemWorkspace(root)
            adapter.prepare("task-write")
            reference = WorkspaceFileReference("task-write", "media", "partial.bin")
            real_write = os.write
            first_call = True

            def short_write(fd, data):
                nonlocal first_call
                if first_call:
                    first_call = False
                    count = max(1, len(data) // 2)
                    return real_write(fd, data[:count])
                return real_write(fd, data)

            with patch("ai_course_factory.persistence.workspace.os.write", side_effect=short_write):
                record = adapter.commit(reference, b"partial-content")
            self.assertEqual(record, WorkspaceFileRecord(reference, 15))
            self.assertEqual(adapter.read(reference), b"partial-content")

            failed = WorkspaceFileReference("task-write", "media", "fsync.bin")
            area = root / "tasks" / "task-write" / "media"
            with patch("ai_course_factory.persistence.workspace.os.fsync", side_effect=OSError("injected")):
                result = adapter.commit(failed, b"will-not-commit")
            self.assertEqual(result.code, "WORKSPACE_STORAGE_ERROR")
            self.assertFalse((area / failed.name).exists())
            self.assertEqual(list(area.glob(".workspace-*")), [])

    def test_area_swap_between_open_and_commit_is_safe_and_restorable(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            outside = base / "outside"
            outside.mkdir()
            adapter = FilesystemWorkspace(root)
            adapter.prepare("task-swap")
            existing = WorkspaceFileReference("task-swap", "media", "existing.bin")
            self.assertEqual(adapter.commit(existing, b"prior"), WorkspaceFileRecord(existing, 5))
            target = WorkspaceFileReference("task-swap", "media", "new.bin")
            task = root / "tasks" / target.task_id
            area = task / target.area
            real_area = task / "media-real"

            original_area = adapter._area

            def swapped_area(reference, *, create):
                handle = original_area(reference, create=create)
                if not create:
                    area.rename(real_area)
                    area.symlink_to(outside, target_is_directory=True)
                return handle

            with patch.object(adapter, "_area", side_effect=swapped_area):
                result = adapter.commit(target, b"escaped")
            self.assertIsInstance(result, WorkspaceFailure)
            self.assertEqual(result.code, "WORKSPACE_STORAGE_ERROR")
            self.assertFalse((outside / target.name).exists())
            self.assertFalse((real_area / target.name).exists())
            self.assertEqual(list(real_area.glob(".workspace-*")), [])
            area.unlink()
            real_area.rename(area)
            self.assertEqual(adapter.read(existing), b"prior")

    def test_area_swap_between_open_and_read_never_follows_external_directory(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            outside = base / "outside"
            outside.mkdir()
            adapter = FilesystemWorkspace(root)
            adapter.prepare("task-read-swap")
            reference = WorkspaceFileReference("task-read-swap", "media", "fixture.bin")
            self.assertEqual(adapter.commit(reference, b"owned"), WorkspaceFileRecord(reference, 5))
            (outside / reference.name).write_bytes(b"external")
            task = root / "tasks" / reference.task_id
            area = task / reference.area
            real_area = task / "media-real"
            original_area = adapter._area

            def swapped_area(ref, *, create):
                handle = original_area(ref, create=create)
                if not create:
                    area.rename(real_area)
                    area.symlink_to(outside, target_is_directory=True)
                return handle

            with patch.object(adapter, "_area", side_effect=swapped_area):
                result = adapter.read(reference)
            self.assertIsInstance(result, WorkspaceFailure)
            self.assertEqual(result.code, "WORKSPACE_STORAGE_ERROR")
            area.unlink()
            real_area.rename(area)
            self.assertEqual(adapter.read(reference), b"owned")

    def test_prepare_revalidates_all_held_area_handles_before_success(self):
        with TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "root"
            outside = base / "outside"
            outside.mkdir()
            adapter = FilesystemWorkspace(root)
            original_area = adapter._area
            opened = 0
            task = root / "tasks" / "task-prepare"
            task_real = root / "tasks" / "task-prepare-real"

            def swapped_after_area(reference, *, create):
                nonlocal opened
                handle = original_area(reference, create=create)
                opened += 1
                if opened == len(("media", "provider-records", "exports")):
                    task.rename(task_real)
                    task.symlink_to(outside, target_is_directory=True)
                return handle

            with patch.object(adapter, "_area", side_effect=swapped_after_area):
                result = adapter.prepare("task-prepare")
            self.assertIsInstance(result, WorkspaceFailure)
            self.assertEqual(result.code, "WORKSPACE_STORAGE_ERROR")
            task.unlink()
            task_real.rename(task)
            self.assertEqual(adapter.prepare("task-prepare"), TaskWorkspace("task-prepare", ("media", "provider-records", "exports")))

    def test_hardlink_tamper_is_rejected_and_cleaned_before_success(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            adapter = FilesystemWorkspace(root)
            adapter.prepare("task-link")
            reference = WorkspaceFileReference("task-link", "exports", "tampered.bin")
            real_link = os.link

            def tamper_after_link(source, destination, **kwargs):
                real_link(source, destination, **kwargs)
                destination_fd = kwargs["dst_dir_fd"]
                os.unlink(destination, dir_fd=destination_fd)
                fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=destination_fd)
                try:
                    os.write(fd, b"tampered")
                finally:
                    os.close(fd)

            with patch("ai_course_factory.persistence.workspace.os.link", side_effect=tamper_after_link):
                result = adapter.commit(reference, b"original")
            self.assertIsInstance(result, WorkspaceFailure)
            self.assertEqual(result.code, "WORKSPACE_STORAGE_ERROR")
            area = root / "tasks" / "task-link" / "exports"
            self.assertFalse((area / reference.name).exists())
            self.assertEqual(list(area.glob(".workspace-*")), [])
