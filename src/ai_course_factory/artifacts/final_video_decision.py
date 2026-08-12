"""Mandatory Final Video Review assessment and Creator decision seam."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from .model import ArtifactReference, ArtifactVersion


_MAX_IDENTITY_LENGTH = 256
_MAX_COMPONENT_LENGTH = 128
_MAX_CONTEXT_LENGTH = 4096
_MAX_INT = 2**63 - 1
_MAX_FINDING_CODES = 9
_VIDEO_FIELDS = {
    "production_request_reference",
    "timeline_reference",
    "composition_id",
    "scene_ids",
    "scene_clip_references",
    "subtitle_reference",
    "master_audio_reference",
    "composer",
    "output_reference",
    "media_type",
    "duration_milliseconds",
}


@dataclass(frozen=True, slots=True)
class FinalVideoGateFinding:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class FinalVideoGateAssessment:
    video_reference: ArtifactReference
    disposition: str
    findings: tuple[FinalVideoGateFinding, ...]


@dataclass(frozen=True, slots=True)
class FinalVideoDecisionFailure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class FinalVideoDecisionRecord:
    decision_id: str
    task_id: str
    thread_id: str
    creator_id: str
    gate_kind: str
    video_reference: ArtifactReference
    assessment_disposition: str
    finding_codes: tuple[str, ...]
    action: str
    decision_context: str


@runtime_checkable
class FinalVideoDecisionRepository(Protocol):
    def save(
        self, record: FinalVideoDecisionRecord
    ) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure: ...

    def get(
        self, decision_id: str
    ) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure: ...


class _DecisionValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _failure(kind: str, code: str, message: str) -> FinalVideoDecisionFailure:
    return FinalVideoDecisionFailure(kind, code, message)


def _safe_text(value: object, *, limit: int, code: str, message: str) -> str:
    if (
        type(value) is not str
        or not value.strip()
        or len(value) > limit
        or value.strip().casefold() in {"latest", "current"}
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
    ):
        raise _DecisionValidation(code, message)
    return value


def _safe_reference(value: object, artifact_type: str) -> ArtifactReference:
    if type(value) is not ArtifactReference:
        raise _DecisionValidation(
            f"INVALID_{artifact_type.upper()}_REFERENCE",
            f"an exact {artifact_type} Reference is required",
        )
    if type(value.artifact_type) is not str or value.artifact_type != artifact_type:
        raise _DecisionValidation(
            f"INVALID_{artifact_type.upper()}_REFERENCE",
            f"an exact {artifact_type} Reference is required",
        )
    _safe_text(
        value.identity,
        limit=_MAX_IDENTITY_LENGTH,
        code=f"INVALID_{artifact_type.upper()}_REFERENCE",
        message=f"an exact {artifact_type} Reference is required",
    )
    if type(value.version) is not int or not 1 <= value.version <= _MAX_INT:
        raise _DecisionValidation(
            f"INVALID_{artifact_type.upper()}_REFERENCE",
            f"an exact {artifact_type} Reference is required",
        )
    return value


def _exact_value_shape(value: object, active: set[int] | None = None) -> bool:
    """Accept only detached immutable values used by committed Artifacts."""

    if value is None or type(value) in (str, bytes, int, bool):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is ArtifactReference:
        return (
            type(value.artifact_type) is str
            and type(value.identity) is str
            and bool(value.identity.strip())
            and value.identity.strip().casefold() not in {"latest", "current"}
            and len(value.identity) <= _MAX_IDENTITY_LENGTH
            and not any(ord(char) < 0x20 or ord(char) == 0x7F for char in value.identity)
            and type(value.version) is int
            and not isinstance(value.version, bool)
            and 1 <= value.version <= _MAX_INT
        )
    if type(value) is not MappingProxyType and type(value) is not tuple:
        return False
    active = set() if active is None else active
    marker = id(value)
    if marker in active:
        return False
    active.add(marker)
    try:
        if type(value) is MappingProxyType:
            return all(
                type(key) is str and _exact_value_shape(item, active)
                for key, item in value.items()
            )
        return all(_exact_value_shape(item, active) for item in value)
    except Exception:
        return False
    finally:
        active.remove(marker)


def _exact_version_shape(value: object) -> bool:
    if type(value) is not ArtifactVersion:
        return False
    if (
        type(value.reference) is not ArtifactReference
        or type(value.payload) is not MappingProxyType
        or type(value.provenance) is not tuple
        or type(value.dependencies) is not tuple
        or type(value.commit_id) is not str
        or (value.prior_reference is not None and type(value.prior_reference) is not ArtifactReference)
    ):
        return False
    try:
        _safe_text(value.commit_id, limit=_MAX_IDENTITY_LENGTH, code="INVALID_VIDEO_VERSION", message="a resolved Video Version is required")
    except _DecisionValidation:
        return False
    return all(
        _exact_value_shape(getattr(value, field))
        for field in ("reference", "payload", "provenance", "dependencies", "commit_id", "prior_reference")
    )


def _validate_record(record: object) -> FinalVideoDecisionFailure | None:
    try:
        if type(record) is not FinalVideoDecisionRecord:
            raise _DecisionValidation("INVALID_DECISION_RECORD", "decision record is invalid")
        for value, code, message in (
            (record.decision_id, "INVALID_DECISION_ID", "decision identity is required"),
            (record.task_id, "INVALID_TASK_ID", "task identity is required"),
            (record.thread_id, "INVALID_THREAD_ID", "thread identity is required"),
            (record.creator_id, "INVALID_CREATOR_ID", "Creator identity is required"),
        ):
            _safe_text(value, limit=_MAX_IDENTITY_LENGTH, code=code, message=message)
        if type(record.gate_kind) is not str or record.gate_kind != "final_video_review":
            raise _DecisionValidation("INVALID_DECISION_RECORD", "decision gate kind is invalid")
        _safe_reference(record.video_reference, "video")
        if type(record.assessment_disposition) is not str or record.assessment_disposition not in {"pass", "hard_block"}:
            raise _DecisionValidation("INVALID_DECISION_RECORD", "assessment disposition is invalid")
        if type(record.finding_codes) is not tuple or len(record.finding_codes) > _MAX_FINDING_CODES or any(
            type(code) is not str
            or not code.strip()
            or len(code) > _MAX_COMPONENT_LENGTH
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in code)
            for code in record.finding_codes
        ):
            raise _DecisionValidation("INVALID_DECISION_RECORD", "finding codes are invalid")
        if len(set(record.finding_codes)) != len(record.finding_codes):
            raise _DecisionValidation("INVALID_DECISION_RECORD", "finding codes are invalid")
        if record.assessment_disposition == "pass" and record.finding_codes:
            raise _DecisionValidation("INVALID_DECISION_RECORD", "Pass decision cannot contain findings")
        if record.assessment_disposition == "hard_block" and not record.finding_codes:
            raise _DecisionValidation("INVALID_DECISION_RECORD", "Hard Block decision requires findings")
        if type(record.action) is not str or record.action not in {"approve", "reject", "revise"}:
            raise _DecisionValidation("INVALID_DECISION_RECORD", "decision action is invalid")
        _validate_context(record.decision_context, record.action)
        if record.assessment_disposition == "hard_block" and record.action == "approve":
            raise _DecisionValidation(
                "HARD_BLOCK_APPROVAL_FORBIDDEN", "Hard Block Video cannot be approved"
            )
    except _DecisionValidation as exc:
        return _failure("validation", exc.code, exc.message)
    except Exception:
        return _failure("execution", "FINAL_VIDEO_DECISION_FAILED", "final video decision could not be recorded")
    return None


def _record_matches(actual: object, expected: FinalVideoDecisionRecord) -> bool:
    """Compare repository success without trusting an overridden dataclass equality."""

    if type(actual) is not FinalVideoDecisionRecord:
        return False
    return all(
        type(getattr(actual, field)) is type(getattr(expected, field))
        and getattr(actual, field) == getattr(expected, field)
        for field in (
            "decision_id",
            "task_id",
            "thread_id",
            "creator_id",
            "gate_kind",
            "video_reference",
            "assessment_disposition",
            "finding_codes",
            "action",
            "decision_context",
        )
    )


def _validate_context(value: object, action: str) -> None:
    if (
        type(value) is not str
        or len(value) > _MAX_CONTEXT_LENGTH
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        or action in {"reject", "revise"} and not value.strip()
    ):
        raise _DecisionValidation("INVALID_DECISION_CONTEXT", "decision context must be safe and bounded")


def _safe_workspace_component(value: object, *, task: bool) -> bool:
    if type(value) is not str or not value or len(value) > _MAX_COMPONENT_LENGTH:
        return False
    if value.casefold() in {"latest", "current"} or value[0] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
        return False
    allowed = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-"
    if task:
        allowed += ":"
    return all(char in allowed for char in value)


class _InMemoryFinalVideoDecisionRepository:
    def __init__(self) -> None:
        self._records: dict[str, FinalVideoDecisionRecord] = {}

    def save(self, record: FinalVideoDecisionRecord) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure:
        invalid = _validate_record(record)
        if invalid is not None:
            return invalid
        existing = self._records.get(record.decision_id)
        if existing is not None:
            if existing == record:
                return existing
            return _failure("validation", "DECISION_CONFLICT", "decision identity was already used with different input")
        self._records[record.decision_id] = record
        return record

    def get(self, decision_id: str) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure:
        try:
            _safe_text(decision_id, limit=_MAX_IDENTITY_LENGTH, code="INVALID_DECISION_ID", message="decision identity is required")
        except _DecisionValidation as exc:
            return _failure("validation", exc.code, exc.message)
        return self._records.get(decision_id) or _failure("validation", "DECISION_NOT_FOUND", "decision record does not exist")


class FinalVideoDecisionBoundary:
    """Assess one exact Video Version and persist its mandatory Creator action."""

    def __init__(self, repository: FinalVideoDecisionRepository | None = None) -> None:
        self._repository = repository if repository is not None else _InMemoryFinalVideoDecisionRepository()
        self._assessments: dict[int, tuple[FinalVideoGateAssessment, object]] = {}

    def assess(
        self, video_reference: ArtifactReference, resolved_video: ArtifactVersion
    ) -> FinalVideoGateAssessment | FinalVideoDecisionFailure:
        try:
            _safe_reference(video_reference, "video")
            if not _exact_version_shape(resolved_video):
                raise _DecisionValidation("INVALID_VIDEO_VERSION", "a resolved Video Version is required")
            if resolved_video.reference != video_reference:
                raise _DecisionValidation("VIDEO_REFERENCE_MISMATCH", "Video Reference does not match Version")
            findings = self._findings(video_reference, resolved_video)
            assessment = FinalVideoGateAssessment(
                video_reference,
                "hard_block" if findings else "pass",
                tuple(findings),
            )
            self._assessments[id(assessment)] = (
                assessment,
                (assessment.video_reference, assessment.disposition, tuple((item.code, item.message) for item in assessment.findings)),
            )
            return assessment
        except _DecisionValidation as exc:
            return _failure("validation", exc.code, exc.message)
        except Exception:
            return _failure("execution", "FINAL_VIDEO_DECISION_FAILED", "final video assessment failed")

    def decide(
        self,
        assessment: FinalVideoGateAssessment,
        *,
        decision_id: str,
        task_id: str,
        thread_id: str,
        creator_id: str,
        action: str,
        decision_context: str = "",
    ) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure:
        try:
            issued = self._assessments.get(id(assessment))
            snapshot = (assessment.video_reference, assessment.disposition, tuple((item.code, item.message) for item in assessment.findings)) if type(assessment) is FinalVideoGateAssessment else None
            if issued is None or issued[0] is not assessment or issued[1] != snapshot:
                raise _DecisionValidation("ASSESSMENT_NOT_ISSUED", "decision must use an assessment issued by this boundary")
            self._validate_assessment(assessment)
            for value, code, message in (
                (decision_id, "INVALID_DECISION_ID", "decision identity is required"),
                (task_id, "INVALID_TASK_ID", "task identity is required"),
                (thread_id, "INVALID_THREAD_ID", "thread identity is required"),
                (creator_id, "INVALID_CREATOR_ID", "Creator identity is required"),
            ):
                _safe_text(value, limit=_MAX_IDENTITY_LENGTH, code=code, message=message)
            if type(action) is not str or action not in {"approve", "reject", "revise"}:
                raise _DecisionValidation("INVALID_DECISION_ACTION", "decision action is invalid")
            _validate_context(decision_context, action)
            if assessment.disposition == "hard_block" and action == "approve":
                raise _DecisionValidation("HARD_BLOCK_APPROVAL_FORBIDDEN", "Hard Block Video cannot be approved")
            record = FinalVideoDecisionRecord(
                decision_id, task_id, thread_id, creator_id, "final_video_review",
                assessment.video_reference, assessment.disposition,
                tuple(finding.code for finding in assessment.findings), action, decision_context,
            )
            persisted = self._repository.save(record)
            if type(persisted) is FinalVideoDecisionFailure:
                return persisted
            if (
                type(persisted) is not FinalVideoDecisionRecord
                or _validate_record(persisted) is not None
                or not _record_matches(persisted, record)
            ):
                return _failure("execution", "FINAL_VIDEO_DECISION_FAILED", "final video decision could not be recorded")
            return persisted
        except _DecisionValidation as exc:
            return _failure("validation", exc.code, exc.message)
        except Exception:
            return _failure("execution", "FINAL_VIDEO_DECISION_FAILED", "final video decision could not be recorded")

    def get(self, decision_id: str) -> FinalVideoDecisionRecord | FinalVideoDecisionFailure:
        try:
            _safe_text(decision_id, limit=_MAX_IDENTITY_LENGTH, code="INVALID_DECISION_ID", message="decision identity is required")
            result = self._repository.get(decision_id)
            if type(result) is FinalVideoDecisionFailure:
                return result
            if type(result) is FinalVideoDecisionRecord and _validate_record(result) is None:
                return result
            return _failure("execution", "FINAL_VIDEO_DECISION_FAILED", "final video decision lookup failed")
        except _DecisionValidation as exc:
            return _failure("validation", exc.code, exc.message)
        except Exception:
            return _failure("execution", "FINAL_VIDEO_DECISION_FAILED", "final video decision lookup failed")

    @staticmethod
    def _validate_identity(value: object) -> None:
        _safe_text(
            value,
            limit=_MAX_IDENTITY_LENGTH,
            code="INVALID_DECISION_ID",
            message="decision identity is required",
        )

    @classmethod
    def _validate_assessment(cls, assessment: object) -> None:
        if type(assessment) is not FinalVideoGateAssessment:
            raise _DecisionValidation("INVALID_ASSESSMENT", "Final Video Gate assessment is required")
        _safe_reference(assessment.video_reference, "video")
        if type(assessment.disposition) is not str or assessment.disposition not in {"pass", "hard_block"} or type(assessment.findings) is not tuple:
            raise _DecisionValidation("INVALID_ASSESSMENT", "Final Video assessment is invalid")
        for finding in assessment.findings:
            if type(finding) is not FinalVideoGateFinding:
                raise _DecisionValidation("INVALID_ASSESSMENT", "Final Video findings are invalid")
            _safe_text(finding.code, limit=_MAX_COMPONENT_LENGTH, code="INVALID_ASSESSMENT", message="Final Video findings are invalid")
            _safe_text(finding.message, limit=_MAX_CONTEXT_LENGTH, code="INVALID_ASSESSMENT", message="Final Video findings are invalid")
        if len({finding.code for finding in assessment.findings}) != len(assessment.findings):
            raise _DecisionValidation("INVALID_ASSESSMENT", "Final Video findings are invalid")
        if assessment.disposition == "pass" and assessment.findings:
            raise _DecisionValidation("INVALID_ASSESSMENT", "Pass assessment cannot contain findings")
        if assessment.disposition == "hard_block" and not assessment.findings:
            raise _DecisionValidation("INVALID_ASSESSMENT", "Hard Block assessment requires findings")

    @classmethod
    def _findings(cls, reference: ArtifactReference, version: ArtifactVersion) -> list[FinalVideoGateFinding]:
        findings: list[FinalVideoGateFinding] = []

        def add(code: str, message: str) -> None:
            if not any(item.code == code for item in findings):
                findings.append(FinalVideoGateFinding(code, message))

        payload = version.payload
        if type(payload) is not MappingProxyType or set(payload) != _VIDEO_FIELDS:
            add("INVALID_VIDEO_PAYLOAD", "Video payload fields are invalid")
            return findings
        try:
            request = _safe_reference(payload["production_request_reference"], "production_request")
            timeline = _safe_reference(payload["timeline_reference"], "timeline")
            subtitle = _safe_reference(payload["subtitle_reference"], "subtitle")
            master = _safe_reference(payload["master_audio_reference"], "master_audio")
            scene_refs = payload["scene_clip_references"]
            scene_ids = payload["scene_ids"]
            if type(scene_ids) is not tuple or not scene_ids or any(
                not _safe_workspace_component(item, task=False) for item in scene_ids
            ) or len(set(scene_ids)) != len(scene_ids):
                add("INVALID_VIDEO_SCENES", "Video scene identities are invalid")
            if type(scene_refs) is not tuple or not scene_refs or len(scene_refs) != len(scene_ids):
                add("INVALID_VIDEO_SCENES", "Video Scene Clip References are invalid")
            else:
                seen: set[ArtifactReference] = set()
                for scene_id, item in zip(scene_ids, scene_refs):
                    try:
                        item = _safe_reference(item, "scene_clip")
                    except _DecisionValidation:
                        add("INVALID_VIDEO_SCENES", "Video Scene Clip References are invalid")
                        break
                    if item in seen:
                        add("INVALID_VIDEO_SCENES", "Video Scene Clip References must be unique")
                        break
                    if item.identity != f"{reference.identity}:{scene_id}":
                        add("VIDEO_LINEAGE_MISMATCH", "Video Scene Clip Reference is not bound to its Scene")
                    seen.add(item)
            if not _safe_workspace_component(payload["composition_id"], task=True):
                add("INVALID_VIDEO_COMPOSITION", "Video composition identity is invalid")
            if not _safe_workspace_component(payload["composer"], task=False):
                add("INVALID_VIDEO_COMPOSER", "Video composer identity is invalid")
            output = payload["output_reference"]
            if (
                type(output) is not MappingProxyType
                or set(output) != {"task_id", "area", "name"}
                or type(output["area"]) is not str
                or output["area"] != "media"
            ):
                add("INVALID_VIDEO_OUTPUT_REFERENCE", "Video output reference is invalid")
            else:
                if not _safe_workspace_component(output["task_id"], task=True) or not _safe_workspace_component(output["name"], task=False):
                    add("INVALID_VIDEO_OUTPUT_REFERENCE", "Video output reference is invalid")
            if payload["media_type"] != "video/mp4":
                add("INVALID_VIDEO_MEDIA_TYPE", "Video media type must be video/mp4")
            if subtitle.identity != reference.identity:
                add("VIDEO_LINEAGE_MISMATCH", "Video Subtitle Reference is not bound to the Video")
            if master.identity != reference.identity:
                add("VIDEO_LINEAGE_MISMATCH", "Video Master Audio Reference is not bound to the Video")
            duration = payload["duration_milliseconds"]
            if type(duration) is not int or isinstance(duration, bool) or not 0 < duration <= _MAX_INT:
                add("INVALID_VIDEO_DURATION", "Video duration must be a positive exact integer")
            expected_dependencies = (request, timeline, *scene_refs, subtitle, master) if type(scene_refs) is tuple else ()
            if version.dependencies != expected_dependencies:
                add("VIDEO_LINEAGE_MISMATCH", "Video dependencies do not match canonical lineage")
            if version.reference != reference:
                add("VIDEO_REFERENCE_MISMATCH", "Video Reference does not match payload")
        except _DecisionValidation:
            add("INVALID_VIDEO_PAYLOAD", "Video payload fields are invalid")
        except Exception:
            add("INVALID_VIDEO_PAYLOAD", "Video payload fields are invalid")
        return findings


__all__ = [
    "FinalVideoDecisionBoundary",
    "FinalVideoDecisionFailure",
    "FinalVideoDecisionRecord",
    "FinalVideoDecisionRepository",
    "FinalVideoGateAssessment",
    "FinalVideoGateFinding",
]
