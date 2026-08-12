"""Claim-gated, provider-neutral execution of one offline media operation."""
from __future__ import annotations
from collections.abc import Callable, Mapping
from datetime import datetime
import math
from ai_course_factory.artifacts import ArtifactReference, ArtifactVersion
from ai_course_factory.persistence import WorkspaceFileReference
from .attempt import (
    ProviderAttemptClaim,
    ProviderAttemptFailure,
    ProviderAttemptLedger,
    ProviderAttemptOutcome,
    ProviderAttemptRecord,
    ProviderAttemptReservation,
)
from .budget import _validate_request
from .composition import compose_product_path
from .interfaces import VisualGenerator, VoiceGenerator
from .model import (
    MediaGenerationResult,
    MediaCompositionTask,
    ProductionCompositionResult,
    ProductionExecutionResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VoiceSynthesisTask,
)
_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-:")
_NAME_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-")
_SAFE_KINDS = frozenset(("validation", "execution"))
_GENERATION_FAILURE = "GENERATION_FAILED"
_STORAGE_FAILURE = "ATTEMPT_STORAGE_FAILED"

class _Validation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
def _failure(kind: str, code: str, message: str) -> ProductionMediaFailure:
    return ProductionMediaFailure(kind, code, message)

def _storage_failure() -> ProductionMediaFailure:
    return _failure("execution", _STORAGE_FAILURE, "provider attempt persistence failed")
def _generation_failure() -> ProductionMediaFailure:
    return _failure("execution", _GENERATION_FAILURE, "media generation failed")

def _safe_text(value: object, *, limit: int, allow_colon: bool = True) -> str:
    chars = _ID_CHARS if allow_colon else _NAME_CHARS
    if (
        type(value) is not str
        or not value
        or len(value) > limit
        or value.casefold() in {"latest", "current"}
        or value[0] not in chars
        or any(character not in chars for character in value)
    ):
        raise _Validation("INVALID_MEDIA_TASK", "media task identity is invalid")
    return value

def _aware_time(value: object) -> datetime:
    if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
        raise _Validation("INVALID_RESERVATION", "provider attempt reservation is invalid")
    return value

def _exact_reference(value: object, artifact_type: str) -> ArtifactReference:
    if type(value) is not ArtifactReference or type(value.artifact_type) is not str or value.artifact_type != artifact_type:
        raise _Validation("INVALID_ARTIFACT_REFERENCE", "an exact Artifact Reference is required")
    identity = value.identity
    if (
        type(identity) is not str
        or not identity.strip()
        or len(identity) > 256
        or identity.strip().casefold() in {"latest", "current"}
        or any(ord(character) < 32 or ord(character) == 127 for character in identity)
        or type(value.version) is not int
        or isinstance(value.version, bool)
        or value.version < 1
    ):
        raise _Validation("INVALID_ARTIFACT_REFERENCE", "an exact Artifact Reference is required")
    return value

def _bounded_text(value: object, *, limit: int = 4096) -> str:
    if type(value) is not str or not value or len(value) > limit or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise _Validation("INVALID_MEDIA_TASK", "media task text is invalid")
    return value

def _workspace_reference(value: object, task_id: str, area: str) -> WorkspaceFileReference:
    if type(value) is not WorkspaceFileReference or type(value.task_id) is not str or type(value.area) is not str or type(value.name) is not str:
        raise _Validation("WORKSPACE_REFERENCE_MISMATCH", "workspace reference does not match the operation")
    if value.task_id != task_id or value.area != area:
        raise _Validation("WORKSPACE_REFERENCE_MISMATCH", "workspace reference does not match the operation")
    _safe_text(value.task_id, limit=128)
    _safe_text(value.name, limit=128, allow_colon=False)
    return value

def _duration(value: object) -> int | float:
    if type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(value) or value <= 0:
        raise _Validation("INVALID_MEDIA_TASK", "media task duration is invalid")
    return value

def _validate_reservation(reservation: object) -> ProviderAttemptReservation:
    if type(reservation) is not ProviderAttemptReservation:
        raise _Validation("INVALID_RESERVATION", "provider attempt reservation is invalid")
    for value, limit in ((reservation.attempt_id, 256), (reservation.task_id, 128), (reservation.authorization_id, 256), (reservation.scene_id, 128), (reservation.provider, 128), (reservation.idempotency_key, 256)):
        _safe_text(value, limit=limit)
    if type(reservation.operation) is not str or reservation.operation not in {"visual", "voice"}:
        raise _Validation("INVALID_OPERATION", "provider operation is invalid")
    _workspace_reference(reservation.request_record_reference, reservation.task_id, "provider-records")
    _aware_time(reservation.reserved_at)
    return reservation

