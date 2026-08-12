"""SQLite persistence for immutable Budget decisions and authorizations."""

from __future__ import annotations
from datetime import datetime
import json
import os
import sqlite3
from typing import Any
from .budget import (BudgetAuthorizationRecord, BudgetAuthorizationRepository,
    BudgetDecisionOutcome, BudgetDecisionRecord, BudgetFailure, PriceLineItem,
    PriceSnapshot, _BudgetValidation, _CURRENCY_RE, _MAX_TEXT_LENGTH, _MAX_UNIT_LENGTH,
    _positive_int, _safe_scene_id, _safe_text, _valid_identity,
    _validate_attempts, _validate_context, _validate_identity, _validate_reference,
    _validate_time)
from ai_course_factory.artifacts import ArtifactReference
_SCHEMA_VERSION = 1
_STORAGE_FAILURE = BudgetFailure(
    "execution", "BUDGET_AUTHORIZATION_FAILED", "budget decision persistence failed"
)
_LINE_ITEM_FIELDS = {"scene_id", "operation", "unit", "quantity", "unit_price_micros"}
_DECISION_COLUMNS = ("decision_id, task_id, thread_id, creator_id, gate_kind, "
    "request_artifact_type, request_identity, request_version, budget_artifact_type, "
    "budget_identity, budget_version, action, authorization_id, "
    "maximum_approved_amount_micros, maximum_attempts, decided_at, decision_context")
_AUTHORIZATION_COLUMNS = ("authorization_id, decision_id, task_id, thread_id, creator_id, "
    "request_artifact_type, request_identity, request_version, budget_artifact_type, "
    "budget_identity, budget_version, snapshot_id, snapshot_source, snapshot_currency, "
    "snapshot_request_artifact_type, snapshot_request_identity, snapshot_request_version, "
    "snapshot_line_items_json, currency, maximum_approved_amount_micros, maximum_attempts, decided_at")
def _validation_failure(code: str, message: str) -> BudgetFailure:
    return BudgetFailure("validation", code, message)
