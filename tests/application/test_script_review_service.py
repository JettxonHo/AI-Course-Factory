"""Public behavior tests for Script Review Application coordination."""

from __future__ import annotations

import unittest

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    ArtifactReference,
    ScriptDecisionBoundary,
    ScriptDecisionFailure,
)
from ai_course_factory.application.script_review import ScriptReviewApplicationService
from ai_course_factory.workflow import InMemoryCheckpointAdapter, ScriptReviewWorkflow
from ai_course_factory.workflow.model import WorkflowResult


def committed_lineage() -> tuple[
    ArtifactCommitBoundary,
    ArtifactReference,
    ArtifactReference,
    ArtifactReference,
    ArtifactReference,
]:
    store = ArtifactCommitBoundary()
    knowledge = store.commit(
        ArtifactCandidate(
            artifact_type="knowledge",
            identity="knowledge:episode-1",
            payload={
                "claims": (
                    {"claim_id": "claim-ai-tool", "statement": "AI is a tool."},
                    {"claim_id": "claim-not-magic", "statement": "AI is not magic."},
                )
            },
            provenance=("source-record:v1",),
            dependencies=(),
            validated=True,
            commit_id="knowledge-1",
        )
    )
    course = store.commit(
        ArtifactCandidate(
            artifact_type="content_plan",
            identity="course-plan:episode-1",
            payload={
                "role": "course",
                "knowledge_reference": knowledge,
                "plan": {"knowledge_claim_ids": ("claim-ai-tool", "claim-not-magic")},
            },
            provenance=("knowledge:v1",),
            dependencies=(knowledge,),
            validated=True,
            commit_id="course-plan-1",
        )
    )
    episode = store.commit(
        ArtifactCandidate(
            artifact_type="content_plan",
            identity="episode-plan:episode-1",
            payload={
                "role": "episode",
                "knowledge_reference": knowledge,
                "plan": {"knowledge_claim_ids": ("claim-ai-tool", "claim-not-magic")},
            },
            provenance=("knowledge:v1",),
            dependencies=(knowledge,),
            validated=True,
            commit_id="episode-plan-1",
        )
    )
    script = store.commit(
        ArtifactCandidate(
            artifact_type="script",
            identity="script:episode-1",
            payload=script_payload(knowledge, course, episode),
            provenance=("content-agent:v1",),
            dependencies=(knowledge, course, episode),
            validated=True,
            commit_id="script-1",
        )
    )
    return store, knowledge, course, episode, script


def script_payload(
    knowledge: ArtifactReference,
    course: ArtifactReference,
    episode: ArtifactReference,
    *,
    language: str = "Simplified Chinese",
) -> dict[str, object]:
    return {
        "knowledge_reference": knowledge,
        "course_plan_reference": course,
        "episode_plan_reference": episode,
        "language": language,
        "template_constraint": {
            "scene_count": 6,
            "target_duration_seconds": 60,
            "aspect_ratio": "9:16",
        },
        "duration_seconds": 60,
        "aspect_ratio": "9:16",
        "scenes": tuple(
            {
                "scene_id": f"scene-{index}",
                "duration_seconds": 10,
                "narration": f"第{index + 1}幕：人工智能是一种工具。",
                "teaching_intent": f"解释第{index + 1}幕。",
                "knowledge_claim_ids": (
                    "claim-ai-tool" if index % 2 == 0 else "claim-not-magic",
                ),
            }
            for index in range(6)
        ),
    }


class RecordingWorkflow(ScriptReviewWorkflow):
    """Observe the public decision store immediately before resume."""

    def __init__(self, *args, decision_boundary: ScriptDecisionBoundary, **kwargs):
        super().__init__(*args, **kwargs)
        self._decision_boundary = decision_boundary
        self.observed_decision = None

    def resume(self, command):
        self.observed_decision = self._decision_boundary.get(command.command_id)
        return super().resume(command)


class FailOnceWorkflow:
    """Public workflow adapter that simulates one resume boundary failure."""

    def __init__(self, workflow: ScriptReviewWorkflow) -> None:
        self._workflow = workflow
        self._failed = False

    def start(self, task_id, thread_id, script_reference):
        return self._workflow.start(task_id, thread_id, script_reference)

    def snapshot(self, thread_id):
        return self._workflow.snapshot(thread_id)

    def resume(self, command):
        if not self._failed:
            self._failed = True
            snapshot = self._workflow.snapshot(command.thread_id)
            return WorkflowResult(
                status="failure",
                snapshot=snapshot,
                error_code="WORKFLOW_EXECUTION_FAILED",
                error_message="workflow execution could not be completed",
            )
        return self._workflow.resume(command)


