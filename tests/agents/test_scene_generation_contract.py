"""Public behavior tests for the provider-neutral Scene Generation Contract planner."""

from dataclasses import replace
import unittest

from ai_course_factory.agents import SceneGenerationContractFailure, SceneGenerationContractPlanner
from ai_course_factory.artifacts import ArtifactReference
from tests.agents import test_production_request_planning as production_request_test


class SceneGenerationContractPlanningTests(unittest.TestCase):
    def test_exact_approved_lineage_produces_six_ordered_provider_neutral_entries(self):
        inputs = production_request_test.ProductionRequestPlanningTests()._committed_upstreams()
        (
            boundary,
            _runtime,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            timeline_reference,
            timeline_version,
        ) = inputs
        request_candidate = production_request_test.ProductionRequestPlanningTests()._plan_request(inputs)
        request_reference = boundary.commit(request_candidate)
        request_version = boundary.get(request_reference)

        candidate = SceneGenerationContractPlanner().plan(
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            timeline_reference,
            timeline_version,
            request_reference,
            request_version,
            contract_identity="scene-generation-contract:episode-1",
            contract_commit_id="scene-generation-contract-commit-1",
        )

        self.assertEqual(candidate.artifact_type, "scene_generation_contract")
        self.assertEqual(candidate.identity, "scene-generation-contract:episode-1")
        self.assertTrue(candidate.validated)
        self.assertEqual(
            candidate.dependencies,
            (
                script_reference,
                character_reference,
                storyboard_reference,
                timeline_reference,
                request_reference,
            ),
        )
        payload = candidate.payload
        self.assertEqual(payload["script_reference"], script_reference)
        self.assertEqual(payload["character_reference"], character_reference)
        self.assertEqual(payload["storyboard_reference"], storyboard_reference)
        self.assertEqual(payload["timeline_reference"], timeline_reference)
        self.assertEqual(payload["production_request_reference"], request_reference)
        self.assertEqual(payload["approval_decision_id"], script_decision.decision_id)
        self.assertEqual(payload["storyboard_decision_id"], storyboard_decision.decision_id)
        entries = payload["scene_generation_contract"]["scenes"]
        self.assertEqual(len(entries), 6)
        self.assertEqual(tuple(entry["scene_id"] for entry in entries), tuple(f"scene-{i}" for i in range(6)))
        for index, entry in enumerate(entries, start=1):
            self.assertEqual(
                set(entry),
                {
                    "scene_id",
                    "duration_milliseconds",
                    "narration_identity",
                    "narration",
                    "visual_intent",
                    "character_action",
                    "continuity_notes",
                    "generation_prompt",
                    "camera_motion_instruction",
                    "negative_constraints",
                    "expected_filename",
                },
            )
            self.assertEqual(entry["expected_filename"], f"scene-{index}.mp4")
            self.assertIsInstance(entry["duration_milliseconds"], int)
            self.assertGreater(entry["duration_milliseconds"], 0)
            self.assertEqual(entry["narration_identity"], f"narration:{entry['scene_id']}")
            self.assertNotIn("provider", entry)
            self.assertNotIn("model", entry)
            self.assertNotIn("price", entry)
        self.assertEqual(candidate.provenance[0]["script_approval_decision_id"], script_decision.decision_id)
        self.assertEqual(candidate.provenance[0]["storyboard_approval_decision_id"], storyboard_decision.decision_id)

    def test_foreign_storyboard_decision_fails_safely_without_a_contract_candidate(self):
        inputs = production_request_test.ProductionRequestPlanningTests()._committed_upstreams()
        (
            boundary,
            _runtime,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            timeline_reference,
            timeline_version,
        ) = inputs
        request_candidate = production_request_test.ProductionRequestPlanningTests()._plan_request(inputs)
        request_reference = boundary.commit(request_candidate)
        request_version = boundary.get(request_reference)
        foreign_decision = replace(
            storyboard_decision,
            script_reference=ArtifactReference("script", "foreign-script", 1),
        )

        failure = SceneGenerationContractPlanner().plan(
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            foreign_decision,
            timeline_reference,
            timeline_version,
            request_reference,
            request_version,
            contract_identity="scene-generation-contract:foreign",
            contract_commit_id="scene-generation-contract-foreign",
        )

        self.assertIsInstance(failure, SceneGenerationContractFailure)
        self.assertEqual(failure.kind, "validation")
        self.assertEqual(failure.code, "STORYBOARD_APPROVAL_REQUIRED")
        self.assertEqual(failure.message, "an exact approved Storyboard decision is required")


if __name__ == "__main__":
    unittest.main()
