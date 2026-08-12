"""SQLite persistence adapter for immutable Storyboard decision records."""

from __future__ import annotations

import os
import sqlite3
from typing import Any

from .model import ArtifactReference
from .storyboard_decision import (
    StoryboardDecisionBoundary,
    StoryboardDecisionFailure,
    StoryboardDecisionRecord,
    _validate_decision_record,
)


_SCHEMA_VERSION = 1
_STORAGE_FAILURE = StoryboardDecisionFailure(
    "execution",
    "STORYBOARD_DECISION_FAILED",
    "storyboard decision persistence failed",
)


class SQLiteStoryboardDecisionRepository:
    """Durable standard-library SQLite implementation of the decision seam."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure: StoryboardDecisionFailure | None = None
        try:
            if not isinstance(database_path, (str, os.PathLike)):
                raise TypeError("database path is invalid")
            self._connection = sqlite3.connect(database_path, timeout=5.0)
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._initialize_schema()
        except Exception:
            self._rollback_quietly()
            self._close_quietly()
            self._initialization_failure = _STORAGE_FAILURE

    def save(
        self, record: StoryboardDecisionRecord
    ) -> StoryboardDecisionRecord | StoryboardDecisionFailure:
        """Persist one immutable decision or return a bounded failure."""

        invalid = _validate_decision_record(record)
        if invalid is not None:
            return invalid
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE

        connection = self._connection
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                """
                SELECT decision_id, task_id, thread_id, creator_id, gate_kind,
                       storyboard_artifact_type, storyboard_identity, storyboard_version,
                       script_artifact_type, script_identity, script_version,
                       character_artifact_type, character_identity, character_version,
                       script_approval_decision_id, review_enabled, action, decision_context
                FROM storyboard_decisions
                WHERE decision_id = ?
                """,
                (record.decision_id,),
            ).fetchone()
            if row is not None:
                existing = self._decode_row(row)
                connection.rollback()
                if existing == record:
                    return existing
                return StoryboardDecisionFailure(
                    "validation",
                    "DECISION_CONFLICT",
                    "decision identity was already used with different input",
                )

            connection.execute(
                """
                INSERT INTO storyboard_decisions (
                    decision_id, task_id, thread_id, creator_id, gate_kind,
                    storyboard_artifact_type, storyboard_identity, storyboard_version,
                    script_artifact_type, script_identity, script_version,
                    character_artifact_type, character_identity, character_version,
                    script_approval_decision_id, review_enabled, action, decision_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._row_values(record),
            )
            connection.commit()
            return record
        except Exception:
            self._rollback_quietly()
            return _STORAGE_FAILURE

    def get(self, decision_id: str) -> StoryboardDecisionRecord | StoryboardDecisionFailure:
        """Retrieve one exact decision identity without exposing SQLite errors."""

        if not isinstance(decision_id, str) or not StoryboardDecisionBoundary._valid_identity(decision_id):
            return StoryboardDecisionFailure(
                "validation", "INVALID_DECISION_ID", "decision identity is required"
            )
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE

        try:
            row = self._connection.execute(
                """
                SELECT decision_id, task_id, thread_id, creator_id, gate_kind,
                       storyboard_artifact_type, storyboard_identity, storyboard_version,
                       script_artifact_type, script_identity, script_version,
                       character_artifact_type, character_identity, character_version,
                       script_approval_decision_id, review_enabled, action, decision_context
                FROM storyboard_decisions
                WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()
            if row is None:
                return StoryboardDecisionFailure(
                    "validation", "DECISION_NOT_FOUND", "decision record does not exist"
                )
            return self._decode_row(row)
        except Exception:
            return _STORAGE_FAILURE

    def close(self) -> None:
        """Close the local database connection; later calls fail safely."""

        self._close_quietly()

    def __enter__(self) -> "SQLiteStoryboardDecisionRepository":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def _initialize_schema(self) -> None:
        if self._connection is None:
            raise RuntimeError("connection is unavailable")
        connection = self._connection
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS storyboard_decision_schema (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL
            )
            """
        )
        row = connection.execute(
            "SELECT version FROM storyboard_decision_schema WHERE singleton = 1"
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO storyboard_decision_schema (singleton, version) VALUES (1, ?)",
                (_SCHEMA_VERSION,),
            )
        elif row[0] != _SCHEMA_VERSION:
            raise ValueError("unsupported Storyboard decision schema")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS storyboard_decisions (
                decision_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                gate_kind TEXT NOT NULL,
                storyboard_artifact_type TEXT NOT NULL,
                storyboard_identity TEXT NOT NULL,
                storyboard_version INTEGER NOT NULL,
                script_artifact_type TEXT NOT NULL,
                script_identity TEXT NOT NULL,
                script_version INTEGER NOT NULL,
                character_artifact_type TEXT NOT NULL,
                character_identity TEXT NOT NULL,
                character_version INTEGER NOT NULL,
                script_approval_decision_id TEXT NOT NULL,
                review_enabled INTEGER NOT NULL,
                action TEXT NOT NULL,
                decision_context TEXT NOT NULL
            )
            """
        )
        connection.commit()

    @staticmethod
    def _row_values(record: StoryboardDecisionRecord) -> tuple[Any, ...]:
        def reference_values(reference: ArtifactReference) -> tuple[Any, ...]:
            return reference.artifact_type, reference.identity, reference.version

        return (
            record.decision_id,
            record.task_id,
            record.thread_id,
            record.creator_id,
            record.gate_kind,
            *reference_values(record.storyboard_reference),
            *reference_values(record.script_reference),
            *reference_values(record.character_reference),
            record.script_approval_decision_id,
            int(record.review_enabled),
            record.action,
            record.decision_context,
        )

    @staticmethod
    def _decode_row(row: tuple[Any, ...]) -> StoryboardDecisionRecord:
        if len(row) != 18:
            raise ValueError("stored Storyboard decision row is malformed")
        if row[15] not in (0, 1):
            raise ValueError("stored Storyboard review mode is malformed")
        record = StoryboardDecisionRecord(
            decision_id=row[0],
            task_id=row[1],
            thread_id=row[2],
            creator_id=row[3],
            gate_kind=row[4],
            storyboard_reference=ArtifactReference(row[5], row[6], row[7]),
            script_reference=ArtifactReference(row[8], row[9], row[10]),
            character_reference=ArtifactReference(row[11], row[12], row[13]),
            script_approval_decision_id=row[14],
            review_enabled=bool(row[15]),
            action=row[16],
            decision_context=row[17],
        )
        invalid = _validate_decision_record(record)
        if invalid is not None:
            raise ValueError("stored Storyboard decision is invalid")
        return record

    def _rollback_quietly(self) -> None:
        if self._connection is None:
            return
        try:
            self._connection.rollback()
        except Exception:
            pass

    def _close_quietly(self) -> None:
        if self._connection is None:
            return
        try:
            self._connection.close()
        except Exception:
            pass
        finally:
            self._connection = None


__all__ = ["SQLiteStoryboardDecisionRepository"]