def _validate_snapshot(snapshot: object, request_reference: ArtifactReference) -> None:
    if not isinstance(snapshot, PriceSnapshot):
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT", "a PriceSnapshot is required")
    _validate_identity(snapshot.snapshot_id, "INVALID_PRICE_SNAPSHOT", "price snapshot identity is invalid")
    _safe_text(snapshot.source, "INVALID_PRICE_SNAPSHOT", "price snapshot source is invalid")
    if not isinstance(snapshot.currency, str) or _CURRENCY_RE.fullmatch(snapshot.currency) is None:
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT", "price snapshot currency is invalid")
    if snapshot.production_request_reference != request_reference:
        raise _BudgetValidation("PRICE_SNAPSHOT_REQUEST_MISMATCH", "price snapshot Request Reference does not match")
    if type(snapshot.line_items) is not tuple or not snapshot.line_items:
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT", "price snapshot line items are invalid")
    items = snapshot.line_items
    if len(items) % 2:
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT_COVERAGE", "price snapshot must contain visual/voice pairs")
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, PriceLineItem):
            raise _BudgetValidation("INVALID_PRICE_LINE_ITEM", "price snapshot line item is invalid")
        _safe_scene_id(item.scene_id)
        if item.operation not in {"visual", "voice"}:
            raise _BudgetValidation("INVALID_PRICE_LINE_ITEM", "price line operation is invalid")
        _safe_text(item.unit, "INVALID_PRICE_LINE_ITEM", "price line unit is invalid", limit=_MAX_UNIT_LENGTH)
        _positive_int(item.quantity, "INVALID_PRICE_LINE_ITEM", "price quantity must be a positive integer")
        _positive_int(item.unit_price_micros, "INVALID_PRICE_LINE_ITEM", "unit price must be a positive integer")
        if index % 2 == 0:
            if index + 1 >= len(items) or item.operation != "visual":
                raise _BudgetValidation("INVALID_PRICE_SNAPSHOT_COVERAGE", "price snapshot line items are not canonical")
            continue
        first = items[index - 1]
        if item.operation != "voice" or item.scene_id != first.scene_id or item.scene_id in seen:
            raise _BudgetValidation("INVALID_PRICE_SNAPSHOT_COVERAGE", "price snapshot line items are not canonical")
        seen.add(item.scene_id)
    if len(_line_items_json(items)) > _MAX_TEXT_LENGTH * 8:
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT", "price snapshot is too large")
def _validate_decision(record: object) -> BudgetFailure | None:
    if not isinstance(record, BudgetDecisionRecord):
        return _validation_failure("INVALID_DECISION_RECORD", "Budget decision record is invalid")
    try:
        for value, code, message in (
            (record.decision_id, "INVALID_DECISION_ID", "decision identity is required"),
            (record.task_id, "INVALID_TASK_ID", "task identity is required"),
            (record.thread_id, "INVALID_THREAD_ID", "thread identity is required"),
            (record.creator_id, "INVALID_CREATOR_ID", "Creator identity is required"),
        ):
            _validate_identity(value, code, message)
        if record.gate_kind != "budget_review":
            raise _BudgetValidation("INVALID_DECISION_RECORD", "Budget decision gate is invalid")
        _validate_reference(record.production_request_reference, "production_request")
        _validate_reference(record.budget_reference, "production_budget")
        _validate_time(record.decided_at)
        if record.action not in {"approve", "reject"}:
            raise _BudgetValidation("INVALID_DECISION_ACTION", "budget decision action is invalid")
        _validate_context(record.decision_context, record.action)
        if record.action == "reject":
            if any(getattr(record, field) is not None for field in (
                "authorization_id", "maximum_approved_amount_micros", "maximum_attempts"
            )):
                raise _BudgetValidation(
                    "INVALID_REJECTION_FIELDS",
                    "rejected Budget Review cannot carry authorization fields",
                )
        else:
            _validate_identity(record.authorization_id, "INVALID_AUTHORIZATION_ID", "authorization identity is required")
            for value, code, message in (
                (record.maximum_approved_amount_micros, "INVALID_APPROVED_AMOUNT", "approved amount must be a positive integer"),
            ):
                _positive_int(value, code, message)
            _validate_attempts(record.maximum_attempts, 3)
    except _BudgetValidation as exc:
        return _validation_failure(exc.code, exc.message)
    except Exception:
        return _validation_failure("INVALID_DECISION_RECORD", "Budget decision record is invalid")
    return None
def _validate_authorization(record: object) -> BudgetFailure | None:
    if not isinstance(record, BudgetAuthorizationRecord):
        return _validation_failure(
            "INVALID_AUTHORIZATION_RECORD", "Budget authorization record is invalid"
        )
    try:
        for value, code, message in (
            (record.authorization_id, "INVALID_AUTHORIZATION_ID", "authorization identity is required"),
            (record.decision_id, "INVALID_DECISION_ID", "decision identity is required"),
            (record.task_id, "INVALID_TASK_ID", "task identity is required"),
            (record.thread_id, "INVALID_THREAD_ID", "thread identity is required"),
            (record.creator_id, "INVALID_CREATOR_ID", "Creator identity is required"),
        ):
            _validate_identity(value, code, message)
        _validate_reference(record.production_request_reference, "production_request")
        _validate_reference(record.budget_reference, "production_budget")
        _validate_snapshot(record.price_snapshot, record.production_request_reference)
        if (
            not isinstance(record.currency, str)
            or _CURRENCY_RE.fullmatch(record.currency) is None
            or record.currency != record.price_snapshot.currency
        ):
            raise _BudgetValidation("INVALID_AUTHORIZATION_RECORD", "authorization currency is invalid")
        for value, code, message in (
            (record.maximum_approved_amount_micros, "INVALID_APPROVED_AMOUNT", "approved amount must be a positive integer"),
        ):
            _positive_int(value, code, message)
        _validate_attempts(record.maximum_attempts, 3)
        _validate_time(record.decided_at)
    except _BudgetValidation as exc:
        return _validation_failure(exc.code, exc.message)
    except Exception:
        return _validation_failure(
            "INVALID_AUTHORIZATION_RECORD", "Budget authorization record is invalid"
        )
    return None
