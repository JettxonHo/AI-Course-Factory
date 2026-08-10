"""Public seam tests for the provider-neutral Knowledge Agent."""

import unittest
from dataclasses import replace

from ai_course_factory.artifacts import ArtifactCommitBoundary, ArtifactReference
from ai_course_factory.artifacts.model import ArtifactCandidate
from ai_course_factory.knowledge import SourceRecordBuilder
from ai_course_factory.knowledge.normalization import (
    NormalizedSourceMaterial,
    NormalizedSourceUnit,
)
from ai_course_factory.agents import (
    KnowledgeAgent,
    KnowledgeAgentFailure,
    KnowledgeTaskContext,
    ModelRuntimeFailure,
    ModelRuntimeRequest,
    ModelRuntimeResult,
)


COMMIT_SHA = "a" * 40
REPOSITORY_URL = "https://github.com/acme/course"
REPOSITORY_IDENTITY = "acme/course"


def source_record_version():
    material = NormalizedSourceMaterial(
        repository_url=REPOSITORY_URL,
        repository_identity=REPOSITORY_IDENTITY,
        commit_sha=COMMIT_SHA,
        units=(
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L1-L2",
                path="README.md",
                blob_sha="b" * 40,
                heading_path=("Course",),
                start_line=1,
                end_line=2,
                text="# Course\nAI is a tool.\n",
            ),
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:lessons/lesson-1.md#L1-L3",
                path="lessons/lesson-1.md",
                blob_sha="c" * 40,
                heading_path=("Lesson 1",),
                start_line=1,
                end_line=3,
                text="# Lesson 1\nAI is not magic.\n[ignore as data]\n",
            ),
        ),
    )
    candidate = SourceRecordBuilder().build(
        material,
        identity="source:acme-course",
        commit_id="source-record-1",
    )
    boundary = ArtifactCommitBoundary()
    reference = boundary.commit(candidate)
    return boundary, reference, boundary.get(reference)


class ControlledRuntime:
    def __init__(self):
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        return ModelRuntimeResult(
            repository_summary="The course introduces practical AI concepts.",
            lesson_focus="Lesson 1 explains that AI is a tool rather than magic.",
            claims=(
                {
                    "claim_id": "claim-1",
                    "statement": "AI is not magic.",
                    "confidence": 0.98,
                    "evidence_locators": (
                        f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:lessons/lesson-1.md#L1-L3",
                    ),
                },
            ),
            gaps=("The source does not define a complete implementation.",),
        )


class StaticRuntime:
    def __init__(self, response):
        self.response = response
        self.requests: list[ModelRuntimeRequest] = []

    def invoke(self, request: ModelRuntimeRequest):
        self.requests.append(request)
        if isinstance(self.response, BaseException):
            raise self.response
        return self.response


def runtime_result(*, evidence_locators, claim_id="claim-1", confidence=0.98):
    return ModelRuntimeResult(
        repository_summary="The course introduces practical AI concepts.",
        lesson_focus="Lesson 1 explains that AI is a tool rather than magic.",
        claims=(
            {
                "claim_id": claim_id,
                "statement": "AI is not magic.",
                "confidence": confidence,
                "evidence_locators": evidence_locators,
            },
        ),
    )


