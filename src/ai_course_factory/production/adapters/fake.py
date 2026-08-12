"""Deterministic, no-cost Fixture adapters for the media interfaces."""

from __future__ import annotations

import json
import math
from typing import Any

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import (
    WorkspaceAdapter,
    WorkspaceFailure,
    WorkspaceFileRecord,
    WorkspaceFileReference,
)

from ..interfaces import VisualGenerator, VoiceGenerator
from ..model import (
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VoiceSynthesisTask,
)


_MAX_IDENTITY = 256
_MAX_COMPONENT = 128
_MAX_TEXT = 4096
_MAX_DURATION = 3600
_MAX_BYTES = 32 * 1024
_MAX_INT = 2**63 - 1
_ASCII_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
_WORKSPACE_NAME_CHARS = _ASCII_ALNUM | frozenset("._-")
_WORKSPACE_TASK_CHARS = _ASCII_ALNUM | frozenset("._-:")
_FORMAT = "ai-course-factory-fake-media"
_VISUAL_PROVIDER = "fake-visual-v1"
_VOICE_PROVIDER = "fake-voice-v1"
_VISUAL_MEDIA_TYPE = "application/x-ai-course-factory-fake-visual"
_VOICE_MEDIA_TYPE = "application/x-ai-course-factory-fake-voice"


class _InvalidTask(Exception):
    def __init__(self, code: str) -> None:
        self.code = code


def _failure(kind: str, code: str, message: str) -> ProductionMediaFailure:
    return ProductionMediaFailure(kind, code, message)


def _invalid(code: str) -> ProductionMediaFailure:
    return _failure("validation", code, "media generation task is invalid")


def _storage(code: str = "MEDIA_STORAGE_FAILED") -> ProductionMediaFailure:
    message = {
        "MEDIA_OUTPUT_CONFLICT": "media output reference conflicts with existing Fixture bytes",
        "MEDIA_STORAGE_FAILED": "media output storage failed",
    }[code]
    return _failure("execution", code, message)


