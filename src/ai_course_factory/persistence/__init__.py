"""Persistence adapters for durable local task state and workspace blobs."""

from .workspace import (
    FilesystemWorkspace,
    TaskWorkspace,
    WorkspaceAdapter,
    WorkspaceFailure,
    WorkspaceFileRecord,
    WorkspaceFileReference,
)

__all__ = [
    "FilesystemWorkspace", "TaskWorkspace", "WorkspaceAdapter", "WorkspaceFailure",
    "WorkspaceFileRecord", "WorkspaceFileReference",
]
