"""Public contract tests for the Mandatory Final Video Review seam."""

from __future__ import annotations

import unittest
from dataclasses import fields, replace
from types import MappingProxyType

from ai_course_factory.artifacts import (
    ArtifactReference,
    ArtifactVersion,
    FinalVideoDecisionBoundary,
    FinalVideoDecisionFailure,
    FinalVideoDecisionRecord,
    FinalVideoGateAssessment,
    FinalVideoGateFinding,
)


def valid_video_version() -> tuple[ArtifactReference, ArtifactVersion]:
    request = ArtifactReference("production_request", "request:episode-1", 1)
    timeline = ArtifactReference("timeline", "timeline:episode-1", 1)
    clip_one = ArtifactReference("scene_clip", "media:episode-1:scene-1", 1)
    clip_two = ArtifactReference("scene_clip", "media:episode-1:scene-2", 1)
    subtitle = ArtifactReference("subtitle", "media:episode-1", 1)
    master_audio = ArtifactReference("master_audio", "media:episode-1", 1)
    video = ArtifactReference("video", "media:episode-1", 1)
    payload = MappingProxyType(
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
    )
    version = ArtifactVersion(
        reference=video,
        payload=payload,
        provenance=(
            MappingProxyType(
                {
                    "purpose": "production_composition_video",
                    "production_request_reference": request,
                    "timeline_reference": timeline,
                    "composition_id": "composition:episode-1",
                }
            ),
        ),
        dependencies=(request, timeline, clip_one, clip_two, subtitle, master_audio),
        commit_id="composition-commit-1:video",
    )
    return video, version


