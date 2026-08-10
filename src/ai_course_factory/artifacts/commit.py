"""In-memory Artifact Commit boundary for the first vertical slice.

The implementation is intentionally local and deterministic.  Its public
surface models the frozen Artifact contract; persistence can be replaced later
behind the same seam without changing callers.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any

from .model import ArtifactCandidate, ArtifactReference, ArtifactVersion, freeze_value


class ArtifactCommitError(Exception):
    """Base class for bounded Artifact Commit failures."""

    code = "ARTIFACT_COMMIT_ERROR"


class CandidateValidationError(ArtifactCommitError):
    """Candidate is incomplete or has not passed validation."""

    code = "INVALID_CANDIDATE"


class ArtifactNotFoundError(ArtifactCommitError):
    """An exact Artifact Reference does not exist."""

    code = "ARTIFACT_NOT_FOUND"


class CommitConflictError(ArtifactCommitError):
    """A logical Commit identity was reused with different input."""

    code = "COMMIT_CONFLICT"


class RevisionMismatchError(ArtifactCommitError):
    """A revision does not name the exact current predecessor."""

    code = "REVISION_MISMATCH"


@dataclass(frozen=True, slots=True)
class _CommittedLogicalInput:
    """Private snapshot used only for duplicate logical Commit detection."""

    fingerprint: Any
    reference: ArtifactReference


class ArtifactCommitBoundary:
    """Commit and retrieve immutable Artifact Versions by exact Reference."""

    def __init__(self) -> None:
        self._versions: dict[ArtifactReference, ArtifactVersion] = {}
        self._next_versions: dict[tuple[str, str], int] = {}
        self._logical_commits: dict[tuple[tuple[str, str], str], _CommittedLogicalInput] = {}

    def commit(self, candidate: ArtifactCandidate) -> ArtifactReference:
        """Validate and commit a Candidate, or raise a bounded domain error."""

        self._validate_candidate(candidate)
        key = (candidate.artifact_type, candidate.identity)
        fingerprint = self._fingerprint(candidate)
        logical_key = (key, candidate.commit_id)

        existing = self._logical_commits.get(logical_key)
        if existing is not None:
            if existing.fingerprint == fingerprint:
                return existing.reference
            raise CommitConflictError("logical Commit identity conflicts with its original input")

        self._validate_revision(candidate, key)

        version = self._next_versions.get(key, 1)
        reference = ArtifactReference(
            artifact_type=candidate.artifact_type,
            identity=candidate.identity,
            version=version,
        )
        # All potentially failing conversion work happens before mutating the
        # indexes, preserving validation-before-commit and atomic failure.
        committed = ArtifactVersion(
            reference=reference,
            payload=freeze_value(candidate.payload),
            provenance=tuple(freeze_value(item) for item in candidate.provenance or ()),
            dependencies=tuple(candidate.dependencies or ()),
            commit_id=candidate.commit_id,
            prior_reference=candidate.prior_reference,
        )
        self._versions[reference] = committed
        self._next_versions[key] = version + 1
        self._logical_commits[logical_key] = _CommittedLogicalInput(
            fingerprint=fingerprint,
            reference=reference,
        )
        return reference

    def get(self, reference: ArtifactReference) -> ArtifactVersion:
        """Retrieve one committed Version using its exact Reference only."""

        if not self._is_valid_reference(reference):
            raise ArtifactNotFoundError("an exact Artifact Reference is required")
        try:
            return self._versions[reference]
        except KeyError as exc:
            raise ArtifactNotFoundError("the exact Artifact Reference does not exist") from exc

    def _validate_candidate(self, candidate: ArtifactCandidate) -> None:
        if not isinstance(candidate, ArtifactCandidate):
            raise CandidateValidationError("Commit accepts an ArtifactCandidate")
        if candidate.validated is not True:
            raise CandidateValidationError("Candidate validation must pass before Commit")
        if not isinstance(candidate.artifact_type, str) or not candidate.artifact_type.strip():
            raise CandidateValidationError("Artifact type is required")
        if not isinstance(candidate.identity, str) or not candidate.identity.strip():
            raise CandidateValidationError("stable Artifact identity is required")
        if candidate.payload is None:
            raise CandidateValidationError("Artifact payload is required")
        if not self._is_freezable_value(candidate.payload):
            raise CandidateValidationError("payload contains an unsupported mutable value")
        if not isinstance(candidate.commit_id, str) or not candidate.commit_id.strip():
            raise CandidateValidationError("logical Commit identity is required")
        if candidate.provenance is None or candidate.dependencies is None:
            raise CandidateValidationError("provenance and dependencies must be explicit")
        if not all(self._is_freezable_value(item) for item in candidate.provenance):
            raise CandidateValidationError("provenance contains an unsupported mutable value")
        for dependency in candidate.dependencies:
            if not self._is_valid_reference(dependency):
                raise CandidateValidationError("dependencies must be exact Artifact References")
        if candidate.prior_reference is not None and not self._is_valid_reference(candidate.prior_reference):
            raise CandidateValidationError("revision predecessor must be an exact Artifact Reference")

    def _validate_revision(
        self,
        candidate: ArtifactCandidate,
        key: tuple[str, str],
    ) -> None:
        current_version = self._next_versions.get(key, 1) - 1
        prior = candidate.prior_reference
        if current_version == 0:
            if prior is not None:
                raise RevisionMismatchError("a first Version cannot revise a predecessor")
            return
        if prior is None:
            raise RevisionMismatchError("an existing Artifact requires an explicit predecessor Reference")
        if (prior.artifact_type, prior.identity) != key:
            raise RevisionMismatchError("revision predecessor belongs to another Artifact identity")
        if prior.version != current_version or prior not in self._versions:
            raise RevisionMismatchError("revision predecessor is not the current exact Version")

    @staticmethod
    def _is_valid_reference(reference: Any) -> bool:
        return (
            isinstance(reference, ArtifactReference)
            and isinstance(reference.artifact_type, str)
            and bool(reference.artifact_type.strip())
            and isinstance(reference.identity, str)
            and bool(reference.identity.strip())
            and isinstance(reference.version, int)
            and not isinstance(reference.version, bool)
            and reference.version > 0
        )

    @classmethod
    def _is_freezable_value(cls, value: Any, seen: set[int] | None = None) -> bool:
        """Allow only recursively copyable shapes that ``freeze_value`` seals."""

        if isinstance(value, float):
            return math.isfinite(value)
        if isinstance(value, (str, bytes, int, bool, type(None))):
            return True
        if isinstance(value, ArtifactReference):
            return cls._is_valid_reference(value)
        if seen is None:
            seen = set()
        marker = id(value)
        if marker in seen:
            return False
        if isinstance(value, Mapping):
            seen.add(marker)
            result = all(
                cls._is_freezable_value(key, seen)
                and cls._is_freezable_value(item, seen)
                for key, item in value.items()
            )
            seen.remove(marker)
            return result
        if isinstance(value, (list, tuple, set, frozenset)):
            seen.add(marker)
            result = all(cls._is_freezable_value(item, seen) for item in value)
            seen.remove(marker)
            return result
        return False

    @staticmethod
    def _fingerprint(candidate: ArtifactCandidate) -> Any:
        return (
            candidate.artifact_type,
            candidate.identity,
            freeze_value(candidate.payload),
            tuple(freeze_value(item) for item in candidate.provenance or ()),
            tuple(candidate.dependencies or ()),
            candidate.prior_reference,
        )
