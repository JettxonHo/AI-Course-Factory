"""Durable, mandatory Final Video Review control gate."""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
)
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from ai_course_factory.artifacts.commit import (
    ArtifactCommitBoundary,
    ArtifactNotFoundError,
)
from ai_course_factory.artifacts.model import ArtifactReference, ArtifactVersion

from .checkpoint import (
    CheckpointAdapter,
    CheckpointNotFoundError,
    CheckpointStorageError,
    InMemoryCheckpointAdapter,
)
from .model import decode_reference, encode_reference


FINAL_VIDEO_REVIEW_NAMESPACE = "final_video_review"
ALLOWED_FINAL_VIDEO_REVIEW_ACTIONS = ("approve", "reject", "revise")
_MAX_IDENTITY_LENGTH = 256
_APPLICATION_FAILURE_MESSAGE = "final video review workflow could not be completed"
_WORKFLOW_FAILURE_MESSAGE = "workflow execution could not be completed"
_FINAL_CONTROL_KEYS = frozenset(
    "task_id thread_id lifecycle_state current_stage selected_video_ref pending_gate "
    "allowed_actions resume_position decision command_record".split()
)
_FINAL_COMMAND_KEYS = frozenset("task_id thread_id command_id action video_reference".split())


@dataclass(frozen=True, slots=True)
class FinalVideoReviewCommand:
    task_id: str
    thread_id: str
    command_id: str
    action: str
    video_reference: ArtifactReference


@dataclass(frozen=True, slots=True)
class FinalVideoWorkflowSnapshot:
    task_id: str
    thread_id: str
    lifecycle_state: str
    current_stage: str
    video_reference: ArtifactReference
    pending_gate: str | None
    allowed_actions: tuple[str, ...]
    resume_position: str
    last_command_id: str | None = None


@dataclass(frozen=True, slots=True)
class FinalVideoWorkflowResult:
    status: str
    snapshot: FinalVideoWorkflowSnapshot | None = None
    error_code: str | None = None
    error_message: str | None = None

    def _projection(self, field: str, default: Any) -> Any:
        return getattr(self.snapshot, field, default)

    @property
    def lifecycle_state(self) -> str | None:
        return self._projection("lifecycle_state", None)

    @property
    def current_stage(self) -> str | None:
        return self._projection("current_stage", None)

    @property
    def video_reference(self) -> ArtifactReference | None:
        return self._projection("video_reference", None)

    @property
    def pending_gate(self) -> str | None:
        return self._projection("pending_gate", None)

    @property
    def allowed_actions(self) -> tuple[str, ...]:
        return self._projection("allowed_actions", ())

    @property
    def resume_position(self) -> str | None:
        return self._projection("resume_position", None)


class FinalVideoWorkflowNotFoundError(KeyError):
    pass

class _WorkflowValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _FinalVideoState(TypedDict, total=False):
    task_id: str
    thread_id: str
    lifecycle_state: str
    current_stage: str
    selected_video_ref: dict[str, Any]
    pending_gate: str | None
    allowed_actions: list[str]
    resume_position: str
    decision: dict[str, Any]
    command_record: dict[str, Any]


