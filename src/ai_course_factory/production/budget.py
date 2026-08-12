"""Deterministic provider-neutral budget and Creator authorization seams."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
import math
import re
from typing import Any

from ai_course_factory.artifacts import ArtifactCandidate, ArtifactReference, ArtifactVersion


_MAX_IDENTITY_LENGTH = 256
_MAX_TEXT_LENGTH = 4096
_MAX_SCENE_ID_LENGTH = 128
_MAX_UNIT_LENGTH = 128
_TIMELINE_TOLERANCE = 1e-9
_REQUEST_PAYLOAD_FIELDS = {
    "script_reference",
    "approval_decision_id",
    "character_reference",
    "storyboard_reference",
    "storyboard_decision_id",
    "timeline_reference",
    "production_request",
}
_REQUEST_FIELDS = {"language", "aspect_ratio", "duration_seconds", "scenes"}
_REQUEST_SCENE_FIELDS = {
    "scene_id",
    "start_seconds",
    "duration_seconds",
    "end_seconds",
    "narration",
    "visual_intent",
    "character_action",
    "continuity_notes",
}
_SNAPSHOT_FIELDS = {
    "snapshot_id",
    "source",
    "currency",
    "production_request_reference",
    "line_items",
}
_SNAPSHOT_ITEM_FIELDS = {
    "scene_id",
    "operation",
    "unit",
    "quantity",
    "unit_price_micros",
}
_ESTIMATE_FIELDS = {"subtotals", "per_attempt_amount_micros", "policy_maximum_amount_micros"}
_CURRENCY_RE = re.compile(r"^[A-Z]{3}$")


@dataclass(frozen=True, slots=True)
class PriceLineItem:
    """One deterministic fixture quote for one Scene operation."""

    scene_id: str
    operation: str
    unit: str
    quantity: int
    unit_price_micros: int


@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    """The caller-supplied, immutable price input used for one Request Version."""

    snapshot_id: str
    source: str
    currency: str
    production_request_reference: ArtifactReference
    line_items: tuple[PriceLineItem, ...]

    def __post_init__(self) -> None:
        try:
            normalized = tuple(self.line_items)
        except Exception:
            normalized = self.line_items
        object.__setattr__(self, "line_items", normalized)


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Bounded retry policy used by the budget estimate."""

    maximum_attempts: int


@dataclass(frozen=True, slots=True)
class BudgetFailure:
    """Safe validation or execution failure for the budget seams."""

    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class BudgetDecisionRecord:
    """Immutable Creator decision bound to exact Request and Budget Versions."""

    decision_id: str
    task_id: str
    thread_id: str
    creator_id: str
    gate_kind: str
    production_request_reference: ArtifactReference
    budget_reference: ArtifactReference
    action: str
    authorization_id: str | None
    maximum_approved_amount_micros: int | None
    maximum_attempts: int | None
    decided_at: datetime
    decision_context: str


@dataclass(frozen=True, slots=True)
class BudgetAuthorizationRecord:
    """Independent authorization for later production side effects."""

    authorization_id: str
    decision_id: str
    task_id: str
    thread_id: str
    creator_id: str
    production_request_reference: ArtifactReference
    budget_reference: ArtifactReference
    price_snapshot: PriceSnapshot
    currency: str
    maximum_approved_amount_micros: int
    maximum_attempts: int
    decided_at: datetime


@dataclass(frozen=True, slots=True)
class BudgetDecisionOutcome:
    """The immutable decision and optional independent authorization."""

    decision: BudgetDecisionRecord
    authorization: BudgetAuthorizationRecord | None


