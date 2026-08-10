"""Control-only public value objects for the Script Review workflow."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_course_factory.artifacts.model import ArtifactReference


ALLOWED_SCRIPT_REVIEW_ACTIONS = ("approve", "reject", "revise")


@dataclass(frozen=True, slots=True)
class ScriptReviewCommand:
    """An exact-version Creator decision for one workflow thread."""

    task_id: str
    thread_id: str
    command_id: str
    action: str
    script_reference: ArtifactReference


@dataclass(frozen=True, slots=True)
class WorkflowSnapshot:
    """Normalized workflow projection; raw LangGraph state never escapes."""

    task_id: str
    thread_id: str
    lifecycle_state: str
    current_stage: str
    script_reference: ArtifactReference
    pending_gate: str | None
    allowed_actions: tuple[str, ...]
    resume_position: str
    last_command_id: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    """Success, Pending or Failure result at the public workflow boundary."""

    status: str
    snapshot: WorkflowSnapshot | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def lifecycle_state(self) -> str | None:
        return self.snapshot.lifecycle_state if self.snapshot else None

    @property
    def current_stage(self) -> str | None:
        return self.snapshot.current_stage if self.snapshot else None

    @property
    def script_reference(self) -> ArtifactReference | None:
        return self.snapshot.script_reference if self.snapshot else None

    @property
    def pending_gate(self) -> str | None:
        return self.snapshot.pending_gate if self.snapshot else None

    @property
    def allowed_actions(self) -> tuple[str, ...]:
        return self.snapshot.allowed_actions if self.snapshot else ()

    @property
    def resume_position(self) -> str | None:
        return self.snapshot.resume_position if self.snapshot else None


class WorkflowControlError(Exception):
    """Base error used internally to normalize fail-closed results."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def encode_reference(reference: ArtifactReference) -> dict[str, Any]:
    """Encode an exact reference into a serializer-friendly control value."""

    return {
        "artifact_type": reference.artifact_type,
        "identity": reference.identity,
        "version": reference.version,
    }


def decode_reference(value: Any) -> ArtifactReference:
    """Decode and validate an exact reference stored in graph control state."""

    if isinstance(value, ArtifactReference):
        reference = value
    elif isinstance(value, dict):
        try:
            reference = ArtifactReference(
                artifact_type=value["artifact_type"],
                identity=value["identity"],
                version=value["version"],
            )
        except (KeyError, TypeError) as exc:
            raise WorkflowControlError("INVALID_SCRIPT_REFERENCE", "invalid exact Artifact Reference") from exc
    else:
        raise WorkflowControlError("INVALID_SCRIPT_REFERENCE", "invalid exact Artifact Reference")

    if (
        not isinstance(reference.artifact_type, str)
        or not reference.artifact_type.strip()
        or not isinstance(reference.identity, str)
        or not reference.identity.strip()
        or not isinstance(reference.version, int)
        or isinstance(reference.version, bool)
        or reference.version <= 0
    ):
        raise WorkflowControlError("INVALID_SCRIPT_REFERENCE", "invalid exact Artifact Reference")
    return reference
