"""SQLite persistence adapter for immutable Script decision records."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from .model import ArtifactReference
from .script_decision import (
    ScriptDecisionFailure,
    ScriptDecisionRecord,
    _validate_decision_record,
)


_SCHEMA_VERSION = 1
_STORAGE_FAILURE = ScriptDecisionFailure(
    "execution",
    "SCRIPT_DECISION_FAILED",
    "script decision persistence failed",
)


class SQLiteScriptDecisionRepository:
    """Durable standard-library SQLite implementation of the decision seam."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure: ScriptDecisionFailure | None = None
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

    def save(self, record: ScriptDecisionRecord) -> ScriptDecisionRecord | ScriptDecisionFailure:
        """Persist one immutable decision, or return a bounded failure."""

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
                       script_artifact_type, script_identity, script_version,
                       knowledge_artifact_type, knowledge_identity, knowledge_version,
                       course_plan_artifact_type, course_plan_identity, course_plan_version,
                       episode_plan_artifact_type, episode_plan_identity, episode_plan_version,
                       assessment_disposition, finding_codes_json, action, decision_context
                FROM script_decisions
                WHERE decision_id = ?
                """,
                (record.decision_id,),
            ).fetchone()
            if row is not None:
                existing = self._decode_row(row)
                connection.rollback()
                if existing == record:
                    return existing
                return ScriptDecisionFailure(
                    "validation",
                    "DECISION_CONFLICT",
                    "decision identity was already used with different input",
                )

            connection.execute(
                """
                INSERT INTO script_decisions (
                    decision_id, task_id, thread_id, creator_id, gate_kind,
                    script_artifact_type, script_identity, script_version,
                    knowledge_artifact_type, knowledge_identity, knowledge_version,
                    course_plan_artifact_type, course_plan_identity, course_plan_version,
                    episode_plan_artifact_type, episode_plan_identity, episode_plan_version,
                    assessment_disposition, finding_codes_json, action, decision_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._row_values(record),
            )
            connection.commit()
            return record
        except Exception:
            self._rollback_quietly()
            return _STORAGE_FAILURE

    def get(self, decision_id: str) -> ScriptDecisionRecord | ScriptDecisionFailure:
        """Retrieve one exact decision identity without exposing SQLite errors."""

        if not isinstance(decision_id, str) or not decision_id.strip():
            return ScriptDecisionFailure(
                "validation", "INVALID_DECISION_ID", "decision identity is required"
            )
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE

        try:
            row = self._connection.execute(
                """
                SELECT decision_id, task_id, thread_id, creator_id, gate_kind,
                       script_artifact_type, script_identity, script_version,
                       knowledge_artifact_type, knowledge_identity, knowledge_version,
                       course_plan_artifact_type, course_plan_identity, course_plan_version,
                       episode_plan_artifact_type, episode_plan_identity, episode_plan_version,
                       assessment_disposition, finding_codes_json, action, decision_context
                FROM script_decisions
                WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()
            if row is None:
                return ScriptDecisionFailure(
                    "validation", "DECISION_NOT_FOUND", "decision record does not exist"
                )
            return self._decode_row(row)
        except Exception:
            return _STORAGE_FAILURE

    def close(self) -> None:
        """Close the local database connection; later calls fail safely."""

        self._close_quietly()

    def __enter__(self) -> "SQLiteScriptDecisionRepository":
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
            CREATE TABLE IF NOT EXISTS script_decision_schema (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL
            )
            """
        )
        row = connection.execute(
            "SELECT version FROM script_decision_schema WHERE singleton = 1"
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO script_decision_schema (singleton, version) VALUES (1, ?)",
                (_SCHEMA_VERSION,),
            )
        elif row[0] != _SCHEMA_VERSION:
            raise ValueError("unsupported Script decision schema")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS script_decisions (
                decision_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                gate_kind TEXT NOT NULL,
                script_artifact_type TEXT NOT NULL,
                script_identity TEXT NOT NULL,
                script_version INTEGER NOT NULL,
                knowledge_artifact_type TEXT NOT NULL,
                knowledge_identity TEXT NOT NULL,
                knowledge_version INTEGER NOT NULL,
                course_plan_artifact_type TEXT NOT NULL,
                course_plan_identity TEXT NOT NULL,
                course_plan_version INTEGER NOT NULL,
                episode_plan_artifact_type TEXT NOT NULL,
                episode_plan_identity TEXT NOT NULL,
                episode_plan_version INTEGER NOT NULL,
                assessment_disposition TEXT NOT NULL,
                finding_codes_json TEXT NOT NULL,
                action TEXT NOT NULL,
                decision_context TEXT NOT NULL
            )
            """
        )
        connection.commit()

    @staticmethod
    def _row_values(record: ScriptDecisionRecord) -> tuple[Any, ...]:
        def reference_values(reference: ArtifactReference) -> tuple[Any, ...]:
            return reference.artifact_type, reference.identity, reference.version

        return (
            record.decision_id,
            record.task_id,
            record.thread_id,
            record.creator_id,
            record.gate_kind,
            *reference_values(record.script_reference),
            *reference_values(record.knowledge_reference),
            *reference_values(record.course_plan_reference),
            *reference_values(record.episode_plan_reference),
            record.assessment_disposition,
            json.dumps(
                list(record.finding_codes), ensure_ascii=False, separators=(",", ":")
            ),
            record.action,
            record.decision_context,
        )

    @staticmethod
    def _decode_row(row: tuple[Any, ...]) -> ScriptDecisionRecord:
        if len(row) != 21:
            raise ValueError("stored Script decision row is malformed")
        finding_codes = json.loads(row[18])
        if not isinstance(finding_codes, list):
            raise ValueError("stored finding codes are malformed")
        record = ScriptDecisionRecord(
            decision_id=row[0],
            task_id=row[1],
            thread_id=row[2],
            creator_id=row[3],
            gate_kind=row[4],
            script_reference=ArtifactReference(row[5], row[6], row[7]),
            knowledge_reference=ArtifactReference(row[8], row[9], row[10]),
            course_plan_reference=ArtifactReference(row[11], row[12], row[13]),
            episode_plan_reference=ArtifactReference(row[14], row[15], row[16]),
            assessment_disposition=row[17],
            finding_codes=tuple(finding_codes),
            action=row[19],
            decision_context=row[20],
        )
        invalid = _validate_decision_record(record)
        if invalid is not None:
            raise ValueError("stored Script decision is invalid")
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

__all__ = ["SQLiteScriptDecisionRepository"]