class _BudgetValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class BudgetModule:
    """Estimate a provider-neutral budget without lookup or external calls."""

    @staticmethod
    def estimate(
        production_request_reference: ArtifactReference,
        resolved_production_request: ArtifactVersion,
        *,
        price_snapshot: PriceSnapshot,
        retry_policy: RetryPolicy,
        budget_identity: str,
        budget_commit_id: str,
    ) -> ArtifactCandidate | BudgetFailure:
        try:
            scene_ids = _validate_request(production_request_reference, resolved_production_request)
            _validate_identity(budget_identity, "INVALID_BUDGET_IDENTITY", "Budget identity is required")
            _validate_identity(
                budget_commit_id,
                "INVALID_BUDGET_COMMIT_ID",
                "logical Commit identity is required",
            )
            snapshot = _canonical_snapshot(price_snapshot, production_request_reference, scene_ids)
            policy = _canonical_retry_policy(retry_policy)
            estimate = _estimate(snapshot, policy)
            payload = {
                "production_request_reference": production_request_reference,
                "price_snapshot": _snapshot_payload(snapshot),
                "retry_policy": {"maximum_attempts": policy.maximum_attempts},
                "estimate": estimate,
            }
            return ArtifactCandidate(
                artifact_type="production_budget",
                identity=budget_identity,
                payload=payload,
                provenance=(
                    {
                        "purpose": "budget_estimation",
                        "production_request_reference": production_request_reference,
                        "price_snapshot_id": snapshot.snapshot_id,
                    },
                ),
                dependencies=(production_request_reference,),
                validated=True,
                commit_id=budget_commit_id,
            )
        except _BudgetValidation as exc:
            return BudgetFailure("validation", exc.code, exc.message)
        except Exception:
            return BudgetFailure(
                "execution", "BUDGET_ESTIMATION_FAILED", "budget estimation failed"
            )


class BudgetAuthorizationBoundary:
    """Record mandatory Creator Budget Review and independent authorization."""

    def __init__(self) -> None:
        self._decisions: dict[str, BudgetDecisionRecord] = {}
        self._authorizations: dict[str, BudgetAuthorizationRecord] = {}

    def decide(
        self,
        production_request_reference: ArtifactReference,
        resolved_production_request: ArtifactVersion,
        budget_reference: ArtifactReference,
        resolved_budget: ArtifactVersion,
        *,
        decision_id: str,
        authorization_id: str | None,
        task_id: str,
        thread_id: str,
        creator_id: str,
        decided_at: datetime,
        action: str,
        maximum_approved_amount_micros: int | None = None,
        maximum_attempts: int | None = None,
        decision_context: str = "",
    ) -> BudgetDecisionOutcome | BudgetFailure:
        try:
            scene_ids = _validate_request(production_request_reference, resolved_production_request)
            budget_payload = _validate_budget(
                production_request_reference,
                budget_reference,
                resolved_budget,
                scene_ids,
            )
            _validate_identity(decision_id, "INVALID_DECISION_ID", "decision identity is required")
            _validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
            _validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")
            _validate_identity(creator_id, "INVALID_CREATOR_ID", "Creator identity is required")
            _validate_time(decided_at)
            if action not in {"approve", "reject"}:
                raise _BudgetValidation("INVALID_DECISION_ACTION", "budget decision action is invalid")
            _validate_context(decision_context, action)

            if action == "reject":
                if authorization_id is not None or maximum_approved_amount_micros is not None or maximum_attempts is not None:
                    raise _BudgetValidation(
                        "INVALID_REJECTION_FIELDS",
                        "rejected Budget Review cannot carry authorization fields",
                    )
                authorization = None
            else:
                _validate_identity(
                    authorization_id,
                    "INVALID_AUTHORIZATION_ID",
                    "authorization identity is required",
                )
                _positive_int(
                    maximum_approved_amount_micros,
                    "INVALID_APPROVED_AMOUNT",
                    "approved amount must be a positive integer",
                )
                maximum_attempts = _validate_attempts(
                    maximum_attempts, budget_payload["retry_policy"]["maximum_attempts"]
                )
                required = budget_payload["estimate"]["per_attempt_amount_micros"] * maximum_attempts
                if maximum_approved_amount_micros < required:
                    raise _BudgetValidation(
                        "UNDERFUNDED_AUTHORIZATION",
                        "approved amount does not cover the selected attempts",
                    )
                authorization = BudgetAuthorizationRecord(
                    authorization_id=authorization_id,
                    decision_id=decision_id,
                    task_id=task_id,
                    thread_id=thread_id,
                    creator_id=creator_id,
                    production_request_reference=production_request_reference,
                    budget_reference=budget_reference,
                    price_snapshot=budget_payload["price_snapshot"],
                    currency=budget_payload["price_snapshot"].currency,
                    maximum_approved_amount_micros=maximum_approved_amount_micros,
                    maximum_attempts=maximum_attempts,
                    decided_at=decided_at,
                )

            decision = BudgetDecisionRecord(
                decision_id=decision_id,
                task_id=task_id,
                thread_id=thread_id,
                creator_id=creator_id,
                gate_kind="budget_review",
                production_request_reference=production_request_reference,
                budget_reference=budget_reference,
                action=action,
                authorization_id=authorization_id,
                maximum_approved_amount_micros=maximum_approved_amount_micros,
                maximum_attempts=maximum_attempts,
                decided_at=decided_at,
                decision_context=decision_context,
            )
            existing = self._decisions.get(decision_id)
            existing_authorization = (
                self._authorizations.get(authorization_id) if authorization_id is not None else None
            )
            if existing is not None:
                if existing != decision:
                    raise _BudgetValidation("DECISION_CONFLICT", "decision identity was already used with different input")
                if existing.authorization_id is None:
                    return BudgetDecisionOutcome(existing, None)
                if existing_authorization is None or existing_authorization != authorization:
                    raise _BudgetValidation("DECISION_CONFLICT", "decision identity was already used with different input")
                return BudgetDecisionOutcome(existing, existing_authorization)
            if authorization is not None:
                prior = self._authorizations.get(authorization.authorization_id)
                if prior is not None:
                    raise _BudgetValidation(
                        "AUTHORIZATION_CONFLICT",
                        "authorization identity was already used with different decision",
                    )
            self._decisions[decision_id] = decision
            if authorization is not None:
                self._authorizations[authorization.authorization_id] = authorization
            return BudgetDecisionOutcome(decision, authorization)
        except _BudgetValidation as exc:
            return BudgetFailure("validation", exc.code, exc.message)
        except Exception:
            return BudgetFailure(
                "execution", "BUDGET_AUTHORIZATION_FAILED", "budget decision could not be recorded"
            )

    def get_decision(self, decision_id: str) -> BudgetDecisionRecord | BudgetFailure:
        try:
            _validate_identity(decision_id, "INVALID_DECISION_ID", "decision identity is required")
            try:
                return self._decisions[decision_id]
            except KeyError:
                return BudgetFailure("validation", "DECISION_NOT_FOUND", "decision record does not exist")
        except _BudgetValidation as exc:
            return BudgetFailure("validation", exc.code, exc.message)
        except Exception:
            return BudgetFailure("execution", "BUDGET_AUTHORIZATION_FAILED", "decision lookup failed")

    def get_authorization(self, authorization_id: str) -> BudgetAuthorizationRecord | BudgetFailure:
        try:
            _validate_identity(
                authorization_id,
                "INVALID_AUTHORIZATION_ID",
                "authorization identity is required",
            )
            try:
                return self._authorizations[authorization_id]
            except KeyError:
                return BudgetFailure(
                    "validation", "AUTHORIZATION_NOT_FOUND", "authorization record does not exist"
                )
        except _BudgetValidation as exc:
            return BudgetFailure("validation", exc.code, exc.message)
        except Exception:
            return BudgetFailure("execution", "BUDGET_AUTHORIZATION_FAILED", "authorization lookup failed")


