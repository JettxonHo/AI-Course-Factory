"""Offline integration evidence for Storyboard Candidate -> exact Reference."""

import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    ProductionAgent,
    ProductionAgentFailure,
    ProductionModelRuntimeResult,
    StoryboardModelRuntimeResult,
)
from ai_course_factory.artifacts import ArtifactNotFoundError, ArtifactReference, CommitConflictError

from tests.agents.test_production_agent import approved_script, character_result


def valid_storyboard(scene_ids, *, summary="A deterministic storyboard."):
    return StoryboardModelRuntimeResult(
        storyboard={
            "aspect_ratio": "9:16",
            "scenes": tuple(
                {
                    "scene_id": scene_id,
                    "visual_intent": f"Visual beat for {scene_id}.",
                    "character_action": f"小土豆 acts in {scene_id}.",
                    "continuity_notes": (summary,),
                }
                for scene_id in scene_ids
            ),
        }
    )


class DeterministicStoryboardRuntime:
    def __init__(self, response):
        self.response = response
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        return self.response


class StoryboardPlanningIntegrationTests(unittest.TestCase):
    def _candidate(self, runtime=None):
        boundary, script_reference, script_version, decision = approved_script()
        character_runtime = DeterministicStoryboardRuntime(
            ProductionModelRuntimeResult(character=character_result().character)
        )
        character_candidate = ProductionAgent(character_runtime).plan_character(
            script_reference,
            script_version,
            decision,
            constraints={"name": "小土豆", "design_version": "v1.0"},
            character_identity="character:小土豆:v1",
            character_commit_id="character-commit-1",
        )
        character_reference = boundary.commit(character_candidate)
        character_version = boundary.get(character_reference)
        scene_ids = tuple(scene["scene_id"] for scene in script_version.payload["scenes"])
        runtime = runtime or DeterministicStoryboardRuntime(valid_storyboard(scene_ids))
        storyboard_candidate = ProductionAgent(runtime).plan_storyboard(
            script_reference,
            script_version,
            decision,
            character_reference,
            character_version,
            constraints={"aspect_ratio": "9:16"},
            storyboard_identity="storyboard:episode-1",
            storyboard_commit_id="storyboard-commit-1",
        )
        return (
            boundary,
            script_reference,
            character_reference,
            runtime,
            storyboard_candidate,
        )

    def test_candidate_commits_externally_with_exact_lineage(self):
        boundary, script_reference, character_reference, runtime, candidate = self._candidate()
        self.assertEqual(len(runtime.requests), 1)
        storyboard_reference = boundary.commit(candidate)
        self.assertEqual(storyboard_reference.artifact_type, "storyboard")
        version = boundary.get(storyboard_reference)
        self.assertEqual(version.payload["script_reference"], script_reference)
        self.assertEqual(version.payload["character_reference"], character_reference)
        self.assertEqual(version.dependencies, (script_reference, character_reference))
        self.assertTrue(version.payload["storyboard"]["scenes"])
        self.assertEqual(version.provenance[0]["purpose"], "storyboard_planning")

    def test_equivalent_replay_is_idempotent_and_changed_input_conflicts(self):
        boundary, _script_reference, _character_reference, _runtime, candidate = self._candidate()
        first_reference = boundary.commit(candidate)
        replay_reference = boundary.commit(replace(candidate, payload=dict(candidate.payload)))
        self.assertEqual(replay_reference, first_reference)

        changed = dict(candidate.payload["storyboard"])
        changed["scenes"] = tuple(
            {**scene, "visual_intent": "A changed visual beat."}
            for scene in changed["scenes"]
        )
        conflicting = replace(
            candidate,
            payload={**candidate.payload, "storyboard": changed},
        )
        with self.assertRaises(CommitConflictError):
            boundary.commit(conflicting)
        self.assertEqual(boundary.get(first_reference).version, 1)

    def test_malformed_runtime_result_never_reaches_artifact_commit(self):
        runtime = DeterministicStoryboardRuntime(
            StoryboardModelRuntimeResult(
                storyboard={
                    "aspect_ratio": "9:16",
                    "scenes": (
                        {
                            "scene_id": "scene-0",
                            "visual_intent": "ok",
                            "character_action": "ok",
                            "continuity_notes": ("same", "same"),
                        },
                    ),
                }
            )
        )
        boundary, _script_reference, _character_reference, _runtime, candidate = self._candidate(runtime)
        self.assertIsInstance(candidate, ProductionAgentFailure)
        self.assertEqual(candidate.kind, "validation")
        self.assertEqual(len(runtime.requests), 1)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("storyboard", "storyboard:episode-1", 1))


if __name__ == "__main__":
    unittest.main()
