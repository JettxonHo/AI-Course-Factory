"""Application coordination for the mandatory Final Video Review gate."""

from __future__ import annotations

from dataclasses import dataclass

from ai_course_factory.artifacts import (
    ArtifactNotFoundError,
    ArtifactReference,
    ArtifactVersion,
    FinalVideoDecisionBoundary,
    FinalVideoDecisionFailure,
    FinalVideoDecisionRecord,
    FinalVideoGateAssessment,
    FinalVideoGateFinding,
)
from ai_course_factory.workflow import (
    FinalVideoReviewCommand,
    FinalVideoReviewWorkflow,
    FinalVideoWorkflowResult,
    FinalVideoWorkflowSnapshot,
)
from ai_course_factory.workflow.final_video_review import FinalVideoWorkflowNotFoundError

_APPLICATION_FAILURE_MESSAGE = "final video review application could not be completed"
_MAX_IDENTITY_LENGTH = 256
_MAX_FINDING_CODE_LENGTH = 128
_MAX_FINDING_MESSAGE_LENGTH = 4096


def _same_reference(actual: object, expected: ArtifactReference) -> bool:
    return type(actual) is ArtifactReference and all(
        (type(value) is expected_type and value == expected_value)
        for value, expected_type, expected_value in zip(
            (actual.artifact_type, actual.identity, actual.version),
            (str, str, int),
            (expected.artifact_type, expected.identity, expected.version),
        )
    )


def _safe_finding(finding: FinalVideoGateFinding) -> bool:
    return (
        type(finding.code) is str
        and bool(finding.code.strip())
        and len(finding.code) <= _MAX_FINDING_CODE_LENGTH
        and type(finding.message) is str
        and bool(finding.message.strip())
        and len(finding.message) <= _MAX_FINDING_MESSAGE_LENGTH
        and not any(ord(char) < 0x20 or ord(char) == 0x7F for char in finding.code + finding.message)
    )


def _invalid_reference() -> None:
    raise _ApplicationValidation(
        "INVALID_VIDEO_REFERENCE", "an exact Video Artifact Reference is required"
    )


def _failed_assessment() -> FinalVideoDecisionFailure:
    return FinalVideoDecisionFailure("execution", "FINAL_VIDEO_DECISION_FAILED", _APPLICATION_FAILURE_MESSAGE)


@dataclass(frozen=True, slots=True)
class FinalVideoReviewApplicationResult:
    status: str
    assessment: FinalVideoGateAssessment | None = None
    decision_record: FinalVideoDecisionRecord | None = None
    workflow_result: FinalVideoWorkflowResult | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def snapshot(self) -> FinalVideoWorkflowSnapshot | None:
        return self.workflow_result.snapshot if self.workflow_result else None


