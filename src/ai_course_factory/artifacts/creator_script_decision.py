"""Creator-authored Script Package review decision boundary."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .model import ArtifactReference, ArtifactVersion


_MAX_IDENTITY_LENGTH = 256
_MAX_DECISION_CONTEXT_LENGTH = 4096


@dataclass(frozen=True, slots=True)
class CreatorScriptDecisionFailure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CreatorScriptDecisionRecord:
    """Immutable decision bound to one exact Creator Script Version."""

    decision_id: str
    task_id: str
    thread_id: str
    creator_id: str
    gate_kind: str
    source_reference: ArtifactReference
    script_reference: ArtifactReference
    script_package_id: str
    action: str
    decision_context: str

    @property
    def operator_id(self) -> str:
        """Compatibility-readable name for the human operator identity."""

        return self.creator_id


@runtime_checkable
class CreatorScriptDecisionRepository(Protocol):
    def save(self, record: CreatorScriptDecisionRecord) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        ...

    def get(self, decision_id: str) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        ...


class _DecisionValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _valid_identity(value: object) -> bool:
    return (
        isinstance(value, str)
        and 0 < len(value) <= _MAX_IDENTITY_LENGTH
        and bool(value.strip())
        and value.strip().casefold() not in {"latest", "current"}
        and not any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
    )


def _valid_reference(value: object, artifact_type: str) -> bool:
    return (
        isinstance(value, ArtifactReference)
        and value.artifact_type == artifact_type
        and _valid_identity(value.identity)
        and type(value.version) is int
        and value.version > 0
    )


def _validate_record(record: object) -> CreatorScriptDecisionFailure | None:
    try:
        if not isinstance(record, CreatorScriptDecisionRecord):
            raise _DecisionValidation("INVALID_DECISION_RECORD", "creator Script decision record is invalid")
        for value, code, message in (
            (record.decision_id, "INVALID_DECISION_ID", "decision identity is required"),
            (record.task_id, "INVALID_TASK_ID", "task identity is required"),
            (record.thread_id, "INVALID_THREAD_ID", "thread identity is required"),
            (record.creator_id, "INVALID_CREATOR_ID", "Creator identity is required"),
            (record.script_package_id, "INVALID_SCRIPT_PACKAGE_ID", "Script Package identity is required"),
        ):
            if not _valid_identity(value):
                raise _DecisionValidation(code, message)
        if record.gate_kind != "creator_script_package_review":
            raise _DecisionValidation("INVALID_DECISION_RECORD", "creator Script decision gate kind is invalid")
        if not _valid_reference(record.source_reference, "source_record"):
            raise _DecisionValidation("INVALID_SOURCE_REFERENCE", "an exact Source Record Reference is required")
        if not _valid_reference(record.script_reference, "script"):
            raise _DecisionValidation("INVALID_SCRIPT_REFERENCE", "an exact Script Reference is required")
        if record.action not in {"approve", "reject"}:
            raise _DecisionValidation("INVALID_DECISION_ACTION", "Creator Script actions are approve or reject")
        if (
            not isinstance(record.decision_context, str)
            or len(record.decision_context) > _MAX_DECISION_CONTEXT_LENGTH
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in record.decision_context)
            or record.action == "reject" and not record.decision_context.strip()
        ):
            raise _DecisionValidation("INVALID_DECISION_CONTEXT", "decision context must be safe and bounded")
    except _DecisionValidation as exc:
        return CreatorScriptDecisionFailure("validation", exc.code, exc.message)
    except Exception:
        return CreatorScriptDecisionFailure("execution", "CREATOR_SCRIPT_DECISION_FAILED", "creator Script decision could not be recorded")
    return None


class _InMemoryCreatorScriptDecisionRepository:
    def __init__(self) -> None:
        self._records: dict[str, CreatorScriptDecisionRecord] = {}

    def save(self, record: CreatorScriptDecisionRecord) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        invalid = _validate_record(record)
        if invalid:
            return invalid
        existing = self._records.get(record.decision_id)
        if existing is not None:
            if existing == record:
                return existing
            return CreatorScriptDecisionFailure("validation", "DECISION_CONFLICT", "decision identity was already used with different input")
        self._records[record.decision_id] = record
        return record

    def get(self, decision_id: str) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        if not _valid_identity(decision_id):
            return CreatorScriptDecisionFailure("validation", "INVALID_DECISION_ID", "decision identity is required")
        return self._records.get(decision_id) or CreatorScriptDecisionFailure("validation", "DECISION_NOT_FOUND", "decision record does not exist")


class CreatorScriptDecisionBoundary:
    """Validate package lineage, then persist one exact human action."""

    def __init__(self, repository: CreatorScriptDecisionRepository | None = None) -> None:
        self._repository = repository or _InMemoryCreatorScriptDecisionRepository()

    def decide(
        self,
        script_reference: ArtifactReference,
        resolved_script: ArtifactVersion,
        *,
        source_reference: ArtifactReference,
        decision_id: str,
        task_id: str,
        thread_id: str,
        creator_id: str,
        action: str,
        decision_context: str = "",
    ) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        try:
            self._validate_reference(script_reference, "script")
            self._validate_reference(source_reference, "source_record")
            if not isinstance(resolved_script, ArtifactVersion) or resolved_script.reference != script_reference:
                raise _DecisionValidation("SCRIPT_REFERENCE_MISMATCH", "Script Reference does not match Version")
            dependencies = resolved_script.dependencies
            if dependencies != (source_reference,):
                raise _DecisionValidation("SCRIPT_LINEAGE_MISMATCH", "Creator Script must depend on exactly the current Source Record")
            payload = resolved_script.payload
            if not isinstance(payload, Mapping) or set(payload) != {"script_package"}:
                raise _DecisionValidation("INVALID_SCRIPT_PAYLOAD", "Creator Script payload must contain complete script_package")
            package = payload.get("script_package")
            if not isinstance(package, Mapping):
                raise _DecisionValidation("INVALID_SCRIPT_PAYLOAD", "Creator Script package binding is invalid")
            package_id = package.get("script_package_id")
            if not _valid_identity(package_id):
                raise _DecisionValidation("INVALID_SCRIPT_PACKAGE_ID", "Creator Script Package identity is invalid")
            for value, code, message in (
                (decision_id, "INVALID_DECISION_ID", "decision identity is required"),
                (task_id, "INVALID_TASK_ID", "task identity is required"),
                (thread_id, "INVALID_THREAD_ID", "thread identity is required"),
                (creator_id, "INVALID_CREATOR_ID", "Creator identity is required"),
            ):
                if not _valid_identity(value):
                    raise _DecisionValidation(code, message)
            if action not in {"approve", "reject"}:
                raise _DecisionValidation("INVALID_DECISION_ACTION", "Creator Script actions are approve or reject")
            if (
                not isinstance(decision_context, str)
                or len(decision_context) > _MAX_DECISION_CONTEXT_LENGTH
                or any(ord(char) < 0x20 or ord(char) == 0x7F for char in decision_context)
                or action == "reject" and not decision_context.strip()
            ):
                raise _DecisionValidation("INVALID_DECISION_CONTEXT", "decision context must be safe and bounded")
            record = CreatorScriptDecisionRecord(
                decision_id, task_id, thread_id, creator_id,
                "creator_script_package_review", source_reference, script_reference,
                package_id, action, decision_context,
            )
            persisted = self._repository.save(record)
            if isinstance(persisted, CreatorScriptDecisionFailure):
                return persisted
            if persisted != record:
                return CreatorScriptDecisionFailure("execution", "CREATOR_SCRIPT_DECISION_FAILED", "creator Script decision could not be recorded")
            return persisted
        except _DecisionValidation as exc:
            return CreatorScriptDecisionFailure("validation", exc.code, exc.message)
        except Exception:
            return CreatorScriptDecisionFailure("execution", "CREATOR_SCRIPT_DECISION_FAILED", "creator Script decision could not be recorded")

    def get(self, decision_id: str) -> CreatorScriptDecisionRecord | CreatorScriptDecisionFailure:
        if not _valid_identity(decision_id):
            return CreatorScriptDecisionFailure("validation", "INVALID_DECISION_ID", "decision identity is required")
        try:
            result = self._repository.get(decision_id)
            return result if isinstance(result, (CreatorScriptDecisionRecord, CreatorScriptDecisionFailure)) else CreatorScriptDecisionFailure("execution", "CREATOR_SCRIPT_DECISION_FAILED", "creator Script decision lookup failed")
        except Exception:
            return CreatorScriptDecisionFailure("execution", "CREATOR_SCRIPT_DECISION_FAILED", "creator Script decision lookup failed")

    @staticmethod
    def _validate_reference(reference: object, artifact_type: str) -> None:
        if not _valid_reference(reference, artifact_type):
            raise _DecisionValidation(f"INVALID_{artifact_type.upper()}_REFERENCE", f"an exact {artifact_type} Reference is required")


def validate_creator_script_decision_record(record: object) -> CreatorScriptDecisionFailure | None:
    return _validate_record(record)


__all__ = [
    "CreatorScriptDecisionBoundary",
    "CreatorScriptDecisionFailure",
    "CreatorScriptDecisionRecord",
    "CreatorScriptDecisionRepository",
    "validate_creator_script_decision_record",
]
