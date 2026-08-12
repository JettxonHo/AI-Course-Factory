"""Public behavior tests for provider-neutral Production Request planning."""

import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    ModelRuntimeFailure,
    ModelRuntimeRequest,
    ProductionAgent,
    ProductionAgentFailure,
    ProductionModelRuntimeResult,
    ProductionRequestModelRuntimeResult,
    StoryboardModelRuntimeResult,
    TimelineModelRuntimeResult,
)
from ai_course_factory.artifacts import ArtifactReference, StoryboardDecisionBoundary, StoryboardDecisionRecord

from tests.agents.test_production_agent import approved_script, character_result


class DeterministicRequestRuntime:
    def __init__(self, production_response=None):
        self.requests: list[ModelRuntimeRequest] = []
        self.production_response = production_response

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        if request.purpose == "character_planning":
            return character_result()
        if request.purpose == "storyboard_planning":
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
        if request.purpose == "timeline_planning":
            start = 0.0
            scenes = []
            for scene in request.inputs["script_payload"]["scenes"]:
                duration = scene["duration_seconds"]
                end = start + duration
                scenes.append(
                    {
                        "scene_id": scene["scene_id"],
                        "start_seconds": start,
                        "duration_seconds": duration,
                        "end_seconds": end,
                    }
                )
                start = end
            return TimelineModelRuntimeResult(
                timeline={
                    "duration_seconds": request.inputs["script_payload"]["duration_seconds"],
                    "scenes": tuple(scenes),
                }
            )
        if isinstance(self.production_response, BaseException):
            raise self.production_response
        if self.production_response is not None:
            return self.production_response
        scene_lookup = {
            scene["scene_id"]: scene
            for scene in request.inputs["storyboard_payload"]["storyboard"]["scenes"]
        }
        production_scenes = []
        for timeline_scene, script_scene in zip(
            request.inputs["timeline_payload"]["timeline"]["scenes"],
            request.inputs["script_payload"]["scenes"],
        ):
            storyboard_scene = scene_lookup[timeline_scene["scene_id"]]
            production_scenes.append(
                {
                    **timeline_scene,
                    "narration": script_scene["narration"],
                    "visual_intent": storyboard_scene["visual_intent"],
                    "character_action": storyboard_scene["character_action"],
                    "continuity_notes": storyboard_scene["continuity_notes"],
                }
            )
        return ProductionRequestModelRuntimeResult(
            production_request={
                "language": request.inputs["script_payload"]["language"],
                "aspect_ratio": request.inputs["script_payload"]["aspect_ratio"],
                "duration_seconds": request.inputs["timeline_payload"]["timeline"]["duration_seconds"],
                "scenes": tuple(production_scenes),
            }
        )


