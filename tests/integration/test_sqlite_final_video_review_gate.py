"""Durable Final Video Review Workflow + Application integration evidence."""

from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    FinalVideoDecisionBoundary,
    SQLiteFinalVideoDecisionRepository,
)
from ai_course_factory.application import FinalVideoReviewApplicationService
from ai_course_factory.workflow import (
    FinalVideoReviewWorkflow,
    SQLiteCheckpointAdapter,
    ScriptReviewWorkflow,
)
from tests.workflow.test_final_video_review_workflow import commit_video


class FailingOnceResumeWorkflow:
    def __init__(self, workflow):
        self._workflow = workflow
        self.failed = False

    def start(self, *args, **kwargs):
        return self._workflow.start(*args, **kwargs)

    def snapshot(self, *args, **kwargs):
        return self._workflow.snapshot(*args, **kwargs)

    def resume(self, command):
        if not self.failed:
            self.failed = True
            from ai_course_factory.workflow import FinalVideoWorkflowResult

            return FinalVideoWorkflowResult(
                status="failure",
                error_code="WORKFLOW_EXECUTION_FAILED",
                error_message="workflow execution could not be completed",
            )
        return self._workflow.resume(command)


class SQLiteFinalVideoReviewGateIntegrationTests(unittest.TestCase):
    def test_one_sqlite_checkpoint_db_keeps_script_default_and_final_namespace_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workflow.sqlite3"
            artifacts = ArtifactCommitBoundary()
            script = artifacts.commit(
                ArtifactCandidate(
                    "script", "episode:script", {"text": "bounded"}, (), (), True, "script-1"
                )
            )
            video = commit_video(artifacts)
            adapter = SQLiteCheckpointAdapter(database)
            try:
                script_workflow = ScriptReviewWorkflow(artifacts, adapter)
                final_workflow = FinalVideoReviewWorkflow(artifacts, adapter)
                self.assertEqual(script_workflow.start("task-1", "shared-thread", script).status, "pending")
                self.assertEqual(final_workflow.start("task-1", "shared-thread", video).status, "pending")
                self.assertTrue(adapter.has_checkpoint("shared-thread"))
                self.assertTrue(adapter.has_checkpoint("shared-thread", "final_video_review"))
                self.assertEqual(adapter.inspect("shared-thread")["pending_gate"], "script_review")
                self.assertEqual(
                    adapter.inspect("shared-thread", "final_video_review")["pending_gate"],
                    "final_video_review",
                )
                adapter.close()

                reopened = SQLiteCheckpointAdapter(database)
                try:
                    script_restarted = ScriptReviewWorkflow(artifacts, reopened)
                    final_restarted = FinalVideoReviewWorkflow(artifacts, reopened)
                    self.assertEqual(script_restarted.snapshot("shared-thread").script_reference, script)
                    self.assertEqual(final_restarted.snapshot("shared-thread").video_reference, video)
                finally:
                    reopened.close()
            finally:
                adapter.close()

    def test_decision_persists_before_resume_and_retries_after_sqlite_reconstruction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workflow_db = root / "workflow.sqlite3"
            decision_db = root / "decision.sqlite3"
            artifacts = ArtifactCommitBoundary()
            video = commit_video(artifacts)
            checkpoints = SQLiteCheckpointAdapter(workflow_db)
            decisions = SQLiteFinalVideoDecisionRepository(decision_db)
            try:
                workflow = FinalVideoReviewWorkflow(artifacts, checkpoints)
                boundary = FinalVideoDecisionBoundary(decisions)
                failing = FailingOnceResumeWorkflow(workflow)
                service = FinalVideoReviewApplicationService(artifacts, boundary, failing)
                self.assertEqual(service.start("task-1", "thread-1", video).status, "pending")
                first = service.decide(
                    "task-1", "thread-1", "decision-1", "creator-1", "approve", video
                )
                self.assertEqual(first.error_code, "WORKFLOW_EXECUTION_FAILED")
                self.assertIsNotNone(first.decision_record)
                self.assertEqual(workflow.snapshot("thread-1").pending_gate, "final_video_review")
                checkpoints.close()
                decisions.close()

                reopened_checkpoints = SQLiteCheckpointAdapter(workflow_db)
                reopened_decisions = SQLiteFinalVideoDecisionRepository(decision_db)
                try:
                    restarted_workflow = FinalVideoReviewWorkflow(artifacts, reopened_checkpoints)
                    restarted_boundary = FinalVideoDecisionBoundary(reopened_decisions)
                    restarted_service = FinalVideoReviewApplicationService(
                        artifacts, restarted_boundary, restarted_workflow
                    )
                    retry = restarted_service.decide(
                        "task-1", "thread-1", "decision-1", "creator-1", "approve", video
                    )
                    self.assertEqual(retry.status, "success")
                    self.assertEqual(retry.workflow_result.snapshot.lifecycle_state, "approved")
                    self.assertEqual(restarted_boundary.get("decision-1"), first.decision_record)
                finally:
                    reopened_checkpoints.close()
                    reopened_decisions.close()
            finally:
                checkpoints.close()
                decisions.close()


if __name__ == "__main__":
    unittest.main()