def _validate_request(
    reference: ArtifactReference, version: ArtifactVersion
) -> tuple[str, ...]:
    _validate_reference(reference, "production_request")
    if not isinstance(version, ArtifactVersion):
        raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_VERSION", "a resolved Production Request Version is required")
    if version.reference != reference:
        raise _BudgetValidation("PRODUCTION_REQUEST_REFERENCE_MISMATCH", "Production Request Reference does not match Version")
    dependencies = version.dependencies
    expected_types = ("script", "character", "storyboard", "timeline")
    if not isinstance(dependencies, tuple) or len(dependencies) != 4 or any(
        not _valid_reference(dep, kind) for dep, kind in zip(dependencies, expected_types)
    ):
        raise _BudgetValidation("PRODUCTION_REQUEST_LINEAGE_MISMATCH", "Production Request dependencies are invalid")
    payload = version.payload
    if not isinstance(payload, Mapping) or set(payload) != _REQUEST_PAYLOAD_FIELDS:
        raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request payload is invalid")
    for key, dependency in zip(
        ("script_reference", "character_reference", "storyboard_reference", "timeline_reference"),
        dependencies,
    ):
        if payload.get(key) != dependency:
            raise _BudgetValidation("PRODUCTION_REQUEST_LINEAGE_MISMATCH", "Production Request lineage is invalid")
    for key in ("approval_decision_id", "storyboard_decision_id"):
        _validate_identity(payload.get(key), "INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request decision identity is invalid")
    request = payload.get("production_request")
    if not isinstance(request, Mapping) or set(request) != _REQUEST_FIELDS:
        raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "nested Production Request is invalid")
    _safe_text(request.get("language"), "INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request language is invalid")
    _safe_text(request.get("aspect_ratio"), "INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request aspect ratio is invalid")
    duration = _number(request.get("duration_seconds"), "INVALID_PRODUCTION_REQUEST_PAYLOAD")
    if duration <= 0:
        raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request duration is invalid")
    scenes = request.get("scenes")
    if not isinstance(scenes, tuple) or not scenes:
        raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request scenes are invalid")
    scene_ids: list[str] = []
    previous_end = 0.0
    for index, scene in enumerate(scenes):
        if not isinstance(scene, Mapping) or set(scene) != _REQUEST_SCENE_FIELDS:
            raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_SCENE", "Production Request scene is invalid")
        scene_id = _safe_scene_id(scene.get("scene_id"))
        if scene_id in scene_ids:
            raise _BudgetValidation("DUPLICATE_PRODUCTION_REQUEST_SCENE", "Production Request scene identities must be unique")
        scene_ids.append(scene_id)
        start = _number(scene.get("start_seconds"), "INVALID_PRODUCTION_REQUEST_SCENE")
        scene_duration = _number(scene.get("duration_seconds"), "INVALID_PRODUCTION_REQUEST_SCENE")
        end = _number(scene.get("end_seconds"), "INVALID_PRODUCTION_REQUEST_SCENE")
        if start < 0 or scene_duration <= 0 or end <= 0 or not math.isclose(start, previous_end, rel_tol=_TIMELINE_TOLERANCE, abs_tol=_TIMELINE_TOLERANCE) or not math.isclose(end, start + scene_duration, rel_tol=_TIMELINE_TOLERANCE, abs_tol=_TIMELINE_TOLERANCE):
            raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_SCENE", "Production Request scene timing is invalid")
        for key in ("narration", "visual_intent", "character_action"):
            _safe_text(scene.get(key), "INVALID_PRODUCTION_REQUEST_SCENE", "Production Request scene content is invalid")
        notes = scene.get("continuity_notes")
        if not isinstance(notes, tuple) or not notes or len(notes) > 32 or any(
            not isinstance(note, str) or not note.strip() or len(note) > _MAX_TEXT_LENGTH or _has_control(note)
            for note in notes
        ) or len(set(notes)) != len(notes):
            raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_SCENE", "Production Request continuity notes are invalid")
        previous_end = end
    if not math.isclose(previous_end, duration, rel_tol=_TIMELINE_TOLERANCE, abs_tol=_TIMELINE_TOLERANCE):
        raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request duration does not match scenes")
    return tuple(scene_ids)


