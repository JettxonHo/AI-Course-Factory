"""Task projection records and the application persistence seam."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, Protocol, runtime_checkable

from ai_course_factory.artifacts import (
    ArtifactNotFoundError,
    ArtifactReference,
    ArtifactRepository,
    ArtifactVersion,
)

_SLOTS = (
    "source", "knowledge", "course_plan", "episode_plan", "script",
    "character", "storyboard", "timeline", "production_request", "production_budget",
)
_TYPES = {
    "source": "source", "knowledge": "knowledge", "course_plan": "content_plan",
    "episode_plan": "content_plan", "script": "script", "character": "character",
    "storyboard": "storyboard", "timeline": "timeline",
    "production_request": "production_request", "production_budget": "production_budget",
}
_STATES = {
    "source": "source_ready", "knowledge": "knowledge_ready", "course_plan": "knowledge_ready",
    "episode_plan": "knowledge_ready", "script": "script_review_pending",
    "character": "production_planning", "storyboard": "production_planning",
    "timeline": "production_planning", "production_request": "production_planning",
    "production_budget": "budget_review_pending",
}
_VALID_STATES = {"created", *_STATES.values()}
_SAFE_FAILURE = "task projection operation failed"
_MAX_ID = 256


@dataclass(frozen=True, slots=True)
class TaskArtifactSelection:
    slot: str
    reference: ArtifactReference
    status: Literal["current", "stale"]


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    task_id: str
    revision: int
    lifecycle_state: str
    selections: tuple[TaskArtifactSelection, ...]
    last_command_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "selections", tuple(self.selections))


@dataclass(frozen=True, slots=True)
class TaskImpact:
    task_id: str
    slot: str
    previous_reference: ArtifactReference | None
    replacement_reference: ArtifactReference
    direct: tuple[TaskArtifactSelection, ...]
    transitive: tuple[TaskArtifactSelection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "direct", tuple(self.direct))
        object.__setattr__(self, "transitive", tuple(self.transitive))


@dataclass(frozen=True, slots=True)
class TaskOperationResult:
    status: Literal["success", "failure"]
    snapshot: TaskSnapshot | None = None
    impact: TaskImpact | None = None
    error_code: str | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class TaskRepositoryFailure:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class TaskProjectionChange:
    task_id: str
    command_id: str
    expected_revision: int | None
    snapshot: TaskSnapshot
    impact: TaskImpact | None = None


@runtime_checkable
class TaskRepository(Protocol):
    def save(self, change: TaskProjectionChange) -> TaskOperationResult: ...
    def get(self, task_id: str, revision: int | None = None) -> TaskSnapshot | TaskRepositoryFailure: ...


class InMemoryTaskRepository:
    def __init__(self) -> None:
        self._snapshots: dict[str, dict[int, TaskSnapshot]] = {}
        self._commands: dict[str, tuple[TaskProjectionChange, TaskOperationResult]] = {}

    def save(self, change: TaskProjectionChange) -> TaskOperationResult:
        invalid = _validate_change(change)
        if invalid is not None:
            return _failure(invalid)
        existing = self._commands.get(change.command_id)
        if existing is not None:
            return existing[1] if existing[0] == change else _failure(
                TaskRepositoryFailure("TASK_COMMAND_CONFLICT", "command identity was already used with different input")
            )
        history = self._snapshots.get(change.task_id)
        current = history[max(history)] if history else None
        if change.expected_revision is None:
            if current is not None:
                return _failure(TaskRepositoryFailure("TASK_ALREADY_EXISTS", "task identity already exists"))
            if change.snapshot.revision != 1 or change.snapshot.selections:
                return _failure(TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE))
        elif current is None:
            return _failure(TaskRepositoryFailure("TASK_NOT_FOUND", "task does not exist"))
        elif current.revision != change.expected_revision:
            return _failure(TaskRepositoryFailure("TASK_REVISION_CONFLICT", "task revision is no longer current"))
        elif change.snapshot.revision != current.revision + 1:
            return _failure(TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE))
        transition = _validate_transition(current, change)
        if transition is not None:
            return _failure(transition)
        self._snapshots.setdefault(change.task_id, {})[change.snapshot.revision] = change.snapshot
        result = TaskOperationResult("success", change.snapshot, change.impact)
        self._commands[change.command_id] = (change, result)
        return result

    def get(self, task_id: str, revision: int | None = None) -> TaskSnapshot | TaskRepositoryFailure:
        invalid = _validate_id(task_id, "INVALID_TASK_ID", "task identity is required")
        if invalid is not None:
            return invalid
        if revision is not None and not _positive_int(revision):
            return TaskRepositoryFailure("INVALID_EXPECTED_REVISION", "task revision must be a positive integer")
        history = self._snapshots.get(task_id)
        if history is None:
            return TaskRepositoryFailure("TASK_NOT_FOUND", "task does not exist")
        snapshot = history.get(max(history) if revision is None else revision)
        if snapshot is None:
            return TaskRepositoryFailure("TASK_NOT_FOUND", "task revision does not exist")
        command = self._commands.get(snapshot.last_command_id)
        if command is None or command[0].task_id != snapshot.task_id or command[0].snapshot != snapshot:
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
        invalid = _validate_change(command[0])
        return invalid or snapshot


class TaskProjectionService:
    def __init__(self, artifact_repository: ArtifactRepository, repository: TaskRepository | None = None) -> None:
        self._artifact_repository = artifact_repository
        self._repository = repository if repository is not None else InMemoryTaskRepository()

    def create(self, task_id: str, command_id: str) -> TaskOperationResult:
        for value, code, message in ((task_id, "INVALID_TASK_ID", "task identity is required"),
                                     (command_id, "INVALID_COMMAND_ID", "command identity is required")):
            invalid = _validate_id(value, code, message)
            if invalid is not None:
                return _failure(invalid)
        return self._save(TaskProjectionChange(
            task_id, command_id, None, TaskSnapshot(task_id, 1, "created", (), command_id)
        ))

    def inspect(self, task_id: str, revision: int | None = None) -> TaskOperationResult:
        result = self._repository.get(task_id, revision)
        if isinstance(result, TaskRepositoryFailure):
            return _failure(result)
        invalid = _validate_snapshot(result)
        return _failure(invalid) if invalid else TaskOperationResult("success", snapshot=result)

    def preview_selection(self, task_id: str, slot: str, reference: ArtifactReference) -> TaskOperationResult:
        result = self._repository.get(task_id)
        if isinstance(result, TaskRepositoryFailure):
            return _failure(result)
        invalid = _validate_snapshot(result)
        if invalid is not None:
            return _failure(invalid)
        try:
            impact, _ = self._prepare(result, slot, reference)
            return TaskOperationResult("success", snapshot=result, impact=impact)
        except _TaskValidation as exc:
            return _failure(TaskRepositoryFailure(exc.code, exc.message))
        except Exception:
            return _failure(TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE))

    def select(self, task_id: str, command_id: str, expected_revision: int, slot: str,
               reference: ArtifactReference) -> TaskOperationResult:
        for value, code, message in ((task_id, "INVALID_TASK_ID", "task identity is required"),
                                     (command_id, "INVALID_COMMAND_ID", "command identity is required")):
            invalid = _validate_id(value, code, message)
            if invalid is not None:
                return _failure(invalid)
        if not _positive_int(expected_revision):
            return _failure(TaskRepositoryFailure("INVALID_EXPECTED_REVISION", "task revision must be a positive integer"))
        current = self._repository.get(task_id)
        if isinstance(current, TaskRepositoryFailure):
            return _failure(current)
        invalid = _validate_snapshot(current)
        if invalid is not None:
            return _failure(invalid)
        base = current
        if current.revision != expected_revision:
            historical = self._repository.get(task_id, expected_revision)
            if isinstance(historical, TaskRepositoryFailure):
                return _failure(TaskRepositoryFailure("TASK_REVISION_CONFLICT", "task revision is no longer current"))
            invalid = _validate_snapshot(historical)
            if invalid is not None:
                return _failure(invalid)
            base = historical
        try:
            impact, snapshot = self._prepare(base, slot, reference, command_id)
        except _TaskValidation as exc:
            return _failure(TaskRepositoryFailure(exc.code, exc.message))
        except Exception:
            return _failure(TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE))
        return self._save(TaskProjectionChange(task_id, command_id, expected_revision, snapshot, impact))

    def _save(self, change: TaskProjectionChange) -> TaskOperationResult:
        try:
            invalid = _validate_change(change)
            if invalid is not None:
                return _failure(invalid)
            result = self._repository.save(change)
        except Exception:
            return _failure(TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE))
        if not isinstance(result, TaskOperationResult):
            return _failure(TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE))
        if result.status != "success":
            return result
        if (result.snapshot != change.snapshot or result.impact != change.impact
                or result.error_code is not None or result.error_message is not None
                or _validate_snapshot(result.snapshot) is not None):
            return _failure(TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE))
        return result

    def _prepare(self, snapshot: TaskSnapshot, slot: str, reference: ArtifactReference,
                 command_id: str = "preview") -> tuple[TaskImpact, TaskSnapshot]:
        _validate_slot(slot)
        _validate_reference(reference)
        selected = {item.slot: item for item in snapshot.selections}
        previous = selected.get(slot)
        version = self._resolve(reference)
        _validate_slot_version(slot, reference, version)
        if previous is not None:
            if previous.reference == reference:
                raise _TaskValidation("TASK_SELECTION_UNCHANGED", "selected Artifact Reference is unchanged")
            if (previous.reference.artifact_type, previous.reference.identity) != (reference.artifact_type, reference.identity):
                raise _TaskValidation("TASK_SELECTION_IDENTITY_MISMATCH", "replacement must keep the selected Artifact identity")
            if version.prior_reference != previous.reference:
                raise _TaskValidation("TASK_SELECTION_REVISION_MISMATCH", "replacement must name the selected Reference as predecessor")
        _validate_current_dependencies(version, selected, previous)
        impact = _impact_for(self._artifact_repository, snapshot, slot,
                             previous.reference if previous else None, reference)
        selected[slot] = TaskArtifactSelection(slot, reference, "current")
        for item in impact.direct + impact.transitive:
            selected[item.slot] = TaskArtifactSelection(item.slot, item.reference, "stale")
        if command_id != "preview":
            impact = TaskImpact(
                impact.task_id, impact.slot, impact.previous_reference, impact.replacement_reference,
                tuple(TaskArtifactSelection(item.slot, item.reference, "stale") for item in impact.direct),
                tuple(TaskArtifactSelection(item.slot, item.reference, "stale") for item in impact.transitive),
            )
        ordered = tuple(selected[name] for name in _SLOTS if name in selected)
        return impact, TaskSnapshot(snapshot.task_id, snapshot.revision + 1, _STATES[slot], ordered, command_id)

    def _resolve(self, reference: ArtifactReference) -> ArtifactVersion:
        try:
            version = self._artifact_repository.get(reference)
        except ArtifactNotFoundError:
            raise _TaskValidation("TASK_ARTIFACT_NOT_FOUND", "exact Artifact Reference does not exist") from None
        except Exception:
            raise _TaskValidation("TASK_REPOSITORY_FAILED", _SAFE_FAILURE) from None
        if not isinstance(version, ArtifactVersion) or version.reference != reference:
            raise _TaskValidation("TASK_ARTIFACT_NOT_FOUND", "exact Artifact Reference does not exist")
        return version


class _TaskValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code, self.message = code, message


def _failure(failure: TaskRepositoryFailure) -> TaskOperationResult:
    return TaskOperationResult("failure", error_code=failure.code, error_message=failure.message)


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _validate_id(value: Any, code: str, message: str) -> TaskRepositoryFailure | None:
    if (not isinstance(value, str) or not value or len(value) > _MAX_ID or value.lower() == "latest"
            or any(ord(char) < 32 or ord(char) == 127 for char in value)):
        return TaskRepositoryFailure(code, message)
    return None


def _validate_reference(reference: Any) -> None:
    if not isinstance(reference, ArtifactReference) or not _positive_int(reference.version):
        raise _TaskValidation("INVALID_TASK_REFERENCE", "exact Artifact Reference is required")
    for value in (reference.artifact_type, reference.identity):
        invalid = _validate_id(value, "INVALID_TASK_REFERENCE", "exact Artifact Reference is required")
        if invalid is not None:
            raise _TaskValidation(invalid.code, invalid.message)


def _validate_slot(slot: Any) -> None:
    if not isinstance(slot, str) or slot not in _SLOTS:
        raise _TaskValidation("INVALID_TASK_SLOT", "task slot is invalid")


def _validate_slot_version(slot: str, reference: ArtifactReference, version: ArtifactVersion) -> None:
    if reference.artifact_type != _TYPES[slot]:
        raise _TaskValidation("TASK_SLOT_TYPE_MISMATCH", "Artifact type does not match task slot")
    if slot in {"course_plan", "episode_plan"}:
        role = version.payload.get("role") if isinstance(version.payload, Mapping) else None
        if role != ("course" if slot == "course_plan" else "episode"):
            raise _TaskValidation("TASK_SLOT_TYPE_MISMATCH", "content plan role does not match task slot")


def _validate_current_dependencies(version: ArtifactVersion,
                                   selected: dict[str, TaskArtifactSelection],
                                   previous: TaskArtifactSelection | None) -> None:
    for dependency in version.dependencies:
        try:
            _validate_reference(dependency)
        except _TaskValidation:
            raise _TaskValidation("TASK_SELECTION_LINEAGE_MISMATCH", "Artifact dependency is invalid") from None
        if not any(item.reference == dependency and item.status == "current"
                   and (previous is None or item.slot != previous.slot) for item in selected.values()):
            raise _TaskValidation("TASK_SELECTION_LINEAGE_MISMATCH", "every direct dependency must be selected and current")


def _impact_for(store: ArtifactRepository, snapshot: TaskSnapshot, slot: str,
                previous: ArtifactReference | None, replacement: ArtifactReference) -> TaskImpact:
    if previous is None:
        return TaskImpact(snapshot.task_id, slot, None, replacement, (), ())
    selected = tuple(item for item in snapshot.selections if item.slot != slot)
    versions: dict[str, ArtifactVersion] = {}
    for item in selected:
        try:
            version = store.get(item.reference)
        except Exception:
            raise _TaskValidation("TASK_ARTIFACT_NOT_FOUND", "selected Artifact Reference does not exist") from None
        if not isinstance(version, ArtifactVersion) or version.reference != item.reference:
            raise _TaskValidation("TASK_ARTIFACT_NOT_FOUND", "selected Artifact Reference does not exist")
        versions[item.slot] = version
    direct: list[TaskArtifactSelection] = []
    transitive: list[TaskArtifactSelection] = []
    frontier: list[ArtifactReference] = []
    for item in selected:
        if item.status == "current" and previous in versions[item.slot].dependencies:
            direct.append(item)
            frontier.append(item.reference)
    seen = {item.slot for item in direct}
    while frontier:
        upstream = frontier.pop(0)
        for item in selected:
            if item.status == "current" and item.slot not in seen and upstream in versions[item.slot].dependencies:
                seen.add(item.slot)
                transitive.append(item)
                frontier.append(item.reference)
    key = _SLOTS.index
    direct.sort(key=lambda item: key(item.slot))
    transitive.sort(key=lambda item: key(item.slot))
    return TaskImpact(snapshot.task_id, slot, previous, replacement, tuple(direct), tuple(transitive))


def _validate_snapshot(snapshot: Any, task_id: str | None = None,
                       command_id: str | None = None,
                       expected_lifecycle: str | None = None) -> TaskRepositoryFailure | None:
    if not isinstance(snapshot, TaskSnapshot) or (task_id is not None and snapshot.task_id != task_id):
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    invalid = _validate_id(snapshot.task_id, "INVALID_TASK_ID", "task identity is required")
    if invalid is not None or not _positive_int(snapshot.revision):
        return invalid or TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    invalid = _validate_id(snapshot.last_command_id, "INVALID_COMMAND_ID", "command identity is required")
    if invalid is not None or (command_id is not None and snapshot.last_command_id != command_id):
        return invalid or TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    if snapshot.lifecycle_state not in _VALID_STATES:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    if expected_lifecycle is not None and snapshot.lifecycle_state != expected_lifecycle:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    for item in snapshot.selections:
        if (not isinstance(item, TaskArtifactSelection) or item.status not in {"current", "stale"}):
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
        try:
            _validate_slot(item.slot)
            _validate_reference(item.reference)
        except _TaskValidation:
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
        if item.reference.artifact_type != _TYPES[item.slot]:
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    slots = tuple(item.slot for item in snapshot.selections)
    if slots != tuple(name for name in _SLOTS if name in slots) or len(slots) != len(set(slots)):
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    return None


def _validate_change(change: Any) -> TaskRepositoryFailure | None:
    if not isinstance(change, TaskProjectionChange):
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    for value, code, message in ((change.task_id, "INVALID_TASK_ID", "task identity is required"),
                                 (change.command_id, "INVALID_COMMAND_ID", "command identity is required")):
        invalid = _validate_id(value, code, message)
        if invalid is not None:
            return invalid
    if change.expected_revision is not None and not _positive_int(change.expected_revision):
        return TaskRepositoryFailure("INVALID_EXPECTED_REVISION", "task revision must be a positive integer")
    invalid = _validate_snapshot(change.snapshot, change.task_id, change.command_id)
    if invalid is not None:
        return invalid
    if change.expected_revision is None:
        if (change.snapshot.revision != 1 or change.snapshot.selections or change.impact is not None
                or change.snapshot.lifecycle_state != "created"):
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    elif change.snapshot.revision != change.expected_revision + 1 or change.impact is None:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    if change.impact is None:
        return None
    invalid = _validate_impact(change.impact, change.snapshot)
    if invalid is not None:
        return invalid
    expected_lifecycle = _STATES[change.impact.slot]
    return _validate_snapshot(change.snapshot, expected_lifecycle=expected_lifecycle)


def _validate_impact(impact: Any, snapshot: TaskSnapshot) -> TaskRepositoryFailure | None:
    if not isinstance(impact, TaskImpact) or impact.task_id != snapshot.task_id or impact.slot not in _SLOTS:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    by_slot = {item.slot: item for item in snapshot.selections}
    replacement = by_slot.get(impact.slot)
    if replacement is None or replacement.status != "current" or replacement.reference != impact.replacement_reference:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    try:
        _validate_reference(impact.replacement_reference)
        if impact.previous_reference is not None:
            _validate_reference(impact.previous_reference)
            if (impact.previous_reference.artifact_type, impact.previous_reference.identity,
                    impact.previous_reference.version) == (impact.replacement_reference.artifact_type,
                                                            impact.replacement_reference.identity,
                                                            impact.replacement_reference.version):
                return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
            if impact.replacement_reference.version != impact.previous_reference.version + 1:
                return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
            if (impact.previous_reference.artifact_type, impact.previous_reference.identity) != \
                    (impact.replacement_reference.artifact_type, impact.replacement_reference.identity):
                return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    except _TaskValidation:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    seen: set[str] = set()
    for group in (impact.direct, impact.transitive):
        if any(not isinstance(item, TaskArtifactSelection) for item in group):
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
        slots = tuple(item.slot for item in group)
        if slots != tuple(name for name in _SLOTS if name in set(slots)):
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
        for item in group:
            if item.slot in seen or item.slot == impact.slot or by_slot.get(item.slot) != item or item.status != "stale":
                return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
            seen.add(item.slot)
    if impact.previous_reference is None and (impact.direct or impact.transitive):
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    return None


def _validate_transition(
    current: TaskSnapshot | None, change: TaskProjectionChange
) -> TaskRepositoryFailure | None:
    """Reject direct repository writes that do not represent one projection step."""

    if current is None:
        return None
    if change.expected_revision != current.revision or change.snapshot.revision != current.revision + 1:
        return TaskRepositoryFailure("TASK_REVISION_CONFLICT", "task revision is no longer current")
    old = {item.slot: item for item in current.selections}
    new = {item.slot: item for item in change.snapshot.selections}
    impact = change.impact
    if impact is None:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    selected = old.get(impact.slot)
    replacement = new.get(impact.slot)
    if replacement is None or replacement.status != "current" or replacement.reference != impact.replacement_reference:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    if impact.previous_reference is None:
        if selected is not None or impact.direct or impact.transitive:
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    elif selected is None or selected.status not in {"current", "stale"} or selected.reference != impact.previous_reference:
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    if set(new) != (set(old) if selected is not None else set(old) | {impact.slot}):
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    affected = {item.slot for item in impact.direct + impact.transitive}
    if impact.slot in affected or len(affected) != len(impact.direct) + len(impact.transitive):
        return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    for slot in set(old) | set(new):
        before, after = old.get(slot), new.get(slot)
        if slot == impact.slot:
            continue
        if slot in affected:
            if (before is None or before.status != "current"
                    or after != TaskArtifactSelection(slot, before.reference, "stale")):
                return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
        elif before != after:
            return TaskRepositoryFailure("TASK_REPOSITORY_FAILED", _SAFE_FAILURE)
    return None


__all__ = [
    "InMemoryTaskRepository", "TaskArtifactSelection", "TaskImpact", "TaskOperationResult",
    "TaskProjectionChange", "TaskProjectionService", "TaskRepository", "TaskRepositoryFailure",
    "TaskSnapshot",
]
