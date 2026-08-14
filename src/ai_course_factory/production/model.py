"""Immutable provider-neutral values for offline media generation."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

from ai_course_factory.artifacts import ArtifactReference, ArtifactVersion
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
class CommittedMediaCompositionScene:
    """One already committed clip/audio pair for the no-attempt path."""

    scene_id: str
    start_milliseconds: int
    end_milliseconds: int
    clip_reference: ArtifactReference
    clip_output_reference: WorkspaceFileReference
    audio_reference: ArtifactReference
    audio_output_reference: WorkspaceFileReference
    subtitle_text: str


@dataclass(frozen=True, slots=True)
class CommittedMediaCompositionTask:
    """Composition inputs whose provenance is committed Artifact state."""

    task_id: str
    composition_id: str
    production_request_reference: ArtifactReference
    timeline_reference: ArtifactReference
    scenes: tuple[CommittedMediaCompositionScene, ...]
    output_reference: WorkspaceFileReference

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenes", tuple(self.scenes))


@dataclass(frozen=True, slots=True)
class CreatorImportedFinalCandidateGateResult:
    """Successful exact lineage resolution for an H3 Final candidate."""

    video_reference: ArtifactReference
    scene_generation_contract_reference: ArtifactReference
    scene_clip_references: tuple[ArtifactReference, ...]
    result_code: str = "SUCCESS"


class CreatorImportedFinalCandidateGate:
    """Resolve the exact six creator-import Clips behind a Video Version."""

    __slots__ = ("_artifacts",)

    def __init__(self, artifact_repository: object) -> None:
        self._artifacts = artifact_repository

    def validate(
        self,
        video_reference: ArtifactReference,
        scene_generation_contract_reference: ArtifactReference,
    ) -> CreatorImportedFinalCandidateGateResult | "ProductionMediaFailure":
        from .model import ProductionMediaFailure  # local for the frozen model module

        failure = lambda code, message: ProductionMediaFailure("validation", code, message)
        if (
            type(video_reference) is not ArtifactReference
            or video_reference.artifact_type != "video"
            or type(scene_generation_contract_reference) is not ArtifactReference
            or scene_generation_contract_reference.artifact_type != "scene_generation_contract"
        ):
            return failure("CREATOR_FINAL_GATE_INVALID_REFERENCE", "exact Final and Scene Generation Contract References are required")
        try:
            video = self._artifacts.get(video_reference)
            contract = self._artifacts.get(scene_generation_contract_reference)
        except Exception:
            return failure("CREATOR_FINAL_GATE_ARTIFACT_NOT_FOUND", "the exact Final or Scene Generation Contract Artifact is unavailable")
        if type(video) is not ArtifactVersion or type(contract) is not ArtifactVersion:
            return failure("CREATOR_FINAL_GATE_ARTIFACT_NOT_FOUND", "the exact Final or Scene Generation Contract Artifact is unavailable")
        payload = video.payload
        contract_payload = contract.payload
        if not isinstance(payload, Mapping) or not isinstance(contract_payload, Mapping):
            return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Video lineage is invalid")
        expected_video_keys = {
            "production_request_reference",
            "timeline_reference",
            "composition_id",
            "scene_ids",
            "scene_clip_references",
            "subtitle_reference",
            "master_audio_reference",
            "composer",
            "output_reference",
            "media_type",
            "duration_milliseconds",
        }
        if set(payload) != expected_video_keys:
            return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Video lineage is invalid")
        clips = payload.get("scene_clip_references")
        scene_ids = payload.get("scene_ids")
        request_reference = payload.get("production_request_reference")
        timeline_reference = payload.get("timeline_reference")
        subtitle_reference = payload.get("subtitle_reference")
        master_audio_reference = payload.get("master_audio_reference")
        contract_entries = contract_payload.get("scene_generation_contract", {}).get("scenes") if isinstance(contract_payload.get("scene_generation_contract"), Mapping) else None
        if (
            type(clips) is not tuple or len(clips) != 6
            or type(scene_ids) is not tuple or scene_ids != tuple(f"scene-{index}" for index in range(1, 7))
            or type(contract_entries) is not tuple or len(contract_entries) != 6
            or type(request_reference) is not ArtifactReference or request_reference.artifact_type != "production_request"
            or type(timeline_reference) is not ArtifactReference or timeline_reference.artifact_type != "timeline"
            or type(subtitle_reference) is not ArtifactReference or subtitle_reference.artifact_type != "subtitle"
            or type(master_audio_reference) is not ArtifactReference or master_audio_reference.artifact_type != "master_audio"
            or type(video.dependencies) is not tuple
            or video.dependencies != (request_reference, timeline_reference, *clips, subtitle_reference, master_audio_reference)
            or payload.get("media_type") != "video/mp4"
            or type(payload.get("duration_milliseconds")) is not int
        ):
            return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Video must bind six ordered creator-import Scene Clips")
        video_output = payload.get("output_reference")
        if (
            not isinstance(video_output, Mapping)
            or set(video_output) != {"task_id", "area", "name"}
            or type(video_output.get("task_id")) is not str
            or not video_output.get("task_id")
            or type(video_output.get("area")) is not str
            or video_output.get("area") != "media"
            or type(video_output.get("name")) is not str
            or not video_output.get("name")
        ):
            return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Video output does not bind a credible media Workspace reference")
        contract_root = contract_payload.get("scene_generation_contract")
        if (
            not isinstance(contract_root, Mapping)
            or contract_payload.get("production_request_reference") != request_reference
            or contract_payload.get("timeline_reference") != timeline_reference
        ):
            return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Video and Contract do not share the exact Request and Timeline")
        expected_duration = 0
        resolved: list[ArtifactReference] = []
        for index, (scene_id, clip_reference, entry) in enumerate(zip(scene_ids, clips, contract_entries, strict=True)):
            if (
                type(clip_reference) is not ArtifactReference
                or clip_reference.artifact_type != "scene_clip"
                or not isinstance(entry, Mapping)
                or entry.get("scene_id") != scene_id
                or type(entry.get("duration_milliseconds")) is not int
            ):
                return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Scene order or Contract entry is invalid")
            try:
                clip = self._artifacts.get(clip_reference)
            except Exception:
                return failure("CREATOR_FINAL_GATE_ARTIFACT_NOT_FOUND", "a selected creator-import Scene Clip is unavailable")
            clip_payload = clip.payload if type(clip) is ArtifactVersion else None
            if (
                type(clip) is not ArtifactVersion or not isinstance(clip_payload, Mapping)
                or set(clip_payload) != {
                    "source_kind",
                    "production_request_reference",
                    "scene_generation_contract_reference",
                    "scene_id",
                    "declared_filename",
                    "creator_provenance",
                    "output_reference",
                    "media_type",
                    "duration_milliseconds",
                }
                or clip_payload.get("source_kind") != "creator_import"
                or clip_payload.get("scene_id") != scene_id
                or clip_payload.get("production_request_reference") != request_reference
                or clip_payload.get("scene_generation_contract_reference") != scene_generation_contract_reference
                or clip_payload.get("duration_milliseconds") != entry.get("duration_milliseconds")
                or clip_payload.get("media_type") != "video/mp4"
                or not isinstance(clip_payload.get("declared_filename"), str)
                or not (
                    clip_payload.get("declared_filename") == entry.get("expected_filename")
                    or (scene_id == "scene-2" and clip_payload.get("declared_filename") == "scene-2-replacement.mp4")
                )
                or not isinstance(clip_payload.get("creator_provenance"), Mapping)
                or clip_payload["creator_provenance"].get("supplied_by") != "creator"
                or clip_payload["creator_provenance"].get("generated_outside_application") is not True
                or clip_payload["creator_provenance"].get("application_provider_attempt") is not False
                or clip_payload["creator_provenance"].get("application_charge_micros") != 0
                or clip_payload["creator_provenance"].get("native_audio/subtitles/effects") != "metadata_only"
                or not isinstance(clip_payload.get("output_reference"), Mapping)
                or set(clip_payload["output_reference"]) != {"task_id", "area", "name"}
                or clip_payload["output_reference"].get("task_id") != video_output["task_id"]
                or clip_payload["output_reference"].get("area") != "media"
                or clip_payload["output_reference"].get("name") != clip_payload.get("declared_filename")
                or clip.dependencies != (request_reference, scene_generation_contract_reference)
            ):
                return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Video contains a legacy, mixed-Contract or misordered Scene Clip")
            expected_duration += entry["duration_milliseconds"]
            resolved.append(clip_reference)
        if payload.get("duration_milliseconds") != expected_duration:
            return failure("CREATOR_FINAL_GATE_LINEAGE_MISMATCH", "Final Video duration does not match the exact Contract timeline")
        return CreatorImportedFinalCandidateGateResult(video_reference, scene_generation_contract_reference, tuple(resolved))


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
    "CommittedMediaCompositionScene",
    "CommittedMediaCompositionTask",
    "CreatorImportedFinalCandidateGateResult",
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
