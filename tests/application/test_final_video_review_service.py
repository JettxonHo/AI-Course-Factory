"""Public behavior tests for Final Video Review application coordination."""

from __future__ import annotations

import unittest
from dataclasses import fields, replace

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    FinalVideoDecisionBoundary,
    FinalVideoDecisionFailure,
    FinalVideoDecisionRecord,
    FinalVideoGateFinding,
)
from ai_course_factory.application import (
    FinalVideoReviewApplicationResult,
    FinalVideoReviewApplicationService,
)
from ai_course_factory.workflow import (
    FinalVideoReviewWorkflow,
    FinalVideoWorkflowResult,
)
from tests.workflow.test_final_video_review_workflow import commit_video


class FailingDecisionRepository:
    def save(self, _record):
        return FinalVideoDecisionFailure(
            "execution", "FINAL_VIDEO_DECISION_FAILED", "decision persistence failed"
        )

    def get(self, _decision_id):
        return FinalVideoDecisionFailure(
            "validation", "DECISION_NOT_FOUND", "decision record does not exist"
        )


class FailingResumeWorkflow:
    def __init__(self, workflow):
        self._workflow = workflow
        self.resume_calls = 0

    def start(self, *args, **kwargs):
        return self._workflow.start(*args, **kwargs)

    def snapshot(self, *args, **kwargs):
        return self._workflow.snapshot(*args, **kwargs)

    def resume(self, command):
        self.resume_calls += 1
        if self.resume_calls == 1:
            return FinalVideoWorkflowResult(
                status="failure",
                error_code="WORKFLOW_EXECUTION_FAILED",
                error_message="workflow execution could not be completed",
            )
        return self._workflow.resume(command)


class MismatchedDecisionBoundary:
    def __init__(self):
        self._boundary = FinalVideoDecisionBoundary()

    def assess(self, *args):
        return self._boundary.assess(*args)

    def decide(self, *args, **kwargs):
        decision = self._boundary.decide(*args, **kwargs)
        if isinstance(decision, FinalVideoDecisionRecord):
            return replace(decision, decision_id="foreign-decision")
        return decision

    def get(self, decision_id):
        return self._boundary.get(decision_id)


class ForgedAssessmentBoundary:
    def __init__(self):
        self._boundary = FinalVideoDecisionBoundary()

    def assess(self, *args):
        assessment = self._boundary.assess(*args)
        if hasattr(assessment, "video_reference"):
            return replace(
                assessment,
                disposition="pass",
                findings=(FinalVideoGateFinding("FORGED", "forged finding"),),
            )
        return assessment

    def decide(self, *args, **kwargs):
        return self._boundary.decide(*args, **kwargs)

    def get(self, decision_id):
        return self._boundary.get(decision_id)


class ForgedRecordBoundary:
    def __init__(self, finding_codes=()):
        self._boundary = FinalVideoDecisionBoundary()
        self._finding_codes = finding_codes

    def assess(self, *args):
        return self._boundary.assess(*args)

    def decide(self, *args, **kwargs):
        decision = self._boundary.decide(*args, **kwargs)
        if isinstance(decision, FinalVideoDecisionRecord):
            return replace(
                decision,
                assessment_disposition="hard_block" if not self._finding_codes else decision.assessment_disposition,
                finding_codes=self._finding_codes,
            )
        return decision

    def get(self, decision_id):
        return self._boundary.get(decision_id)


class RecordingDecisionRepository:
    def __init__(self, events):
        self._records = {}
        self._events = events

    def save(self, record):
        self._events.append("save")
        self._records[record.decision_id] = record
        return record

    def get(self, decision_id):
        return self._records.get(decision_id)


class RecordingWorkflow:
    def __init__(self, workflow, repository, events):
        self._workflow = workflow
        self._repository = repository
        self._events = events

    def start(self, *args, **kwargs):
        return self._workflow.start(*args, **kwargs)

    def snapshot(self, *args, **kwargs):
        return self._workflow.snapshot(*args, **kwargs)

    def resume(self, command):
        self._events.append(
            "resume_after_save"
            if isinstance(self._repository.get(command.command_id), FinalVideoDecisionRecord)
            else "resume_before_save"
        )
        return self._workflow.resume(command)


class FinalVideoReviewApplicationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.artifacts = ArtifactCommitBoundary()
        self.video_reference = commit_video(self.artifacts)
        self.workflow = FinalVideoReviewWorkflow(self.artifacts)
        self.boundary = FinalVideoDecisionBoundary()
        self.service = FinalVideoReviewApplicationService(
            self.artifacts,
            self.boundary,
            self.workflow,
        )

    def _start(self):
        return self.service.start("task:episode-1", "thread:episode-1", self.video_reference)

    def test_start_assesses_exact_video_then_opens_pending_gate(self):
        result = self._start()
        self.assertEqual(result.status, "pending")
        self.assertEqual(result.assessment.disposition, "pass")
        self.assertEqual(result.workflow_result.snapshot.video_reference, self.video_reference)
        self.assertNotIn("payload", self.workflow.checkpoint_adapter.inspect("thread:episode-1", "final_video_review"))

    def test_public_application_result_is_literal_frozen_and_slotted(self):
        self.assertEqual(
            tuple(field.name for field in fields(FinalVideoReviewApplicationResult)),
            ("status", "assessment", "decision_record", "workflow_result", "error_code", "error_message"),
        )
        self.assertTrue(FinalVideoReviewApplicationResult.__dataclass_params__.frozen)
        self.assertTrue(hasattr(FinalVideoReviewApplicationResult, "__slots__"))

    def test_forged_assessment_fails_before_opening_checkpoint(self):
        workflow = FinalVideoReviewWorkflow(self.artifacts)
        service = FinalVideoReviewApplicationService(
            self.artifacts, ForgedAssessmentBoundary(), workflow
        )
        result = service.start("task-forged", "thread-forged", self.video_reference)
        self.assertEqual(result.error_code, "FINAL_VIDEO_DECISION_FAILED")
        self.assertFalse(workflow.checkpoint_adapter.has_checkpoint("thread-forged", "final_video_review"))

    def test_forged_exact_record_assessment_fields_cannot_resume(self):
        for finding_codes in ((), ("FORGED",)):
            with self.subTest(finding_codes=finding_codes):
                workflow = FinalVideoReviewWorkflow(self.artifacts)
                service = FinalVideoReviewApplicationService(
                    self.artifacts, ForgedRecordBoundary(finding_codes), workflow
                )
                self.assertEqual(service.start("task-forged", "thread-forged", self.video_reference).status, "pending")
                result = service.decide(
                    "task-forged", "thread-forged", "decision-forged", "creator-1", "approve", self.video_reference
                )
                self.assertEqual(result.error_code, "FINAL_VIDEO_DECISION_FAILED")
                self.assertEqual(workflow.snapshot("thread-forged").pending_gate, "final_video_review")

    def test_decision_persist_order_is_observed_at_resume_boundary(self):
        events = []
        repository = RecordingDecisionRepository(events)
        boundary = FinalVideoDecisionBoundary(repository)
        workflow = FinalVideoReviewWorkflow(self.artifacts)
        recording_workflow = RecordingWorkflow(workflow, repository, events)
        service = FinalVideoReviewApplicationService(self.artifacts, boundary, recording_workflow)
        self.assertEqual(service.start("task-order", "thread-order", self.video_reference).status, "pending")
        events.clear()
        result = service.decide(
            "task-order", "thread-order", "decision-order", "creator-1", "approve", self.video_reference
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(events, ["save", "resume_after_save"])

    def test_decision_persists_before_workflow_resume_and_returns_terminal(self):
        self._start()
        result = self.service.decide(
            "task:episode-1",
            "thread:episode-1",
            "decision-1",
            "creator-1",
            "approve",
            self.video_reference,
        )
        self.assertEqual(result.status, "success")
        self.assertIsInstance(result.decision_record, FinalVideoDecisionRecord)
        self.assertEqual(result.workflow_result.snapshot.lifecycle_state, "approved")
        self.assertEqual(self.boundary.get("decision-1"), result.decision_record)

    def test_hard_block_approval_does_not_advance_pending_checkpoint(self):
        bad_payload = dict(self.artifacts.get(self.video_reference).payload)
        bad_payload["media_type"] = "video/webm"
        bad_reference = self.artifacts.commit(
            ArtifactCandidate(
                "video",
                "media:episode-1-bad",
                bad_payload,
                (),
                self.artifacts.get(self.video_reference).dependencies,
                True,
                "video-bad",
            )
        )
        workflow = FinalVideoReviewWorkflow(self.artifacts)
        boundary = FinalVideoDecisionBoundary()
        service = FinalVideoReviewApplicationService(self.artifacts, boundary, workflow)
        self.assertEqual(service.start("task:bad", "thread:bad", bad_reference).status, "pending")
        result = service.decide(
            "task:bad", "thread:bad", "decision-bad", "creator-1", "approve", bad_reference
        )
        self.assertEqual(result.error_code, "HARD_BLOCK_APPROVAL_FORBIDDEN")
        self.assertEqual(workflow.snapshot("thread:bad").pending_gate, "final_video_review")

    def test_decision_storage_failure_leaves_checkpoint_pending(self):
        workflow = FinalVideoReviewWorkflow(self.artifacts)
        failing = FinalVideoReviewApplicationService(
            self.artifacts,
            FinalVideoDecisionBoundary(FailingDecisionRepository()),
            workflow,
        )
        self.assertEqual(failing.start("task-1", "thread-1", self.video_reference).status, "pending")
        result = failing.decide(
            "task-1", "thread-1", "decision-fail", "creator-1", "approve", self.video_reference
        )
        self.assertEqual(result.error_code, "FINAL_VIDEO_DECISION_FAILED")
        self.assertEqual(workflow.snapshot("thread-1").pending_gate, "final_video_review")

    def test_mismatched_repository_success_cannot_advance_checkpoint(self):
        workflow = FinalVideoReviewWorkflow(self.artifacts)
        service = FinalVideoReviewApplicationService(
            self.artifacts, MismatchedDecisionBoundary(), workflow
        )
        service.start("task-1", "thread-1", self.video_reference)
        result = service.decide(
            "task-1", "thread-1", "decision-foreign", "creator-1", "approve", self.video_reference
        )
        self.assertEqual(result.error_code, "FINAL_VIDEO_DECISION_FAILED")
        self.assertEqual(workflow.snapshot("thread-1").pending_gate, "final_video_review")

    def test_decision_survives_resume_failure_and_retry_after_reconstruction(self):
        workflow = FinalVideoReviewWorkflow(self.artifacts)
        boundary = FinalVideoDecisionBoundary()
        failing_workflow = FailingResumeWorkflow(workflow)
        first = FinalVideoReviewApplicationService(self.artifacts, boundary, failing_workflow)
        first.start("task-1", "thread-1", self.video_reference)
        failed = first.decide(
            "task-1", "thread-1", "decision-retry", "creator-1", "approve", self.video_reference
        )
        self.assertEqual(failed.error_code, "WORKFLOW_EXECUTION_FAILED")
        self.assertIsNotNone(failed.decision_record)
        self.assertEqual(workflow.snapshot("thread-1").pending_gate, "final_video_review")

        reconstructed = FinalVideoReviewApplicationService(self.artifacts, boundary, workflow)
        retried = reconstructed.decide(
            "task-1", "thread-1", "decision-retry", "creator-1", "approve", self.video_reference
        )
        self.assertEqual(retried.status, "success")
        self.assertEqual(retried.workflow_result.snapshot.lifecycle_state, "approved")

    def test_terminal_replay_returns_same_decision_without_new_record(self):
        self._start()
        first = self.service.decide(
            "task:episode-1", "thread:episode-1", "decision-replay", "creator-1", "approve", self.video_reference
        )
        replay = self.service.decide(
            "task:episode-1", "thread:episode-1", "decision-replay", "creator-1", "approve", self.video_reference
        )
        self.assertEqual(replay.status, "success")
        self.assertEqual(replay.decision_record, first.decision_record)
        self.assertEqual(replay.assessment, first.assessment)
        conflict = self.service.decide(
            "task:episode-1", "thread:episode-1", "decision-replay", "creator-1", "reject", self.video_reference,
            "reject exact version",
        )
        self.assertEqual(conflict.error_code, "COMMAND_CONFLICT")

    def test_mismatched_target_and_invalid_video_fail_without_resume(self):
        self._start()
        mismatch = self.service.decide(
            "task:episode-1", "thread:episode-1", "decision-wrong", "creator-1", "approve",
            replace(self.video_reference, version=2),
        )
        self.assertEqual(mismatch.error_code, "VIDEO_REFERENCE_MISMATCH")
        self.assertEqual(self.workflow.snapshot("thread:episode-1").pending_gate, "final_video_review")


if __name__ == "__main__":
    unittest.main()
