"""Restart, replay and failure evidence for the SQLite Script Review checkpoint."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from ai_course_factory.application.script_review import ScriptReviewApplicationService
from ai_course_factory.artifacts import (
    ArtifactCandidate,
    SQLiteArtifactRepository,
    SQLiteScriptDecisionRepository,
    ScriptDecisionBoundary,
)
from ai_course_factory.workflow import (
    CheckpointStorageError,
    InMemoryCheckpointAdapter,
    SQLiteCheckpointAdapter,
    ScriptReviewCommand,
    ScriptReviewWorkflow,
)
from tests.application.test_script_review_service import committed_lineage


def _control_reference(reference):
    return {
        "artifact_type": reference.artifact_type,
        "identity": reference.identity,
        "version": reference.version,
    }


def _seed_checkpoint(adapter, thread_id, values):
    versions = {key: index + 1 for index, key in enumerate(values)}
    adapter.saver.put(
        {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_ns": "",
            }
        },
        {
            "v": 1,
            "id": f"checkpoint-{thread_id}",
            "ts": "2026-08-12T00:00:00+00:00",
            "channel_values": values,
            "channel_versions": versions,
            "versions_seen": {},
            "updated_channels": None,
        },
        {"source": "input", "step": 0, "writes": {}},
        versions,
    )


class SQLiteScriptReviewCheckpointIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self._temporary.name)
        self.artifact_path = self.directory / "artifacts.sqlite3"
        self.checkpoint_path = self.directory / "checkpoints.sqlite3"
        self.artifacts = SQLiteArtifactRepository(self.artifact_path)
        knowledge_reference = self.artifacts.commit(
            ArtifactCandidate(
                artifact_type="knowledge",
                identity="knowledge:checkpoint-demo",
                payload={"claims": ("claim-checkpoint",)},
                provenance=(),
                dependencies=(),
                validated=True,
                commit_id="knowledge-1",
            )
        )
        course_reference = self.artifacts.commit(
            ArtifactCandidate(
                artifact_type="content_plan",
                identity="course-plan:checkpoint-demo",
                payload={"role": "course", "knowledge_reference": knowledge_reference},
                provenance=(),
                dependencies=(knowledge_reference,),
                validated=True,
                commit_id="course-plan-1",
            )
        )
        episode_reference = self.artifacts.commit(
            ArtifactCandidate(
                artifact_type="content_plan",
                identity="episode-plan:checkpoint-demo",
                payload={"role": "episode", "knowledge_reference": knowledge_reference},
                provenance=(),
                dependencies=(knowledge_reference,),
                validated=True,
                commit_id="episode-plan-1",
            )
        )
        self.script_reference = self.artifacts.commit(
            ArtifactCandidate(
                artifact_type="script",
                identity="script:checkpoint-demo",
                payload={
                    "text": "distinctive-checkpoint-script-payload",
                    "knowledge_reference": knowledge_reference,
                    "course_plan_reference": course_reference,
                    "episode_plan_reference": episode_reference,
                },
                provenance=(),
                dependencies=(knowledge_reference, course_reference, episode_reference),
                validated=True,
                commit_id="script-1",
            )
        )
        self.checkpoints = SQLiteCheckpointAdapter(self.checkpoint_path)
        self.workflow = ScriptReviewWorkflow(self.artifacts, self.checkpoints)

    def tearDown(self) -> None:
        self.checkpoints.close()
        self.artifacts.close()
        self._temporary.cleanup()

    def _command(self, action: str = "approve", command_id: str = "command-1") -> ScriptReviewCommand:
        return ScriptReviewCommand(
            task_id="task-1",
            thread_id="thread-1",
            command_id=command_id,
            action=action,
            script_reference=self.script_reference,
        )

    def test_pending_checkpoint_restores_exact_binding_after_close_and_reopen(self):
        pending = self.workflow.start("task-1", "thread-1", self.script_reference)
        self.assertEqual(pending.status, "pending")
        before = pending.snapshot
        checkpoint = self.checkpoints.inspect("thread-1")
        self.assertEqual(checkpoint["selected_script_ref"], self.script_reference)
        self.assertNotIn("distinctive-checkpoint-script-payload", repr(checkpoint))
        self.assertNotIn("payload", checkpoint)
        self.assertNotIn(
            b"distinctive-checkpoint-script-payload",
            self.checkpoint_path.read_bytes(),
        )

        self.checkpoints.close()
        self.artifacts.close()
        self.checkpoints = SQLiteCheckpointAdapter(self.checkpoint_path)
        self.artifacts = SQLiteArtifactRepository(self.artifact_path)
        self.workflow = ScriptReviewWorkflow(self.artifacts, self.checkpoints)

        restored = self.workflow.start("task-1", "thread-1", self.script_reference)
        self.assertEqual(restored.status, "pending")
        self.assertEqual(restored.snapshot, before)
        restored_script = self.artifacts.get(self.script_reference)
        self.assertEqual(len(restored_script.dependencies), 3)
        self.assertEqual(self.artifacts.get(restored_script.dependencies[0]).artifact_type, "knowledge")

        task_conflict = self.workflow.start("other-task", "thread-1", self.script_reference)
        self.assertEqual(task_conflict.error_code, "THREAD_BINDING_CONFLICT")
        self.assertEqual(self.workflow.snapshot("thread-1"), before)

        changed_reference = self.artifacts.commit(
            ArtifactCandidate(
                artifact_type="script",
                identity="script:other",
                payload={"text": "another script"},
                provenance=(),
                dependencies=(),
                validated=True,
                commit_id="script-other",
            )
        )
        reference_conflict = self.workflow.start("task-1", "thread-1", changed_reference)
        self.assertEqual(reference_conflict.error_code, "THREAD_BINDING_CONFLICT")
        self.assertEqual(self.workflow.snapshot("thread-1"), before)

    def test_terminal_checkpoint_and_equivalent_command_replay_after_reopen(self):
        pending = self.workflow.start("task-1", "thread-1", self.script_reference)
        approved = self.workflow.resume(self._command())
        self.assertEqual(approved.status, "success")
        self.assertEqual(approved.lifecycle_state, "script_approved")
        self.assertEqual(approved.snapshot.last_command_id, "command-1")

        self.checkpoints.close()
        self.artifacts.close()
        self.checkpoints = SQLiteCheckpointAdapter(self.checkpoint_path)
        self.artifacts = SQLiteArtifactRepository(self.artifact_path)
        self.workflow = ScriptReviewWorkflow(self.artifacts, self.checkpoints)

        self.assertEqual(
            self.workflow.start("task-1", "thread-1", self.script_reference),
            approved,
        )
        self.assertEqual(self.workflow.resume(self._command()), approved)
        conflict = self.workflow.resume(self._command(action="revise"))
        self.assertEqual(conflict.status, "failure")
        self.assertEqual(conflict.error_code, "COMMAND_CONFLICT")
        self.assertEqual(self.workflow.snapshot("thread-1"), approved.snapshot)

    def test_two_sqlite_adapters_observe_one_committed_checkpoint(self):
        second = SQLiteCheckpointAdapter(self.checkpoint_path)
        try:
            pending = self.workflow.start("task-1", "thread-1", self.script_reference)
            self.assertTrue(second.has_checkpoint("thread-1"))
            self.assertEqual(second.inspect("thread-1")["selected_script_ref"], self.script_reference)
            second_workflow = ScriptReviewWorkflow(self.artifacts, second)
            self.assertEqual(
                second_workflow.start("task-1", "thread-1", self.script_reference),
                pending,
            )
        finally:
            second.close()

    def test_closed_or_corrupt_storage_is_safe_and_does_not_advance(self):
        pending = self.workflow.start("task-1", "thread-1", self.script_reference)
        self.checkpoints.close()

        failed_start = self.workflow.start("task-1", "other-thread", self.script_reference)
        self.assertEqual(failed_start.status, "failure")
        self.assertEqual(failed_start.error_code, "WORKFLOW_EXECUTION_FAILED")
        self.assertEqual(failed_start.error_message, "workflow execution could not be completed")
        with self.assertRaises(CheckpointStorageError) as context:
            self.workflow.snapshot("thread-1")
        self.assertEqual(str(context.exception), "workflow checkpoint persistence failed")
        self.assertIsNone(context.exception.__cause__)
        self.assertNotIn(str(self.checkpoint_path), str(context.exception))

        self.checkpoint_path.write_bytes(b"not a SQLite database")
        with self.assertRaisesRegex(
            CheckpointStorageError,
            "^workflow checkpoint persistence failed$",
        ) as corrupt:
            SQLiteCheckpointAdapter(self.checkpoint_path)
        self.assertNotIn(str(self.checkpoint_path), str(corrupt.exception))

    def test_application_persists_decision_before_failed_resume_and_retries_after_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            artifacts, _, _, _, script_reference = committed_lineage()
            decision_path = directory / "decisions.sqlite3"
            checkpoint_path = directory / "checkpoints.sqlite3"
            decisions = SQLiteScriptDecisionRepository(decision_path)
            checkpoints = SQLiteCheckpointAdapter(checkpoint_path)
            try:
                boundary = ScriptDecisionBoundary(decisions)
                workflow = ScriptReviewWorkflow(artifacts, checkpoints)
                service = ScriptReviewApplicationService(artifacts, boundary, workflow)
                started = service.start("task-1", "thread-app", script_reference)
                self.assertEqual(started.status, "pending")
                pending_snapshot = started.snapshot

                def fail_checkpoint_write(*args, **kwargs):
                    raise RuntimeError("raw checkpoint path should not escape")

                checkpoints.saver.put = fail_checkpoint_write
                failed = service.decide(
                    "task-1",
                    "thread-app",
                    "decision-app",
                    "creator-1",
                    "approve",
                    script_reference,
                )
                self.assertEqual(failed.status, "failure")
                self.assertEqual(failed.error_code, "WORKFLOW_EXECUTION_FAILED")
                self.assertEqual(failed.error_message, "workflow execution could not be completed")
                self.assertIsNotNone(failed.decision_record)
                self.assertEqual(workflow.snapshot("thread-app").pending_gate, "script_review")
                self.assertNotIn("raw checkpoint path", failed.error_message or "")
                self.assertEqual(decisions.get("decision-app"), failed.decision_record)

                checkpoints.close()
                decisions.close()
                decisions = SQLiteScriptDecisionRepository(decision_path)
                checkpoints = SQLiteCheckpointAdapter(checkpoint_path)
                reopened_boundary = ScriptDecisionBoundary(decisions)
                reopened_workflow = ScriptReviewWorkflow(artifacts, checkpoints)
                reopened_service = ScriptReviewApplicationService(
                    artifacts,
                    reopened_boundary,
                    reopened_workflow,
                )
                self.assertEqual(reopened_workflow.snapshot("thread-app"), pending_snapshot)
                self.assertEqual(decisions.get("decision-app"), failed.decision_record)

                retry = reopened_service.decide(
                    "task-1",
                    "thread-app",
                    "decision-app",
                    "creator-1",
                    "approve",
                    script_reference,
                )
                self.assertEqual(retry.status, "success")
                self.assertEqual(retry.lifecycle_state, "script_approved")
                self.assertEqual(decisions.get("decision-app"), failed.decision_record)
            finally:
                checkpoints.close()
                decisions.close()

    def test_sqlite_decision_and_terminal_checkpoint_replay_after_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            artifacts, _, _, _, script_reference = committed_lineage()
            decision_path = directory / "decisions.sqlite3"
            checkpoint_path = directory / "checkpoints.sqlite3"
            decisions = SQLiteScriptDecisionRepository(decision_path)
            checkpoints = SQLiteCheckpointAdapter(checkpoint_path)
            boundary = ScriptDecisionBoundary(decisions)
            workflow = ScriptReviewWorkflow(artifacts, checkpoints)
            service = ScriptReviewApplicationService(artifacts, boundary, workflow)
            try:
                self.assertEqual(service.start("task-1", "thread-replay", script_reference).status, "pending")
                first = service.decide(
                    "task-1",
                    "thread-replay",
                    "decision-replay",
                    "creator-1",
                    "revise",
                    script_reference,
                    decision_context="Clarify scene two.",
                )
                self.assertEqual(first.status, "success")
            finally:
                checkpoints.close()
                decisions.close()

            decisions = SQLiteScriptDecisionRepository(decision_path)
            checkpoints = SQLiteCheckpointAdapter(checkpoint_path)
            try:
                reopened_boundary = ScriptDecisionBoundary(decisions)
                reopened_workflow = ScriptReviewWorkflow(artifacts, checkpoints)
                reopened_service = ScriptReviewApplicationService(
                    artifacts,
                    reopened_boundary,
                    reopened_workflow,
                )
                replay = reopened_service.decide(
                    "task-1",
                    "thread-replay",
                    "decision-replay",
                    "creator-1",
                    "revise",
                    script_reference,
                    decision_context="Clarify scene two.",
                )
                self.assertEqual(replay, first)
                self.assertEqual(reopened_workflow.snapshot("thread-replay"), first.snapshot)
            finally:
                checkpoints.close()
                decisions.close()

    def test_invalid_control_id_inputs_do_not_read_or_advance_checkpoint(self):
        for invalid_thread in ("thread\x00", "t" * 257):
            with self.subTest(kind="thread", value=repr(invalid_thread)):
                started = self.workflow.start("task-1", invalid_thread, self.script_reference)
                self.assertEqual(started.error_code, "INVALID_THREAD_ID")
                self.assertFalse(self.checkpoints.has_checkpoint(invalid_thread))
                resumed = self.workflow.resume(
                    ScriptReviewCommand(
                        task_id="task-1",
                        thread_id=invalid_thread,
                        command_id="command-1",
                        action="approve",
                        script_reference=self.script_reference,
                    )
                )
                self.assertEqual(resumed.error_code, "INVALID_THREAD_ID")
                self.assertFalse(self.checkpoints.has_checkpoint(invalid_thread))

        for invalid_task in ("task\x00", "t" * 257):
            with self.subTest(kind="task", value=repr(invalid_task)):
                started = self.workflow.start(invalid_task, "thread-invalid-task", self.script_reference)
                self.assertEqual(started.error_code, "INVALID_TASK_ID")
                self.assertFalse(self.checkpoints.has_checkpoint("thread-invalid-task"))
                resumed = self.workflow.resume(
                    ScriptReviewCommand(
                        task_id=invalid_task,
                        thread_id="thread-invalid-task",
                        command_id="command-1",
                        action="approve",
                        script_reference=self.script_reference,
                    )
                )
                self.assertEqual(resumed.error_code, "INVALID_TASK_ID")
                self.assertFalse(self.checkpoints.has_checkpoint("thread-invalid-task"))

        pending = self.workflow.start("task-1", "thread-command-id", self.script_reference)
        self.assertEqual(pending.status, "pending")
        before = self.checkpoints.values("thread-command-id")
        for invalid_command_id in ("command\x00", "c" * 257):
            with self.subTest(kind="command", value=repr(invalid_command_id)):
                resumed = self.workflow.resume(
                    ScriptReviewCommand(
                        task_id="task-1",
                        thread_id="thread-command-id",
                        command_id=invalid_command_id,
                        action="approve",
                        script_reference=self.script_reference,
                    )
                )
                self.assertEqual(resumed.error_code, "INVALID_COMMAND")
                self.assertEqual(self.checkpoints.values("thread-command-id"), before)
                self.assertEqual(self.workflow.snapshot("thread-command-id"), pending.snapshot)

    def test_snapshot_restores_only_exact_script_review_projections(self):
        projections = (
            {
                "task_id": "task-1",
                "thread_id": "thread-projection",
                "lifecycle_state": "script_review_pending",
                "current_stage": "script_review",
                "selected_script_ref": _control_reference(self.script_reference),
                "pending_gate": "script_review",
                "allowed_actions": ["approve", "reject", "revise"],
                "resume_position": "script_review_decision",
            },
            {
                "task_id": "task-1",
                "thread_id": "thread-projection",
                "lifecycle_state": "script_approved",
                "current_stage": "script_review",
                "selected_script_ref": _control_reference(self.script_reference),
                "pending_gate": None,
                "allowed_actions": [],
                "resume_position": "script_approved",
                "command_record": {
                    "task_id": "task-1",
                    "thread_id": "thread-projection",
                    "command_id": "command-approved",
                    "action": "approve",
                    "script_reference": _control_reference(self.script_reference),
                },
            },
            {
                "task_id": "task-1",
                "thread_id": "thread-projection",
                "lifecycle_state": "script_revision_required",
                "current_stage": "script_review",
                "selected_script_ref": _control_reference(self.script_reference),
                "pending_gate": None,
                "allowed_actions": [],
                "resume_position": "script_revision_required",
                "command_record": {
                    "task_id": "task-1",
                    "thread_id": "thread-projection",
                    "command_id": "command-revise",
                    "action": "revise",
                    "script_reference": _control_reference(self.script_reference),
                },
            },
        )
        expected = (
            ("script_review_pending", "script_review", ("approve", "reject", "revise"), "script_review_decision", None),
            ("script_approved", None, (), "script_approved", "command-approved"),
            ("script_revision_required", None, (), "script_revision_required", "command-revise"),
        )

        for values, expectation in zip(projections, expected, strict=True):
            with self.subTest(lifecycle=expectation[0]):
                adapter = InMemoryCheckpointAdapter()
                _seed_checkpoint(adapter, "thread-projection", values)
                workflow = ScriptReviewWorkflow(self.artifacts, adapter)
                snapshot = workflow.snapshot("thread-projection")
                self.assertEqual(snapshot.task_id, "task-1")
                self.assertEqual(snapshot.thread_id, "thread-projection")
                self.assertEqual(snapshot.lifecycle_state, expectation[0])
                self.assertEqual(snapshot.current_stage, "script_review")
                self.assertEqual(snapshot.script_reference, self.script_reference)
                self.assertEqual(snapshot.pending_gate, expectation[1])
                self.assertIs(type(snapshot.allowed_actions), tuple)
                self.assertEqual(snapshot.allowed_actions, expectation[2])
                self.assertEqual(snapshot.resume_position, expectation[3])
                self.assertEqual(snapshot.last_command_id, expectation[4])

    def test_malformed_pending_projection_fails_safe_without_checkpoint_write(self):
        pending = {
            "task_id": "task-1",
            "thread_id": "thread-mutation",
            "lifecycle_state": "script_review_pending",
            "current_stage": "script_review",
            "selected_script_ref": _control_reference(self.script_reference),
            "pending_gate": "script_review",
            "allowed_actions": ["approve", "reject", "revise"],
            "resume_position": "script_review_decision",
        }
        mutations = {
            "task_type": {"task_id": 17},
            "thread_binding": {"thread_id": "other-thread"},
            "lifecycle_type": {"lifecycle_state": 17},
            "current_stage_type": {"current_stage": 17},
            "pending_gate_type": {"pending_gate": 17},
            "allowed_actions_type": {"allowed_actions": "approve"},
            "resume_position_type": {"resume_position": 17},
            "reference_type": {
                "selected_script_ref": {
                    "artifact_type": "other",
                    "identity": "script",
                    "version": 1,
                }
            },
        }
        for name, mutation in mutations.items():
            with self.subTest(mutation=name):
                values = dict(pending)
                values.update(mutation)
                adapter = InMemoryCheckpointAdapter()
                _seed_checkpoint(adapter, "thread-mutation", values)
                workflow = ScriptReviewWorkflow(self.artifacts, adapter)
                before = adapter.values("thread-mutation")
                with self.assertRaises(CheckpointStorageError) as context:
                    workflow.snapshot("thread-mutation")
                self.assertIsNone(context.exception.__cause__)
                result = workflow.start("task-1", "thread-mutation", self.script_reference)
                self.assertEqual(result.status, "failure")
                self.assertEqual(result.error_code, "WORKFLOW_EXECUTION_FAILED")
                self.assertEqual(adapter.values("thread-mutation"), before)

    def test_malformed_terminal_projection_fails_safe_without_checkpoint_write(self):
        terminal = {
            "task_id": "task-1",
            "thread_id": "thread-terminal",
            "lifecycle_state": "script_approved",
            "current_stage": "script_review",
            "selected_script_ref": _control_reference(self.script_reference),
            "pending_gate": None,
            "allowed_actions": [],
            "resume_position": "script_approved",
            "command_record": {
                "task_id": "task-1",
                "thread_id": "thread-terminal",
                "command_id": "command-terminal",
                "action": "approve",
                "script_reference": _control_reference(self.script_reference),
            },
        }
        mutations = (
            ("stored_thread", {"thread_id": "other-thread"}),
            ("command_id_type", {"command_record": {**terminal["command_record"], "command_id": 17}}),
            ("command_thread", {"command_record": {**terminal["command_record"], "thread_id": "other-thread"}}),
            ("terminal_actions", {"allowed_actions": "approve"}),
        )
        for name, mutation in mutations:
            with self.subTest(mutation=name):
                values = dict(terminal)
                values.update(mutation)
                adapter = InMemoryCheckpointAdapter()
                _seed_checkpoint(adapter, "thread-terminal", values)
                workflow = ScriptReviewWorkflow(self.artifacts, adapter)
                before = adapter.values("thread-terminal")
                with self.assertRaises(CheckpointStorageError) as context:
                    workflow.snapshot("thread-terminal")
                self.assertIsNone(context.exception.__cause__)
                result = workflow.start("task-1", "thread-terminal", self.script_reference)
                self.assertEqual(result.status, "failure")
                self.assertEqual(result.error_code, "WORKFLOW_EXECUTION_FAILED")
                self.assertEqual(adapter.values("thread-terminal"), before)


if __name__ == "__main__":
    unittest.main()
