"""Public behavior tests for the staged Timeline Production Agent."""

import math
import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    ContentModelRuntimeResult,
    ModelRuntimeFailure,
    ModelRuntimeRequest,
    ProductionAgent,
    ProductionModelRuntimeResult,
    ProductionAgentFailure,
    StoryboardModelRuntimeResult,
    TimelineModelRuntimeResult,
)
from ai_course_factory.artifacts import (
    ArtifactReference,
    StoryboardDecisionBoundary,
    StoryboardDecisionRecord,
)

from tests.agents.test_production_agent import approved_script, character_result


class ControlledTimelineRuntime:
    def __init__(self, response):
        self.response = response
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def contiguous_timeline(script_version):
    start = 0.0
    scenes = []
    for scene in script_version.payload["scenes"]:
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
            "duration_seconds": script_version.payload["duration_seconds"],
            "scenes": tuple(scenes),
        }
    )


class TimelinePlanningTests(unittest.TestCase):
    def _committed_upstreams(self):
        boundary, script_reference, script_version, script_decision = approved_script()

        character_runtime = ControlledTimelineRuntime(
            ProductionModelRuntimeResult(character=character_result().character)
        )
        agent = ProductionAgent(character_runtime)
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

        scene_ids = tuple(scene["scene_id"] for scene in script_version.payload["scenes"])
        storyboard_runtime = ControlledTimelineRuntime(
            StoryboardModelRuntimeResult(
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
        )
        storyboard_candidate = ProductionAgent(storyboard_runtime).plan_storyboard(
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

        decision = StoryboardDecisionBoundary().decide(
            storyboard_reference,
            storyboard_version,
            review_enabled=True,
            decision_id="storyboard-approve-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(decision, StoryboardDecisionRecord)
        return (
            boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            decision,
        )

    def _plan(self, runtime=None):
        inputs = self._committed_upstreams()
        (
            _boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
        ) = inputs
        runtime = runtime or ControlledTimelineRuntime(contiguous_timeline(script_version))
        result = ProductionAgent(runtime).plan_timeline(
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
        return inputs, runtime, result

    def test_exact_approved_upstreams_produce_contiguous_timeline_candidate(self):
        (
            _boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
        ) = self._committed_upstreams()
        runtime = ControlledTimelineRuntime(contiguous_timeline(script_version))

        candidate = ProductionAgent(runtime).plan_timeline(
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

        self.assertEqual(candidate.artifact_type, "timeline")
        self.assertEqual(candidate.identity, "timeline:episode-1")
        self.assertEqual(candidate.commit_id, "timeline-commit-1")
        self.assertTrue(candidate.validated)
        self.assertIsNone(candidate.prior_reference)
        self.assertEqual(
            candidate.dependencies,
            (script_reference, character_reference, storyboard_reference),
        )
        self.assertEqual(candidate.payload["script_reference"], script_reference)
        self.assertEqual(candidate.payload["approval_decision_id"], script_decision.decision_id)
        self.assertEqual(candidate.payload["character_reference"], character_reference)
        self.assertEqual(candidate.payload["storyboard_reference"], storyboard_reference)
        self.assertEqual(
            candidate.payload["storyboard_decision_id"], storyboard_decision.decision_id
        )
        self.assertEqual(
            candidate.payload["timeline"]["duration_seconds"],
            script_version.payload["duration_seconds"],
        )
        self.assertEqual(
            tuple(scene["scene_id"] for scene in candidate.payload["timeline"]["scenes"]),
            tuple(scene["scene_id"] for scene in script_version.payload["scenes"]),
        )
        timeline_scenes = candidate.payload["timeline"]["scenes"]
        self.assertEqual(timeline_scenes[0]["start_seconds"], 0.0)
        for previous, current in zip(timeline_scenes, timeline_scenes[1:]):
            self.assertEqual(current["start_seconds"], previous["end_seconds"])
        for scene in timeline_scenes:
            self.assertEqual(
                scene["end_seconds"],
                scene["start_seconds"] + scene["duration_seconds"],
            )
        self.assertEqual(timeline_scenes[-1]["end_seconds"], 60.0)
        self.assertEqual(candidate.provenance[0]["purpose"], "timeline_planning")
        self.assertEqual(candidate.provenance[0]["storyboard_decision_id"], storyboard_decision.decision_id)

        self.assertEqual(len(runtime.requests), 1)
        request = runtime.requests[0]
        self.assertEqual(request.purpose, "timeline_planning")
        self.assertEqual(
            set(request.inputs),
            {
                "script_reference",
                "script_payload",
                "character_reference",
                "character_payload",
                "storyboard_reference",
                "storyboard_payload",
                "approval_decision_id",
                "storyboard_decision_id",
            },
        )
        self.assertEqual(request.constraints, {})

    def test_lineage_and_storyboard_gate_mutations_fail_before_runtime(self):
        (
            _boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
        ) = self._committed_upstreams()
        valid_response = contiguous_timeline(script_version)

        cases = (
            (
                "script version reference",
                replace(script_version, reference=replace(script_reference, version=2)),
                character_version,
                storyboard_version,
                storyboard_decision,
            ),
            (
                "character dependency",
                script_version,
                replace(character_version, dependencies=()),
                storyboard_version,
                storyboard_decision,
            ),
            (
                "storyboard dependency",
                script_version,
                character_version,
                replace(storyboard_version, dependencies=(character_reference, script_reference)),
                storyboard_decision,
            ),
            (
                "storyboard scene order",
                script_version,
                character_version,
                replace(
                    storyboard_version,
                    payload={
                        **storyboard_version.payload,
                        "storyboard": {
                            **storyboard_version.payload["storyboard"],
                            "scenes": storyboard_version.payload["storyboard"]["scenes"][::-1],
                        },
                    },
                ),
                storyboard_decision,
            ),
        )
        for label, changed_script, changed_character, changed_storyboard, changed_decision in cases:
            with self.subTest(label=label):
                runtime = ControlledTimelineRuntime(valid_response)
                result = ProductionAgent(runtime).plan_timeline(
                    script_reference,
                    changed_script,
                    script_decision,
                    character_reference,
                    changed_character,
                    storyboard_reference,
                    changed_storyboard,
                    changed_decision,
                    timeline_identity="timeline:invalid",
                    timeline_commit_id=f"timeline-invalid-{label}",
                )
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertEqual(result.kind, "validation")
                self.assertEqual(runtime.requests, [])

        decision_boundary = StoryboardDecisionBoundary()
        non_satisfying = (
            decision_boundary.decide(
                storyboard_reference,
                storyboard_version,
                review_enabled=True,
                decision_id="timeline-reject",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="reject",
                decision_context="Not approved.",
            ),
            decision_boundary.decide(
                storyboard_reference,
                storyboard_version,
                review_enabled=True,
                decision_id="timeline-revise",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="revise",
                decision_context="Revise the visual beat.",
            ),
            decision_boundary.decide(
                storyboard_reference,
                storyboard_version,
                review_enabled=True,
                decision_id="timeline-enabled-skip",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="approve",
            ),
            decision_boundary.decide(
                storyboard_reference,
                storyboard_version,
                review_enabled=False,
                decision_id="timeline-disabled-skip",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="skip",
            ),
        )
        # The first two are reject/revise records, the third is a satisfying
        # enabled approve and the fourth is a satisfying disabled skip.  Use
        # a deliberately malformed copy for the two opposite action/mode
        # combinations and assert they remain outside the runtime boundary.
        for decision in non_satisfying[:2]:
            self.assertIsInstance(decision, StoryboardDecisionRecord)
            runtime = ControlledTimelineRuntime(valid_response)
            result = ProductionAgent(runtime).plan_timeline(
                script_reference,
                script_version,
                script_decision,
                character_reference,
                character_version,
                storyboard_reference,
                storyboard_version,
                decision,
                timeline_identity="timeline:gate-invalid",
                timeline_commit_id=f"timeline-gate-{decision.decision_id}",
            )
            self.assertIsInstance(result, ProductionAgentFailure)
            self.assertEqual(runtime.requests, [])

        enabled_approve = non_satisfying[2]
        disabled_skip = non_satisfying[3]
        self.assertIsInstance(enabled_approve, StoryboardDecisionRecord)
        self.assertIsInstance(disabled_skip, StoryboardDecisionRecord)
        for changed in (
            replace(enabled_approve, action="skip"),
            replace(disabled_skip, action="approve", review_enabled=False),
            replace(storyboard_decision, storyboard_reference=replace(storyboard_reference, version=2)),
        ):
            runtime = ControlledTimelineRuntime(valid_response)
            result = ProductionAgent(runtime).plan_timeline(
                script_reference,
                script_version,
                script_decision,
                character_reference,
                character_version,
                storyboard_reference,
                storyboard_version,
                changed,
                timeline_identity="timeline:gate-invalid",
                timeline_commit_id=f"timeline-gate-{changed.decision_id}-{changed.action}",
            )
            self.assertIsInstance(result, ProductionAgentFailure)
            self.assertEqual(runtime.requests, [])

    def test_script_and_storyboard_mutations_fail_before_runtime(self):
        inputs = self._committed_upstreams()
        (
            _boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
        ) = inputs
        for changed_script in (
            replace(script_version, payload={**script_version.payload, "duration_seconds": 61}),
            replace(
                script_version,
                payload={
                    **script_version.payload,
                    "scenes": tuple(
                        {**scene, "duration_seconds": 9}
                        if index == 0
                        else scene
                        for index, scene in enumerate(script_version.payload["scenes"])
                    ),
                },
            ),
        ):
            runtime = ControlledTimelineRuntime(contiguous_timeline(script_version))
            result = ProductionAgent(runtime).plan_timeline(
                script_reference,
                changed_script,
                script_decision,
                character_reference,
                character_version,
                storyboard_reference,
                storyboard_version,
                storyboard_decision,
                timeline_identity="timeline:script-invalid",
                timeline_commit_id="timeline-script-invalid",
            )
            self.assertIsInstance(result, ProductionAgentFailure)
            self.assertEqual(runtime.requests, [])

    def test_non_exact_references_and_identity_aliases_fail_before_runtime(self):
        inputs = self._committed_upstreams()
        (
            _boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
        ) = inputs
        for reference_name, changed_reference in (
            ("script", ArtifactReference("script", "current", 1)),
            ("character", ArtifactReference("character", "latest", 1)),
            ("storyboard", ArtifactReference("storyboard", "current", 1)),
        ):
            runtime = ControlledTimelineRuntime(contiguous_timeline(script_version))
            result = ProductionAgent(runtime).plan_timeline(
                changed_reference if reference_name == "script" else script_reference,
                script_version,
                script_decision,
                changed_reference if reference_name == "character" else character_reference,
                character_version,
                changed_reference if reference_name == "storyboard" else storyboard_reference,
                storyboard_version,
                storyboard_decision,
                timeline_identity="timeline:exact",
                timeline_commit_id=f"timeline-exact-{reference_name}",
            )
            self.assertIsInstance(result, ProductionAgentFailure)
            self.assertEqual(runtime.requests, [])

        runtime = ControlledTimelineRuntime(contiguous_timeline(script_version))
        result = ProductionAgent(runtime).plan_timeline(
            script_reference,
            script_version,
            replace(script_decision, decision_id="current"),
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            timeline_identity="timeline:exact",
            timeline_commit_id="timeline-exact-script-decision",
        )
        self.assertIsInstance(result, ProductionAgentFailure)
        self.assertEqual(runtime.requests, [])

    def test_timeline_runtime_result_is_strictly_normalized(self):
        inputs = self._committed_upstreams()
        script_version = inputs[2]
        base = contiguous_timeline(script_version).timeline
        base_scenes = base["scenes"]
        malformed = (
            ContentModelRuntimeResult(content={"timeline": {}}),
            TimelineModelRuntimeResult(timeline={**base, "extra": "forbidden"}),
            TimelineModelRuntimeResult(timeline={"duration_seconds": 60}),
            TimelineModelRuntimeResult(timeline={**base, "scenes": list(base_scenes)}),
            TimelineModelRuntimeResult(
                timeline={
                    **base,
                    "scenes": tuple({**scene, "extra": "forbidden"} for scene in base_scenes),
                }
            ),
            TimelineModelRuntimeResult(
                timeline={
                    **base,
                    "scenes": tuple(
                        {**scene, "scene_id": "foreign"} if index == 0 else scene
                        for index, scene in enumerate(base_scenes)
                    ),
                }
            ),
            TimelineModelRuntimeResult(
                timeline={
                    **base,
                    "scenes": tuple(
                        {**scene, "start_seconds": scene["start_seconds"] + 1}
                        if index == 1
                        else scene
                        for index, scene in enumerate(base_scenes)
                    ),
                }
            ),
            TimelineModelRuntimeResult(
                timeline={
                    **base,
                    "scenes": tuple(
                        {**scene, "duration_seconds": scene["duration_seconds"] + 1}
                        if index == 2
                        else scene
                        for index, scene in enumerate(base_scenes)
                    ),
                }
            ),
            TimelineModelRuntimeResult(
                timeline={
                    **base,
                    "duration_seconds": math.inf,
                }
            ),
            TimelineModelRuntimeResult(
                timeline={
                    **base,
                    "scenes": tuple(
                        {**scene, "start_seconds": math.nan} if index == 0 else scene
                        for index, scene in enumerate(base_scenes)
                    ),
                }
            ),
            TimelineModelRuntimeResult(
                timeline={
                    **base,
                    "scenes": (
                        *base_scenes[:-1],
                        {
                            **base_scenes[-1],
                            "end_seconds": base_scenes[-1]["end_seconds"] + 1,
                        },
                    ),
                }
            ),
            TimelineModelRuntimeResult(timeline=base, diagnostics=["malformed"]),
            TimelineModelRuntimeResult(timeline=base, diagnostics=("\n",)),
            ModelRuntimeFailure("execution", "MODEL_RUNTIME_FAILED", "secret detail"),
            RuntimeError("secret detail"),
        )
        for index, response in enumerate(malformed):
            with self.subTest(index=index):
                runtime = ControlledTimelineRuntime(response)
                _inputs, _runtime, result = self._plan(runtime)
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertNotIn("secret detail", result.message)
                self.assertEqual(len(runtime.requests), 1)
                if isinstance(response, RuntimeError):
                    self.assertEqual(result.kind, "execution")
                    self.assertEqual(result.code, "MODEL_RUNTIME_FAILED")


if __name__ == "__main__":
    unittest.main()
