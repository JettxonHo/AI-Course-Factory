"""Public behavior tests for the staged Content Agent boundary."""

import unittest
from dataclasses import replace

from ai_course_factory.artifacts import ArtifactCandidate, ArtifactCommitBoundary, ArtifactReference
from ai_course_factory.agents import (
    ContentAgent,
    ContentAgentFailure,
    ContentPlanCandidateSet,
    ContentRevisionContext,
    ContentTaskContext,
    EpisodeTemplateConstraint,
    ContentModelRuntimeResult,
    ModelRuntimeFailure,
    ModelRuntimeRequest,
)


def knowledge_version():
    boundary = ArtifactCommitBoundary()
    candidate = ArtifactCandidate(
        artifact_type="knowledge",
        identity="episode:ai-is-not-magic-knowledge",
        payload={
            "claims": (
                {
                    "claim_id": "claim-ai-tool",
                    "statement": "AI is a tool.",
                    "confidence": 0.98,
                    "evidence_locators": ("source@commit:lesson.md#L1-L2",),
                },
                {
                    "claim_id": "claim-not-magic",
                    "statement": "AI is not magic.",
                    "confidence": 0.96,
                    "evidence_locators": ("source@commit:lesson.md#L3-L4",),
                },
            ),
            "lesson_scope": "Lesson 1",
        },
        provenance=("source_record:source:v1",),
        dependencies=(),
        validated=True,
        commit_id="knowledge-1",
    )
    reference = boundary.commit(candidate)
    return boundary, reference, boundary.get(reference)


class ControlledContentRuntime:
    def __init__(self):
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        return ContentModelRuntimeResult(
            content={
                "course_plan": {
                    "course_goal": "Build an intuitive AI foundation.",
                    "topics": ("AI concepts", "AI as a tool"),
                    "knowledge_claim_ids": ("claim-ai-tool", "claim-not-magic"),
                },
                "episode_plan": {
                    "title": "AI不是魔法",
                    "episode_number": 1,
                    "learning_goal": "Explain why AI is a tool rather than magic.",
                    "scene_outline": (
                        "Hook",
                        "Question",
                        "Example",
                        "Explanation",
                        "Takeaway",
                        "Close",
                    ),
                    "knowledge_claim_ids": ("claim-ai-tool", "claim-not-magic"),
                },
            },
        )


class ControlledScriptRuntime:
    def __init__(self, *, claim_ids=("claim-ai-tool", "claim-not-magic"), duration=60, english_only=False):
        self.requests: list[ModelRuntimeRequest] = []
        self.claim_ids = claim_ids
        self.duration = duration
        self.english_only = english_only

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        scene_duration = self.duration / 6
        return ContentModelRuntimeResult(
            content={
                "script": {
                    "duration_seconds": self.duration,
                    "aspect_ratio": "9:16",
                    "scenes": tuple(
                    {
                            "scene_id": f"scene-{index}",
                            "duration_seconds": scene_duration,
                            "narration": (
                                f"Scene {index} explains AI."
                                if self.english_only
                                else f"第{index + 1}幕：人工智能是一种工具。"
                            ),
                            "teaching_intent": (
                                f"Show educational visual {index}."
                                if self.english_only
                                else f"展示第{index + 1}幕教育画面。"
                            ),
                            "knowledge_claim_ids": (self.claim_ids[index % len(self.claim_ids)],),
                        }
                        for index in range(6)
                    ),
                }
            },
        )


