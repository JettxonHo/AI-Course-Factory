"""Offline Source-to-approved-Script vertical-slice proof."""

from __future__ import annotations

import base64
import unittest

from ai_course_factory.agents import (
    ContentAgent,
    ContentModelRuntimeResult,
    ContentRevisionContext,
    ContentTaskContext,
    EpisodeTemplateConstraint,
    KnowledgeAgent,
    KnowledgeTaskContext,
    ModelRuntimeRequest,
    ModelRuntimeResult,
)
from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    ScriptDecisionBoundary,
)
from ai_course_factory.application import ScriptReviewApplicationService
from ai_course_factory.knowledge import (
    GitHubSourceConnector,
    SourceNormalizer,
    SourceRecordBuilder,
)
from ai_course_factory.workflow import InMemoryCheckpointAdapter, ScriptReviewWorkflow


COMMIT_SHA = "a" * 40
BLOB_SHA = "b" * 40
REPOSITORY_URL = "https://github.com/microsoft/AI-For-Beginners"


def file_response(path: str, text: str) -> dict[str, object]:
    return {
        "type": "file",
        "path": path,
        "sha": BLOB_SHA,
        "size": len(text.encode("utf-8")),
        "encoding": "base64",
        "content": base64.b64encode(text.encode("utf-8")).decode("ascii"),
    }


class FixtureGitHubTransport:
    """Deterministic public GitHub transport fixture; it never accesses a network."""

    def __init__(self, responses: dict[str, object]) -> None:
        self.responses = responses
        self.calls: list[str] = []

    def __call__(self, api_path: str) -> object:
        self.calls.append(api_path)
        return self.responses[api_path]


class FixtureKnowledgeRuntime:
    def __init__(self) -> None:
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest) -> ModelRuntimeResult:
        self.requests.append(request)
        source_units = request.source_record_payload["units"]
        locator = source_units[-1]["locator"]
        return ModelRuntimeResult(
            repository_summary="The fixture course introduces the idea that AI is not magic.",
            lesson_focus="Lesson 1 explains that AI is not magic.",
            claims=(
                {
                    "claim_id": "claim-not-magic",
                    "statement": "AI is not magic.",
                    "confidence": 0.98,
                    "evidence_locators": (locator,),
                },
            ),
        )


class FixtureContentRuntime:
    def __init__(self) -> None:
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        if request.purpose == "content_planning":
            return ContentModelRuntimeResult(
                content={
                    "course_plan": {
                        "course_goal": "Build an intuitive AI foundation.",
                        "topics": ("AI concepts", "AI is not magic"),
                        "knowledge_claim_ids": ("claim-not-magic",),
                    },
                    "episode_plan": {
                        "title": "AI不是魔法",
                        "episode_number": 1,
                        "learning_goal": "Explain why AI is not magic.",
                        "scene_outline": (
                            "Hook",
                            "Question",
                            "Example",
                            "Explanation",
                            "Takeaway",
                            "Close",
                        ),
                        "knowledge_claim_ids": ("claim-not-magic",),
                    },
                }
            )
        revision = request.constraints["revision_context"]
        revised = revision is not None
        narration_prefix = "修订版：" if revised else ""
        return ContentModelRuntimeResult(
            content={
                "script": {
                    "duration_seconds": 60,
                    "aspect_ratio": "9:16",
                    "scenes": tuple(
                        {
                            "scene_id": f"scene-{index}",
                            "duration_seconds": 10,
                            "narration": f"{narration_prefix}第{index + 1}幕：人工智能不是魔法。",
                            "teaching_intent": f"说明第{index + 1}幕中人工智能不是魔法。",
                            "knowledge_claim_ids": ("claim-not-magic",),
                        }
                        for index in range(6)
                    ),
                }
            }
        )


