"""Validated product-path composition behind ``ProductionOrchestrator``."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from types import MappingProxyType

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitError,
    ArtifactReference,
    ArtifactVersion,
    CommitConflictError,
    RevisionMismatchError,
)
from ai_course_factory.persistence import WorkspaceFileReference

from .adapters import fake as _fake
from .adapters.ffmpeg_composer import _task_valid
from .attempt import ProviderAttemptFailure, ProviderAttemptLedger, ProviderAttemptRecord
from .budget import _validate_request
from .model import (
    MediaCompositionResult,
    MediaCompositionTask,
    MediaGenerationResult,
    ProductionCompositionResult,
    ProductionMediaFailure,
)


_MAX_ARTIFACT_COMPONENT = 256
_COMMIT_FAILED = ProductionMediaFailure(
    "execution", "MEDIA_ARTIFACT_COMMIT_FAILED", "media Artifact persistence failed"
)
_COMMIT_CONFLICT = ProductionMediaFailure(
    "execution", "MEDIA_ARTIFACT_CONFLICT", "media Artifact identity conflicts with existing input"
)
_ATTEMPT_FAILED = ProductionMediaFailure(
    "execution", "ATTEMPT_STORAGE_FAILED", "provider attempt persistence failed"
)
_COMPOSITION_FAILED = ProductionMediaFailure(
    "execution", "MEDIA_COMPOSITION_FAILED", "local media composition failed"
)
_UNAVAILABLE = ProductionMediaFailure(
    "validation", "MEDIA_COMPOSITION_UNAVAILABLE", "media composition dependencies are unavailable"
)
_INVALID_CONTEXT = ProductionMediaFailure(
    "validation", "INVALID_COMPOSITION_CONTEXT", "media composition context is invalid"
)
_COMPOSER_FAILURE_MESSAGES = {
    "INVALID_COMPOSITION_TASK": ("validation", "media composition task is invalid"),
    "MEDIA_TOOL_UNAVAILABLE": ("validation", "media tool configuration is unavailable"),
    "INVALID_MEDIA_TOOL_TIMEOUT": ("validation", "media tool timeout is invalid"),
    "MEDIA_COMPOSITION_FAILED": ("execution", "local media composition failed"),
    "MEDIA_OUTPUT_CONFLICT": ("execution", "media output reference conflicts with existing Fixture bytes"),
    "MEDIA_STORAGE_FAILED": ("execution", "media output storage failed"),
}


class _InvalidContext(Exception):
    pass


class _AttemptStorage(Exception):
    pass


class _ArtifactStorage(Exception):
    pass


@dataclass(frozen=True, slots=True)
class _Context:
    task: MediaCompositionTask
    request_reference: ArtifactReference
    timeline_reference: ArtifactReference
    scenes: tuple[tuple[str, int, int, str], ...]


def _repository_capabilities(repository: object) -> tuple[object, object]:
    try:
        commit = getattr(repository, "commit")
        get = getattr(repository, "get")
    except Exception:
        raise _InvalidContext from None
    if not callable(commit) or not callable(get):
        raise _InvalidContext
    return commit, get


def _safe_token(value: object, *, limit: int = _MAX_ARTIFACT_COMPONENT) -> str:
    try:
        return _fake._safe_identity(value, "INVALID_COMPOSITION_CONTEXT", limit)
    except Exception:
        raise _InvalidContext from None


def _reference(value: object, artifact_type: str) -> ArtifactReference:
    if (
        type(value) is not ArtifactReference
        or type(value.artifact_type) is not str
        or value.artifact_type != artifact_type
        or type(value.identity) is not str
        or type(value.version) is not int
        or isinstance(value.version, bool)
        or not 1 <= value.version <= 2**63 - 1
    ):
        raise _InvalidContext
    _safe_token(value.identity)
    return value


def _same_reference(first: object, second: object) -> bool:
    return all(
        type(item) is ArtifactReference
        and type(item.artifact_type) is str
        and type(item.identity) is str
        and type(item.version) is int
        for item in (first, second)
    ) and (first.artifact_type, first.identity, first.version) == (second.artifact_type, second.identity, second.version)


def _milliseconds(value: object) -> int:
    if type(value) not in (int, float) or isinstance(value, bool) or not math.isfinite(value):
        raise _InvalidContext
    result = value * 1000
    if not math.isfinite(result) or result < 0 or result != round(result):
        raise _InvalidContext
    return int(round(result))


def _workspace_reference(value: object, task_id: str) -> None:
    if type(value) is not WorkspaceFileReference:
        raise _InvalidContext
    try:
        _fake._safe_output_reference(value, task_id)
    except Exception:
        raise _InvalidContext from None


def _workspace_payload(value: WorkspaceFileReference) -> Mapping[str, str]:
    return {"task_id": value.task_id, "area": value.area, "name": value.name}


def _exact_value_shape(value: object, active: set[int] | None = None) -> bool:
    if value is None or type(value) in (str, bool, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is ArtifactReference:
        return (
            type(value.artifact_type) is str
            and type(value.identity) is str
            and type(value.version) is int
            and value.version >= 1
        )
    if type(value) not in (dict, MappingProxyType, tuple):
        return False
    if active is None:
        active = set()
    marker = id(value)
    if marker in active:
        return False
    active.add(marker)
    try:
        values = value.items() if type(value) in (dict, MappingProxyType) else ((None, item) for item in value)
        return all(
            _exact_value_shape(key, active) and _exact_value_shape(item, active)
            for key, item in values
        )
    finally:
        active.remove(marker)


def _request_version_shape(value: object) -> None:
    if type(value) is not ArtifactVersion or not all(
        _exact_value_shape(getattr(value, field))
        for field in ("reference", "payload", "provenance", "dependencies", "commit_id", "prior_reference")
    ):
        raise _InvalidContext


def _validate_context(
    production_request_reference: object,
    production_request_version: object,
    task: object,
    artifact_identity: object,
    composition_commit_id: object,
) -> _Context:
    request_reference = _reference(production_request_reference, "production_request")
    _safe_token(artifact_identity)
    _safe_token(composition_commit_id)
    if type(production_request_version) is not ArtifactVersion:
        raise _InvalidContext
    _reference(production_request_version.reference, "production_request")
    try:
        _validate_request(request_reference, production_request_version)
    except Exception:
        raise _InvalidContext from None
    if type(task) is not MediaCompositionTask or not _task_valid(task):
        raise _InvalidContext
    _reference(task.timeline_reference, "timeline")
    payload = production_request_version.payload
    if not isinstance(payload, Mapping):
        raise _InvalidContext
    timeline_reference = payload.get("timeline_reference")
    _reference(timeline_reference, "timeline")
    if not _same_reference(task.production_request_reference, request_reference) or not _same_reference(task.timeline_reference, timeline_reference):
        raise _InvalidContext
    request = payload.get("production_request")
    request_scenes = request.get("scenes") if isinstance(request, Mapping) else None
    if not isinstance(request_scenes, tuple) or len(request_scenes) != len(task.scenes):
        raise _InvalidContext
    expected: list[tuple[str, int, int, str]] = []
    previous_end = 0
    for source, scene in zip(request_scenes, task.scenes):
        if not isinstance(source, Mapping) or type(source.get("scene_id")) is not str:
            raise _InvalidContext
        start = _milliseconds(source.get("start_seconds"))
        end = _milliseconds(source.get("end_seconds"))
        duration = _milliseconds(source.get("duration_seconds"))
        if start != previous_end or end <= start or end - start != duration:
            raise _InvalidContext
        if (
            scene.scene_id != source.get("scene_id")
            or scene.start_milliseconds != start
            or scene.end_milliseconds != end
            or scene.subtitle_text != source.get("narration")
        ):
            raise _InvalidContext
        expected.append((scene.scene_id, start, end, scene.subtitle_text))
        previous_end = end
    if not expected or previous_end != _milliseconds(request.get("duration_seconds")):
        raise _InvalidContext
    for scene_id, _start, _end, _text in expected:
        _safe_token(f"{artifact_identity}:{scene_id}")
        for kind in ("scene_clip", "scene_audio"):
            _safe_token(f"{composition_commit_id}:{kind}:{scene_id}")
    for kind in ("subtitle", "master_audio", "video"):
        _safe_token(f"{composition_commit_id}:{kind}")
    return _Context(task, request_reference, timeline_reference, tuple(expected))


def _media_result_valid(
    result: object,
    record: ProviderAttemptRecord,
    context: _Context,
    scene_id: str,
    start: int,
    end: int,
    operation: str,
) -> None:
    expected_type = "video/mp4" if operation == "visual" else "audio/mp4"
    if type(result) is not MediaGenerationResult:
        raise _InvalidContext
    if any(type(getattr(result, field)) is not str for field in ("attempt_id", "scene_id", "operation", "provider", "media_type", "result_code")):
        raise _InvalidContext
    if result.result_code != "SUCCESS" or result.operation != operation or result.media_type != expected_type or result.scene_id != scene_id:
        raise _InvalidContext
    if type(result.duration_seconds) not in (int, float) or isinstance(result.duration_seconds, bool) or not math.isfinite(result.duration_seconds) or result.duration_seconds != (end - start) / 1000:
        raise _InvalidContext
    if any(type(getattr(record, field)) is not str for field in ("attempt_id", "task_id", "status", "result_code", "scene_id", "operation", "provider")) or type(record.charged_amount_micros) is not int or isinstance(record.charged_amount_micros, bool):
        raise _AttemptStorage
    if (
        (record.status, record.charged_amount_micros, record.result_code, record.attempt_id, record.task_id, record.scene_id, record.operation, record.provider)
        != ("succeeded", 0, "SUCCESS", result.attempt_id, context.task.task_id, scene_id, operation, result.provider)
        or not _same_reference(record.production_request_reference, context.request_reference)
        or type(record.output_references) is not tuple
        or len(record.output_references) != 1
    ):
        raise _AttemptStorage
    try:
        _workspace_reference(record.output_references[0], context.task.task_id)
    except _InvalidContext:
        raise _AttemptStorage from None
    if type(record.output_references[0]) is not WorkspaceFileReference or record.output_references[0] != result.output_reference:
        raise _AttemptStorage


def _load_attempts(ledger: ProviderAttemptLedger, context: _Context) -> None:
    attempt_ids: set[str] = set()
    output_refs: set[object] = set()
    for scene, (scene_id, start, end, _text) in zip(context.task.scenes, context.scenes):
        for result, operation in ((scene.visual_result, "visual"), (scene.voice_result, "voice")):
            if type(result) is not MediaGenerationResult or result.attempt_id in attempt_ids:
                raise _InvalidContext
            attempt_ids.add(result.attempt_id)
            try:
                record = ledger.get(result.attempt_id)
            except Exception:
                raise _AttemptStorage from None
            if isinstance(record, ProviderAttemptFailure) or type(record) is not ProviderAttemptRecord:
                raise _AttemptStorage
            _media_result_valid(result, record, context, scene_id, start, end, operation)
            if result.output_reference in output_refs:
                raise _InvalidContext
            output_refs.add(result.output_reference)


def _deep_equal(value: object, expected: object) -> bool:
    if isinstance(expected, Mapping):
        if type(value) is not MappingProxyType or len(value) != len(expected):
            return False
        for expected_key, expected_item in expected.items():
            matches = [
                key for key in value
                if type(key) is type(expected_key) and key == expected_key
            ]
            if len(matches) != 1 or not _deep_equal(value[matches[0]], expected_item):
                return False
        return True
    if isinstance(expected, tuple):
        return type(value) is tuple and len(value) == len(expected) and all(_deep_equal(item, target) for item, target in zip(value, expected))
    if type(expected) is ArtifactReference:
        return _same_reference(value, expected)
    if type(expected) is str:
        return type(value) is str and value == expected
    if type(expected) is int:
        return type(value) is int and not isinstance(value, bool) and value == expected
    if type(expected) is float:
        return type(value) is float and value == expected
    return type(value) is type(expected) and value == expected


def _version_matches(version: object, reference: ArtifactReference, candidate: ArtifactCandidate) -> bool:
    return (
        type(version) is ArtifactVersion
        and _same_reference(version.reference, reference)
        and _deep_equal(version.payload, candidate.payload)
        and _deep_equal(version.provenance, candidate.provenance)
        and _deep_equal(version.dependencies, candidate.dependencies)
        and type(version.commit_id) is str
        and version.commit_id == candidate.commit_id
        and version.prior_reference is None
    )


def _same_version(first: object, second: object) -> bool:
    return (
        type(first) is ArtifactVersion
        and type(second) is ArtifactVersion
        and _deep_equal(first.reference, second.reference)
        and _deep_equal(first.payload, second.payload)
        and _deep_equal(first.provenance, second.provenance)
        and _deep_equal(first.dependencies, second.dependencies)
        and type(first.commit_id) is str
        and type(second.commit_id) is str
        and first.commit_id == second.commit_id
        and _deep_equal(first.prior_reference, second.prior_reference)
    )


def _verify_repository_inputs(repository: object, context: _Context, supplied_request: ArtifactVersion) -> None:
    try:
        request_version = repository.get(context.request_reference)
        timeline_version = repository.get(context.timeline_reference)
    except Exception:
        raise _ArtifactStorage from None
    if not _same_version(request_version, supplied_request):
        raise _InvalidContext
    if type(timeline_version) is not ArtifactVersion or not _same_reference(timeline_version.reference, context.timeline_reference):
        raise _InvalidContext


def _commit(repository: object, candidate: ArtifactCandidate) -> ArtifactReference | ProductionMediaFailure:
    try:
        reference = repository.commit(candidate)
    except (CommitConflictError, RevisionMismatchError):
        return _COMMIT_CONFLICT
    except ArtifactCommitError:
        return _COMMIT_FAILED
    except Exception:
        return _COMMIT_FAILED
    if (
        type(reference) is not ArtifactReference
        or type(reference.artifact_type) is not str
        or type(reference.identity) is not str
        or reference.artifact_type != candidate.artifact_type
        or reference.identity != candidate.identity
        or type(reference.version) is not int
        or isinstance(reference.version, bool)
        or reference.version != 1
    ):
        return _COMMIT_FAILED
    try:
        version = repository.get(reference)
    except Exception:
        return _COMMIT_FAILED
    try:
        return reference if _version_matches(version, reference, candidate) else _COMMIT_FAILED
    except Exception:
        return _COMMIT_FAILED


def _candidate(
    artifact_type: str,
    identity: str,
    payload: Mapping[str, object],
    dependencies: tuple[ArtifactReference, ...],
    commit_id: str,
    provenance: Mapping[str, object],
) -> ArtifactCandidate:
    return ArtifactCandidate(artifact_type, identity, payload, (provenance,), dependencies, True, commit_id)


def _composer_failure(value: object) -> ProductionMediaFailure:
    if type(value) is ProductionMediaFailure:
        item = _COMPOSER_FAILURE_MESSAGES.get(value.code)
        if (
            type(value.kind) is str
            and type(value.code) is str
            and type(value.message) is str
            and item is not None
            and value.kind == item[0]
            and value.message == item[1]
        ):
            return value
    return _COMPOSITION_FAILED


def _composition_result_valid(value: object, context: _Context) -> MediaCompositionResult:
    if type(value) is not MediaCompositionResult:
        raise _InvalidContext
    task = context.task
    if type(value.composition_id) is not str or value.composition_id != task.composition_id:
        raise _InvalidContext
    if not _same_reference(value.production_request_reference, context.request_reference) or not _same_reference(value.timeline_reference, context.timeline_reference):
        raise _InvalidContext
    if type(value.scene_ids) is not tuple or any(type(item) is not str for item in value.scene_ids) or value.scene_ids != tuple(item[0] for item in context.scenes):
        raise _InvalidContext
    if type(value.composer) is not str or not value.composer or type(value.media_type) is not str or value.media_type != "video/mp4":
        raise _InvalidContext
    if type(value.output_reference) is not WorkspaceFileReference or value.output_reference != task.output_reference:
        raise _InvalidContext
    if type(value.duration_milliseconds) is not int or isinstance(value.duration_milliseconds, bool) or value.duration_milliseconds != context.scenes[-1][2] or type(value.result_code) is not str or value.result_code != "SUCCESS":
        raise _InvalidContext
    _safe_token(value.composer, limit=128)
    _workspace_reference(value.output_reference, task.task_id)
    return value


def compose_product_path(
    ledger: ProviderAttemptLedger,
    composer: object,
    repository: object,
    production_request_reference: object,
    production_request_version: object,
    composition_task: object,
    *,
    artifact_identity: object,
    composition_commit_id: object,
) -> ProductionCompositionResult | ProductionMediaFailure:
    if composer is None or repository is None:
        return _UNAVAILABLE
    try:
        _repository_capabilities(repository)
        compose_method = getattr(composer, "compose")
    except Exception:
        return _UNAVAILABLE
    if not callable(compose_method):
        return _UNAVAILABLE
    try:
        _request_version_shape(production_request_version)
        context = _validate_context(
            production_request_reference,
            production_request_version,
            composition_task,
            artifact_identity,
            composition_commit_id,
        )
        _verify_repository_inputs(repository, context, production_request_version)
        _load_attempts(ledger, context)
    except _ArtifactStorage:
        return _COMMIT_FAILED
    except _AttemptStorage:
        return _ATTEMPT_FAILED
    except _InvalidContext:
        return _INVALID_CONTEXT
    except Exception:
        return _INVALID_CONTEXT

    task = context.task
    artifact_identity = str(artifact_identity)
    composition_commit_id = str(composition_commit_id)
    scene_clip_references: list[ArtifactReference] = []
    scene_audio_references: list[ArtifactReference] = []
    for (scene_id, start, end, _text), scene in zip(context.scenes, task.scenes):
        visual, voice = scene.visual_result, scene.voice_result
        for artifact_type, result, purpose, output in (
            ("scene_clip", visual, "production_composition_scene_clip", scene_clip_references),
            ("scene_audio", voice, "production_composition_scene_audio", scene_audio_references),
        ):
            candidate = _candidate(
                artifact_type,
                f"{artifact_identity}:{scene_id}",
                {
                    "production_request_reference": context.request_reference,
                    "scene_id": scene_id,
                    "attempt_id": result.attempt_id,
                    "provider": result.provider,
                    "output_reference": _workspace_payload(result.output_reference),
                    "media_type": result.media_type,
                    "duration_milliseconds": end - start,
                },
                (context.request_reference,),
                f"{composition_commit_id}:{artifact_type}:{scene_id}",
                {
                    "purpose": purpose,
                    "production_request_reference": context.request_reference,
                    "scene_id": scene_id,
                    "attempt_id": result.attempt_id,
                },
            )
            committed = _commit(repository, candidate)
            if isinstance(committed, ProductionMediaFailure):
                return committed
            output.append(committed)

    cues = tuple(
        MappingProxyType(
            {
                "scene_id": scene_id,
                "start_milliseconds": start,
                "end_milliseconds": end,
                "text": text,
            }
        )
        for scene_id, start, end, text in context.scenes
    )
    subtitle_candidate = _candidate(
        "subtitle",
        artifact_identity,
        {
            "production_request_reference": context.request_reference,
            "timeline_reference": context.timeline_reference,
            "cues": cues,
        },
        (context.request_reference, context.timeline_reference),
        f"{composition_commit_id}:subtitle",
        {
            "purpose": "production_composition_subtitle",
            "production_request_reference": context.request_reference,
            "timeline_reference": context.timeline_reference,
        },
    )
    subtitle_reference = _commit(repository, subtitle_candidate)
    if isinstance(subtitle_reference, ProductionMediaFailure):
        return subtitle_reference

    master_candidate = _candidate(
        "master_audio",
        artifact_identity,
        {
            "production_request_reference": context.request_reference,
            "timeline_reference": context.timeline_reference,
            "scene_audio_references": tuple(scene_audio_references),
            "duration_milliseconds": context.scenes[-1][2],
        },
        (context.request_reference, context.timeline_reference, *scene_audio_references),
        f"{composition_commit_id}:master_audio",
        {
            "purpose": "production_composition_master_audio",
            "production_request_reference": context.request_reference,
            "timeline_reference": context.timeline_reference,
            "scene_audio_references": tuple(scene_audio_references),
        },
    )
    master_audio_reference = _commit(repository, master_candidate)
    if isinstance(master_audio_reference, ProductionMediaFailure):
        return master_audio_reference

    try:
        composed = compose_method(task)
    except Exception:
        return _COMPOSITION_FAILED
    if isinstance(composed, ProductionMediaFailure):
        return _composer_failure(composed)
    try:
        composed = _composition_result_valid(composed, context)
    except _InvalidContext:
        return _COMPOSITION_FAILED

    video_candidate = _candidate(
        "video",
        artifact_identity,
        {
            "production_request_reference": context.request_reference,
            "timeline_reference": context.timeline_reference,
            "composition_id": task.composition_id,
            "scene_ids": tuple(scene_id for scene_id, _start, _end, _text in context.scenes),
            "scene_clip_references": tuple(scene_clip_references),
            "subtitle_reference": subtitle_reference,
            "master_audio_reference": master_audio_reference,
            "composer": composed.composer,
            "output_reference": _workspace_payload(composed.output_reference),
            "media_type": composed.media_type,
            "duration_milliseconds": composed.duration_milliseconds,
        },
        (
            context.request_reference,
            context.timeline_reference,
            *scene_clip_references,
            subtitle_reference,
            master_audio_reference,
        ),
        f"{composition_commit_id}:video",
        {
            "purpose": "production_composition_video",
            "production_request_reference": context.request_reference,
            "timeline_reference": context.timeline_reference,
            "composition_id": task.composition_id,
        },
    )
    video_reference = _commit(repository, video_candidate)
    if isinstance(video_reference, ProductionMediaFailure):
        return video_reference
    return ProductionCompositionResult(
        task.task_id,
        task.composition_id,
        context.request_reference,
        context.timeline_reference,
        tuple(scene_clip_references),
        tuple(scene_audio_references),
        subtitle_reference,
        master_audio_reference,
        video_reference,
        composed.output_reference,
        "SUCCESS",
    )


__all__ = ["compose_product_path"]
