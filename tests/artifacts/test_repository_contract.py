"""Shared public behavior contract for Artifact repositories."""

import math
import tempfile
import unittest
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    ArtifactNotFoundError,
    ArtifactReference,
    ArtifactRepository,
    CandidateValidationError,
    CommitConflictError,
    RevisionMismatchError,
    SQLiteArtifactRepository,
)


def _for_each_repository(exercise: Callable[[ArtifactRepository], None]) -> None:
    """Run one public behavior assertion against both implementations."""

    exercise(ArtifactCommitBoundary())
    with tempfile.TemporaryDirectory() as directory:
        repository = SQLiteArtifactRepository(Path(directory) / "artifacts.sqlite3")
        try:
            exercise(repository)
        finally:
            repository.close()


def _candidate(
    *,
    artifact_type: str = "script",
    identity: str = "episode:contract",
    payload: Any = None,
    provenance: tuple[Any, ...] | None = None,
    dependencies: tuple[ArtifactReference, ...] | None = None,
    commit_id: str = "contract-v1",
    prior_reference: ArtifactReference | None = None,
) -> ArtifactCandidate:
    if payload is None:
        payload = {"text": "first", "count": 1}
    return ArtifactCandidate(
        artifact_type=artifact_type,
        identity=identity,
        payload=payload,
        provenance=("source:v1",) if provenance is None else provenance,
        dependencies=() if dependencies is None else dependencies,
        validated=True,
        commit_id=commit_id,
        prior_reference=prior_reference,
    )


class ArtifactRepositoryContractTests(unittest.TestCase):
    def test_both_implementations_satisfy_the_runtime_protocol(self):
        _for_each_repository(lambda repository: self.assertIsInstance(repository, ArtifactRepository))

    def test_valid_commit_exact_get_and_detached_immutable_values(self):
        def exercise(repository: ArtifactRepository) -> None:
            payload = {"nested": {"values": [1]}}
            provenance = {"source": {"uri": "source:v1"}}
            candidate = _candidate(payload=payload, provenance=(provenance,))

            reference = repository.commit(candidate)
            payload["nested"]["values"].append(2)
            provenance["source"]["uri"] = "mutated"
            version = repository.get(reference)

            self.assertEqual(reference, ArtifactReference("script", "episode:contract", 1))
            self.assertEqual(version.payload, {"nested": {"values": (1,)}})
            self.assertEqual(version.provenance, ({"source": {"uri": "source:v1"}},))
            with self.assertRaises(TypeError):
                version.payload["nested"]["values"] += (2,)

        _for_each_repository(exercise)

    def test_revision_requires_current_exact_predecessor_and_preserves_history(self):
        def exercise(repository: ArtifactRepository) -> None:
            with self.assertRaises(RevisionMismatchError):
                repository.commit(
                    _candidate(
                        identity="episode:first-with-prior",
                        payload={"text": "invalid first"},
                        commit_id="first-with-prior-v1",
                        prior_reference=ArtifactReference("script", "episode:first-with-prior", 1),
                    )
                )
            first = repository.commit(_candidate())
            second = repository.commit(
                _candidate(
                    payload={"text": "second"},
                    commit_id="contract-v2",
                    prior_reference=first,
                )
            )
            self.assertEqual(second.version, 2)
            self.assertEqual(repository.get(first).payload, {"text": "first", "count": 1})

            with self.assertRaises(RevisionMismatchError):
                repository.commit(
                    _candidate(
                        payload={"text": "stale"},
                        commit_id="contract-v3",
                        prior_reference=first,
                    )
                )
            with self.assertRaises(RevisionMismatchError):
                repository.commit(
                    _candidate(
                        payload={"text": "foreign"},
                        commit_id="contract-v4",
                        prior_reference=ArtifactReference("script", "episode:other", 1),
                    )
                )
            with self.assertRaises(ArtifactNotFoundError):
                repository.get(ArtifactReference("script", "episode:contract", 3))

        _for_each_repository(exercise)

    def test_equivalent_replay_is_idempotent_and_changed_input_conflicts(self):
        def exercise(repository: ArtifactRepository) -> None:
            first_candidate = _candidate()
            first = repository.commit(first_candidate)
            self.assertEqual(repository.commit(_candidate()), first)
            with self.assertRaises(CommitConflictError):
                repository.commit(_candidate(payload={"text": "changed"}))
            with self.assertRaises(ArtifactNotFoundError):
                repository.get(ArtifactReference("script", "episode:contract", 2))

        _for_each_repository(exercise)

    def test_validation_and_exact_reference_fail_without_mutation(self):
        def exercise(repository: ArtifactRepository) -> None:
            invalid = _candidate(commit_id="invalid")
            invalid = ArtifactCandidate(
                artifact_type=invalid.artifact_type,
                identity="episode:invalid",
                payload=invalid.payload,
                provenance=invalid.provenance,
                dependencies=invalid.dependencies,
                validated=False,
                commit_id=invalid.commit_id,
            )
            with self.assertRaises(CandidateValidationError):
                repository.commit(invalid)
            with self.assertRaises(ArtifactNotFoundError):
                repository.get(ArtifactReference("script", "episode:invalid", 1))

            with self.assertRaises(CandidateValidationError):
                repository.commit(_candidate(payload={"score": math.nan}, commit_id="nan"))
            with self.assertRaises(ArtifactNotFoundError):
                repository.get(ArtifactReference("script", "episode:contract", 1))
            with self.assertRaises(ArtifactNotFoundError):
                repository.get(("script", "episode:contract"))

        _for_each_repository(exercise)

    def test_unsupported_cyclic_nonfinite_and_invalid_reference_values_fail_atomically(self):
        class UnsupportedPayload:
            pass

        def exercise(repository: ArtifactRepository) -> None:
            cyclic: list[Any] = []
            cyclic.append(cyclic)
            invalid_candidates = (
                _candidate(identity="episode:unsupported", payload=UnsupportedPayload(), commit_id="unsupported"),
                _candidate(identity="episode:cyclic", payload=cyclic, commit_id="cyclic"),
                _candidate(identity="episode:nan", payload={"score": math.nan}, commit_id="nan"),
                _candidate(
                    identity="episode:infinite-provenance",
                    provenance=({"score": math.inf},),
                    commit_id="infinite-provenance",
                ),
                _candidate(
                    identity="episode:bad-dependency",
                    dependencies=("not-an-artifact-reference",),
                    commit_id="bad-dependency",
                ),
                _candidate(
                    identity="episode:bad-prior",
                    prior_reference=ArtifactReference("script", "episode:bad-prior", 0),
                    commit_id="bad-prior",
                ),
            )
            for candidate in invalid_candidates:
                with self.subTest(identity=candidate.identity):
                    with self.assertRaises(CandidateValidationError):
                        repository.commit(candidate)
                    with self.assertRaises(ArtifactNotFoundError):
                        repository.get(ArtifactReference(candidate.artifact_type, candidate.identity, 1))

        _for_each_repository(exercise)


if __name__ == "__main__":
    unittest.main()
