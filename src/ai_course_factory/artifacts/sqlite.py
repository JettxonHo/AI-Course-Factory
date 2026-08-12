"""SQLite-backed Artifact repository with the in-memory boundary's semantics."""

from __future__ import annotations

import base64
import binascii
from collections.abc import Mapping
import json
import os
import re
import sqlite3
from typing import Any

from .commit import (
    ArtifactCommitError,
    ArtifactNotFoundError,
    ArtifactStorageError,
    CommitConflictError,
    _build_committed_version,
    _fingerprint,
    _is_valid_reference,
    _validate_candidate,
    _validate_revision,
)
from .model import ArtifactCandidate, ArtifactReference, ArtifactVersion, freeze_value


_SCHEMA_VERSION = 1
_INTEGER_RE = re.compile(r"^-?(0|[1-9][0-9]*)$")
_STORAGE_FAILURE = "artifact storage operation failed"


class _StoredDataError(ValueError):
    """Internal marker for malformed persisted values."""


def _json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _encode_value(value: Any) -> dict[str, Any]:
    """Encode a frozen Artifact value using an explicit, typed JSON shape."""

    if value is None:
        return {"t": "null"}
    if isinstance(value, bool):
        return {"t": "bool", "v": value}
    if isinstance(value, int):
        return {"t": "int", "v": str(value)}
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("non-finite float")
        return {"t": "float", "v": value.hex()}
    if isinstance(value, str):
        return {"t": "str", "v": value}
    if isinstance(value, bytes):
        return {"t": "bytes", "v": base64.b64encode(value).decode("ascii")}
    if isinstance(value, ArtifactReference):
        if not _is_valid_reference(value):
            raise ValueError("invalid Artifact Reference")
        return {
            "t": "reference",
            "artifact_type": value.artifact_type,
            "identity": value.identity,
            "version": value.version,
        }
    if isinstance(value, Mapping):
        entries = [
            {"k": _encode_value(key), "v": _encode_value(item)}
            for key, item in value.items()
        ]
        entries.sort(key=_json_text)
        return {"t": "mapping", "v": entries}
    if isinstance(value, tuple):
        return {"t": "tuple", "v": [_encode_value(item) for item in value]}
    if isinstance(value, frozenset):
        values = [_encode_value(item) for item in value]
        values.sort(key=_json_text)
        return {"t": "frozenset", "v": values}
    raise ValueError("unsupported Artifact value")


def _expect_keys(node: dict[str, Any], expected: set[str]) -> None:
    if set(node) != expected:
        raise _StoredDataError("invalid typed JSON keys")