class VerticalSliceIntegrationTests(unittest.TestCase):
    def test_source_to_exact_v2_script_approval_is_offline_and_reconstructable(self):
        lesson_text = "# Lesson 1\nAI is not magic.\n"
        transport = FixtureGitHubTransport(
            {
                "/repos/microsoft/AI-For-Beginners": {"default_branch": "main"},
                "/repos/microsoft/AI-For-Beginners/commits?sha=main&per_page=1": [{"sha": COMMIT_SHA}],
                f"/repos/microsoft/AI-For-Beginners/contents/lessons/intro.md?ref={COMMIT_SHA}": file_response(
                    "lessons/intro.md", lesson_text
                ),
            }
        )
        acquisition = GitHubSourceConnector(transport=transport).acquire(
            REPOSITORY_URL,
            ["lessons/intro.md"],
        )
        material = SourceNormalizer().normalize(acquisition)
        source_candidate = SourceRecordBuilder().build(
            material,
            identity="source:microsoft-ai-for-beginners",
            commit_id="source-record-1",
        )
        store = ArtifactCommitBoundary()
        source_reference = store.commit(source_candidate)
        source_version = store.get(source_reference)
        self.assertEqual(source_reference.artifact_type, "source_record")
        self.assertEqual(source_version.payload["repository_url"], REPOSITORY_URL)

        knowledge_runtime = FixtureKnowledgeRuntime()
        knowledge_candidate = KnowledgeAgent(knowledge_runtime).invoke(
            source_reference,
            source_version,
            context=KnowledgeTaskContext(
                course="AI-For-Beginners",
                lesson_scope="Lesson 1",
                language="English",
                audience="adult AI beginners",
            ),
            identity="knowledge:episode-1",
            commit_id="knowledge-1",
            knowledge_boundary="traceable-source-only",
        )
        knowledge_reference = store.commit(knowledge_candidate)
        knowledge_version = store.get(knowledge_reference)
        self.assertEqual(knowledge_version.dependencies, (source_reference,))
        self.assertEqual(knowledge_version.payload["source_record_reference"], source_reference)

        content_context = ContentTaskContext(
            audience="adult AI beginners",
            series="小土豆学 AI",
            episode_number=1,
            episode_title="AI不是魔法",
            language="Simplified Chinese",
            learning_goal="Explain why AI is not magic.",
        )
        template = EpisodeTemplateConstraint(
            scene_count=6,
            target_duration_seconds=60,
            aspect_ratio="9:16",
        )
        content_runtime = FixtureContentRuntime()
        plan_candidates = ContentAgent(content_runtime).plan(
            knowledge_reference,
            knowledge_version,
            context=content_context,
            template=template,
            course_identity="course-plan:episode-1",
            episode_identity="episode-plan:episode-1",
            course_commit_id="course-plan-1",
            episode_commit_id="episode-plan-1",
        )
        course_reference = store.commit(plan_candidates.course)
        episode_reference = store.commit(plan_candidates.episode)
        course_version = store.get(course_reference)
        episode_version = store.get(episode_reference)
        self.assertEqual(course_version.dependencies, (knowledge_reference,))
        self.assertEqual(episode_version.dependencies, (knowledge_reference,))
        self.assertEqual(course_version.payload["knowledge_reference"], knowledge_reference)
        self.assertEqual(episode_version.payload["knowledge_reference"], knowledge_reference)

        script_v1_candidate = ContentAgent(content_runtime).script(
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
            context=content_context,
            template=template,
            script_identity="script:episode-1",
            script_commit_id="script-1",
        )
        script_v1_reference = store.commit(script_v1_candidate)
        script_v1_version = store.get(script_v1_reference)
        self.assertEqual(
            script_v1_version.dependencies,
            (knowledge_reference, course_reference, episode_reference),
        )

        checkpoints = InMemoryCheckpointAdapter()
        decisions = ScriptDecisionBoundary()
        workflow_v1_start = ScriptReviewWorkflow(store, checkpoints)
        service_v1_start = ScriptReviewApplicationService(store, decisions, workflow_v1_start)
        pending_v1 = service_v1_start.start("task-1", "thread-v1", script_v1_reference)
        self.assertEqual(pending_v1.status, "pending")
        self.assertEqual(pending_v1.assessment.disposition, "pass")

        # Reconstruct the mandatory gate before recording the Creator Reject.
        workflow_v1_resume = ScriptReviewWorkflow(store, checkpoints)
        service_v1_resume = ScriptReviewApplicationService(store, decisions, workflow_v1_resume)
        rejected = service_v1_resume.decide(
            "task-1",
            "thread-v1",
            "decision-reject-v1",
            "creator-1",
            "reject",
            script_v1_reference,
            decision_context="Make the explanation more concrete.",
        )
        self.assertEqual(rejected.status, "success")
        self.assertEqual(rejected.lifecycle_state, "script_revision_required")
        self.assertEqual(rejected.decision_record.action, "reject")
        self.assertEqual(rejected.decision_record.decision_context, "Make the explanation more concrete.")

        revision = ContentRevisionContext(
            prior_reference=script_v1_reference,
            prior_version=script_v1_version,
            creator_decision_id=rejected.decision_record.decision_id,
            instruction=rejected.decision_record.decision_context,
        )
        script_v2_candidate = ContentAgent(content_runtime).script(
            knowledge_reference,
            knowledge_version,
            course_reference,
            course_version,
            episode_reference,
            episode_version,
            context=content_context,
            template=template,
            script_identity="script:episode-1",
            script_commit_id="script-2",
            revision=revision,
        )
        script_v2_reference = store.commit(script_v2_candidate)
        script_v2_version = store.get(script_v2_reference)
        self.assertEqual(script_v2_candidate.prior_reference, script_v1_reference)
        self.assertEqual(script_v2_version.prior_reference, script_v1_reference)
        self.assertEqual(
            script_v2_version.dependencies,
            (knowledge_reference, course_reference, episode_reference),
        )
        self.assertEqual(store.get(script_v1_reference).payload, script_v1_version.payload)

        # Start with one runtime and reconstruct the control runtime before
        # deciding on the exact v2 reference using the shared checkpoint adapter.
        workflow_v2_start = ScriptReviewWorkflow(store, checkpoints)
        service_v2_start = ScriptReviewApplicationService(store, decisions, workflow_v2_start)
        pending_v2 = service_v2_start.start("task-1", "thread-v2", script_v2_reference)
        self.assertEqual(pending_v2.status, "pending")
        self.assertEqual(pending_v2.workflow_result.script_reference, script_v2_reference)

        reconstructed = ScriptReviewWorkflow(store, checkpoints)
        service_v2_resume = ScriptReviewApplicationService(store, decisions, reconstructed)
        approved = service_v2_resume.decide(
            "task-1",
            "thread-v2",
            "decision-approve-v2",
            "creator-1",
            "approve",
            script_v2_reference,
        )
        self.assertEqual(approved.status, "success")
        self.assertEqual(approved.lifecycle_state, "script_approved")
        self.assertEqual(approved.decision_record.action, "approve")
        self.assertEqual(approved.decision_record.script_reference, script_v2_reference)
        self.assertEqual(approved.workflow_result.script_reference, script_v2_reference)

        checkpoint = checkpoints.inspect("thread-v2")
        self.assertEqual(checkpoint["selected_script_ref"], script_v2_reference)
        self.assertEqual(checkpoint["pending_gate"], None)
        self.assertNotIn("payload", checkpoint)
        self.assertNotIn("人工智能", repr(checkpoint))
        self.assertEqual(
            [call.split("?")[0] for call in transport.calls],
            [
                "/repos/microsoft/AI-For-Beginners",
                "/repos/microsoft/AI-For-Beginners/commits",
                "/repos/microsoft/AI-For-Beginners/contents/lessons/intro.md",
            ],
        )


if __name__ == "__main__":
    unittest.main()