class ProductionRequestPlanningTests(unittest.TestCase):
    def _committed_upstreams(self):
        boundary, script_reference, script_version, script_decision = approved_script()
        runtime = DeterministicRequestRuntime()
        agent = ProductionAgent(runtime)
        character_candidate = agent.plan_character(
            script_reference,
            script_version,
            script_decision,
            constraints={"name": "小土豆", "design_version": "v1.0"},
            character_identity="character:小土豆:v1",
            character_commit_id="character-commit-1",
        )
        character_reference = boundary.commit(character_candidate)
        character_version = boundary.get(character_reference)
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
        storyboard_reference = boundary.commit(storyboard_candidate)
        storyboard_version = boundary.get(storyboard_reference)
        storyboard_decision = StoryboardDecisionBoundary().decide(
            storyboard_reference,
            storyboard_version,
            review_enabled=True,
            decision_id="storyboard-approve-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(storyboard_decision, StoryboardDecisionRecord)
        timeline_candidate = agent.plan_timeline(
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            timeline_identity="timeline:episode-1",
            timeline_commit_id="timeline-commit-1",
        )
        timeline_reference = boundary.commit(timeline_candidate)
        timeline_version = boundary.get(timeline_reference)
        return (
            boundary,
            runtime,
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
        )

    def _plan_request(self, inputs, *, runtime=None, **kwargs):
        (
            _boundary,
            default_runtime,
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
        runtime = runtime or default_runtime
        return ProductionAgent(runtime).plan_request(
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
            request_identity=kwargs.pop("request_identity", "production-request:episode-1"),
            request_commit_id=kwargs.pop("request_commit_id", "production-request-commit-1"),
            **kwargs,
        )

    def test_exact_committed_lineage_produces_provider_neutral_request_candidate(self):
        (
            _boundary,
            runtime,
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
        ) = self._committed_upstreams()

        candidate = ProductionAgent(runtime).plan_request(
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
            request_identity="production-request:episode-1",
            request_commit_id="production-request-commit-1",
        )

        self.assertEqual(candidate.artifact_type, "production_request")
        self.assertEqual(candidate.identity, "production-request:episode-1")
        self.assertEqual(candidate.commit_id, "production-request-commit-1")
        self.assertTrue(candidate.validated)
        self.assertIsNone(candidate.prior_reference)
        self.assertEqual(
            candidate.dependencies,
            (script_reference, character_reference, storyboard_reference, timeline_reference),
        )
        self.assertEqual(
            set(candidate.payload),
            {
                "script_reference",
                "approval_decision_id",
                "character_reference",
                "storyboard_reference",
                "storyboard_decision_id",
                "timeline_reference",
                "production_request",
            },
        )
        production_request = candidate.payload["production_request"]
        self.assertEqual(set(production_request), {"language", "aspect_ratio", "duration_seconds", "scenes"})
        self.assertEqual(len(runtime.requests), 4)
        request = runtime.requests[-1]
        self.assertEqual(request.purpose, "production_request_planning")
        self.assertEqual(
            set(request.inputs),
            {
                "script_reference",
                "script_payload",
                "approval_decision_id",
                "character_reference",
                "character_payload",
                "storyboard_reference",
                "storyboard_payload",
                "storyboard_decision_id",
                "timeline_reference",
                "timeline_payload",
            },
        )
        self.assertEqual(request.constraints, {})

        self.assertEqual(
            production_request["scenes"][0]["narration"],
            script_version.payload["scenes"][0]["narration"],
        )
        self.assertEqual(
            production_request["scenes"][0]["visual_intent"],
            storyboard_version.payload["storyboard"]["scenes"][0]["visual_intent"],
        )

    def test_committed_timeline_lineage_and_timing_mutations_fail_before_request_runtime(self):
        inputs = self._committed_upstreams()
        (
            _boundary,
            runtime,
            script_reference,
            _script_version,
            _script_decision,
            character_reference,
            _character_version,
            storyboard_reference,
            _storyboard_version,
            _storyboard_decision,
            timeline_reference,
            timeline_version,
        ) = inputs
        payload = dict(timeline_version.payload)
        cases = (
            replace(
                timeline_version,
                payload={
                    **payload,
                    "script_reference": ArtifactReference("script", "foreign", 1),
                },
            ),
            replace(
                timeline_version,
                dependencies=(script_reference, storyboard_reference, character_reference),
            ),
            replace(timeline_version, reference=replace(timeline_reference, version=2)),
        )
        timeline_payload = dict(payload["timeline"])
        timeline_scenes = list(timeline_payload["scenes"])
        timeline_scenes[1] = {
            **timeline_scenes[1],
            "start_seconds": timeline_scenes[1]["start_seconds"] + 1,
        }
        cases += (
            replace(
                timeline_version,
                payload={
                    **payload,
                    "timeline": {
                        **timeline_payload,
                        "scenes": tuple(timeline_scenes),
                    },
                },
            ),
        )
        for index, changed_timeline in enumerate(cases):
            with self.subTest(index=index):
                result = self._plan_request(
                    (*inputs[:10], timeline_reference, changed_timeline),
                    request_identity=f"production-request:invalid-{index}",
                    request_commit_id=f"production-request-invalid-{index}",
                )
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertEqual(
                    [r for r in runtime.requests if r.purpose == "production_request_planning"],
                    [],
                )

        changed_script = replace(
            inputs[3],
            payload={
                **inputs[3].payload,
                "scenes": tuple(
                    {
                        **scene,
                        "narration": "\n",
                    }
                    if index == 0
                    else scene
                    for index, scene in enumerate(inputs[3].payload["scenes"])
                ),
            },
        )
        result = self._plan_request(
            (*inputs[:3], changed_script, *inputs[4:]),
            request_identity="production-request:invalid-script-narration",
            request_commit_id="production-request-invalid-script-narration",
        )
        self.assertIsInstance(result, ProductionAgentFailure)
        self.assertEqual(
            [r for r in runtime.requests if r.purpose == "production_request_planning"],
            [],
        )

    def test_gate_and_exact_reference_mutations_fail_before_request_runtime(self):
        inputs = self._committed_upstreams()
        (
            _boundary,
            runtime,
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
        invalid_decision = replace(storyboard_decision, action="reject", decision_context="Not approved.")
        invalid_cases = (
            {
                "script_decision": replace(script_decision, action="reject", decision_context="Not approved."),
            },
            {"storyboard_decision": invalid_decision},
            {"timeline_reference": ArtifactReference("timeline", "current", 1)},
            {"request_identity": "latest"},
        )
        for index, changes in enumerate(invalid_cases):
            with self.subTest(index=index):
                args = {
                    "script_reference": script_reference,
                    "resolved_script": script_version,
                    "script_decision": script_decision,
                    "character_reference": character_reference,
                    "resolved_character": character_version,
                    "storyboard_reference": storyboard_reference,
                    "resolved_storyboard": storyboard_version,
                    "storyboard_decision": storyboard_decision,
                    "timeline_reference": timeline_reference,
                    "resolved_timeline": timeline_version,
                }
                request_identity = changes.pop("request_identity", f"production-request:gate-{index}")
                args.update(changes)
                result = ProductionAgent(runtime).plan_request(
                    **args,
                    request_identity=request_identity,
                    request_commit_id=f"production-request-gate-{index}",
                )
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertEqual(
                    [r for r in runtime.requests if r.purpose == "production_request_planning"],
                    [],
                )

    def test_runtime_result_rejects_provider_fields_drift_wrong_collections_and_failures(self):
        baseline_inputs = self._committed_upstreams()
        baseline = self._plan_request(baseline_inputs)
        self.assertFalse(isinstance(baseline, ProductionAgentFailure))
        valid = baseline.payload["production_request"]
        malformed = (
            ProductionRequestModelRuntimeResult(
                production_request={**valid, "provider": "forbidden"}
            ),
            ProductionRequestModelRuntimeResult(
                production_request={
                    **valid,
                    "duration_seconds": valid["duration_seconds"] + 1,
                }
            ),
            ProductionRequestModelRuntimeResult(
                production_request={**valid, "scenes": list(valid["scenes"])}
            ),
            ProductionRequestModelRuntimeResult(
                production_request={
                    **valid,
                    "scenes": (
                        {**valid["scenes"][0], "prompt": "forbidden"},
                        *valid["scenes"][1:],
                    ),
                }
            ),
            ProductionRequestModelRuntimeResult(
                production_request={
                    **valid,
                    "scenes": (
                        {**valid["scenes"][0], "narration": "另一段合法旁白。"},
                        *valid["scenes"][1:],
                    ),
                }
            ),
            ProductionModelRuntimeResult(character={}),
            ProductionRequestModelRuntimeResult(
                production_request=valid, diagnostics=["malformed"]
            ),
            ProductionRequestModelRuntimeResult(
                production_request=valid, diagnostics=("\n",)
            ),
            ModelRuntimeFailure("execution", "MODEL_RUNTIME_FAILED", "secret detail"),
            RuntimeError("secret detail"),
        )
        for index, response in enumerate(malformed):
            with self.subTest(index=index):
                inputs = self._committed_upstreams()
                runtime = inputs[1]
                runtime.production_response = response
                result = self._plan_request(
                    inputs,
                    request_identity=f"production-request:malformed-{index}",
                    request_commit_id=f"production-request-malformed-{index}",
                )
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertNotIn("secret detail", result.message)
                self.assertEqual(
                    len([r for r in runtime.requests if r.purpose == "production_request_planning"]),
                    1,
                )


if __name__ == "__main__":
    unittest.main()
