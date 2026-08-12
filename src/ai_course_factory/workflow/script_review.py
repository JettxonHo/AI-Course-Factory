"""Real LangGraph runtime for the mandatory Script Review gate."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from ai_course_factory.artifacts.commit import ArtifactCommitBoundary, ArtifactNotFoundError
from ai_course_factory.artifacts.model import ArtifactReference

from .checkpoint import (
    CheckpointAdapter,
    CheckpointNotFoundError,
    CheckpointStorageError,
    InMemoryCheckpointAdapter,
)
from .model import (
    ALLOWED_SCRIPT_REVIEW_ACTIONS,
    ScriptReviewCommand,
    WorkflowControlError,
    WorkflowResult,
    WorkflowSnapshot,
    decode_reference,
    encode_reference,
)


_MAX_ID_LENGTH = 256


class _ScriptReviewState(TypedDict, total=False):
    """LangGraph control state; no Artifact payload is allowed here."""

    task_id: str
    thread_id: str
    lifecycle_state: str
    current_stage: str
    selected_script_ref: dict[str, Any]
    pending_gate: str | None
    allowed_actions: list[str]
    resume_position: str
    decision: dict[str, Any]
    command_record: dict[str, Any]


class WorkflowNotFoundError(KeyError):
    """No workflow checkpoint exists for a requested thread."""


class ScriptReviewWorkflow:
    """Public control runtime for one exact Script Review lifecycle.

    The Artifact boundary is used only to validate that the supplied exact
    Script Reference exists.  Script content is never copied to graph state or
    returned by this class.
    """

    def __init__(
        self,
        artifact_store: ArtifactCommitBoundary,
        checkpoint_adapter: CheckpointAdapter | None = None,
    ) -> None:
        self._artifact_store = artifact_store
        self._checkpoint_adapter = checkpoint_adapter if checkpoint_adapter is not None else InMemoryCheckpointAdapter()
        self._graph = self._build_graph()

    @property
    def checkpoint_adapter(self) -> CheckpointAdapter:
        return self._checkpoint_adapter

    def start(
        self,
        task_id: str,
        thread_id: str,
        script_reference: ArtifactReference,
    ) -> WorkflowResult:
        """Start or inspect a Script Review workflow for an exact Script Ref."""

        try:
            self._validate_identity(task_id, thread_id)
            reference = self._validate_script_reference(script_reference)
            self._require_script(reference)
        except WorkflowControlError as exc:
            return WorkflowResult(status="failure", error_code=exc.code, error_message=str(exc))

        try:
            has_checkpoint = self._checkpoint_adapter.has_checkpoint(thread_id)
            if has_checkpoint:
                snapshot = self.snapshot(thread_id)
                if snapshot.task_id != task_id or snapshot.script_reference != reference:
                    return WorkflowResult(
                        status="failure",
                        snapshot=snapshot,
                        error_code="THREAD_BINDING_CONFLICT",
                        error_message="thread is already bound to another task or Script Version",
                    )
                return self._result_for_snapshot(snapshot)
        except WorkflowNotFoundError:
            return WorkflowResult(
                status="failure",
                error_code="CHECKPOINT_INVALID",
                error_message="workflow checkpoint is not readable",
            )
        except CheckpointStorageError:
            return self._execution_failure()

        initial_state: _ScriptReviewState = {
            "task_id": task_id,
            "thread_id": thread_id,
            "lifecycle_state": "task_initialized",
            "current_stage": "script_review",
            "selected_script_ref": encode_reference(reference),
            "pending_gate": None,
            "allowed_actions": [],
            "resume_position": "script_review_start",
        }
        try:
            config = self._checkpoint_adapter.config(thread_id)
            self._graph.invoke(initial_state, config)
            return self._result_for_snapshot(self.snapshot(thread_id))
        except Exception:
            return WorkflowResult(
                status="failure",
                error_code="WORKFLOW_EXECUTION_FAILED",
                error_message="workflow execution could not be completed",
            )

    def resume(self, command: ScriptReviewCommand) -> WorkflowResult:
        """Resume the pending interrupt with one exact-version decision."""

        try:
            self._validate_command(command)
            snapshot = self.snapshot(command.thread_id)
        except (WorkflowControlError, WorkflowNotFoundError) as exc:
            code = exc.code if isinstance(exc, WorkflowControlError) else "WORKFLOW_NOT_FOUND"
            return WorkflowResult(status="failure", error_code=code, error_message=str(exc))
        except CheckpointStorageError:
            return self._execution_failure(snapshot=None)

        try:
            state = self._checkpoint_adapter.inspect(command.thread_id)
            existing = state.get("command_record")
            if isinstance(existing, dict) and existing.get("command_id") == command.command_id:
                if self._record_matches(existing, command):
                    return self._result_for_snapshot(snapshot)
                return WorkflowResult(
                    status="failure",
                    snapshot=snapshot,
                    error_code="COMMAND_CONFLICT",
                    error_message="command identity was already used for another decision",
                )

            if snapshot.task_id != command.task_id:
                return self._failure(snapshot, "TASK_MISMATCH", "command task does not match checkpoint")
            if snapshot.thread_id != command.thread_id:
                return self._failure(snapshot, "THREAD_MISMATCH", "command thread does not match checkpoint")
            if snapshot.pending_gate != "script_review":
                return self._failure(snapshot, "GATE_NOT_PENDING", "Script Review is not awaiting a decision")
            if snapshot.script_reference != command.script_reference:
                return self._failure(snapshot, "SCRIPT_REFERENCE_MISMATCH", "command must target the selected exact Script Version")
            self._require_script(command.script_reference)
        except WorkflowControlError as exc:
            return self._failure(snapshot, exc.code, str(exc))
        except CheckpointNotFoundError:
            return self._failure(
                snapshot,
                "WORKFLOW_EXECUTION_FAILED",
                "workflow execution could not be completed",
            )
        except CheckpointStorageError:
            return self._failure(
                snapshot,
                "WORKFLOW_EXECUTION_FAILED",
                "workflow execution could not be completed",
            )

        decision = {
            "task_id": command.task_id,
            "thread_id": command.thread_id,
            "command_id": command.command_id,
            "action": command.action,
            "script_reference": encode_reference(command.script_reference),
        }
        try:
            self._graph.invoke(Command(resume=decision), self._checkpoint_adapter.config(command.thread_id))
        except Exception as exc:  # LangGraph failures are normalized at the boundary.
            return self._failure(
                snapshot,
                "WORKFLOW_EXECUTION_FAILED",
                "workflow execution could not be completed",
            )
        try:
            return self._result_for_snapshot(self.snapshot(command.thread_id))
        except (CheckpointStorageError, WorkflowNotFoundError):
            return self._failure(
                snapshot,
                "WORKFLOW_EXECUTION_FAILED",
                "workflow execution could not be completed",
            )

    def snapshot(self, thread_id: str) -> WorkflowSnapshot:
        """Read a normalized projection from the latest workflow checkpoint."""

        try:
            values = self._checkpoint_adapter.inspect(thread_id)
            return self._snapshot_from_values(thread_id, values)
        except CheckpointNotFoundError:
            raise WorkflowNotFoundError(thread_id) from None
        except CheckpointStorageError:
            raise CheckpointStorageError() from None
        except WorkflowNotFoundError:
            raise
        except Exception as exc:
            raise CheckpointStorageError() from None

    def _build_graph(self):
        graph = StateGraph(_ScriptReviewState)
        graph.add_node("prepare_script_review", self._prepare_script_review)
        graph.add_node("script_review_gate", self._script_review_gate)
        graph.add_node("approve_script", self._approve_script)
        graph.add_node("require_script_revision", self._require_script_revision)
        graph.add_edge(START, "prepare_script_review")
        graph.add_edge("prepare_script_review", "script_review_gate")
        graph.add_conditional_edges(
            "script_review_gate",
            self._route_decision,
            {"approve": "approve_script", "revision": "require_script_revision"},
        )
        graph.add_edge("approve_script", END)
        graph.add_edge("require_script_revision", END)
        return graph.compile(checkpointer=self._checkpoint_adapter.saver)

    @staticmethod
    def _prepare_script_review(state: _ScriptReviewState) -> _ScriptReviewState:
        return {
            "lifecycle_state": "script_review_pending",
            "current_stage": "script_review",
            "pending_gate": "script_review",
            "allowed_actions": list(ALLOWED_SCRIPT_REVIEW_ACTIONS),
            "resume_position": "script_review_decision",
        }

    @staticmethod
    def _script_review_gate(state: _ScriptReviewState) -> _ScriptReviewState:
        # This node has no side effect before interrupt(). It only builds a
        # control request from exact references already in graph state.
        decision = interrupt(
            {
                "gate": "script_review",
                "required": True,
                "script_reference": state["selected_script_ref"],
                "allowed_actions": list(ALLOWED_SCRIPT_REVIEW_ACTIONS),
            }
        )
        return {"decision": decision}

    @staticmethod
    def _route_decision(state: _ScriptReviewState) -> Literal["approve", "revision"]:
        decision = state.get("decision", {})
        return "approve" if decision.get("action") == "approve" else "revision"

    @staticmethod
    def _approve_script(state: _ScriptReviewState) -> _ScriptReviewState:
        return {
            "lifecycle_state": "script_approved",
            "current_stage": "script_review",
            "pending_gate": None,
            "allowed_actions": [],
            "resume_position": "script_approved",
            "command_record": dict(state.get("decision", {})),
        }

    @staticmethod
    def _require_script_revision(state: _ScriptReviewState) -> _ScriptReviewState:
        return {
            "lifecycle_state": "script_revision_required",
            "current_stage": "script_review",
            "pending_gate": None,
            "allowed_actions": [],
            "resume_position": "script_revision_required",
            "command_record": dict(state.get("decision", {})),
        }

    def _validate_command(self, command: ScriptReviewCommand) -> None:
        if not isinstance(command, ScriptReviewCommand):
            raise WorkflowControlError("INVALID_COMMAND", "resume requires a ScriptReviewCommand")
        self._validate_identity(command.task_id, command.thread_id)
        if not self._is_safe_identity(command.command_id):
            raise WorkflowControlError("INVALID_COMMAND", "command identity is required")
        if command.action not in ALLOWED_SCRIPT_REVIEW_ACTIONS:
            raise WorkflowControlError("INVALID_ACTION", "unsupported Script Review action")
        self._validate_script_reference(command.script_reference)

    @staticmethod
    def _validate_identity(task_id: str, thread_id: str) -> None:
        if not ScriptReviewWorkflow._is_safe_identity(task_id):
            raise WorkflowControlError("INVALID_TASK_ID", "task identity is required")
        if not ScriptReviewWorkflow._is_safe_identity(thread_id):
            raise WorkflowControlError("INVALID_THREAD_ID", "thread identity is required")

    @staticmethod
    def _is_safe_identity(value: object) -> bool:
        return (
            isinstance(value, str)
            and bool(value.strip())
            and len(value) <= _MAX_ID_LENGTH
            and not any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
        )

    @staticmethod
    def _validate_script_reference(reference: ArtifactReference) -> ArtifactReference:
        if not isinstance(reference, ArtifactReference):
            raise WorkflowControlError("INVALID_SCRIPT_REFERENCE", "exact Script Artifact Reference is required")
        if reference.artifact_type != "script":
            raise WorkflowControlError("INVALID_SCRIPT_REFERENCE", "reference must target a Script Artifact")
        return decode_reference(reference)

    def _require_script(self, reference: ArtifactReference) -> None:
        try:
            self._artifact_store.get(reference)
        except ArtifactNotFoundError as exc:
            raise WorkflowControlError("SCRIPT_NOT_FOUND", "the exact Script Artifact Reference does not exist") from exc

    @staticmethod
    def _record_matches(record: dict[str, Any], command: ScriptReviewCommand) -> bool:
        try:
            return (
                record.get("task_id") == command.task_id
                and record.get("thread_id") == command.thread_id
                and record.get("command_id") == command.command_id
                and record.get("action") == command.action
                and decode_reference(record.get("script_reference")) == command.script_reference
            )
        except WorkflowControlError:
            return False

    @staticmethod
    def _snapshot_from_values(thread_id: str, values: dict[str, Any]) -> WorkflowSnapshot:
        try:
            if not isinstance(values, dict):
                raise CheckpointStorageError()
            task_id = values["task_id"]
            stored_thread_id = values["thread_id"]
            ScriptReviewWorkflow._validate_stored_identity(task_id)
            ScriptReviewWorkflow._validate_stored_identity(stored_thread_id)
            if stored_thread_id != thread_id:
                raise CheckpointStorageError()

            reference = decode_reference(values["selected_script_ref"])
            if reference.artifact_type != "script":
                raise WorkflowControlError(
                    "INVALID_SCRIPT_REFERENCE",
                    "reference must target a Script Artifact",
                )
            lifecycle_state = values["lifecycle_state"]
            current_stage = values["current_stage"]
            pending_gate = values["pending_gate"]
            stored_allowed_actions = values["allowed_actions"]
            resume_position = values["resume_position"]
            if current_stage != "script_review":
                raise CheckpointStorageError()
            if lifecycle_state == "script_review_pending":
                if (
                    pending_gate != "script_review"
                    or not isinstance(stored_allowed_actions, list)
                    or stored_allowed_actions != list(ALLOWED_SCRIPT_REVIEW_ACTIONS)
                    or resume_position != "script_review_decision"
                    or values.get("command_record") is not None
                ):
                    raise CheckpointStorageError()
                allowed_actions = tuple(stored_allowed_actions)
                last_command_id = None
            elif lifecycle_state in {"script_approved", "script_revision_required"}:
                expected_action = (
                    ("approve",)
                    if lifecycle_state == "script_approved"
                    else ("reject", "revise")
                )
                expected_resume_position = lifecycle_state
                if (
                    pending_gate is not None
                    or not isinstance(stored_allowed_actions, list)
                    or stored_allowed_actions
                    or resume_position != expected_resume_position
                ):
                    raise CheckpointStorageError()
                record = values.get("command_record")
                if not isinstance(record, dict) or set(record) != {
                    "task_id",
                    "thread_id",
                    "command_id",
                    "action",
                    "script_reference",
                }:
                    raise CheckpointStorageError()
                record_task_id = ScriptReviewWorkflow._validate_stored_identity(record["task_id"])
                record_thread_id = ScriptReviewWorkflow._validate_stored_identity(record["thread_id"])
                command_id = ScriptReviewWorkflow._validate_stored_identity(record["command_id"])
                record_reference = decode_reference(record["script_reference"])
                if (
                    record_task_id != task_id
                    or record_thread_id != stored_thread_id
                    or record_reference != reference
                    or record["action"] not in expected_action
                ):
                    raise CheckpointStorageError()
                allowed_actions = ()
                last_command_id = command_id
            else:
                raise CheckpointStorageError()
        except (KeyError, TypeError, WorkflowControlError) as exc:
            raise CheckpointStorageError() from None
        return WorkflowSnapshot(
            task_id=task_id,
            thread_id=stored_thread_id,
            lifecycle_state=lifecycle_state,
            current_stage=current_stage,
            script_reference=reference,
            pending_gate=pending_gate,
            allowed_actions=allowed_actions,
            resume_position=resume_position,
            last_command_id=last_command_id,
        )

    @staticmethod
    def _validate_stored_identity(value: object) -> str:
        if not ScriptReviewWorkflow._is_safe_identity(value):
            raise CheckpointStorageError()
        return value

    @staticmethod
    def _result_for_snapshot(snapshot: WorkflowSnapshot) -> WorkflowResult:
        status = "pending" if snapshot.pending_gate else "success"
        return WorkflowResult(status=status, snapshot=snapshot)

    @staticmethod
    def _failure(snapshot: WorkflowSnapshot, code: str, message: str) -> WorkflowResult:
        return WorkflowResult(status="failure", snapshot=snapshot, error_code=code, error_message=message)

    @staticmethod
    def _execution_failure(snapshot: WorkflowSnapshot | None = None) -> WorkflowResult:
        return WorkflowResult(
            status="failure",
            snapshot=snapshot,
            error_code="WORKFLOW_EXECUTION_FAILED",
            error_message="workflow execution could not be completed",
        )
