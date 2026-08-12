"""Bounded task-scoped filesystem storage for opaque local blobs."""

from __future__ import annotations

import os
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

_AREAS = ("media", "provider-records", "exports")
_MAX_COMPONENT = 128
_ASCII_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
_MESSAGES = {
    "INVALID_WORKSPACE_TASK_ID": "workspace task identity is invalid",
    "INVALID_WORKSPACE_AREA": "workspace area is invalid",
    "INVALID_WORKSPACE_FILE_NAME": "workspace file name is invalid",
    "INVALID_WORKSPACE_REFERENCE": "workspace file reference is invalid",
    "INVALID_WORKSPACE_CONTENT": "workspace content must be exact bytes",
    "WORKSPACE_FILE_NOT_FOUND": "workspace file was not found",
    "WORKSPACE_FILE_CONFLICT": "workspace file reference conflicts with committed bytes",
    "WORKSPACE_STORAGE_ERROR": "workspace storage operation failed",
}


@dataclass(frozen=True, slots=True)
class TaskWorkspace:
    task_id: str
    areas: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "areas", tuple(self.areas))


WorkspaceArea = Literal["media", "provider-records", "exports"]


@dataclass(frozen=True, slots=True)
class WorkspaceFileReference:
    task_id: str
    area: WorkspaceArea
    name: str


@dataclass(frozen=True, slots=True)
class WorkspaceFileRecord:
    reference: WorkspaceFileReference
    size_bytes: int


@dataclass(frozen=True, slots=True)
class WorkspaceFailure:
    code: str
    message: str


@runtime_checkable
class WorkspaceAdapter(Protocol):
    def prepare(self, task_id: str) -> TaskWorkspace | WorkspaceFailure: ...

    def commit(self, reference: WorkspaceFileReference, content: bytes) -> WorkspaceFileRecord | WorkspaceFailure: ...

    def read(self, reference: WorkspaceFileReference) -> bytes | WorkspaceFailure: ...


class _MissingPath(Exception):
    pass


class _StorageError(Exception):
    pass


def _failure(code: str) -> WorkspaceFailure:
    return WorkspaceFailure(code, _MESSAGES[code])


def _valid_component(value: object, *, allow_colon: bool) -> bool:
    if type(value) is not str or not value or len(value) > _MAX_COMPONENT:
        return False
    if value.lower() == "latest" or value in {".", ".."}:
        return False
    if value[0] not in _ASCII_ALNUM:
        return False
    allowed = _ASCII_ALNUM | frozenset("._-")
    if allow_colon:
        allowed = allowed | {":"}
    return all(char in allowed for char in value)


def _validate_task_id(task_id: object) -> WorkspaceFailure | None:
    return None if _valid_component(task_id, allow_colon=True) else _failure("INVALID_WORKSPACE_TASK_ID")


def _validate_area(area: object) -> WorkspaceFailure | None:
    return None if type(area) is str and area in _AREAS else _failure("INVALID_WORKSPACE_AREA")


def _validate_name(name: object) -> WorkspaceFailure | None:
    return None if _valid_component(name, allow_colon=False) else _failure("INVALID_WORKSPACE_FILE_NAME")


def _validate_reference(reference: object) -> WorkspaceFailure | None:
    if not isinstance(reference, WorkspaceFileReference):
        return _failure("INVALID_WORKSPACE_REFERENCE")
    return (_validate_task_id(reference.task_id)
            or _validate_area(reference.area)
            or _validate_name(reference.name))


def _directory_flags() -> int:
    return (os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0))


def _read_flags() -> int:
    return os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


def _close_fd(fd: int | None) -> None:
    if fd is not None:
        try:
            os.close(fd)
        except OSError:
            pass


def _same_directory(first: int, second: int) -> bool:
    left, right = os.fstat(first), os.fstat(second)
    return (stat.S_ISDIR(left.st_mode) and stat.S_ISDIR(right.st_mode)
            and left.st_dev == right.st_dev and left.st_ino == right.st_ino)


def _open_child(parent_fd: int, name: str, *, create: bool) -> int:
    flags = _directory_flags()
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        if not create:
            raise _MissingPath from None
        try:
            os.mkdir(name, 0o700, dir_fd=parent_fd)
        except FileExistsError:
            pass
        try:
            return os.open(name, flags, dir_fd=parent_fd)
        except FileNotFoundError:
            raise _MissingPath from None
        except OSError:
            raise _StorageError from None
    except OSError:
        raise _StorageError from None


