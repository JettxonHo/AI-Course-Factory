"""Offline integration evidence for Storyboard Candidate -> decision."""

import unittest

from ai_course_factory.agents import (
    ProductionAgent,
    StoryboardModelRuntimeResult,
)
from ai_course_factory.artifacts import (
    ArtifactCommitBoundary,
    StoryboardDecisionBoundary,
    StoryboardDecisionRecord,
)

from tests.agents.test_production_agent import approved_script, character_result


class DeterministicPlanningRuntime:
    def __init__(self) -> None:
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        if request.purpose == "character_planning":
            return character_result()
        scene_ids = tuple(
            scene["scene_id"] for scene in request.inputs["script_payload"]["scenes"]
        )
        return StoryboardModelRuntimeResult(
            storyboard={
                "aspect_ratio": "9:16",
                "scenes": tuple(
                    {
                        "scene_id": scene_id,
                        "visual_intent": f"Visual beat for {scene_id}.",
                        "character_action": f"小土豆 acts in {scene_id}.",
                        "continuity_notes": ("keep the blue scarf visible",),
                    }
                    for scene_id in scene_ids
                ),
            }
        )


class StoryboardDecisionIntegrationTests(unittest.TestCase):
    def _committed_storyboard(self):
        artifact_boundary, script_reference, script_version, script_decision = approved_script()
        runtime = DeterministicPlanningRuntime()
        agent = ProductionAgent(runtime)
        character_candidate = agent.plan_character(
            script_reference,
            script_version,
            script_decision,
            constraints={"name": "小土豆", "design_version": "v1.0"},
            character_identity="character:小土豆:v1",
            character_commit_id="character-commit-1",
        )
        character_reference = artifact_boundary.commit(character_candidate)
        character_version = artifact_boundary.get(character_reference)
        storyboard_candidate = agent.plan_storyboard(
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            constraints={"aspect_ratio": "9:16"},
            storyboard_identity="storyboard:episode-1",
            storyboard_commit_id="storyboard-commit-1",
        )
        storyboard_reference = artifact_boundary.commit(storyboard_candidate)
        storyboard_version = artifact_boundary.get(storyboard_reference)
        return (
            artifact_boundary,
            script_reference,
            script_decision,
            character_reference,
            storyboard_reference,
            storyboard_version,
            runtime,
        )

    def test_committed_storyboard_reaches_enabled_and_disabled_decisions(self):
        (
            _artifact_boundary,
            script_reference,
            script_decision,
            character_reference,
            storyboard_reference,
            storyboard_version,
            runtime,
        ) = self._committed_storyboard()
        self.assertEqual([request.purpose for request in runtime.requests], [
            "character_planning",
            "storyboard_planning",
        ])

        boundary = StoryboardDecisionBoundary()
        approved = boundary.decide(
            storyboard_reference,
            storyboard_version,
            review_enabled=True,
            decision_id="storyboard-approve-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(approved, StoryboardDecisionRecord)
        self.assertEqual(approved.storyboard_reference, storyboard_reference)
        self.assertEqual(approved.script_reference, script_reference)
        self.assertEqual(approved.character_reference, character_reference)
        self.assertEqual(approved.script_approval_decision_id, script_decision.decision_id)
        self.assertIs(approved.review_enabled, True)

        skipped = boundary.decide(
            storyboard_reference,
            storyboard_version,
            review_enabled=False,
            decision_id="storyboard-skip-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="skip",
        )
        self.assertIsInstance(skipped, StoryboardDecisionRecord)
        self.assertEqual(skipped.storyboard_reference, storyboard_reference)
        self.assertEqual(skipped.script_reference, script_reference)
        self.assertEqual(skipped.character_reference, character_reference)
        self.assertEqual(skipped.script_approval_decision_id, script_decision.decision_id)
        self.assertIs(skipped.review_enabled, False)


if __name__ == "__main__":
    unittest.main()
