"""Core value objects for the Artifact Commit boundary.

These objects deliberately contain no workflow or storage implementation
details.  A candidate is an input proposal; an artifact version is a committed
business fact addressed by an exact reference.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ArtifactReference:
    """An exact, immutable address for one Artifact Version."""

    artifact_type: str
    identity: str
    version: int


@dataclass(frozen=True, slots=True)
class ArtifactCandidate:
    """A producer's proposed Artifact Version, before boundary validation."""

    artifact_type: str
    identity: str
    payload: Any
    provenance: tuple[Any, ...] | None = field(default_factory=tuple)
    dependencies: tuple[ArtifactReference, ...] | None = field(default_factory=tuple)
    validated: bool = False
    commit_id: str = ""
    prior_reference: ArtifactReference | None = None

    def __post_init__(self) -> None:
        # Freeze the collection boundary while leaving payload as producer-owned
        # input.  Commit takes an independent immutable snapshot of the payload.
        if self.provenance is not None and not isinstance(self.provenance, tuple):
            object.__setattr__(self, "provenance", tuple(self.provenance))
        if self.dependencies is not None and not isinstance(self.dependencies, tuple):
            object.__setattr__(self, "dependencies", tuple(self.dependencies))

    @property
    def logical_commit_id(self) -> str:
        """Readable alias for the logical id used for idempotent Commit."""

        return self.commit_id


@dataclass(frozen=True, slots=True)
class ArtifactVersion:
    """An immutable committed Artifact Version."""

    reference: ArtifactReference
    payload: Any
    provenance: tuple[Any, ...]
    dependencies: tuple[ArtifactReference, ...]
    commit_id: str
    prior_reference: ArtifactReference | None = None

    @property
    def artifact_type(self) -> str:
        return self.reference.artifact_type

    @property
    def identity(self) -> str:
        return self.reference.identity

    @property
    def version(self) -> int:
        return self.reference.version


def freeze_value(value: Any) -> Any:
    """Return a recursively detached, read-only snapshot for common payloads.

    Artifact payloads are intentionally kept provider- and storage-neutral.  The
    supported container shapes are copied recursively so caller-owned mappings,
    sequences and sets cannot mutate a committed Version.
    """

    if isinstance(value, Mapping):
        frozen = {freeze_value(key): freeze_value(item) for key, item in value.items()}
        return MappingProxyType(frozen)
    if isinstance(value, (list, tuple)):
        return tuple(freeze_value(item) for item in value)
    if isinstance(value, (set, frozenset)):
        return frozenset(freeze_value(item) for item in value)
    if isinstance(value, (str, bytes, int, float, bool, type(None))):
        return value
    # Detach non-container values as a conservative boundary.  The public
    # contract does not depend on their concrete runtime type.
    return deepcopy(value)