class _AreaHandle:
    """Open descriptors for the owned root/tasks/task/area chain."""

    __slots__ = ("root_path", "task_id", "area", "root_fd", "tasks_fd", "task_fd", "area_fd", "closed")

    def __init__(self, root_path: Path, task_id: str, area: str,
                 root_fd: int, tasks_fd: int, task_fd: int, area_fd: int) -> None:
        self.root_path = root_path
        self.task_id = task_id
        self.area = area
        self.root_fd = root_fd
        self.tasks_fd = tasks_fd
        self.task_fd = task_fd
        self.area_fd = area_fd
        self.closed = False

    def __enter__(self) -> "_AreaHandle":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        _close_fd(self.area_fd)
        _close_fd(self.task_fd)
        _close_fd(self.tasks_fd)
        _close_fd(self.root_fd)

    def assert_current(self) -> None:
        if self.closed:
            raise _StorageError
        check_root: int | None = None
        check_tasks: int | None = None
        check_task: int | None = None
        check_area: int | None = None
        try:
            try:
                check_root = os.open(self.root_path, _directory_flags())
            except OSError:
                raise _StorageError from None
            check_tasks = _open_child(check_root, "tasks", create=False)
            check_task = _open_child(check_tasks, self.task_id, create=False)
            check_area = _open_child(check_task, self.area, create=False)
            if not (_same_directory(self.root_fd, check_root)
                    and _same_directory(self.tasks_fd, check_tasks)
                    and _same_directory(self.task_fd, check_task)
                    and _same_directory(self.area_fd, check_area)):
                raise _StorageError
        finally:
            _close_fd(check_area)
            _close_fd(check_task)
            _close_fd(check_tasks)
            _close_fd(check_root)


class FilesystemWorkspace:
    """Own exactly one fixed task directory tree beneath a trusted root."""

    def __init__(self, root: str | os.PathLike[str] = ".ai-course-factory") -> None:
        try:
            self._root: Path | None = Path(root)
        except (TypeError, ValueError, OSError):
            self._root = None

    def prepare(self, task_id: str) -> TaskWorkspace | WorkspaceFailure:
        invalid = _validate_task_id(task_id)
        if invalid is not None:
            return invalid
        handles: list[_AreaHandle] = []
        try:
            for area in _AREAS:
                handles.append(self._area(
                    WorkspaceFileReference(task_id, area, "placeholder"), create=True
                ))
            for handle in handles:
                handle.assert_current()
            return TaskWorkspace(task_id, _AREAS)
        except Exception:
            return _failure("WORKSPACE_STORAGE_ERROR")
        finally:
            for handle in handles:
                handle.close()

    def commit(self, reference: WorkspaceFileReference, content: bytes) -> WorkspaceFileRecord | WorkspaceFailure:
        invalid = _validate_reference(reference)
        if invalid is not None:
            return invalid
        if type(content) is not bytes:
            return _failure("INVALID_WORKSPACE_CONTENT")
        handle: _AreaHandle | None = None
        temporary: str | None = None
        created = False
        success = False
        try:
            handle = self._area(reference, create=False)
            handle.assert_current()
            if _existing_file(handle.area_fd, reference.name, missing_ok=True) is not None:
                result = _record_or_conflict(handle.area_fd, reference, content)
                handle.assert_current()
                success = True
                return result

            temporary, fd = _create_temporary(handle.area_fd)
            try:
                _write_exact(fd, content)
                os.fsync(fd)
                temporary_info = os.fstat(fd)
            finally:
                _close_fd(fd)
            try:
                os.link(temporary, reference.name, src_dir_fd=handle.area_fd,
                        dst_dir_fd=handle.area_fd, follow_symlinks=False)
                created = True
            except FileExistsError:
                result = _record_or_conflict(handle.area_fd, reference, content)
                handle.assert_current()
                success = True
                return result
            _verify_link(handle.area_fd, reference.name, temporary_info, content)
            _unlink_relative(handle.area_fd, temporary)
            temporary = None
            handle.assert_current()
            success = True
            return WorkspaceFileRecord(reference, len(content))
        except _MissingPath:
            return _failure("WORKSPACE_STORAGE_ERROR")
        except Exception:
            return _failure("WORKSPACE_STORAGE_ERROR")
        finally:
            if handle is not None:
                if not success and created:
                    _unlink_quietly(handle.area_fd, reference.name)
                if temporary is not None:
                    _unlink_quietly(handle.area_fd, temporary)
                handle.close()

    def read(self, reference: WorkspaceFileReference) -> bytes | WorkspaceFailure:
        invalid = _validate_reference(reference)
        if invalid is not None:
            return invalid
        handle: _AreaHandle | None = None
        try:
            handle = self._area(reference, create=False)
            handle.assert_current()
            _existing_file(handle.area_fd, reference.name, missing_ok=False)
            content = _read_relative(handle.area_fd, reference.name)
            handle.assert_current()
            return content
        except _MissingPath:
            return _failure("WORKSPACE_FILE_NOT_FOUND")
        except FileNotFoundError:
            return _failure("WORKSPACE_FILE_NOT_FOUND")
        except Exception:
            return _failure("WORKSPACE_STORAGE_ERROR")
        finally:
            if handle is not None:
                handle.close()

    def _area(self, reference: WorkspaceFileReference, *, create: bool) -> _AreaHandle:
        if self._root is None:
            raise _StorageError
        root_path = self._root
        if create:
            try:
                root_path.mkdir(parents=True, exist_ok=True)
            except OSError:
                raise _StorageError from None
        try:
            root_fd = os.open(root_path, _directory_flags())
        except FileNotFoundError:
            raise _MissingPath from None
        except OSError:
            raise _StorageError from None
        tasks_fd: int | None = None
        task_fd: int | None = None
        area_fd: int | None = None
        try:
            tasks_fd = _open_child(root_fd, "tasks", create=create)
            task_fd = _open_child(tasks_fd, reference.task_id, create=create)
            area_fd = _open_child(task_fd, reference.area, create=create)
            return _AreaHandle(root_path, reference.task_id, reference.area,
                               root_fd, tasks_fd, task_fd, area_fd)
        except Exception:
            _close_fd(area_fd)
            _close_fd(task_fd)
            _close_fd(tasks_fd)
            _close_fd(root_fd)
            raise


