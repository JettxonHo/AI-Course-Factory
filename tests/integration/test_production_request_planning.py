"""Offline integration evidence for Production Request Candidate Commit."""

import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    ProductionAgent,
    ProductionAgentFailure,
    ProductionRequestModelRuntimeResult,
)
from ai_course_factory.artifacts import (
    ArtifactNotFoundError,
    ArtifactReference,
    CommitConflictError,
    StoryboardDecisionBoundary,
    StoryboardDecisionRecord,
)

from tests.agents.test_production_request_planning import DeterministicRequestRuntime
from tests.agents.test_production_agent import approved_script, character_result


def committed_upstreams():
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
    assert isinstance(storyboard_decision, StoryboardDecisionRecord)
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


def request_candidate(inputs):
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
    assert not isinstance(candidate, ProductionAgentFailure)
    return candidate


class ProductionRequestPlanningIntegrationTests(unittest.TestCase):
    def test_candidate_commits_with_exact_lineage_replays_and_conflicts(self):
        inputs = committed_upstreams()
        boundary = inputs[0]
        script_reference, script_decision = inputs[2], inputs[4]
        character_reference, storyboard_reference = inputs[5], inputs[7]
        timeline_reference, runtime = inputs[10], inputs[1]
        candidate = request_candidate(inputs)

        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("production_request", candidate.identity, 1))
        first_reference = boundary.commit(candidate)
        committed = boundary.get(first_reference)
        self.assertEqual(first_reference.artifact_type, "production_request")
        self.assertEqual(
            committed.dependencies,
            (script_reference, character_reference, storyboard_reference, timeline_reference),
        )
        self.assertEqual(committed.payload["approval_decision_id"], script_decision.decision_id)
        self.assertEqual(committed.provenance[0]["purpose"], "production_request_planning")
        self.assertEqual(committed.provenance[0]["timeline_reference"], timeline_reference)
        self.assertEqual(
            boundary.commit(replace(candidate, payload=dict(candidate.payload))),
            first_reference,
        )

        production_request = dict(candidate.payload["production_request"])
        scenes = list(production_request["scenes"])
        scenes[0] = {**scenes[0], "narration": scenes[0]["narration"] + "。"}
        conflicting = replace(
            candidate,
            payload={
                **candidate.payload,
                "production_request": {
                    **production_request,
                    "scenes": tuple(scenes),
                },
            },
        )
        with self.assertRaises(CommitConflictError):
            boundary.commit(conflicting)
        self.assertEqual(boundary.get(first_reference), committed)
        self.assertEqual(
            len([request for request in runtime.requests if request.purpose == "production_request_planning"]),
            1,
        )

    def test_malformed_request_is_not_committed_or_retrievable(self):
        inputs = committed_upstreams()
        boundary, runtime = inputs[0], inputs[1]
        valid = request_candidate(inputs)
        malformed = ProductionRequestModelRuntimeResult(
            production_request={
                **valid.payload["production_request"],
                "scenes": list(valid.payload["production_request"]["scenes"]),
            }
        )
        runtime.production_response = malformed
        (
            _boundary,
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
        result = ProductionAgent(runtime).plan_request(
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
            request_identity="production-request:malformed",
            request_commit_id="production-request-malformed",
        )
        self.assertIsInstance(result, ProductionAgentFailure)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("production_request", "production-request:malformed", 1))


if __name__ == "__main__":
    unittest.main()