class _ApplicationValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class FinalVideoReviewApplicationService:
    def __init__(
        self,
        artifact_repository,
        decision_boundary: FinalVideoDecisionBoundary,
        workflow: FinalVideoReviewWorkflow,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._decision_boundary = decision_boundary
        self._workflow = workflow

    def start(
        self,
        task_id: str,
        thread_id: str,
        video_reference: ArtifactReference,
    ) -> FinalVideoReviewApplicationResult:
        try:
            self._validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
            self._validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")
            assessment = self._assessment_for(video_reference)
        except _ApplicationValidation as exc:
            return self._failure(exc.code, exc.message)
        except Exception:
            return self._failure("APPLICATION_EXECUTION_FAILED")
        try:
            workflow_result = self._workflow.start(task_id, thread_id, video_reference)
        except Exception:
            return self._failure("APPLICATION_EXECUTION_FAILED", assessment=assessment)
        return self._workflow_outcome(workflow_result, assessment=assessment)
    def decide(
        self,
        task_id: str,
        thread_id: str,
        decision_id: str,
        creator_id: str,
        action: str,
        video_reference: ArtifactReference,
        decision_context: str = "",
    ) -> FinalVideoReviewApplicationResult:
        """Persist the exact decision first, then resume the workflow gate."""

        try:
            snapshot = self._workflow.snapshot(thread_id)
        except FinalVideoWorkflowNotFoundError:
            return self._failure("WORKFLOW_NOT_FOUND", "workflow checkpoint does not exist")
        except Exception:
            return self._failure("APPLICATION_EXECUTION_FAILED")
        pending = self._snapshot_result(snapshot)

        try:
            self._validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
            self._validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")
            self._validate_identity(decision_id, "INVALID_DECISION_ID", "decision identity is required")
            self._validate_identity(creator_id, "INVALID_CREATOR_ID", "Creator identity is required")
            self._validate_reference(video_reference)
            if snapshot.task_id != task_id:
                raise _ApplicationValidation("TASK_MISMATCH", "decision task does not match checkpoint")
            if not _same_reference(snapshot.video_reference, video_reference):
                raise _ApplicationValidation(
                    "VIDEO_REFERENCE_MISMATCH",
                    "decision must target the selected exact Video Version",
                )
            if snapshot.pending_gate == "final_video_review":
                pass
            elif snapshot.last_command_id == decision_id:
                existing = self._decision_boundary.get(decision_id)
                assessment = self._assessment_for(video_reference)
                if not self._record_matches(
                    existing,
                    decision_id=decision_id,
                    task_id=task_id,
                    thread_id=thread_id,
                    creator_id=creator_id,
                    action=action,
                    video_reference=video_reference,
                    decision_context=decision_context,
                    assessment=assessment,
                ):
                    raise _ApplicationValidation("COMMAND_CONFLICT", "decision identity was already used for another decision")
                return FinalVideoReviewApplicationResult(
                    status="success",
                    assessment=assessment,
                    decision_record=existing,
                    workflow_result=pending,
                )
            else:
                raise _ApplicationValidation(
                    "GATE_NOT_PENDING",
                    "Final Video Review is not awaiting a decision",
                )
        except _ApplicationValidation as exc:
            return self._failure(exc.code, exc.message, workflow_result=pending)
        except Exception:
            return self._failure(
                "APPLICATION_EXECUTION_FAILED",
                workflow_result=pending,
            )

        try:
            assessment = self._assessment_for(video_reference)
        except _ApplicationValidation as exc:
            return self._failure(exc.code, exc.message, workflow_result=pending)
        except Exception:
            return self._failure("APPLICATION_EXECUTION_FAILED", workflow_result=pending)

        try:
            decision = self._decision_boundary.decide(
                assessment,
                decision_id=decision_id,
                task_id=task_id,
                thread_id=thread_id,
                creator_id=creator_id,
                action=action,
                decision_context=decision_context,
            )
        except Exception:
            return self._failure(
                "APPLICATION_EXECUTION_FAILED",
                assessment=assessment,
                workflow_result=pending,
            )
        if type(decision) is FinalVideoDecisionFailure:
            return self._failure(
                decision.code,
                decision.message,
                assessment=assessment,
                workflow_result=pending,
            )
        if not self._record_matches(
            decision,
            decision_id=decision_id,
            task_id=task_id,
            thread_id=thread_id,
            creator_id=creator_id,
            action=action,
            video_reference=video_reference,
            decision_context=decision_context,
            assessment=assessment,
        ):
            return self._failure(
                "FINAL_VIDEO_DECISION_FAILED",
                assessment=assessment,
                workflow_result=pending,
            )

        command = FinalVideoReviewCommand(
            task_id=task_id,
            thread_id=thread_id,
            command_id=decision_id,
            action=action,
            video_reference=video_reference,
        )
        try:
            workflow_result = self._workflow.resume(command)
        except Exception:
            return self._failure(
                "APPLICATION_EXECUTION_FAILED",
                assessment=assessment,
                decision_record=decision,
                workflow_result=pending,
        )
        return self._workflow_outcome(
            workflow_result,
            assessment=assessment,
            decision_record=decision,
            fallback=pending,
        )
    def _resolve_video(self, reference: ArtifactReference) -> ArtifactVersion:
        self._validate_reference(reference)
        try:
            version = self._artifact_repository.get(reference)
        except ArtifactNotFoundError as exc:
            raise _ApplicationValidation("VIDEO_NOT_FOUND", "the exact Video Artifact Reference does not exist") from exc
        if type(version) is not ArtifactVersion or not _same_reference(version.reference, reference):
            raise _ApplicationValidation("INVALID_VIDEO_VERSION", "the exact Video Artifact Version is invalid")
        return version
    def _assess(
        self,
        reference: ArtifactReference,
        video: ArtifactVersion,
    ) -> FinalVideoGateAssessment | FinalVideoDecisionFailure:
        try:
            assessment = self._decision_boundary.assess(reference, video)
        except Exception:
            return _failed_assessment()
        if type(assessment) is FinalVideoDecisionFailure:
            return assessment
        return assessment if self._assessment_is_exact(assessment, reference) else _failed_assessment()

    def _assessment_for(self, reference: ArtifactReference) -> FinalVideoGateAssessment:
        assessment = self._assess(reference, self._resolve_video(reference))
        if type(assessment) is FinalVideoDecisionFailure: raise _ApplicationValidation(assessment.code, assessment.message)
        return assessment

    @classmethod
    def _workflow_outcome(
        cls,
        workflow_result: object,
        *,
        assessment: FinalVideoGateAssessment | None = None,
        decision_record: FinalVideoDecisionRecord | None = None,
        fallback: FinalVideoWorkflowResult | None = None,
    ) -> FinalVideoReviewApplicationResult:
        if type(workflow_result) is not FinalVideoWorkflowResult:
            return cls._failure(
                "APPLICATION_EXECUTION_FAILED",
                assessment=assessment,
                decision_record=decision_record,
                workflow_result=fallback,
            )
        if workflow_result.status == "failure":
            return cls._failure(
                workflow_result.error_code or "WORKFLOW_EXECUTION_FAILED",
                workflow_result.error_message,
                assessment=assessment,
                decision_record=decision_record,
                workflow_result=workflow_result,
            )
        return FinalVideoReviewApplicationResult(
            status=workflow_result.status,
            assessment=assessment,
            decision_record=decision_record,
            workflow_result=workflow_result,
        )

    @staticmethod
    def _validate_identity(value: object, code: str, message: str) -> str:
        if (
            type(value) is not str
            or not value.strip()
            or len(value) > _MAX_IDENTITY_LENGTH
            or value.strip().casefold() in {"latest", "current"}
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        ):
            raise _ApplicationValidation(code, message)
        return value

    @classmethod
    def _validate_reference(cls, reference: object) -> ArtifactReference:
        if type(reference) is not ArtifactReference or reference.artifact_type != "video":
            _invalid_reference()
        cls._validate_identity(reference.identity, "INVALID_VIDEO_REFERENCE", "an exact Video Artifact Reference is required")
        if type(reference.version) is not int or isinstance(reference.version, bool) or reference.version <= 0:
            _invalid_reference()
        return reference

    @staticmethod
    def _record_matches(
        record: object,
        *,
        decision_id: str,
        task_id: str,
        thread_id: str,
        creator_id: str,
        action: str,
        video_reference: ArtifactReference,
        decision_context: str,
        assessment: FinalVideoGateAssessment,
    ) -> bool:
        if type(record) is not FinalVideoDecisionRecord or not _same_reference(record.video_reference, video_reference):
            return False
        expected = (("decision_id", decision_id), ("task_id", task_id), ("thread_id", thread_id),
                    ("creator_id", creator_id), ("gate_kind", "final_video_review"),
                    ("assessment_disposition", assessment.disposition), ("action", action),
                    ("decision_context", decision_context))
        if any(type(getattr(record, field)) is not type(value) or getattr(record, field) != value
               for field, value in expected):
            return False
        expected_findings = tuple(finding.code for finding in assessment.findings)
        return type(record.finding_codes) is tuple and len(record.finding_codes) == len(expected_findings) and all(type(code) is str and code == expected for code, expected in zip(record.finding_codes, expected_findings))

    @staticmethod
    def _assessment_is_exact(
        assessment: object,
        video_reference: ArtifactReference,
    ) -> bool:
        if type(assessment) is not FinalVideoGateAssessment or not _same_reference(assessment.video_reference, video_reference):
            return False
        if type(assessment.disposition) is not str or assessment.disposition not in {"pass", "hard_block"}:
            return False
        if type(assessment.findings) is not tuple or not all(
            type(finding) is FinalVideoGateFinding and _safe_finding(finding) for finding in assessment.findings
        ):
            return False
        codes = tuple(finding.code for finding in assessment.findings)
        return len(set(codes)) == len(codes) and (assessment.disposition == "pass") == (not codes)

    @staticmethod
    def _snapshot_result(snapshot: FinalVideoWorkflowSnapshot) -> FinalVideoWorkflowResult:
        return FinalVideoWorkflowResult(status="pending" if snapshot.pending_gate else "success", snapshot=snapshot)

    @staticmethod
    def _failure(
        code: str,
        message: str | None = None,
        *,
        assessment: FinalVideoGateAssessment | None = None,
        decision_record: FinalVideoDecisionRecord | None = None,
        workflow_result: FinalVideoWorkflowResult | None = None,
    ) -> FinalVideoReviewApplicationResult:
        return FinalVideoReviewApplicationResult(
            status="failure",
            assessment=assessment,
            decision_record=decision_record,
            workflow_result=workflow_result,
            error_code=code,
            error_message=message or _APPLICATION_FAILURE_MESSAGE,
        )


__all__ = [
    "FinalVideoReviewApplicationResult",
    "FinalVideoReviewApplicationService",
]
