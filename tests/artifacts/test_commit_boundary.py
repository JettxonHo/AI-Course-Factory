"""Public behavior tests for the Artifact Commit boundary."""

import math
import unittest

from ai_course_factory.artifacts.commit import (
    ArtifactCommitBoundary,
    ArtifactNotFoundError,
    CandidateValidationError,
    CommitConflictError,
    RevisionMismatchError,
)
from ai_course_factory.artifacts.model import ArtifactCandidate, ArtifactReference


class MutablePayload:
    def __init__(self):
        self.value = "mutable"


class ArtifactCommitBoundaryTests(unittest.TestCase):
    def test_valid_candidate_commit_returns_version_one_and_exact_retrieval(self):
        boundary = ArtifactCommitBoundary()
        candidate = ArtifactCandidate(
            artifact_type="source_record",
            identity="source:ai-for-beginners",
            payload={"uri": "https://github.com/microsoft/AI-For-Beginners"},
            provenance=("input:user",),
            dependencies=(),
            validated=True,
            commit_id="source-import-1",
        )

        reference = boundary.commit(candidate)

        self.assertEqual(reference.artifact_type, "source_record")
        self.assertEqual(reference.identity, "source:ai-for-beginners")
        self.assertEqual(reference.version, 1)
        committed = boundary.get(reference)
        self.assertEqual(committed.reference, reference)
        self.assertEqual(committed.payload, candidate.payload)
        self.assertIsNot(committed, candidate)

    def test_explicit_revision_creates_next_version_and_preserves_history(self):
        boundary = ArtifactCommitBoundary()
        first = boundary.commit(
            ArtifactCandidate(
                artifact_type="knowledge",
                identity="episode:ai-is-not-magic",
                payload={"lesson": "AI is a tool"},
                provenance=("source:v1",),
                dependencies=(),
                validated=True,
                commit_id="knowledge-v1",
            )
        )
        revision = boundary.commit(
            ArtifactCandidate(
                artifact_type="knowledge",
                identity="episode:ai-is-not-magic",
                payload={"lesson": "AI is a tool, not magic"},
                provenance=("source:v1",),
                dependencies=(),
                validated=True,
                commit_id="knowledge-v2",
                prior_reference=first,
            )
        )

        self.assertEqual(revision.version, 2)
        self.assertEqual(boundary.get(first).payload, {"lesson": "AI is a tool"})
        self.assertEqual(boundary.get(revision).payload, {"lesson": "AI is a tool, not magic"})
        self.assertEqual(boundary.get(revision).prior_reference, first)

    def test_stale_predecessor_cannot_create_a_third_version(self):
        boundary = ArtifactCommitBoundary()
        first = boundary.commit(
            ArtifactCandidate(
                artifact_type="script",
                identity="episode:stale-predecessor",
                payload={"text": "version one"},
                provenance=(),
                dependencies=(),
                validated=True,
                commit_id="stale-predecessor-v1",
            )
        )
        second = boundary.commit(
            ArtifactCandidate(
                artifact_type="script",
                identity="episode:stale-predecessor",
                payload={"text": "version two"},
                provenance=(),
                dependencies=(),
                validated=True,
                commit_id="stale-predecessor-v2",
                prior_reference=first,
            )
        )
        stale_revision = ArtifactCandidate(
            artifact_type="script",
            identity="episode:stale-predecessor",
            payload={"text": "invalid version three"},
            provenance=(),
            dependencies=(),
            validated=True,
            commit_id="stale-predecessor-v3",
            prior_reference=first,
        )

        with self.assertRaises(RevisionMismatchError):
            boundary.commit(stale_revision)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("script", "episode:stale-predecessor", 3))
        self.assertEqual(boundary.get(first).payload, {"text": "version one"})
        self.assertEqual(boundary.get(second).payload, {"text": "version two"})

    def test_equivalent_logical_commit_returns_existing_reference_without_new_version(self):
        boundary = ArtifactCommitBoundary()
        candidate = ArtifactCandidate(
            artifact_type="script",
            identity="episode:ai-is-not-magic",
            payload={"scenes": ["AI is not magic"]},
            provenance=("knowledge:1",),
            dependencies=(),
            validated=True,
            commit_id="script-generation-1",
        )

        first = boundary.commit(candidate)
        repeated = boundary.commit(candidate)
        revision = boundary.commit(
            ArtifactCandidate(
                artifact_type="script",
                identity="episode:ai-is-not-magic",
                payload={"scenes": ["AI is a tool, not magic"]},
                provenance=("knowledge:1",),
                dependencies=(),
                validated=True,
                commit_id="script-generation-2",
                prior_reference=first,
            )
        )

        self.assertEqual(repeated, first)
        self.assertEqual(revision.version, 2)

    def test_invalid_candidate_and_revision_mismatch_create_no_version(self):
        boundary = ArtifactCommitBoundary()
        invalid = ArtifactCandidate(
            artifact_type="knowledge",
            identity="episode:invalid",
            payload={"lesson": "unvalidated"},
            provenance=(),
            dependencies=(),
            validated=False,
            commit_id="invalid-1",
        )

        with self.assertRaises(CandidateValidationError):
            boundary.commit(invalid)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("knowledge", "episode:invalid", 1))

        first = boundary.commit(
            ArtifactCandidate(
                artifact_type="knowledge",
                identity="episode:revision-source",
                payload={"lesson": "original"},
                provenance=(),
                dependencies=(),
                validated=True,
                commit_id="revision-source-1",
            )
        )
        mismatched = ArtifactCandidate(
            artifact_type="knowledge",
            identity="episode:revision-source",
            payload={"lesson": "mismatch"},
            provenance=(),
            dependencies=(),
            validated=True,
            commit_id="revision-source-2",
            prior_reference=ArtifactReference("knowledge", "another-identity", 1),
        )

        with self.assertRaises(RevisionMismatchError):
            boundary.commit(mismatched)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("knowledge", "episode:revision-source", 2))
        self.assertEqual(boundary.get(first).payload, {"lesson": "original"})

    def test_committed_payload_provenance_and_dependencies_are_detached_and_immutable(self):
        boundary = ArtifactCommitBoundary()
        payload = {"nested": {"values": [1]}}
        provenance = {"source": {"uri": "source:v1"}}
        candidate = ArtifactCandidate(
            artifact_type="knowledge",
            identity="episode:immutable",
            payload=payload,
            provenance=(provenance,),
            dependencies=(),
            validated=True,
            commit_id="immutable-1",
        )

        reference = boundary.commit(candidate)
        payload["nested"]["values"].append(2)
        provenance["source"]["uri"] = "mutated-after-commit"
        committed = boundary.get(reference)

        self.assertEqual(committed.payload, {"nested": {"values": (1,)}})
        self.assertEqual(committed.provenance[0], {"source": {"uri": "source:v1"}})
        with self.assertRaises(TypeError):
            committed.payload["nested"]["values"] += (2,)

    def test_boundary_has_no_implicit_latest_or_non_exact_retrieval(self):
        boundary = ArtifactCommitBoundary()
        reference = boundary.commit(
            ArtifactCandidate(
                artifact_type="source_record",
                identity="source:exact-only",
                payload={"uri": "source:v1"},
                provenance=(),
                dependencies=(),
                validated=True,
                commit_id="exact-only-1",
            )
        )

        self.assertFalse(hasattr(boundary, "latest"))
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get((reference.artifact_type, reference.identity))
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("source_record", [], 1))

    def test_reusing_logical_commit_id_with_different_input_is_a_conflict(self):
        boundary = ArtifactCommitBoundary()
        first = ArtifactCandidate(
            artifact_type="script",
            identity="episode:conflict",
            payload={"text": "first"},
            provenance=(),
            dependencies=(),
            validated=True,
            commit_id="same-logical-commit",
        )
        reference = boundary.commit(first)
        changed = ArtifactCandidate(
            artifact_type="script",
            identity="episode:conflict",
            payload={"text": "changed"},
            provenance=(),
            dependencies=(),
            validated=True,
            commit_id="same-logical-commit",
        )

        with self.assertRaises(CommitConflictError):
            boundary.commit(changed)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("script", "episode:conflict", 2))
        self.assertEqual(boundary.get(reference).payload, {"text": "first"})

    def test_unsupported_mutable_payload_is_rejected_before_commit(self):
        boundary = ArtifactCommitBoundary()
        candidate = ArtifactCandidate(
            artifact_type="knowledge",
            identity="episode:unsupported-payload",
            payload=MutablePayload(),
            provenance=(),
            dependencies=(),
            validated=True,
            commit_id="unsupported-payload-1",
        )

        with self.assertRaises(CandidateValidationError):
            boundary.commit(candidate)
        with self.assertRaises(ArtifactNotFoundError):
            boundary.get(ArtifactReference("knowledge", "episode:unsupported-payload", 1))

    def test_non_finite_float_payload_or_provenance_is_rejected_before_commit(self):
        boundary = ArtifactCommitBoundary()
        candidates = (
            ArtifactCandidate(
                artifact_type="knowledge",
                identity="episode:nan-payload",
                payload={"score": math.nan},
                provenance=(),
                dependencies=(),
                validated=True,
                commit_id="nan-payload-1",
            ),
            ArtifactCandidate(
                artifact_type="knowledge",
                identity="episode:infinite-provenance",
                payload={"score": 1.0},
                provenance=({"confidence": math.inf},),
                dependencies=(),
                validated=True,
                commit_id="infinite-provenance-1",
            ),
        )

        for candidate in candidates:
            with self.subTest(identity=candidate.identity):
                with self.assertRaises(CandidateValidationError):
                    boundary.commit(candidate)
                with self.assertRaises(ArtifactNotFoundError):
                    boundary.get(ArtifactReference(candidate.artifact_type, candidate.identity, 1))
