"""Provider-attempt reservation and terminal-outcome persistence contracts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from datetime import datetime
import re
from threading import RLock
from typing import Any, Protocol, runtime_checkable

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference

from .budget import BudgetAuthorizationRecord, BudgetFailure, PriceLineItem, PriceSnapshot

_MAX_ID = 256
_MAX_TEXT = 4096
_MAX_INT = 2**63 - 1
_OPS = frozenset(("visual", "voice"))
_STATES = frozenset(("started", "succeeded", "failed"))
_CURRENCY = re.compile(r"^[A-Z]{3}$")
_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")

@dataclass(frozen=True, slots=True)
class ProviderAttemptReservation:
    attempt_id: str
    task_id: str
    authorization_id: str
    scene_id: str
    operation: str
    provider: str
    idempotency_key: str
    request_record_reference: WorkspaceFileReference
    reserved_at: datetime


@dataclass(frozen=True, slots=True)
class ProviderAttemptOutcome:
    attempt_id: str
    status: str
    completed_at: datetime
    charged_amount_micros: int
    result_code: str
    response_record_reference: WorkspaceFileReference | None
    output_references: tuple[WorkspaceFileReference, ...]

@dataclass(frozen=True, slots=True)
class ProviderAttemptRecord:
    attempt_id: str
    task_id: str
    authorization_id: str
    production_request_reference: ArtifactReference
    budget_reference: ArtifactReference
    scene_id: str
    operation: str
    provider: str
    attempt_number: int
    idempotency_key: str
    request_record_reference: WorkspaceFileReference
    currency: str
    reserved_amount_micros: int
    status: str
    reserved_at: datetime
    completed_at: datetime | None
    charged_amount_micros: int | None
    result_code: str | None
    response_record_reference: WorkspaceFileReference | None
    output_references: tuple[WorkspaceFileReference, ...]

@dataclass(frozen=True, slots=True)
class ProviderAttemptFailure:
    kind: str
    code: str
    message: str

@runtime_checkable
class ProviderAttemptRepository(Protocol):
    def reserve(self, reservation: ProviderAttemptReservation, authorization: BudgetAuthorizationRecord) -> ProviderAttemptRecord | ProviderAttemptFailure: ...
    def complete(self, outcome: ProviderAttemptOutcome) -> ProviderAttemptRecord | ProviderAttemptFailure: ...
    def get(self, attempt_id: str) -> ProviderAttemptRecord | ProviderAttemptFailure: ...
    def list_for_authorization(self, authorization_id: str) -> tuple[ProviderAttemptRecord, ...] | ProviderAttemptFailure: ...

class _Invalid(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code, self.message = code, message

_STORAGE = ProviderAttemptFailure("execution", "ATTEMPT_STORAGE_FAILED", "provider attempt persistence failed")

def _bad(code: str, message: str) -> ProviderAttemptFailure:
    return ProviderAttemptFailure("validation", code, message)

def _text(value: object, code: str, message: str, limit: int = _MAX_TEXT) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise _Invalid(code, message)
    return value

def _scene(value: object, code: str = "INVALID_SCENE_ID") -> str:
    value = _text(value, code, "Scene identity is invalid", 128)
    if value.strip().casefold() in {"latest", "current"}:
        raise _Invalid(code, "Scene identity is invalid")
    return value

def _workspace_task(value: object) -> str:
    value = _text(value, "INVALID_WORKSPACE_TASK_ID", "workspace task identity is invalid", 128)
    if value.strip().casefold() == "latest" or value[0] not in _ALNUM or any(c not in (_ALNUM | frozenset("._-:")) for c in value):
        raise _Invalid("INVALID_WORKSPACE_TASK_ID", "workspace task identity is invalid")
    return value

def _id(value: object, code: str = "INVALID_ATTEMPT_ID") -> str:
    value = _text(value, code, "provider attempt identity is invalid", _MAX_ID)
    if value.strip().casefold() in {"latest", "current"}:
        raise _Invalid(code, "provider attempt identity is invalid")
    return value

def _integer(value: object, code: str, message: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > _MAX_INT:
        raise _Invalid(code, message)
    return value

def _time(value: object, code: str = "INVALID_ATTEMPT_TIME") -> datetime:
    try:
        valid = isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
    except Exception:
        valid = False
    if not valid:
        raise _Invalid(code, "attempt time must be timezone-aware")
    return value

def _artifact(value: object, expected: str, code: str) -> ArtifactReference:
    if not isinstance(value, ArtifactReference) or value.artifact_type != expected:
        raise _Invalid(code, f"an exact {expected} Reference is required")
    _id(value.identity, code)
    if type(value.version) is not int or value.version < 1:
        raise _Invalid(code, f"an exact {expected} Reference is required")
    return value

def _workspace(value: object, area: str, task_id: str) -> WorkspaceFileReference:
    if not isinstance(value, WorkspaceFileReference) or value.task_id != task_id:
        raise _Invalid("WORKSPACE_TASK_MISMATCH", "workspace file task does not match attempt task")
    _workspace_task(value.task_id)
    if value.area != area:
        raise _Invalid("INVALID_WORKSPACE_AREA", "workspace file area is invalid")
    if type(value.name) is not str or not value.name or len(value.name) > 128 or value.name.lower() == "latest" or value.name[0] not in _ALNUM or any(c not in (_ALNUM | frozenset("._-")) for c in value.name):
        raise _Invalid("INVALID_WORKSPACE_FILE_NAME", "workspace file name is invalid")
    return value

def _authorization(value: object) -> tuple[BudgetAuthorizationRecord, dict[tuple[str, str], int]]:
    if not isinstance(value, BudgetAuthorizationRecord):
        raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
    for item in (value.authorization_id, value.decision_id, value.task_id, value.thread_id, value.creator_id):
        _id(item, "INVALID_AUTHORIZATION")
    request = _artifact(value.production_request_reference, "production_request", "INVALID_AUTHORIZATION")
    _artifact(value.budget_reference, "production_budget", "INVALID_AUTHORIZATION")
    if not isinstance(value.currency, str) or _CURRENCY.fullmatch(value.currency) is None:
        raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
    _integer(value.maximum_approved_amount_micros, "INVALID_AUTHORIZATION", "Budget Authorization is invalid", 1)
    attempts = _integer(value.maximum_attempts, "INVALID_AUTHORIZATION", "Budget Authorization is invalid", 1)
    if attempts > 3:
        raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
    _time(value.decided_at, "INVALID_AUTHORIZATION")
    snapshot = value.price_snapshot
    if not isinstance(snapshot, PriceSnapshot) or snapshot.production_request_reference != request or snapshot.currency != value.currency or type(snapshot.line_items) is not tuple or not snapshot.line_items or len(snapshot.line_items) % 2:
        raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
    _id(snapshot.snapshot_id, "INVALID_AUTHORIZATION")
    _text(snapshot.source, "INVALID_AUTHORIZATION", "Budget Authorization is invalid")
    amounts: dict[tuple[str, str], int] = {}
    for index, line in enumerate(snapshot.line_items):
        if not isinstance(line, PriceLineItem) or line.operation not in _OPS:
            raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
        scene = _scene(line.scene_id, "INVALID_AUTHORIZATION")
        _text(line.unit, "INVALID_AUTHORIZATION", "Budget Authorization is invalid", 128)
        quantity = _integer(line.quantity, "INVALID_AUTHORIZATION", "Budget Authorization is invalid", 1)
        price = _integer(line.unit_price_micros, "INVALID_AUTHORIZATION", "Budget Authorization is invalid", 1)
        amount = quantity * price
        if amount > _MAX_INT or (scene, line.operation) in amounts:
            raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
        if index % 2 == 0 and line.operation != "visual":
            raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
        if index % 2 == 1:
            previous = snapshot.line_items[index - 1]
            if line.operation != "voice" or line.scene_id != previous.scene_id:
                raise _Invalid("INVALID_AUTHORIZATION", "Budget Authorization is invalid")
        amounts[(scene, line.operation)] = amount
    return value, amounts

def _reservation(value: object) -> ProviderAttemptReservation:
    if not isinstance(value, ProviderAttemptReservation):
        raise _Invalid("INVALID_RESERVATION", "provider attempt reservation is invalid")
    _id(value.attempt_id)
    _id(value.task_id, "INVALID_TASK_ID")
    _id(value.authorization_id, "INVALID_AUTHORIZATION_ID")
    _scene(value.scene_id)
    if value.operation not in _OPS:
        raise _Invalid("INVALID_OPERATION", "provider operation is invalid")
    provider = _text(value.provider, "INVALID_PROVIDER", "provider identity is invalid", 128)
    if provider.strip().casefold() in {"latest", "current"}:
        raise _Invalid("INVALID_PROVIDER", "provider identity is invalid")
    _id(value.idempotency_key, "INVALID_IDEMPOTENCY_KEY")
    _workspace(value.request_record_reference, "provider-records", value.task_id)
    _time(value.reserved_at)
    return value

def _outcome(value: object) -> ProviderAttemptOutcome:
    if not isinstance(value, ProviderAttemptOutcome):
        raise _Invalid("INVALID_OUTCOME", "provider attempt outcome is invalid")
    _id(value.attempt_id)
    if value.status not in {"succeeded", "failed"}:
        raise _Invalid("INVALID_OUTCOME_STATUS", "provider attempt outcome status is invalid")
    _time(value.completed_at, "INVALID_COMPLETED_AT")
    _integer(value.charged_amount_micros, "INVALID_CHARGED_AMOUNT", "charged amount is invalid")
    _text(value.result_code, "INVALID_RESULT_CODE", "provider result code is invalid", 128)
    if type(value.output_references) is not tuple:
        raise _Invalid("INVALID_OUTPUT_REFERENCES", "output references are invalid")
    if len(set(value.output_references)) != len(value.output_references):
        raise _Invalid("INVALID_OUTPUT_REFERENCES", "output references are invalid")
    if value.status == "succeeded" and (value.result_code != "SUCCESS" or not value.output_references):
        raise _Invalid("INVALID_SUCCESS_OUTCOME", "successful outcome is incomplete")
    if value.status == "failed" and (value.result_code == "SUCCESS" or value.output_references):
        raise _Invalid("INVALID_FAILURE_OUTCOME", "failed outcome is invalid")
    if value.response_record_reference is not None:
        _workspace(value.response_record_reference, "provider-records", value.response_record_reference.task_id)
    return value

def _record(value: object) -> ProviderAttemptRecord:
    if not isinstance(value, ProviderAttemptRecord):
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    _id(value.attempt_id); _id(value.task_id, "INVALID_TASK_ID"); _id(value.authorization_id, "INVALID_AUTHORIZATION_ID")
    _artifact(value.production_request_reference, "production_request", "INVALID_STORED_RECORD")
    _artifact(value.budget_reference, "production_budget", "INVALID_STORED_RECORD")
    _scene(value.scene_id, "INVALID_STORED_RECORD")
    if value.operation not in _OPS:
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    provider = _text(value.provider, "INVALID_STORED_RECORD", "provider attempt record is invalid", 128)
    if provider.strip().casefold() in {"latest", "current"}:
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    _integer(value.attempt_number, "INVALID_STORED_RECORD", "provider attempt record is invalid", 1)
    _id(value.idempotency_key, "INVALID_STORED_RECORD")
    _workspace(value.request_record_reference, "provider-records", value.task_id)
    if not isinstance(value.currency, str) or _CURRENCY.fullmatch(value.currency) is None:
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    _integer(value.reserved_amount_micros, "INVALID_STORED_RECORD", "provider attempt record is invalid", 1)
    _time(value.reserved_at)
    if value.status not in _STATES or type(value.output_references) is not tuple:
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    if value.status == "started":
        if value.completed_at is not None or value.charged_amount_micros is not None or value.result_code is not None or value.response_record_reference is not None or value.output_references:
            raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
        return value
    if value.completed_at is None or value.completed_at < value.reserved_at:
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    _time(value.completed_at, "INVALID_STORED_RECORD")
    _integer(value.charged_amount_micros, "INVALID_STORED_RECORD", "provider attempt record is invalid")
    _text(value.result_code, "INVALID_STORED_RECORD", "provider attempt record is invalid", 128)
    if value.response_record_reference is not None:
        _workspace(value.response_record_reference, "provider-records", value.task_id)
    if len(set(value.output_references)) != len(value.output_references) or any(_workspace(ref, "media", value.task_id) is None for ref in value.output_references):
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    if (value.status == "succeeded") != (value.result_code == "SUCCESS" and bool(value.output_references)):
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    if value.status == "failed" and (value.result_code == "SUCCESS" or value.output_references):
        raise _Invalid("INVALID_STORED_RECORD", "provider attempt record is invalid")
    return value

def _auth_fp(auth: BudgetAuthorizationRecord) -> tuple[Any, ...]:
    s = auth.price_snapshot
    return (
        auth.authorization_id, auth.decision_id, auth.task_id, auth.thread_id, auth.creator_id,
        auth.production_request_reference, auth.budget_reference, auth.currency,
        auth.maximum_approved_amount_micros, auth.maximum_attempts, auth.decided_at,
        s.snapshot_id, s.source, s.currency, s.production_request_reference,
        tuple((x.scene_id, x.operation, x.unit, x.quantity, x.unit_price_micros) for x in s.line_items),
    )

def _static(record: ProviderAttemptRecord, reservation: ProviderAttemptReservation, auth: BudgetAuthorizationRecord, amount: int) -> bool:
    stored = (
        record.attempt_id, record.task_id, record.authorization_id,
        record.production_request_reference, record.budget_reference, record.scene_id,
        record.operation, record.provider, record.idempotency_key,
        record.request_record_reference, record.currency,
        record.reserved_amount_micros, record.reserved_at,
    )
    requested = (
        reservation.attempt_id, reservation.task_id, reservation.authorization_id,
        auth.production_request_reference, auth.budget_reference, reservation.scene_id,
        reservation.operation, reservation.provider, reservation.idempotency_key,
        reservation.request_record_reference, auth.currency, amount, reservation.reserved_at,
    )
    return stored == requested

def _same_outcome(record: ProviderAttemptRecord, outcome: ProviderAttemptOutcome) -> bool:
    stored = (
        record.attempt_id, record.status, record.completed_at, record.charged_amount_micros,
        record.result_code, record.response_record_reference, record.output_references,
    )
    requested = (
        outcome.attempt_id, outcome.status, outcome.completed_at, outcome.charged_amount_micros,
        outcome.result_code, outcome.response_record_reference, outcome.output_references,
    )
    return stored == requested

def _terminal_record(record: ProviderAttemptRecord, outcome: ProviderAttemptOutcome) -> ProviderAttemptRecord:
    return replace(
        record,
        status=outcome.status,
        completed_at=outcome.completed_at,
        charged_amount_micros=outcome.charged_amount_micros,
        result_code=outcome.result_code,
        response_record_reference=outcome.response_record_reference,
        output_references=outcome.output_references,
    )

class _MemoryProviderAttemptRepository:
    def __init__(self) -> None:
        self._lock = RLock(); self._records: dict[str, ProviderAttemptRecord] = {}; self._keys: dict[str, str] = {}; self._auth: dict[str, tuple[Any, ...]] = {}; self._order: list[str] = []

    def reserve(self, reservation: ProviderAttemptReservation, authorization: BudgetAuthorizationRecord) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            with self._lock:
                reservation = _reservation(reservation); authorization, amounts = _authorization(authorization)
                if reservation.task_id != authorization.task_id or reservation.authorization_id != authorization.authorization_id:
                    return _bad("AUTHORIZATION_MISMATCH", "Budget Authorization does not match reservation")
                amount = amounts.get((reservation.scene_id, reservation.operation))
                if amount is None:
                    return _bad("SCENE_OPERATION_NOT_AUTHORIZED", "Scene operation is not authorized")
                existing = self._records.get(reservation.attempt_id); fingerprint = _auth_fp(authorization)
                if existing is not None:
                    return existing if _static(existing, reservation, authorization, amount) and self._auth.get(existing.attempt_id) == fingerprint else _bad("ATTEMPT_CONFLICT", "attempt identity was already used with different input")
                if reservation.idempotency_key in self._keys:
                    return _bad("IDEMPOTENCY_CONFLICT", "idempotency key was already used with different input")
                authorization_records = [r for r in self._records.values() if r.authorization_id == authorization.authorization_id]
                if any(self._auth.get(r.attempt_id) != fingerprint for r in authorization_records):
                    return _bad("ATTEMPT_CONFLICT", "authorization identity was already used with different input")
                related = [r for r in authorization_records if r.scene_id == reservation.scene_id and r.operation == reservation.operation]
                if any(r.status == "started" for r in related):
                    return _bad("ATTEMPT_IN_PROGRESS", "a nonterminal attempt already exists")
                if any(r.status == "succeeded" for r in related):
                    return _bad("ATTEMPT_ALREADY_SUCCEEDED", "a successful attempt already exists")
                number = max((r.attempt_number for r in related), default=0) + 1
                if number > authorization.maximum_attempts:
                    return _bad("ATTEMPT_LIMIT", "maximum attempts have been exhausted")
                if sum(r.reserved_amount_micros for r in self._records.values() if r.authorization_id == authorization.authorization_id) + amount > authorization.maximum_approved_amount_micros:
                    return _bad("BUDGET_LIMIT", "approved attempt budget has been exhausted")
                record = ProviderAttemptRecord(reservation.attempt_id, reservation.task_id, reservation.authorization_id, authorization.production_request_reference, authorization.budget_reference, reservation.scene_id, reservation.operation, reservation.provider, number, reservation.idempotency_key, reservation.request_record_reference, authorization.currency, amount, "started", reservation.reserved_at, None, None, None, None, ())
                _record(record); self._records[record.attempt_id] = record; self._keys[record.idempotency_key] = record.attempt_id; self._auth[record.attempt_id] = fingerprint; self._order.append(record.attempt_id)
                return record
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE
    def complete(self, outcome: ProviderAttemptOutcome) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            with self._lock:
                outcome = _outcome(outcome); existing = self._records.get(outcome.attempt_id)
                if existing is None:
                    return _bad("ATTEMPT_NOT_FOUND", "provider attempt does not exist")
                if existing.status != "started":
                    return existing if _same_outcome(existing, outcome) else _bad("ATTEMPT_OUTCOME_CONFLICT", "attempt outcome conflicts with the stored terminal result")
                if outcome.completed_at < existing.reserved_at:
                    return _bad("INVALID_COMPLETED_AT", "completion time cannot precede reservation")
                if outcome.response_record_reference is not None:
                    _workspace(outcome.response_record_reference, "provider-records", existing.task_id)
                for ref in outcome.output_references:
                    _workspace(ref, "media", existing.task_id)
                record = _terminal_record(existing, outcome)
                _record(record); self._records[record.attempt_id] = record; return record
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE
    def get(self, attempt_id: str) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            with self._lock:
                _id(attempt_id); return self._records.get(attempt_id, _bad("ATTEMPT_NOT_FOUND", "provider attempt does not exist"))
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE
    def list_for_authorization(self, authorization_id: str) -> tuple[ProviderAttemptRecord, ...] | ProviderAttemptFailure:
        try:
            with self._lock:
                _id(authorization_id, "INVALID_AUTHORIZATION_ID"); return tuple(self._records[i] for i in self._order if self._records[i].authorization_id == authorization_id)
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE

class ProviderAttemptLedger:
    """Load exact Authorization before invoking repository mutation."""

    def __init__(self, authorization_lookup: Any, repository: ProviderAttemptRepository | None = None) -> None:
        self._lookup_source = authorization_lookup; self._repository: ProviderAttemptRepository = repository or _MemoryProviderAttemptRepository()

    def reserve(self, reservation: ProviderAttemptReservation) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            reservation = _reservation(reservation); raw = self._lookup(reservation.authorization_id)
            if isinstance(raw, BudgetFailure):
                return ProviderAttemptFailure(raw.kind, raw.code, raw.message)
            authorization, amounts = _authorization(raw)
            if reservation.task_id != authorization.task_id or reservation.authorization_id != authorization.authorization_id:
                return _bad("AUTHORIZATION_MISMATCH", "Budget Authorization does not match reservation")
            amount = amounts.get((reservation.scene_id, reservation.operation))
            if amount is None:
                return _bad("SCENE_OPERATION_NOT_AUTHORIZED", "Scene operation is not authorized")
            prior = self._repository.get(reservation.attempt_id)
            if isinstance(prior, ProviderAttemptFailure) and prior.code != "ATTEMPT_NOT_FOUND":
                return prior
            prior_record = None if isinstance(prior, ProviderAttemptFailure) else prior
            result = self._repository.reserve(reservation, authorization)
            if isinstance(result, ProviderAttemptFailure):
                return result
            try:
                _record(result)
            except _Invalid:
                return _STORAGE
            if not _static(result, reservation, authorization, amount) or result.attempt_number > authorization.maximum_attempts:
                return _STORAGE
            if prior_record is not None:
                return result if result == prior_record else _STORAGE
            if result.status != "started":
                return _STORAGE
            listed = self._repository.list_for_authorization(authorization.authorization_id)
            if isinstance(listed, ProviderAttemptFailure) or type(listed) is not tuple:
                return _STORAGE
            related = [item for item in listed if item.scene_id == reservation.scene_id and item.operation == reservation.operation]
            others = [item for item in related if item.attempt_id != result.attempt_id]
            if result not in related or result.attempt_number != max((item.attempt_number for item in others), default=0) + 1:
                return _STORAGE
            return result
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE

    def complete(self, outcome: ProviderAttemptOutcome) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            _outcome(outcome)
            prior = self._repository.get(outcome.attempt_id)
            if isinstance(prior, ProviderAttemptFailure) and prior.code != "ATTEMPT_NOT_FOUND":
                return prior
            if isinstance(prior, ProviderAttemptFailure):
                prior_record = None
            else:
                try:
                    prior_record = _record(prior)
                except _Invalid:
                    return _STORAGE
            result = self._repository.complete(outcome)
            if isinstance(result, ProviderAttemptFailure):
                return result
            try:
                _record(result)
            except _Invalid:
                return _STORAGE
            if prior_record is None:
                return _STORAGE
            if prior_record.status == "started":
                expected = _terminal_record(prior_record, outcome)
                return result if result == expected else _STORAGE
            return result if result == prior_record and _same_outcome(prior_record, outcome) else _STORAGE
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE

    def get(self, attempt_id: str) -> ProviderAttemptRecord | ProviderAttemptFailure:
        try:
            _id(attempt_id); result = self._repository.get(attempt_id)
            if isinstance(result, ProviderAttemptFailure):
                return result
            try:
                return _record(result)
            except _Invalid:
                return _STORAGE
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE

    def list_for_authorization(self, authorization_id: str) -> tuple[ProviderAttemptRecord, ...] | ProviderAttemptFailure:
        try:
            _id(authorization_id, "INVALID_AUTHORIZATION_ID"); result = self._repository.list_for_authorization(authorization_id)
            if isinstance(result, ProviderAttemptFailure) or type(result) is not tuple:
                return result if isinstance(result, ProviderAttemptFailure) else _STORAGE
            for item in result:
                if item.authorization_id != authorization_id:
                    return _STORAGE
                try:
                    _record(item)
                except _Invalid:
                    return _STORAGE
            return result
        except _Invalid as exc:
            return _bad(exc.code, exc.message)
        except Exception:
            return _STORAGE

    def _lookup(self, authorization_id: str) -> object:
        source = self._lookup_source
        try:
            if hasattr(source, "get_authorization"):
                return source.get_authorization(authorization_id)
            if callable(source):
                return source(authorization_id)
            if isinstance(source, Mapping):
                return source.get(authorization_id, BudgetFailure("validation", "AUTHORIZATION_NOT_FOUND", "authorization record does not exist"))
        except Exception:
            return BudgetFailure("execution", "BUDGET_AUTHORIZATION_FAILED", "authorization lookup failed")
        return BudgetFailure("execution", "BUDGET_AUTHORIZATION_FAILED", "authorization lookup failed")


__all__ = ["ProviderAttemptFailure", "ProviderAttemptLedger", "ProviderAttemptOutcome", "ProviderAttemptRecord", "ProviderAttemptRepository", "ProviderAttemptReservation"]