def _canonical_snapshot(
    snapshot: PriceSnapshot, request_reference: ArtifactReference, scene_ids: tuple[str, ...]
) -> PriceSnapshot:
    if not isinstance(snapshot, PriceSnapshot):
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT", "a PriceSnapshot is required")
    _validate_identity(snapshot.snapshot_id, "INVALID_PRICE_SNAPSHOT", "price snapshot identity is invalid")
    _safe_text(snapshot.source, "INVALID_PRICE_SNAPSHOT", "price snapshot source is invalid")
    if not isinstance(snapshot.currency, str) or _CURRENCY_RE.fullmatch(snapshot.currency) is None:
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT", "price snapshot currency is invalid")
    if snapshot.production_request_reference != request_reference:
        raise _BudgetValidation("PRICE_SNAPSHOT_REQUEST_MISMATCH", "price snapshot Request Reference does not match")
    items = snapshot.line_items
    if not isinstance(items, tuple) or len(items) != len(scene_ids) * 2:
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT_COVERAGE", "price snapshot coverage is invalid")
    by_key: dict[tuple[str, str], PriceLineItem] = {}
    for item in items:
        if not isinstance(item, PriceLineItem):
            raise _BudgetValidation("INVALID_PRICE_LINE_ITEM", "price snapshot line item is invalid")
        _safe_scene_id(item.scene_id)
        if item.operation not in {"visual", "voice"}:
            raise _BudgetValidation("INVALID_PRICE_LINE_ITEM", "price line operation is invalid")
        _safe_text(item.unit, "INVALID_PRICE_LINE_ITEM", "price line unit is invalid", limit=_MAX_UNIT_LENGTH)
        _positive_int(item.quantity, "INVALID_PRICE_LINE_ITEM", "price quantity must be a positive integer")
        _positive_int(item.unit_price_micros, "INVALID_PRICE_LINE_ITEM", "unit price must be a positive integer")
        key = (item.scene_id, item.operation)
        if key in by_key:
            raise _BudgetValidation("DUPLICATE_PRICE_LINE_ITEM", "price snapshot contains duplicate coverage")
        by_key[key] = item
    expected = {(scene_id, operation) for scene_id in scene_ids for operation in ("visual", "voice")}
    if set(by_key) != expected:
        raise _BudgetValidation("INVALID_PRICE_SNAPSHOT_COVERAGE", "price snapshot must quote each Scene visual and voice operation")
    ordered = tuple(by_key[(scene_id, operation)] for scene_id in scene_ids for operation in ("visual", "voice"))
    return PriceSnapshot(snapshot.snapshot_id, snapshot.source, snapshot.currency, request_reference, ordered)


