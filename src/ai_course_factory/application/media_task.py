"""Durable, application-owned Task media projection.

This seam records selections of already committed media Artifacts.  It never
generates media, calls a Provider, or changes Artifact Versions.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Literal, Protocol, runtime_checkable

from ai_course_factory.artifacts import ArtifactNotFoundError, ArtifactReference, ArtifactRepository, ArtifactVersion

_SCENE_ROLES = ("scene_clip", "scene_audio")
_DELIVERY_ROLES = ("subtitle", "master_audio", "video", "artifact_manifest", "publish_package")
_LIFECYCLES = ("production_ready", "producing", "final_review_pending", "packaged")
_SAFE = "task media repository operation failed"
_MAX_ID = 256
_MAX_SCENE = 128
_MEDIA_DEPENDENCIES = {
    "scene_clip": (("video",), ("artifact_manifest", "publish_package")),
    "scene_audio": (("master_audio",), ("video", "artifact_manifest", "publish_package")),
    "subtitle": (("video", "artifact_manifest", "publish_package"), ()),
    "master_audio": (("video",), ("artifact_manifest", "publish_package")),
    "video": (("artifact_manifest", "publish_package"), ()),
    "artifact_manifest": (("publish_package",), ()),
    "publish_package": ((), ()),
}
@dataclass(frozen=True, slots=True)
class TaskSceneMediaSelection:
    scene_id: str
    role: Literal["scene_clip", "scene_audio"]
    reference: ArtifactReference
    status: Literal["current", "stale"]
@dataclass(frozen=True, slots=True)
class TaskDeliveryMediaSelection:
    role: Literal["subtitle", "master_audio", "video", "artifact_manifest", "publish_package"]
    reference: ArtifactReference
    status: Literal["current", "stale"]
@dataclass(frozen=True, slots=True)
class TaskMediaSnapshot:
    task_id: str
    revision: int
    lifecycle_state: Literal["production_ready", "producing", "final_review_pending", "packaged"]
    production_request_reference: ArtifactReference
    timeline_reference: ArtifactReference
    scene_ids: tuple[str, ...]
    scene_selections: tuple[TaskSceneMediaSelection, ...]
    delivery_selections: tuple[TaskDeliveryMediaSelection, ...]
    last_command_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "scene_ids", tuple(self.scene_ids))
        object.__setattr__(self, "scene_selections", tuple(self.scene_selections))
        object.__setattr__(self, "delivery_selections", tuple(self.delivery_selections))
_MediaSelection = TaskSceneMediaSelection | TaskDeliveryMediaSelection
@dataclass(frozen=True, slots=True)
class TaskMediaImpact:
    task_id: str
    role: str
    scene_id: str | None
    previous_reference: ArtifactReference | None
    replacement_reference: ArtifactReference
    direct: tuple[_MediaSelection, ...]
    transitive: tuple[_MediaSelection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "direct", tuple(self.direct))
        object.__setattr__(self, "transitive", tuple(self.transitive))


@dataclass(frozen=True, slots=True)
class TaskMediaBatchImpact:
    """One durable projection change containing several exact selections."""

    task_id: str
    operations: tuple[TaskMediaImpact, ...]
    discriminator: Literal["batch"] = "batch"

    def __post_init__(self) -> None:
        object.__setattr__(self, "operations", tuple(self.operations))
@dataclass(frozen=True, slots=True)
class TaskMediaOperationResult:
    status: Literal["success", "failure"]
    snapshot: TaskMediaSnapshot | None = None
    impact: TaskMediaImpact | None = None
    error_code: str | None = None
    error_message: str | None = None
@dataclass(frozen=True, slots=True)
class TaskMediaRepositoryFailure:
    code: str
    message: str
@dataclass(frozen=True, slots=True)
class TaskMediaProjectionChange:
    task_id: str
    command_id: str
    expected_revision: int | None
    snapshot: TaskMediaSnapshot
    impact: TaskMediaImpact | TaskMediaBatchImpact | None = None
@runtime_checkable
class TaskMediaRepository(Protocol):
    def save(self, change: TaskMediaProjectionChange) -> TaskMediaOperationResult: ...
    def get(self, task_id: str, revision: int | None = None) -> TaskMediaSnapshot | TaskMediaRepositoryFailure: ...
class _Invalid(Exception):
    def __init__(self, code: str, message: str = _SAFE) -> None:
        super().__init__(message)
        self.code, self.message = code, message
def _failure(code: str, message: str = _SAFE) -> TaskMediaOperationResult:
    return TaskMediaOperationResult("failure", error_code=code, error_message=message)
def _repo_failure(code: str, message: str = _SAFE) -> TaskMediaRepositoryFailure:
    return TaskMediaRepositoryFailure(code, message)
def _id(value: Any, code: str, *, scene: bool = False) -> None:
    if type(value) is not str or not value or len(value) > (_MAX_SCENE if scene else _MAX_ID):
        raise _Invalid(code, "identifier is invalid")
    if value.lower() in {"latest", "current"} or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise _Invalid(code, "identifier is invalid")
def _positive(value: Any) -> bool:
    return type(value) is int and value > 0 and value <= 2**63 - 1
def _ref(value: Any, code: str = "INVALID_MEDIA_REFERENCE", kind: str | None = None) -> ArtifactReference:
    if type(value) is not ArtifactReference or type(value.artifact_type) is not str or type(value.identity) is not str or not _positive(value.version):
        raise _Invalid(code, "exact Artifact Reference is required")
    try:
        _id(value.artifact_type, code)
        _id(value.identity, code)
    except _Invalid:
        raise
    if kind is not None and value.artifact_type != kind:
        raise _Invalid(code, "Artifact type is invalid")
    return value

def _same_ref(first: Any, second: Any) -> bool:
    return type(first) is ArtifactReference and type(second) is ArtifactReference and all(type(getattr(item, field)) is expected for item in (first, second) for field, expected in (("artifact_type", str), ("identity", str), ("version", int))) and (first.artifact_type, first.identity, first.version) == (second.artifact_type, second.identity, second.version)

def _same_refs(first: Any, second: Any) -> bool:
    return type(first) is tuple and type(second) is tuple and len(first) == len(second) and all(_same_ref(left, right) for left, right in zip(first, second))

def _same_selection(first: Any, second: Any) -> bool:
    if type(first) is TaskSceneMediaSelection and type(second) is TaskSceneMediaSelection:
        return (first.scene_id, first.role, first.status) == (second.scene_id, second.role, second.status) and _same_ref(first.reference, second.reference)
    if type(first) is TaskDeliveryMediaSelection and type(second) is TaskDeliveryMediaSelection:
        return (first.role, first.status) == (second.role, second.status) and _same_ref(first.reference, second.reference)
    return False

def _same_selections(first: Any, second: Any) -> bool:
    return type(first) is tuple and type(second) is tuple and len(first) == len(second) and all(_same_selection(left, right) for left, right in zip(first, second))

def _same_impact(first: Any, second: Any) -> bool:
    if type(first) is TaskMediaBatchImpact or type(second) is TaskMediaBatchImpact:
        return (
            type(first) is TaskMediaBatchImpact and type(second) is TaskMediaBatchImpact
            and first.task_id == second.task_id
            and first.discriminator == second.discriminator
            and type(first.operations) is tuple and type(second.operations) is tuple
            and len(first.operations) == len(second.operations)
            and all(_same_impact(left, right) for left, right in zip(first.operations, second.operations))
        )
    if type(first) is not TaskMediaImpact or type(second) is not TaskMediaImpact:
        return first is second
    previous = first.previous_reference is None and second.previous_reference is None or _same_ref(first.previous_reference, second.previous_reference)
    return (first.task_id, first.role, first.scene_id) == (second.task_id, second.role, second.scene_id) and previous and _same_ref(first.replacement_reference, second.replacement_reference) and _same_selections(first.direct, second.direct) and _same_selections(first.transitive, second.transitive)

def _same_snapshot(first: Any, second: Any) -> bool:
    return type(first) is TaskMediaSnapshot and type(second) is TaskMediaSnapshot and (first.task_id, first.revision, first.lifecycle_state, first.scene_ids, first.last_command_id) == (second.task_id, second.revision, second.lifecycle_state, second.scene_ids, second.last_command_id) and _same_ref(first.production_request_reference, second.production_request_reference) and _same_ref(first.timeline_reference, second.timeline_reference) and _same_selections(first.scene_selections, second.scene_selections) and _same_selections(first.delivery_selections, second.delivery_selections)

def _same_change(first: Any, second: Any) -> bool:
    return type(first) is TaskMediaProjectionChange and type(second) is TaskMediaProjectionChange and (first.task_id, first.command_id, first.expected_revision) == (second.task_id, second.command_id, second.expected_revision) and _same_snapshot(first.snapshot, second.snapshot) and _same_impact(first.impact, second.impact)

def _mapping(value: Any, keys: set[str], code: str) -> Mapping[str, Any]:
    if type(value) not in (dict, MappingProxyType) or set(value) != keys or any(type(key) is not str for key in value):
        raise _Invalid(code)
    return value
def _number(value: Any, code: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(value):
        raise _Invalid(code)
    return float(value)
def _version(repo: ArtifactRepository, reference: ArtifactReference, code: str = "TASK_MEDIA_ARTIFACT_NOT_FOUND") -> ArtifactVersion:
    try:
        result = repo.get(reference)
    except ArtifactNotFoundError:
        raise _Invalid(code, "exact Artifact Version does not exist") from None
    except Exception:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED") from None
    if type(result) is not ArtifactVersion or not _same_ref(result.reference, reference):
        raise _Invalid(code, "exact Artifact Version does not exist")
    return result
def _text(value: Any, code: str) -> None:
    if type(value) is not str or not value or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise _Invalid(code, "text is invalid")
def _request_context(repo: ArtifactRepository, request_ref: Any) -> tuple[ArtifactReference, ArtifactVersion, tuple[str, ...]]:
    request_ref = _ref(request_ref, "INVALID_PRODUCTION_REQUEST_REFERENCE", "production_request")
    request = _version(repo, request_ref)
    deps = request.dependencies
    if type(deps) is not tuple or len(deps) != 4 or any(type(item) is not ArtifactReference for item in deps):
        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    for item, kind in zip(deps, ("script", "character", "storyboard", "timeline")):
        _ref(item, "TASK_MEDIA_LINEAGE_MISMATCH", kind)
    payload = _mapping(request.payload, {"script_reference", "approval_decision_id", "character_reference", "storyboard_reference", "storyboard_decision_id", "timeline_reference", "production_request"}, "TASK_MEDIA_LINEAGE_MISMATCH")
    if not _same_refs(tuple(payload[k] for k in ("script_reference", "character_reference", "storyboard_reference", "timeline_reference")), deps):
        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    _id(payload["approval_decision_id"], "TASK_MEDIA_LINEAGE_MISMATCH")
    _id(payload["storyboard_decision_id"], "TASK_MEDIA_LINEAGE_MISMATCH")
    nested = _mapping(payload["production_request"], {"language", "aspect_ratio", "duration_seconds", "scenes"}, "TASK_MEDIA_LINEAGE_MISMATCH")
    _id(nested["language"], "TASK_MEDIA_LINEAGE_MISMATCH")
    _id(nested["aspect_ratio"], "TASK_MEDIA_LINEAGE_MISMATCH")
    duration = _number(nested["duration_seconds"], "TASK_MEDIA_LINEAGE_MISMATCH")
    scenes = nested["scenes"]
    if type(scenes) is not tuple or not scenes or duration <= 0:
        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    scene_ids: list[str] = []
    for scene in scenes:
        scene = _mapping(scene, {"scene_id", "start_seconds", "duration_seconds", "end_seconds", "narration", "visual_intent", "character_action", "continuity_notes"}, "TASK_MEDIA_LINEAGE_MISMATCH")
        _id(scene["scene_id"], "TASK_MEDIA_LINEAGE_MISMATCH", scene=True)
        if scene["scene_id"] in scene_ids:
            raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
        scene_ids.append(scene["scene_id"])
        start, length, end = (_number(scene[k], "TASK_MEDIA_LINEAGE_MISMATCH") for k in ("start_seconds", "duration_seconds", "end_seconds"))
        if start < 0 or length <= 0 or end <= start or not math.isclose(end, start + length, rel_tol=1e-9, abs_tol=1e-9):
            raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
        _text(scene["narration"], "TASK_MEDIA_LINEAGE_MISMATCH")
        _text(scene["visual_intent"], "TASK_MEDIA_LINEAGE_MISMATCH")
        _text(scene["character_action"], "TASK_MEDIA_LINEAGE_MISMATCH")
        notes = scene["continuity_notes"]
        if type(notes) is not tuple or not notes or any(type(note) is not str or not note for note in notes):
            raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    if not math.isclose(float(scenes[-1]["end_seconds"]), duration, rel_tol=1e-9, abs_tol=1e-9):
        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    timeline_ref = deps[3]
    timeline = _version(repo, timeline_ref)
    timeline_payload = _mapping(timeline.payload, {"script_reference", "approval_decision_id", "character_reference", "storyboard_reference", "storyboard_decision_id", "timeline"}, "TASK_MEDIA_LINEAGE_MISMATCH")
    _id(timeline_payload["approval_decision_id"], "TASK_MEDIA_LINEAGE_MISMATCH")
    _id(timeline_payload["storyboard_decision_id"], "TASK_MEDIA_LINEAGE_MISMATCH")
    if not _same_refs(timeline.dependencies, deps[:3]) or not _same_refs(tuple(timeline_payload[k] for k in ("script_reference", "character_reference", "storyboard_reference")), deps[:3]) or timeline_payload["approval_decision_id"] != payload["approval_decision_id"] or timeline_payload["storyboard_decision_id"] != payload["storyboard_decision_id"]:
        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    timeline_nested = _mapping(timeline_payload["timeline"], {"duration_seconds", "scenes"}, "TASK_MEDIA_LINEAGE_MISMATCH")
    if not math.isclose(_number(timeline_nested["duration_seconds"], "TASK_MEDIA_LINEAGE_MISMATCH"), duration, rel_tol=1e-9, abs_tol=1e-9) or type(timeline_nested["scenes"]) is not tuple or len(timeline_nested["scenes"]) != len(scenes):
        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    for left, right in zip(scenes, timeline_nested["scenes"]):
        right = _mapping(right, {"scene_id", "start_seconds", "duration_seconds", "end_seconds"}, "TASK_MEDIA_LINEAGE_MISMATCH")
        _id(right["scene_id"], "TASK_MEDIA_LINEAGE_MISMATCH", scene=True)
        right_start, right_duration, right_end = (_number(right[k], "TASK_MEDIA_LINEAGE_MISMATCH") for k in ("start_seconds", "duration_seconds", "end_seconds"))
        left_start, left_duration, left_end = (_number(left[k], "TASK_MEDIA_LINEAGE_MISMATCH") for k in ("start_seconds", "duration_seconds", "end_seconds"))
        if right["scene_id"] != left["scene_id"] or not math.isclose(right_start, left_start, rel_tol=1e-9, abs_tol=1e-9) or not math.isclose(right_duration, left_duration, rel_tol=1e-9, abs_tol=1e-9) or not math.isclose(right_end, left_end, rel_tol=1e-9, abs_tol=1e-9):
            raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    return request_ref, timeline, tuple(scene_ids)
def _selected_maps(snapshot: TaskMediaSnapshot) -> tuple[dict[tuple[str, str], TaskSceneMediaSelection], dict[str, TaskDeliveryMediaSelection]]:
    return ({(item.scene_id, item.role): item for item in snapshot.scene_selections}, {item.role: item for item in snapshot.delivery_selections})

def _validate_snapshot(value: Any) -> None:
    if type(value) is not TaskMediaSnapshot:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    _id(value.task_id, "TASK_MEDIA_REPOSITORY_FAILED")
    if not _positive(value.revision) or type(value.lifecycle_state) is not str or value.lifecycle_state not in _LIFECYCLES:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    _ref(value.production_request_reference, "TASK_MEDIA_REPOSITORY_FAILED", "production_request")
    _ref(value.timeline_reference, "TASK_MEDIA_REPOSITORY_FAILED", "timeline")
    _id(value.last_command_id, "TASK_MEDIA_REPOSITORY_FAILED")
    if type(value.scene_ids) is not tuple or not value.scene_ids or any(type(item) is not str for item in value.scene_ids) or len(set(value.scene_ids)) != len(value.scene_ids):
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    for item in value.scene_ids:
        _id(item, "TASK_MEDIA_REPOSITORY_FAILED", scene=True)
    if type(value.scene_selections) is not tuple or type(value.delivery_selections) is not tuple:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    seen_scene: set[tuple[str, str]] = set()
    order = {(scene, role): index for index, scene in enumerate(value.scene_ids) for role in _SCENE_ROLES}
    previous_order = -1
    for item in value.scene_selections:
        if type(item) is not TaskSceneMediaSelection or type(item.scene_id) is not str or type(item.role) is not str or type(item.status) is not str or item.role not in _SCENE_ROLES or item.status not in {"current", "stale"}:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        _id(item.scene_id, "TASK_MEDIA_REPOSITORY_FAILED", scene=True)
        _ref(item.reference, "TASK_MEDIA_REPOSITORY_FAILED", item.role)
        key = (item.scene_id, item.role)
        if key not in order or key in seen_scene or (order[key] * 2 + _SCENE_ROLES.index(item.role)) < previous_order:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        seen_scene.add(key); previous_order = order[key] * 2 + _SCENE_ROLES.index(item.role)
    seen_delivery: set[str] = set(); previous_order = -1
    for item in value.delivery_selections:
        if type(item) is not TaskDeliveryMediaSelection or type(item.role) is not str or type(item.status) is not str or item.role not in _DELIVERY_ROLES or item.status not in {"current", "stale"}:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        _ref(item.reference, "TASK_MEDIA_REPOSITORY_FAILED", item.role)
        position = _DELIVERY_ROLES.index(item.role)
        if item.role in seen_delivery or position < previous_order:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        seen_delivery.add(item.role); previous_order = position
    current = {item.role for item in value.delivery_selections if item.status == "current"}
    expected = "packaged" if "publish_package" in current else "final_review_pending" if "video" in current else "producing" if value.scene_selections or value.delivery_selections else "production_ready"
    if value.lifecycle_state != expected:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")

def _validate_impact(value: Any, snapshot: TaskMediaSnapshot) -> None:
    if type(value) is not TaskMediaImpact or type(value.task_id) is not str or value.task_id != snapshot.task_id or type(value.role) is not str or (value.scene_id is not None and type(value.scene_id) is not str) or type(value.replacement_reference) is not ArtifactReference or value.role not in (*_SCENE_ROLES, *_DELIVERY_ROLES):
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    if value.role in _SCENE_ROLES:
        _id(value.scene_id, "TASK_MEDIA_REPOSITORY_FAILED", scene=True)
    elif value.scene_id is not None:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    _ref(value.replacement_reference, "TASK_MEDIA_REPOSITORY_FAILED", value.role)
    if value.previous_reference is not None:
        _ref(value.previous_reference, "TASK_MEDIA_REPOSITORY_FAILED", value.role)
    all_items = (*value.direct, *value.transitive)
    if any(type(item) not in (TaskSceneMediaSelection, TaskDeliveryMediaSelection) for item in all_items):
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    seen: set[tuple[str, str] | str] = set()
    for item in all_items:
        if type(item.status) is not str or item.status != "stale" or type(item.role) is not str:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        if type(item) is TaskSceneMediaSelection:
            if type(item.scene_id) is not str:
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
            _id(item.scene_id, "TASK_MEDIA_REPOSITORY_FAILED", scene=True)
            if item.role not in _SCENE_ROLES:
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        elif item.role not in _DELIVERY_ROLES:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        _ref(item.reference, "TASK_MEDIA_REPOSITORY_FAILED", item.role)
        key: tuple[str, str] | str = (item.scene_id, item.role) if type(item) is TaskSceneMediaSelection else item.role
        if key in seen:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        seen.add(key)


def _validate_batch_impact(value: Any, snapshot: TaskMediaSnapshot) -> None:
    if (
        type(value) is not TaskMediaBatchImpact
        or value.task_id != snapshot.task_id
        or value.discriminator != "batch"
        or type(value.operations) is not tuple
        or not value.operations
    ):
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    seen: set[tuple[str, str] | str] = set()
    for operation in value.operations:
        _validate_impact(operation, snapshot)
        key: tuple[str, str] | str = (operation.scene_id, operation.role) if operation.role in _SCENE_ROLES else operation.role
        if key in seen:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        seen.add(key)

def _validate_change(change: Any) -> None:
    if type(change) is not TaskMediaProjectionChange:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    _id(change.task_id, "INVALID_TASK_ID"); _id(change.command_id, "INVALID_COMMAND_ID")
    if change.expected_revision is not None and not _positive(change.expected_revision):
        raise _Invalid("INVALID_EXPECTED_REVISION", "expected revision is invalid")
    _validate_snapshot(change.snapshot)
    if change.snapshot.task_id != change.task_id or change.snapshot.last_command_id != change.command_id:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    if change.expected_revision is None:
        if change.snapshot.revision != 1 or change.snapshot.scene_selections or change.snapshot.delivery_selections or change.impact is not None:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    else:
        if change.snapshot.revision != change.expected_revision + 1 or change.impact is None:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        if type(change.impact) is TaskMediaBatchImpact:
            _validate_batch_impact(change.impact, change.snapshot)
        else:
            _validate_impact(change.impact, change.snapshot)

def _validate_transition(current: TaskMediaSnapshot | None, change: TaskMediaProjectionChange) -> None:
    _validate_change(change)
    if current is None:
        return
    _validate_snapshot(current)
    if current.task_id != change.task_id or not _same_ref(current.production_request_reference, change.snapshot.production_request_reference) or not _same_ref(current.timeline_reference, change.snapshot.timeline_reference) or current.scene_ids != change.snapshot.scene_ids:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    impact = change.impact
    if impact is None or change.expected_revision != current.revision or change.snapshot.revision != current.revision + 1:
        raise _Invalid("TASK_MEDIA_REVISION_CONFLICT")
    if type(impact) is TaskMediaBatchImpact:
        _validate_batch_transition(current, change, impact)
        return
    old_scene, old_delivery = _selected_maps(current); new_scene, new_delivery = _selected_maps(change.snapshot)
    key: tuple[str, str] | str = (impact.scene_id, impact.role) if impact.role in _SCENE_ROLES else impact.role
    old = old_scene.get(key) if isinstance(key, tuple) else old_delivery.get(key)
    new = new_scene.get(key) if isinstance(key, tuple) else new_delivery.get(key)
    if new is None or new.status != "current" or not _same_ref(new.reference, impact.replacement_reference) or (old is None) != (impact.previous_reference is None):
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    if old is not None and (not _same_ref(old.reference, impact.previous_reference) or old.status not in {"current", "stale"}):
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    old_keys = set(old_scene) | set(old_delivery); new_keys = set(new_scene) | set(new_delivery)
    if old is None and new_keys != old_keys | {key} or old is not None and new_keys != old_keys:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    affected = {(item.scene_id, item.role) if type(item) is TaskSceneMediaSelection else item.role for item in (*impact.direct, *impact.transitive)}
    expected_direct, expected_transitive = _impact_keys(current, key)
    actual_direct = tuple((item.scene_id, item.role) if type(item) is TaskSceneMediaSelection else item.role for item in impact.direct)
    actual_transitive = tuple((item.scene_id, item.role) if type(item) is TaskSceneMediaSelection else item.role for item in impact.transitive)
    if actual_direct != expected_direct or actual_transitive != expected_transitive:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    if key in affected:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    for item_key in old_keys | new_keys:
        if item_key == key:
            continue
        before = old_scene.get(item_key) if isinstance(item_key, tuple) else old_delivery.get(item_key)
        after = new_scene.get(item_key) if isinstance(item_key, tuple) else new_delivery.get(item_key)
        if item_key in affected:
            if before is None or before.status != "current" or after is None or not _same_ref(after.reference, before.reference) or after.status != "stale":
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
            impacted = next(item for item in (*impact.direct, *impact.transitive) if ((item.scene_id, item.role) if type(item) is TaskSceneMediaSelection else item.role) == item_key)
            expected_stale = TaskSceneMediaSelection(before.scene_id, before.role, before.reference, "stale") if type(before) is TaskSceneMediaSelection else TaskDeliveryMediaSelection(before.role, before.reference, "stale")
            if not _same_selection(impacted, expected_stale):
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        elif not _same_selection(before, after):
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")


def _batch_selection_key(item: _MediaSelection) -> tuple[str, str] | str:
    return (item.scene_id, item.role) if type(item) is TaskSceneMediaSelection else item.role


def _validate_batch_transition(current: TaskMediaSnapshot, change: TaskMediaProjectionChange, impact: TaskMediaBatchImpact) -> None:
    if impact.task_id != current.task_id or not impact.operations:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    old_scene, old_delivery = _selected_maps(current)
    new_scene, new_delivery = _selected_maps(change.snapshot)
    old_keys = set(old_scene) | set(old_delivery)
    new_keys = set(new_scene) | set(new_delivery)
    operation_keys = {
        (operation.scene_id, operation.role) if operation.role in _SCENE_ROLES else operation.role
        for operation in impact.operations
    }
    if len(operation_keys) != len(impact.operations):
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    # Every operation must describe the exact current replacement in the
    # resulting snapshot; batch initialization has no predecessor and is
    # therefore validated by the artifact lineage checks in _prepare_batch.
    operation_keys_in_order = [
        (operation.scene_id, operation.role) if operation.role in _SCENE_ROLES else operation.role
        for operation in impact.operations
    ]
    for operation_index, operation in enumerate(impact.operations):
        key = (operation.scene_id, operation.role) if operation.role in _SCENE_ROLES else operation.role
        old = old_scene.get(key) if isinstance(key, tuple) else old_delivery.get(key)
        new = new_scene.get(key) if isinstance(key, tuple) else new_delivery.get(key)
        if new is None or new.status != "current" or not _same_ref(new.reference, operation.replacement_reference):
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        if old is None:
            if operation.previous_reference is not None:
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        elif operation.previous_reference != old.reference:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        later_operation_keys = set(operation_keys_in_order[operation_index + 1:])
        for item in (*operation.direct, *operation.transitive):
            stale_key = _batch_selection_key(item)
            before = old_scene.get(stale_key) if isinstance(stale_key, tuple) else old_delivery.get(stale_key)
            after = new_scene.get(stale_key) if isinstance(stale_key, tuple) else new_delivery.get(stale_key)
            superseded = stale_key in later_operation_keys
            if before is None or after is None or before.status != "current":
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
            if superseded:
                # A later operation in the same atomic batch may immediately
                # replace the stale downstream delivery (Scene-2 Clip + Video
                # replacement).  Its final status/reference is validated by
                # that later operation instead of requiring an intermediate
                # stale row to remain visible.
                later = next(
                    candidate
                    for candidate, candidate_key in zip(impact.operations[operation_index + 1:], operation_keys_in_order[operation_index + 1:])
                    if candidate_key == stale_key
                )
                if not _same_ref(after.reference, later.replacement_reference):
                    raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
                continue
            if not _same_ref(before.reference, after.reference):
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
            if after.status != "stale" or not _same_selection(item, after):
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    expected_keys = old_keys | operation_keys
    if new_keys != expected_keys:
        raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
    for key in old_keys | new_keys:
        if key in operation_keys:
            continue
        before = old_scene.get(key) if isinstance(key, tuple) else old_delivery.get(key)
        after = new_scene.get(key) if isinstance(key, tuple) else new_delivery.get(key)
        if not _same_selection(before, after):
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")

def _impact_keys(snapshot: TaskMediaSnapshot, key: tuple[str, str] | str) -> tuple[tuple[Any, ...], tuple[Any, ...]]:
    direct_roles, transitive_roles = _MEDIA_DEPENDENCIES[key[1] if isinstance(key, tuple) else key]
    delivery = {item.role: item for item in snapshot.delivery_selections if item.status == "current"}
    return tuple(role for role in direct_roles if role in delivery), tuple(role for role in transitive_roles if role in delivery)

class InMemoryTaskMediaRepository:
    def __init__(self) -> None:
        self._snapshots: dict[str, dict[int, TaskMediaSnapshot]] = {}
        self._commands: dict[str, tuple[TaskMediaProjectionChange, TaskMediaOperationResult]] = {}

    def save(self, change: TaskMediaProjectionChange) -> TaskMediaOperationResult:
        try:
            _validate_change(change)
            existing = self._commands.get(change.command_id)
            if existing is not None:
                if _same_change(existing[0], change):
                    return existing[1]
                return _failure("TASK_MEDIA_COMMAND_CONFLICT", "command identity was already used with different input")
            history = self._snapshots.get(change.task_id); current = history[max(history)] if history else None
            if change.expected_revision is None:
                if current is not None:
                    return _failure("TASK_MEDIA_ALREADY_EXISTS", "task media projection already exists")
            elif current is None:
                return _failure("TASK_MEDIA_NOT_FOUND", "task media projection does not exist")
            elif current.revision != change.expected_revision:
                return _failure("TASK_MEDIA_REVISION_CONFLICT", "task media revision is no longer current")
            _validate_transition(current, change)
            self._snapshots.setdefault(change.task_id, {})[change.snapshot.revision] = change.snapshot
            result = TaskMediaOperationResult("success", change.snapshot, change.impact)
            self._commands[change.command_id] = (change, result)
            return result
        except _Invalid as exc:
            return _failure(exc.code, exc.message)
        except Exception:
            return _failure("TASK_MEDIA_REPOSITORY_FAILED")

    def get(self, task_id: str, revision: int | None = None) -> TaskMediaSnapshot | TaskMediaRepositoryFailure:
        try:
            _id(task_id, "INVALID_TASK_ID")
            if revision is not None and not _positive(revision):
                return _repo_failure("INVALID_EXPECTED_REVISION", "revision is invalid")
            history = self._snapshots.get(task_id)
            if not history:
                return _repo_failure("TASK_MEDIA_NOT_FOUND", "task media projection does not exist")
            snapshot = history.get(max(history) if revision is None else revision)
            if snapshot is None:
                return _repo_failure("TASK_MEDIA_NOT_FOUND", "task media revision does not exist")
            _validate_snapshot(snapshot)
            command = self._commands.get(snapshot.last_command_id)
            if command is None or not _same_snapshot(command[0].snapshot, snapshot) or command[0].task_id != task_id:
                raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
            _validate_change(command[0])
            return snapshot
        except _Invalid as exc:
            return _repo_failure(exc.code, exc.message)
        except Exception:
            return _repo_failure("TASK_MEDIA_REPOSITORY_FAILED")

class TaskMediaProjectionService:
    def __init__(self, artifact_repository: ArtifactRepository, repository: TaskMediaRepository | None = None) -> None:
        self._artifacts = artifact_repository
        self._repository = repository if repository is not None else InMemoryTaskMediaRepository()

    def create(self, task_id: str, command_id: str, production_request_reference: ArtifactReference) -> TaskMediaOperationResult:
        try:
            _id(task_id, "INVALID_TASK_ID"); _id(command_id, "INVALID_COMMAND_ID")
            request_ref, timeline, scene_ids = _request_context(self._artifacts, production_request_reference)
            change = TaskMediaProjectionChange(task_id, command_id, None, TaskMediaSnapshot(task_id, 1, "production_ready", request_ref, timeline.reference, scene_ids, (), (), command_id))
            return self._save(change)
        except _Invalid as exc:
            return _failure(exc.code, exc.message)
        except Exception:
            return _failure("TASK_MEDIA_REPOSITORY_FAILED")

    def inspect(self, task_id: str, revision: int | None = None) -> TaskMediaOperationResult:
        try:
            result = self._repository.get(task_id, revision)
            if type(result) is TaskMediaRepositoryFailure:
                if not (type(result.code) is str and type(result.message) is str):
                    return _failure("TASK_MEDIA_REPOSITORY_FAILED")
                return _failure(result.code, result.message)
            if type(result) is not TaskMediaSnapshot:
                return _failure("TASK_MEDIA_REPOSITORY_FAILED")
            _validate_snapshot(result)
            return TaskMediaOperationResult("success", snapshot=result)
        except _Invalid as exc:
            return _failure(exc.code, exc.message)
        except Exception:
            return _failure("TASK_MEDIA_REPOSITORY_FAILED")

    def preview_scene_selection(self, task_id: str, scene_id: str, role: str, reference: ArtifactReference) -> TaskMediaOperationResult:
        return self._preview(task_id, scene_id, role, reference)

    def select_scene(self, task_id: str, command_id: str, expected_revision: int, scene_id: str, role: str, reference: ArtifactReference) -> TaskMediaOperationResult:
        return self._select(task_id, command_id, expected_revision, scene_id, role, reference)

    def preview_delivery_selection(self, task_id: str, role: str, reference: ArtifactReference) -> TaskMediaOperationResult:
        return self._preview(task_id, None, role, reference)

    def select_delivery(self, task_id: str, command_id: str, expected_revision: int, role: str, reference: ArtifactReference) -> TaskMediaOperationResult:
        return self._select(task_id, command_id, expected_revision, None, role, reference)

    def select_batch(
        self,
        task_id: str,
        command_id: str,
        expected_revision: int,
        selections: tuple[tuple[str, str, ArtifactReference], ...] = (),
        delivery_selections: tuple[tuple[str, ArtifactReference], ...] = (),
    ) -> TaskMediaOperationResult:
        """Publish a complete set of Scene/delivery selections in one save."""
        try:
            _id(task_id, "INVALID_TASK_ID"); _id(command_id, "INVALID_COMMAND_ID")
            if not _positive(expected_revision):
                raise _Invalid("INVALID_EXPECTED_REVISION", "expected revision is invalid")
            current = self._current(task_id)
            if current.revision != expected_revision:
                raise _Invalid("TASK_MEDIA_REVISION_CONFLICT", "task media revision is no longer current")
            if type(selections) is not tuple or type(delivery_selections) is not tuple:
                raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
            if not current.scene_selections and not current.delivery_selections:
                expected_scene_keys = {
                    (scene_id, role)
                    for scene_id in current.scene_ids
                    for role in _SCENE_ROLES
                }
                actual_scene_keys: list[tuple[str, str]] = []
                for item in selections:
                    if type(item) is not tuple or len(item) != 3:
                        raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
                    scene_id, role, _reference = item
                    if type(scene_id) is not str or type(role) is not str:
                        raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
                    actual_scene_keys.append((scene_id, role))
                actual_delivery_roles: list[str] = []
                for item in delivery_selections:
                    if type(item) is not tuple or len(item) != 2:
                        raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
                    role, _reference = item
                    if type(role) is not str:
                        raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
                    actual_delivery_roles.append(role)
                if (
                    len(actual_scene_keys) != len(expected_scene_keys)
                    or len(set(actual_scene_keys)) != len(actual_scene_keys)
                    or set(actual_scene_keys) != expected_scene_keys
                    or len(actual_delivery_roles) != 3
                    or len(set(actual_delivery_roles)) != len(actual_delivery_roles)
                    or set(actual_delivery_roles) != {"subtitle", "master_audio", "video"}
                ):
                    raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
            scene_map, delivery_map = _selected_maps(current)
            operations: list[TaskMediaImpact] = []
            for scene_id, role, reference in selections:
                if type(scene_id) is not str or type(role) is not str:
                    raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
                if role not in _SCENE_ROLES:
                    raise _Invalid("INVALID_MEDIA_ROLE", "media role is invalid")
                impact = self._prepare_batch_item(current, scene_map, delivery_map, scene_id, role, reference)
                operations.append(impact)
                scene_map[(scene_id, role)] = TaskSceneMediaSelection(scene_id, role, reference, "current")
                for stale in (*impact.direct, *impact.transitive):
                    key = _batch_selection_key(stale)
                    if isinstance(key, tuple):
                        scene_map[key] = TaskSceneMediaSelection(stale.scene_id, stale.role, stale.reference, "stale")
                    else:
                        delivery_map[key] = TaskDeliveryMediaSelection(stale.role, stale.reference, "stale")
            for role, reference in delivery_selections:
                if type(role) is not str or role not in _DELIVERY_ROLES:
                    raise _Invalid("INVALID_MEDIA_ROLE", "media role is invalid")
                impact = self._prepare_batch_item(current, scene_map, delivery_map, None, role, reference)
                operations.append(impact)
                delivery_map[role] = TaskDeliveryMediaSelection(role, reference, "current")
                for stale in (*impact.direct, *impact.transitive):
                    key = _batch_selection_key(stale)
                    if isinstance(key, tuple):
                        scene_map[key] = TaskSceneMediaSelection(stale.scene_id, stale.role, stale.reference, "stale")
                    else:
                        delivery_map[key] = TaskDeliveryMediaSelection(stale.role, stale.reference, "stale")
            if not operations:
                raise _Invalid("INVALID_MEDIA_BATCH", "complete media selections are required")
            # Initial import may include all downstream roles.  A replacement
            # carries only Scene 2 Clip + Video and stales exact dependencies.
            direct_map: dict[tuple[str, str] | str, tuple[_MediaSelection, ...]] = {}
            transitive_map: dict[tuple[str, str] | str, tuple[_MediaSelection, ...]] = {}
            for operation in operations:
                key = (operation.scene_id, operation.role) if operation.role in _SCENE_ROLES else operation.role
                direct_map[key] = operation.direct
                transitive_map[key] = operation.transitive
            ordered_scene = tuple(scene_map[(sid, role)] for sid in current.scene_ids for role in _SCENE_ROLES if (sid, role) in scene_map)
            ordered_delivery = tuple(delivery_map[role] for role in _DELIVERY_ROLES if role in delivery_map)
            current_delivery = {item.role for item in ordered_delivery if item.status == "current"}
            lifecycle = "packaged" if "publish_package" in current_delivery else "final_review_pending" if "video" in current_delivery else "producing"
            snapshot = TaskMediaSnapshot(task_id, current.revision + 1, lifecycle, current.production_request_reference, current.timeline_reference, current.scene_ids, ordered_scene, ordered_delivery, command_id)
            batch = TaskMediaBatchImpact(task_id, tuple(operations))
            return self._save(TaskMediaProjectionChange(task_id, command_id, expected_revision, snapshot, batch))
        except _Invalid as exc:
            return _failure(exc.code, exc.message)
        except Exception:
            return _failure("TASK_MEDIA_REPOSITORY_FAILED")

    def _current(self, task_id: str) -> TaskMediaSnapshot:
        result = self._repository.get(task_id)
        if type(result) is TaskMediaRepositoryFailure:
            raise _Invalid(result.code, result.message)
        if type(result) is not TaskMediaSnapshot:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        _validate_snapshot(result)
        return result

    def _preview(self, task_id: str, scene_id: str | None, role: str, reference: ArtifactReference) -> TaskMediaOperationResult:
        try:
            _id(task_id, "INVALID_TASK_ID"); snapshot = self._current(task_id)
            impact, _ = self._prepare(snapshot, scene_id, role, reference, None)
            return TaskMediaOperationResult("success", snapshot, impact)
        except _Invalid as exc:
            return _failure(exc.code, exc.message)
        except Exception:
            return _failure("TASK_MEDIA_REPOSITORY_FAILED")
    def _select(self, task_id: str, command_id: str, expected_revision: int, scene_id: str | None, role: str, reference: ArtifactReference) -> TaskMediaOperationResult:
        try:
            _id(task_id, "INVALID_TASK_ID"); _id(command_id, "INVALID_COMMAND_ID")
            if not _positive(expected_revision):
                raise _Invalid("INVALID_EXPECTED_REVISION", "expected revision is invalid")
            current = self._current(task_id)
            base = current if current.revision == expected_revision else self._history(task_id, expected_revision)
            impact, snapshot = self._prepare(base, scene_id, role, reference, command_id)
            if current.revision != expected_revision:
                raise _Invalid("TASK_MEDIA_REVISION_CONFLICT", "task media revision is no longer current")
            return self._save(TaskMediaProjectionChange(task_id, command_id, expected_revision, snapshot, impact))
        except _Invalid as exc:
            return _failure(exc.code, exc.message)
        except Exception as exc:
            return _failure("TASK_MEDIA_REPOSITORY_FAILED")
    def _history(self, task_id: str, revision: int) -> TaskMediaSnapshot:
        result = self._repository.get(task_id, revision)
        if type(result) is TaskMediaRepositoryFailure:
            raise _Invalid("TASK_MEDIA_REVISION_CONFLICT", "task media revision is no longer current")
        if type(result) is not TaskMediaSnapshot:
            raise _Invalid("TASK_MEDIA_REPOSITORY_FAILED")
        _validate_snapshot(result); return result
    def _prepare(self, base: TaskMediaSnapshot, scene_id: str | None, role: str, reference: ArtifactReference, command_id: str | None) -> tuple[TaskMediaImpact, TaskMediaSnapshot]:
        if type(role) is not str or role not in (*_SCENE_ROLES, *_DELIVERY_ROLES):
            raise _Invalid("INVALID_MEDIA_ROLE", "media role is invalid")
        if role in _SCENE_ROLES:
            if scene_id is None:
                raise _Invalid("INVALID_SCENE_ID", "scene identity is required")
            _id(scene_id, "INVALID_SCENE_ID", scene=True)
            if scene_id not in base.scene_ids:
                raise _Invalid("INVALID_SCENE_ID", "scene identity is not in the exact production order")
        elif scene_id is not None:
            raise _Invalid("INVALID_SCENE_ID", "delivery media has no scene identity")
        _ref(reference, "INVALID_MEDIA_REFERENCE", role)
        scene_map, delivery_map = _selected_maps(base)
        key: tuple[str, str] | str = (scene_id, role) if role in _SCENE_ROLES else role
        previous = scene_map.get(key) if isinstance(key, tuple) else delivery_map.get(key)
        if previous is not None and _same_ref(previous.reference, reference):
            raise _Invalid("TASK_MEDIA_SELECTION_UNCHANGED", "selected Artifact Reference is unchanged")
        version = _version(self._artifacts, reference)
        if previous is None:
            if version.prior_reference is not None:
                raise _Invalid("TASK_MEDIA_SELECTION_REVISION_MISMATCH", "initial selection must name no predecessor")
        else:
            if (previous.reference.artifact_type, previous.reference.identity) != (reference.artifact_type, reference.identity):
                raise _Invalid("TASK_MEDIA_SELECTION_IDENTITY_MISMATCH", "replacement must keep Artifact identity")
            if not _same_ref(version.prior_reference, previous.reference):
                raise _Invalid("TASK_MEDIA_SELECTION_REVISION_MISMATCH", "replacement must name the selected Reference as predecessor")
        self._validate_selection(base, scene_id, role, reference, version, scene_map, delivery_map)
        impact = self._impact(base, key, previous.reference if previous else None, reference, scene_map, delivery_map)
        if command_id is None:
            return impact, base
        if isinstance(key, tuple): scene_map[key] = TaskSceneMediaSelection(scene_id, role, reference, "current")
        else: delivery_map[key] = TaskDeliveryMediaSelection(role, reference, "current")
        for item in (*impact.direct, *impact.transitive):
            item_key = (item.scene_id, item.role) if type(item) is TaskSceneMediaSelection else item.role
            if isinstance(item_key, tuple): scene_map[item_key] = TaskSceneMediaSelection(item.scene_id, item.role, item.reference, "stale")
            else: delivery_map[item_key] = TaskDeliveryMediaSelection(item.role, item.reference, "stale")
        ordered_scene = tuple(scene_map[(sid, item_role)] for sid in base.scene_ids for item_role in _SCENE_ROLES if (sid, item_role) in scene_map)
        ordered_delivery = tuple(delivery_map[item_role] for item_role in _DELIVERY_ROLES if item_role in delivery_map)
        current_delivery = {item.role for item in ordered_delivery if item.status == "current"}
        lifecycle = "packaged" if "publish_package" in current_delivery else "final_review_pending" if "video" in current_delivery else "producing"
        snapshot = TaskMediaSnapshot(base.task_id, base.revision + 1, lifecycle, base.production_request_reference, base.timeline_reference, base.scene_ids, ordered_scene, ordered_delivery, command_id)
        return impact, snapshot

    def _prepare_batch_item(
        self,
        base: TaskMediaSnapshot,
        scenes: dict[tuple[str, str], TaskSceneMediaSelection],
        deliveries: dict[str, TaskDeliveryMediaSelection],
        scene_id: str | None,
        role: str,
        reference: ArtifactReference,
    ) -> TaskMediaImpact:
        if role in _SCENE_ROLES:
            if scene_id is None:
                raise _Invalid("INVALID_SCENE_ID", "scene identity is required")
            _id(scene_id, "INVALID_SCENE_ID", scene=True)
            if scene_id not in base.scene_ids:
                raise _Invalid("INVALID_SCENE_ID", "scene identity is not in the exact production order")
            key: tuple[str, str] | str = (scene_id, role)
        else:
            if scene_id is not None:
                raise _Invalid("INVALID_SCENE_ID", "delivery media has no scene identity")
            key = role
        _ref(reference, "INVALID_MEDIA_REFERENCE", role)
        previous = scenes.get(key) if isinstance(key, tuple) else deliveries.get(key)
        if previous is not None and _same_ref(previous.reference, reference):
            raise _Invalid("TASK_MEDIA_SELECTION_UNCHANGED", "selected Artifact Reference is unchanged")
        version = _version(self._artifacts, reference)
        if previous is None:
            if version.prior_reference is not None:
                raise _Invalid("TASK_MEDIA_SELECTION_REVISION_MISMATCH", "initial selection must name no predecessor")
        elif (previous.reference.artifact_type, previous.reference.identity) != (reference.artifact_type, reference.identity):
            raise _Invalid("TASK_MEDIA_SELECTION_IDENTITY_MISMATCH", "replacement must keep Artifact identity")
        elif not _same_ref(version.prior_reference, previous.reference):
            raise _Invalid("TASK_MEDIA_SELECTION_REVISION_MISMATCH", "replacement must name the selected Reference as predecessor")
        self._validate_selection(base, scene_id, role, reference, version, scenes, deliveries)
        return self._impact(base, key, previous.reference if previous else None, reference, scenes, deliveries)
    def _validate_selection(self, snapshot: TaskMediaSnapshot, scene_id: str | None, role: str, reference: ArtifactReference, version: ArtifactVersion, scenes: dict[tuple[str, str], TaskSceneMediaSelection], deliveries: dict[str, TaskDeliveryMediaSelection]) -> None:
        request, timeline, scene_ids = snapshot.production_request_reference, snapshot.timeline_reference, snapshot.scene_ids
        payload = version.payload
        if role in _SCENE_ROLES:
            if isinstance(payload, Mapping) and payload.get("source_kind") in {"creator_import", "local_narration"}:
                expected_kind = "creator_import" if role == "scene_clip" else "local_narration"
                expected_keys = (
                    {"source_kind", "production_request_reference", "scene_generation_contract_reference", "scene_id", "declared_filename", "creator_provenance", "output_reference", "media_type", "duration_milliseconds"}
                    if expected_kind == "creator_import" else
                    {"source_kind", "production_request_reference", "scene_generation_contract_reference", "creator_handoff_package_reference", "scene_id", "output_reference", "media_type", "duration_milliseconds"}
                )
                expected_dependencies = (request, payload.get("scene_generation_contract_reference")) if expected_kind == "creator_import" else (request, payload.get("scene_generation_contract_reference"), payload.get("creator_handoff_package_reference"))
                if set(payload) != expected_keys or payload.get("source_kind") != expected_kind or not _same_ref(payload.get("production_request_reference"), request) or payload.get("scene_id") != scene_id or not _same_refs(version.dependencies, expected_dependencies):
                    raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
                contract_reference = _ref(payload.get("scene_generation_contract_reference"), "TASK_MEDIA_LINEAGE_MISMATCH", "scene_generation_contract")
                contract = _version(self._artifacts, contract_reference, "TASK_MEDIA_LINEAGE_MISMATCH")
                contract_payload = contract.payload
                entries = contract_payload.get("scene_generation_contract", {}).get("scenes") if isinstance(contract_payload, Mapping) and isinstance(contract_payload.get("scene_generation_contract"), Mapping) else None
                entry = next((item for item in entries if isinstance(item, Mapping) and item.get("scene_id") == scene_id), None) if type(entries) is tuple else None
                if not isinstance(entry, Mapping) or type(entry.get("duration_milliseconds")) is not int or entry.get("duration_milliseconds") != payload.get("duration_milliseconds"):
                    raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
                output = _mapping(payload["output_reference"], {"task_id", "area", "name"}, "TASK_MEDIA_LINEAGE_MISMATCH")
                _text(output["task_id"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["area"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["name"], "TASK_MEDIA_LINEAGE_MISMATCH")
                if type(payload.get("duration_milliseconds")) is not int or payload["duration_milliseconds"] <= 0 or payload.get("media_type") != ("video/mp4" if expected_kind == "creator_import" else "audio/mp4"):
                    raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
                if expected_kind == "creator_import":
                    filename = payload.get("declared_filename")
                    if filename != entry.get("expected_filename") and not (scene_id == "scene-2" and filename == "scene-2-replacement.mp4"):
                        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
                    provenance = payload.get("creator_provenance")
                    if not isinstance(provenance, Mapping) or provenance.get("supplied_by") != "creator" or provenance.get("generated_outside_application") is not True or provenance.get("application_provider_attempt") is not False or provenance.get("application_charge_micros") != 0:
                        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
                else:
                    handoff_reference = _ref(payload.get("creator_handoff_package_reference"), "TASK_MEDIA_LINEAGE_MISMATCH", "creator_handoff_package")
                    handoff = _version(self._artifacts, handoff_reference, "TASK_MEDIA_LINEAGE_MISMATCH")
                    handoff_payload = handoff.payload
                    narration = handoff_payload.get("narration_references") if isinstance(handoff_payload, Mapping) else None
                    if type(narration) is not tuple or not any(isinstance(item, Mapping) and item.get("task_id") == output["task_id"] and item.get("name") == output["name"] for item in narration):
                        raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
                return
            p = _mapping(payload, {"production_request_reference", "scene_id", "attempt_id", "provider", "output_reference", "media_type", "duration_milliseconds"}, "TASK_MEDIA_LINEAGE_MISMATCH")
            if not _same_ref(p["production_request_reference"], request) or p["scene_id"] != scene_id or not _same_refs(version.dependencies, (request,)):
                raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
            _id(p["attempt_id"], "TASK_MEDIA_LINEAGE_MISMATCH"); _id(p["provider"], "TASK_MEDIA_LINEAGE_MISMATCH"); _id(p["media_type"], "TASK_MEDIA_LINEAGE_MISMATCH")
            output = _mapping(p["output_reference"], {"task_id", "area", "name"}, "TASK_MEDIA_LINEAGE_MISMATCH")
            _text(output["task_id"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["area"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["name"], "TASK_MEDIA_LINEAGE_MISMATCH")
            if type(p["duration_milliseconds"]) is not int or p["duration_milliseconds"] <= 0:
                raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
            return
        if role == "subtitle":
            p = _mapping(payload, {"production_request_reference", "timeline_reference", "cues"}, "TASK_MEDIA_LINEAGE_MISMATCH")
            if not _same_ref(p["production_request_reference"], request) or not _same_ref(p["timeline_reference"], timeline) or not _same_refs(version.dependencies, (request, timeline)) or type(p["cues"]) is not tuple or len(p["cues"]) != len(scene_ids):
                raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
            previous_end = 0
            for cue, sid in zip(p["cues"], scene_ids):
                cue = _mapping(cue, {"scene_id", "start_milliseconds", "end_milliseconds", "text"}, "TASK_MEDIA_LINEAGE_MISMATCH")
                if cue["scene_id"] != sid or type(cue["start_milliseconds"]) is not int or type(cue["end_milliseconds"]) is not int or cue["start_milliseconds"] != previous_end or cue["end_milliseconds"] <= cue["start_milliseconds"] or type(cue["text"]) is not str or not cue["text"]:
                    raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
                previous_end = cue["end_milliseconds"]
            return
        if role == "master_audio":
            p = _mapping(payload, {"production_request_reference", "timeline_reference", "scene_audio_references", "duration_milliseconds"}, "TASK_MEDIA_LINEAGE_MISMATCH")
            audio = tuple(scenes[(sid, "scene_audio")].reference for sid in scene_ids if (sid, "scene_audio") in scenes and scenes[(sid, "scene_audio")].status == "current")
            if len(audio) != len(scene_ids) or type(p["scene_audio_references"]) is not tuple or type(p["duration_milliseconds"]) is not int or p["duration_milliseconds"] <= 0 or not _same_ref(p["production_request_reference"], request) or not _same_ref(p["timeline_reference"], timeline) or not _same_refs(p["scene_audio_references"], audio) or not _same_refs(version.dependencies, (request, timeline, *audio)):
                raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
            return
        if role == "video":
            p = _mapping(payload, {"production_request_reference", "timeline_reference", "composition_id", "scene_ids", "scene_clip_references", "subtitle_reference", "master_audio_reference", "composer", "output_reference", "media_type", "duration_milliseconds"}, "TASK_MEDIA_LINEAGE_MISMATCH")
            clips = tuple(scenes[(sid, "scene_clip")].reference for sid in scene_ids if (sid, "scene_clip") in scenes and scenes[(sid, "scene_clip")].status == "current")
            subtitle = deliveries.get("subtitle"); master = deliveries.get("master_audio")
            output = _mapping(p["output_reference"], {"task_id", "area", "name"}, "TASK_MEDIA_LINEAGE_MISMATCH")
            _text(output["task_id"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["area"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["name"], "TASK_MEDIA_LINEAGE_MISMATCH")
            if len(clips) != len(scene_ids) or subtitle is None or subtitle.status != "current" or master is None or master.status != "current" or type(p["scene_ids"]) is not tuple or type(p["scene_clip_references"]) is not tuple or type(p["duration_milliseconds"]) is not int or p["duration_milliseconds"] <= 0 or not _same_ref(p["production_request_reference"], request) or not _same_ref(p["timeline_reference"], timeline) or p["scene_ids"] != scene_ids or not _same_refs(p["scene_clip_references"], clips) or not _same_ref(p["subtitle_reference"], subtitle.reference) or not _same_ref(p["master_audio_reference"], master.reference) or not _same_refs(version.dependencies, (request, timeline, *clips, subtitle.reference, master.reference)):
                raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
            return
        if role == "artifact_manifest":
            p = _mapping(payload, {"schema_version", "task_id", "source_record_reference", "subtitle_reference", "video_reference", "final_video_decision_id", "files"}, "TASK_MEDIA_LINEAGE_MISMATCH")
            subtitle = deliveries.get("subtitle"); video = deliveries.get("video")
            source = _ref(p["source_record_reference"], "TASK_MEDIA_LINEAGE_MISMATCH", "source_record")
            if p["schema_version"] != 1 or p["task_id"] != snapshot.task_id or subtitle is None or subtitle.status != "current" or video is None or video.status != "current" or not _same_ref(p["subtitle_reference"], subtitle.reference) or not _same_ref(p["video_reference"], video.reference) or not _same_refs(version.dependencies, (source, subtitle.reference, video.reference)):
                raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
            return
        p = _mapping(payload, {"manifest_reference", "source_record_reference", "subtitle_reference", "video_reference", "final_video_decision_id", "output_reference", "format"}, "TASK_MEDIA_LINEAGE_MISMATCH")
        manifest = deliveries.get("artifact_manifest"); subtitle = deliveries.get("subtitle"); video = deliveries.get("video")
        source = _ref(p["source_record_reference"], "TASK_MEDIA_LINEAGE_MISMATCH", "source_record")
        output = _mapping(p["output_reference"], {"task_id", "area", "name"}, "TASK_MEDIA_LINEAGE_MISMATCH")
        _text(output["task_id"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["area"], "TASK_MEDIA_LINEAGE_MISMATCH"); _text(output["name"], "TASK_MEDIA_LINEAGE_MISMATCH")
        if p["format"] != "zip" or manifest is None or manifest.status != "current" or subtitle is None or subtitle.status != "current" or video is None or video.status != "current" or not _same_ref(p["manifest_reference"], manifest.reference) or not _same_ref(p["subtitle_reference"], subtitle.reference) or not _same_ref(p["video_reference"], video.reference) or not _same_refs(version.dependencies, (manifest.reference, source, subtitle.reference, video.reference)):
            raise _Invalid("TASK_MEDIA_LINEAGE_MISMATCH")
    def _impact(self, snapshot: TaskMediaSnapshot, key: tuple[str, str] | str, previous: ArtifactReference | None, replacement: ArtifactReference, scenes: dict[tuple[str, str], TaskSceneMediaSelection], deliveries: dict[str, TaskDeliveryMediaSelection]) -> TaskMediaImpact:
        if previous is None:
            return TaskMediaImpact(snapshot.task_id, key[1], key[0], None, replacement, (), ()) if isinstance(key, tuple) else TaskMediaImpact(snapshot.task_id, key, None, None, replacement, (), ())
        direct_roles, transitive_roles = _MEDIA_DEPENDENCIES[key[1] if isinstance(key, tuple) else key]
        direct: list[_MediaSelection] = []; transitive: list[_MediaSelection] = []
        for role_name in direct_roles:
            item = deliveries.get(role_name)
            if item is not None and item.status == "current": direct.append(item)
        for role_name in transitive_roles:
            item = deliveries.get(role_name)
            if item is not None and item.status == "current": transitive.append(item)
        def stale(items: list[_MediaSelection]) -> tuple[_MediaSelection, ...]:
            return tuple(TaskSceneMediaSelection(i.scene_id, i.role, i.reference, "stale") if type(i) is TaskSceneMediaSelection else TaskDeliveryMediaSelection(i.role, i.reference, "stale") for i in items)
        return TaskMediaImpact(snapshot.task_id, key[1], key[0], previous, replacement, stale(direct), stale(transitive)) if isinstance(key, tuple) else TaskMediaImpact(snapshot.task_id, key, None, previous, replacement, stale(direct), stale(transitive))
    def _save(self, change: TaskMediaProjectionChange) -> TaskMediaOperationResult:
        try:
            result = self._repository.save(change)
            if type(result) is not TaskMediaOperationResult:
                return _failure("TASK_MEDIA_REPOSITORY_FAILED")
            if type(result.status) is not str or result.status not in {"success", "failure"}:
                return _failure("TASK_MEDIA_REPOSITORY_FAILED")
            if result.status == "failure":
                if result.snapshot is not None or result.impact is not None or type(result.error_code) is not str or type(result.error_message) is not str:
                    return _failure("TASK_MEDIA_REPOSITORY_FAILED")
                return _failure(result.error_code, result.error_message)
            if not _same_snapshot(result.snapshot, change.snapshot) or not _same_impact(result.impact, change.impact):
                return _failure("TASK_MEDIA_REPOSITORY_FAILED")
            return result
        except Exception:
            return _failure("TASK_MEDIA_REPOSITORY_FAILED")
__all__ = [
    "InMemoryTaskMediaRepository", "TaskDeliveryMediaSelection", "TaskMediaImpact", "TaskMediaBatchImpact", "TaskMediaOperationResult",
    "TaskMediaProjectionChange", "TaskMediaProjectionService", "TaskMediaRepository", "TaskMediaRepositoryFailure",
    "TaskMediaSnapshot", "TaskSceneMediaSelection",
]