def _decode_value(node: Any) -> Any:
    if not isinstance(node, dict) or not isinstance(node.get("t"), str):
        raise _StoredDataError("invalid typed JSON value")
    tag = node["t"]
    if tag == "null":
        _expect_keys(node, {"t"})
        return None
    if tag == "bool":
        _expect_keys(node, {"t", "v"})
        if not isinstance(node["v"], bool):
            raise _StoredDataError("invalid boolean")
        return node["v"]
    if tag == "int":
        _expect_keys(node, {"t", "v"})
        raw = node["v"]
        if not isinstance(raw, str) or _INTEGER_RE.fullmatch(raw) is None:
            raise _StoredDataError("invalid integer")
        try:
            return int(raw)
        except ValueError as exc:
            raise _StoredDataError("invalid integer") from exc
    if tag == "float":
        _expect_keys(node, {"t", "v"})
        raw = node["v"]
        if not isinstance(raw, str):
            raise _StoredDataError("invalid float")
        try:
            value = float.fromhex(raw)
        except ValueError as exc:
            raise _StoredDataError("invalid float") from exc
        if value != value or value in (float("inf"), float("-inf")):
            raise _StoredDataError("invalid float")
        return value
    if tag == "str":
        _expect_keys(node, {"t", "v"})
        if not isinstance(node["v"], str):
            raise _StoredDataError("invalid string")
        return node["v"]
    if tag == "bytes":
        _expect_keys(node, {"t", "v"})
        raw = node["v"]
        if not isinstance(raw, str):
            raise _StoredDataError("invalid bytes")
        try:
            return base64.b64decode(raw.encode("ascii"), validate=True)
        except (ValueError, UnicodeError, binascii.Error) as exc:
            raise _StoredDataError("invalid bytes") from exc
    if tag == "reference":
        _expect_keys(node, {"t", "artifact_type", "identity", "version"})
        reference = ArtifactReference(node["artifact_type"], node["identity"], node["version"])
        if not _is_valid_reference(reference):
            raise _StoredDataError("invalid Artifact Reference")
        return reference
    if tag in {"mapping", "tuple", "frozenset"}:
        _expect_keys(node, {"t", "v"})
        values = node["v"]
        if not isinstance(values, list):
            raise _StoredDataError("invalid container")
        if tag == "mapping":
            result: dict[Any, Any] = {}
            for entry in values:
                if not isinstance(entry, dict):
                    raise _StoredDataError("invalid mapping entry")
                _expect_keys(entry, {"k", "v"})
                key = _decode_value(entry["k"])
                item = _decode_value(entry["v"])
                try:
                    result[key] = item
                except TypeError as exc:
                    raise _StoredDataError("unhashable mapping key") from exc
            return freeze_value(result)
        decoded = [_decode_value(item) for item in values]
        if tag == "tuple":
            return tuple(decoded)
        try:
            return frozenset(decoded)
        except TypeError as exc:
            raise _StoredDataError("unhashable set value") from exc
    raise _StoredDataError("unknown typed JSON tag")


def _encode_json(value: Any) -> str:
    return _json_text(_encode_value(freeze_value(value)))


def _decode_json(raw: Any) -> Any:
    if not isinstance(raw, str):
        raise _StoredDataError("stored value is not text")
    try:
        node = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise _StoredDataError("stored value is not valid JSON") from exc
    return _decode_value(node)


def _safe_storage_error() -> ArtifactStorageError:
    return ArtifactStorageError(_STORAGE_FAILURE)


def _version_fingerprint(version: ArtifactVersion) -> tuple[Any, ...]:
    """Build the canonical logical-input tuple from persisted Version fields."""

    return (
        version.artifact_type,
        version.identity,
        freeze_value(version.payload),
        tuple(freeze_value(item) for item in version.provenance),
        tuple(version.dependencies),
        version.prior_reference,
    )