class StaticContentRuntime:
    def __init__(self, response):
        self.response = response
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def malformed_script_result(
    *, scene_count=6, duration=60, aspect_ratio="9:16", claim_id="claim-ai-tool", english_only=False
):
    scene_duration = duration / scene_count if scene_count else duration
    return ContentModelRuntimeResult(
        content={
            "script": {
                "duration_seconds": duration,
                "aspect_ratio": aspect_ratio,
                "scenes": tuple(
                    {
                        "scene_id": f"scene-{index}",
                        "duration_seconds": scene_duration,
                        "narration": (
                            f"Scene {index} explains AI."
                            if english_only
                            else f"第{index + 1}幕：人工智能是一种工具。"
                        ),
                        "teaching_intent": (
                            f"Show educational visual {index}."
                            if english_only
                            else f"展示第{index + 1}幕教育画面。"
                        ),
                        "knowledge_claim_ids": (claim_id,),
                    }
                    for index in range(scene_count)
                ),
            }
        },
    )


def content_context():
    return ContentTaskContext(
        audience="adult AI beginners",
        series="小土豆学 AI",
        episode_number=1,
        episode_title="AI不是魔法",
        language="Simplified Chinese",
        learning_goal="Explain why AI is not magic.",
    )


def template_constraint():
    return EpisodeTemplateConstraint(
        scene_count=6,
        target_duration_seconds=60,
        aspect_ratio="9:16",
    )


def committed_plans():
    boundary, knowledge_reference, knowledge_version_value = knowledge_version()
    plan_set = ContentAgent(ControlledContentRuntime()).plan(
        knowledge_reference,
        knowledge_version_value,
        context=content_context(),
        template=template_constraint(),
        course_identity="course-plan:ai-for-beginners",
        episode_identity="episode-plan:ai-is-not-magic",
        course_commit_id="course-plan-1",
        episode_commit_id="episode-plan-1",
    )
    course_reference = boundary.commit(plan_set.course)
    episode_reference = boundary.commit(plan_set.episode)
    return (
        boundary,
        knowledge_reference,
        knowledge_version_value,
        course_reference,
        boundary.get(course_reference),
        episode_reference,
        boundary.get(episode_reference),
    )


