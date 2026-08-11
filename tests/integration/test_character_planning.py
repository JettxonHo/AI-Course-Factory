"""Offline integration evidence for Character Candidate -> exact Reference."""

import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    ProductionAgent,
    ProductionAgentFailure,
    ProductionModelRuntimeResult,
)
from ai_course_factory.artifacts import (
    ArtifactNotFoundError,
    ArtifactReference,
    CommitConflictError,
)

from tests.agents.test_production_agent import approved_script


class DeterministicCharacterRuntime:
    def __init__(self, *, summary="A friendly potato teacher."):
        self.summary = summary
        self.requests = []

    def invoke(self, request):
        self.requests.append(request)
        return ProductionModelRuntimeResult(
            character={
                "name": "小土豆",
                "design_version": "v1.0",
                "summary": self.summary,
                "visual_traits": ("round potato silhouette", "blue scarf"),
                "personality_traits": ("curious", "encouraging"),
                "continuity_rules": ("keep the blue scarf visible",),
            }
        )


class CharacterPlanningIntegrationTests(unittest.TestCase):
    def _candidate(self, runtime=None):
        boundary, script_reference, script_version, decision = approved_script()
        runtime = runtime or DeterministicCharacterRuntime()
        candidate = ProductionAgent(runtime).plan_character(
            script_reference,
            script_version,
            decision,
            constraints={"name": "小土豆", "design_version": "v1.0"},
            character_identity="character:小土豆:v1",
            character_commit_id="character-commit-1",
        )
        return boundary, script_reference, runtime, candidate

    def test_candidate_commits_externally_with_exact_script_lineage(self):
        boundary, script_reference, runtime, candidate = self._candidate()
        self.assertEqual(len(runtime.requests), 1)

        character_reference = boundary.commit(candidate)
        self.assertEqual(character_reference.artifact_type, "character")
        self.assertEqual(character_reference.identity, "character:小土豆:v1")
        character_version = boundary.get(character_reference)
        self.assertEqual(character_version.dependencies, (script_reference,))
        self.assertEqual(character_version.payload["script_reference"], script_reference)
        self.assertEqual(character_version.payload["character"]["name"], "小土豆")
        self.assertEqual(character_version.provenance[0]["purpose"], "character_planning")
        self.assertEqual(
            character_version.provenance[0]["approval_decision_id"],
            "script-approval-1",
        )

    def test_equivalent_replay_is_idempotent_and_changed_input_conflicts(self):
        boundary, _, _, candidate = self._candidate()
        first_reference = boundary.commit(candidate)
        replay_reference = boundary.commit(replace(candidate, payload=dict(candidate.payload)))
        self.assertEqual(replay_reference, first_reference)

        changed_character = dict(candidate.payload["character"])
        changed_character["summary"] = "A changed character description."
        conflicting = replace(
            candidate,
            payload={**candidate.payload, "character": changed_character},
        )
        with self.assertRaises(CommitConflictError):
            boundary.commit(conflicting)
        self.assertEqual(boundary.get(first_reference).version, 1)

    def test_malformed_runtime_result_never_reaches_artifact_commit(self):
        runtime = DeterministicCharacterRuntime()
        original_invoke = runtime.invoke

        def malformed_invoke(request):
            original_invoke(request)
            return ProductionModelRuntimeResult(
                character={
                    "name": "小土豆",
                    "design_version": "v1.0",
                    "summary": "ok",
                    "visual_traits": ("same", "same"),
                    "personality_traits": ("curious",),
                    "continuity_rules": ("keep the scarf",),
                }
            )

        runtime.invoke = malformed_invoke
        boundary, _, _, candidate = self._candidate(runtime)
        self.assertIsInstance(candidate, ProductionAgentFailure)
        self.assertEqual(candidate.kind, "validation")
        self.assertEqual(len(runtime.requests), 1)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("character", "character:小土豆:v1", 1))


if __name__ == "__main__":
    unittest.main()