def _safe_text(value: object, code: str, limit: int) -> str:
    if (
        type(value) is not str
        or not value.strip()
        or len(value) > limit
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise _InvalidTask(code)
    if value.strip().casefold() in {"latest", "current"}:
        raise _InvalidTask(code)
    return value


def _safe_identity(value: object, code: str, limit: int = _MAX_IDENTITY) -> str:
    return _safe_text(value, code, limit)


def _safe_workspace_task(value: object) -> str:
    value = _safe_text(value, "INVALID_TASK_ID", _MAX_COMPONENT)
    if value[0] not in _ASCII_ALNUM or any(character not in _WORKSPACE_TASK_CHARS for character in value):
        raise _InvalidTask("INVALID_TASK_ID")
    return value


def _safe_workspace_name(value: object) -> str:
    if (
        type(value) is not str
        or not value
        or len(value) > _MAX_COMPONENT
        or value.casefold() in {"latest", "current"}
        or value[0] not in _ASCII_ALNUM
        or any(character not in _WORKSPACE_NAME_CHARS for character in value)
    ):
        raise _InvalidTask("INVALID_OUTPUT_REFERENCE")
    return value


def _safe_artifact_reference(value: object) -> ArtifactReference:
    if type(value) is not ArtifactReference or value.artifact_type != "production_request":
        raise _InvalidTask("INVALID_PRODUCTION_REQUEST_REFERENCE")
    _safe_identity(value.identity, "INVALID_PRODUCTION_REQUEST_REFERENCE")
    if type(value.version) is not int or value.version < 1 or value.version > _MAX_INT:
        raise _InvalidTask("INVALID_PRODUCTION_REQUEST_REFERENCE")
    return value


def _safe_duration(value: object) -> int | float:
    if type(value) is int:
        if value <= 0 or value > _MAX_DURATION:
            raise _InvalidTask("INVALID_DURATION")
        return value
    if type(value) is not float or not math.isfinite(value) or value <= 0 or value > _MAX_DURATION:
        raise _InvalidTask("INVALID_DURATION")
    return value


def _safe_output_reference(value: object, task_id: str) -> WorkspaceFileReference:
    if type(value) is not WorkspaceFileReference or value.task_id != task_id or value.area != "media":
        raise _InvalidTask("INVALID_OUTPUT_REFERENCE")
    _safe_workspace_task(value.task_id)
    _safe_workspace_name(value.name)
    return value


def _validate_visual(task: object) -> VisualGenerationTask:
    if type(task) is not VisualGenerationTask:
        raise _InvalidTask("INVALID_VISUAL_TASK")
    _safe_workspace_task(task.task_id)
    _safe_identity(task.attempt_id, "INVALID_ATTEMPT_ID")
    _safe_identity(task.scene_id, "INVALID_SCENE_ID", _MAX_COMPONENT)
    _safe_artifact_reference(task.production_request_reference)
    if task.aspect_ratio != "9:16":
        raise _InvalidTask("INVALID_ASPECT_RATIO")
    _safe_duration(task.duration_seconds)
    _safe_text(task.visual_intent, "INVALID_VISUAL_INTENT", _MAX_TEXT)
    _safe_text(task.character_action, "INVALID_CHARACTER_ACTION", _MAX_TEXT)
    _safe_output_reference(task.output_reference, task.task_id)
    return task


def _validate_voice(task: object) -> VoiceSynthesisTask:
    if type(task) is not VoiceSynthesisTask:
        raise _InvalidTask("INVALID_VOICE_TASK")
    _safe_workspace_task(task.task_id)
    _safe_identity(task.attempt_id, "INVALID_ATTEMPT_ID")
    _safe_identity(task.scene_id, "INVALID_SCENE_ID", _MAX_COMPONENT)
    _safe_artifact_reference(task.production_request_reference)
    _safe_text(task.language, "INVALID_LANGUAGE", 128)
    _safe_duration(task.duration_seconds)
    _safe_text(task.narration, "INVALID_NARRATION", _MAX_TEXT)
    _safe_output_reference(task.output_reference, task.task_id)
    return task


def _artifact_payload(reference: ArtifactReference) -> dict[str, Any]:
    return {
        "artifact_type": reference.artifact_type,
        "identity": reference.identity,
        "version": reference.version,
    }


def _workspace_payload(reference: WorkspaceFileReference) -> dict[str, str]:
    return {"area": reference.area, "name": reference.name, "task_id": reference.task_id}


def _encode(operation: str, provider: str, media_type: str, task_fields: dict[str, Any]) -> bytes:
    envelope = {
        "format": _FORMAT,
        "media_type": media_type,
        "operation": operation,
        "provider": provider,
        "task": task_fields,
        "version": 1,
    }
    try:
        encoded = json.dumps(
            envelope,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except Exception:
        raise RuntimeError from None
    if len(encoded) > _MAX_BYTES:
        raise _InvalidTask("MEDIA_FIXTURE_TOO_LARGE")
    return encoded


def _commit_fixture(
    workspace: object,
    reference: WorkspaceFileReference,
    encoded: bytes,
) -> ProductionMediaFailure | None:
    try:
        result = workspace.commit(reference, encoded)
    except Exception:
        return _storage()
    expected = WorkspaceFileRecord(reference, len(encoded))
    try:
        if (
            type(result) is WorkspaceFileRecord
            and type(result.reference) is WorkspaceFileReference
            and type(result.size_bytes) is int
            and result == expected
        ):
            return None
        if isinstance(result, WorkspaceFailure) and result.code == "WORKSPACE_FILE_CONFLICT":
            return _storage("MEDIA_OUTPUT_CONFLICT")
    except Exception:
        return _storage()
    return _storage()


class DeterministicFakeVisualGenerator:
    """Write deterministic, explicitly non-playable visual Fixture bytes."""

    __slots__ = ("_workspace",)

    def __init__(self, workspace: WorkspaceAdapter) -> None:
        self._workspace = workspace

    def generate(self, task: VisualGenerationTask) -> MediaGenerationResult | ProductionMediaFailure:
        try:
            task = _validate_visual(task)
            encoded = _encode(
                "visual",
                _VISUAL_PROVIDER,
                _VISUAL_MEDIA_TYPE,
                {
                    "aspect_ratio": task.aspect_ratio,
                    "attempt_id": task.attempt_id,
                    "character_action": task.character_action,
                    "duration_seconds": task.duration_seconds,
                    "output_reference": _workspace_payload(task.output_reference),
                    "production_request_reference": _artifact_payload(task.production_request_reference),
                    "scene_id": task.scene_id,
                    "task_id": task.task_id,
                    "visual_intent": task.visual_intent,
                },
            )
        except _InvalidTask as error:
            return _invalid(error.code)
        except Exception:
            return _storage()
        failure = _commit_fixture(self._workspace, task.output_reference, encoded)
        if failure is not None:
            return failure
        return MediaGenerationResult(
            task.attempt_id,
            task.scene_id,
            "visual",
            _VISUAL_PROVIDER,
            task.output_reference,
            _VISUAL_MEDIA_TYPE,
            task.duration_seconds,
            "SUCCESS",
        )


class DeterministicFakeVoiceGenerator:
    """Write deterministic, explicitly non-playable voice Fixture bytes."""

    __slots__ = ("_workspace",)

    def __init__(self, workspace: WorkspaceAdapter) -> None:
        self._workspace = workspace

    def synthesize(self, task: VoiceSynthesisTask) -> MediaGenerationResult | ProductionMediaFailure:
        try:
            task = _validate_voice(task)
            encoded = _encode(
                "voice",
                _VOICE_PROVIDER,
                _VOICE_MEDIA_TYPE,
                {
                    "attempt_id": task.attempt_id,
                    "duration_seconds": task.duration_seconds,
                    "language": task.language,
                    "narration": task.narration,
                    "output_reference": _workspace_payload(task.output_reference),
                    "production_request_reference": _artifact_payload(task.production_request_reference),
                    "scene_id": task.scene_id,
                    "task_id": task.task_id,
                },
            )
        except _InvalidTask as error:
            return _invalid(error.code)
        except Exception:
            return _storage()
        failure = _commit_fixture(self._workspace, task.output_reference, encoded)
        if failure is not None:
            return failure
        return MediaGenerationResult(
            task.attempt_id,
            task.scene_id,
            "voice",
            _VOICE_PROVIDER,
            task.output_reference,
            _VOICE_MEDIA_TYPE,
            task.duration_seconds,
            "SUCCESS",
        )


__all__ = ["DeterministicFakeVisualGenerator", "DeterministicFakeVoiceGenerator"]
