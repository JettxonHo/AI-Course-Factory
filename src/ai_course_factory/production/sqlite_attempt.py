"""Durable SQLite implementation of the Provider-attempt repository."""

from __future__ import annotations

from datetime import datetime
import json
import os
import sqlite3
from typing import Any

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference

from .attempt import (
    ProviderAttemptClaim,
    ProviderAttemptFailure,
    ProviderAttemptOutcome,
    ProviderAttemptRecord,
    ProviderAttemptRepository,
    ProviderAttemptReservation,
    _STORAGE,
    _auth_fp,
    _authorization,
    _bad,
    _outcome,
    _record,
    _reservation,
    _same_outcome,
    _static,
    _terminal_record,
    _workspace,
)
from .budget import BudgetAuthorizationRecord, PriceLineItem, PriceSnapshot

_SCHEMA_VERSION = 1
_MAX_JSON = 32768
_SCHEMA_COLUMNS = "singleton, version"
_COLUMNS = """attempt_id, task_id, authorization_id,
request_artifact_type, request_identity, request_version,
budget_artifact_type, budget_identity, budget_version,
scene_id, operation, provider, attempt_number, idempotency_key,
request_task_id, request_area, request_name, currency,
reserved_amount_micros, status, reserved_at, completed_at,
charged_amount_micros, result_code, response_task_id, response_area,
response_name, output_references_json, authorization_fingerprint_json"""
_COLUMN_COUNT = 29


