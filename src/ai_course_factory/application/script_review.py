"""Application coordination for the mandatory Script Review gate.

This module composes the accepted Artifact, Script Decision and Workflow
boundaries.  It deliberately keeps Script payloads in the Artifact layer and
passes only exact References into the control runtime.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_course_factory.artifacts import (
    ArtifactCommitBoundary,
    ArtifactNotFoundError,
    ArtifactReference,
    ArtifactVersion,
    ScriptDecisionBoundary,
    ScriptDecisionFailure,
    ScriptDecisionRecord,
    ScriptGateAssessment,
)
from ai_course_factory.workflow import (
    ScriptReviewCommand,
    ScriptReviewWorkflow,
    WorkflowResult,
    WorkflowSnapshot,
)
from ai_course_factory.workflow.script_review import WorkflowNotFoundError


_APPLICATION_FAILURE_MESSAGE = "script review application could not be completed"
_LINEAGE_TYPES = ("knowledge", "content_plan", "content_plan")


@dataclass(frozen=True, slots=True)
class ScriptReviewApplicationResult:
    """Normalized result of one application-level Script Review operation."""

    status: str
    assessment: ScriptGateAssessment | None = None
    decision_record: ScriptDecisionRecord | None = None
    workflow_result: WorkflowResult | None = None
    error_code: str | None = None
    error_message: str | None = None

    @property
    def snapshot(self) -> WorkflowSnapshot | None:
        return self.workflow_result.snapshot if self.workflow_result else None

    @property
    def lifecycle_state(self) -> str | None:
        return self.workflow_result.lifecycle_state if self.workflow_result else None

    @property
    def pending_gate(self) -> str | None:
        return self.workflow_result.pending_gate if self.workflow_result else None


@dataclass(frozen=True, slots=True)
class _ResolvedScriptLineage:
    script_reference: ArtifactReference
    script_version: ArtifactVersion
    knowledge_reference: ArtifactReference
    knowledge_version: ArtifactVersion
    course_plan_reference: ArtifactReference
    course_plan_version: ArtifactVersion
    episode_plan_reference: ArtifactReference
    episode_plan_version: ArtifactVersion


class _ApplicationValidation(Exception):
    """Internal normalized validation failure."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ScriptReviewApplicationService:
    """Coordinate exact Script lineage, decisions and Workflow control.

    The service does not own Artifact persistence or Workflow state.  Artifact
    candidates are committed by their producing boundaries; this service only
    reads exact Versions, asks the decision boundary for an assessment/record,
    and resumes the existing control runtime after a successful decision.
    """

    def __init__(
        self,
        artifact_store: ArtifactCommitBoundary,
        decision_boundary: ScriptDecisionBoundary,
        workflow: ScriptReviewWorkflow,
    ) -> None:
        self._artifact_store = artifact_store
        self._decision_boundary = decision_boundary
        self._workflow = workflow

    def start(
        self,
        task_id: str,
        thread_id: str,
        script_reference: ArtifactReference,
    ) -> ScriptReviewApplicationResult:
        """Assess one exact Script lineage, then open its mandatory gate."""

        try:
            self._validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
            self._validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")
            lineage = self._resolve_lineage(script_reference)
        except _ApplicationValidation as exc:
            return self._failure(exc.code, exc.message)
        except Exception:
            return self._failure("APPLICATION_EXECUTION_FAILED")

        try:
            assessment = self._assess(lineage)
        except Exception:
            return self._failure("APPLICATION_EXECUTION_FAILED")
        if isinstance(assessment, ScriptDecisionFailure):
            return self._failure(
                assessment.code,
                assessment.message,
            )

        try:
            workflow_result = self._workflow.start(task_id, thread_id, script_reference)
            if not isinstance(workflow_result, WorkflowResult):
                return self._failure(
                    "APPLICATION_EXECUTION_FAILED",
                    assessment=assessment,
                )
        except Exception:
            return self._failure(
                "APPLICATION_EXECUTION_FAILED",
                assessment=assessment,
            )
        if workflow_result.status == "failure":
            return self._failure(
                workflow_result.error_code or "WORKFLOW_EXECUTION_FAILED",
                workflow_result.error_message,
                assessment=assessment,
                workflow_result=workflow_result,
            )
        return ScriptReviewApplicationResult(
            status=workflow_result.status,
            assessment=assessment,
            workflow_result=workflow_result,
        )

    def decide(
        self,
        task_id: str,
        thread_id: str,
        decision_id: str,
        creator_id: str,
        action: str,
        script_reference: ArtifactReference,
        decision_context: str = "",
    ) -> ScriptReviewApplicationResult:
        """Persist a Creator decision, then resume the pending Workflow.

        A pending checkpoint and exact selected Script are checked before any
        assessment or decision persistence.  An equivalent completed command
        is allowed through the same path for idempotent replay.
        """

        try:
            snapshot = self._workflow.snapshot(thread_id)
        except WorkflowNotFoundError:
            return self._failure("WORKFLOW_NOT_FOUND", "workflow checkpoint does not exist")
        except Exception:
            return self._failure("APPLICATION_EXECUTION_FAILED")

        try:
            self._validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
            self._validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")
            self._validate_identity(decision_id, "INVALID_DECISION_ID", "decision identity is required")
            self._validate_identity(creator_id, "INVALID_CREATOR_ID", "Creator identity is required")
            if snapshot.task_id != task_id:
                raise _ApplicationValidation("TASK_MISMATCH", "decision task does not match checkpoint")
            if not isinstance(script_reference, ArtifactReference) or snapshot.script_reference != script_reference:
                raise _ApplicationValidation(
                    "SCRIPT_REFERENCE_MISMATCH",
                    "decision must target the selected exact Script Version",
                )

            if snapshot.pending_gate == "script_review":
                pass
            elif snapshot.last_command_id == decision_id:
                existing = self._decision_boundary.get(decision_id)
                if not isinstance(existing, ScriptDecisionRecord) or not self._record_matches(
                    existing,
                    task_id=task_id,
                    thread_id=thread_id,
                    creator_id=creator_id,
                    action=action,
                    script_reference=script_reference,
                    decision_context=decision_context,
                ):
                    raise _ApplicationValidation(
                        "COMMAND_CONFLICT",
                        "decision identity was already used for another decision",
                    )
            else:
                raise _ApplicationValidation(
                    "GATE_NOT_PENDING",
                    "Script Review is not awaiting a decision",
                )
        except _ApplicationValidation as exc:
            return self._failure(exc.code, exc.message, workflow_result=self._snapshot_result(snapshot))

        try:
            lineage = self._resolve_lineage(script_reference)
        except _ApplicationValidation as exc:
            return self._failure(exc.code, exc.message, workflow_result=self._snapshot_result(snapshot))
        except Exception:
            return self._failure(
                "APPLICATION_EXECUTION_FAILED",
                workflow_result=self._snapshot_result(snapshot),
            )

        try:
            assessment = self._assess(lineage)
        except Exception:
            return self._failure(
                "APPLICATION_EXECUTION_FAILED",
                workflow_result=self._snapshot_result(snapshot),
            )
        if isinstance(assessment, ScriptDecisionFailure):
            return self._failure(
                assessment.code,
                assessment.message,
                workflow_result=self._snapshot_result(snapshot),
            )

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
                workflow_result=self._snapshot_result(snapshot),
            )
        if isinstance(decision, ScriptDecisionFailure):
            return self._failure(
                decision.code,
                decision.message,
                assessment=assessment,
                workflow_result=self._snapshot_result(snapshot),
            )

        command = ScriptReviewCommand(
            task_id=task_id,
            thread_id=thread_id,
            command_id=decision_id,
            action=action,
            script_reference=script_reference,
        )
        try:
            workflow_result = self._workflow.resume(command)
            if not isinstance(workflow_result, WorkflowResult):
                return self._failure(
                    "APPLICATION_EXECUTION_FAILED",
                    assessment=assessment,
                    decision_record=decision,
                    workflow_result=self._snapshot_result(snapshot),
                )
        except Exception:
            return self._failure(
                "APPLICATION_EXECUTION_FAILED",
                assessment=assessment,
                decision_record=decision,
                workflow_result=self._snapshot_result(snapshot),
            )
        if workflow_result.status == "failure":
            return self._failure(
                workflow_result.error_code or "WORKFLOW_EXECUTION_FAILED",
                workflow_result.error_message,
                assessment=assessment,
                decision_record=decision,
                workflow_result=workflow_result,
            )
        return ScriptReviewApplicationResult(
            status=workflow_result.status,
            assessment=assessment,
            decision_record=decision,
            workflow_result=workflow_result,
        )

    def _resolve_lineage(self, script_reference: ArtifactReference) -> _ResolvedScriptLineage:
        self._validate_reference(script_reference, "script")
        try:
            script_version = self._artifact_store.get(script_reference)
        except ArtifactNotFoundError as exc:
            raise _ApplicationValidation(
                "SCRIPT_NOT_FOUND",
                "the exact Script Artifact Reference does not exist",
            ) from exc

        dependencies = script_version.dependencies
        if not isinstance(dependencies, tuple) or len(dependencies) != 3:
            raise _ApplicationValidation(
                "SCRIPT_LINEAGE_INVALID",
                "Script dependencies must name exact Knowledge and Plan Versions",
            )
        for dependency, expected_type in zip(dependencies, _LINEAGE_TYPES, strict=True):
            self._validate_reference(dependency, expected_type)
        knowledge_reference, course_plan_reference, episode_plan_reference = dependencies

        try:
            knowledge_version = self._artifact_store.get(knowledge_reference)
            course_plan_version = self._artifact_store.get(course_plan_reference)
            episode_plan_version = self._artifact_store.get(episode_plan_reference)
        except ArtifactNotFoundError as exc:
            raise _ApplicationValidation(
                "ARTIFACT_LINEAGE_NOT_FOUND",
                "an exact Script dependency Reference does not exist",
            ) from exc
        return _ResolvedScriptLineage(
            script_reference=script_reference,
            script_version=script_version,
            knowledge_reference=knowledge_reference,
            knowledge_version=knowledge_version,
            course_plan_reference=course_plan_reference,
            course_plan_version=course_plan_version,
            episode_plan_reference=episode_plan_reference,
            episode_plan_version=episode_plan_version,
        )

    def _assess(self, lineage: _ResolvedScriptLineage) -> ScriptGateAssessment | ScriptDecisionFailure:
        return self._decision_boundary.assess(
            lineage.script_reference,
            lineage.script_version,
            lineage.knowledge_reference,
            lineage.knowledge_version,
            lineage.course_plan_reference,
            lineage.course_plan_version,
            lineage.episode_plan_reference,
            lineage.episode_plan_version,
        )

    @staticmethod
    def _validate_identity(value: object, code: str, message: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().casefold() == "latest"
            or any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
        ):
            raise _ApplicationValidation(code, message)

    @classmethod
    def _validate_reference(cls, reference: object, artifact_type: str) -> None:
        if not isinstance(reference, ArtifactReference):
            raise _ApplicationValidation(
                f"INVALID_{artifact_type.upper()}_REFERENCE",
                f"an exact {artifact_type} Reference is required",
            )
        cls._validate_identity(
            reference.identity,
            f"INVALID_{artifact_type.upper()}_REFERENCE",
            f"an exact {artifact_type} Reference is required",
        )
        if reference.artifact_type != artifact_type or not isinstance(reference.version, int) or isinstance(reference.version, bool) or reference.version <= 0:
            raise _ApplicationValidation(
                f"INVALID_{artifact_type.upper()}_REFERENCE",
                f"an exact {artifact_type} Reference is required",
            )

    @staticmethod
    def _record_matches(
        record: ScriptDecisionRecord,
        *,
        task_id: str,
        thread_id: str,
        creator_id: str,
        action: str,
        script_reference: ArtifactReference,
        decision_context: str,
    ) -> bool:
        return (
            record.task_id == task_id
            and record.thread_id == thread_id
            and record.creator_id == creator_id
            and record.action == action
            and record.script_reference == script_reference
            and record.decision_context == decision_context
        )

    @staticmethod
    def _snapshot_result(snapshot: WorkflowSnapshot) -> WorkflowResult:
        status = "pending" if snapshot.pending_gate else "success"
        return WorkflowResult(status=status, snapshot=snapshot)

    @staticmethod
    def _failure(
        code: str,
        message: str | None = None,
        *,
        assessment: ScriptGateAssessment | None = None,
        decision_record: ScriptDecisionRecord | None = None,
        workflow_result: WorkflowResult | None = None,
    ) -> ScriptReviewApplicationResult:
        return ScriptReviewApplicationResult(
            status="failure",
            assessment=assessment,
            decision_record=decision_record,
            workflow_result=workflow_result,
            error_code=code,
            error_message=message or _APPLICATION_FAILURE_MESSAGE,
        )


__all__ = ["ScriptReviewApplicationResult", "ScriptReviewApplicationService"]