def _validate_request_and_scene(
    production_request_reference: object,
    production_request_version: object,
    reservation: object,
    media_task: object,
) -> tuple[ArtifactReference, ArtifactVersion, ProviderAttemptReservation, str, Mapping[str, object]]:
    try:
        production_request_reference = _exact_reference(production_request_reference, "production_request")
    except _Validation as exc:
        raise _Validation("INVALID_PRODUCTION_REQUEST_REFERENCE", exc.message) from None
    if type(production_request_version) is not ArtifactVersion:
        raise _Validation("INVALID_PRODUCTION_REQUEST_VERSION", "a resolved Production Request Version is required")
    _exact_reference(production_request_version.reference, "production_request")
    try:
        _validate_request(production_request_reference, production_request_version)
    except Exception as exc:
        code = getattr(exc, "code", "INVALID_PRODUCTION_REQUEST_VERSION")
        message = getattr(exc, "message", "Production Request is invalid")
        raise _Validation(code, message) from None

    normalized_reservation = _validate_reservation(reservation)
    if type(media_task) is VisualGenerationTask:
        operation = "visual"
    elif type(media_task) is VoiceSynthesisTask:
        operation = "voice"
    else:
        raise _Validation("INVALID_MEDIA_TASK", "media task is invalid")

    task_id, attempt_id, scene_id = (_safe_text(value, limit=limit) for value, limit in ((media_task.task_id, 128), (media_task.attempt_id, 256), (media_task.scene_id, 128)))
    _exact_reference(media_task.production_request_reference, "production_request")
    if media_task.production_request_reference != production_request_reference:
        raise _Validation("PRODUCTION_REQUEST_REFERENCE_MISMATCH", "media task Production Request does not match")
    if (
        normalized_reservation.task_id != task_id
        or normalized_reservation.attempt_id != attempt_id
        or normalized_reservation.scene_id != scene_id
        or normalized_reservation.operation != operation
    ):
        raise _Validation("RESERVATION_TASK_MISMATCH", "provider attempt reservation does not match media task")
    _workspace_reference(media_task.output_reference, task_id, "media")
    duration = _duration(media_task.duration_seconds)

    payload = production_request_version.payload
    if not isinstance(payload, Mapping):
        raise _Validation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request payload is invalid")
    request = payload.get("production_request")
    scenes = request.get("scenes") if isinstance(request, Mapping) else None
    if not isinstance(scenes, tuple):
        raise _Validation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request scenes are invalid")
    scene = next((item for item in scenes if isinstance(item, Mapping) and item.get("scene_id") == scene_id), None)
    if not isinstance(scene, Mapping):
        raise _Validation("SCENE_NOT_FOUND", "requested Scene does not exist")
    if scene.get("duration_seconds") != duration:
        raise _Validation("MEDIA_TASK_MISMATCH", "media task duration does not match Scene")
    if type(media_task) is VisualGenerationTask:
        _bounded_text(media_task.aspect_ratio, limit=128)
        _bounded_text(media_task.visual_intent)
        _bounded_text(media_task.character_action)
        if media_task.aspect_ratio != request.get("aspect_ratio"):
            raise _Validation("MEDIA_TASK_MISMATCH", "visual task aspect ratio does not match Request")
        if media_task.visual_intent != scene.get("visual_intent") or media_task.character_action != scene.get("character_action"):
            raise _Validation("MEDIA_TASK_MISMATCH", "visual task does not match Scene")
    else:
        _bounded_text(media_task.language, limit=128)
        _bounded_text(media_task.narration)
        if media_task.language != request.get("language") or media_task.narration != scene.get("narration"):
            raise _Validation("MEDIA_TASK_MISMATCH", "voice task does not match Request")
    return production_request_reference, production_request_version, normalized_reservation, operation, scene

def _record_matches(
    record: ProviderAttemptRecord,
    reference: ArtifactReference,
    reservation: ProviderAttemptReservation,
) -> bool:
    return ((record.attempt_id, record.task_id, record.authorization_id, record.production_request_reference,
             record.scene_id, record.operation, record.provider, record.idempotency_key,
             record.request_record_reference, record.reserved_at)
            == (reservation.attempt_id, reservation.task_id, reservation.authorization_id, reference,
                reservation.scene_id, reservation.operation, reservation.provider, reservation.idempotency_key,
                reservation.request_record_reference, reservation.reserved_at)
            and type(record.attempt_number) is int and not isinstance(record.attempt_number, bool)
            and record.attempt_number > 0)

