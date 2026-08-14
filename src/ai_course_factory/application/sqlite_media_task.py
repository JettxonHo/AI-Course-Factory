"""SQLite adapter for the additive Task media projection."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from ai_course_factory.artifacts import ArtifactReference

from .media_task import (
    InMemoryTaskMediaRepository,
    TaskDeliveryMediaSelection,
    TaskMediaImpact,
    TaskMediaBatchImpact,
    TaskMediaOperationResult,
    TaskMediaProjectionChange,
    TaskMediaRepository,
    TaskMediaRepositoryFailure,
    TaskMediaSnapshot,
    TaskSceneMediaSelection,
    _DELIVERY_ROLES,
    _SCENE_ROLES,
    _validate_change,
    _validate_impact,
    _validate_snapshot,
    _validate_transition,
    _same_change,
    _same_snapshot,
    _id,
    _positive,
)

_SCHEMA_VERSION = 1
_SAFE = "task media repository operation failed"


class _StoredDataError(ValueError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _ref_value(value: ArtifactReference) -> dict[str, Any]:
    return {"artifact_type": value.artifact_type, "identity": value.identity, "version": value.version}


def _ref_from(value: Any) -> ArtifactReference:
    if type(value) is not dict or set(value) != {"artifact_type", "identity", "version"}:
        raise _StoredDataError("invalid reference")
    reference = ArtifactReference(value["artifact_type"], value["identity"], value["version"])
    if type(reference.artifact_type) is not str or type(reference.identity) is not str or not _positive(reference.version):
        raise _StoredDataError("invalid reference")
    return reference


def _scene_value(value: TaskSceneMediaSelection) -> dict[str, Any]:
    return {"scene_id": value.scene_id, "role": value.role, "reference": _ref_value(value.reference), "status": value.status}


def _scene_from(value: Any) -> TaskSceneMediaSelection:
    if type(value) is not dict or set(value) != {"scene_id", "role", "reference", "status"}:
        raise _StoredDataError("invalid scene selection")
    result = TaskSceneMediaSelection(value["scene_id"], value["role"], _ref_from(value["reference"]), value["status"])
    if type(result.scene_id) is not str or type(result.role) is not str or type(result.status) is not str:
        raise _StoredDataError("invalid scene selection")
    return result


def _delivery_value(value: TaskDeliveryMediaSelection) -> dict[str, Any]:
    return {"role": value.role, "reference": _ref_value(value.reference), "status": value.status}


def _delivery_from(value: Any) -> TaskDeliveryMediaSelection:
    if type(value) is not dict or set(value) != {"role", "reference", "status"}:
        raise _StoredDataError("invalid delivery selection")
    result = TaskDeliveryMediaSelection(value["role"], _ref_from(value["reference"]), value["status"])
    if type(result.role) is not str or type(result.status) is not str:
        raise _StoredDataError("invalid delivery selection")
    return result


def _snapshot_value(value: TaskMediaSnapshot) -> dict[str, Any]:
    return {
        "task_id": value.task_id,
        "revision": value.revision,
        "lifecycle_state": value.lifecycle_state,
        "production_request_reference": _ref_value(value.production_request_reference),
        "timeline_reference": _ref_value(value.timeline_reference),
        "scene_ids": list(value.scene_ids),
        "scene_selections": [_scene_value(item) for item in value.scene_selections],
        "delivery_selections": [_delivery_value(item) for item in value.delivery_selections],
        "last_command_id": value.last_command_id,
    }


def _load_json(raw: Any, label: str) -> Any:
    if type(raw) is not str:
        raise _StoredDataError(f"invalid {label}")
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        raise _StoredDataError(f"invalid {label}") from None


def _snapshot_from(raw: Any) -> TaskMediaSnapshot:
    value = _load_json(raw, "snapshot")
    expected = {
        "task_id", "revision", "lifecycle_state", "production_request_reference", "timeline_reference",
        "scene_ids", "scene_selections", "delivery_selections", "last_command_id",
    }
    if type(value) is not dict or set(value) != expected or type(value["scene_ids"]) is not list or type(value["scene_selections"]) is not list or type(value["delivery_selections"]) is not list:
        raise _StoredDataError("invalid snapshot")
    snapshot = TaskMediaSnapshot(
        value["task_id"], value["revision"], value["lifecycle_state"],
        _ref_from(value["production_request_reference"]), _ref_from(value["timeline_reference"]),
        tuple(value["scene_ids"]), tuple(_scene_from(item) for item in value["scene_selections"]),
        tuple(_delivery_from(item) for item in value["delivery_selections"]), value["last_command_id"],
    )
    try:
        _validate_snapshot(snapshot)
    except Exception:
        raise _StoredDataError("invalid snapshot") from None
    return snapshot


def _impact_value(value: TaskMediaImpact | TaskMediaBatchImpact) -> dict[str, Any]:
    if type(value) is TaskMediaBatchImpact:
        return {
            "discriminator": "batch",
            "task_id": value.task_id,
            "operations": [_impact_value(item) for item in value.operations],
        }
    return {
        "task_id": value.task_id,
        "role": value.role,
        "scene_id": value.scene_id,
        "previous_reference": None if value.previous_reference is None else _ref_value(value.previous_reference),
        "replacement_reference": _ref_value(value.replacement_reference),
        "direct": [_scene_value(item) if type(item) is TaskSceneMediaSelection else _delivery_value(item) for item in value.direct],
        "transitive": [_scene_value(item) if type(item) is TaskSceneMediaSelection else _delivery_value(item) for item in value.transitive],
    }


def _impact_from(raw: Any, snapshot: TaskMediaSnapshot) -> TaskMediaImpact | TaskMediaBatchImpact | None:
    if raw is None:
        return None
    value = _load_json(raw, "impact")
    if type(value) is dict and value.get("discriminator") == "batch":
        if set(value) != {"discriminator", "task_id", "operations"} or type(value["operations"]) is not list:
            raise _StoredDataError("invalid batch impact")
        operations = tuple(_impact_from(_json(item), snapshot) for item in value["operations"])
        if any(type(item) is not TaskMediaImpact for item in operations):
            raise _StoredDataError("invalid batch impact")
        batch = TaskMediaBatchImpact(value["task_id"], operations)
        return batch
    expected = {"task_id", "role", "scene_id", "previous_reference", "replacement_reference", "direct", "transitive"}
    if type(value) is not dict or set(value) != expected or type(value["direct"]) is not list or type(value["transitive"]) is not list:
        raise _StoredDataError("invalid impact")
    def selection(item: Any) -> TaskSceneMediaSelection | TaskDeliveryMediaSelection:
        if type(item) is not dict:
            raise _StoredDataError("invalid impact selection")
        if set(item) == {"scene_id", "role", "reference", "status"}:
            return _scene_from(item)
        if set(item) == {"role", "reference", "status"}:
            return _delivery_from(item)
        raise _StoredDataError("invalid impact selection")
    impact = TaskMediaImpact(
        value["task_id"], value["role"], value["scene_id"],
        None if value["previous_reference"] is None else _ref_from(value["previous_reference"]),
        _ref_from(value["replacement_reference"]), tuple(selection(item) for item in value["direct"]),
        tuple(selection(item) for item in value["transitive"]),
    )
    try:
        _validate_impact(impact, snapshot)
    except Exception:
        raise _StoredDataError("invalid impact") from None
    return impact


def _change_from(row: tuple[Any, ...]) -> tuple[TaskMediaProjectionChange, TaskMediaOperationResult]:
    if len(row) != 5 or type(row[0]) is not str or type(row[1]) is not str:
        raise _StoredDataError("invalid command")
    expected = row[2]
    if expected is not None and not _positive(expected):
        raise _StoredDataError("invalid command")
    snapshot = _snapshot_from(row[3])
    impact = _impact_from(row[4], snapshot)
    change = TaskMediaProjectionChange(row[1], row[0], expected, snapshot, impact)
    try:
        _validate_change(change)
    except Exception:
        raise _StoredDataError("invalid command") from None
    return change, TaskMediaOperationResult("success", snapshot, impact)


class SQLiteTaskMediaRepository(TaskMediaRepository):
    """Durable SQLite implementation using additive task-media tables only."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure = False
        try:
            self._connection = sqlite3.connect(os.fspath(database_path), isolation_level=None, timeout=5.0, check_same_thread=False)
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._initialize()
        except Exception:
            self._rollback_quietly()
            self._close_quietly()
            self._initialization_failure = True

    def _initialize(self) -> None:
        connection = self._connection_or_raise()
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS task_media_schema (singleton INTEGER PRIMARY KEY CHECK(singleton=1), version INTEGER NOT NULL)")
        row = connection.execute("SELECT version FROM task_media_schema WHERE singleton=1").fetchone()
        if row is None:
            connection.execute("INSERT INTO task_media_schema(singleton, version) VALUES(1, ?)", (_SCHEMA_VERSION,))
        elif type(row[0]) is not int or row[0] != _SCHEMA_VERSION:
            raise _StoredDataError("unsupported schema")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS task_media_revisions(
                task_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
                snapshot_json TEXT NOT NULL, PRIMARY KEY(task_id, revision))
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS task_media_commands(
                command_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
                expected_revision INTEGER, snapshot_json TEXT NOT NULL, impact_json TEXT)
        """)
        connection.execute("COMMIT")

    def _connection_or_raise(self) -> sqlite3.Connection:
        if self._connection is None:
            raise _StoredDataError("connection unavailable")
        return self._connection

    def save(self, change: TaskMediaProjectionChange) -> TaskMediaOperationResult:
        try:
            _validate_change(change)
        except Exception:
            return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_REPOSITORY_FAILED", error_message=_SAFE)
        if self._initialization_failure or self._connection is None:
            return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_REPOSITORY_FAILED", error_message=_SAFE)
        connection = self._connection
        try:
            connection.execute("BEGIN IMMEDIATE")
            current_row = connection.execute("SELECT revision, snapshot_json FROM task_media_revisions WHERE task_id=? ORDER BY revision DESC LIMIT 1", (change.task_id,)).fetchone()
            current = None
            if current_row is not None:
                if not _positive(current_row[0]):
                    raise _StoredDataError("invalid revision")
                current = _snapshot_from(current_row[1])
                if current.task_id != change.task_id or current.revision != current_row[0]:
                    raise _StoredDataError("invalid revision")
                self._verify_command_link(connection, current)
            row = connection.execute("SELECT command_id, task_id, expected_revision, snapshot_json, impact_json FROM task_media_commands WHERE command_id=?", (change.command_id,)).fetchone()
            if row is not None:
                stored, result = _change_from(row)
                linked = connection.execute("SELECT revision, snapshot_json FROM task_media_revisions WHERE task_id=? AND revision=?", (stored.task_id, stored.snapshot.revision)).fetchone()
                if linked is None or linked[0] != stored.snapshot.revision or not _same_snapshot(_snapshot_from(linked[1]), stored.snapshot):
                    raise _StoredDataError("command points to invalid revision")
                connection.execute("COMMIT")
                if _same_change(stored, change):
                    return result
                return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_COMMAND_CONFLICT", error_message="command identity was already used with different input")
            if change.expected_revision is None:
                if current is not None:
                    connection.execute("ROLLBACK")
                    return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_ALREADY_EXISTS", error_message="task media projection already exists")
            elif current is None:
                connection.execute("ROLLBACK")
                return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_NOT_FOUND", error_message="task media projection does not exist")
            elif current.revision != change.expected_revision:
                connection.execute("ROLLBACK")
                return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_REVISION_CONFLICT", error_message="task media revision is no longer current")
            _validate_transition(current, change)
            connection.execute("INSERT INTO task_media_revisions(task_id, revision, snapshot_json) VALUES(?, ?, ?)", (change.task_id, change.snapshot.revision, _json(_snapshot_value(change.snapshot))))
            connection.execute("INSERT INTO task_media_commands(command_id, task_id, expected_revision, snapshot_json, impact_json) VALUES(?, ?, ?, ?, ?)", (change.command_id, change.task_id, change.expected_revision, _json(_snapshot_value(change.snapshot)), None if change.impact is None else _json(_impact_value(change.impact))))
            connection.execute("COMMIT")
            return TaskMediaOperationResult("success", change.snapshot, change.impact)
        except _StoredDataError:
            self._rollback_quietly()
            return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_REPOSITORY_FAILED", error_message=_SAFE)
        except Exception as exc:
            self._rollback_quietly()
            code = getattr(exc, "code", None)
            message = getattr(exc, "message", None)
            if type(code) is str and type(message) is str:
                return TaskMediaOperationResult("failure", error_code=code, error_message=message)
            return TaskMediaOperationResult("failure", error_code="TASK_MEDIA_REPOSITORY_FAILED", error_message=_SAFE)

    def get(self, task_id: str, revision: int | None = None) -> TaskMediaSnapshot | TaskMediaRepositoryFailure:
        try:
            _id(task_id, "INVALID_TASK_ID")
            if revision is not None and not _positive(revision):
                return TaskMediaRepositoryFailure("INVALID_EXPECTED_REVISION", "revision is invalid")
        except Exception as exc:
            return TaskMediaRepositoryFailure(getattr(exc, "code", "TASK_MEDIA_REPOSITORY_FAILED"), getattr(exc, "message", _SAFE))
        if self._initialization_failure or self._connection is None:
            return TaskMediaRepositoryFailure("TASK_MEDIA_REPOSITORY_FAILED", _SAFE)
        try:
            if revision is None:
                row = self._connection.execute("SELECT revision, snapshot_json FROM task_media_revisions WHERE task_id=? ORDER BY revision DESC LIMIT 1", (task_id,)).fetchone()
            else:
                row = self._connection.execute("SELECT revision, snapshot_json FROM task_media_revisions WHERE task_id=? AND revision=?", (task_id, revision)).fetchone()
            if row is None:
                return TaskMediaRepositoryFailure("TASK_MEDIA_NOT_FOUND", "task media revision does not exist")
            if not _positive(row[0]):
                raise _StoredDataError("invalid revision")
            snapshot = _snapshot_from(row[1])
            if snapshot.task_id != task_id or snapshot.revision != row[0]:
                raise _StoredDataError("revision mismatch")
            self._verify_command_link(self._connection, snapshot)
            return snapshot
        except Exception:
            return TaskMediaRepositoryFailure("TASK_MEDIA_REPOSITORY_FAILED", _SAFE)

    def _verify_command_link(self, connection: sqlite3.Connection, snapshot: TaskMediaSnapshot) -> None:
        row = connection.execute("SELECT command_id, task_id, expected_revision, snapshot_json, impact_json FROM task_media_commands WHERE command_id=?", (snapshot.last_command_id,)).fetchone()
        if row is None:
            raise _StoredDataError("snapshot command link is missing")
        change, _ = _change_from(row)
        if change.task_id != snapshot.task_id or not _same_snapshot(change.snapshot, snapshot):
            raise _StoredDataError("snapshot command link is inconsistent")

    def close(self) -> None:
        self._close_quietly()

    def __enter__(self) -> "SQLiteTaskMediaRepository":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def _rollback_quietly(self) -> None:
        if self._connection is not None:
            try:
                self._connection.rollback()
            except sqlite3.Error:
                pass

    def _close_quietly(self) -> None:
        connection, self._connection = self._connection, None
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:
                pass


__all__ = ["SQLiteTaskMediaRepository"]