class ContentAgentTests(unittest.TestCase):
    def test_exact_knowledge_produces_course_and_episode_plan_candidates(self):
        _, knowledge_reference, knowledge_version_value = knowledge_version()
        runtime = ControlledContentRuntime()
        plan_set = ContentAgent(runtime).plan(
            knowledge_reference,
            knowledge_version_value,
            context=ContentTaskContext(
                audience="adult AI beginners",
                series="小土豆学 AI",
                episode_number=1,
                episode_title="AI不是魔法",
                language="Simplified Chinese",
                learning_goal="Explain why AI is not magic.",
            ),
            template=EpisodeTemplateConstraint(
                scene_count=6,
                target_duration_seconds=60,
                aspect_ratio="9:16",
            ),
            course_identity="course-plan:ai-for-beginners",
            episode_identity="episode-plan:ai-is-not-magic",
            course_commit_id="course-plan-1",
            episode_commit_id="episode-plan-1",
        )

        self.assertIsInstance(plan_set, ContentPlanCandidateSet)
        self.assertIsInstance(plan_set.course, ArtifactCandidate)
        self.assertIsInstance(plan_set.episode, ArtifactCandidate)
        self.assertEqual(plan_set.course.artifact_type, "content_plan")
        self.assertEqual(plan_set.course.payload["role"], "course")
        self.assertEqual(plan_set.episode.payload["role"], "episode")
        self.assertEqual(plan_set.course.dependencies, (knowledge_reference,))
        self.assertEqual(plan_set.episode.dependencies, (knowledge_reference,))
        self.assertEqual(len(runtime.requests), 1)
        self.assertEqual(
            runtime.requests[0].inputs["knowledge_reference"], knowledge_reference
        )
        self.assertEqual(
            runtime.requests[0].inputs["knowledge_payload"], knowledge_version_value.payload
        )

    def test_plan_candidates_commit_externally_and_preserve_exact_knowledge_lineage(self):
        boundary, knowledge_reference, _, course_reference, course_version_value, episode_reference, episode_version_value = committed_plans()

        self.assertEqual(course_reference.artifact_type, "content_plan")
        self.assertEqual(episode_reference.artifact_type, "content_plan")
        self.assertEqual(course_version_value.payload["role"], "course")
        self.assertEqual(episode_version_value.payload["role"], "episode")
        self.assertEqual(course_version_value.dependencies, (knowledge_reference,))
        self.assertEqual(episode_version_value.dependencies, (knowledge_reference,))
        self.assertEqual(course_version_value.payload["knowledge_reference"], knowledge_reference)
        self.assertEqual(episode_version_value.payload["knowledge_reference"], knowledge_reference)

    def test_foreign_plan_claim_ids_fail_closed(self):
        _, knowledge_reference, knowledge_version_value = knowledge_version()
        runtime = StaticContentRuntime(
            ContentModelRuntimeResult(
                content={
                    "course_plan": {
                        "course_goal": "Build an intuitive AI foundation.",
                        "knowledge_claim_ids": ("foreign-claim",),
                    },
                    "episode_plan": {
                        "title": "AI不是魔法",
                        "knowledge_claim_ids": ("claim-ai-tool",),
                    },
                }
            )
        )
        failure = ContentAgent(runtime).plan(
            knowledge_reference,
            knowledge_version_value,
            context=content_context(),
            template=template_constraint(),
            course_identity="course-plan:ai-for-beginners",
            episode_identity="episode-plan:ai-is-not-magic",
            course_commit_id="course-plan-1",
            episode_commit_id="episode-plan-1",
        )

        self.assertIsInstance(failure, ContentAgentFailure)
        self.assertEqual(failure.kind, "validation")
        self.assertEqual(failure.code, "UNTRACEABLE_PLAN")

    def test_oversized_nested_plan_output_fails_closed(self):
        _, knowledge_reference, knowledge_version_value = knowledge_version()
        runtime = StaticContentRuntime(
            ContentModelRuntimeResult(
                content={
                    "course_plan": {
                        "course_goal": "Build an intuitive AI foundation.",
                        "knowledge_claim_ids": ("claim-ai-tool",),
                        "nested": tuple(range(65)),
                    },
                    "episode_plan": {
                        "title": "AI不是魔法",
                        "knowledge_claim_ids": ("claim-ai-tool",),
                    },
                }
            )
        )
        failure = ContentAgent(runtime).plan(
            knowledge_reference,
            knowledge_version_value,
            context=content_context(),
            template=template_constraint(),
            course_identity="course-plan:ai-for-beginners",
            episode_identity="episode-plan:ai-is-not-magic",
            course_commit_id="course-plan-1",
            episode_commit_id="episode-plan-1",
        )

        self.assertIsInstance(failure, ContentAgentFailure)
        self.assertEqual(failure.kind, "validation")
        self.assertEqual(failure.code, "INVALID_PLAN")

    def test_exact_knowledge_and_committed_plans_produce_grounded_six_scene_script_candidate(self):
        _, knowledge_reference, knowledge_version_value, course_reference, course_version_value, episode_reference, episode_version_value = committed_plans()
        runtime = ControlledScriptRuntime()
        candidate = ContentAgent(runtime).script(
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
            context=content_context(),
            template=template_constraint(),
            script_identity="script:ai-is-not-magic",
            script_commit_id="script-1",
        )

        self.assertIsInstance(candidate, ArtifactCandidate)
        self.assertEqual(candidate.artifact_type, "script")
        self.assertEqual(candidate.payload["language"], "Simplified Chinese")
        self.assertEqual(
            candidate.dependencies,
            (knowledge_reference, course_reference, episode_reference),
        )
        self.assertEqual(candidate.payload["duration_seconds"], 60)
        self.assertEqual(candidate.payload["aspect_ratio"], "9:16")
        self.assertEqual(len(candidate.payload["scenes"]), 6)
        self.assertTrue(
            all(
                set(scene["knowledge_claim_ids"]) <= {"claim-ai-tool", "claim-not-magic"}
                for scene in candidate.payload["scenes"]
            )
        )
        self.assertEqual(runtime.requests[0].purpose, "content_scripting")
        self.assertEqual(runtime.requests[0].inputs["course_plan_reference"], course_reference)
        self.assertEqual(runtime.requests[0].inputs["episode_plan_reference"], episode_reference)

    def test_script_commit_and_exact_prior_revision_preserve_immutable_history(self):
        boundary, knowledge_reference, knowledge_version_value, course_reference, course_version_value, episode_reference, episode_version_value = committed_plans()
        first_candidate = ContentAgent(ControlledScriptRuntime()).script(
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
            context=content_context(),
            template=template_constraint(),
            script_identity="script:ai-is-not-magic",
            script_commit_id="script-1",
        )
        first_reference = boundary.commit(first_candidate)
        first_version = boundary.get(first_reference)

        revised_candidate = ContentAgent(
            ControlledScriptRuntime(claim_ids=("claim-not-magic", "claim-ai-tool"))
        ).script(
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
            context=content_context(),
            template=template_constraint(),
            script_identity="script:ai-is-not-magic",
            script_commit_id="script-2",
            revision=ContentRevisionContext(
                prior_reference=first_reference,
                prior_version=first_version,
                creator_decision_id="creator-revise-1",
                instruction="Make the explanation more concrete.",
            ),
        )
        self.assertIsInstance(revised_candidate, ArtifactCandidate)
        self.assertEqual(revised_candidate.identity, first_reference.identity)
        self.assertEqual(revised_candidate.prior_reference, first_reference)
        second_reference = boundary.commit(revised_candidate)

        self.assertEqual(second_reference.version, 2)
        self.assertEqual(boundary.get(first_reference).payload, first_version.payload)
        self.assertEqual(boundary.get(second_reference).prior_reference, first_reference)

    def test_reference_context_template_and_runtime_failures_fail_closed_before_or_at_invocation(self):
        _, knowledge_reference, knowledge_version_value = knowledge_version()
        cases = (
            (
                "INVALID_KNOWLEDGE_REFERENCE",
                ArtifactReference("content_plan", "wrong", 1),
                knowledge_version_value,
                content_context(),
                template_constraint(),
            ),
            (
                "KNOWLEDGE_REFERENCE_MISMATCH",
                knowledge_reference,
                replace(
                    knowledge_version_value,
                    reference=ArtifactReference("knowledge", "other", 1),
                ),
                content_context(),
                template_constraint(),
            ),
            (
                "INVALID_CONTENT_CONTEXT",
                knowledge_reference,
                knowledge_version_value,
                {"audience": "only"},
                template_constraint(),
            ),
            (
                "INVALID_TEMPLATE_CONSTRAINT",
                knowledge_reference,
                knowledge_version_value,
                content_context(),
                {"scene_count": 5, "target_duration_seconds": 60, "aspect_ratio": "9:16"},
            ),
            (
                "INVALID_KNOWLEDGE_REFERENCE",
                ArtifactReference("knowledge", "latest", 1),
                knowledge_version_value,
                content_context(),
                template_constraint(),
            ),
        )
        for expected_code, reference, version, context, template in cases:
            with self.subTest(expected_code=expected_code):
                runtime = ControlledContentRuntime()
                failure = ContentAgent(runtime).plan(
                    reference,
                    version,
                    context=context,
                    template=template,
                    course_identity="course-plan:ai-for-beginners",
                    episode_identity="episode-plan:ai-is-not-magic",
                    course_commit_id="course-plan-1",
                    episode_commit_id="episode-plan-1",
                )
                self.assertIsInstance(failure, ContentAgentFailure)
                self.assertEqual(failure.kind, "validation")
                self.assertEqual(failure.code, expected_code)
                self.assertEqual(runtime.requests, [])

        for response in (
            ModelRuntimeFailure("execution", "PROVIDER_TIMEOUT", "provider raw detail"),
            RuntimeError("provider raw detail"),
        ):
            with self.subTest(response_type=type(response).__name__):
                runtime = StaticContentRuntime(response)
                failure = ContentAgent(runtime).plan(
                    knowledge_reference,
                    knowledge_version_value,
                    context=content_context(),
                    template=template_constraint(),
                    course_identity="course-plan:ai-for-beginners",
                    episode_identity="episode-plan:ai-is-not-magic",
                    course_commit_id="course-plan-1",
                    episode_commit_id="episode-plan-1",
                )
                self.assertIsInstance(failure, ContentAgentFailure)
                self.assertEqual(failure.kind, "execution")
                self.assertEqual(failure.code, "MODEL_RUNTIME_FAILED")
                self.assertNotIn("provider raw detail", failure.message)

    def test_plan_lineage_grounding_scene_shape_and_duration_fail_closed(self):
        (
            _,
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
        ) = committed_plans()
        cases = (
            (
                "PLAN_KNOWLEDGE_MISMATCH",
                replace(
                    course_version_value,
                    payload={**course_version_value.payload, "knowledge_reference": ArtifactReference("knowledge", "other", 1)},
                ),
                episode_version_value,
                malformed_script_result(),
            ),
            (
                "UNTRACEABLE_SCENE",
                course_version_value,
                episode_version_value,
                malformed_script_result(claim_id="foreign-claim"),
            ),
            (
                "INVALID_SCENE_TEMPLATE",
                course_version_value,
                episode_version_value,
                malformed_script_result(scene_count=5),
            ),
            (
                "INVALID_SCRIPT_DURATION",
                course_version_value,
                episode_version_value,
                malformed_script_result(duration=72),
            ),
        )
        for expected_code, course_version, episode_version, response in cases:
            with self.subTest(expected_code=expected_code):
                failure = ContentAgent(StaticContentRuntime(response)).script(
                    knowledge_reference,
                    knowledge_version_value,
                    course_reference,
                    course_version,
                    episode_reference,
                    episode_version,
                    context=content_context(),
                    template=template_constraint(),
                    script_identity="script:ai-is-not-magic",
                    script_commit_id="script-1",
                )
                self.assertIsInstance(failure, ContentAgentFailure)
                self.assertEqual(failure.kind, "validation")
                self.assertEqual(failure.code, expected_code)

        failure = ContentAgent(
            StaticContentRuntime(malformed_script_result(english_only=True))
        ).script(
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
            context=content_context(),
            template=template_constraint(),
            script_identity="script:ai-is-not-magic",
            script_commit_id="script-language-1",
        )
        self.assertIsInstance(failure, ContentAgentFailure)
        self.assertEqual(failure.code, "INVALID_SCRIPT_LANGUAGE")

    def test_revision_lineage_requires_matching_prior_script_identity_and_version(self):
        (
            boundary,
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
        ) = committed_plans()
        first_candidate = ContentAgent(ControlledScriptRuntime()).script(
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
            context=content_context(),
            template=template_constraint(),
            script_identity="script:ai-is-not-magic",
            script_commit_id="script-1",
        )
        first_reference = boundary.commit(first_candidate)
        first_version = boundary.get(first_reference)

        bad_revision = ContentRevisionContext(
            prior_reference=ArtifactReference("script", "other", 1),
            prior_version=first_version,
            creator_decision_id="creator-revise-1",
            instruction="Revise.",
        )
        failure = ContentAgent(ControlledScriptRuntime()).script(
            knowledge_reference,
            knowledge_version_value,
            course_reference,
            course_version_value,
            episode_reference,
            episode_version_value,
            context=content_context(),
            template=template_constraint(),
            script_identity="script:ai-is-not-magic",
            script_commit_id="script-2",
            revision=bad_revision,
        )
        self.assertIsInstance(failure, ContentAgentFailure)
        self.assertEqual(failure.code, "SCRIPT_IDENTITY_MISMATCH")


if __name__ == "__main__":
    unittest.main()