class ScriptReviewApplicationTests(unittest.TestCase):
    def setUp(self) -> None:
        (
            self.store,
            self.knowledge_reference,
            self.course_reference,
            self.episode_reference,
            self.script_reference,
        ) = committed_lineage()
        self.decisions = ScriptDecisionBoundary()
        self.checkpoints = InMemoryCheckpointAdapter()
        self.workflow = ScriptReviewWorkflow(self.store, self.checkpoints)
        self.service = ScriptReviewApplicationService(self.store, self.decisions, self.workflow)

    def test_start_resolves_exact_lineage_and_opens_mandatory_pending_gate(self):
        result = self.service.start("task-1", "thread-1", self.script_reference)

        self.assertEqual(result.status, "pending")
        self.assertIsNotNone(result.assessment)
        self.assertEqual(result.assessment.disposition, "pass")
        self.assertEqual(result.assessment.script_reference, self.script_reference)
        self.assertEqual(result.workflow_result.pending_gate, "script_review")
        checkpoint = self.checkpoints.inspect("thread-1")
        self.assertEqual(checkpoint["selected_script_ref"], self.script_reference)
        self.assertNotIn("payload", checkpoint)

    def test_hard_block_approve_fails_before_resume_and_keeps_pending(self):
        bad_reference = self.store.commit(
            ArtifactCandidate(
                artifact_type="script",
                identity="script:episode-1",
                payload=script_payload(
                    self.knowledge_reference,
                    self.course_reference,
                    self.episode_reference,
                    language="English",
                ),
                provenance=("content-agent:v2",),
                dependencies=(self.knowledge_reference, self.course_reference, self.episode_reference),
                validated=True,
                commit_id="script-2",
                prior_reference=self.script_reference,
            )
        )
        started = self.service.start("task-1", "hard-block-thread", bad_reference)
        self.assertEqual(started.status, "pending")
        self.assertEqual(started.assessment.disposition, "hard_block")

        result = self.service.decide(
            "task-1",
            "hard-block-thread",
            "decision-hard-block",
            "creator-1",
            "approve",
            bad_reference,
        )

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error_code, "HARD_BLOCK_APPROVAL_FORBIDDEN")
        self.assertIsInstance(self.decisions.get("decision-hard-block"), ScriptDecisionFailure)
        self.assertEqual(
            self.workflow.snapshot("hard-block-thread").pending_gate,
            "script_review",
        )

    def test_pending_validation_happens_before_decision_persistence(self):
        result = self.service.decide(
            "task-1",
            "missing-thread",
            "decision-missing",
            "creator-1",
            "approve",
            self.script_reference,
        )

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error_code, "WORKFLOW_NOT_FOUND")
        self.assertIsInstance(self.decisions.get("decision-missing"), ScriptDecisionFailure)

    def test_decision_is_persisted_before_workflow_resume(self):
        workflow = RecordingWorkflow(
            self.store,
            self.checkpoints,
            decision_boundary=self.decisions,
        )
        service = ScriptReviewApplicationService(self.store, self.decisions, workflow)
        service.start("task-1", "thread-order", self.script_reference)

        result = service.decide(
            "task-1",
            "thread-order",
            "decision-revise",
            "creator-1",
            "revise",
            self.script_reference,
            decision_context="Make scene two more concrete.",
        )

        self.assertEqual(result.status, "success")
        self.assertEqual(result.workflow_result.lifecycle_state, "script_revision_required")
        self.assertEqual(workflow.observed_decision, result.decision_record)
        self.assertEqual(result.decision_record.decision_context, "Make scene two more concrete.")

        replay = service.decide(
            "task-1",
            "thread-order",
            "decision-revise",
            "creator-1",
            "revise",
            self.script_reference,
            decision_context="Make scene two more concrete.",
        )
        self.assertEqual(replay.status, "success")
        self.assertIs(replay.decision_record, result.decision_record)
        self.assertEqual(replay.lifecycle_state, "script_revision_required")

    def test_workflow_failure_after_persistence_keeps_record_and_allows_retry(self):
        failing_workflow = FailOnceWorkflow(self.workflow)
        service = ScriptReviewApplicationService(self.store, self.decisions, failing_workflow)
        service.start("task-1", "thread-failure", self.script_reference)

        first = service.decide(
            "task-1",
            "thread-failure",
            "decision-failure",
            "creator-1",
            "approve",
            self.script_reference,
        )
        self.assertEqual(first.status, "failure")
        self.assertEqual(first.error_code, "WORKFLOW_EXECUTION_FAILED")
        self.assertIsNotNone(first.decision_record)
        self.assertIs(self.decisions.get("decision-failure"), first.decision_record)

        retry_service = ScriptReviewApplicationService(
            self.store,
            self.decisions,
            ScriptReviewWorkflow(self.store, self.checkpoints),
        )
        retry = retry_service.decide(
            "task-1",
            "thread-failure",
            "decision-failure",
            "creator-1",
            "approve",
            self.script_reference,
        )
        self.assertEqual(retry.status, "success")
        self.assertIs(retry.decision_record, first.decision_record)
        self.assertEqual(retry.lifecycle_state, "script_approved")

    def test_wrong_exact_script_reference_fails_closed_without_resuming_gate(self):
        self.service.start("task-1", "thread-ref", self.script_reference)
        wrong_reference = ArtifactReference("script", self.script_reference.identity, 2)

        result = self.service.decide(
            "task-1",
            "thread-ref",
            "decision-wrong-ref",
            "creator-1",
            "approve",
            wrong_reference,
        )

        self.assertEqual(result.status, "failure")
        self.assertEqual(result.error_code, "SCRIPT_REFERENCE_MISMATCH")
        self.assertIsInstance(self.decisions.get("decision-wrong-ref"), ScriptDecisionFailure)
        self.assertEqual(self.workflow.snapshot("thread-ref").pending_gate, "script_review")


if __name__ == "__main__":
    unittest.main()