def _valid_claim_record(record: object, reference: ArtifactReference, reservation: ProviderAttemptReservation) -> bool:
    try:
        if type(record) is not ProviderAttemptRecord:
            return False
        for value, limit in ((record.attempt_id, 256), (record.task_id, 128), (record.authorization_id, 256), (record.scene_id, 128), (record.provider, 128), (record.idempotency_key, 256)):
            _safe_text(value, limit=limit)
        _exact_reference(record.production_request_reference, "production_request")
        _exact_reference(record.budget_reference, "production_budget")
        _workspace_reference(record.request_record_reference, reservation.task_id, "provider-records")
        if type(record.operation) is not str or record.operation not in {"visual", "voice"} or type(record.attempt_number) is not int or isinstance(record.attempt_number, bool) or record.attempt_number < 1:
            return False
        if type(record.currency) is not str or len(record.currency) != 3 or not record.currency.isascii() or not record.currency.isupper() or type(record.reserved_amount_micros) is not int or isinstance(record.reserved_amount_micros, bool) or record.reserved_amount_micros < 1:
            return False
        _aware_time(record.reserved_at)
        if type(record.status) is not str or record.status not in {"started", "succeeded", "failed"} or type(record.output_references) is not tuple:
            return False
        if any(_workspace_reference(item, reservation.task_id, "media") is None for item in record.output_references):
            return False
        if record.completed_at is not None:
            _aware_time(record.completed_at)
        if record.charged_amount_micros is not None and (type(record.charged_amount_micros) is not int or isinstance(record.charged_amount_micros, bool) or record.charged_amount_micros < 0):
            return False
        if record.result_code is not None:
            _bounded_text(record.result_code, limit=128)
        if record.response_record_reference is not None:
            _workspace_reference(record.response_record_reference, reservation.task_id, "provider-records")
        if record.status == "started":
            if any(item is not None for item in (record.completed_at, record.charged_amount_micros, record.result_code, record.response_record_reference)) or record.output_references:
                return False
        elif record.completed_at is None or record.charged_amount_micros != 0 or record.result_code is None or record.completed_at < record.reserved_at:
            return False
        elif record.status == "failed" and (record.result_code == "SUCCESS" or record.output_references):
            return False
        elif record.status == "succeeded" and (record.result_code != "SUCCESS" or len(record.output_references) != 1):
            return False
        return _record_matches(record, reference, reservation)
    except Exception:
        return False

def _claim_failure(failure: ProviderAttemptFailure) -> ProductionMediaFailure:
    if type(failure.code) is not str or not failure.code or len(failure.code) > 128 or any(ord(char) < 32 or ord(char) == 127 for char in failure.code):
        return _storage_failure()
    messages = {
        "ATTEMPT_IN_PROGRESS": "a provider attempt is already in progress",
        "ATTEMPT_ALREADY_SUCCEEDED": "the provider attempt already succeeded",
        "ATTEMPT_LIMIT": "the provider attempt limit has been reached",
        "BUDGET_LIMIT": "the approved attempt budget has been exhausted",
    }
    kind = failure.kind if type(failure.kind) is str and failure.kind in _SAFE_KINDS else "execution"
    return _failure(kind, failure.code, messages.get(failure.code, "provider attempt could not be claimed"))

def _result_matches(result: MediaGenerationResult, task: object, reservation: ProviderAttemptReservation, operation: str) -> bool:
    try:
        _safe_text(result.attempt_id, limit=256)
        _safe_text(result.scene_id, limit=128)
        _bounded_text(result.provider, limit=128)
        _bounded_text(result.media_type, limit=256)
        _workspace_reference(result.output_reference, task.task_id, "media")
        _duration(result.duration_seconds)
        if type(result.operation) is not str or type(result.result_code) is not str or result.result_code != "SUCCESS":
            return False
        return result.attempt_id == reservation.attempt_id and result.scene_id == reservation.scene_id and result.operation == operation and result.provider == reservation.provider and result.output_reference == task.output_reference and result.duration_seconds == task.duration_seconds
    except Exception:
        return False

def _failure_code(result: ProductionMediaFailure) -> str:
    code = result.code
    if type(code) is str and 0 < len(code) <= 128 and code != "SUCCESS" and not any(ord(char) < 32 or ord(char) == 127 for char in code):
        return code
    return _GENERATION_FAILURE

def _execution_result(
    record: ProviderAttemptRecord,
    reference: ArtifactReference,
    output_reference: WorkspaceFileReference,
) -> ProductionExecutionResult:
    return ProductionExecutionResult(
        record.task_id,
        record.attempt_id,
        reference,
        record.scene_id,
        record.operation,
        record.provider,
        output_reference,
        "SUCCESS",
    )

