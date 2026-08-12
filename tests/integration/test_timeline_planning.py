"""Offline integration evidence for Timeline Candidate -> exact Reference."""

import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    ModelRuntimeRequest,
    ProductionAgent,
    ProductionAgentFailure,
    ProductionModelRuntimeResult,
    StoryboardModelRuntimeResult,
    TimelineModelRuntimeResult,
)
from ai_course_factory.artifacts import (
    ArtifactNotFoundError,
    ArtifactReference,
    CommitConflictError,
    StoryboardDecisionBoundary,
    StoryboardDecisionRecord,
)

from tests.agents.test_production_agent import approved_script, character_result


def timeline_result(script_version, *, scene_changes=None):
    scene_changes = scene_changes or {}
    payload = getattr(script_version, "payload", script_version)
    start = 0.0
    scenes = []
    for index, scene in enumerate(payload["scenes"]):
        duration = scene["duration_seconds"]
        changed = {**scene_changes.get(index, {})}
        scene_id = changed.pop("scene_id", scene["scene_id"])
        start_seconds = changed.pop("start_seconds", start)
        duration_seconds = changed.pop("duration_seconds", duration)
        end_seconds = changed.pop("end_seconds", start_seconds + duration_seconds)
        scenes.append(
            {
                "scene_id": scene_id,
                "start_seconds": start_seconds,
                "duration_seconds": duration_seconds,
                "end_seconds": end_seconds,
            }
        )
        start = end_seconds
    return TimelineModelRuntimeResult(
        timeline={
            "duration_seconds": payload["duration_seconds"],
            "scenes": tuple(scenes),
        }
    )


class DeterministicTimelineRuntime:
    def __init__(self, *, timeline_response=None):
        self.timeline_response = timeline_response
        self.requests: list[ModelRuntimeRequest] = []

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
        if self.timeline_response is not None:
            return self.timeline_response
        return timeline_result(request.inputs["script_payload"])


class TimelinePlanningIntegrationTests(unittest.TestCase):
    def _committed_storyboard(self, *, timeline_response=None):
        artifact_boundary, script_reference, script_version, script_decision = approved_script()
        runtime = DeterministicTimelineRuntime(timeline_response=timeline_response)
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
        decision_boundary = StoryboardDecisionBoundary()
        storyboard_decision = decision_boundary.decide(
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
        return (
            artifact_boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            runtime,
        )

    def _timeline_candidate(self, *, timeline_response=None):
        inputs = self._committed_storyboard(timeline_response=timeline_response)
        (
            artifact_boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            storyboard_decision,
            runtime,
        ) = inputs
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
        return inputs, candidate

    def test_candidate_commits_externally_with_exact_lineage(self):
        inputs, candidate = self._timeline_candidate()
        (
            artifact_boundary,
            script_reference,
            _script_version,
            script_decision,
            character_reference,
            _character_version,
            storyboard_reference,
            _storyboard_version,
            storyboard_decision,
            runtime,
        ) = inputs
        self.assertEqual([request.purpose for request in runtime.requests], [
            "character_planning",
            "storyboard_planning",
            "timeline_planning",
        ])
        timeline_reference = artifact_boundary.commit(candidate)
        self.assertEqual(timeline_reference.artifact_type, "timeline")
        version = artifact_boundary.get(timeline_reference)
        self.assertEqual(version.payload["script_reference"], script_reference)
        self.assertEqual(version.payload["approval_decision_id"], script_decision.decision_id)
        self.assertEqual(version.payload["character_reference"], character_reference)
        self.assertEqual(version.payload["storyboard_reference"], storyboard_reference)
        self.assertEqual(
            version.payload["storyboard_decision_id"], storyboard_decision.decision_id
        )
        self.assertEqual(
            version.dependencies,
            (script_reference, character_reference, storyboard_reference),
        )
        self.assertEqual(version.provenance[0]["purpose"], "timeline_planning")
        self.assertEqual(version.provenance[0]["script_reference"], script_reference)
        self.assertEqual(version.provenance[0]["character_reference"], character_reference)
        self.assertEqual(version.provenance[0]["storyboard_reference"], storyboard_reference)
        self.assertEqual(
            version.provenance[0]["approval_decision_id"], script_decision.decision_id
        )
        self.assertEqual(
            version.provenance[0]["storyboard_decision_id"], storyboard_decision.decision_id
        )
        self.assertEqual(
            version.payload["timeline"]["duration_seconds"],
            60,
        )

    def test_disabled_storyboard_skip_reaches_timeline_without_bypassing_gate(self):
        inputs = self._committed_storyboard()
        (
            artifact_boundary,
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            _approved_decision,
            runtime,
        ) = inputs
        skipped = StoryboardDecisionBoundary().decide(
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
        candidate = ProductionAgent(runtime).plan_timeline(
            script_reference,
            script_version,
            script_decision,
            character_reference,
            character_version,
            storyboard_reference,
            storyboard_version,
            skipped,
            timeline_identity="timeline:episode-1-skip",
            timeline_commit_id="timeline-commit-skip-1",
        )
        self.assertNotIsInstance(candidate, ProductionAgentFailure)
        self.assertEqual(candidate.payload["storyboard_decision_id"], "storyboard-skip-1")
        self.assertEqual(
            artifact_boundary.commit(candidate).artifact_type,
            "timeline",
        )

    def test_equivalent_replay_is_idempotent_and_changed_input_conflicts(self):
        inputs, candidate = self._timeline_candidate()
        artifact_boundary = inputs[0]
        first_reference = artifact_boundary.commit(candidate)
        replay_reference = artifact_boundary.commit(
            replace(candidate, payload=dict(candidate.payload))
        )
        self.assertEqual(replay_reference, first_reference)

        changed_timeline = dict(candidate.payload["timeline"])
        changed_scenes = list(changed_timeline["scenes"])
        changed_scenes[0] = {
            **changed_scenes[0],
            "end_seconds": changed_scenes[0]["end_seconds"] + 1,
        }
        changed_timeline["scenes"] = tuple(changed_scenes)
        conflicting = replace(
            candidate,
            payload={**candidate.payload, "timeline": changed_timeline},
        )
        with self.assertRaises(CommitConflictError):
            artifact_boundary.commit(conflicting)
        self.assertEqual(artifact_boundary.get(first_reference).version, 1)

    def test_malformed_runtime_result_never_reaches_artifact_commit(self):
        malformed = timeline_result(
            approved_script()[2],
            scene_changes={1: {"start_seconds": 11}},
        )
        inputs, candidate = self._timeline_candidate(timeline_response=malformed)
        artifact_boundary = inputs[0]
        self.assertIsInstance(candidate, ProductionAgentFailure)
        self.assertEqual(candidate.kind, "validation")
        self.assertEqual(
            len([request for request in inputs[-1].requests if request.purpose == "timeline_planning"]),
            1,
        )
        with self.assertRaises(ArtifactNotFoundError):
            artifact_boundary.get(ArtifactReference("timeline", "timeline:episode-1", 1))


if __name__ == "__main__":
    unittest.main()