def _json(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    if len(encoded) > _MAX_JSON:
        raise ValueError
    return encoded


def _ref_payload(reference: WorkspaceFileReference) -> dict[str, str]:
    return {"task_id": reference.task_id, "area": reference.area, "name": reference.name}


def _auth_payload(auth: BudgetAuthorizationRecord) -> dict[str, object]:
    snapshot = auth.price_snapshot
    return {
        "authorization_id": auth.authorization_id,
        "decision_id": auth.decision_id,
        "task_id": auth.task_id,
        "thread_id": auth.thread_id,
        "creator_id": auth.creator_id,
        "production_request_reference": {
            "artifact_type": auth.production_request_reference.artifact_type,
            "identity": auth.production_request_reference.identity,
            "version": auth.production_request_reference.version,
        },
        "budget_reference": {
            "artifact_type": auth.budget_reference.artifact_type,
            "identity": auth.budget_reference.identity,
            "version": auth.budget_reference.version,
        },
        "currency": auth.currency,
        "maximum_approved_amount_micros": auth.maximum_approved_amount_micros,
        "maximum_attempts": auth.maximum_attempts,
        "decided_at": auth.decided_at.isoformat(),
        "snapshot_id": snapshot.snapshot_id,
        "snapshot_source": snapshot.source,
        "snapshot_currency": snapshot.currency,
        "snapshot_production_request_reference": {
            "artifact_type": snapshot.production_request_reference.artifact_type,
            "identity": snapshot.production_request_reference.identity,
            "version": snapshot.production_request_reference.version,
        },
        "line_items": [
            {
                "scene_id": item.scene_id,
                "operation": item.operation,
                "unit": item.unit,
                "quantity": item.quantity,
                "unit_price_micros": item.unit_price_micros,
            }
            for item in snapshot.line_items
        ],
    }


def _auth_json(auth: BudgetAuthorizationRecord) -> str:
    return _json(_auth_payload(auth))


def _output_json(references: tuple[WorkspaceFileReference, ...]) -> str:
    return _json([_ref_payload(reference) for reference in references])


def _decode_output(value: object) -> tuple[WorkspaceFileReference, ...]:
    if not isinstance(value, str) or len(value) > _MAX_JSON:
        raise ValueError
    decoded = json.loads(value)
    if not isinstance(decoded, list) or _json(decoded) != value:
        raise ValueError
    result: list[WorkspaceFileReference] = []
    for item in decoded:
        if not isinstance(item, dict) or set(item) != {"task_id", "area", "name"}:
            raise ValueError
        result.append(WorkspaceFileReference(item["task_id"], item["area"], item["name"]))
    if len(set(result)) != len(result):
        raise ValueError
    return tuple(result)


def _decode_auth_fingerprint(value: object) -> tuple[BudgetAuthorizationRecord, str]:
    if not isinstance(value, str) or len(value) > _MAX_JSON:
        raise ValueError
    decoded = json.loads(value)
    required = {
        "authorization_id", "decision_id", "task_id", "thread_id", "creator_id",
        "production_request_reference", "budget_reference", "currency",
        "maximum_approved_amount_micros", "maximum_attempts", "decided_at", "snapshot_id",
        "snapshot_source", "snapshot_currency", "snapshot_production_request_reference", "line_items",
    }
    if not isinstance(decoded, dict) or set(decoded) != required or _json(decoded) != value:
        raise ValueError
    for key in ("authorization_id", "decision_id", "task_id", "thread_id", "creator_id", "currency", "decided_at", "snapshot_id", "snapshot_source", "snapshot_currency"):
        if not isinstance(decoded[key], str) or not decoded[key]:
            raise ValueError
    for key in ("production_request_reference", "budget_reference", "snapshot_production_request_reference"):
        reference = decoded[key]
        if not isinstance(reference, dict) or set(reference) != {"artifact_type", "identity", "version"} or not isinstance(reference["artifact_type"], str) or not isinstance(reference["identity"], str) or type(reference["version"]) is not int or reference["version"] < 1:
            raise ValueError
    if decoded["production_request_reference"]["artifact_type"] != "production_request" or decoded["budget_reference"]["artifact_type"] != "production_budget" or decoded["snapshot_production_request_reference"] != decoded["production_request_reference"]:
        raise ValueError
    if type(decoded["maximum_approved_amount_micros"]) is not int or not 1 <= decoded["maximum_approved_amount_micros"] <= 2**63 - 1 or type(decoded["maximum_attempts"]) is not int or not 1 <= decoded["maximum_attempts"] <= 3:
        raise ValueError
    items = decoded["line_items"]
    if not isinstance(items, list) or not items or len(items) % 2 or any(not isinstance(item, dict) or set(item) != {"scene_id", "operation", "unit", "quantity", "unit_price_micros"} for item in items):
        raise ValueError
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(items):
        if not all(isinstance(item[key], str) and item[key] for key in ("scene_id", "operation", "unit")) or item["operation"] not in {"visual", "voice"} or type(item["quantity"]) is not int or item["quantity"] < 1 or type(item["unit_price_micros"]) is not int or item["unit_price_micros"] < 1:
            raise ValueError
        key = (item["scene_id"], item["operation"])
        if key in seen or (index % 2 == 0 and item["operation"] != "visual") or (index % 2 == 1 and (item["operation"] != "voice" or item["scene_id"] != items[index - 1]["scene_id"])):
            raise ValueError
        seen.add(key)
    try:
        request = ArtifactReference(**decoded["production_request_reference"])
        budget = ArtifactReference(**decoded["budget_reference"])
        snapshot_reference = ArtifactReference(**decoded["snapshot_production_request_reference"])
        snapshot = PriceSnapshot(
            decoded["snapshot_id"],
            decoded["snapshot_source"],
            decoded["snapshot_currency"],
            snapshot_reference,
            tuple(PriceLineItem(**item) for item in decoded["line_items"]),
        )
        authorization = BudgetAuthorizationRecord(
            decoded["authorization_id"], decoded["decision_id"], decoded["task_id"],
            decoded["thread_id"], decoded["creator_id"], request, budget, snapshot,
            decoded["currency"], decoded["maximum_approved_amount_micros"],
            decoded["maximum_attempts"], datetime.fromisoformat(decoded["decided_at"]),
        )
        _authorization(authorization)
        if _auth_json(authorization) != value:
            raise ValueError
    except Exception as exc:
        raise ValueError from exc
    return authorization, value


def _row_values(record: ProviderAttemptRecord, auth_json: str) -> tuple[Any, ...]:
    request = record.production_request_reference
    budget = record.budget_reference
    request_file = record.request_record_reference
    response = record.response_record_reference
    return (
        record.attempt_id, record.task_id, record.authorization_id,
        request.artifact_type, request.identity, request.version,
        budget.artifact_type, budget.identity, budget.version,
        record.scene_id, record.operation, record.provider, record.attempt_number,
        record.idempotency_key, request_file.task_id, request_file.area, request_file.name,
        record.currency, record.reserved_amount_micros, record.status,
        record.reserved_at.isoformat(), record.completed_at.isoformat() if record.completed_at else None,
        record.charged_amount_micros, record.result_code,
        response.task_id if response else None, response.area if response else None,
        response.name if response else None, _output_json(record.output_references), auth_json,
    )


def _decode_row(row: tuple[Any, ...]) -> tuple[ProviderAttemptRecord, BudgetAuthorizationRecord, str]:
    if len(row) != _COLUMN_COUNT:
        raise ValueError
    request = ArtifactReference(row[3], row[4], row[5])
    budget = ArtifactReference(row[6], row[7], row[8])
    response_values = row[24:27]
    if any(value is None for value in response_values) and not all(value is None for value in response_values):
        raise ValueError
    response = None if all(value is None for value in response_values) else WorkspaceFileReference(*response_values)
    record = ProviderAttemptRecord(
        row[0], row[1], row[2], request, budget, row[9], row[10], row[11], row[12], row[13],
        WorkspaceFileReference(row[14], row[15], row[16]), row[17], row[18], row[19],
        datetime.fromisoformat(row[20]), datetime.fromisoformat(row[21]) if row[21] else None,
        row[22], row[23], response, _decode_output(row[27]),
    )
    record = _record(record)
    authorization, auth_json = _decode_auth_fingerprint(row[28])
    if (
        record.authorization_id != authorization.authorization_id
        or record.task_id != authorization.task_id
        or record.production_request_reference != authorization.production_request_reference
        or record.budget_reference != authorization.budget_reference
        or record.currency != authorization.currency
    ):
        raise ValueError
    amounts = _authorization(authorization)[1]
    if amounts.get((record.scene_id, record.operation)) != record.reserved_amount_micros or record.attempt_number > authorization.maximum_attempts:
        raise ValueError
    return record, authorization, auth_json


def _validate_group(rows: list[tuple[ProviderAttemptRecord, BudgetAuthorizationRecord, str]]) -> None:
    if not rows:
        return
    first = rows[0]
    authorization_id, fingerprint, authorization = first[0].authorization_id, first[2], first[1]
    if any(record.authorization_id != authorization_id or stored != fingerprint for record, _auth, stored in rows):
        raise ValueError
    if sum(record.reserved_amount_micros for record, _auth, _stored in rows) > authorization.maximum_approved_amount_micros:
        raise ValueError
    scopes: dict[tuple[str, str], list[ProviderAttemptRecord]] = {}
    for record, _auth, _stored in rows:
        scopes.setdefault((record.scene_id, record.operation), []).append(record)
    for records in scopes.values():
        numbers = sorted(record.attempt_number for record in records)
        if numbers != list(range(1, len(records) + 1)) or any(record.status != "failed" for record in sorted(records, key=lambda item: item.attempt_number)[:-1]):
            raise ValueError


class SQLiteProviderAttemptRepository(ProviderAttemptRepository):
    """SQLite adapter with explicit schema and atomic reservation transactions."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure = False
        try:
            path = os.fspath(database_path)
            connection = sqlite3.connect(path, timeout=5.0, isolation_level=None, check_same_thread=False)
            connection.execute("PRAGMA foreign_keys = ON")
            self._connection = connection
            self._initialize()
        except Exception:
            self._rollback_quietly(); self._close_quietly(); self._initialization_failure = True

    def close(self) -> None:
        self._close_quietly()

    def __enter__(self) -> "SQLiteProviderAttemptRepository":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def reserve(self, reservation: ProviderAttemptReservation, authorization: BudgetAuthorizationRecord) -> ProviderAttemptRecord | ProviderAttemptFailure:
        result = self.claim(reservation, authorization)
        return result.record if isinstance(result, ProviderAttemptClaim) else result

    def claim(self, reservation: ProviderAttemptReservation, authorization: BudgetAuthorizationRecord) -> ProviderAttemptClaim | ProviderAttemptFailure:
        try:
            reservation = _reservation(reservation); authorization, amounts = _authorization(authorization)
            if reservation.task_id != authorization.task_id or reservation.authorization_id != authorization.authorization_id:
                return _bad("AUTHORIZATION_MISMATCH", "Budget Authorization does not match reservation")
            amount = amounts.get((reservation.scene_id, reservation.operation))
            if amount is None:
                return _bad("SCENE_OPERATION_NOT_AUTHORIZED", "Scene operation is not authorized")
        except Exception as exc:
            return _bad(exc.code, exc.message) if hasattr(exc, "code") else _STORAGE
        if not self._active():
            return _STORAGE
        connection = self._connection
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(f"SELECT {_COLUMNS} FROM provider_attempts WHERE attempt_id = ?", (reservation.attempt_id,)).fetchone()
            auth_json = _auth_json(authorization)
            if row is not None:
                existing, _stored_authorization, stored_auth = _decode_row(row)
                self._group(existing.authorization_id)
                connection.rollback()
                return ProviderAttemptClaim(existing, False) if _static(existing, reservation, authorization, amount) and stored_auth == auth_json else _bad("ATTEMPT_CONFLICT", "attempt identity was already used with different input")
            key_row = connection.execute(f"SELECT {_COLUMNS} FROM provider_attempts WHERE idempotency_key = ?", (reservation.idempotency_key,)).fetchone()
            if key_row is not None:
                key_record, _key_authorization, _key_auth_json = _decode_row(key_row)
                self._group(key_record.authorization_id)
                connection.rollback(); return _bad("IDEMPOTENCY_CONFLICT", "idempotency key was already used with different input")
            all_decoded = self._group(authorization.authorization_id)
            if any(stored_auth != auth_json for _record_value, _stored_authorization, stored_auth in all_decoded):
                connection.rollback(); return _bad("ATTEMPT_CONFLICT", "authorization identity was already used with different input")
            related = [item for item, _stored_authorization, _stored_auth in all_decoded if item.scene_id == reservation.scene_id and item.operation == reservation.operation]
            if any(item.status == "started" for item in related):
                connection.rollback(); return _bad("ATTEMPT_IN_PROGRESS", "a nonterminal attempt already exists")
            if any(item.status == "succeeded" for item in related):
                connection.rollback(); return _bad("ATTEMPT_ALREADY_SUCCEEDED", "a successful attempt already exists")
            number = max((item.attempt_number for item in related), default=0) + 1
            if number > authorization.maximum_attempts:
                connection.rollback(); return _bad("ATTEMPT_LIMIT", "maximum attempts have been exhausted")
            spent = sum(item.reserved_amount_micros for item, _stored_authorization, _stored_auth in all_decoded)
            if spent + amount > authorization.maximum_approved_amount_micros:
                connection.rollback(); return _bad("BUDGET_LIMIT", "approved attempt budget has been exhausted")
            record = ProviderAttemptRecord(reservation.attempt_id, reservation.task_id, reservation.authorization_id, authorization.production_request_reference, authorization.budget_reference, reservation.scene_id, reservation.operation, reservation.provider, number, reservation.idempotency_key, reservation.request_record_reference, authorization.currency, amount, "started", reservation.reserved_at, None, None, None, None, ())
            _record(record)
            connection.execute(f"INSERT INTO provider_attempts ({_COLUMNS}) VALUES ({','.join('?' for _ in range(_COLUMN_COUNT))})", _row_values(record, auth_json))
            connection.commit(); return ProviderAttemptClaim(record, True)
        except Exception:
            self._rollback_quietly(); return _STORAGE

    def complete(self, outcome: ProviderAttemptOutcome) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            outcome = _outcome(outcome)
        except Exception as exc:
            return _bad(exc.code, exc.message) if hasattr(exc, "code") else _STORAGE
        if not self._active():
            return _STORAGE
        connection = self._connection
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(f"SELECT {_COLUMNS} FROM provider_attempts WHERE attempt_id = ?", (outcome.attempt_id,)).fetchone()
            if row is None:
                connection.rollback(); return _bad("ATTEMPT_NOT_FOUND", "provider attempt does not exist")
            existing, _authorization, auth_json = _decode_row(row)
            self._group(existing.authorization_id)
            if existing.status != "started":
                connection.rollback(); return existing if _same_outcome(existing, outcome) else _bad("ATTEMPT_OUTCOME_CONFLICT", "attempt outcome conflicts with the stored terminal result")
            if outcome.completed_at < existing.reserved_at:
                connection.rollback(); return _bad("INVALID_COMPLETED_AT", "completion time cannot precede reservation")
            if outcome.response_record_reference is not None:
                _workspace(outcome.response_record_reference, "provider-records", existing.task_id)
            for reference in outcome.output_references:
                _workspace(reference, "media", existing.task_id)
            record = _terminal_record(existing, outcome)
            _record(record)
            connection.execute(f"UPDATE provider_attempts SET status = ?, completed_at = ?, charged_amount_micros = ?, result_code = ?, response_task_id = ?, response_area = ?, response_name = ?, output_references_json = ? WHERE attempt_id = ?", (record.status, record.completed_at.isoformat(), record.charged_amount_micros, record.result_code, record.response_record_reference.task_id if record.response_record_reference else None, record.response_record_reference.area if record.response_record_reference else None, record.response_record_reference.name if record.response_record_reference else None, _output_json(record.output_references), record.attempt_id))
            connection.commit(); return record
        except Exception:
            self._rollback_quietly(); return _STORAGE

    def get(self, attempt_id: str) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            from .attempt import _id
            _id(attempt_id)
        except Exception as exc:
            return _bad(exc.code, exc.message) if hasattr(exc, "code") else _STORAGE
        if not self._active():
            return _STORAGE
        try:
            row = self._connection.execute(f"SELECT {_COLUMNS} FROM provider_attempts WHERE attempt_id = ?", (attempt_id,)).fetchone()
            if row is None:
                return _bad("ATTEMPT_NOT_FOUND", "provider attempt does not exist")
            record, _authorization, _auth_json_value = _decode_row(row)
            self._group(record.authorization_id)
            return record
        except Exception:
            return _STORAGE

    def list_for_authorization(self, authorization_id: str) -> tuple[ProviderAttemptRecord, ...] | ProviderAttemptFailure:
        try:
            from .attempt import _id
            _id(authorization_id, "INVALID_AUTHORIZATION_ID")
        except Exception as exc:
            return _bad(exc.code, exc.message) if hasattr(exc, "code") else _STORAGE
        if not self._active():
            return _STORAGE
        try:
            decoded = self._group(authorization_id)
            return tuple(record for record, _authorization, _auth_json_value in decoded)
        except Exception:
            return _STORAGE

    def _active(self) -> bool:
        return not self._initialization_failure and self._connection is not None

    def _group(self, authorization_id: str) -> list[tuple[ProviderAttemptRecord, BudgetAuthorizationRecord, str]]:
        rows = self._connection.execute(f"SELECT {_COLUMNS} FROM provider_attempts WHERE authorization_id = ? ORDER BY rowid", (authorization_id,)).fetchall()
        decoded = [_decode_row(row) for row in rows]
        _validate_group(decoded)
        return decoded

    def _initialize(self) -> None:
        connection = self._connection
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("CREATE TABLE IF NOT EXISTS provider_attempt_schema (singleton INTEGER PRIMARY KEY CHECK(singleton = 1), version INTEGER NOT NULL)")
        schema = connection.execute(f"SELECT {_SCHEMA_COLUMNS} FROM provider_attempt_schema WHERE singleton = 1").fetchone()
        if schema is None:
            connection.execute("INSERT INTO provider_attempt_schema(singleton, version) VALUES(1, ?)", (_SCHEMA_VERSION,))
        elif type(schema[1]) is not int or schema[1] != _SCHEMA_VERSION:
            raise ValueError
        connection.execute("""CREATE TABLE IF NOT EXISTS provider_attempts (
            attempt_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, authorization_id TEXT NOT NULL,
            request_artifact_type TEXT NOT NULL, request_identity TEXT NOT NULL, request_version INTEGER NOT NULL,
            budget_artifact_type TEXT NOT NULL, budget_identity TEXT NOT NULL, budget_version INTEGER NOT NULL,
            scene_id TEXT NOT NULL, operation TEXT NOT NULL, provider TEXT NOT NULL, attempt_number INTEGER NOT NULL,
            idempotency_key TEXT NOT NULL UNIQUE, request_task_id TEXT NOT NULL, request_area TEXT NOT NULL,
            request_name TEXT NOT NULL, currency TEXT NOT NULL, reserved_amount_micros INTEGER NOT NULL,
            status TEXT NOT NULL, reserved_at TEXT NOT NULL, completed_at TEXT, charged_amount_micros INTEGER,
            result_code TEXT, response_task_id TEXT, response_area TEXT, response_name TEXT,
            output_references_json TEXT NOT NULL, authorization_fingerprint_json TEXT NOT NULL
        )""")
        connection.commit()

    def _rollback_quietly(self) -> None:
        if self._connection is not None:
            try:
                self._connection.rollback()
            except Exception:
                pass

    def _close_quietly(self) -> None:
        connection, self._connection = self._connection, None
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


__all__ = ["SQLiteProviderAttemptRepository"]
