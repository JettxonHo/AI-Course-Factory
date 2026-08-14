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
class LocalNarrationTask:
    """Provider-independent task for the pre-generation handoff narration."""

    task_id: str
    production_request_reference: ArtifactReference
    scene_id: str
    language: str
    duration_seconds: int | float
    narration: str
    output_reference: WorkspaceFileReference


@dataclass(frozen=True, slots=True)
class LocalNarrationResult:
    """Durable result of one local handoff narration render."""

    task_id: str
    scene_id: str
    output_reference: WorkspaceFileReference
    media_type: str
    duration_seconds: int | float
    result_code: str


@dataclass(frozen=True, slots=True)
class LocalNarrationPreflight:
    """Side-effect-free local narration runtime facts."""

    repository_commit: str
    model_identifier: str
    reference_audio: str
    reference_transcript: str
    engine: str = "local-gpt-sovits-v2"


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
class MediaCompositionScene:
    scene_id: str
    start_milliseconds: int
    end_milliseconds: int
    visual_result: MediaGenerationResult
    voice_result: MediaGenerationResult
    subtitle_text: str


@dataclass(frozen=True, slots=True)
class MediaCompositionTask:
    task_id: str
    composition_id: str
    production_request_reference: ArtifactReference
    timeline_reference: ArtifactReference
    scenes: tuple[MediaCompositionScene, ...]
    output_reference: WorkspaceFileReference


@dataclass(frozen=True, slots=True)
class MediaCompositionResult:
    composition_id: str
    production_request_reference: ArtifactReference
    timeline_reference: ArtifactReference
    scene_ids: tuple[str, ...]
    composer: str
    output_reference: WorkspaceFileReference
    media_type: str
    duration_milliseconds: int
    result_code: str


@dataclass(frozen=True, slots=True)
class ProductionCompositionResult:
    task_id: str
    composition_id: str
    production_request_reference: ArtifactReference
    timeline_reference: ArtifactReference
    scene_clip_references: tuple[ArtifactReference, ...]
    scene_audio_references: tuple[ArtifactReference, ...]
    subtitle_reference: ArtifactReference
    master_audio_reference: ArtifactReference
    video_reference: ArtifactReference
    output_reference: WorkspaceFileReference
    result_code: str


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
    "MediaCompositionResult",
    "MediaCompositionScene",
    "MediaCompositionTask",
    "MediaGenerationResult",
    "LocalNarrationPreflight",
    "LocalNarrationResult",
    "LocalNarrationTask",
    "ProductionCompositionResult",
    "ProductionExecutionResult",
    "ProductionMediaFailure",
    "VisualGenerationTask",
    "VoiceSynthesisTask",
]
