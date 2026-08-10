"""Public behavior tests for deterministic Script Gate and Creator decisions."""

import unittest
from dataclasses import replace

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    ArtifactReference,
)
from ai_course_factory.artifacts.script_decision import (
    ScriptDecisionBoundary,
    ScriptGateAssessment,
    ScriptDecisionFailure,
    ScriptDecisionRecord,
)


def valid_versions():
    boundary = ArtifactCommitBoundary()
    knowledge_reference = boundary.commit(
        ArtifactCandidate(
            artifact_type="knowledge",
            identity="knowledge:episode-1",
            payload={
                "claims": (
                    {"claim_id": "claim-ai-tool", "statement": "AI is a tool."},
                    {"claim_id": "claim-not-magic", "statement": "AI is not magic."},
                )
            },
            provenance=("source-record:v1",),
            dependencies=(),
            validated=True,
            commit_id="knowledge-1",
        )
    )
    knowledge_version = boundary.get(knowledge_reference)
    course_reference = boundary.commit(
        ArtifactCandidate(
            artifact_type="content_plan",
            identity="course-plan:episode-1",
            payload={
                "role": "course",
                "knowledge_reference": knowledge_reference,
                "plan": {"knowledge_claim_ids": ("claim-ai-tool", "claim-not-magic")},
            },
            provenance=("knowledge:v1",),
            dependencies=(knowledge_reference,),
            validated=True,
            commit_id="course-plan-1",
        )
    )
    course_version = boundary.get(course_reference)
    episode_reference = boundary.commit(
        ArtifactCandidate(
            artifact_type="content_plan",
            identity="episode-plan:episode-1",
            payload={
                "role": "episode",
                "knowledge_reference": knowledge_reference,
                "plan": {"knowledge_claim_ids": ("claim-ai-tool", "claim-not-magic")},
            },
            provenance=("knowledge:v1",),
            dependencies=(knowledge_reference,),
            validated=True,
            commit_id="episode-plan-1",
        )
    )
    episode_version = boundary.get(episode_reference)
    script_reference = boundary.commit(
        ArtifactCandidate(
            artifact_type="script",
            identity="script:episode-1",
            payload={
                "knowledge_reference": knowledge_reference,
                "course_plan_reference": course_reference,
                "episode_plan_reference": episode_reference,
                "language": "Simplified Chinese",
                "template_constraint": {
                    "scene_count": 6,
                    "target_duration_seconds": 60,
                    "aspect_ratio": "9:16",
                },
                "duration_seconds": 60,
                "aspect_ratio": "9:16",
                "scenes": tuple(
                    {
                        "scene_id": f"scene-{index}",
                        "duration_seconds": 10,
                        "narration": f"第{index + 1}幕：人工智能是一种工具。",
                        "teaching_intent": f"解释第{index + 1}幕。",
                        "knowledge_claim_ids": (
                            "claim-ai-tool" if index % 2 == 0 else "claim-not-magic",
                        ),
                    }
                    for index in range(6)
                ),
            },
            provenance=("content-agent:v1",),
            dependencies=(knowledge_reference, course_reference, episode_reference),
            validated=True,
            commit_id="script-1",
        )
    )
    script_version = boundary.get(script_reference)
    return (
        boundary,
        knowledge_reference,
        knowledge_version,
        course_reference,
        course_version,
        episode_reference,
        episode_version,
        script_reference,
        script_version,
    )


def replace_scene(scene, **changes):
    return {**scene, **changes}


