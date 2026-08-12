"""Durable SQLite adapter for the Task projection seam."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from ai_course_factory.artifacts import ArtifactReference
from .task import (
    TaskArtifactSelection,
    TaskImpact,
    TaskOperationResult,
    TaskProjectionChange,
    TaskRepository,
    TaskRepositoryFailure,
    TaskSnapshot,
    _SAFE_FAILURE,
    _validate_change,
    _validate_id,
    _validate_impact,
    _validate_reference,
    _validate_snapshot,
    _validate_transition,
    _positive_int,
)

_SCHEMA_VERSION = 1
_STORAGE_FAILURE = TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)


class _StoredDataError(ValueError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _ref_value(reference: ArtifactReference) -> dict[str, Any]:
    return {"artifact_type": reference.artifact_type, "identity": reference.identity, "version": reference.version}


def _ref_from(value: Any) -> ArtifactReference:
    if not isinstance(value, dict) or set(value) != {"artifact_type", "identity", "version"}:
        raise _StoredDataError("invalid reference")
    reference = ArtifactReference(value["artifact_type"], value["identity"], value["version"])
    try:
        _validate_reference(reference)
    except Exception as exc:
        raise _StoredDataError("invalid reference") from exc
    return reference


def _selection_value(selection: TaskArtifactSelection) -> dict[str, Any]:
    return {"slot": selection.slot, "reference": _ref_value(selection.reference), "status": selection.status}


def _selection_from(value: Any) -> TaskArtifactSelection:
    if not isinstance(value, dict) or set(value) != {"slot", "reference", "status"}:
        raise _StoredDataError("invalid selection")
    if not isinstance(value["slot"], str) or value["status"] not in {"current", "stale"}:
        raise _StoredDataError("invalid selection")
    return TaskArtifactSelection(value["slot"], _ref_from(value["reference"]), value["status"])


def _snapshot_value(snapshot: TaskSnapshot) -> dict[str, Any]:
    return {
        "task_id": snapshot.task_id,
        "revision": snapshot.revision,
        "lifecycle_state": snapshot.lifecycle_state,
        "selections": [_selection_value(item) for item in snapshot.selections],
        "last_command_id": snapshot.last_command_id,
    }


def _snapshot_from(raw: Any) -> TaskSnapshot:
    if not isinstance(raw, str):
        raise _StoredDataError("invalid snapshot")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise _StoredDataError("invalid snapshot") from exc
    if not isinstance(value, dict) or set(value) != {"task_id", "revision", "lifecycle_state", "selections", "last_command_id"}:
        raise _StoredDataError("invalid snapshot")
    if (not isinstance(value["task_id"], str) or not _positive_int(value["revision"])
            or not isinstance(value["lifecycle_state"], str)
            or not isinstance(value["selections"], list)
            or not isinstance(value["last_command_id"], str)):
        raise _StoredDataError("invalid snapshot")
    snapshot = TaskSnapshot(value["task_id"], value["revision"], value["lifecycle_state"],
                            tuple(_selection_from(item) for item in value["selections"]), value["last_command_id"])
    if _validate_snapshot(snapshot) is not None:
        raise _StoredDataError("invalid snapshot")
    return snapshot


def _impact_value(impact: TaskImpact) -> dict[str, Any]:
    return {
        "task_id": impact.task_id,
        "slot": impact.slot,
        "previous_reference": None if impact.previous_reference is None else _ref_value(impact.previous_reference),
        "replacement_reference": _ref_value(impact.replacement_reference),
        "direct": [_selection_value(item) for item in impact.direct],
        "transitive": [_selection_value(item) for item in impact.transitive],
    }


def _impact_from(raw: Any, snapshot: TaskSnapshot) -> TaskImpact | None:
    if raw is None:
        return None
    if not isinstance(raw, str):
        raise _StoredDataError("invalid impact")
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise _StoredDataError("invalid impact") from exc
    expected = {"task_id", "slot", "previous_reference", "replacement_reference", "direct", "transitive"}
    if not isinstance(value, dict) or set(value) != expected or not isinstance(value["direct"], list) or not isinstance(value["transitive"], list):
        raise _StoredDataError("invalid impact")
    impact = TaskImpact(
        value["task_id"], value["slot"],
        None if value["previous_reference"] is None else _ref_from(value["previous_reference"]),
        _ref_from(value["replacement_reference"]),
        tuple(_selection_from(item) for item in value["direct"]),
        tuple(_selection_from(item) for item in value["transitive"]),
    )
    if _validate_impact(impact, snapshot) is not None:
        raise _StoredDataError("invalid impact")
    return impact


def _change_from(row: tuple[Any, ...]) -> tuple[TaskProjectionChange, TaskOperationResult]:
    if len(row) != 5 or not isinstance(row[0], str) or not isinstance(row[1], str):
        raise _StoredDataError("invalid command")
    expected = row[2]
    if expected is not None and not _positive_int(expected):
        raise _StoredDataError("invalid command")
    snapshot = _snapshot_from(row[3])
    impact = _impact_from(row[4], snapshot)
    change = TaskProjectionChange(row[1], row[0], expected, snapshot, impact)
    if _validate_change(change) is not None:
        raise _StoredDataError("invalid command")
    return change, TaskOperationResult("success", snapshot, impact)


def _verify_command_link(connection: sqlite3.Connection, snapshot: TaskSnapshot) -> None:
    row = connection.execute(
        "SELECT command_id, task_id, expected_revision, snapshot_json, impact_json "
        "FROM task_commands WHERE command_id=?",
        (snapshot.last_command_id,),
    ).fetchone()
    if row is None:
        raise _StoredDataError("snapshot command link is missing")
    stored, _ = _change_from(row)
    if stored.task_id != snapshot.task_id or stored.snapshot != snapshot:
        raise _StoredDataError("snapshot command link is inconsistent")


class SQLiteTaskRepository(TaskRepository):
    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure: TaskRepositoryFailure | None = None
        try:
            self._connection = sqlite3.connect(database_path, isolation_level=None, timeout=5.0)
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._initialize()
        except Exception:
            self._rollback_quietly()
            self._close_quietly()
            self._initialization_failure = _STORAGE_FAILURE

    def _initialize(self) -> None:
        connection = self._connection_or_raise()
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS task_schema (singleton INTEGER PRIMARY KEY CHECK(singleton=1), version INTEGER NOT NULL)")
        row = connection.execute("SELECT version FROM task_schema WHERE singleton=1").fetchone()
        if row is None:
            connection.execute("INSERT INTO task_schema(singleton, version) VALUES(1, ?)", (_SCHEMA_VERSION,))
        elif row[0] != _SCHEMA_VERSION:
            raise _StoredDataError("unsupported schema")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS task_revisions(
                task_id TEXT NOT NULL, revision INTEGER NOT NULL CHECK(revision > 0),
                snapshot_json TEXT NOT NULL, PRIMARY KEY(task_id, revision))
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS task_commands(
                command_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
                expected_revision INTEGER, snapshot_json TEXT NOT NULL, impact_json TEXT)
        """)
        connection.execute("COMMIT")

    def save(self, change: TaskProjectionChange) -> TaskOperationResult:
        invalid = _validate_change(change)
        if invalid is not None:
            return _failure(invalid)
        if self._initialization_failure is not None or self._connection is None:
            return _failure(_STORAGE_FAILURE)
        connection = self._connection
        try:
            connection.execute("BEGIN IMMEDIATE")
            current_row = connection.execute(
                "SELECT revision, snapshot_json FROM task_revisions WHERE task_id=? ORDER BY revision DESC LIMIT 1",
                (change.task_id,),
            ).fetchone()
            current = None
            if current_row is not None:
                if not _positive_int(current_row[0]):
                    raise _StoredDataError("invalid revision")
                current = _snapshot_from(current_row[1])
                if current.revision != current_row[0]:
                    raise _StoredDataError("revision mismatch")
                _verify_command_link(connection, current)
            row = connection.execute(
                "SELECT command_id, task_id, expected_revision, snapshot_json, impact_json FROM task_commands WHERE command_id=?",
                (change.command_id,),
            ).fetchone()
            if row is not None:
                stored, result = _change_from(row)
                linked = connection.execute(
                    "SELECT revision, snapshot_json FROM task_revisions WHERE task_id=? AND revision=?",
                    (stored.task_id, stored.snapshot.revision),
                ).fetchone()
                if linked is None or linked[0] != stored.snapshot.revision or _snapshot_from(linked[1]) != stored.snapshot:
                    raise _StoredDataError("command points to invalid revision")
                connection.execute("COMMIT")
                if stored == change:
                    return result
                return _failure(TaskRepositoryFailure("TASK_COMMAND_CONFLICT", "command identity was already used with different input"))
            if change.expected_revision is None:
                if current is not None:
                    connection.execute("ROLLBACK")
                    return _failure(TaskRepositoryFailure("TASK_ALREADY_EXISTS", "task identity already exists"))
            elif current is None:
                connection.execute("ROLLBACK")
                return _failure(TaskRepositoryFailure("TASK_NOT_FOUND", "task does not exist"))
            elif current.revision != change.expected_revision:
                connection.execute("ROLLBACK")
                return _failure(TaskRepositoryFailure("TASK_REVISION_CONFLICT", "task revision is no longer current"))
            elif change.snapshot.revision != current.revision + 1:
                raise _StoredDataError("invalid revision")
            transition = _validate_transition(current, change)
            if transition is not None:
                connection.execute("ROLLBACK")
                return _failure(transition)
            connection.execute(
                "INSERT INTO task_revisions(task_id, revision, snapshot_json) VALUES(?, ?, ?)",
                (change.task_id, change.snapshot.revision, _json(_snapshot_value(change.snapshot))),
            )
            connection.execute(
                "INSERT INTO task_commands(command_id, task_id, expected_revision, snapshot_json, impact_json) VALUES(?, ?, ?, ?, ?)",
                (change.command_id, change.task_id, change.expected_revision,
                 _json(_snapshot_value(change.snapshot)), None if change.impact is None else _json(_impact_value(change.impact))),
            )
            connection.execute("COMMIT")
            return TaskOperationResult("success", change.snapshot, change.impact)
        except _StoredDataError:
            self._rollback_quietly()
            return _failure(_STORAGE_FAILURE)
        except sqlite3.Error:
            self._rollback_quietly()
            return _failure(_STORAGE_FAILURE)
        except Exception:
            self._rollback_quietly()
            return _failure(_STORAGE_FAILURE)

    def get(self, task_id: str, revision: int | None = None) -> TaskSnapshot | TaskRepositoryFailure:
        invalid = _validate_id(task_id, "INVALID_TASK_ID", "task identity is required")
        if invalid is not None:
            return invalid
        if revision is not None and not _positive_int(revision):
            return TaskRepositoryFailure("INVALID_EXPECTED_REVISION", "task revision must be a positive integer")
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE
        try:
            if revision is None:
                row = self._connection.execute("SELECT revision, snapshot_json FROM task_revisions WHERE task_id=? ORDER BY revision DESC LIMIT 1", (task_id,)).fetchone()
            else:
                row = self._connection.execute("SELECT revision, snapshot_json FROM task_revisions WHERE task_id=? AND revision=?", (task_id, revision)).fetchone()
            if row is None:
                return TaskRepositoryFailure("TASK_NOT_FOUND", "task revision does not exist")
            if not _positive_int(row[0]):
                raise _StoredDataError("invalid revision")
            snapshot = _snapshot_from(row[1])
            if snapshot.task_id != task_id or snapshot.revision != row[0]:
                raise _StoredDataError("revision mismatch")
            _verify_command_link(self._connection, snapshot)
            return snapshot
        except Exception:
            return _STORAGE_FAILURE

    def close(self) -> None:
        self._close_quietly()

    def __enter__(self) -> "SQLiteTaskRepository":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def _connection_or_raise(self) -> sqlite3.Connection:
        if self._connection is None:
            raise _StoredDataError("connection unavailable")
        return self._connection

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


def _failure(failure: TaskRepositoryFailure) -> TaskOperationResult:
    return TaskOperationResult("failure", error_code=failure.code, error_message=failure.message)


__all__ = ["SQLiteTaskRepository"]