class ProductionOrchestrator:
    """Execute exactly one claimed visual or voice operation."""

    __slots__ = (
        "_attempt_ledger", "_visual_generator", "_voice_generator", "_clock",
        "_media_composer", "_artifact_repository",
    )

    def __init__(
        self,
        attempt_ledger: ProviderAttemptLedger,
        visual_generator: VisualGenerator,
        voice_generator: VoiceGenerator,
        *,
        clock: Callable[[], datetime],
        media_composer: object | None = None,
        artifact_repository: object | None = None,
    ) -> None:
        self._attempt_ledger = attempt_ledger
        self._visual_generator = visual_generator
        self._voice_generator = voice_generator
        self._clock = clock
        self._media_composer = media_composer
        self._artifact_repository = artifact_repository

    def execute(
        self,
        production_request_reference: ArtifactReference,
        production_request_version: ArtifactVersion,
        reservation: ProviderAttemptReservation,
        media_task: VisualGenerationTask | VoiceSynthesisTask,
    ) -> ProductionExecutionResult | ProductionMediaFailure:
        try:
            reference, _version, reservation, operation, _scene = _validate_request_and_scene(
                production_request_reference,
                production_request_version,
                reservation,
                media_task,
            )
        except _Validation as exc:
            return _failure("validation", exc.code, exc.message)
        except Exception:
            return _failure("validation", "INVALID_PRODUCTION_REQUEST", "Production Request is invalid")

        try:
            claim = self._attempt_ledger.claim(reservation)
        except Exception:
            return _storage_failure()
        if type(claim) is ProviderAttemptFailure:
            return _claim_failure(claim)
        if type(claim) is not ProviderAttemptClaim or type(claim.created) is not bool or type(claim.record) is not ProviderAttemptRecord:
            return _storage_failure()
        record = claim.record
        if not _valid_claim_record(record, reference, reservation):
            return _storage_failure()

        if not claim.created:
            if record.status == "started":
                return _failure("execution", "ATTEMPT_IN_PROGRESS", "a provider attempt is already in progress")
            if record.status == "failed":
                return _generation_failure()
            if record.charged_amount_micros != 0:
                return _storage_failure()
            output_reference = record.output_references[0]
            if output_reference != media_task.output_reference:
                return _storage_failure()
            return _execution_result(record, reference, output_reference)

        generated: object
        try:
            if operation == "visual":
                generated = self._visual_generator.generate(media_task)  # type: ignore[arg-type]
            else:
                generated = self._voice_generator.synthesize(media_task)  # type: ignore[arg-type]
        except Exception:
            generated = None

        succeeded = type(generated) is MediaGenerationResult and _result_matches(generated, media_task, reservation, operation)
        result_code = "SUCCESS" if succeeded else (
            _failure_code(generated) if type(generated) is ProductionMediaFailure else _GENERATION_FAILURE
        )
        try:
            completed_at = self._clock()
            if type(completed_at) is not datetime or completed_at.tzinfo is None or completed_at.utcoffset() is None or completed_at < record.reserved_at:
                return _storage_failure()
        except Exception:
            return _storage_failure()
        outcome = ProviderAttemptOutcome(
            record.attempt_id,
            "succeeded" if succeeded else "failed",
            completed_at,
            0,
            result_code,
            None,
            (media_task.output_reference,) if succeeded else (),
        )
        try:
            completed = self._attempt_ledger.complete(outcome)
        except Exception:
            return _storage_failure()
        if type(completed) is not ProviderAttemptRecord:
            return _storage_failure()
        if not _valid_claim_record(completed, reference, reservation):
            return _storage_failure()
        actual_terminal = (
            completed.status,
            completed.completed_at,
            completed.charged_amount_micros,
            completed.result_code,
            completed.response_record_reference,
            completed.output_references,
        )
        expected_terminal = (
            outcome.status,
            outcome.completed_at,
            outcome.charged_amount_micros,
            outcome.result_code,
            outcome.response_record_reference,
            outcome.output_references,
        )
        if actual_terminal != expected_terminal:
            return _storage_failure()
        if not succeeded:
            return _generation_failure()
        return _execution_result(record, reference, media_task.output_reference)

    def compose(
        self,
        production_request_reference: ArtifactReference,
        production_request_version: ArtifactVersion,
        composition_task: MediaCompositionTask,
        *,
        artifact_identity: str,
        composition_commit_id: str,
    ) -> ProductionCompositionResult | ProductionMediaFailure:
        return compose_product_path(
            self._attempt_ledger,
            self._media_composer,
            self._artifact_repository,
            production_request_reference,
            production_request_version,
            composition_task,
            artifact_identity=artifact_identity,
            composition_commit_id=composition_commit_id,
        )


__all__ = ["ProductionOrchestrator"]