def _validate_outcome(outcome: object) -> BudgetFailure | None:
    if not isinstance(outcome, BudgetDecisionOutcome):
        return _validation_failure("INVALID_BUDGET_OUTCOME", "Budget decision outcome is invalid")
    invalid = _validate_decision(outcome.decision)
    if invalid is not None:
        return invalid
    if outcome.authorization is None:
        if outcome.decision.action != "reject":
            return _validation_failure(
                "INVALID_BUDGET_OUTCOME", "approved Budget decision requires an authorization"
            )
        return None
    if outcome.decision.action != "approve":
        return _validation_failure(
            "INVALID_BUDGET_OUTCOME", "rejected Budget decision cannot carry an authorization"
        )
    invalid = _validate_authorization(outcome.authorization)
    if invalid is not None:
        return invalid
    decision = outcome.decision
    authorization = outcome.authorization
    pairs = (
        (decision.authorization_id, authorization.authorization_id),
        (decision.decision_id, authorization.decision_id),
        (decision.task_id, authorization.task_id),
        (decision.thread_id, authorization.thread_id),
        (decision.creator_id, authorization.creator_id),
        (decision.production_request_reference, authorization.production_request_reference),
        (decision.budget_reference, authorization.budget_reference),
        (decision.maximum_approved_amount_micros, authorization.maximum_approved_amount_micros),
        (decision.maximum_attempts, authorization.maximum_attempts),
        (decision.decided_at, authorization.decided_at),
        (authorization.currency, authorization.price_snapshot.currency),
    )
    if any(left != right for left, right in pairs):
        return _validation_failure(
            "BUDGET_OUTCOME_MISMATCH", "Budget decision and authorization do not match"
        )
    return None