class FinalVideoDecisionRepositoryContractTests(unittest.TestCase):
    def test_assess_exact_committed_video_passes(self):
        reference, version = valid_video_version()
        result = FinalVideoDecisionBoundary().assess(reference, version)
        self.assertIsInstance(result, FinalVideoGateAssessment)
        self.assertEqual(result.video_reference, reference)
        self.assertEqual(result.disposition, "pass")
        self.assertEqual(result.findings, ())

    def test_public_shapes_and_idempotent_creator_approval(self):
        reference, version = valid_video_version()
        boundary = FinalVideoDecisionBoundary()
        assessment = boundary.assess(reference, version)
        self.assertIsInstance(assessment, FinalVideoGateAssessment)
        self.assertEqual(
            tuple(field.name for field in fields(FinalVideoGateFinding)),
            ("code", "message"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(FinalVideoGateAssessment)),
            ("video_reference", "disposition", "findings"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(FinalVideoDecisionFailure)),
            ("kind", "code", "message"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(FinalVideoDecisionRecord)),
            (
                "decision_id",
                "task_id",
                "thread_id",
                "creator_id",
                "gate_kind",
                "video_reference",
                "assessment_disposition",
                "finding_codes",
                "action",
                "decision_context",
            ),
        )
        for record_type in (
            FinalVideoGateFinding,
            FinalVideoGateAssessment,
            FinalVideoDecisionFailure,
            FinalVideoDecisionRecord,
        ):
            self.assertTrue(record_type.__dataclass_params__.frozen)
            self.assertTrue(hasattr(record_type, "__slots__"))
        result = boundary.decide(
            assessment,
            decision_id="decision-final-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(result, FinalVideoDecisionRecord)
        self.assertEqual(result.gate_kind, "final_video_review")
        self.assertEqual(result.video_reference, reference)
        self.assertEqual(result.assessment_disposition, "pass")
        self.assertEqual(result.finding_codes, ())
        self.assertIs(boundary.get("decision-final-1"), result)
        self.assertIs(
            boundary.decide(
                assessment,
                decision_id="decision-final-1",
                task_id="task:episode-1",
                thread_id="thread:episode-1",
                creator_id="creator-1",
                action="approve",
            ),
            result,
        )
        conflict = boundary.decide(
            assessment,
            decision_id="decision-final-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            action="reject",
            decision_context="Reject this exact video.",
        )
        self.assertIsInstance(conflict, FinalVideoDecisionFailure)
        self.assertEqual(conflict.code, "DECISION_CONFLICT")
        with self.assertRaises((AttributeError, TypeError)):
            result.action = "reject"

    def test_hard_block_is_issued_for_lineage_and_media_mutations(self):
        reference, version = valid_video_version()
        payload = dict(version.payload)
        payload["media_type"] = "video/webm"
        payload["duration_milliseconds"] = 0
        payload["scene_clip_references"] = (version.payload["scene_clip_references"][1],) * 2
        mutated = replace(version, payload=MappingProxyType(payload), dependencies=())
        assessment = FinalVideoDecisionBoundary().assess(reference, mutated)
        self.assertIsInstance(assessment, FinalVideoGateAssessment)
        self.assertEqual(assessment.disposition, "hard_block")
        self.assertGreaterEqual(
            {finding.code for finding in assessment.findings},
            {"INVALID_VIDEO_MEDIA_TYPE", "INVALID_VIDEO_DURATION", "VIDEO_LINEAGE_MISMATCH"},
        )
        boundary = FinalVideoDecisionBoundary()
        issued = boundary.assess(reference, mutated)
        blocked = boundary.decide(
            issued,
            decision_id="decision-hard-block-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertEqual(blocked.code, "HARD_BLOCK_APPROVAL_FORBIDDEN")
        rejected = boundary.decide(
            issued,
            decision_id="decision-hard-block-2",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            action="reject",
            decision_context="Video output needs correction.",
        )
        self.assertIsInstance(rejected, FinalVideoDecisionRecord)

    def test_scene_clip_binding_mutation_blocks_approval_even_with_matching_dependencies(self):
        reference, version = valid_video_version()
        original_payload = version.payload
        original_clips = original_payload["scene_clip_references"]
        changed_clip = replace(original_clips[0], identity="media:other:scene-1")
        payload = MappingProxyType(
            {
                **original_payload,
                "scene_clip_references": (changed_clip, original_clips[1]),
            }
        )
        mutated = replace(
            version,
            payload=payload,
            dependencies=(
                original_payload["production_request_reference"],
                original_payload["timeline_reference"],
                changed_clip,
                original_clips[1],
                original_payload["subtitle_reference"],
                original_payload["master_audio_reference"],
            ),
        )
        boundary = FinalVideoDecisionBoundary()
        assessment = boundary.assess(reference, mutated)
        self.assertIsInstance(assessment, FinalVideoGateAssessment)
        self.assertEqual(assessment.disposition, "hard_block")
        self.assertIn("VIDEO_LINEAGE_MISMATCH", {finding.code for finding in assessment.findings})
        blocked = boundary.decide(
            assessment,
            decision_id="decision-binding-mutation-1",
            task_id="task:episode-1",
            thread_id="thread:episode-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(blocked, FinalVideoDecisionFailure)
        self.assertEqual(blocked.code, "HARD_BLOCK_APPROVAL_FORBIDDEN")

    def test_exact_immutable_envelope_mutations_fail_safely(self):
        reference, version = valid_video_version()
        boundary = FinalVideoDecisionBoundary()
        mutable = boundary.assess(reference, replace(version, payload=dict(version.payload)))
        self.assertIsInstance(mutable, FinalVideoDecisionFailure)
        self.assertEqual(mutable.code, "INVALID_VIDEO_VERSION")
        nonfinite = boundary.assess(
            reference,
            replace(version, provenance=(MappingProxyType({"score": float("nan")}),)),
        )
        self.assertIsInstance(nonfinite, FinalVideoDecisionFailure)
        self.assertEqual(nonfinite.code, "INVALID_VIDEO_VERSION")
        wrong_target = boundary.assess(
            replace(reference, artifact_type="production_request"), version
        )
        self.assertIsInstance(wrong_target, FinalVideoDecisionFailure)
        self.assertEqual(wrong_target.code, "INVALID_VIDEO_REFERENCE")
        forged = FinalVideoGateAssessment(reference, "pass", ())
        self.assertEqual(
            boundary.decide(
                forged,
                decision_id="decision-forged-1",
                task_id="task:episode-1",
                thread_id="thread:episode-1",
                creator_id="creator-1",
                action="approve",
            ).code,
            "ASSESSMENT_NOT_ISSUED",
        )
        issued = boundary.assess(reference, version)
        object.__setattr__(issued, "disposition", "hard_block")
        self.assertEqual(
            boundary.decide(
                issued,
                decision_id="decision-mutated-assessment",
                task_id="task:episode-1",
                thread_id="thread:episode-1",
                creator_id="creator-1",
                action="approve",
            ).code,
            "ASSESSMENT_NOT_ISSUED",
        )

    def test_reject_and_revise_require_bounded_context(self):
        reference, version = valid_video_version()
        boundary = FinalVideoDecisionBoundary()
        assessment = boundary.assess(reference, version)
        for action in ("reject", "revise"):
            result = boundary.decide(
                assessment,
                decision_id=f"decision-empty-{action}",
                task_id="task:episode-1",
                thread_id="thread:episode-1",
                creator_id="creator-1",
                action=action,
            )
            self.assertEqual(result.code, "INVALID_DECISION_CONTEXT")
        for index, context in enumerate((None, "\n", "x" * 4097)):
            result = boundary.decide(
                assessment,
                decision_id=f"decision-context-{index}",
                task_id="task:episode-1",
                thread_id="thread:episode-1",
                creator_id="creator-1",
                action="approve",
                decision_context=context,
            )
            self.assertEqual(result.code, "INVALID_DECISION_CONTEXT")


if __name__ == "__main__":
    unittest.main()
