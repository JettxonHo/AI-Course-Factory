"""Durable standard-library SQLite persistence for Final Video decisions."""

from __future__ import annotations

import json
import os
import sqlite3
from typing import Any

from .final_video_decision import (
    FinalVideoDecisionBoundary,
    FinalVideoDecisionFailure,
    FinalVideoDecisionRecord,
    _validate_record,
)
from .model import ArtifactReference


_SCHEMA_VERSION = 1
_STORAGE_FAILURE = FinalVideoDecisionFailure(
    "execution", "FINAL_VIDEO_DECISION_FAILED", "final video decision persistence failed"
)


class SQLiteFinalVideoDecisionRepository:
    """Persist immutable Final Video decision records without media payloads."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure: FinalVideoDecisionFailure | None = None
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

    def save(self, record: FinalVideoDecisionRecord) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure:
        invalid = _validate_record(record)
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
                       video_artifact_type, video_identity, video_version,
                       assessment_disposition, finding_codes_json, action, decision_context
                FROM final_video_decisions WHERE decision_id = ?
                """,
                (record.decision_id,),
            ).fetchone()
            if row is not None:
                existing = self._decode_row(row)
                connection.rollback()
                if existing == record:
                    return existing
                return FinalVideoDecisionFailure(
                    "validation", "DECISION_CONFLICT", "decision identity was already used with different input"
                )
            connection.execute(
                """
                INSERT INTO final_video_decisions (
                    decision_id, task_id, thread_id, creator_id, gate_kind,
                    video_artifact_type, video_identity, video_version,
                    assessment_disposition, finding_codes_json, action, decision_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._row_values(record),
            )
            connection.commit()
            return record
        except Exception:
            self._rollback_quietly()
            return _STORAGE_FAILURE

    def get(self, decision_id: str) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure:
        try:
            FinalVideoDecisionBoundary._validate_identity(decision_id)
        except Exception:
            return FinalVideoDecisionFailure(
                "validation", "INVALID_DECISION_ID", "decision identity is required"
            )
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE
        try:
            row = self._connection.execute(
                """
                SELECT decision_id, task_id, thread_id, creator_id, gate_kind,
                       video_artifact_type, video_identity, video_version,
                       assessment_disposition, finding_codes_json, action, decision_context
                FROM final_video_decisions WHERE decision_id = ?
                """,
                (decision_id,),
            ).fetchone()
            if row is None:
                return FinalVideoDecisionFailure(
                    "validation", "DECISION_NOT_FOUND", "decision record does not exist"
                )
            return self._decode_row(row)
        except Exception:
            return _STORAGE_FAILURE

    def close(self) -> None:
        self._close_quietly()

    def __enter__(self) -> "SQLiteFinalVideoDecisionRepository":
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
            CREATE TABLE IF NOT EXISTS final_video_decision_schema (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL
            )
            """
        )
        row = connection.execute(
            "SELECT version FROM final_video_decision_schema WHERE singleton = 1"
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO final_video_decision_schema (singleton, version) VALUES (1, ?)",
                (_SCHEMA_VERSION,),
            )
        elif row[0] != _SCHEMA_VERSION:
            raise ValueError("unsupported Final Video decision schema")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS final_video_decisions (
                decision_id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                thread_id TEXT NOT NULL,
                creator_id TEXT NOT NULL,
                gate_kind TEXT NOT NULL,
                video_artifact_type TEXT NOT NULL,
                video_identity TEXT NOT NULL,
                video_version INTEGER NOT NULL,
                assessment_disposition TEXT NOT NULL,
                finding_codes_json TEXT NOT NULL,
                action TEXT NOT NULL,
                decision_context TEXT NOT NULL
            )
            """
        )
        connection.commit()

    @staticmethod
    def _row_values(record: FinalVideoDecisionRecord) -> tuple[Any, ...]:
        reference = record.video_reference
        return (
            record.decision_id,
            record.task_id,
            record.thread_id,
            record.creator_id,
            record.gate_kind,
            reference.artifact_type,
            reference.identity,
            reference.version,
            record.assessment_disposition,
            json.dumps(list(record.finding_codes), ensure_ascii=False, separators=(",", ":")),
            record.action,
            record.decision_context,
        )

    @staticmethod
    def _decode_row(row: tuple[Any, ...]) -> FinalVideoDecisionRecord:
        if len(row) != 12:
            raise ValueError("stored Final Video decision row is malformed")
        finding_codes = json.loads(row[9])
        if not isinstance(finding_codes, list):
            raise ValueError("stored finding codes are malformed")
        record = FinalVideoDecisionRecord(
            decision_id=row[0],
            task_id=row[1],
            thread_id=row[2],
            creator_id=row[3],
            gate_kind=row[4],
            video_reference=ArtifactReference(row[5], row[6], row[7]),
            assessment_disposition=row[8],
            finding_codes=tuple(finding_codes),
            action=row[10],
            decision_context=row[11],
        )
        invalid = _validate_record(record)
        if invalid is not None:
            raise ValueError("stored Final Video decision is invalid")
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


__all__ = ["SQLiteFinalVideoDecisionRepository"]