class ScriptDecisionBoundaryTests(unittest.TestCase):
    def _assess(self, values, decision_boundary=None):
        (
            _,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
            script_reference,
            script_version,
        ) = values
        boundary = decision_boundary or ScriptDecisionBoundary()
        return boundary.assess(
            script_reference,
            script_version,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
        )

    def test_valid_exact_lineage_produces_pass_assessment(self):
        (
            _,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
            script_reference,
            script_version,
        ) = valid_versions()

        assessment = ScriptDecisionBoundary().assess(
            script_reference,
            script_version,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
        )

        self.assertIsInstance(assessment, ScriptGateAssessment)
        self.assertEqual(assessment.disposition, "pass")
        self.assertEqual(assessment.script_reference, script_reference)
        self.assertEqual(assessment.knowledge_reference, knowledge_reference)
        self.assertEqual(assessment.course_plan_reference, course_reference)
        self.assertEqual(assessment.episode_plan_reference, episode_reference)
        self.assertEqual(assessment.findings, ())

    def test_foreign_claim_plan_lineage_format_language_and_scene_mutations_hard_block(self):
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
        cases = (
            (
                "UNTRACEABLE_SCENE",
                replace(
                    script_version,
                    payload={
                        **script_version.payload,
                        "scenes": (
                            replace_scene(script_version.payload["scenes"][0], knowledge_claim_ids=("foreign",)),
                            *script_version.payload["scenes"][1:],
                        ),
                    },
                ),
                script_version,
            ),
            (
                "SCRIPT_LINEAGE_MISMATCH",
                replace(
                    script_version,
                    dependencies=(course_reference, knowledge_reference, episode_reference),
                ),
                script_version,
            ),
            (
                "PLAN_KNOWLEDGE_MISMATCH",
                script_version,
                replace(
                    course_version,
                    payload={
                        **course_version.payload,
                        "knowledge_reference": ArtifactReference("knowledge", "other", 1),
                    },
                ),
            ),
            (
                "INVALID_SCRIPT_FORMAT",
                replace(
                    script_version,
                    payload={**script_version.payload, "aspect_ratio": "16:9"},
                ),
                script_version,
            ),
            (
                "INVALID_SCRIPT_LANGUAGE",
                replace(
                    script_version,
                    payload={
                        **script_version.payload,
                        "scenes": tuple(
                            replace_scene(scene, narration="Scene explains AI.")
                            for scene in script_version.payload["scenes"]
                        ),
                    },
                ),
                script_version,
            ),
            (
                "INVALID_SCENE_ID",
                replace(
                    script_version,
                    payload={
                        **script_version.payload,
                        "scenes": (
                            replace_scene(script_version.payload["scenes"][0], scene_id=""),
                            *script_version.payload["scenes"][1:],
                        ),
                    },
                ),
                script_version,
            ),
            (
                "INVALID_SCRIPT_DURATION",
                replace(
                    script_version,
                    payload={**script_version.payload, "duration_seconds": 72},
                ),
                script_version,
            ),
        )
        for expected_code, mutated_script, mutated_course in cases:
            with self.subTest(expected_code=expected_code):
                assessment = ScriptDecisionBoundary().assess(
                    script_reference,
                    mutated_script,
                    knowledge_reference,
                    knowledge_version,
                    course_reference,
                    mutated_course if mutated_course is not script_version else course_version,
                    episode_reference,
                    episode_version,
                )
                self.assertIsInstance(assessment, ScriptGateAssessment)
                self.assertEqual(assessment.disposition, "hard_block")
                self.assertIn(expected_code, {finding.code for finding in assessment.findings})

    def test_pass_approve_persists_immutable_exact_decision_and_replays(self):
        values = valid_versions()
        boundary = ScriptDecisionBoundary()
        assessment = self._assess(values, boundary)

        record = boundary.decide(
            assessment,
            decision_id="decision-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )

        self.assertIsInstance(record, ScriptDecisionRecord)
        self.assertEqual(record.decision_id, "decision-1")
        self.assertEqual(record.task_id, "task-1")
        self.assertEqual(record.thread_id, "thread-1")
        self.assertEqual(record.creator_id, "creator-1")
        self.assertEqual(record.gate_kind, "script_review")
        self.assertEqual(record.script_reference, assessment.script_reference)
        self.assertEqual(record.assessment_disposition, "pass")
        self.assertEqual(record.action, "approve")
        self.assertEqual(record.finding_codes, ())
        self.assertEqual(boundary.get("decision-1"), record)

        replay = boundary.decide(
            assessment,
            decision_id="decision-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIs(replay, record)
        with self.assertRaises((AttributeError, TypeError)):
            record.action = "revise"

        conflict = boundary.decide(
            assessment,
            decision_id="decision-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="revise",
            decision_context="Use a different revision instruction.",
        )
        self.assertIsInstance(conflict, ScriptDecisionFailure)
        self.assertEqual(conflict.kind, "validation")
        self.assertEqual(conflict.code, "DECISION_CONFLICT")

    def test_revise_persists_bounded_decision_context_and_context_conflicts(self):
        values = valid_versions()
        boundary = ScriptDecisionBoundary()
        assessment = self._assess(values, boundary)

        record = boundary.decide(
            assessment,
            decision_id="decision-context-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="revise",
            decision_context="Ground scene two in the source claim.",
        )

        self.assertIsInstance(record, ScriptDecisionRecord)
        self.assertEqual(record.decision_context, "Ground scene two in the source claim.")

        replay = boundary.decide(
            assessment,
            decision_id="decision-context-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="revise",
            decision_context="Ground scene two in the source claim.",
        )
        self.assertIs(replay, record)

        conflict = boundary.decide(
            assessment,
            decision_id="decision-context-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="revise",
            decision_context="Use a different revision instruction.",
        )
        self.assertIsInstance(conflict, ScriptDecisionFailure)
        self.assertEqual(conflict.kind, "validation")
        self.assertEqual(conflict.code, "DECISION_CONFLICT")

    def test_reject_and_revise_require_safe_bounded_decision_context(self):
        values = valid_versions()
        boundary = ScriptDecisionBoundary()
        assessment = self._assess(values, boundary)

        invalid_contexts = ("", "   ", "\n", "x" * 4097)
        for action in ("reject", "revise"):
            for index, context in enumerate(invalid_contexts):
                with self.subTest(action=action, index=index):
                    result = boundary.decide(
                        assessment,
                        decision_id=f"invalid-context-{action}-{index}",
                        task_id="task-1",
                        thread_id="thread-1",
                        creator_id="creator-1",
                        action=action,
                        decision_context=context,
                    )
                    self.assertIsInstance(result, ScriptDecisionFailure)
                    self.assertEqual(result.kind, "validation")
                    self.assertEqual(result.code, "INVALID_DECISION_CONTEXT")
                    self.assertIsInstance(
                        boundary.get(f"invalid-context-{action}-{index}"),
                        ScriptDecisionFailure,
                    )

    def test_hard_block_cannot_approve_but_reject_and_revise_are_recorded(self):
        values = list(valid_versions())
        script_reference = values[7]
        script_version = values[8]
        values[8] = replace(
            script_version,
            payload={
                **script_version.payload,
                "scenes": (
                    replace_scene(script_version.payload["scenes"][0], knowledge_claim_ids=("foreign",)),
                    *script_version.payload["scenes"][1:],
                ),
            },
        )
        boundary = ScriptDecisionBoundary()
        assessment = self._assess(tuple(values), boundary)
        self.assertEqual(assessment.disposition, "hard_block")

        blocked = boundary.decide(
            assessment,
            decision_id="blocked-approve",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(blocked, ScriptDecisionFailure)
        self.assertEqual(blocked.kind, "validation")
        self.assertEqual(blocked.code, "HARD_BLOCK_APPROVAL_FORBIDDEN")
        self.assertIsInstance(boundary.get("blocked-approve"), ScriptDecisionFailure)

        for action in ("reject", "revise"):
            with self.subTest(action=action):
                record = boundary.decide(
                    assessment,
                    decision_id=f"decision-{action}",
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action=action,
                    decision_context=f"Creator requested {action} for this exact Script version.",
                )
                self.assertIsInstance(record, ScriptDecisionRecord)
                self.assertEqual(record.action, action)
                self.assertEqual(record.assessment_disposition, "hard_block")
                self.assertEqual(record.script_reference, script_reference)

        self.assertEqual(values[8].payload["scenes"][0]["knowledge_claim_ids"], ("foreign",))

    def test_forged_pass_assessment_cannot_approve_after_hard_block(self):
        values = list(valid_versions())
        (
            _,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
            script_reference,
            script_version,
        ) = values
        invalid_script = replace(
            script_version,
            payload={
                **script_version.payload,
                "scenes": (
                    replace_scene(script_version.payload["scenes"][0], knowledge_claim_ids=("foreign",)),
                    *script_version.payload["scenes"][1:],
                ),
            },
        )
        boundary = ScriptDecisionBoundary()
        hard_block = boundary.assess(
            script_reference,
            invalid_script,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
        )
        self.assertIsInstance(hard_block, ScriptGateAssessment)
        self.assertEqual(hard_block.disposition, "hard_block")

        forged_pass = ScriptGateAssessment(
            script_reference=hard_block.script_reference,
            knowledge_reference=hard_block.knowledge_reference,
            course_plan_reference=hard_block.course_plan_reference,
            episode_plan_reference=hard_block.episode_plan_reference,
            disposition="pass",
            findings=(),
        )
        result = boundary.decide(
            forged_pass,
            decision_id="forged-approve",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIsInstance(result, ScriptDecisionFailure)
        self.assertEqual(result.kind, "validation")
        self.assertEqual(result.code, "ASSESSMENT_NOT_ISSUED")
        self.assertIsInstance(boundary.get("forged-approve"), ScriptDecisionFailure)

    def test_exact_reference_version_and_action_mismatches_fail_closed(self):
        values = valid_versions()
        (
            _,
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
            script_reference,
            script_version,
        ) = values
        boundary = ScriptDecisionBoundary()
        cases = (
            (
                "SCRIPT_REFERENCE_MISMATCH",
                ArtifactReference("script", script_reference.identity, 2),
                script_version,
                script_reference,
                knowledge_version,
                course_reference,
                course_version,
                episode_reference,
                episode_version,
            ),
            (
                "INVALID_SCRIPT_REFERENCE",
                ArtifactReference("script", "latest", 1),
                script_version,
                script_reference,
                knowledge_version,
                course_reference,
                course_version,
                episode_reference,
                episode_version,
            ),
            (
                "COURSE_PLAN_REFERENCE_MISMATCH",
                script_reference,
                script_version,
                script_reference,
                knowledge_version,
                ArtifactReference("content_plan", course_reference.identity, 2),
                course_version,
                episode_reference,
                episode_version,
            ),
        )
        for (
            expected_code,
            target_script_reference,
            target_script_version,
            _,
            target_knowledge_version,
            target_course_reference,
            target_course_version,
            target_episode_reference,
            target_episode_version,
        ) in cases:
            with self.subTest(expected_code=expected_code):
                result = boundary.assess(
                    target_script_reference,
                    target_script_version,
                    knowledge_reference,
                    target_knowledge_version,
                    target_course_reference,
                    target_course_version,
                    target_episode_reference,
                    target_episode_version,
                )
                self.assertIsInstance(result, ScriptDecisionFailure)
                self.assertEqual(result.kind, "validation")
                self.assertEqual(result.code, expected_code)

        assessment = self._assess(values, boundary)
        invalid = boundary.decide(
            assessment,
            decision_id="invalid-action",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="publish",
        )
        self.assertIsInstance(invalid, ScriptDecisionFailure)
        self.assertEqual(invalid.code, "INVALID_DECISION_ACTION")


if __name__ == "__main__":
    unittest.main()
