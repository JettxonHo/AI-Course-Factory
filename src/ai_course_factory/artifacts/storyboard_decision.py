"""In-memory Creator decision boundary for an exact Storyboard Version."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from .model import ArtifactReference, ArtifactVersion


_MAX_IDENTITY_LENGTH = 256
_MAX_DECISION_CONTEXT_LENGTH = 4096
_STORYBOARD_PAYLOAD_FIELDS = {
    "script_reference",
    "approval_decision_id",
    "character_reference",
    "storyboard_constraints",
    "storyboard",
}


@dataclass(frozen=True, slots=True)
class StoryboardDecisionFailure:
    """Safe validation or execution failure for the decision seam."""

    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class StoryboardDecisionRecord:
    """Immutable Creator decision bound to one exact Storyboard Version."""

    decision_id: str
    task_id: str
    thread_id: str
    creator_id: str
    gate_kind: str
    storyboard_reference: ArtifactReference
    script_reference: ArtifactReference
    character_reference: ArtifactReference
    script_approval_decision_id: str
    review_enabled: bool
    action: str
    decision_context: str


class _DecisionValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StoryboardDecisionBoundary:
    """Record Creator actions against exact committed Storyboard lineage."""

    def __init__(self) -> None:
        self._records: dict[str, StoryboardDecisionRecord] = {}

    def decide(
        self,
        storyboard_reference: ArtifactReference,
        resolved_storyboard: ArtifactVersion,
        *,
        review_enabled: bool,
        decision_id: str,
        task_id: str,
        thread_id: str,
        creator_id: str,
        action: str,
        decision_context: str = "",
    ) -> StoryboardDecisionRecord | StoryboardDecisionFailure:
        """Validate and record one enabled-review or explicit-skip decision."""

        try:
            self._validate_reference(storyboard_reference, "storyboard")
            self._validate_version(storyboard_reference, resolved_storyboard)
            script_reference, character_reference, approval_id = (
                self._validate_storyboard_lineage(resolved_storyboard)
            )
            self._validate_review_enabled(review_enabled)
            self._validate_action(action, review_enabled)
            self._validate_identity(
                decision_id,
                "INVALID_DECISION_ID",
                "decision identity is required",
            )
            self._validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
            self._validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")
            self._validate_identity(
                creator_id,
                "INVALID_CREATOR_ID",
                "Creator identity is required",
            )
            self._validate_decision_context(decision_context, action)

            record = StoryboardDecisionRecord(
                decision_id=decision_id,
                task_id=task_id,
                thread_id=thread_id,
                creator_id=creator_id,
                gate_kind="storyboard_review",
                storyboard_reference=storyboard_reference,
                script_reference=script_reference,
                character_reference=character_reference,
                script_approval_decision_id=approval_id,
                review_enabled=review_enabled,
                action=action,
                decision_context=decision_context,
            )
            existing = self._records.get(decision_id)
            if existing is not None:
                if existing == record:
                    return existing
                raise _DecisionValidation(
                    "DECISION_CONFLICT",
                    "decision identity was already used with different input",
                )
            self._records[decision_id] = record
            return record
        except _DecisionValidation as exc:
            return StoryboardDecisionFailure("validation", exc.code, exc.message)
        except Exception:
            return StoryboardDecisionFailure(
                "execution",
                "STORYBOARD_DECISION_FAILED",
                "storyboard decision could not be recorded",
            )

    def get(self, decision_id: str) -> StoryboardDecisionRecord | StoryboardDecisionFailure:
        """Retrieve one decision by its exact decision identity."""

        try:
            self._validate_identity(
                decision_id,
                "INVALID_DECISION_ID",
                "decision identity is required",
            )
            try:
                return self._records[decision_id]
            except KeyError:
                return StoryboardDecisionFailure(
                    "validation",
                    "DECISION_NOT_FOUND",
                    "decision record does not exist",
                )
        except _DecisionValidation as exc:
            return StoryboardDecisionFailure("validation", exc.code, exc.message)
        except Exception:
            return StoryboardDecisionFailure(
                "execution",
                "STORYBOARD_DECISION_FAILED",
                "storyboard decision lookup failed",
            )

    @classmethod
    def _validate_storyboard_lineage(
        cls, version: ArtifactVersion
    ) -> tuple[ArtifactReference, ArtifactReference, str]:
        dependencies = version.dependencies
        if not isinstance(dependencies, tuple) or len(dependencies) != 2:
            raise _DecisionValidation(
                "STORYBOARD_LINEAGE_MISMATCH",
                "Storyboard dependencies must be Script then Character",
            )
        script_reference, character_reference = dependencies
        if (
            not isinstance(script_reference, ArtifactReference)
            or script_reference.artifact_type != "script"
            or not isinstance(character_reference, ArtifactReference)
            or character_reference.artifact_type != "character"
        ):
            raise _DecisionValidation(
                "STORYBOARD_LINEAGE_MISMATCH",
                "Storyboard dependencies must be Script then Character",
            )
        cls._validate_reference(script_reference, "script")
        cls._validate_reference(character_reference, "character")

        payload = version.payload
        if not isinstance(payload, Mapping) or set(payload) != _STORYBOARD_PAYLOAD_FIELDS:
            raise _DecisionValidation(
                "INVALID_STORYBOARD_PAYLOAD",
                "Storyboard payload fields are invalid",
            )
        if payload.get("script_reference") != script_reference:
            raise _DecisionValidation(
                "STORYBOARD_LINEAGE_MISMATCH",
                "Storyboard Script Reference does not match dependencies",
            )
        if payload.get("character_reference") != character_reference:
            raise _DecisionValidation(
                "STORYBOARD_LINEAGE_MISMATCH",
                "Storyboard Character Reference does not match dependencies",
            )
        approval_id = payload.get("approval_decision_id")
        cls._validate_identity(
            approval_id,
            "INVALID_SCRIPT_APPROVAL_ID",
            "Storyboard Script approval identity is invalid",
        )
        return script_reference, character_reference, approval_id

    @classmethod
    def _validate_reference(cls, reference: object, artifact_type: str) -> None:
        if (
            not isinstance(reference, ArtifactReference)
            or reference.artifact_type != artifact_type
            or not cls._valid_identity(reference.identity)
            or not isinstance(reference.version, int)
            or isinstance(reference.version, bool)
            or reference.version <= 0
        ):
            raise _DecisionValidation(
                f"INVALID_{artifact_type.upper()}_REFERENCE",
                f"an exact {artifact_type} Reference is required",
            )

    @classmethod
    def _validate_version(
        cls, reference: ArtifactReference, version: object
    ) -> None:
        if not isinstance(version, ArtifactVersion):
            raise _DecisionValidation(
                "INVALID_STORYBOARD_VERSION",
                "a resolved Storyboard Version is required",
            )
        if version.reference != reference:
            raise _DecisionValidation(
                "STORYBOARD_REFERENCE_MISMATCH",
                "Storyboard Reference does not match Version",
            )

    @staticmethod
    def _validate_review_enabled(value: object) -> None:
        if type(value) is not bool:
            raise _DecisionValidation(
                "INVALID_REVIEW_ENABLED",
                "review_enabled must be an exact bool",
            )

    @staticmethod
    def _validate_action(action: object, review_enabled: bool) -> None:
        if not isinstance(action, str):
            raise _DecisionValidation(
                "INVALID_DECISION_ACTION",
                "decision action is invalid",
            )
        allowed = {"approve", "reject", "revise"} if review_enabled else {"skip"}
        if action not in allowed:
            raise _DecisionValidation(
                "INVALID_DECISION_ACTION",
                "decision action is invalid for Storyboard Review mode",
            )

    @classmethod
    def _validate_identity(cls, value: object, code: str, message: str) -> None:
        if not cls._valid_identity(value):
            raise _DecisionValidation(code, message)

    @classmethod
    def _valid_identity(cls, value: object) -> bool:
        return (
            isinstance(value, str)
            and bool(value.strip())
            and len(value) <= _MAX_IDENTITY_LENGTH
            and value.strip().casefold() not in {"latest", "current"}
            and not cls._has_control(value)
        )

    @classmethod
    def _validate_decision_context(cls, value: object, action: str) -> None:
        if (
            not isinstance(value, str)
            or len(value) > _MAX_DECISION_CONTEXT_LENGTH
            or cls._has_control(value)
            or action in {"reject", "revise"}
            and not value.strip()
        ):
            raise _DecisionValidation(
                "INVALID_DECISION_CONTEXT",
                "decision context must be safe and bounded",
            )

    @staticmethod
    def _has_control(value: str) -> bool:
        return any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)


__all__ = [
    "StoryboardDecisionBoundary",
    "StoryboardDecisionFailure",
    "StoryboardDecisionRecord",
]
