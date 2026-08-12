"""Immutable provider-neutral values for offline media generation."""

from __future__ import annotations

from dataclasses import dataclass

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference


@dataclass(frozen=True, slots=True)
class VisualGenerationTask:
    task_id: str
    attempt_id: str
    production_request_reference: ArtifactReference
    scene_id: str
    aspect_ratio: str
    duration_seconds: int | float
    visual_intent: str
    character_action: str
    output_reference: WorkspaceFileReference


@dataclass(frozen=True, slots=True)
class VoiceSynthesisTask:
    task_id: str
    attempt_id: str
    production_request_reference: ArtifactReference
    scene_id: str
    language: str
    duration_seconds: int | float
    narration: str
    output_reference: WorkspaceFileReference


@dataclass(frozen=True, slots=True)
class MediaGenerationResult:
    attempt_id: str
    scene_id: str
    operation: str
    provider: str
    output_reference: WorkspaceFileReference
    media_type: str
    duration_seconds: int | float
    result_code: str


@dataclass(frozen=True, slots=True)
class ProductionMediaFailure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ProductionExecutionResult:
    task_id: str
    attempt_id: str
    production_request_reference: ArtifactReference
    scene_id: str
    operation: str
    provider: str
    output_reference: WorkspaceFileReference
    result_code: str


__all__ = [
    "MediaGenerationResult",
    "ProductionExecutionResult",
    "ProductionMediaFailure",
    "VisualGenerationTask",
    "VoiceSynthesisTask",
]
