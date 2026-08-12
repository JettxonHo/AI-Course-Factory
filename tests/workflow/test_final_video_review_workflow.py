"""Public contract tests for the mandatory Final Video Review workflow."""

from __future__ import annotations

import unittest
from dataclasses import fields
from pathlib import Path
import tempfile
from types import MappingProxyType

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    ArtifactReference,
    ArtifactVersion,
)
from ai_course_factory.workflow import (
    CheckpointStorageError,
    FinalVideoReviewCommand,
    FinalVideoReviewWorkflow,
    FinalVideoWorkflowResult,
    FinalVideoWorkflowSnapshot,
    InMemoryCheckpointAdapter,
    SQLiteCheckpointAdapter,
)


def commit_video(artifacts: ArtifactCommitBoundary) -> ArtifactReference:
    request = ArtifactReference("production_request", "request:episode-1", 1)
    timeline = ArtifactReference("timeline", "timeline:episode-1", 1)
    clip_one = ArtifactReference("scene_clip", "media:episode-1:scene-1", 1)
    clip_two = ArtifactReference("scene_clip", "media:episode-1:scene-2", 1)
    subtitle = ArtifactReference("subtitle", "media:episode-1", 1)
    master_audio = ArtifactReference("master_audio", "media:episode-1", 1)
    return artifacts.commit(
        ArtifactCandidate(
            artifact_type="video",
            identity="media:episode-1",
            payload=MappingProxyType(
                {
                    "production_request_reference": request,
                    "timeline_reference": timeline,
                    "composition_id": "composition:episode-1",
                    "scene_ids": ("scene-1", "scene-2"),
                    "scene_clip_references": (clip_one, clip_two),
                    "subtitle_reference": subtitle,
                    "master_audio_reference": master_audio,
                    "composer": "ffmpeg-composer-v1",
                    "output_reference": MappingProxyType(
                        {"task_id": "task:episode-1", "area": "media", "name": "composition.mp4"}
                    ),
                    "media_type": "video/mp4",
                    "duration_milliseconds": 60_000,
                }
            ),
            provenance=(),
            dependencies=(request, timeline, clip_one, clip_two, subtitle, master_audio),
            validated=True,
            commit_id="video-1",
        )
    )


