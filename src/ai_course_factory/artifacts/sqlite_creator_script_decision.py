"""Additive SQLite persistence for Creator Script Package decisions."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from .creator_script_decision import (
    CreatorScriptDecisionFailure,
    CreatorScriptDecisionRecord,
    validate_creator_script_decision_record,
)
from .model import ArtifactReference


_STORAGE_FAILURE = CreatorScriptDecisionFailure("execution", "CREATOR_SCRIPT_DECISION_FAILED", "creator Script decision persistence failed")


class SQLiteCreatorScriptDecisionRepository:
    """Durable repository using a creator-specific additive table."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure: CreatorScriptDecisionFailure | None = None
        try:
            if not isinstance(database_path, (str, os.PathLike)):
                raise TypeError
            self._connection = sqlite3.connect(os.fspath(database_path), isolation_level=None, timeout=5.0)
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._initialize_schema()
        except Exception:
            self._close_quietly()
            self._initialization_failure = _STORAGE_FAILURE

    def save(self, record: CreatorScriptDecisionRecord) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        invalid = validate_creator_script_decision_record(record)
        if invalid is not None:
            return invalid
        if self._connection is None or self._initialization_failure is not None:
            return _STORAGE_FAILURE
        try:
            row = self._connection.execute(
                "SELECT decision_id, task_id, thread_id, creator_id, gate_kind, source_artifact_type, source_identity, source_version, script_artifact_type, script_identity, script_version, script_package_id, action, decision_context FROM creator_script_decisions WHERE decision_id = ?",
                (record.decision_id,),
            ).fetchone()
            if row is not None:
                existing = self._decode(row)
                if existing == record:
                    return existing
                return CreatorScriptDecisionFailure("validation", "DECISION_CONFLICT", "decision identity was already used with different input")
            self._connection.execute(
                "INSERT INTO creator_script_decisions (decision_id, task_id, thread_id, creator_id, gate_kind, source_artifact_type, source_identity, source_version, script_artifact_type, script_identity, script_version, script_package_id, action, decision_context) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                self._values(record),
            )
            return record
        except Exception:
            return _STORAGE_FAILURE

    def get(self, decision_id: str) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        if not isinstance(decision_id, str) or not decision_id.strip():
            return CreatorScriptDecisionFailure("validation", "INVALID_DECISION_ID", "decision identity is required")
        if self._connection is None or self._initialization_failure is not None:
            return _STORAGE_FAILURE
        try:
            row = self._connection.execute(
                "SELECT decision_id, task_id, thread_id, creator_id, gate_kind, source_artifact_type, source_identity, source_version, script_artifact_type, script_identity, script_version, script_package_id, action, decision_context FROM creator_script_decisions WHERE decision_id = ?",
                (decision_id,),
            ).fetchone()
            if row is None:
                return CreatorScriptDecisionFailure("validation", "DECISION_NOT_FOUND", "decision record does not exist")
            return self._decode(row)
        except Exception:
            return _STORAGE_FAILURE

    def count(self) -> int:
        if self._connection is None:
            return 0
        try:
            return int(self._connection.execute("SELECT COUNT(*) FROM creator_script_decisions").fetchone()[0])
        except Exception:
            return 0

    def close(self) -> None:
        self._close_quietly()

    def __enter__(self) -> "SQLiteCreatorScriptDecisionRepository":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def _initialize_schema(self) -> None:
        if self._connection is None:
            raise RuntimeError
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS creator_script_decision_schema (singleton INTEGER PRIMARY KEY CHECK(singleton = 1), version INTEGER NOT NULL)"
        )
        row = self._connection.execute("SELECT version FROM creator_script_decision_schema WHERE singleton = 1").fetchone()
        if row is None:
            self._connection.execute("INSERT INTO creator_script_decision_schema(singleton, version) VALUES(1, 1)")
        elif row[0] != 1:
            raise ValueError("unsupported Creator Script decision schema")
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS creator_script_decisions (decision_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, thread_id TEXT NOT NULL, creator_id TEXT NOT NULL, gate_kind TEXT NOT NULL, source_artifact_type TEXT NOT NULL, source_identity TEXT NOT NULL, source_version INTEGER NOT NULL, script_artifact_type TEXT NOT NULL, script_identity TEXT NOT NULL, script_version INTEGER NOT NULL, script_package_id TEXT NOT NULL, action TEXT NOT NULL, decision_context TEXT NOT NULL)"
        )

    @staticmethod
    def _values(record: CreatorScriptDecisionRecord) -> tuple[Any, ...]:
        return (
            record.decision_id,
            record.task_id,
            record.thread_id,
            record.creator_id,
            record.gate_kind,
            record.source_reference.artifact_type,
            record.source_reference.identity,
            record.source_reference.version,
            record.script_reference.artifact_type,
            record.script_reference.identity,
            record.script_reference.version,
            record.script_package_id,
            record.action,
            record.decision_context,
        )

    @staticmethod
    def _decode(row: tuple[Any, ...]) -> CreatorScriptDecisionRecord:
        if len(row) != 14:
            raise ValueError("stored creator Script decision row is malformed")
        record = CreatorScriptDecisionRecord(
            row[0], row[1], row[2], row[3], row[4],
            ArtifactReference(row[5], row[6], row[7]),
            ArtifactReference(row[8], row[9], row[10]),
            row[11], row[12], row[13],
        )
        if validate_creator_script_decision_record(record) is not None:
            raise ValueError("stored creator Script decision is invalid")
        return record

    def _close_quietly(self) -> None:
        if self._connection is None:
            return
        try:
            self._connection.close()
        except Exception:
            pass
        finally:
            self._connection = None


__all__ = ["SQLiteCreatorScriptDecisionRepository"]