def _existing_file(area_fd: int, name: str, *, missing_ok: bool) -> os.stat_result | None:
    try:
        info = os.lstat(name, dir_fd=area_fd)
    except FileNotFoundError:
        if missing_ok:
            return None
        raise _MissingPath from None
    except OSError:
        raise _StorageError from None
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
        raise _StorageError
    return info


def _create_temporary(area_fd: int) -> tuple[str, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    for _ in range(32):
        name = f".workspace-{uuid.uuid4().hex}"
        try:
            return name, os.open(name, flags, 0o600, dir_fd=area_fd)
        except FileExistsError:
            continue
        except OSError:
            raise _StorageError from None
    raise _StorageError


def _write_exact(fd: int, content: bytes) -> None:
    view = memoryview(content)
    while view:
        try:
            written = os.write(fd, view)
        except OSError:
            raise _StorageError from None
        if not isinstance(written, int) or written <= 0 or written > len(view):
            raise _StorageError
        view = view[written:]


def _unlink_relative(area_fd: int, name: str) -> None:
    try:
        os.unlink(name, dir_fd=area_fd)
    except OSError:
        raise _StorageError from None


def _unlink_quietly(area_fd: int, name: str) -> None:
    try:
        os.unlink(name, dir_fd=area_fd)
    except OSError:
        pass


def _record_or_conflict(area_fd: int, reference: WorkspaceFileReference,
                        content: bytes) -> WorkspaceFileRecord | WorkspaceFailure:
    stored = _read_relative(area_fd, reference.name)
    if stored == content:
        return WorkspaceFileRecord(reference, len(stored))
    return _failure("WORKSPACE_FILE_CONFLICT")


def _verify_link(area_fd: int, name: str, temporary_info: os.stat_result,
                 content: bytes) -> None:
    info = _existing_file(area_fd, name, missing_ok=False)
    if (info is None or info.st_dev != temporary_info.st_dev
            or info.st_ino != temporary_info.st_ino
            or info.st_size != len(content) or _read_relative(area_fd, name) != content):
        raise _StorageError


def _read_relative(area_fd: int, name: str) -> bytes:
    try:
        fd = os.open(name, _read_flags(), dir_fd=area_fd)
    except FileNotFoundError:
        raise _MissingPath from None
    except OSError:
        raise _StorageError from None
    try:
        info = os.fstat(fd)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise _StorageError
        chunks: list[bytes] = []
        while True:
            try:
                chunk = os.read(fd, 1024 * 1024)
            except OSError:
                raise _StorageError from None
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    finally:
        _close_fd(fd)


__all__ = [
    "FilesystemWorkspace", "TaskWorkspace", "WorkspaceAdapter", "WorkspaceFailure",
    "WorkspaceFileRecord", "WorkspaceFileReference",
]