def _seed_checkpoint(adapter, thread_id, values):
    versions = {key: index + 1 for index, key in enumerate(values)}
    adapter.saver.put(
        {"configurable": {"thread_id": thread_id, "checkpoint_ns": "final_video_review"}},
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


def _control_reference(reference):
    return {
        "artifact_type": reference.artifact_type,
        "identity": reference.identity,
        "version": reference.version,
    }


class AlwaysEqual(str):
    def __eq__(self, _other):
        return True


class ForgedReference(ArtifactReference):
    pass


class ForgedCommand(FinalVideoReviewCommand):
    pass


class ForgedVideoRepository:
    def __init__(self, version):
        self.version = version

    def get(self, _reference):
        return self.version


class FinalVideoReviewWorkflowTests(unittest.TestCase):
    def test_start_opens_namespaced_mandatory_final_video_gate(self):
        artifacts = ArtifactCommitBoundary()
        video_reference = commit_video(artifacts)

        result = FinalVideoReviewWorkflow(artifacts).start(
            task_id="task-1",
            thread_id="shared-thread",
            video_reference=video_reference,
        )

        self.assertEqual(result.status, "pending")
        self.assertEqual(result.snapshot.lifecycle_state, "final_review_pending")
        self.assertEqual(result.snapshot.current_stage, "final_video_review")
        self.assertEqual(result.snapshot.video_reference, video_reference)
        self.assertEqual(result.snapshot.pending_gate, "final_video_review")
        self.assertEqual(result.snapshot.allowed_actions, ("approve", "reject", "revise"))

    def test_terminal_resume_replay_and_conflict_preserve_exact_projection(self):
        artifacts = ArtifactCommitBoundary()
        reference = commit_video(artifacts)
        workflow = FinalVideoReviewWorkflow(artifacts)
        workflow.start("task-1", "thread-1", reference)
        command = FinalVideoReviewCommand("task-1", "thread-1", "command-1", "approve", reference)

        terminal = workflow.resume(command)
        self.assertEqual(terminal.status, "success")
        self.assertEqual(terminal.snapshot.lifecycle_state, "approved")
        self.assertEqual(workflow.resume(command), terminal)

        conflict = workflow.resume(
            FinalVideoReviewCommand("task-1", "thread-1", "command-1", "revise", reference)
        )
        self.assertEqual(conflict.error_code, "COMMAND_CONFLICT")
        self.assertEqual(workflow.snapshot("thread-1"), terminal.snapshot)

    def test_exact_command_and_reference_mutations_never_advance_checkpoint(self):
        artifacts = ArtifactCommitBoundary()
        reference = commit_video(artifacts)
        workflow = FinalVideoReviewWorkflow(artifacts)
        pending = workflow.start("task-1", "thread-mutation", reference)
        before = workflow.checkpoint_adapter.values("thread-mutation", "final_video_review")

        forged_command = ForgedCommand("task-1", "thread-mutation", "command-1", "approve", reference)
        rejected_subclass = workflow.resume(forged_command)
        self.assertEqual(rejected_subclass.error_code, "INVALID_COMMAND")

        mutated = FinalVideoReviewCommand("task-1", "thread-mutation", "command-1", "approve", reference)
        object.__setattr__(mutated, "video_reference", ArtifactReference("video", AlwaysEqual(reference.identity), reference.version))
        rejected_reference = workflow.resume(mutated)
        self.assertEqual(rejected_reference.error_code, "INVALID_VIDEO_REFERENCE")
        self.assertEqual(workflow.snapshot("thread-mutation"), pending.snapshot)
        self.assertEqual(workflow.checkpoint_adapter.values("thread-mutation", "final_video_review"), before)

    def test_repository_returned_forged_exact_version_fails_before_checkpoint(self):
        artifacts = ArtifactCommitBoundary()
        reference = commit_video(artifacts)
        original = artifacts.get(reference)
        forged_reference = ForgedReference("video", AlwaysEqual(reference.identity), reference.version)
        forged = ArtifactVersion(
            forged_reference,
            original.payload,
            original.provenance,
            original.dependencies,
            original.commit_id,
            original.prior_reference,
        )
        workflow = FinalVideoReviewWorkflow(ForgedVideoRepository(forged))
        result = workflow.start("task-1", "thread-forged", reference)
        self.assertEqual(result.error_code, "INVALID_VIDEO_VERSION")
        self.assertFalse(workflow.checkpoint_adapter.has_checkpoint("thread-forged", "final_video_review"))

    def test_reject_and_revise_are_terminal_revision_required(self):
        artifacts = ArtifactCommitBoundary()
        reference = commit_video(artifacts)
        for action, thread in (("reject", "thread-reject"), ("revise", "thread-revise")):
            with self.subTest(action=action):
                workflow = FinalVideoReviewWorkflow(artifacts)
                workflow.start("task-1", thread, reference)
                result = workflow.resume(FinalVideoReviewCommand("task-1", thread, f"{action}-1", action, reference))
                self.assertEqual(result.snapshot.lifecycle_state, "revision_required")

    def test_invalid_context_and_missing_video_fail_before_checkpoint_write(self):
        artifacts = ArtifactCommitBoundary()
        workflow = FinalVideoReviewWorkflow(artifacts)
        missing = ArtifactReference("video", "missing", 1)
        result = workflow.start("task-1", "thread-1", missing)
        self.assertEqual(result.error_code, "VIDEO_NOT_FOUND")
        with self.assertRaises(KeyError):
            workflow.snapshot("thread-1")

        invalid = workflow.start("task-1", "thread-2", ArtifactReference("script", "script-1", 1))
        self.assertEqual(invalid.error_code, "INVALID_VIDEO_REFERENCE")

    def test_public_records_are_frozen_and_slotted(self):
        expected_fields = {
            FinalVideoReviewCommand: ("task_id", "thread_id", "command_id", "action", "video_reference"),
            FinalVideoWorkflowSnapshot: (
                "task_id", "thread_id", "lifecycle_state", "current_stage", "video_reference",
                "pending_gate", "allowed_actions", "resume_position", "last_command_id",
            ),
            FinalVideoWorkflowResult: ("status", "snapshot", "error_code", "error_message"),
        }
        for record_type, names in expected_fields.items():
            self.assertEqual(tuple(field.name for field in fields(record_type)), names)
            self.assertTrue(record_type.__dataclass_params__.frozen)
            self.assertTrue(hasattr(record_type, "__slots__"))
        reference = ArtifactReference("video", "media:projection", 1)
        snapshot = FinalVideoWorkflowSnapshot(
            "task", "thread", "approved", "final_video_review", reference,
            None, (), "approved", "command-1",
        )
        result = FinalVideoWorkflowResult("success", snapshot=snapshot)
        self.assertEqual(result.lifecycle_state, "approved")
        self.assertEqual(result.current_stage, "final_video_review")
        self.assertEqual(result.video_reference, reference)
        self.assertIsNone(result.pending_gate)
        self.assertEqual(result.allowed_actions, ())
        self.assertEqual(result.resume_position, "approved")
        empty = FinalVideoWorkflowResult("failure")
        self.assertIsNone(empty.lifecycle_state)
        self.assertEqual(empty.allowed_actions, ())

    def test_sqlite_pending_and_terminal_survive_close_reopen(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workflow.sqlite3"
            artifacts = ArtifactCommitBoundary()
            reference = commit_video(artifacts)
            first_adapter = SQLiteCheckpointAdapter(database)
            try:
                first = FinalVideoReviewWorkflow(artifacts, first_adapter)
                pending = first.start("task-1", "thread-1", reference)
                self.assertEqual(pending.status, "pending")
                first_adapter.close()

                second_adapter = SQLiteCheckpointAdapter(database)
                second = FinalVideoReviewWorkflow(artifacts, second_adapter)
                command = FinalVideoReviewCommand("task-1", "thread-1", "command-1", "approve", reference)
                terminal = second.resume(command)
                self.assertEqual(terminal.snapshot.lifecycle_state, "approved")
                second_adapter.close()

                third_adapter = SQLiteCheckpointAdapter(database)
                try:
                    third = FinalVideoReviewWorkflow(artifacts, third_adapter)
                    self.assertEqual(third.snapshot("thread-1"), terminal.snapshot)
                    self.assertEqual(third.resume(command), terminal)
                finally:
                    third_adapter.close()
            finally:
                first_adapter.close()

    def test_malformed_checkpoint_is_safe_and_namespace_rejects_before_saver(self):
        class FailingSaver:
            def get_tuple(self, _config):
                raise AssertionError("saver must not be touched")

        adapter = InMemoryCheckpointAdapter(FailingSaver())
        with self.assertRaises(CheckpointStorageError):
            adapter.config("thread-1", "bad/namespace")

    def test_malformed_cross_thread_and_foreign_video_projection_is_safe_without_write(self):
        reference = ArtifactReference("video", "media:episode-1", 1)
        pending = {
            "task_id": "task-1",
            "thread_id": "thread-projection",
            "lifecycle_state": "final_review_pending",
            "current_stage": "final_video_review",
            "selected_video_ref": _control_reference(reference),
            "pending_gate": "final_video_review",
            "allowed_actions": ["approve", "reject", "revise"],
            "resume_position": "final_video_review_decision",
        }
        mutations = (
            ("malformed", {"allowed_actions": "approve"}),
            ("cross_thread", {"thread_id": "other-thread"}),
            ("foreign_video", {"selected_video_ref": {"artifact_type": "script", "identity": "script:foreign", "version": 1}}),
        )
        for name, mutation in mutations:
            with self.subTest(mutation=name):
                values = dict(pending)
                values.update(mutation)
                adapter = InMemoryCheckpointAdapter()
                _seed_checkpoint(adapter, "thread-projection", values)
                workflow = FinalVideoReviewWorkflow(ArtifactCommitBoundary(), adapter)
                before = adapter.values("thread-projection", "final_video_review")
                with self.assertRaises(CheckpointStorageError):
                    workflow.snapshot("thread-projection")
                result = workflow.start("task-1", "thread-projection", reference)
                self.assertEqual(result.status, "failure")
                self.assertEqual(adapter.values("thread-projection", "final_video_review"), before)


if __name__ == "__main__":
    unittest.main()
