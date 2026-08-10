"""Public behavior tests for the resumable Script Review workflow."""

import unittest

from langgraph.checkpoint.memory import InMemorySaver

from ai_course_factory.artifacts.commit import ArtifactCommitBoundary
from ai_course_factory.artifacts.model import ArtifactCandidate, ArtifactReference
from ai_course_factory.workflow import (
    InMemoryCheckpointAdapter,
    ScriptReviewCommand,
    ScriptReviewWorkflow,
)


class ScriptReviewWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts = ArtifactCommitBoundary()
        self.script_reference = self.artifacts.commit(
            ArtifactCandidate(
                artifact_type="script",
                identity="episode:ai-is-not-magic",
                payload={"text": "AI is a tool, not magic."},
                provenance=("knowledge:episode:ai-is-not-magic:v1",),
                dependencies=(),
                validated=True,
                commit_id="script-generation-1",
            )
        )
        self.checkpoints = InMemoryCheckpointAdapter()
        self.workflow = ScriptReviewWorkflow(
            artifact_store=self.artifacts,
            checkpoint_adapter=self.checkpoints,
        )

    def _start(self, thread_id: str = "thread-1"):
        return self.workflow.start(
            task_id="task-1",
            thread_id=thread_id,
            script_reference=self.script_reference,
        )

    def _command(self, thread_id: str, action: str, command_id: str = "cmd-1"):
        return ScriptReviewCommand(
            task_id="task-1",
            thread_id=thread_id,
            command_id=command_id,
            action=action,
            script_reference=self.script_reference,
        )

    def test_start_pauses_at_mandatory_review_with_exact_reference(self):
        pending = self._start()

        self.assertEqual(pending.status, "pending")
        self.assertEqual(pending.lifecycle_state, "script_review_pending")
        self.assertEqual(pending.pending_gate, "script_review")
        self.assertEqual(pending.script_reference, self.script_reference)
        self.assertEqual(pending.allowed_actions, ("approve", "reject", "revise"))

    def test_start_normalizes_checkpoint_execution_failure(self):
        class FailingSaver(InMemorySaver):
            def put(self, *args, **kwargs):
                raise RuntimeError("simulated checkpoint failure")

        failing_workflow = ScriptReviewWorkflow(
            artifact_store=self.artifacts,
            checkpoint_adapter=InMemoryCheckpointAdapter(FailingSaver()),
        )

        result = failing_workflow.start(
            task_id="task-1",
            thread_id="failing-thread",
            script_reference=self.script_reference,
        )

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error_code, "WORKFLOW_EXECUTION_FAILED")
        self.assertEqual(result.error_message, "workflow execution could not be completed")

    def test_checkpoint_is_control_only_and_reconstructed_runtime_can_resume(self):
        pending = self._start()
        checkpoint = self.checkpoints.inspect("thread-1")
        self.assertEqual(checkpoint["selected_script_ref"], self.script_reference)
        self.assertEqual(checkpoint["pending_gate"], "script_review")
        self.assertNotIn("payload", checkpoint)
        self.assertNotIn("text", repr(checkpoint))

        reconstructed = ScriptReviewWorkflow(
            artifact_store=self.artifacts,
            checkpoint_adapter=self.checkpoints,
        )
        self.assertEqual(reconstructed.snapshot("thread-1"), pending.snapshot)

        approved = reconstructed.resume(self._command("thread-1", "approve"))
        self.assertEqual(approved.status, "success")
        self.assertEqual(approved.lifecycle_state, "script_approved")
        self.assertEqual(approved.script_reference, self.script_reference)
        self.assertIsNone(approved.pending_gate)

    def test_reject_and_revise_reach_revision_required(self):
        for action, thread_id in (("reject", "thread-reject"), ("revise", "thread-revise")):
            with self.subTest(action=action):
                self._start(thread_id)
                result = self.workflow.resume(self._command(thread_id, action))
                self.assertEqual(result.status, "success")
                self.assertEqual(result.lifecycle_state, "script_revision_required")
                self.assertEqual(result.script_reference, self.script_reference)

    def test_wrong_version_unknown_reference_and_invalid_action_fail_closed(self):
        pending = self._start()
        wrong_version = ArtifactReference("script", self.script_reference.identity, 2)
        unknown = ArtifactReference("script", "episode:unknown", 1)

        wrong = self.workflow.resume(
            ScriptReviewCommand(
                task_id="task-1",
                thread_id="thread-1",
                command_id="wrong-version",
                action="approve",
                script_reference=wrong_version,
            )
        )
        self.assertEqual(wrong.status, "failure")
        self.assertEqual(self.workflow.snapshot("thread-1"), pending.snapshot)

        missing = self.workflow.resume(
            ScriptReviewCommand(
                task_id="task-1",
                thread_id="thread-1",
                command_id="unknown-reference",
                action="approve",
                script_reference=unknown,
            )
        )
        self.assertEqual(missing.status, "failure")
        self.assertEqual(self.workflow.snapshot("thread-1"), pending.snapshot)

        invalid = self.workflow.resume(
            ScriptReviewCommand(
                task_id="task-1",
                thread_id="thread-1",
                command_id="invalid-action",
                action="publish",
                script_reference=self.script_reference,
            )
        )
        self.assertEqual(invalid.status, "failure")
        self.assertEqual(self.workflow.snapshot("thread-1"), pending.snapshot)

    def test_equivalent_command_replay_is_idempotent_and_conflict_fails_closed(self):
        self._start()
        command = self._command("thread-1", "approve", "decision-1")
        first = self.workflow.resume(command)
        replay = self.workflow.resume(command)

        self.assertEqual(first, replay)
        self.assertEqual(replay.lifecycle_state, "script_approved")

        conflict = self.workflow.resume(
            self._command("thread-1", "revise", "decision-1")
        )
        self.assertEqual(conflict.status, "failure")
        self.assertEqual(conflict.error_code, "COMMAND_CONFLICT")
        self.assertEqual(self.workflow.snapshot("thread-1").lifecycle_state, "script_approved")

        task_conflict = self.workflow.resume(
            ScriptReviewCommand(
                task_id="other-task",
                thread_id="thread-1",
                command_id="decision-1",
                action="approve",
                script_reference=self.script_reference,
            )
        )
        self.assertEqual(task_conflict.status, "failure")
        self.assertEqual(task_conflict.error_code, "COMMAND_CONFLICT")

    def test_command_target_must_match_task_and_thread(self):
        self._start()
        wrong_task = ScriptReviewCommand(
            task_id="other-task",
            thread_id="thread-1",
            command_id="wrong-task",
            action="approve",
            script_reference=self.script_reference,
        )
        wrong_thread = ScriptReviewCommand(
            task_id="task-1",
            thread_id="other-thread",
            command_id="wrong-thread",
            action="approve",
            script_reference=self.script_reference,
        )

        self.assertEqual(self.workflow.resume(wrong_task).status, "failure")
        self.assertEqual(self.workflow.resume(wrong_thread).status, "failure")
        self.assertEqual(self.workflow.snapshot("thread-1").lifecycle_state, "script_review_pending")


if __name__ == "__main__":
    unittest.main()