def _canonical_retry_policy(policy: RetryPolicy) -> RetryPolicy:
    if not isinstance(policy, RetryPolicy):
        raise _BudgetValidation("INVALID_RETRY_POLICY", "a RetryPolicy is required")
    return RetryPolicy(_validate_attempts(policy.maximum_attempts, 3))


def _estimate(snapshot: PriceSnapshot, policy: RetryPolicy) -> dict[str, Any]:
    subtotals = tuple(
        {
            "scene_id": item.scene_id,
            "operation": item.operation,
            "subtotal_micros": item.quantity * item.unit_price_micros,
        }
        for item in snapshot.line_items
    )
    per_attempt = sum(row["subtotal_micros"] for row in subtotals)
    return {
        "subtotals": subtotals,
        "per_attempt_amount_micros": per_attempt,
        "policy_maximum_amount_micros": per_attempt * policy.maximum_attempts,
    }


def _snapshot_payload(snapshot: PriceSnapshot) -> dict[str, Any]:
    return {
        "snapshot_id": snapshot.snapshot_id,
        "source": snapshot.source,
        "currency": snapshot.currency,
        "production_request_reference": snapshot.production_request_reference,
        "line_items": tuple(
            {
                "scene_id": item.scene_id,
                "operation": item.operation,
                "unit": item.unit,
                "quantity": item.quantity,
                "unit_price_micros": item.unit_price_micros,
            }
            for item in snapshot.line_items
        ),
    }


def _validate_budget(
    request_reference: ArtifactReference,
    budget_reference: ArtifactReference,
    version: ArtifactVersion,
    scene_ids: tuple[str, ...],
) -> dict[str, Any]:
    _validate_reference(budget_reference, "production_budget")
    if not isinstance(version, ArtifactVersion):
        raise _BudgetValidation("INVALID_BUDGET_VERSION", "a resolved Budget Version is required")
    if version.reference != budget_reference:
        raise _BudgetValidation("BUDGET_REFERENCE_MISMATCH", "Budget Reference does not match Version")
    if version.dependencies != (request_reference,):
        raise _BudgetValidation("BUDGET_LINEAGE_MISMATCH", "Budget dependencies are invalid")
    payload = version.payload
    if not isinstance(payload, Mapping) or set(payload) != {
        "production_request_reference", "price_snapshot", "retry_policy", "estimate"
    }:
        raise _BudgetValidation("INVALID_BUDGET_PAYLOAD", "Budget payload is invalid")
    if payload.get("production_request_reference") != request_reference:
        raise _BudgetValidation("BUDGET_LINEAGE_MISMATCH", "Budget Request Reference does not match")
    snapshot = _snapshot_from_payload(payload.get("price_snapshot"))
    snapshot = _canonical_snapshot(snapshot, request_reference, scene_ids)
    policy_raw = payload.get("retry_policy")
    if not isinstance(policy_raw, Mapping) or set(policy_raw) != {"maximum_attempts"}:
        raise _BudgetValidation("INVALID_BUDGET_PAYLOAD", "Budget retry policy is invalid")
    policy = _canonical_retry_policy(RetryPolicy(policy_raw.get("maximum_attempts")))
    estimate = payload.get("estimate")
    expected = _estimate(snapshot, policy)
    if not _estimate_matches(estimate, expected):
        raise _BudgetValidation("INVALID_BUDGET_ESTIMATE", "Budget estimate is invalid")
    return {"price_snapshot": snapshot, "retry_policy": {"maximum_attempts": policy.maximum_attempts}, "estimate": expected}


