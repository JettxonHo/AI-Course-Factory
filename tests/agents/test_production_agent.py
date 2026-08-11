"""Public behavior tests for the staged Character Production Agent."""

import unittest
from dataclasses import replace

from ai_course_factory.agents import (
    CharacterPlanningConstraints,
    ContentModelRuntimeResult,
    ModelRuntimeFailure,
    ModelRuntimeRequest,
    ProductionAgent,
    ProductionAgentFailure,
    ProductionModelRuntimeResult,
)
from ai_course_factory.artifacts import ScriptDecisionBoundary, ScriptDecisionRecord

from tests.artifacts.test_script_decision import valid_versions


def approved_script():
    values = valid_versions()
    (
        boundary,
        knowledge_reference,
        knowledge_version,
        course_reference,
        course_version,
        episode_reference,
        episode_version,
        script_reference,
        script_version,
    ) = values
    decision_boundary = ScriptDecisionBoundary()
    assessment = decision_boundary.assess(
        script_reference,
        script_version,
        knowledge_reference,
        knowledge_version,
        course_reference,
        course_version,
        episode_reference,
        episode_version,
    )
    decision = decision_boundary.decide(
        assessment,
        decision_id="script-approval-1",
        task_id="task-1",
        thread_id="thread-1",
        creator_id="creator-1",
        action="approve",
    )
    assert isinstance(decision, ScriptDecisionRecord)
    return boundary, script_reference, script_version, decision


def character_result(**changes):
    value = {
        "name": "小土豆",
        "design_version": "v1.0",
        "summary": "A friendly potato teacher for the fixed MVP episode.",
        "visual_traits": ("round potato silhouette", "blue scarf"),
        "personality_traits": ("curious", "encouraging"),
        "continuity_rules": ("keep the blue scarf visible", "keep the silhouette round"),
    }
    value.update(changes)
    return ProductionModelRuntimeResult(character=value)


class ControlledProductionRuntime:
    def __init__(self, response=None):
        self.response = response if response is not None else character_result()
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


class ProductionAgentTests(unittest.TestCase):
    def _plan(self, runtime, **kwargs):
        _, script_reference, script_version, decision = approved_script()
        return ProductionAgent(runtime).plan_character(
            script_reference,
            script_version,
            decision,
            constraints=CharacterPlanningConstraints("小土豆", "v1.0"),
            character_identity="character:小土豆:v1",
            character_commit_id="character-1",
            **kwargs,
        )

    def test_exact_approved_script_produces_provider_neutral_character_candidate(self):
        runtime = ControlledProductionRuntime()
        candidate = self._plan(runtime)

        self.assertEqual(candidate.artifact_type, "character")
        self.assertEqual(candidate.identity, "character:小土豆:v1")
        self.assertTrue(candidate.validated)
        self.assertIsNone(candidate.prior_reference)
        self.assertEqual(candidate.dependencies, (candidate.payload["script_reference"],))
        self.assertEqual(candidate.payload["approval_decision_id"], "script-approval-1")
        self.assertEqual(candidate.payload["character_constraints"]["name"], "小土豆")
        self.assertEqual(candidate.payload["character"]["design_version"], "v1.0")
        self.assertEqual(candidate.payload["character"]["visual_traits"], ("round potato silhouette", "blue scarf"))
        self.assertEqual(set(candidate.payload["character_constraints"]), {"name", "design_version"})
        self.assertEqual(candidate.provenance[0]["purpose"], "character_planning")

        self.assertEqual(len(runtime.requests), 1)
        request = runtime.requests[0]
        self.assertEqual(request.purpose, "character_planning")
        self.assertIsNone(request.source_record_reference)
        self.assertIsNone(request.source_record_payload)
        self.assertEqual(request.task_context, {})
        self.assertEqual(request.inputs["script_reference"], candidate.payload["script_reference"])
        self.assertEqual(request.inputs["approval_decision_id"], "script-approval-1")
        self.assertEqual(
            set(request.constraints["character_constraints"]), {"name", "design_version"}
        )

    def test_approval_mismatch_and_script_lineage_mutation_fail_before_runtime(self):
        boundary, script_reference, script_version, decision = approved_script()

        for label, changed_script, changed_decision in (
            (
                "reject",
                script_version,
                replace(decision, action="reject", decision_context="Not approved."),
            ),
            (
                "lineage",
                replace(
                    script_version,
                    dependencies=(
                        script_version.dependencies[1],
                        script_version.dependencies[0],
                        script_version.dependencies[2],
                    ),
                ),
                decision,
            ),
        ):
            with self.subTest(label=label):
                runtime = ControlledProductionRuntime()
                result = ProductionAgent(runtime).plan_character(
                    script_reference,
                    changed_script,
                    changed_decision,
                    constraints={"name": "小土豆", "design_version": "v1.0"},
                    character_identity="character:小土豆:v1",
                    character_commit_id="character-1",
                )
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertEqual(result.kind, "validation")
                self.assertEqual(runtime.requests, [])

    def test_runtime_result_is_strictly_normalized_and_failures_are_safe(self):
        malformed_results = (
            ContentModelRuntimeResult(content={"character": {}}),
            character_result(extra="unexpected"),
            character_result(name="another character"),
            character_result(visual_traits=("duplicate", "duplicate")),
            character_result(summary="x" * 4097),
        )
        for index, response in enumerate(malformed_results):
            with self.subTest(index=index):
                runtime = ControlledProductionRuntime(response)
                result = self._plan(runtime)
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertEqual(result.kind, "validation")
                self.assertEqual(len(runtime.requests), 1)

        for response in (
            ModelRuntimeFailure("execution", "PROVIDER_TIMEOUT", "provider secret detail"),
            RuntimeError("provider secret detail"),
        ):
            with self.subTest(response_type=type(response).__name__):
                runtime = ControlledProductionRuntime(response)
                result = self._plan(runtime)
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertEqual(result.kind, "execution")
                self.assertEqual(result.code, "MODEL_RUNTIME_FAILED")
                self.assertNotIn("provider secret detail", result.message)

    def test_invalid_exact_input_and_constraints_are_rejected_without_invocation(self):
        _, script_reference, script_version, decision = approved_script()
        invalid_cases = (
            (replace(script_reference, artifact_type="content_plan"), script_version, decision, {"name": "小土豆", "design_version": "v1.0"}),
            (script_reference, replace(script_version, reference=replace(script_reference, version=2)), decision, {"name": "小土豆", "design_version": "v1.0"}),
            (script_reference, script_version, decision, {"name": "小土豆"}),
            (script_reference, script_version, decision, {"name": "小土豆", "design_version": "v1.0", "extra": "forbidden"}),
        )
        for changed_reference, changed_version, changed_decision, constraints in invalid_cases:
            with self.subTest(changed_reference=changed_reference, constraints=constraints):
                runtime = ControlledProductionRuntime()
                result = ProductionAgent(runtime).plan_character(
                    changed_reference,
                    changed_version,
                    changed_decision,
                    constraints=constraints,
                    character_identity="character:小土豆:v1",
                    character_commit_id="character-1",
                )
                self.assertIsInstance(result, ProductionAgentFailure)
                self.assertEqual(result.kind, "validation")
                self.assertEqual(runtime.requests, [])


if __name__ == "__main__":
    unittest.main()