class SQLiteBudgetAuthorizationRepository(BudgetAuthorizationRepository):
    """Durable standard-library SQLite implementation of the Budget seam."""
    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._connection: sqlite3.Connection | None = None
        self._initialization_failure: BudgetFailure | None = None
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
    def save(self, outcome: BudgetDecisionOutcome) -> BudgetDecisionOutcome | BudgetFailure:
        invalid = _validate_outcome(outcome)
        if invalid is not None:
            return invalid
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE
        connection = self._connection
        try:
            connection.execute("BEGIN IMMEDIATE")
            decision_row = self._fetch("budget_decisions", _DECISION_COLUMNS, "decision_id", outcome.decision.decision_id)
            if decision_row is not None:
                existing_decision = self._decode_decision(decision_row)
                self._assert_pair(existing_decision)
                if existing_decision != outcome.decision:
                    connection.rollback()
                    return _validation_failure(
                        "DECISION_CONFLICT",
                        "decision identity was already used with different input",
                    )
                if outcome.authorization is None:
                    authorization_row = self._fetch(
                        "budget_authorizations", "authorization_id", "decision_id", existing_decision.decision_id
                    )
                    if authorization_row is not None:
                        connection.rollback()
                        return _STORAGE_FAILURE
                    connection.rollback()
                    return BudgetDecisionOutcome(existing_decision, None)
                authorization_row = self._fetch(
                    "budget_authorizations", _AUTHORIZATION_COLUMNS,
                    "authorization_id", outcome.authorization.authorization_id,
                )
                if authorization_row is None:
                    connection.rollback()
                    return _STORAGE_FAILURE
                existing_authorization = self._decode_authorization(authorization_row)
                if existing_authorization != outcome.authorization:
                    connection.rollback()
                    return _validation_failure(
                        "DECISION_CONFLICT",
                        "decision identity was already used with different input",
                    )
                connection.rollback()
                return BudgetDecisionOutcome(existing_decision, existing_authorization)
            if outcome.authorization is not None:
                authorization_row = self._fetch(
                    "budget_authorizations", _AUTHORIZATION_COLUMNS,
                    "authorization_id", outcome.authorization.authorization_id,
                )
                if authorization_row is not None:
                    existing_authorization = self._decode_authorization(authorization_row)
                    decision_row = self._fetch(
                        "budget_decisions", _DECISION_COLUMNS,
                        "decision_id", existing_authorization.decision_id,
                    )
                    if decision_row is None:
                        raise ValueError("authorization decision is missing")
                    self._assert_pair(self._decode_decision(decision_row), existing_authorization)
                    connection.rollback()
                    return _validation_failure(
                        "AUTHORIZATION_CONFLICT",
                        "authorization identity was already used with different decision",
                )
            connection.execute(
                """
                INSERT INTO budget_decisions (
                    decision_id, task_id, thread_id, creator_id, gate_kind,
                    request_artifact_type, request_identity, request_version,
                    budget_artifact_type, budget_identity, budget_version,
                    action, authorization_id, maximum_approved_amount_micros,
                    maximum_attempts, decided_at, decision_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._decision_values(outcome.decision),
            )
            if outcome.authorization is not None:
                connection.execute(
                    """
                    INSERT INTO budget_authorizations (
                        authorization_id, decision_id, task_id, thread_id, creator_id,
                        request_artifact_type, request_identity, request_version,
                        budget_artifact_type, budget_identity, budget_version,
                        snapshot_id, snapshot_source, snapshot_currency,
                        snapshot_request_artifact_type, snapshot_request_identity,
                        snapshot_request_version, snapshot_line_items_json, currency,
                        maximum_approved_amount_micros, maximum_attempts, decided_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    self._authorization_values(outcome.authorization),
                )
            connection.commit()
            return outcome
        except Exception:
            self._rollback_quietly()
            return _STORAGE_FAILURE
    def get_decision(self, decision_id: str) -> BudgetDecisionRecord | BudgetFailure:
        invalid = self._validate_lookup_identity(decision_id, "INVALID_DECISION_ID")
        if invalid is not None:
            return invalid
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE
        try:
            row = self._fetch("budget_decisions", _DECISION_COLUMNS, "decision_id", decision_id)
            if row is None:
                return BudgetFailure("validation", "DECISION_NOT_FOUND", "decision record does not exist")
            decision = self._decode_decision(row)
            self._assert_pair(decision)
            return decision
        except Exception:
            return _STORAGE_FAILURE
    def get_authorization(self, authorization_id: str) -> BudgetAuthorizationRecord | BudgetFailure:
        invalid = self._validate_lookup_identity(authorization_id, "INVALID_AUTHORIZATION_ID")
        if invalid is not None:
            return invalid
        if self._initialization_failure is not None or self._connection is None:
            return _STORAGE_FAILURE
        try:
            row = self._fetch(
                "budget_authorizations", _AUTHORIZATION_COLUMNS,
                "authorization_id", authorization_id,
            )
            if row is None:
                return BudgetFailure(
                    "validation", "AUTHORIZATION_NOT_FOUND", "authorization record does not exist"
                )
            authorization = self._decode_authorization(row)
            decision_row = self._fetch("budget_decisions", _DECISION_COLUMNS, "decision_id", authorization.decision_id)
            if decision_row is None:
                raise ValueError("authorization decision is missing")
            self._assert_pair(self._decode_decision(decision_row), authorization)
            return authorization
        except Exception:
            return _STORAGE_FAILURE
    def close(self) -> None:
        self._close_quietly()
    def __enter__(self) -> "SQLiteBudgetAuthorizationRepository":
        return self
    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()
    def _assert_pair(
        self, decision: BudgetDecisionRecord, authorization: BudgetAuthorizationRecord | None = None
    ) -> None:
        if authorization is None and decision.action == "reject":
            if self._fetch("budget_authorizations", "authorization_id", "decision_id", decision.decision_id):
                raise ValueError("reject has an authorization")
            return
        if authorization is None:
            if not decision.authorization_id:
                raise ValueError("approval has no authorization identity")
            row = self._fetch("budget_authorizations", _AUTHORIZATION_COLUMNS, "authorization_id", decision.authorization_id)
            if row is None:
                raise ValueError("approval authorization is missing")
            authorization = self._decode_authorization(row)
        if _validate_outcome(BudgetDecisionOutcome(decision, authorization)) is not None:
            raise ValueError("decision and authorization do not match")
    def _fetch(self, table: str, columns: str, key: str, value: object) -> tuple[Any, ...] | None:
        if self._connection is None:
            raise RuntimeError("connection is unavailable")
        return self._connection.execute(
            f"SELECT {columns} FROM {table} WHERE {key} = ?", (value,)
        ).fetchone()
    def _initialize_schema(self) -> None:
        if self._connection is None:
            raise RuntimeError("connection is unavailable")
        connection = self._connection
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS budget_authorization_schema (
                singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                version INTEGER NOT NULL
            )
            """
        )
        row = connection.execute(
            "SELECT version FROM budget_authorization_schema WHERE singleton = 1"
        ).fetchone()
        if row is None:
            connection.execute(
                "INSERT INTO budget_authorization_schema (singleton, version) VALUES (1, ?)",
                (_SCHEMA_VERSION,),
            )
        elif type(row[0]) is not int or row[0] != _SCHEMA_VERSION:
            raise ValueError("unsupported Budget authorization schema")
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS budget_decisions (
                decision_id TEXT PRIMARY KEY, task_id TEXT NOT NULL,
                thread_id TEXT NOT NULL, creator_id TEXT NOT NULL, gate_kind TEXT NOT NULL,
                request_artifact_type TEXT NOT NULL, request_identity TEXT NOT NULL,
                request_version INTEGER NOT NULL, budget_artifact_type TEXT NOT NULL,
                budget_identity TEXT NOT NULL, budget_version INTEGER NOT NULL,
                action TEXT NOT NULL, authorization_id TEXT,
                maximum_approved_amount_micros INTEGER, maximum_attempts INTEGER,
                decided_at TEXT NOT NULL, decision_context TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS budget_authorizations (
                authorization_id TEXT PRIMARY KEY, decision_id TEXT NOT NULL,
                task_id TEXT NOT NULL, thread_id TEXT NOT NULL, creator_id TEXT NOT NULL,
                request_artifact_type TEXT NOT NULL, request_identity TEXT NOT NULL,
                request_version INTEGER NOT NULL, budget_artifact_type TEXT NOT NULL,
                budget_identity TEXT NOT NULL, budget_version INTEGER NOT NULL,
                snapshot_id TEXT NOT NULL, snapshot_source TEXT NOT NULL,
                snapshot_currency TEXT NOT NULL, snapshot_request_artifact_type TEXT NOT NULL,
                snapshot_request_identity TEXT NOT NULL, snapshot_request_version INTEGER NOT NULL,
                snapshot_line_items_json TEXT NOT NULL, currency TEXT NOT NULL,
                maximum_approved_amount_micros INTEGER NOT NULL, maximum_attempts INTEGER NOT NULL,
                decided_at TEXT NOT NULL,
                FOREIGN KEY (decision_id) REFERENCES budget_decisions(decision_id)
            )
            """
        )
        connection.commit()
    @staticmethod
    def _decision_values(record: BudgetDecisionRecord) -> tuple[Any, ...]:
        request = record.production_request_reference
        budget = record.budget_reference
        return (
            record.decision_id,
            record.task_id,
            record.thread_id,
            record.creator_id,
            record.gate_kind,
            request.artifact_type,
            request.identity,
            request.version,
            budget.artifact_type,
            budget.identity,
            budget.version,
            record.action,
            record.authorization_id,
            record.maximum_approved_amount_micros,
            record.maximum_attempts,
            record.decided_at.isoformat(),
            record.decision_context,
        )
    @staticmethod
    def _authorization_values(record: BudgetAuthorizationRecord) -> tuple[Any, ...]:
        request = record.production_request_reference
        budget = record.budget_reference
        snapshot_request = record.price_snapshot.production_request_reference
        return (
            record.authorization_id,
            record.decision_id,
            record.task_id,
            record.thread_id,
            record.creator_id,
            request.artifact_type,
            request.identity,
            request.version,
            budget.artifact_type,
            budget.identity,
            budget.version,
            record.price_snapshot.snapshot_id,
            record.price_snapshot.source,
            record.price_snapshot.currency,
            snapshot_request.artifact_type,
            snapshot_request.identity,
            snapshot_request.version,
            _line_items_json(record.price_snapshot.line_items),
            record.currency,
            record.maximum_approved_amount_micros,
            record.maximum_attempts,
            record.decided_at.isoformat(),
        )
    @staticmethod
    def _decode_decision(row: tuple[Any, ...]) -> BudgetDecisionRecord:
        if len(row) != 17:
            raise ValueError("stored Budget decision row is malformed")
        request = ArtifactReference(row[5], row[6], row[7])
        budget = ArtifactReference(row[8], row[9], row[10])
        decided_at = datetime.fromisoformat(row[15])
        record = BudgetDecisionRecord(
            decision_id=row[0],
            task_id=row[1],
            thread_id=row[2],
            creator_id=row[3],
            gate_kind=row[4],
            production_request_reference=request,
            budget_reference=budget,
            action=row[11],
            authorization_id=row[12],
            maximum_approved_amount_micros=row[13],
            maximum_attempts=row[14],
            decided_at=decided_at,
            decision_context=row[16],
        )
        invalid = _validate_decision(record)
        if invalid is not None:
            raise ValueError("stored Budget decision is invalid")
        return record
    @staticmethod
    def _decode_authorization(row: tuple[Any, ...]) -> BudgetAuthorizationRecord:
        if len(row) != 22:
            raise ValueError("stored Budget authorization row is malformed")
        request = ArtifactReference(row[5], row[6], row[7])
        budget = ArtifactReference(row[8], row[9], row[10])
        snapshot_request = ArtifactReference(row[14], row[15], row[16])
        snapshot = PriceSnapshot(
            snapshot_id=row[11],
            source=row[12],
            currency=row[13],
            production_request_reference=snapshot_request,
            line_items=_decode_line_items(row[17]),
        )
        record = BudgetAuthorizationRecord(
            authorization_id=row[0],
            decision_id=row[1],
            task_id=row[2],
            thread_id=row[3],
            creator_id=row[4],
            production_request_reference=request,
            budget_reference=budget,
            price_snapshot=snapshot,
            currency=row[18],
            maximum_approved_amount_micros=row[19],
            maximum_attempts=row[20],
            decided_at=datetime.fromisoformat(row[21]),
        )
        invalid = _validate_authorization(record)
        if invalid is not None:
            raise ValueError("stored Budget authorization is invalid")
        return record

    @staticmethod
    def _validate_lookup_identity(value: object, code: str) -> BudgetFailure | None:
        if not _valid_identity(value):
            return _validation_failure(code, "identity is required")
        return None

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