def _snapshot_from_payload(value: object) -> PriceSnapshot:
    if not isinstance(value, Mapping) or set(value) != _SNAPSHOT_FIELDS:
        raise _BudgetValidation("INVALID_BUDGET_PAYLOAD", "Budget price snapshot is invalid")
    raw_items = value.get("line_items")
    if not isinstance(raw_items, tuple):
        raise _BudgetValidation("INVALID_BUDGET_PAYLOAD", "Budget price snapshot line items are invalid")
    items = []
    for raw in raw_items:
        if not isinstance(raw, Mapping) or set(raw) != _SNAPSHOT_ITEM_FIELDS:
            raise _BudgetValidation("INVALID_BUDGET_PAYLOAD", "Budget price line item is invalid")
        items.append(PriceLineItem(**{key: raw[key] for key in _SNAPSHOT_ITEM_FIELDS}))
    return PriceSnapshot(
        snapshot_id=value.get("snapshot_id"),
        source=value.get("source"),
        currency=value.get("currency"),
        production_request_reference=value.get("production_request_reference"),
        line_items=tuple(items),
    )


def _estimate_matches(value: object, expected: Mapping[str, Any]) -> bool:
    if not isinstance(value, Mapping) or set(value) != _ESTIMATE_FIELDS:
        return False
    if type(value.get("per_attempt_amount_micros")) is not int:
        return False
    if type(value.get("policy_maximum_amount_micros")) is not int:
        return False
    subtotals = value.get("subtotals")
    if not isinstance(subtotals, tuple) or len(subtotals) != len(expected["subtotals"]):
        return False
    for row in subtotals:
        if (
            not isinstance(row, Mapping)
            or set(row) != {"scene_id", "operation", "subtotal_micros"}
            or not isinstance(row.get("scene_id"), str)
            or row.get("operation") not in {"visual", "voice"}
            or type(row.get("subtotal_micros")) is not int
        ):
            return False
    return value == expected


def _validate_reference(value: object, artifact_type: str) -> None:
    if not _valid_reference(value, artifact_type):
        raise _BudgetValidation(
            f"INVALID_{artifact_type.upper()}_REFERENCE",
            f"an exact {artifact_type} Reference is required",
        )


def _valid_reference(value: object, artifact_type: str) -> bool:
    return (
        isinstance(value, ArtifactReference)
        and value.artifact_type == artifact_type
        and _valid_identity(value.identity)
        and isinstance(value.version, int)
        and not isinstance(value.version, bool)
        and value.version > 0
    )


def _validate_identity(value: object, code: str, message: str) -> None:
    if not _valid_identity(value):
        raise _BudgetValidation(code, message)


def _valid_identity(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value.strip())
        and len(value) <= _MAX_IDENTITY_LENGTH
        and value.strip().casefold() not in {"latest", "current"}
        and not _has_control(value)
    )


def _safe_text(value: object, code: str, message: str, *, limit: int = _MAX_TEXT_LENGTH) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit or _has_control(value):
        raise _BudgetValidation(code, message)
    return value


def _safe_scene_id(value: object) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > _MAX_SCENE_ID_LENGTH or _has_control(value):
        raise _BudgetValidation("INVALID_PRODUCTION_REQUEST_SCENE", "Scene identity is invalid")
    return value


def _positive_int(value: object, code: str, message: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise _BudgetValidation(code, message)
    return value


def _validate_attempts(value: object, maximum: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > maximum:
        raise _BudgetValidation("INVALID_MAXIMUM_ATTEMPTS", "maximum attempts are outside the approved policy")
    return value


def _number(value: object, code: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise _BudgetValidation(code, "numeric value is invalid")
    try:
        normalized = float(value)
    except (OverflowError, ValueError):
        raise _BudgetValidation(code, "numeric value is invalid") from None
    if not math.isfinite(normalized):
        raise _BudgetValidation(code, "numeric value is invalid")
    return normalized


def _validate_time(value: object) -> None:
    try:
        aware = isinstance(value, datetime) and value.tzinfo is not None and value.utcoffset() is not None
    except Exception:
        aware = False
    if not aware:
        raise _BudgetValidation("INVALID_DECIDED_AT", "decided_at must be timezone-aware")


def _validate_context(value: object, action: str) -> None:
    if not isinstance(value, str) or len(value) > _MAX_TEXT_LENGTH or _has_control(value) or action == "reject" and not value.strip():
        raise _BudgetValidation("INVALID_DECISION_CONTEXT", "decision context must be safe and bounded")


def _has_control(value: str) -> bool:
    return any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)


__all__ = [
    "BudgetAuthorizationBoundary",
    "BudgetAuthorizationRecord",
    "BudgetDecisionOutcome",
    "BudgetDecisionRecord",
    "BudgetFailure",
    "BudgetModule",
    "PriceLineItem",
    "PriceSnapshot",
    "RetryPolicy",
]
