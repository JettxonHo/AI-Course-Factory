"""Task-level offline Course Factory application facade.

The facade is the only contract consumed by the local web workspace.  It
coordinates the accepted artifact, decision, workflow, budget, production,
composition and packaging seams while keeping their implementation details
out of the browser-facing view model.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sqlite3
import re
from typing import Any, Mapping

from ai_course_factory.agents import (
    ContentAgent,
    ContentModelRuntimeResult,
    ContentRevisionContext,
    ContentTaskContext,
    EpisodeTemplateConstraint,
    KnowledgeAgent,
    KnowledgeTaskContext,
    ModelRuntimeRequest,
    ModelRuntimeResult,
    ProductionAgent,
    ProductionAgentFailure,
    ProductionModelRuntimeResult,
    ProductionRequestModelRuntimeResult,
    SceneGenerationContractFailure,
    SceneGenerationContractPlanner,
    StoryboardModelRuntimeResult,
    TimelineModelRuntimeResult,
)
from ai_course_factory.artifacts import (
    ArtifactReference,
    ArtifactVersion,
    FinalVideoDecisionBoundary,
    SQLiteArtifactRepository,
    SQLiteFinalVideoDecisionRepository,
    SQLiteScriptDecisionRepository,
    SQLiteStoryboardDecisionRepository,
    ScriptDecisionRecord,
    ScriptDecisionBoundary,
    StoryboardDecisionBoundary,
    StoryboardDecisionRecord,
)
from ai_course_factory.knowledge import (
    GitHubSourceConnector,
    NormalizationFailure,
    SourceAcquisitionResult,
    SourceConnectorFailure,
    SourceNormalizer,
    SourceRecordBuilder,
)
from ai_course_factory.packaging import (
    CreatorHandoffPackageBuilder,
    HandoffPackageFailure,
    HandoffPackageResult,
    PackagingFailure,
    PublishPackageBuilder,
    PublishPackageResult,
)
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetDecisionOutcome,
    BudgetFailure,
    FFmpegFixtureVisualGenerator,
    FFmpegFixtureVoiceGenerator,
    FFmpegMediaComposer,
    GPT_SOVITS_PROVIDER,
    GPTSoVITSConfiguration,
    GPTSoVITSSyntheticVoiceGenerator,
    LocalNarrationRenderer,
    LOCAL_IMPORTED_PROVIDER,
    LocalImportedVisualGenerator,
    MediaCompositionScene,
    MediaCompositionTask,
    MediaGenerationResult,
    PriceLineItem,
    PriceSnapshot,
    ProductionCompositionResult,
    ProductionExecutionResult,
    ProductionMediaFailure,
    ProductionOrchestrator,
    ProviderAttemptLedger,
    ProviderAttemptFailure,
    ProviderAttemptReservation,
    ProviderAttemptRecord,
    SQLiteBudgetAuthorizationRepository,
    SQLiteProviderAttemptRepository,
    VisualGenerationTask,
    VoiceSynthesisTask,
)
from ai_course_factory.workflow import (
    FinalVideoReviewWorkflow,
    SQLiteCheckpointAdapter,
    ScriptReviewWorkflow,
)
from .final_video_review import FinalVideoReviewApplicationService
from .media_task import (
    TaskMediaProjectionService,
    TaskMediaSnapshot,
)
from .sqlite_media_task import SQLiteTaskMediaRepository
from .script_review import ScriptReviewApplicationService


TASK_ID = "demo-episode-01"
THREAD_ID = "demo-episode-01-script"
FINAL_THREAD_ID = "demo-episode-01-final"
CREATOR_ID = "creator-local"
REPOSITORY_URL = "https://github.com/microsoft/AI-For-Beginners"
SOURCE_PATH = "lessons/1-Intro/README.md"
SCENE_IDS = tuple(f"scene-{index}" for index in range(1, 7))
_SUBTITLE_OUTPUT = WorkspaceFileReference(TASK_ID, "media", "subtitles.srt")
_STATE_SCHEMA = 1


def _script_thread(reference: ArtifactReference) -> str:
    return f"{THREAD_ID}-v{reference.version}"


def _final_thread(reference: ArtifactReference) -> str:
    return f"{FINAL_THREAD_ID}-v{reference.version}"


def _script_decision_id(reference: ArtifactReference, action: str) -> str:
    return f"decision:script:v{reference.version}:{action}"


def _final_decision_id(reference: ArtifactReference, action: str) -> str:
    return f"decision:final:v{reference.version}:{action}"


def _storyboard_decision_id(reference: ArtifactReference, action: str) -> str:
    return f"decision:storyboard:v{reference.version}:{action}"


def _failure_category(code: str | None) -> str | None:
    if not code:
        return None
    upper = code.upper()
    if "BUDGET" in upper or "AUTHORIZATION" in upper or "ATTEMPT_LIMIT" in upper:
        return "budget_limit"
    if "QUALITY" in upper or "FINAL_VIDEO" in upper or "HARD_BLOCK" in upper:
        return "quality_failure"
    if "GENERATION" in upper or "MEDIA" in upper or "FFMPEG" in upper or "COMPOSITION" in upper or "PRODUCTION_FAILED" in upper or "REPLACEMENT" in upper:
        return "generation_failure"
    return "provider_error"


def _safe_failure_message(category: str | None) -> str:
    return {
        "budget_limit": "The approved budget or attempt limit prevented this action.",
        "quality_failure": "The evidence did not pass the current quality gate.",
        "generation_failure": "Local media generation failed; no new delivery was accepted.",
        "provider_error": "The production operation could not be completed safely.",
    }.get(category, "That action could not be completed. The current task state was preserved.")


def _safe_actionable_failure(code: str, category: str | None, detail: str | None) -> str:
    if code.startswith("LOCAL_IMPORT"):
        allowed = set(re.findall(r"scene-(?:[1-6](?:-replacement)?|2-replacement)\.png", detail or ""))
        if allowed:
            names = tuple(name for name in (*tuple(f"scene-{index}.png" for index in range(1, 7)), "scene-2-replacement.png") if name in allowed)
            return f"Local visual import requires valid PNG/JPEG files: {', '.join(names)}."
        if code == "LOCAL_IMPORT_DIRECTORY_REQUIRED":
            return "An explicit local visual import directory is required."
    return _safe_failure_message(category)


def _prompt_cards(script_scenes: object, production_scenes: object = None) -> tuple[PromptCard, ...]:
    if type(script_scenes) is not tuple or len(script_scenes) != 6:
        return ()
    style = "9:16 vertical educational illustration; keep the friendly 小土豆 character and blue scarf consistent across all scenes"
    cards: list[PromptCard] = []
    production_by_id = {
        scene.get("scene_id"): scene
        for scene in production_scenes
        if isinstance(scene, Mapping) and type(scene.get("scene_id")) is str
    } if type(production_scenes) is tuple else {}
    for index, scene in enumerate(script_scenes, start=1):
        if not isinstance(scene, Mapping):
            return ()
        scene_id = scene.get("scene_id")
        planned = production_by_id.get(scene.get("scene_id"), {})
        intent = planned.get("visual_intent", scene.get("teaching_intent", ""))
        action = planned.get("character_action", "挥手。" if index % 2 else "转身。")
        if type(scene_id) is not str or type(intent) is not str:
            return ()
        target = f"scene-{index}.png"
        prompt = (
            f"{scene_id} | target filename: {target}. {style}. "
            f"Scene intent: {intent}. Character action: {action}. "
            "No text, no watermark."
        )
        cards.append(PromptCard(scene_id, target, style, intent, action, prompt))
    return tuple(cards)


@dataclass(frozen=True, slots=True)
class SceneView:
    scene_id: str
    narration: str
    visual_intent: str
    selected_clip_reference: ArtifactReference | None = None
    selected_audio_reference: ArtifactReference | None = None
    status: str = "planned"


@dataclass(frozen=True, slots=True)
class PromptCard:
    """Frozen, copyable prompt guidance for one exact imported image."""

    scene_id: str
    target_filename: str
    style_character_continuity: str
    scene_intent: str
    character_action: str
    prompt: str


@dataclass(frozen=True, slots=True)
class GenerationEntryView:
    """Small provider-neutral projection for one contract Scene entry."""

    scene_id: str
    duration_milliseconds: int
    narration_identity: str
    narration: str
    visual_intent: str
    character_action: str
    continuity_notes: tuple[str, ...]
    generation_prompt: str
    camera_motion_instruction: str
    negative_constraints: tuple[str, ...]
    expected_filename: str


@dataclass(frozen=True, slots=True)
class ApplicationView:
    task_id: str
    stage: str
    pending_action: str | None
    source_commit: str
    source_locator: str
    source_evidence: tuple[str, ...]
    script_reference: ArtifactReference
    scenes: tuple[SceneView, ...]
    budget_maximum_amount_micros: int | None = None
    budget_maximum_attempts: int | None = None
    budget_approved: bool = False
    video_reference: ArtifactReference | None = None
    subtitle_reference: ArtifactReference | None = None
    package_reference: ArtifactReference | None = None
    package_output: WorkspaceFileReference | None = None
    failure_category: str | None = None
    failure_message: str | None = None
    available_actions: tuple[str, ...] = ()
    offline: bool = True
    replacement_done: bool = False
    provider_attempt_count: int = 0
    provider_attempt_statuses: tuple[str, ...] = ()
    provider_attempt_charged_amount_micros: int = 0
    local_replacement_label: str | None = None
    prompt_cards: tuple[PromptCard, ...] = ()
    visual_mode: str = "fixture"
    tts_engine: str | None = None
    tts_reference_provenance: str | None = None
    tts_external_charge_micros: int | None = None
    storyboard_reference: ArtifactReference | None = None
    scene_generation_contract_reference: ArtifactReference | None = None
    generation_entries: tuple[GenerationEntryView, ...] = ()
    timeline_reference: ArtifactReference | None = None
    production_request_reference: ArtifactReference | None = None
    storyboard_decision_context: str | None = None
    handoff_package_reference: ArtifactReference | None = None
    handoff_package_output: WorkspaceFileReference | None = None
    handoff_narration_references: tuple[WorkspaceFileReference, ...] = ()
    handoff_reference_still_facts: tuple[str, ...] = ()
    external_generation_notice: str | None = None


@dataclass(frozen=True, slots=True)
class ApplicationResult:
    status: str
    view: ApplicationView | None = None
    error_code: str | None = None
    error_message: str | None = None
    package: PublishPackageResult | None = None


@dataclass(frozen=True, slots=True)
class ApplicationDownload:
    """A bounded file response exposed to the local web workspace."""

    content: bytes
    media_type: str
    filename: str


@dataclass(frozen=True, slots=True)
class _State:
    task_id: str
    stage: str
    pending_action: str | None
    refs: Mapping[str, ArtifactReference]
    decision_ids: Mapping[str, str]
    authorization_id: str | None = None
    composition: Mapping[str, Any] | None = None
    package_output: WorkspaceFileReference | None = None
    failure_category: str | None = None
    failure_message: str | None = None
    replacement_done: bool = False
    visual_mode: str = "fixture"
    tts_mode: str = "fixture"
    handoff_package_output: WorkspaceFileReference | None = None
    handoff_narration_references: tuple[WorkspaceFileReference, ...] = ()
    handoff_reference_still_facts: tuple[str, ...] = ()


class _OfflineRuntime:
    def invoke(self, request: ModelRuntimeRequest) -> object:
        if request.purpose == "knowledge_generation":
            units = request.source_record_payload["units"]
            locator = units[0]["locator"]
            return ModelRuntimeResult(
                repository_summary="The source lesson explains that AI is not magic.",
                lesson_focus="Lesson 1 introduces AI as a practical tool.",
                claims=(
                    {
                        "claim_id": "claim-ai-is-not-magic",
                        "statement": "AI is not magic.",
                        "confidence": 0.99,
                        "evidence_locators": (locator,),
                    },
                ),
            )
        if request.purpose == "content_planning":
            return ContentModelRuntimeResult(
                content={
                    "course_plan": {
                        "course_goal": "Build an intuitive AI foundation.",
                        "topics": ("AI concepts", "AI is not magic"),
                        "knowledge_claim_ids": ("claim-ai-is-not-magic",),
                    },
                    "episode_plan": {
                        "title": "AI不是魔法",
                        "episode_number": 1,
                        "learning_goal": "Explain why AI is not magic.",
                        "scene_outline": ("Hook", "Question", "Example", "Explanation", "Takeaway", "Close"),
                        "knowledge_claim_ids": ("claim-ai-is-not-magic",),
                    },
                }
            )
        if request.purpose == "content_scripting":
            revision = request.constraints.get("revision_context")
            prefix = "修订版：" if revision is not None else ""
            return ContentModelRuntimeResult(
                content={
                    "script": {
                        "duration_seconds": 60,
                        "aspect_ratio": "9:16",
                        "scenes": tuple(
                            {
                                "scene_id": scene_id,
                                "duration_seconds": 10,
                                "narration": f"{prefix}第{index}幕：人工智能不是魔法。",
                                "teaching_intent": f"用第{index}幕说明人工智能不是魔法。",
                                "knowledge_claim_ids": ("claim-ai-is-not-magic",),
                            }
                            for index, scene_id in enumerate(SCENE_IDS, start=1)
                        ),
                    }
                }
            )
        if request.purpose == "character_planning":
            return ProductionModelRuntimeResult(
                character={
                    "name": "小土豆",
                    "design_version": "v1.0",
                    "summary": "A friendly potato teacher.",
                    "visual_traits": ("round potato silhouette", "blue scarf"),
                    "personality_traits": ("curious", "encouraging"),
                    "continuity_rules": ("keep the blue scarf visible",),
                }
            )
        if request.purpose == "storyboard_planning":
            scenes = request.inputs["script_payload"]["scenes"]
            return StoryboardModelRuntimeResult(
                storyboard={
                    "aspect_ratio": "9:16",
                    "scenes": tuple(
                        {
                            "scene_id": scene["scene_id"],
                            "visual_intent": f"展示小土豆讲解第{index}幕。",
                            "character_action": "挥手。" if index % 2 else "转身。",
                            "continuity_notes": ("保持蓝色围巾可见。",),
                        }
                        for index, scene in enumerate(scenes, start=1)
                    ),
                }
            )
        if request.purpose == "timeline_planning":
            start = 0.0
            scenes = []
            for scene in request.inputs["script_payload"]["scenes"]:
                end = start + scene["duration_seconds"]
                scenes.append({"scene_id": scene["scene_id"], "start_seconds": start, "duration_seconds": scene["duration_seconds"], "end_seconds": end})
                start = end
            return TimelineModelRuntimeResult(timeline={"duration_seconds": start, "scenes": tuple(scenes)})
        if request.purpose == "production_request_planning":
            script = request.inputs["script_payload"]
            storyboard = request.inputs["storyboard_payload"]["storyboard"]["scenes"]
            timeline = request.inputs["timeline_payload"]["timeline"]["scenes"]
            scenes = tuple(
                {
                    **timing,
                    "narration": script_scene["narration"],
                    "visual_intent": board_scene["visual_intent"],
                    "character_action": board_scene["character_action"],
                    "continuity_notes": board_scene["continuity_notes"],
                }
                for script_scene, board_scene, timing in zip(script["scenes"], storyboard, timeline, strict=True)
            )
            return ProductionRequestModelRuntimeResult(
                production_request={
                    "language": "Simplified Chinese",
                    "aspect_ratio": "9:16",
                    "duration_seconds": script["duration_seconds"],
                    "scenes": scenes,
                }
            )
        raise ValueError("unsupported offline runtime purpose")


def _ref_json(reference: ArtifactReference) -> dict[str, object]:
    return {"artifact_type": reference.artifact_type, "identity": reference.identity, "version": reference.version}


def _ref_from(value: object) -> ArtifactReference:
    if not isinstance(value, dict) or set(value) != {"artifact_type", "identity", "version"}:
        raise ValueError
    return ArtifactReference(value["artifact_type"], value["identity"], value["version"])


def _workspace_json(reference: WorkspaceFileReference) -> dict[str, str]:
    return {"task_id": reference.task_id, "area": reference.area, "name": reference.name}


def _workspace_from(value: object) -> WorkspaceFileReference:
    if not isinstance(value, dict) or set(value) != {"task_id", "area", "name"}:
        raise ValueError
    return WorkspaceFileReference(value["task_id"], value["area"], value["name"])


def _media_result_json(result: MediaGenerationResult) -> dict[str, object]:
    return {
        "attempt_id": result.attempt_id,
        "scene_id": result.scene_id,
        "operation": result.operation,
        "provider": result.provider,
        "output_reference": _workspace_json(result.output_reference),
        "media_type": result.media_type,
        "duration_seconds": result.duration_seconds,
        "result_code": result.result_code,
    }


def _media_result_from(value: object) -> MediaGenerationResult:
    if not isinstance(value, dict):
        raise ValueError
    return MediaGenerationResult(
        value["attempt_id"], value["scene_id"], value["operation"], value["provider"],
        _workspace_from(value["output_reference"]), value["media_type"], value["duration_seconds"], value["result_code"],
    )


def _srt_timestamp(milliseconds: object) -> str:
    if type(milliseconds) is not int or milliseconds < 0:
        raise ValueError
    seconds, millis = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _subtitle_bytes(version: ArtifactVersion) -> bytes:
    payload = version.payload
    cues = payload.get("cues") if isinstance(payload, Mapping) else None
    if type(cues) is not tuple or not cues:
        raise ValueError
    lines: list[str] = []
    for index, cue in enumerate(cues, start=1):
        if not isinstance(cue, Mapping):
            raise ValueError
        start = _srt_timestamp(cue.get("start_milliseconds"))
        end = _srt_timestamp(cue.get("end_milliseconds"))
        text = cue.get("text")
        if type(text) is not str or not text.strip() or any(char in text for char in "\r\n"):
            raise ValueError
        lines.extend((str(index), f"{start} --> {end}", text, ""))
    return "\n".join(lines).encode("utf-8")


class CourseFactoryApplication:
    """Durable one-task offline application facade used by the web workspace."""

    def __init__(
        self,
        data_dir: str | Path,
        *,
        ffmpeg_executable: str | None = None,
        ffprobe_executable: str | None = None,
        visual_import_dir: str | Path | None = None,
        tts_configuration: GPTSoVITSConfiguration | None = None,
        source_connector: object | None = None,
        local_narration_renderer: LocalNarrationRenderer | None = None,
    ) -> None:
        self.data_dir = Path(data_dir).expanduser().resolve()
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_root = self.data_dir / "workspace"
        self.workspace = FilesystemWorkspace(self.workspace_root)
        self.database_path = self.data_dir / "factory.sqlite3"
        self._state_connection = sqlite3.connect(self.database_path, isolation_level=None, check_same_thread=False)
        self._state_connection.execute("CREATE TABLE IF NOT EXISTS application_state (singleton INTEGER PRIMARY KEY CHECK(singleton=1), schema_version INTEGER NOT NULL, state_json TEXT NOT NULL)")
        self.artifacts = SQLiteArtifactRepository(self.database_path)
        self.script_decisions = SQLiteScriptDecisionRepository(self.database_path)
        self.storyboard_decisions = SQLiteStoryboardDecisionRepository(self.database_path)
        self.final_decisions = SQLiteFinalVideoDecisionRepository(self.database_path)
        self.budget_decisions = SQLiteBudgetAuthorizationRepository(self.database_path)
        self.attempts = SQLiteProviderAttemptRepository(self.database_path)
        self.media_repository = SQLiteTaskMediaRepository(self.database_path)
        self.checkpoints = SQLiteCheckpointAdapter(self.database_path)
        self.ffmpeg_executable = ffmpeg_executable or shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        self.ffprobe_executable = ffprobe_executable or shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
        self.tts_configuration = tts_configuration
        self.local_narration_renderer = local_narration_renderer
        # Production uses the real, read-only GitHub connector. Tests and
        # deterministic local acceptance inject an explicit source boundary.
        self.source_connector = source_connector if source_connector is not None else GitHubSourceConnector()
        try:
            self.visual_import_dir = Path(visual_import_dir).expanduser().resolve() if visual_import_dir is not None else None
        except (OSError, TypeError, ValueError):
            # Preserve explicit-but-invalid import mode so it fails closed at
            # preflight instead of silently falling back to Fixture visuals.
            self.visual_import_dir = Path("\0") if visual_import_dir is not None else None

    def close(self) -> None:
        for value in (self.checkpoints, self.media_repository, self.attempts, self.budget_decisions, self.final_decisions, self.storyboard_decisions, self.script_decisions, self.artifacts):
            close = getattr(value, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass
        try:
            self._state_connection.close()
        except Exception:
            pass

    def __enter__(self) -> "CourseFactoryApplication":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def create_or_open(self) -> ApplicationResult:
        try:
            state = self._load_state()
            if state is None:
                return ApplicationResult("source_required")
            return self._success(state)
        except Exception:
            return self._failure("APPLICATION_OPEN_FAILED")

    def inspect(self) -> ApplicationResult:
        return self.create_or_open()

    def start_source(self, repository_url: str) -> ApplicationResult:
        """Acquire and initialize the one supported public source exactly once."""
        try:
            existing = self._load_state()
        except Exception:
            return self._failure("APPLICATION_OPEN_FAILED")
        if existing is not None:
            return self._success(existing)
        if not isinstance(repository_url, str):
            return ApplicationResult(
                "failure", None, "INVALID_REPOSITORY_URL", "Enter the supported public GitHub repository URL and retry."
            )
        if repository_url != REPOSITORY_URL:
            return ApplicationResult(
                "failure", None, "UNSUPPORTED_REPOSITORY", f"Only {REPOSITORY_URL} is supported in this local Demo."
            )
        try:
            acquire = getattr(self.source_connector, "acquire", None)
            if not callable(acquire):
                return ApplicationResult("failure", None, "SOURCE_CONNECTOR_UNAVAILABLE", "The GitHub source connector is unavailable; retry the source start.")
            acquisition = acquire(repository_url, [SOURCE_PATH])
        except Exception:
            return ApplicationResult("failure", None, "SOURCE_ACQUISITION_FAILED", "GitHub source acquisition failed; check connectivity and retry.")
        if isinstance(acquisition, SourceConnectorFailure):
            return ApplicationResult("failure", None, acquisition.code, "GitHub source acquisition failed; check connectivity and retry.")
        if not isinstance(acquisition, SourceAcquisitionResult):
            return ApplicationResult("failure", None, "SOURCE_ACQUISITION_FAILED", "GitHub source acquisition failed; check connectivity and retry.")
        try:
            material = SourceNormalizer().normalize(acquisition)
            if isinstance(material, NormalizationFailure):
                return ApplicationResult("failure", None, material.code, "The acquired source could not be validated; retry the source start.")
            state = self._initialize_demo(material)
            return self._success(state)
        except Exception:
            return ApplicationResult("failure", None, "SOURCE_INITIALIZATION_FAILED", "The source could not be initialized safely; retry the source start.")

    def read_output(self, kind: str) -> ApplicationDownload | None:
        """Read one current video, subtitle, or exported package by role."""
        if kind not in {"video", "subtitle", "package", "handoff_package"}:
            return None
        state = self._load_state()
        if state is None:
            return None
        try:
            version: ArtifactVersion | None = None
            if kind == "handoff_package":
                reference = state.handoff_package_output
                if reference is None and state.refs.get("handoff_package") is not None:
                    handoff = self.artifacts.get(state.refs["handoff_package"])
                    payload = handoff.payload if isinstance(handoff, ArtifactVersion) else None
                    output_payload = payload.get("output_reference") if isinstance(payload, Mapping) else None
                    reference = _workspace_from(dict(output_payload)) if isinstance(output_payload, Mapping) else None
                media_type = "application/zip"
                filename = "creator-handoff-package.zip"
            elif kind == "package":
                reference = state.package_output
                media_type = "application/zip"
                filename = "episode-01.zip"
            else:
                snapshot = self._media_snapshot()
                role = "video" if kind == "video" else "subtitle"
                selection = next(
                    (item for item in snapshot.delivery_selections if item.role == role and item.status == "current"),
                    None,
                )
                reference = None
                if selection is not None:
                    artifact_reference = selection.reference
                    expected_type = "video" if role == "video" else "subtitle"
                    if (
                        type(artifact_reference) is not ArtifactReference
                        or artifact_reference.artifact_type != expected_type
                    ):
                        return None
                    version = self.artifacts.get(artifact_reference)
                    if type(version) is not ArtifactVersion or version.reference != artifact_reference:
                        return None
                    payload = version.payload
                    if role == "video":
                        output_payload = payload.get("output_reference") if isinstance(payload, Mapping) else None
                        if not isinstance(output_payload, Mapping):
                            return None
                        reference = _workspace_from(dict(output_payload))
                    else:
                        output_payload = payload.get("output_reference") if isinstance(payload, Mapping) else None
                        reference = _workspace_from(dict(output_payload)) if isinstance(output_payload, Mapping) else _SUBTITLE_OUTPUT
                media_type = "video/mp4" if kind == "video" else "application/x-subrip; charset=utf-8"
                filename = "episode-01.mp4" if kind == "video" else "episode-01.srt"
            if reference is None:
                return None
            if kind == "subtitle":
                if version is None:
                    return None
                rendered = _subtitle_bytes(version)
                stored = self.workspace.commit(reference, rendered)
                if not hasattr(stored, "reference"):
                    return None
                content = self.workspace.read(reference)
            else:
                content = self.workspace.read(reference)
            if not isinstance(content, bytes):
                return None
            return ApplicationDownload(content, media_type, filename)
        except Exception:
            return None

    def submit_script_decision(self, action: str, *, decision_context: str = "", creator_id: str = CREATOR_ID) -> ApplicationResult:
        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.stage != "script_review" or state.pending_action != "approve_script":
            return self._failure("GATE_NOT_PENDING", state)
        if action not in {"approve", "revise", "reject"}:
            return self._failure("INVALID_DECISION_ACTION", state)
        if action in {"revise", "reject"} and not decision_context.strip():
            return self._failure("INVALID_DECISION_CONTEXT", state)
        script = state.refs["script"]
        thread_id = _script_thread(script)
        service = ScriptReviewApplicationService(
            self.artifacts,
            ScriptDecisionBoundary(self.script_decisions),
            ScriptReviewWorkflow(self.artifacts, self.checkpoints),
        )
        result = service.start(TASK_ID, thread_id, script)
        if result.status == "failure":
            return self._failure(result.error_code or "SCRIPT_REVIEW_FAILED", state, result.error_message)
        decision_id = _script_decision_id(script, action)
        result = service.decide(TASK_ID, thread_id, decision_id, creator_id, action, script, decision_context)
        if result.status == "failure":
            return self._failure(result.error_code or "SCRIPT_REVIEW_FAILED", state, result.error_message)
        if action == "approve":
            updated = _State(TASK_ID, "planning", "advance_planning", state.refs, {**state.decision_ids, "script": decision_id}, state.authorization_id, state.composition, state.package_output, None, None, state.replacement_done, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return self._success(updated)
        try:
            revision = ContentRevisionContext(
                prior_reference=script,
                prior_version=self.artifacts.get(script),
                creator_decision_id=decision_id,
                instruction=decision_context,
            )
            runtime = _OfflineRuntime()
            candidate = ContentAgent(runtime).script(
                state.refs["knowledge"], self.artifacts.get(state.refs["knowledge"]),
                state.refs["course_plan"], self.artifacts.get(state.refs["course_plan"]),
                state.refs["episode_plan"], self.artifacts.get(state.refs["episode_plan"]),
                context=ContentTaskContext("adult AI beginners", "小土豆学 AI", 1, "AI不是魔法", "Simplified Chinese", "Explain why AI is not magic."),
                template=EpisodeTemplateConstraint(6, 60, "9:16"),
                script_identity=script.identity,
                script_commit_id=f"script:episode-1:v{script.version + 1}",
                revision=revision,
            )
            revised_reference = self.artifacts.commit(candidate)
            revised_thread = _script_thread(revised_reference)
            started = service.start(TASK_ID, revised_thread, revised_reference)
            if started.status == "failure":
                return self._failure(started.error_code or "SCRIPT_REVIEW_FAILED", state, started.error_message)
            refs = {**state.refs, "script": revised_reference}
            updated = _State(TASK_ID, "script_review", "approve_script", refs, {**state.decision_ids, "script": decision_id, "script_revision": decision_id}, state.authorization_id, state.composition, state.package_output, None, None, state.replacement_done, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("SCRIPT_REVISION_FAILED", state)

    def advance_planning(self) -> ApplicationResult:
        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.stage != "planning" or state.pending_action != "advance_planning":
            return self._failure("PLANNING_NOT_READY", state)
        try:
            script_reference = state.refs["script"]
            script = self.artifacts.get(script_reference)
            script_decision = self.script_decisions.get(state.decision_ids["script"])
            if not isinstance(script_decision, ScriptDecisionRecord) or script_decision.action != "approve":
                return self._failure("SCRIPT_APPROVAL_REQUIRED", state)
            runtime = _OfflineRuntime()
            production = ProductionAgent(runtime)
            revision_suffix = "" if script_reference.version == 1 else f":v{script_reference.version}"
            character_candidate = production.plan_character(script_reference, script, script_decision, constraints={"name": "小土豆", "design_version": "v1.0"}, character_identity=f"character:episode-1{revision_suffix}", character_commit_id=f"character-{script_reference.version}")
            character_reference = self.artifacts.commit(character_candidate)
            character = self.artifacts.get(character_reference)
            storyboard_candidate = production.plan_storyboard(script_reference, script, script_decision, character_reference, character, constraints={"aspect_ratio": "9:16"}, storyboard_identity=f"storyboard:episode-1{revision_suffix}", storyboard_commit_id=f"storyboard-{script_reference.version}")
            storyboard_reference = self.artifacts.commit(storyboard_candidate)
            refs = {**state.refs, "character": character_reference, "storyboard": storyboard_reference}
            updated = _State(TASK_ID, "planning", "approve_storyboard", refs, state.decision_ids, None, None, None, None, None, state.replacement_done, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("PLANNING_FAILED", state)

    def submit_storyboard_decision(
        self,
        action: str,
        *,
        decision_context: str = "",
        creator_id: str = CREATOR_ID,
    ) -> ApplicationResult:
        """Record the explicit Storyboard decision and, on approve, build H1 facts."""

        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        # A completed approval is a durable replay boundary.  Repeated POSTs,
        # refreshes and process restarts return the same exact refs without
        # invoking planners or committing another Version.
        if state.stage == "handoff_readiness" and state.pending_action is None and action == "approve":
            return self._success(state)
        if state.stage != "planning" or state.pending_action != "approve_storyboard":
            return self._failure("STORYBOARD_GATE_NOT_PENDING", state)
        if action not in {"approve", "reject"}:
            return self._failure("INVALID_DECISION_ACTION", state)
        try:
            storyboard_reference = state.refs["storyboard"]
            script_reference = state.refs["script"]
            character_reference = state.refs["character"]
            revision_suffix = "" if script_reference.version == 1 else f":v{script_reference.version}"
            script = self.artifacts.get(script_reference)
            character = self.artifacts.get(character_reference)
            storyboard = self.artifacts.get(storyboard_reference)
            script_decision = self.script_decisions.get(state.decision_ids["script"])
            if not isinstance(script_decision, ScriptDecisionRecord) or script_decision.action != "approve":
                return self._failure("SCRIPT_APPROVAL_REQUIRED", state)
            decision_id = _storyboard_decision_id(storyboard_reference, action)
            decision = StoryboardDecisionBoundary(self.storyboard_decisions).decide(
                storyboard_reference,
                storyboard,
                review_enabled=True,
                decision_id=decision_id,
                task_id=TASK_ID,
                thread_id=THREAD_ID,
                creator_id=creator_id,
                action=action,
                decision_context=decision_context,
            )
            if not isinstance(decision, StoryboardDecisionRecord):
                return self._failure(getattr(decision, "code", "STORYBOARD_DECISION_FAILED"), state, getattr(decision, "message", None))
            if action == "reject":
                updated = _State(
                    TASK_ID,
                    "planning",
                    "approve_storyboard",
                    state.refs,
                    {**state.decision_ids, "storyboard": decision.decision_id},
                    state.authorization_id,
                    state.composition,
                    state.package_output,
                    None,
                    None,
                    state.replacement_done,
                    state.visual_mode,
                    state.tts_mode,
                )
                self._save_state(updated)
                return self._success(updated)

            production = ProductionAgent(_OfflineRuntime())
            timeline_candidate = production.plan_timeline(
                script_reference,
                script,
                script_decision,
                character_reference,
                character,
                storyboard_reference,
                storyboard,
                decision,
                timeline_identity=f"timeline:episode-1{revision_suffix}",
                timeline_commit_id=f"timeline-{script_reference.version}",
            )
            if isinstance(timeline_candidate, ProductionAgentFailure):
                return self._failure(timeline_candidate.code, state, timeline_candidate.message)
            timeline_reference = self.artifacts.commit(timeline_candidate)
            timeline = self.artifacts.get(timeline_reference)
            request_candidate = production.plan_request(
                script_reference,
                script,
                script_decision,
                character_reference,
                character,
                storyboard_reference,
                storyboard,
                decision,
                timeline_reference,
                timeline,
                request_identity=f"production-request:episode-1{revision_suffix}",
                request_commit_id=f"production-request-{script_reference.version}",
            )
            if isinstance(request_candidate, ProductionAgentFailure):
                return self._failure(request_candidate.code, state, request_candidate.message)
            request_reference = self.artifacts.commit(request_candidate)
            request = self.artifacts.get(request_reference)
            contract_candidate = SceneGenerationContractPlanner().plan(
                script_reference,
                script,
                script_decision,
                character_reference,
                character,
                storyboard_reference,
                storyboard,
                decision,
                timeline_reference,
                timeline,
                request_reference,
                request,
                contract_identity=f"scene-generation-contract:episode-1{revision_suffix}",
                contract_commit_id=f"scene-generation-contract-{script_reference.version}",
            )
            if isinstance(contract_candidate, SceneGenerationContractFailure):
                return self._failure(contract_candidate.code, state, contract_candidate.message)
            contract_reference = self.artifacts.commit(contract_candidate)
            refs = {
                **state.refs,
                "storyboard": storyboard_reference,
                "timeline": timeline_reference,
                "production_request": request_reference,
                "scene_generation_contract": contract_reference,
            }
            updated = _State(
                TASK_ID,
                "handoff_readiness",
                None,
                refs,
                {**state.decision_ids, "storyboard": decision.decision_id},
                None,
                None,
                None,
                None,
                None,
                state.replacement_done,
                state.visual_mode,
                state.tts_mode,
            )
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("STORYBOARD_DECISION_FAILED", state)

    def prepare_handoff_package(self) -> ApplicationResult:
        """Prepare the deterministic pre-generation package after Storyboard approval."""

        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.stage == "external_generation_pending" and state.refs.get("handoff_package") is not None:
            return self._success(state)
        if state.stage != "handoff_readiness" or state.pending_action is not None:
            return self._failure("HANDOFF_READINESS_REQUIRED", state)
        if "storyboard" not in state.decision_ids:
            return self._failure("STORYBOARD_APPROVAL_REQUIRED", state)
        renderer = self.local_narration_renderer
        if renderer is None:
            if self.tts_configuration is None:
                return self._failure("GPT_SOVITS_CONFIG_REQUIRED", state)
            renderer = GPTSoVITSSyntheticVoiceGenerator(self.workspace, self.tts_configuration)
        try:
            builder = CreatorHandoffPackageBuilder(self.artifacts, self.storyboard_decisions, self.workspace, renderer)
            output = WorkspaceFileReference(TASK_ID, "exports", "creator-handoff-package.zip")
            result = builder.build(
                TASK_ID,
                state.refs["source"],
                state.refs["script"],
                state.refs["character"],
                state.refs["storyboard"],
                state.refs["timeline"],
                state.refs["production_request"],
                state.refs["scene_generation_contract"],
                state.decision_ids["storyboard"],
                reference_stills_directory=self.visual_import_dir,
                output_reference=output,
                artifact_identity="handoff:episode-1",
                package_commit_id="handoff-package:episode-1",
            )
            if isinstance(result, HandoffPackageFailure):
                return self._failure(result.code, state, result.message)
            if not isinstance(result, HandoffPackageResult):
                return self._failure("HANDOFF_PACKAGE_FAILED", state)
            refs = {**state.refs, "handoff_package": result.package_reference}
            updated = _State(
                TASK_ID,
                "external_generation_pending",
                None,
                refs,
                state.decision_ids,
                None,
                None,
                state.package_output,
                None,
                None,
                state.replacement_done,
                state.visual_mode,
                state.tts_mode,
                result.output_reference,
                result.narration_references,
                tuple(f"reference-stills/scene-{index}.png" for index in range(1, 7)),
            )
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("HANDOFF_PACKAGE_FAILED", state)

    def submit_budget_decision(self, action: str = "approve", *, maximum_approved_amount_micros: int | None = None, maximum_attempts: int | None = None, decision_context: str = "") -> ApplicationResult:
        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.stage != "budget_review":
            return self._failure("BUDGET_GATE_NOT_PENDING", state)
        try:
            request_reference = state.refs["production_request"]
            budget_reference = state.refs["production_budget"]
            request, budget = self.artifacts.get(request_reference), self.artifacts.get(budget_reference)
            estimate = budget.payload["estimate"]
            maximum_attempts = budget.payload["retry_policy"]["maximum_attempts"] if maximum_attempts is None else maximum_attempts
            maximum_approved_amount_micros = estimate["policy_maximum_amount_micros"] if maximum_approved_amount_micros is None else maximum_approved_amount_micros
            boundary = BudgetAuthorizationBoundary(self.budget_decisions)
            outcome = boundary.decide(request_reference, request, budget_reference, budget, decision_id="decision:budget:offline", authorization_id="authorization:offline" if action == "approve" else None, task_id=TASK_ID, thread_id=THREAD_ID, creator_id=CREATOR_ID, decided_at=datetime.now(timezone.utc), action=action, maximum_approved_amount_micros=maximum_approved_amount_micros if action == "approve" else None, maximum_attempts=maximum_attempts if action == "approve" else None, decision_context=decision_context)
            if not isinstance(outcome, BudgetDecisionOutcome):
                return self._failure(getattr(outcome, "code", "BUDGET_DECISION_FAILED"), state, getattr(outcome, "message", None))
            authorization_id = outcome.authorization.authorization_id if outcome.authorization else None
            updated = _State(TASK_ID, "production" if action == "approve" else "budget_review", "produce_offline" if action == "approve" else "approve_budget", state.refs, {**state.decision_ids, "budget": outcome.decision.decision_id}, authorization_id, state.composition, state.package_output, None, None, state.replacement_done, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("BUDGET_DECISION_FAILED", state)

    def produce_offline(self) -> ApplicationResult:
        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.composition is not None:
            return self._success(state)
        if state.stage != "production" or state.pending_action != "produce_offline":
            return self._failure("BUDGET_APPROVAL_REQUIRED", state)
        try:
            if state.visual_mode == "imported":
                imported = self._local_imported_visual_generator()
                preflight = imported.preflight()
                if isinstance(preflight, ProductionMediaFailure):
                    return self._failure(preflight.code, state, preflight.message)
            if state.tts_mode == "gpt-sovits" and self.tts_configuration is None:
                return self._failure("GPT_SOVITS_CONFIG_REQUIRED", state)
            if state.tts_mode == "gpt-sovits" and self.tts_configuration is not None:
                voice_preflight = GPTSoVITSSyntheticVoiceGenerator(self.workspace, self.tts_configuration).preflight()
                if isinstance(voice_preflight, ProductionMediaFailure):
                    return self._failure(voice_preflight.code, state, voice_preflight.message)
            result, composition = self._run_production(state)
            if isinstance(result, ProductionMediaFailure):
                return self._failure(result.code, state, result.message)
            refs = {**state.refs, "subtitle": result.subtitle_reference, "master_audio": result.master_audio_reference, "video": result.video_reference}
            media = TaskMediaProjectionService(self.artifacts, self.media_repository)
            snapshot = media.inspect(TASK_ID).snapshot
            if snapshot is None:
                return self._failure("MEDIA_TASK_NOT_FOUND", state)
            for scene, reference in zip(composition["scenes"], result.scene_clip_references, strict=True):
                selected = media.select_scene(TASK_ID, f"media:clip:{scene['scene_id']}", snapshot.revision, scene["scene_id"], "scene_clip", reference)
                if selected.status != "success":
                    return self._failure(selected.error_code or "MEDIA_SELECTION_FAILED", state)
                snapshot = selected.snapshot
            for scene, reference in zip(composition["scenes"], result.scene_audio_references, strict=True):
                selected = media.select_scene(TASK_ID, f"media:audio:{scene['scene_id']}", snapshot.revision, scene["scene_id"], "scene_audio", reference)
                if selected.status != "success":
                    return self._failure(selected.error_code or "MEDIA_SELECTION_FAILED", state)
                snapshot = selected.snapshot
            for role, reference in (("subtitle", result.subtitle_reference), ("master_audio", result.master_audio_reference), ("video", result.video_reference)):
                selected = media.select_delivery(TASK_ID, f"media:{role}:1", snapshot.revision, role, reference)
                if selected.status != "success":
                    return self._failure(selected.error_code or "MEDIA_SELECTION_FAILED", state)
                snapshot = selected.snapshot
            updated = _State(TASK_ID, "final_review", "approve_final", refs, state.decision_ids, state.authorization_id, composition, state.package_output, None, None, state.replacement_done, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("PRODUCTION_FAILED", state)

    def replace_scene(self, scene_id: str) -> ApplicationResult:
        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.stage != "final_review" or state.pending_action not in {"approve_final", "replace_scene"} or state.replacement_done:
            return self._failure("SCENE_REPLACEMENT_UNAVAILABLE", state)
        if scene_id not in SCENE_IDS:
            return self._failure("INVALID_SCENE_ID", state)
        if state.visual_mode == "imported" and scene_id != "scene-2":
            return self._failure("SCENE_REPLACEMENT_UNAVAILABLE", state)
        try:
            composition = dict(state.composition or {})
            self._validate_original_scene_attempts(state, composition, SCENE_IDS.index(scene_id))
            task = self._composition_task(composition, state.refs["production_request"], output_name="composition-replaced.mp4")
            index = SCENE_IDS.index(scene_id)
            request = self.artifacts.get(state.refs["production_request"])
            scene_payload = request.payload["production_request"]["scenes"][index]
            if state.visual_mode == "imported":
                imported = self._local_imported_visual_generator()
                preflight = imported.preflight(replacement=True)
                if isinstance(preflight, ProductionMediaFailure):
                    # A missing/invalid operator file is a read-only
                    # preflight failure: show the actionable response, but
                    # do not turn the durable task snapshot into a new state.
                    return self._failure(preflight.code, state, preflight.message, persist_state=False)
                replacement_visual = self._local_imported_replacement_visual(imported, task, scene_payload, scene_id)
                # Imported replacement is visual-only.  Keep the exact
                # predecessor voice result and its selected Audio Artifact.
                replacement_voice = task.scenes[index].voice_result
            else:
                replacement_visual = self._local_replacement_visual(task, scene_payload, scene_id)
                # A GPT-SoVITS task is visual-only on replacement as well: do
                # not synthesize a Fixture voice or create a second TTS result.
                replacement_voice = (
                    task.scenes[index].voice_result
                    if state.tts_mode == "gpt-sovits"
                    else self._local_replacement_voice(task, scene_payload, scene_id)
                )
            scenes = list(task.scenes)
            scenes[index] = MediaCompositionScene(scene_id, scenes[index].start_milliseconds, scenes[index].end_milliseconds, replacement_visual, replacement_voice, scenes[index].subtitle_text)
            replaced_task = MediaCompositionTask(task.task_id, task.composition_id, task.production_request_reference, task.timeline_reference, tuple(scenes), task.output_reference)
            previous_result = self._composition_result(composition)
            orchestrator = self._orchestrator(state.visual_mode, state.tts_mode)
            result = orchestrator.compose(state.refs["production_request"], request, replaced_task, artifact_identity="media:episode-1", composition_commit_id="composition-replaced-1", previous_result=previous_result)
            if isinstance(result, ProductionMediaFailure):
                return self._failure(result.code, state, result.message)
            media = TaskMediaProjectionService(self.artifacts, self.media_repository)
            snapshot = media.inspect(TASK_ID).snapshot
            if snapshot is None:
                return self._failure("MEDIA_TASK_NOT_FOUND", state)
            replacement_roles = (("scene_clip", result.scene_clip_references[index]), ("video", result.video_reference)) if state.visual_mode == "imported" else (("scene_clip", result.scene_clip_references[index]), ("scene_audio", result.scene_audio_references[index]), ("master_audio", result.master_audio_reference), ("video", result.video_reference))
            for role, reference in replacement_roles:
                selected = media.select_scene(TASK_ID, f"media:replace:{role}:{scene_id}", snapshot.revision, scene_id, role, reference) if role.startswith("scene_") else media.select_delivery(TASK_ID, f"media:replace:{role}", snapshot.revision, role, reference)
                if selected.status != "success":
                    return self._failure(selected.error_code or "MEDIA_SELECTION_FAILED", state)
                snapshot = selected.snapshot
            refs = {**state.refs, "master_audio": result.master_audio_reference, "video": result.video_reference}
            review_service = FinalVideoReviewApplicationService(self.artifacts, FinalVideoDecisionBoundary(self.final_decisions), FinalVideoReviewWorkflow(self.artifacts, self.checkpoints))
            review_started = review_service.start(TASK_ID, _final_thread(result.video_reference), result.video_reference)
            if review_started.status == "failure":
                return self._failure(review_started.error_code or "FINAL_REVIEW_FAILED", state, review_started.error_message)
            updated_composition = self._composition_json(replaced_task, result)
            updated = _State(TASK_ID, "final_review", "approve_final", refs, state.decision_ids, state.authorization_id, updated_composition, None, None, None, True, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("SCENE_REPLACEMENT_FAILED", state)

    def submit_final_decision(self, action: str = "approve", *, decision_context: str = "") -> ApplicationResult:
        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.stage != "final_review" or state.pending_action != "approve_final" or not state.refs.get("video"):
            return self._failure("FINAL_REVIEW_NOT_READY", state)
        if action not in {"approve", "reject", "revise"}:
            return self._failure("INVALID_DECISION_ACTION", state)
        if action in {"reject", "revise"} and not decision_context.strip():
            return self._failure("INVALID_DECISION_CONTEXT", state)
        try:
            service = FinalVideoReviewApplicationService(self.artifacts, FinalVideoDecisionBoundary(self.final_decisions), FinalVideoReviewWorkflow(self.artifacts, self.checkpoints))
            video_reference = state.refs["video"]
            thread_id = _final_thread(video_reference)
            started = service.start(TASK_ID, thread_id, video_reference)
            if started.status == "failure":
                return self._failure(started.error_code or "FINAL_REVIEW_FAILED", state, started.error_message)
            decision_id = _final_decision_id(video_reference, action)
            result = service.decide(TASK_ID, thread_id, decision_id, CREATOR_ID, action, video_reference, decision_context)
            if result.status == "failure":
                return self._failure(result.error_code or "FINAL_REVIEW_FAILED", state, result.error_message)
            if action == "approve":
                next_stage, next_action = "final_review", "export_package"
            elif state.replacement_done:
                next_stage, next_action = "rejected", None
            else:
                next_stage, next_action = "final_review", "replace_scene"
            updated = _State(TASK_ID, next_stage, next_action, state.refs, {**state.decision_ids, "final": decision_id}, state.authorization_id, state.composition, state.package_output, None, None, state.replacement_done, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return self._success(updated)
        except Exception:
            return self._failure("FINAL_REVIEW_FAILED", state)

    def export_package(self) -> ApplicationResult:
        state = self._load_state()
        if state is None:
            return self._failure("TASK_NOT_FOUND")
        if state.pending_action != "export_package" or "final" not in state.decision_ids:
            return self._failure("FINAL_APPROVAL_REQUIRED", state)
        try:
            media = self._media_snapshot()
            subtitle = next(item.reference for item in media.delivery_selections if item.role == "subtitle" and item.status == "current")
            output = WorkspaceFileReference(TASK_ID, "exports", "episode-01.zip")
            if state.tts_mode == "gpt-sovits" and self.tts_configuration is None:
                return self._failure("GPT_SOVITS_CONFIG_REQUIRED", state)
            tts_attribution = (
                GPTSoVITSSyntheticVoiceGenerator(self.workspace, self.tts_configuration).engine_metadata
                if state.tts_mode == "gpt-sovits" and self.tts_configuration is not None
                else None
            )
            result = PublishPackageBuilder(self.artifacts, self.final_decisions, self.workspace).build(
                TASK_ID, state.refs["source"], subtitle, state.refs["video"], state.decision_ids["final"],
                artifact_identity="delivery:episode-1", manifest_commit_id="manifest:episode-1",
                package_commit_id="package:episode-1", output_reference=output,
                tts_attribution=tts_attribution,
            )
            if isinstance(result, PackagingFailure):
                return self._failure(result.code, state, result.message)
            refs = {**state.refs, "manifest": result.manifest_reference, "package": result.package_reference}
            updated = _State(TASK_ID, "exported", None, refs, state.decision_ids, state.authorization_id, state.composition, output, None, None, state.replacement_done, state.visual_mode, state.tts_mode)
            self._save_state(updated)
            return ApplicationResult("success", self._view(updated), package=result)
        except Exception:
            return self._failure("PACKAGE_EXPORT_FAILED", state)

    def _initialize_demo(self, material: object) -> _State:
        if not hasattr(material, "commit_sha") or not hasattr(material, "units"):
            raise RuntimeError("normalized source material is required")
        source_candidate = SourceRecordBuilder().build(material, identity="source:microsoft-ai-for-beginners", commit_id="source:episode-1")
        if not hasattr(source_candidate, "artifact_type"):
            raise RuntimeError("source record could not be built")
        prepared_workspace = self.workspace.prepare(TASK_ID)
        if not hasattr(prepared_workspace, "task_id"):
            raise RuntimeError("offline workspace could not be prepared")
        source_reference = self.artifacts.commit(source_candidate)
        source = self.artifacts.get(source_reference)
        runtime = _OfflineRuntime()
        knowledge_candidate = KnowledgeAgent(runtime).invoke(source_reference, source, context=KnowledgeTaskContext("AI-For-Beginners", "Lesson 1", "English", "adult AI beginners"), identity="knowledge:episode-1", commit_id="knowledge:episode-1", knowledge_boundary="traceable-source-only")
        knowledge_reference = self.artifacts.commit(knowledge_candidate)
        knowledge = self.artifacts.get(knowledge_reference)
        context = ContentTaskContext("adult AI beginners", "小土豆学 AI", 1, "AI不是魔法", "Simplified Chinese", "Explain why AI is not magic.")
        template = EpisodeTemplateConstraint(6, 60, "9:16")
        plans = ContentAgent(runtime).plan(knowledge_reference, knowledge, context=context, template=template, course_identity="course-plan:episode-1", episode_identity="episode-plan:episode-1", course_commit_id="course-plan:episode-1", episode_commit_id="episode-plan:episode-1")
        course_reference = self.artifacts.commit(plans.course)
        episode_reference = self.artifacts.commit(plans.episode)
        script_candidate = ContentAgent(runtime).script(knowledge_reference, knowledge, course_reference, self.artifacts.get(course_reference), episode_reference, self.artifacts.get(episode_reference), context=context, template=template, script_identity="script:episode-1", script_commit_id="script:episode-1")
        script_reference = self.artifacts.commit(script_candidate)
        started = ScriptReviewApplicationService(self.artifacts, ScriptDecisionBoundary(self.script_decisions), ScriptReviewWorkflow(self.artifacts, self.checkpoints)).start(TASK_ID, _script_thread(script_reference), script_reference)
        if started.status == "failure":
            raise RuntimeError
        state = _State(TASK_ID, "script_review", "approve_script", {"source": source_reference, "knowledge": knowledge_reference, "course_plan": course_reference, "episode_plan": episode_reference, "script": script_reference}, {}, None, None, None, None, None, False, "imported" if self.visual_import_dir is not None else "fixture", "gpt-sovits" if self.tts_configuration is not None else "fixture")
        self._save_state(state)
        return state

    def _price_snapshot(self, request_reference: ArtifactReference, request: ArtifactVersion) -> PriceSnapshot:
        return PriceSnapshot("offline-fixture-prices-v1", "local-fixture", "USD", request_reference, tuple(item for scene in request.payload["production_request"]["scenes"] for item in (PriceLineItem(scene["scene_id"], "visual", "per_scene", 1, 1_000), PriceLineItem(scene["scene_id"], "voice", "per_scene", 1, 500))))

    def _local_imported_visual_generator(self) -> LocalImportedVisualGenerator:
        if self.visual_import_dir is None:
            raise RuntimeError("explicit local visual import directory is required")
        return LocalImportedVisualGenerator(
            self.workspace,
            self.visual_import_dir,
            ffmpeg_executable=self.ffmpeg_executable,
            ffprobe_executable=self.ffprobe_executable,
        )

    def _orchestrator(self, visual_mode: str = "fixture", tts_mode: str = "fixture") -> ProductionOrchestrator:
        boundary = BudgetAuthorizationBoundary(self.budget_decisions)
        ledger = ProviderAttemptLedger(boundary.get_authorization, self.attempts)
        visual = (
            self._local_imported_visual_generator()
            if visual_mode == "imported"
            else FFmpegFixtureVisualGenerator(self.workspace, ffmpeg_executable=self.ffmpeg_executable, ffprobe_executable=self.ffprobe_executable)
        )
        voice = (
            GPTSoVITSSyntheticVoiceGenerator(self.workspace, self.tts_configuration)
            if tts_mode == "gpt-sovits" and self.tts_configuration is not None
            else FFmpegFixtureVoiceGenerator(self.workspace, ffmpeg_executable=self.ffmpeg_executable, ffprobe_executable=self.ffprobe_executable)
        )
        return ProductionOrchestrator(ledger, visual, voice, clock=lambda: datetime.now(timezone.utc), media_composer=FFmpegMediaComposer(self.workspace, ffmpeg_executable=self.ffmpeg_executable, ffprobe_executable=self.ffprobe_executable), artifact_repository=self.artifacts)

    def _validate_original_scene_attempts(self, state: _State, composition: Mapping[str, Any], index: int) -> None:
        """Require exact successful original Fixture attempts before replacement."""
        authorization = BudgetAuthorizationBoundary(self.budget_decisions).get_authorization(state.authorization_id or "")
        if isinstance(authorization, BudgetFailure):
            raise RuntimeError("budget authorization is unavailable")
        if (
            authorization.production_request_reference != state.refs.get("production_request")
            or authorization.budget_reference != state.refs.get("production_budget")
        ):
            raise RuntimeError("budget authorization does not match task")
        listed = ProviderAttemptLedger(BudgetAuthorizationBoundary(self.budget_decisions).get_authorization, self.attempts).list_for_authorization(authorization.authorization_id)
        if isinstance(listed, ProviderAttemptFailure):
            raise RuntimeError("provider attempt storage is unavailable")
        if type(listed) is not tuple:
            raise RuntimeError("provider attempt storage is unavailable")
        scene = composition["scenes"][index]
        for operation, key in (("visual", "visual_result"), ("voice", "voice_result")):
            result = _media_result_from(scene[key])
            record = next((item for item in listed if item.attempt_id == result.attempt_id), None)
            if (
                type(record) is not ProviderAttemptRecord
                or record.status != "succeeded"
                or record.result_code != "SUCCESS"
                or record.charged_amount_micros != 0
                or record.scene_id != scene["scene_id"]
                or record.operation != operation
                or record.production_request_reference != state.refs["production_request"]
                or record.budget_reference != state.refs["production_budget"]
                or record.output_references != (result.output_reference,)
            ):
                raise RuntimeError("original scene attempt is not terminal")

    def _run_production(self, state: _State) -> tuple[ProductionCompositionResult | ProductionMediaFailure, Mapping[str, Any]]:
        request_reference = state.refs["production_request"]
        request = self.artifacts.get(request_reference)
        if state.visual_mode == "imported" and self.visual_import_dir is None:
            return ProductionMediaFailure("validation", "LOCAL_IMPORT_DIRECTORY_REQUIRED", "an explicit local visual import directory is required"), {}
        authorization = BudgetAuthorizationBoundary(self.budget_decisions).get_authorization(state.authorization_id or "")
        if isinstance(authorization, BudgetFailure):
            return ProductionMediaFailure("validation", authorization.code, authorization.message), {}
        scenes: list[MediaCompositionScene] = []
        start_ms = 0
        orchestrator = self._orchestrator(state.visual_mode, state.tts_mode)
        visual_provider = LOCAL_IMPORTED_PROVIDER if state.visual_mode == "imported" else "ffmpeg-fixture-visual-v1"
        voice_provider = GPT_SOVITS_PROVIDER if state.tts_mode == "gpt-sovits" else "ffmpeg-fixture-voice-v1"
        for index, scene in enumerate(request.payload["production_request"]["scenes"], start=1):
            end_ms = start_ms + int(scene["duration_seconds"] * 1000)
            visual_reservation = ProviderAttemptReservation(f"attempt:offline:visual:{index}", TASK_ID, authorization.authorization_id, scene["scene_id"], "visual", visual_provider, f"offline-key:visual:{index}", WorkspaceFileReference(TASK_ID, "provider-records", f"offline-visual-{index}.json"), datetime.now(timezone.utc))
            voice_reservation = ProviderAttemptReservation(f"attempt:offline:voice:{index}", TASK_ID, authorization.authorization_id, scene["scene_id"], "voice", voice_provider, f"offline-key:voice:{index}", WorkspaceFileReference(TASK_ID, "provider-records", f"offline-voice-{index}.json"), visual_reservation.reserved_at)
            visual = orchestrator.execute(request_reference, request, visual_reservation, VisualGenerationTask(TASK_ID, visual_reservation.attempt_id, request_reference, scene["scene_id"], "9:16", scene["duration_seconds"], scene["visual_intent"], scene["character_action"], WorkspaceFileReference(TASK_ID, "media", f"scene-{index}.mp4")))
            voice = orchestrator.execute(request_reference, request, voice_reservation, VoiceSynthesisTask(TASK_ID, voice_reservation.attempt_id, request_reference, scene["scene_id"], request.payload["production_request"]["language"], scene["duration_seconds"], scene["narration"], WorkspaceFileReference(TASK_ID, "media", f"scene-{index}.m4a")))
            if not isinstance(visual, ProductionExecutionResult) or not isinstance(voice, ProductionExecutionResult):
                return ProductionMediaFailure("execution", "GENERATION_FAILED", "offline media generation failed"), {}
            scenes.append(MediaCompositionScene(scene["scene_id"], start_ms, end_ms, MediaGenerationResult(visual.attempt_id, scene["scene_id"], "visual", visual.provider, visual.output_reference, "video/mp4", scene["duration_seconds"], "SUCCESS"), MediaGenerationResult(voice.attempt_id, scene["scene_id"], "voice", voice.provider, voice.output_reference, "audio/mp4", scene["duration_seconds"], "SUCCESS"), scene["narration"]))
            start_ms = end_ms
        task = MediaCompositionTask(TASK_ID, "composition:episode-1", request_reference, state.refs["timeline"], tuple(scenes), WorkspaceFileReference(TASK_ID, "media", "composition.mp4"))
        result = orchestrator.compose(request_reference, request, task, artifact_identity="media:episode-1", composition_commit_id="composition:episode-1")
        if isinstance(result, ProductionMediaFailure):
            return result, {}
        return result, self._composition_json(task, result)

    def _composition_json(self, task: MediaCompositionTask, result: ProductionCompositionResult) -> dict[str, Any]:
        return {"task_id": task.task_id, "composition_id": task.composition_id, "production_request_reference": _ref_json(task.production_request_reference), "timeline_reference": _ref_json(task.timeline_reference), "output_reference": _workspace_json(task.output_reference), "scenes": [{"scene_id": scene.scene_id, "start_milliseconds": scene.start_milliseconds, "end_milliseconds": scene.end_milliseconds, "subtitle_text": scene.subtitle_text, "visual_result": _media_result_json(scene.visual_result), "voice_result": _media_result_json(scene.voice_result)} for scene in task.scenes], "scene_clip_references": [_ref_json(item) for item in result.scene_clip_references], "scene_audio_references": [_ref_json(item) for item in result.scene_audio_references], "subtitle_reference": _ref_json(result.subtitle_reference), "master_audio_reference": _ref_json(result.master_audio_reference), "video_reference": _ref_json(result.video_reference)}

    def _composition_result(self, value: Mapping[str, Any]) -> ProductionCompositionResult:
        return ProductionCompositionResult(TASK_ID, value["composition_id"], _ref_from(value["production_request_reference"]), _ref_from(value["timeline_reference"]), tuple(_ref_from(item) for item in value["scene_clip_references"]), tuple(_ref_from(item) for item in value["scene_audio_references"]), _ref_from(value["subtitle_reference"]), _ref_from(value["master_audio_reference"]), _ref_from(value["video_reference"]), _workspace_from(value["output_reference"]), "SUCCESS")

    def _composition_task(self, value: Mapping[str, Any], request_reference: ArtifactReference, *, output_name: str | None = None) -> MediaCompositionTask:
        scenes = tuple(MediaCompositionScene(item["scene_id"], item["start_milliseconds"], item["end_milliseconds"], _media_result_from(item["visual_result"]), _media_result_from(item["voice_result"]), item["subtitle_text"]) for item in value["scenes"])
        return MediaCompositionTask(TASK_ID, value["composition_id"], request_reference, _ref_from(value["timeline_reference"]), scenes, WorkspaceFileReference(TASK_ID, "media", output_name or _workspace_from(value["output_reference"]).name))

    def _local_replacement_visual(self, task: MediaCompositionTask, scene: Mapping[str, Any], scene_id: str) -> MediaGenerationResult:
        attempt_id = f"local-replace:{scene_id}:visual"
        result = FFmpegFixtureVisualGenerator(self.workspace, ffmpeg_executable=self.ffmpeg_executable, ffprobe_executable=self.ffprobe_executable).generate(VisualGenerationTask(TASK_ID, attempt_id, task.production_request_reference, scene_id, "9:16", scene["duration_seconds"], scene["visual_intent"] + "（替换）", scene["character_action"], WorkspaceFileReference(TASK_ID, "media", f"{scene_id}-replacement.mp4")))
        if not isinstance(result, MediaGenerationResult):
            raise RuntimeError
        return MediaGenerationResult(result.attempt_id, result.scene_id, result.operation, "ffmpeg-fixture-local-replacement-v1", result.output_reference, result.media_type, result.duration_seconds, result.result_code)

    def _local_imported_replacement_visual(self, adapter: LocalImportedVisualGenerator, task: MediaCompositionTask, scene: Mapping[str, Any], scene_id: str) -> MediaGenerationResult:
        result = adapter.generate(
            VisualGenerationTask(
                TASK_ID,
                f"local-replace:{scene_id}:visual",
                task.production_request_reference,
                scene_id,
                "9:16",
                scene["duration_seconds"],
                scene["visual_intent"],
                scene["character_action"],
                WorkspaceFileReference(TASK_ID, "media", f"{scene_id}-replacement.mp4"),
            )
        )
        if not isinstance(result, MediaGenerationResult):
            raise RuntimeError
        return result

    def _local_replacement_voice(self, task: MediaCompositionTask, scene: Mapping[str, Any], scene_id: str) -> MediaGenerationResult:
        attempt_id = f"local-replace:{scene_id}:voice"
        result = FFmpegFixtureVoiceGenerator(self.workspace, ffmpeg_executable=self.ffmpeg_executable, ffprobe_executable=self.ffprobe_executable).synthesize(VoiceSynthesisTask(TASK_ID, attempt_id, task.production_request_reference, scene_id, "Simplified Chinese", scene["duration_seconds"], scene["narration"] + "（替换）", WorkspaceFileReference(TASK_ID, "media", f"{scene_id}-replacement.m4a")))
        if not isinstance(result, MediaGenerationResult):
            raise RuntimeError
        return MediaGenerationResult(result.attempt_id, result.scene_id, result.operation, "ffmpeg-fixture-local-replacement-v1", result.output_reference, result.media_type, result.duration_seconds, result.result_code)

    def _media_snapshot(self) -> TaskMediaSnapshot:
        result = TaskMediaProjectionService(self.artifacts, self.media_repository).inspect(TASK_ID)
        if result.snapshot is None:
            raise RuntimeError
        return result.snapshot

    def _load_state(self) -> _State | None:
        row = self._state_connection.execute("SELECT schema_version, state_json FROM application_state WHERE singleton=1").fetchone()
        if row is None:
            return None
        if row[0] != _STATE_SCHEMA:
            raise ValueError
        value = json.loads(row[1])
        refs = {key: _ref_from(raw) for key, raw in value["refs"].items()}
        output = _workspace_from(value["package_output"]) if value.get("package_output") else None
        handoff_output = _workspace_from(value["handoff_package_output"]) if value.get("handoff_package_output") else None
        handoff_narration = tuple(_workspace_from(item) for item in value.get("handoff_narration_references", ()))
        handoff_stills = tuple(item for item in value.get("handoff_reference_still_facts", ()) if type(item) is str)
        return _State(value["task_id"], value["stage"], value.get("pending_action"), refs, dict(value.get("decision_ids", {})), value.get("authorization_id"), value.get("composition"), output, value.get("failure_category"), value.get("failure_message"), bool(value.get("replacement_done", False)), value.get("visual_mode", "fixture"), value.get("tts_mode", "fixture"), handoff_output, handoff_narration, handoff_stills)

    def _save_state(self, state: _State) -> None:
        value = {"task_id": state.task_id, "stage": state.stage, "pending_action": state.pending_action, "refs": {key: _ref_json(ref) for key, ref in state.refs.items()}, "decision_ids": dict(state.decision_ids), "authorization_id": state.authorization_id, "composition": state.composition, "package_output": _workspace_json(state.package_output) if state.package_output else None, "handoff_package_output": _workspace_json(state.handoff_package_output) if state.handoff_package_output else None, "handoff_narration_references": [_workspace_json(reference) for reference in state.handoff_narration_references], "handoff_reference_still_facts": list(state.handoff_reference_still_facts), "failure_category": state.failure_category, "failure_message": state.failure_message, "replacement_done": state.replacement_done, "visual_mode": state.visual_mode, "tts_mode": state.tts_mode}
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        self._state_connection.execute("INSERT INTO application_state(singleton, schema_version, state_json) VALUES(1, ?, ?) ON CONFLICT(singleton) DO UPDATE SET schema_version=excluded.schema_version, state_json=excluded.state_json", (_STATE_SCHEMA, encoded))

    def _success(self, state: _State) -> ApplicationResult:
        return ApplicationResult("success", self._view(state))

    def _failure(
        self,
        code: str,
        state: _State | None = None,
        message: str | None = None,
        *,
        persist_state: bool = True,
    ) -> ApplicationResult:
        category = _failure_category(code)
        safe_message = _safe_actionable_failure(code, category, message)
        if state is not None:
            failure_state = _State(state.task_id, state.stage, state.pending_action, state.refs, state.decision_ids, state.authorization_id, state.composition, state.package_output, category, safe_message, state.replacement_done, state.visual_mode, state.tts_mode, state.handoff_package_output, state.handoff_narration_references, state.handoff_reference_still_facts)
            if persist_state:
                try:
                    self._save_state(failure_state)
                    state = failure_state
                except Exception:
                    pass
            else:
                state = failure_state
        return ApplicationResult("failure", self._view(state) if state else None, code, safe_message)

    def _view(self, state: _State | None) -> ApplicationView | None:
        if state is None:
            return None
        source = self.artifacts.get(state.refs["source"])
        script = self.artifacts.get(state.refs["script"])
        source_units = source.payload["units"]
        script_scenes = script.payload["scenes"]
        production_scenes = None
        if "production_request" in state.refs:
            try:
                request = self.artifacts.get(state.refs["production_request"])
                production_scenes = request.payload["production_request"]["scenes"]
            except Exception:
                production_scenes = None
        media = None
        try:
            media = self._media_snapshot()
        except Exception:
            pass
        selected_clips = {(item.scene_id, item.role): item.reference for item in media.scene_selections if item.status == "current"} if media else {}
        selected_delivery = {item.role: item.reference for item in media.delivery_selections if item.status == "current"} if media else {}
        scenes = tuple(SceneView(scene["scene_id"], scene["narration"], scene.get("teaching_intent", scene.get("visual_intent", "")), selected_clips.get((scene["scene_id"], "scene_clip")), selected_clips.get((scene["scene_id"], "scene_audio")), "ready" if (scene["scene_id"], "scene_clip") in selected_clips else "planned") for scene in script_scenes)
        budget_amount = None
        budget_attempts = None
        if "production_budget" in state.refs:
            budget = self.artifacts.get(state.refs["production_budget"])
            budget_amount = budget.payload["estimate"]["policy_maximum_amount_micros"]
            budget_attempts = budget.payload["retry_policy"]["maximum_attempts"]
        attempt_statuses: tuple[str, ...] = ()
        attempt_count = 0
        charged_amount = 0
        if state.authorization_id:
            try:
                listed = ProviderAttemptLedger(BudgetAuthorizationBoundary(self.budget_decisions).get_authorization, self.attempts).list_for_authorization(state.authorization_id)
                if type(listed) is tuple:
                    attempt_count = len(listed)
                    attempt_statuses = tuple(f"{item.scene_id}/{item.operation}:{item.status}" for item in listed if type(item) is ProviderAttemptRecord)
                    charged_amount = sum(item.charged_amount_micros for item in listed if type(item) is ProviderAttemptRecord)
            except Exception:
                pass
        storyboard_reference = state.refs.get("storyboard")
        scene_generation_contract_reference = state.refs.get("scene_generation_contract")
        timeline_reference = state.refs.get("timeline")
        production_request_reference = state.refs.get("production_request")
        storyboard_decision_context: str | None = None
        storyboard_decision_id = state.decision_ids.get("storyboard")
        if storyboard_decision_id:
            try:
                storyboard_decision = self.storyboard_decisions.get(storyboard_decision_id)
                if isinstance(storyboard_decision, StoryboardDecisionRecord):
                    storyboard_decision_context = storyboard_decision.decision_context or None
            except Exception:
                storyboard_decision_context = None
        generation_entries: tuple[GenerationEntryView, ...] = ()
        if scene_generation_contract_reference is not None:
            try:
                contract = self.artifacts.get(scene_generation_contract_reference)
                raw_entries = contract.payload["scene_generation_contract"]["scenes"]
                generation_entries = tuple(
                    GenerationEntryView(
                        entry["scene_id"],
                        entry["duration_milliseconds"],
                        entry["narration_identity"],
                        entry["narration"],
                        entry["visual_intent"],
                        entry["character_action"],
                        tuple(entry["continuity_notes"]),
                        entry["generation_prompt"],
                        entry["camera_motion_instruction"],
                        tuple(entry["negative_constraints"]),
                        entry["expected_filename"],
                    )
                    for entry in raw_entries
                )
            except Exception:
                generation_entries = ()
        handoff_package_reference = state.refs.get("handoff_package")
        handoff_package_output = state.handoff_package_output
        handoff_narration_references = state.handoff_narration_references
        handoff_reference_still_facts = state.handoff_reference_still_facts
        handoff_narration_metadata: Mapping[str, Any] | None = None
        if handoff_package_reference is not None:
            try:
                handoff_version = self.artifacts.get(handoff_package_reference)
                payload = handoff_version.payload if isinstance(handoff_version, ArtifactVersion) else None
                if isinstance(payload, Mapping):
                    if handoff_package_output is None and isinstance(payload.get("output_reference"), Mapping):
                        handoff_package_output = _workspace_from(dict(payload["output_reference"]))
                    if not handoff_narration_references and type(payload.get("narration_references")) is tuple:
                        handoff_narration_references = tuple(_workspace_from(dict(item)) for item in payload["narration_references"] if isinstance(item, Mapping))
                    if isinstance(payload.get("local_narration"), Mapping):
                        handoff_narration_metadata = payload["local_narration"]
            except Exception:
                pass
        view_tts_engine = GPT_SOVITS_PROVIDER if state.tts_mode == "gpt-sovits" else None
        view_tts_reference = "locally generated Qwen3-TTS Serena synthetic reference" if state.tts_mode == "gpt-sovits" else None
        view_tts_charge: int | None = 0 if state.tts_mode == "gpt-sovits" else None
        if handoff_narration_metadata is not None:
            if type(handoff_narration_metadata.get("engine")) is str:
                view_tts_engine = handoff_narration_metadata["engine"]
            if type(handoff_narration_metadata.get("reference_provenance")) is str:
                view_tts_reference = handoff_narration_metadata["reference_provenance"]
            if type(handoff_narration_metadata.get("external_charge_micros")) is int:
                view_tts_charge = handoff_narration_metadata["external_charge_micros"]
        if state.stage == "script_review":
            available = ("approve_script", "revise_script", "reject_script")
        elif state.stage == "planning" and state.pending_action == "approve_storyboard":
            available = ("approve_storyboard", "reject_storyboard")
        elif state.stage == "handoff_readiness":
            available = ("prepare_handoff_package",)
        elif state.stage == "external_generation_pending":
            available = ("download_handoff_package",)
        elif state.pending_action == "export_package":
            available = ("export_package",)
        elif state.stage == "final_review":
            available = ("approve_final", "reject_final") if state.replacement_done else ("approve_final", "reject_final", "replace_scene")
        else:
            available = {"planning": ("advance_planning",), "budget_review": ("approve_budget",), "production": ("produce_offline",), "exported": (), "rejected": ()}.get(state.stage, ())
        local_label = (
            "Imported visual replacement; source supplied via ChatGPT Desktop ImageGen, generated outside the application (zero external charge)."
            if state.replacement_done and state.visual_mode == "imported"
            else "Local deterministic replacement (not a Provider attempt)."
            if state.replacement_done
            else None
        )
        prompt_cards = _prompt_cards(script_scenes, production_scenes) if state.visual_mode == "imported" else ()
        return ApplicationView(
            TASK_ID, state.stage, state.pending_action, source.payload["commit_sha"], source_units[0]["locator"],
            tuple(unit["locator"] for unit in source_units), state.refs["script"], scenes, budget_amount,
            budget_attempts, state.authorization_id is not None, selected_delivery.get("video"),
            selected_delivery.get("subtitle"), state.refs.get("package"), state.package_output,
            state.failure_category, state.failure_message, tuple(available), True, state.replacement_done,
            attempt_count, attempt_statuses, charged_amount, local_label, prompt_cards, state.visual_mode,
            view_tts_engine,
            view_tts_reference,
            view_tts_charge,
            storyboard_reference,
            scene_generation_contract_reference,
            generation_entries,
            timeline_reference,
            production_request_reference,
            storyboard_decision_context,
            handoff_package_reference,
            handoff_package_output,
            handoff_narration_references,
            handoff_reference_still_facts,
            "External Jimeng/Kling subscription generation is outside AI Course Factory; no application Attempt or charge is created.",
        )


__all__ = [
    "ApplicationDownload",
    "ApplicationResult",
    "ApplicationView",
    "CourseFactoryApplication",
    "GenerationEntryView",
    "PromptCard",
    "SceneView",
]