class _NamespacedCheckpointSaver(BaseCheckpointSaver):
    def __init__(self, delegate: BaseCheckpointSaver, namespace: str) -> None:
        super().__init__(serde=delegate.serde)
        self._delegate = delegate
        self._namespace = namespace

    def _config(self, config: dict[str, Any] | None) -> dict[str, Any]:
        result = dict(config or {})
        configurable = dict(result.get("configurable", {}))
        configurable["checkpoint_ns"] = self._namespace
        result["configurable"] = configurable
        return result

    def _call(self, method: str, config: dict[str, Any], *args: Any) -> Any:
        return getattr(self._delegate, method)(self._config(config), *args)

    def get_tuple(self, config: dict[str, Any]) -> Any:
        return self._call("get_tuple", config)

    def put(
        self,
        config: dict[str, Any],
        checkpoint: Any,
        metadata: Any,
        new_versions: Any,
    ) -> dict[str, Any]:
        return self._call("put", config, checkpoint, metadata, new_versions)

    def put_writes(
        self,
        config: dict[str, Any],
        writes: list[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        self._call("put_writes", config, writes, task_id, task_path)


def _same_reference(actual: object, expected: ArtifactReference) -> bool:
    actual_values = (actual.artifact_type, actual.identity, actual.version)
    expected_values = (expected.artifact_type, expected.identity, expected.version)
    return type(actual) is ArtifactReference and all(
        type(value) is expected_type and value == expected_value
        for value, expected_type, expected_value in zip(actual_values, (str, str, int), expected_values)
    )

def _decode_reference(value: object) -> ArtifactReference:
    try:
        if type(value) is dict and set(value) != {"artifact_type", "identity", "version"}:
            raise ValueError
        reference = decode_reference(value)
    except Exception:
        raise _WorkflowValidation(
            "INVALID_VIDEO_REFERENCE", "an exact Video Artifact Reference is required"
        ) from None
    return _validate_video_reference(reference)


def _invalid_video_reference() -> None:
    raise _WorkflowValidation("INVALID_VIDEO_REFERENCE", "an exact Video Artifact Reference is required")


def _validate_video_reference(reference: object) -> ArtifactReference:
    if type(reference) is not ArtifactReference:
        _invalid_video_reference()
    if type(reference.artifact_type) is not str or reference.artifact_type != "video":
        _invalid_video_reference()
    _validate_identity(
        reference.identity,
        "INVALID_VIDEO_REFERENCE",
        "an exact Video Artifact Reference is required",
    )
    if type(reference.version) is not int or isinstance(reference.version, bool) or reference.version <= 0:
        _invalid_video_reference()
    return reference


def _validate_identity(value: object, code: str, message: str) -> str:
    if (
        type(value) is not str
        or not value.strip()
        or len(value) > _MAX_IDENTITY_LENGTH
        or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        or value.strip().casefold() in {"latest", "current"}
    ):
        raise _WorkflowValidation(code, message)
    return value


class FinalVideoReviewWorkflow:
    def __init__(
        self,
        artifact_repository: ArtifactCommitBoundary,
        checkpoint_adapter: CheckpointAdapter | None = None,
    ) -> None:
        self._artifact_repository = artifact_repository
        self._checkpoint_adapter = (
            checkpoint_adapter
            if checkpoint_adapter is not None
            else InMemoryCheckpointAdapter()
        )
        namespaced_saver = _NamespacedCheckpointSaver(
            self._checkpoint_adapter.saver,
            FINAL_VIDEO_REVIEW_NAMESPACE,
        )
        self._graph = self._build_graph(namespaced_saver)

    @property
    def checkpoint_adapter(self) -> CheckpointAdapter:
        return self._checkpoint_adapter

    def start(
        self,
        task_id: str,
        thread_id: str,
        video_reference: ArtifactReference,
    ) -> FinalVideoWorkflowResult:
        try:
            self._validate_command_identity(task_id, thread_id)
            reference = _validate_video_reference(video_reference)
            self._require_video(reference)
        except _WorkflowValidation as exc:
            return self._failure(exc.code, exc.message)
        except Exception:
            return self._failure("WORKFLOW_EXECUTION_FAILED")

        try:
            if self._checkpoint_adapter.has_checkpoint(
                thread_id, FINAL_VIDEO_REVIEW_NAMESPACE
            ):
                snapshot = self.snapshot(thread_id)
                if snapshot.task_id != task_id or snapshot.video_reference != reference:
                    return self._failure(
                        "THREAD_BINDING_CONFLICT",
                        "thread is already bound to another task or Video Version",
                        snapshot=snapshot,
                    )
                return self._result_for_snapshot(snapshot)
        except FinalVideoWorkflowNotFoundError:
            return self._failure("CHECKPOINT_INVALID", "workflow checkpoint is not readable")
        except CheckpointStorageError:
            return self._execution_failure()

        initial_state: _FinalVideoState = {
            "task_id": task_id,
            "thread_id": thread_id,
            "lifecycle_state": "task_initialized",
            "current_stage": "final_video_review",
            "selected_video_ref": encode_reference(reference),
            "pending_gate": None,
            "allowed_actions": [],
            "resume_position": "final_video_review_start",
        }
        try:
            config = self._checkpoint_adapter.config(
                thread_id, FINAL_VIDEO_REVIEW_NAMESPACE
            )
            self._graph.invoke(initial_state, config, durability="sync")
            return self._result_for_snapshot(self.snapshot(thread_id))
        except Exception:
            return self._execution_failure()

    def resume(self, command: FinalVideoReviewCommand) -> FinalVideoWorkflowResult:
        try:
            self._validate_command(command)
            snapshot = self.snapshot(command.thread_id)
        except _WorkflowValidation as exc:
            return self._failure(exc.code, exc.message)
        except FinalVideoWorkflowNotFoundError:
            return self._failure("WORKFLOW_NOT_FOUND", "workflow checkpoint does not exist")
        except CheckpointStorageError:
            return self._execution_failure()

        try:
            state = self._checkpoint_adapter.inspect(
                command.thread_id, FINAL_VIDEO_REVIEW_NAMESPACE
            )
            existing = state.get("command_record")
            if isinstance(existing, dict) and existing.get("command_id") == command.command_id:
                if self._record_matches(existing, command):
                    return self._result_for_snapshot(snapshot)
                return self._failure(
                    "COMMAND_CONFLICT",
                    "command identity was already used for another decision",
                    snapshot=snapshot,
                )
            self._validate_pending_command(snapshot, command)
            self._require_video(command.video_reference)
        except _WorkflowValidation as exc:
            return self._failure(exc.code, exc.message, snapshot=snapshot)
        except CheckpointNotFoundError:
            return self._execution_failure(snapshot=snapshot)
        except CheckpointStorageError:
            return self._execution_failure(snapshot=snapshot)

        decision = {
            "task_id": command.task_id,
            "thread_id": command.thread_id,
            "command_id": command.command_id,
            "action": command.action,
            "video_reference": encode_reference(command.video_reference),
        }
        try:
            self._graph.invoke(
                Command(resume=decision),
                self._checkpoint_adapter.config(
                    command.thread_id, FINAL_VIDEO_REVIEW_NAMESPACE
                ),
                durability="sync",
            )
        except Exception:
            return self._execution_failure(snapshot=snapshot)
        try:
            return self._result_for_snapshot(self.snapshot(command.thread_id))
        except (CheckpointStorageError, FinalVideoWorkflowNotFoundError):
            return self._execution_failure(snapshot=snapshot)

    def snapshot(self, thread_id: str) -> FinalVideoWorkflowSnapshot:
        try:
            _validate_identity(
                thread_id, "INVALID_THREAD_ID", "thread identity is required"
            )
            values = self._checkpoint_adapter.inspect(
                thread_id, FINAL_VIDEO_REVIEW_NAMESPACE
            )
            return self._snapshot_from_values(thread_id, values)
        except CheckpointNotFoundError:
            raise FinalVideoWorkflowNotFoundError(thread_id) from None
        except CheckpointStorageError:
            raise CheckpointStorageError() from None
        except FinalVideoWorkflowNotFoundError:
            raise
        except _WorkflowValidation:
            raise CheckpointStorageError() from None
        except Exception:
            raise CheckpointStorageError() from None

    @staticmethod
    def _build_graph(checkpointer: BaseCheckpointSaver):
        graph = StateGraph(_FinalVideoState)
        graph.add_node("prepare_final_video_review", FinalVideoReviewWorkflow._prepare_gate)
        graph.add_node("final_video_review_gate", FinalVideoReviewWorkflow._gate)
        graph.add_node(
            "approve_final_video",
            partial(FinalVideoReviewWorkflow._finish, lifecycle_state="approved"),
        )
        graph.add_node(
            "require_final_video_revision",
            partial(FinalVideoReviewWorkflow._finish, lifecycle_state="revision_required"),
        )
        graph.add_edge(START, "prepare_final_video_review")
        graph.add_edge("prepare_final_video_review", "final_video_review_gate")
        graph.add_conditional_edges(
            "final_video_review_gate",
            FinalVideoReviewWorkflow._route,
            {"approve": "approve_final_video", "revision": "require_final_video_revision"},
        )
        graph.add_edge("approve_final_video", END)
        graph.add_edge("require_final_video_revision", END)
        return graph.compile(checkpointer=checkpointer)

    @staticmethod
    def _prepare_gate(_: _FinalVideoState) -> _FinalVideoState:
        return {
            "lifecycle_state": "final_review_pending",
            "current_stage": "final_video_review",
            "pending_gate": "final_video_review",
            "allowed_actions": list(ALLOWED_FINAL_VIDEO_REVIEW_ACTIONS),
            "resume_position": "final_video_review_decision",
        }

    @staticmethod
    def _gate(state: _FinalVideoState) -> _FinalVideoState:
        decision = interrupt(
            {
                "gate": "final_video_review",
                "required": True,
                "video_reference": state["selected_video_ref"],
                "allowed_actions": list(ALLOWED_FINAL_VIDEO_REVIEW_ACTIONS),
            }
        )
        return {"decision": decision}

    @staticmethod
    def _route(state: _FinalVideoState) -> Literal["approve", "revision"]:
        decision = state.get("decision", {})
        return "approve" if decision.get("action") == "approve" else "revision"

    @staticmethod
    def _finish(state: _FinalVideoState, *, lifecycle_state: str) -> _FinalVideoState:
        record = dict(state.get("decision", {}))
        return {
            "lifecycle_state": lifecycle_state,
            "current_stage": "final_video_review",
            "pending_gate": None,
            "allowed_actions": [],
            "resume_position": lifecycle_state,
            "command_record": record,
        }

    @staticmethod
    def _validate_command_identity(task_id: object, thread_id: object) -> None:
        _validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
        _validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")

    @staticmethod
    def _validate_command(command: object) -> FinalVideoReviewCommand:
        if type(command) is not FinalVideoReviewCommand:
            raise _WorkflowValidation(
                "INVALID_COMMAND", "resume requires a FinalVideoReviewCommand"
            )
        FinalVideoReviewWorkflow._validate_command_identity(
            command.task_id, command.thread_id
        )
        _validate_identity(command.command_id, "INVALID_COMMAND", "command identity is required")
        if type(command.action) is not str or command.action not in ALLOWED_FINAL_VIDEO_REVIEW_ACTIONS:
            raise _WorkflowValidation("INVALID_ACTION", "unsupported Final Video Review action")
        _validate_video_reference(command.video_reference)
        return command

    def _require_video(self, reference: ArtifactReference) -> ArtifactVersion:
        try:
            version = self._artifact_repository.get(reference)
        except ArtifactNotFoundError as exc:
            raise _WorkflowValidation(
                "VIDEO_NOT_FOUND", "the exact Video Artifact Reference does not exist"
            ) from exc
        if type(version) is not ArtifactVersion or not _same_reference(version.reference, reference):
            raise _WorkflowValidation(
                "INVALID_VIDEO_VERSION", "the exact Video Artifact Version is invalid"
            )
        return version

    @staticmethod
    def _validate_pending_command(
        snapshot: FinalVideoWorkflowSnapshot,
        command: FinalVideoReviewCommand,
    ) -> None:
        checks = (
            (snapshot.task_id, command.task_id, "TASK_MISMATCH", "command task does not match checkpoint"),
            (snapshot.thread_id, command.thread_id, "THREAD_MISMATCH", "command thread does not match checkpoint"),
            (snapshot.pending_gate, FINAL_VIDEO_REVIEW_NAMESPACE, "GATE_NOT_PENDING", "Final Video Review is not awaiting a decision"),
            (snapshot.video_reference, command.video_reference, "VIDEO_REFERENCE_MISMATCH", "command must target the selected exact Video Version"),
        )
        for actual, expected, code, message in checks:
            if actual != expected:
                raise _WorkflowValidation(code, message)

    @staticmethod
    def _decode_record(
        record: object,
        reference: ArtifactReference,
    ) -> dict[str, Any] | None:
        if type(record) is not dict or set(record) != _FINAL_COMMAND_KEYS:
            return None
        try:
            text = tuple(record[key] for key in ("task_id", "thread_id", "command_id", "action"))
            if any(type(value) is not str for value in text) or text[-1] not in ALLOWED_FINAL_VIDEO_REVIEW_ACTIONS:
                return None
            if not _same_reference(_decode_reference(record["video_reference"]), reference):
                return None
        except Exception:
            return None
        return record

    @classmethod
    def _record_matches(
        cls,
        record: object,
        command: FinalVideoReviewCommand,
    ) -> bool:
        decoded = cls._decode_record(record, command.video_reference)
        return decoded is not None and all(
            decoded[key] == getattr(command, key)
            for key in ("task_id", "thread_id", "command_id", "action")
        )

    @classmethod
    def _snapshot_from_values(
        cls,
        thread_id: str,
        values: dict[str, Any],
    ) -> FinalVideoWorkflowSnapshot:
        if type(values) is not dict:
            raise CheckpointStorageError()
        for key, value in values.items():
            if not isinstance(key, str):
                raise CheckpointStorageError()
            if key not in _FINAL_CONTROL_KEYS:
                if not key.startswith("branch:to:") or value is not None:
                    raise CheckpointStorageError()
        try:
            task_id = _validate_identity(values["task_id"], "INVALID_TASK_ID", "task identity is required")
            stored_thread_id = _validate_identity(values["thread_id"], "INVALID_THREAD_ID", "thread identity is required")
            if stored_thread_id != thread_id:
                raise CheckpointStorageError()
            reference = _decode_reference(values["selected_video_ref"])
            if type(values["lifecycle_state"]) is not str or type(values["current_stage"]) is not str:
                raise CheckpointStorageError()
            if values["current_stage"] != "final_video_review":
                raise CheckpointStorageError()
            lifecycle_state = values["lifecycle_state"]
            pending_gate = values["pending_gate"]
            actions = values["allowed_actions"]
            resume_position = values["resume_position"]
            if type(actions) is not list or any(type(item) is not str for item in actions):
                raise CheckpointStorageError()
            if lifecycle_state == "final_review_pending":
                if (
                    pending_gate != "final_video_review"
                    or actions != list(ALLOWED_FINAL_VIDEO_REVIEW_ACTIONS)
                    or resume_position != "final_video_review_decision"
                    or values.get("command_record") is not None
                    or "decision" in values
                ):
                    raise CheckpointStorageError()
                last_command_id = None
            elif lifecycle_state in {"approved", "revision_required"}:
                last_command_id = cls._read_terminal_record(
                    values, lifecycle_state, reference, pending_gate, actions, resume_position
                )
            else:
                raise CheckpointStorageError()
        except (KeyError, TypeError, _WorkflowValidation):
            raise CheckpointStorageError() from None
        return FinalVideoWorkflowSnapshot(
            task_id=task_id,
            thread_id=stored_thread_id,
            lifecycle_state=lifecycle_state,
            current_stage="final_video_review",
            video_reference=reference,
            pending_gate=pending_gate,
            allowed_actions=tuple(actions),
            resume_position=resume_position,
            last_command_id=last_command_id,
        )

    @classmethod
    def _read_terminal_record(
        cls,
        values: dict[str, Any],
        lifecycle_state: str,
        reference: ArtifactReference,
        pending_gate: object,
        actions: list[str],
        resume_position: object,
    ) -> str:
        if pending_gate is not None or actions or resume_position != lifecycle_state:
            raise CheckpointStorageError()
        command = cls._decode_record(values.get("command_record"), reference)
        decision = cls._decode_record(values.get("decision"), reference)
        if command is None or decision is None or command != decision:
            raise CheckpointStorageError()
        expected = "approve" if lifecycle_state == "approved" else {"reject", "revise"}
        valid_action = (
            command["action"] == expected
            if isinstance(expected, str)
            else command["action"] in expected
        )
        if not valid_action:
            raise CheckpointStorageError()
        return command["command_id"]

    @staticmethod
    def _result_for_snapshot(snapshot: FinalVideoWorkflowSnapshot) -> FinalVideoWorkflowResult:
        return FinalVideoWorkflowResult(status="pending" if snapshot.pending_gate else "success", snapshot=snapshot)

    @staticmethod
    def _failure(
        code: str,
        message: str | None = None,
        *,
        snapshot: FinalVideoWorkflowSnapshot | None = None,
    ) -> FinalVideoWorkflowResult:
        return FinalVideoWorkflowResult(
            status="failure",
            snapshot=snapshot,
            error_code=code,
            error_message=message or _APPLICATION_FAILURE_MESSAGE,
        )

    @staticmethod
    def _execution_failure(
        *, snapshot: FinalVideoWorkflowSnapshot | None = None
    ) -> FinalVideoWorkflowResult:
        return FinalVideoReviewWorkflow._failure(
            "WORKFLOW_EXECUTION_FAILED", _WORKFLOW_FAILURE_MESSAGE, snapshot=snapshot
        )


__all__ = [
    "ALLOWED_FINAL_VIDEO_REVIEW_ACTIONS",
    "FINAL_VIDEO_REVIEW_NAMESPACE",
    "FinalVideoReviewCommand",
    "FinalVideoReviewWorkflow",
    "FinalVideoWorkflowNotFoundError",
    "FinalVideoWorkflowResult",
    "FinalVideoWorkflowSnapshot",
]
