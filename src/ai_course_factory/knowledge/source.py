"""Provider-neutral Source Acquisition result contracts."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SourceFile:
    """One explicitly requested UTF-8 source file pinned to a commit."""

    path: str
    blob_sha: str
    text: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class SourceAcquisitionResult:
    """Complete immutable acquisition output for one exact repository commit."""

    repository_url: str
    repository_identity: str
    commit_sha: str
    files: tuple[SourceFile, ...]
    total_size_bytes: int


@dataclass(frozen=True, slots=True)
class SourceConnectorFailure:
    """Normalized safe failure; raw response, credentials and stack traces stay out."""

    kind: str
    code: str
    message: str