def _line_items_json(items: tuple[PriceLineItem, ...]) -> str:
    encoded = json.dumps(
        [
            {
                "scene_id": item.scene_id,
                "operation": item.operation,
                "unit": item.unit,
                "quantity": item.quantity,
                "unit_price_micros": item.unit_price_micros,
            }
            for item in items
        ],
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    if len(encoded) > _MAX_TEXT_LENGTH * 8:
        raise ValueError("stored line items are too large")
    return encoded


def _decode_line_items(value: object) -> tuple[PriceLineItem, ...]:
    if not isinstance(value, str) or len(value) > _MAX_TEXT_LENGTH * 8:
        raise ValueError("stored line items are malformed")
    try:
        raw_items = json.loads(value)
    except Exception as exc:
        raise ValueError("stored line items are malformed") from exc
    if not isinstance(raw_items, list):
        raise ValueError("stored line items are malformed")
    items: list[PriceLineItem] = []
    for raw in raw_items:
        if not isinstance(raw, dict) or set(raw) != _LINE_ITEM_FIELDS:
            raise ValueError("stored line item is malformed")
        if type(raw.get("quantity")) is not int or type(raw.get("unit_price_micros")) is not int:
            raise ValueError("stored line item integer is malformed")
        items.append(
            PriceLineItem(
                scene_id=raw["scene_id"],
                operation=raw["operation"],
                unit=raw["unit"],
                quantity=raw["quantity"],
                unit_price_micros=raw["unit_price_micros"],
            )
        )
    return tuple(items)
__all__ = ["SQLiteBudgetAuthorizationRepository"]
