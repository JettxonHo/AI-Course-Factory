"""Public behavior tests for the staged Storyboard Production Agent."""

import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    ModelRuntimeFailure,
    ModelRuntimeRequest,
    ProductionAgent,
    ProductionAgentFailure,
    ProductionModelRuntimeResult,
    StoryboardModelRuntimeResult,
    StoryboardPlanningConstraints,
)

from tests.agents.test_production_agent import approved_script, character_result


def storyboard_result(scene_ids, **changes):
    scenes = tuple(
        {
            "scene_id": scene_id,
            "visual_intent": f"A provider-neutral visual beat for {scene_id}.",
            "character_action": f"小土豆 demonstrates {scene_id}.",
            "continuity_notes": ("keep the blue scarf visible",),
        }
        for scene_id in scene_ids
    )
    value = {"aspect_ratio": "9:16", "scenes": scenes}
    value.update(changes)
    return StoryboardModelRuntimeResult(storyboard=value)


class ControlledStoryboardRuntime:
    def __init__(self, response=None):
        self.response = response
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


class StoryboardPlanningTests(unittest.TestCase):
    def _inputs(self):
        boundary, script_reference, script_version, decision = approved_script()
        character_runtime = ControlledStoryboardRuntime(
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
        return (
            boundary,
            script_reference,
            script_version,
            decision,
            character_reference,
            character_version,
            scene_ids,
        )

    def _plan(self, runtime=None, **kwargs):
        inputs = self._inputs()
        (
            _boundary,
            script_reference,
            script_version,
            decision,
            character_reference,
            character_version,
            scene_ids,
        ) = inputs
        runtime = runtime or ControlledStoryboardRuntime(storyboard_result(scene_ids))
        candidate = ProductionAgent(runtime).plan_storyboard(
            script_reference,
            script_version,
            decision,
            character_reference,
            character_version,
            constraints=StoryboardPlanningConstraints("9:16"),
            storyboard_identity="storyboard:episode-1",
            storyboard_commit_id="storyboard-commit-1",
            **kwargs,
        )
        return inputs, runtime, candidate

    def test_exact_inputs_produce_ordered_provider_neutral_candidate(self):
        inputs, runtime, candidate = self._plan()
        (
            _boundary,
            script_reference,
            _script_version,
            decision,
            character_reference,
            _character_version,
            scene_ids,
        ) = inputs

        self.assertNotIsInstance(candidate, ProductionAgentFailure)
        self.assertEqual(candidate.artifact_type, "storyboard")
        self.assertEqual(candidate.identity, "storyboard:episode-1")
        self.assertEqual(candidate.commit_id, "storyboard-commit-1")
        self.assertTrue(candidate.validated)
        self.assertIsNone(candidate.prior_reference)
        self.assertEqual(candidate.dependencies, (script_reference, character_reference))
        self.assertEqual(candidate.payload["script_reference"], script_reference)
        self.assertEqual(candidate.payload["character_reference"], character_reference)
        self.assertEqual(candidate.payload["approval_decision_id"], decision.decision_id)
        self.assertEqual(candidate.payload["storyboard_constraints"]["aspect_ratio"], "9:16")
        self.assertEqual(
            tuple(scene["scene_id"] for scene in candidate.payload["storyboard"]["scenes"]),
            scene_ids,
        )
        self.assertEqual(candidate.provenance[0]["purpose"], "storyboard_planning")
        self.assertEqual(candidate.provenance[0]["script_reference"], script_reference)
        self.assertEqual(candidate.provenance[0]["character_reference"], character_reference)

        self.assertEqual(len(runtime.requests), 1)
        request = runtime.requests[0]
        self.assertEqual(request.purpose, "storyboard_planning")
        self.assertEqual(
            set(request.inputs),
            {
                "script_reference",
                "script_payload",
                "character_reference",
                "character_payload",
                "approval_decision_id",
            },
        )
        self.assertEqual(request.inputs["script_reference"], script_reference)
        self.assertEqual(request.inputs["character_reference"], character_reference)
        self.assertEqual(request.inputs["approval_decision_id"], decision.decision_id)
        self.assertEqual(set(request.constraints), {"storyboard_constraints"})
        self.assertEqual(request.constraints["storyboard_constraints"]["aspect_ratio"], "9:16")
        self.assertEqual(request.task_context, {})
        self.assertIsNone(request.source_record_reference)

    def test_exact_one_key_constraints_and_dynamic_scene_count(self):
        inputs = self._inputs()
        (
            _boundary,
            script_reference,
            script_version,
            decision,
            character_reference,
            character_version,
            _scene_ids,
        ) = inputs
        short_script = replace(
            script_version,
            payload={
                **script_version.payload,
                "scenes": script_version.payload["scenes"][:2],
            },
        )
        scene_ids = tuple(scene["scene_id"] for scene in short_script.payload["scenes"])
        for constraints in (
            {"aspect_ratio": "9:16"},
            StoryboardPlanningConstraints("9:16"),
        ):
            runtime = ControlledStoryboardRuntime(storyboard_result(scene_ids))
            result = ProductionAgent(runtime).plan_storyboard(
                script_reference,
                short_script,
                decision,
                character_reference,
                character_version,
                constraints=constraints,
                storyboard_identity="storyboard:short",
                storyboard_commit_id=f"storyboard-short-{type(constraints).__name__}",
            )
            self.assertNotIsInstance(result, ProductionAgentFailure)
            self.assertEqual(len(runtime.requests), 1)

        for invalid in (
            {"aspect_ratio": "9:16", "extra": "forbidden"},
            {"ratio": "9:16"},
            {"aspectRatio": "9:16"},
            {"aspect_ratio": {"nested": "forbidden"}},
        ):
            runtime = ControlledStoryboardRuntime(storyboard_result(scene_ids))
            result = ProductionAgent(runtime).plan_storyboard(
                script_reference,
                short_script,
                decision,
                character_reference,
                character_version,
                constraints=invalid,
                storyboard_identity="storyboard:short",
                storyboard_commit_id="storyboard-short-invalid",
            )
            self.assertIsInstance(result, ProductionAgentFailure)
            self.assertEqual(result.kind, "validation")
            self.assertEqual(runtime.requests, [])

    def test_character_lineage_and_approval_mutations_fail_before_runtime(self):
        inputs = self._inputs()
        (
            _boundary,
            script_reference,
            script_version,
            decision,
            character_reference,
            character_version,
            scene_ids,
        ) = inputs
        mutated_payload = {
            **character_version.payload,
            "script_reference": replace(script_reference, version=2),
        }
        cases = (
            (decision, replace(character_version, dependencies=())),
            (decision, replace(character_version, payload=mutated_payload)),
            (replace(decision, action="reject", decision_context="not approved"), character_version),
        )
        for changed_decision, changed_character in cases:
            runtime = ControlledStoryboardRuntime(storyboard_result(scene_ids))
            result = ProductionAgent(runtime).plan_storyboard(
                script_reference,
                script_version,
                changed_decision,
                character_reference,
                changed_character,
                constraints={"aspect_ratio": "9:16"},
                storyboard_identity="storyboard:invalid",
                storyboard_commit_id="storyboard-invalid",
            )
            self.assertIsInstance(result, ProductionAgentFailure)
            self.assertEqual(result.kind, "validation")
            self.assertEqual(runtime.requests, [])

    def test_scene_set_order_and_result_shape_fail_closed(self):
        inputs = self._inputs()
        scene_ids = inputs[-1]
        malformed = (
            storyboard_result(scene_ids, extra="forbidden"),
            storyboard_result(scene_ids, aspect_ratio="16:9"),
            storyboard_result(scene_ids[:-1]),
            storyboard_result((scene_ids[1], *scene_ids[2:], scene_ids[0])),
            storyboard_result(
                scene_ids,
                scenes=tuple(
                    {**scene, "continuity_notes": ("same", "same")}
                    for scene in storyboard_result(scene_ids).storyboard["scenes"]
                ),
            ),
            ProductionModelRuntimeResult(character={}),
            StoryboardModelRuntimeResult(storyboard={}, diagnostics=["bad"]),
        )
        for response in malformed:
            with self.subTest(response=response):
                runtime = ControlledStoryboardRuntime(response)
                _inputs_value, _runtime, result = self._plan(runtime)
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertNotIn("provider", result.message.casefold())
                self.assertEqual(len(runtime.requests), 1)

    def test_runtime_failures_are_safe(self):
        for response in (
            ModelRuntimeFailure("execution", "PROVIDER_TIMEOUT", "secret provider detail"),
            RuntimeError("secret provider detail"),
        ):
            runtime = ControlledStoryboardRuntime(response)
            _inputs_value, _runtime, result = self._plan(runtime)
            self.assertIsInstance(result, ProductionAgentFailure)
            self.assertEqual(result.kind, "execution")
            self.assertEqual(result.code, "MODEL_RUNTIME_FAILED")
            self.assertNotIn("secret provider detail", result.message)


if __name__ == "__main__":
    unittest.main()