class SQLiteArtifactRepository:
    """Durable Artifact repository using one local SQLite database."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        try:
            path = os.fspath(database_path)
            connection = sqlite3.connect(path, isolation_level=None, timeout=5.0)
            connection.execute("PRAGMA foreign_keys = ON")
            self._connection = connection
            self._initialize()
        except ArtifactStorageError:
            self.close()
            raise
        except (OSError, TypeError, ValueError, sqlite3.Error):
            self.close()
            raise _safe_storage_error() from None

    def close(self) -> None:
        connection, self._connection = self._connection, None
        if connection is not None:
            try:
                connection.close()
            except sqlite3.Error:
                raise _safe_storage_error() from None

    def __enter__(self) -> "SQLiteArtifactRepository":
        if self._connection is None:
            raise _safe_storage_error()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        self.close()

    def _connection_or_raise(self) -> sqlite3.Connection:
        if self._connection is None:
            raise _safe_storage_error()
        return self._connection

    def _initialize(self) -> None:
        connection = self._connection_or_raise()
        try:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifact_schema (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    version INTEGER NOT NULL
                )
                """
            )
            row = connection.execute("SELECT version FROM artifact_schema WHERE singleton = 1").fetchone()
            if row is None:
                connection.execute(
                    "INSERT INTO artifact_schema(singleton, version) VALUES(1, ?)",
                    (_SCHEMA_VERSION,),
                )
            elif row[0] != _SCHEMA_VERSION:
                raise ArtifactStorageError(_STORAGE_FAILURE)
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifact_versions (
                    artifact_type TEXT NOT NULL,
                    identity TEXT NOT NULL,
                    version INTEGER NOT NULL CHECK (version > 0),
                    payload_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    dependencies_json TEXT NOT NULL,
                    commit_id TEXT NOT NULL,
                    prior_reference_json TEXT NOT NULL,
                    PRIMARY KEY (artifact_type, identity, version),
                    UNIQUE (artifact_type, identity, commit_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifact_logical_commits (
                    artifact_type TEXT NOT NULL,
                    identity TEXT NOT NULL,
                    commit_id TEXT NOT NULL,
                    fingerprint_json TEXT NOT NULL,
                    reference_artifact_type TEXT NOT NULL,
                    reference_identity TEXT NOT NULL,
                    reference_version INTEGER NOT NULL CHECK (reference_version > 0),
                    PRIMARY KEY (artifact_type, identity, commit_id),
                    FOREIGN KEY (
                        reference_artifact_type, reference_identity, reference_version
                    ) REFERENCES artifact_versions(artifact_type, identity, version)
                )
                """
            )
            connection.execute("COMMIT")
        except ArtifactStorageError:
            self._rollback_quietly()
            raise
        except sqlite3.Error:
            self._rollback_quietly()
            raise _safe_storage_error() from None

    def commit(self, candidate: ArtifactCandidate) -> ArtifactReference:
        """Validate and atomically persist a Candidate."""

        _validate_candidate(candidate)
        key = (candidate.artifact_type, candidate.identity)
        fingerprint = _fingerprint(candidate)
        fingerprint_json = _encode_json(fingerprint)
        connection = self._connection_or_raise()
        try:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT fingerprint_json, reference_artifact_type, reference_identity, reference_version
                FROM artifact_logical_commits
                WHERE artifact_type = ? AND identity = ? AND commit_id = ?
                """,
                (candidate.artifact_type, candidate.identity, candidate.commit_id),
            ).fetchone()
            if existing is not None:
                stored_fingerprint = _decode_json(existing[0])
                reference = ArtifactReference(existing[1], existing[2], existing[3])
                if not _is_valid_reference(reference):
                    raise _StoredDataError("invalid logical commit reference")
                if (reference.artifact_type, reference.identity) != key:
                    raise _StoredDataError("logical commit points to another Artifact")
                commit_row = connection.execute(
                    """
                    SELECT commit_id FROM artifact_versions
                    WHERE artifact_type = ? AND identity = ? AND version = ?
                    """,
                    (reference.artifact_type, reference.identity, reference.version),
                ).fetchone()
                if commit_row is None or commit_row[0] != candidate.commit_id:
                    raise _StoredDataError("logical commit points to invalid Version")
                # Validate the linked Version before replaying so corruption in
                # any persisted field cannot be hidden by a valid index row.
                stored_version = self.get(reference)
                canonical_fingerprint = _version_fingerprint(stored_version)
                if stored_fingerprint != canonical_fingerprint:
                    raise _StoredDataError("logical commit fingerprint disagrees with Version")
                if stored_fingerprint == fingerprint:
                    connection.execute("COMMIT")
                    return reference
                raise CommitConflictError("logical Commit identity conflicts with its original input")

            version_row = connection.execute(
                "SELECT COALESCE(MAX(version), 0) FROM artifact_versions WHERE artifact_type = ? AND identity = ?",
                key,
            ).fetchone()
            current_version = version_row[0] if version_row is not None else 0
            if not isinstance(current_version, int) or isinstance(current_version, bool) or current_version < 0:
                raise _StoredDataError("invalid version allocation")
            prior = candidate.prior_reference
            predecessor_exists = (
                prior is not None
                and connection.execute(
                    """
                    SELECT 1 FROM artifact_versions
                    WHERE artifact_type = ? AND identity = ? AND version = ?
                    """,
                    (prior.artifact_type, prior.identity, prior.version),
                ).fetchone()
                is not None
            )
            _validate_revision(candidate, key, current_version, predecessor_exists)
            reference = ArtifactReference(candidate.artifact_type, candidate.identity, current_version + 1)
            committed = _build_committed_version(candidate, reference)
            connection.execute(
                """
                INSERT INTO artifact_versions(
                    artifact_type, identity, version, payload_json, provenance_json,
                    dependencies_json, commit_id, prior_reference_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reference.artifact_type,
                    reference.identity,
                    reference.version,
                    _encode_json(committed.payload),
                    _encode_json(committed.provenance),
                    _encode_json(committed.dependencies),
                    committed.commit_id,
                    _encode_json(committed.prior_reference),
                ),
            )
            connection.execute(
                """
                INSERT INTO artifact_logical_commits(
                    artifact_type, identity, commit_id, fingerprint_json,
                    reference_artifact_type, reference_identity, reference_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    candidate.artifact_type,
                    candidate.identity,
                    candidate.commit_id,
                    fingerprint_json,
                    reference.artifact_type,
                    reference.identity,
                    reference.version,
                ),
            )
            connection.execute("COMMIT")
            return reference
        except ArtifactCommitError:
            self._rollback_quietly()
            raise
        except _StoredDataError:
            self._rollback_quietly()
            raise _safe_storage_error() from None
        except sqlite3.Error:
            self._rollback_quietly()
            raise _safe_storage_error() from None
        except (
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            OverflowError,
            binascii.Error,
        ):
            self._rollback_quietly()
            raise _safe_storage_error() from None
        except Exception:
            self._rollback_quietly()
            raise _safe_storage_error() from None

    def get(self, reference: ArtifactReference) -> ArtifactVersion:
        """Retrieve one immutable Version using its exact Reference."""

        if not _is_valid_reference(reference):
            raise ArtifactNotFoundError("an exact Artifact Reference is required")
        connection = self._connection_or_raise()
        try:
            row = connection.execute(
                """
                SELECT artifact_type, identity, version, payload_json, provenance_json,
                       dependencies_json, commit_id, prior_reference_json
                FROM artifact_versions
                WHERE artifact_type = ? AND identity = ? AND version = ?
                """,
                (reference.artifact_type, reference.identity, reference.version),
            ).fetchone()
            if row is None:
                raise ArtifactNotFoundError("the exact Artifact Reference does not exist")
            stored_reference = ArtifactReference(row[0], row[1], row[2])
            if stored_reference != reference or not _is_valid_reference(stored_reference):
                raise _StoredDataError("invalid stored Artifact Reference")
            payload = _decode_json(row[3])
            if payload is None:
                raise _StoredDataError("invalid stored Artifact payload")
            provenance = _decode_json(row[4])
            dependencies = _decode_json(row[5])
            prior_reference = _decode_json(row[7])
            if not isinstance(provenance, tuple) or not isinstance(dependencies, tuple):
                raise _StoredDataError("invalid stored Artifact collections")
            if not all(_is_valid_reference(item) for item in dependencies):
                raise _StoredDataError("invalid stored dependency")
            if stored_reference.version == 1:
                if prior_reference is not None:
                    raise _StoredDataError("invalid stored predecessor")
            elif (
                not _is_valid_reference(prior_reference)
                or prior_reference.artifact_type != stored_reference.artifact_type
                or prior_reference.identity != stored_reference.identity
                or prior_reference.version != stored_reference.version - 1
            ):
                raise _StoredDataError("invalid stored predecessor")
            if not isinstance(row[6], str) or not row[6].strip():
                raise _StoredDataError("invalid stored commit identity")
            return ArtifactVersion(
                reference=stored_reference,
                payload=payload,
                provenance=provenance,
                dependencies=dependencies,
                commit_id=row[6],
                prior_reference=prior_reference,
            )
        except ArtifactCommitError:
            raise
        except (
            sqlite3.Error,
            _StoredDataError,
            KeyError,
            IndexError,
            TypeError,
            ValueError,
            OverflowError,
            binascii.Error,
        ):
            raise _safe_storage_error() from None
        except Exception:
            raise _safe_storage_error() from None

    def _rollback_quietly(self) -> None:
        connection = self._connection
        if connection is None:
            return
        try:
            connection.execute("ROLLBACK")
        except sqlite3.Error:
            pass


__all__ = ["SQLiteArtifactRepository"]