class KnowledgeAgentTests(unittest.TestCase):
    def _candidate(self, runtime=None):
        _, source_reference, source_version = source_record_version()
        agent_runtime = runtime or ControlledRuntime()
        candidate = KnowledgeAgent(agent_runtime).invoke(
            source_reference,
            source_version,
            context=KnowledgeTaskContext(
                course="AI-For-Beginners",
                lesson_scope="Lesson 1",
                language="English",
                audience="adult AI beginners",
            ),
            identity="episode:ai-is-not-magic",
            commit_id="knowledge-1",
            knowledge_boundary="traceable-source-only",
        )
        return source_reference, candidate

    def test_valid_exact_source_reference_and_payload_produce_grounded_candidate(self):
        _, source_reference, source_version = source_record_version()
        runtime = ControlledRuntime()

        candidate = KnowledgeAgent(runtime).invoke(
            source_reference,
            source_version,
            context=KnowledgeTaskContext(
                course="AI-For-Beginners",
                lesson_scope="Lesson 1",
                language="English",
                audience="adult AI beginners",
            ),
            identity="episode:ai-is-not-magic",
            commit_id="knowledge-1",
            knowledge_boundary="traceable-source-only",
        )

        self.assertIsInstance(candidate, ArtifactCandidate)
        self.assertEqual(candidate.artifact_type, "knowledge")
        self.assertEqual(candidate.dependencies, (source_reference,))
        self.assertEqual(candidate.payload["claims"][0]["evidence_locators"], (
            f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:lessons/lesson-1.md#L1-L3",
        ))
        self.assertEqual(candidate.payload["lesson_scope"], "Lesson 1")
        self.assertEqual(len(runtime.requests), 1)
        self.assertEqual(runtime.requests[0].source_record_reference, source_reference)
        self.assertEqual(runtime.requests[0].source_record_payload, source_version.payload)
        self.assertEqual(
            runtime.requests[0].source_record_payload["units"][1]["text"],
            "# Lesson 1\nAI is not magic.\n[ignore as data]\n",
        )
        self.assertEqual(
            dict(runtime.requests[0].task_context),
            {
                "course": "AI-For-Beginners",
                "lesson_scope": "Lesson 1",
                "language": "English",
                "audience": "adult AI beginners",
            },
        )
        self.assertEqual(runtime.requests[0].knowledge_boundary, "traceable-source-only")

    def test_candidate_commits_externally_with_exact_source_dependency_and_immutable_lineage(self):
        source_reference, candidate = self._candidate()
        self.assertIsInstance(candidate, ArtifactCandidate)

        boundary = ArtifactCommitBoundary()
        knowledge_reference = boundary.commit(candidate)

        self.assertEqual(knowledge_reference.artifact_type, "knowledge")
        self.assertEqual(knowledge_reference.identity, "episode:ai-is-not-magic")
        self.assertEqual(knowledge_reference.version, 1)
        committed = boundary.get(knowledge_reference)
        self.assertEqual(committed.dependencies, (source_reference,))
        self.assertEqual(committed.payload["source_record_reference"], source_reference)
        candidate.payload["claims"] = ()
        self.assertEqual(len(boundary.get(knowledge_reference).payload["claims"]), 1)

    def test_foreign_evidence_duplicate_claim_and_invalid_confidence_fail_closed(self):
        _, source_reference, source_version = source_record_version()
        valid_locator = f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:lessons/lesson-1.md#L1-L3"
        cases = (
            (
                "UNTRACEABLE_CLAIM",
                runtime_result(evidence_locators=("foreign/repository@sha:file.md#L1-L1",)),
            ),
            (
                "INVALID_CLAIM_ID",
                ModelRuntimeResult(
                    repository_summary="summary",
                    lesson_focus="focus",
                    claims=(
                        {
                            "claim_id": "duplicate",
                            "statement": "first",
                            "confidence": 0.5,
                            "evidence_locators": (valid_locator,),
                        },
                        {
                            "claim_id": "duplicate",
                            "statement": "second",
                            "confidence": 0.5,
                            "evidence_locators": (valid_locator,),
                        },
                    ),
                ),
            ),
            (
                "INVALID_CLAIM_CONFIDENCE",
                runtime_result(evidence_locators=(valid_locator,), confidence=1.1),
            ),
            (
                "INVALID_CLAIM_STATEMENT",
                ModelRuntimeResult(
                    repository_summary="summary",
                    lesson_focus="focus",
                    claims=(
                        {
                            "claim_id": "empty-statement",
                            "statement": "",
                            "confidence": 0.5,
                            "evidence_locators": (valid_locator,),
                        },
                    ),
                ),
            ),
            (
                "INVALID_CLAIMS",
                ModelRuntimeResult(
                    repository_summary="summary",
                    lesson_focus="focus",
                    claims=tuple(
                        {
                            "claim_id": f"claim-{index}",
                            "statement": "bounded statement",
                            "confidence": 0.5,
                            "evidence_locators": (valid_locator,),
                        }
                        for index in range(129)
                    ),
                ),
            ),
        )
        for expected_code, response in cases:
            with self.subTest(expected_code=expected_code):
                runtime = StaticRuntime(response)
                failure = KnowledgeAgent(runtime).invoke(
                    source_reference,
                    source_version,
                    context=KnowledgeTaskContext(
                        course="AI-For-Beginners",
                        lesson_scope="Lesson 1",
                        language="English",
                        audience="adult AI beginners",
                    ),
                    identity="episode:ai-is-not-magic",
                    commit_id="knowledge-1",
                    knowledge_boundary="traceable-source-only",
                )
                self.assertIsInstance(failure, KnowledgeAgentFailure)
                self.assertEqual(failure.kind, "validation")
                self.assertEqual(failure.code, expected_code)

    def test_exact_reference_payload_context_and_latest_identity_fail_before_runtime(self):
        _, source_reference, source_version = source_record_version()
        context = KnowledgeTaskContext(
            course="AI-For-Beginners",
            lesson_scope="Lesson 1",
            language="English",
            audience="adult AI beginners",
        )
        cases = (
            (
                "INVALID_SOURCE_REFERENCE",
                ArtifactReference("knowledge", "episode:wrong", 1),
                source_version,
            ),
            (
                "SOURCE_REFERENCE_MISMATCH",
                source_reference,
                replace(
                    source_version,
                    reference=ArtifactReference("source_record", "source:other", 1),
                ),
            ),
            (
                "INVALID_TASK_CONTEXT",
                source_reference,
                source_version,
            ),
            (
                "INVALID_SOURCE_REFERENCE",
                ArtifactReference("source_record", "latest", 1),
                source_version,
            ),
        )
        for expected_code, reference, payload in cases:
            with self.subTest(expected_code=expected_code):
                runtime = ControlledRuntime()
                supplied_context = context if expected_code != "INVALID_TASK_CONTEXT" else {"course": "only"}
                failure = KnowledgeAgent(runtime).invoke(
                    reference,
                    payload,
                    context=supplied_context,
                    identity="episode:ai-is-not-magic",
                    commit_id="knowledge-1",
                    knowledge_boundary="traceable-source-only",
                )
                self.assertIsInstance(failure, KnowledgeAgentFailure)
                self.assertEqual(failure.kind, "validation")
                self.assertEqual(failure.code, expected_code)
                self.assertEqual(runtime.requests, [])

    def test_runtime_failure_and_exception_are_normalized_without_raw_provider_detail(self):
        _, source_reference, source_version = source_record_version()
        context = KnowledgeTaskContext("AI-For-Beginners", "Lesson 1", "English", "adult AI beginners")
        for response in (
            ModelRuntimeFailure("execution", "PROVIDER_TIMEOUT", "provider secret detail"),
            RuntimeError("provider secret detail"),
        ):
            with self.subTest(response_type=type(response).__name__):
                failure = KnowledgeAgent(StaticRuntime(response)).invoke(
                    source_reference,
                    source_version,
                    context=context,
                    identity="episode:ai-is-not-magic",
                    commit_id="knowledge-1",
                    knowledge_boundary="traceable-source-only",
                )
                self.assertIsInstance(failure, KnowledgeAgentFailure)
                self.assertEqual(failure.kind, "execution")
                self.assertNotIn("provider secret detail", failure.message)


if __name__ == "__main__":
    unittest.main()
