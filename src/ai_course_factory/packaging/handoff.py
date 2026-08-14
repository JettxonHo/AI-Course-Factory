"""Deterministic pre-generation Creator Handoff Package construction."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import io
import json
import math
from pathlib import Path
import stat
from types import MappingProxyType
import zipfile

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactNotFoundError,
    ArtifactReference,
    ArtifactVersion,
    StoryboardDecisionRecord,
)
from ai_course_factory.persistence import WorkspaceAdapter, WorkspaceFileRecord, WorkspaceFileReference, WorkspaceFailure
from ai_course_factory.production import (
    LocalNarrationPreflight,
    LocalNarrationRenderer,
    LocalNarrationResult,
    LocalNarrationTask,
    ProductionMediaFailure,
)


_SCENE_IDS = tuple(f"scene-{index}" for index in range(1, 7))
_STILL_NAMES = tuple(f"scene-{index}.png" for index in range(1, 7))
_MAX_STILL_BYTES = 64 * 1024 * 1024
_MAX_PACKAGE_BYTES = 256 * 1024 * 1024
_MAX_TEXT_BYTES = 4 * 1024 * 1024
_HANDOFF_ARTIFACT = "creator_handoff_package"
_ZIP_MEDIA_TYPE = "application/zip"
_AUDIO_MEDIA_TYPE = "audio/mp4"
_HANDOFF_BINDING_AREA = "provider-records"


@dataclass(frozen=True, slots=True)
class HandoffPackageFailure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class HandoffPackageResult:
    task_id: str
    source_record_reference: ArtifactReference
    script_reference: ArtifactReference
    character_reference: ArtifactReference
    storyboard_reference: ArtifactReference
    timeline_reference: ArtifactReference
    production_request_reference: ArtifactReference
    scene_generation_contract_reference: ArtifactReference
    storyboard_decision_id: str
    narration_references: tuple[WorkspaceFileReference, ...]
    package_reference: ArtifactReference
    output_reference: WorkspaceFileReference
    file_facts: tuple[Mapping[str, object], ...]
    result_code: str


class _Invalid(Exception):
    def __init__(self, code: str, message: str = "Creator Handoff Package input is invalid") -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _failure(kind: str, code: str, message: str) -> HandoffPackageFailure:
    return HandoffPackageFailure(kind, code, message)


def _ref(value: object, artifact_type: str, code: str) -> ArtifactReference:
    if (
        type(value) is not ArtifactReference
        or value.artifact_type != artifact_type
        or type(value.identity) is not str
        or not value.identity.strip()
        or type(value.version) is not int
        or isinstance(value.version, bool)
        or value.version < 1
    ):
        raise _Invalid(code, f"an exact {artifact_type} Reference is required")
    if value.identity.strip().casefold() in {"latest", "current"}:
        raise _Invalid(code, f"an exact {artifact_type} Reference is required")
    return value


def _same_ref(first: object, second: object) -> bool:
    return type(first) is ArtifactReference and type(second) is ArtifactReference and first == second


def _version(reference: ArtifactReference, value: object, code: str) -> ArtifactVersion:
    if type(value) is not ArtifactVersion or value.reference != reference:
        raise _Invalid(code, "an exact Artifact Version is required")
    if type(value.dependencies) is not tuple or type(value.payload) not in (dict, MappingProxyType):
        raise _Invalid(code, "an exact Artifact Version is required")
    return value


def _ref_json(reference: ArtifactReference) -> dict[str, object]:
    return {"artifact_type": reference.artifact_type, "identity": reference.identity, "version": reference.version}


def _workspace_json(reference: WorkspaceFileReference) -> dict[str, str]:
    return {"task_id": reference.task_id, "area": reference.area, "name": reference.name}


def _workspace_from(value: object) -> WorkspaceFileReference:
    if type(value) not in (dict, MappingProxyType) or set(value) != {"task_id", "area", "name"}:
        raise _Invalid("HANDOFF_ARTIFACT_INVALID", "stored handoff package is invalid")
    reference = WorkspaceFileReference(value["task_id"], value["area"], value["name"])
    if type(reference.task_id) is not str or type(reference.area) is not str or type(reference.name) is not str:
        raise _Invalid("HANDOFF_ARTIFACT_INVALID", "stored handoff package is invalid")
    return reference


def _json_value(value: object) -> object:
    if isinstance(value, ArtifactReference):
        return _ref_json(value)
    if isinstance(value, WorkspaceFileReference):
        return _workspace_json(value)
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise _Invalid("HANDOFF_RENDER_FAILED", "handoff package rendering failed")


def _canonical_json(value: object) -> bytes:
    try:
        content = json.dumps(_json_value(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise _Invalid("HANDOFF_RENDER_FAILED", "handoff package rendering failed") from None
    if len(content) > _MAX_TEXT_BYTES:
        raise _Invalid("HANDOFF_OUTPUT_TOO_LARGE", "handoff package output is too large")
    return content


def _valid_duration(value: object) -> bool:
    """Accept only a finite, positive, non-bool numeric duration."""

    return type(value) in (int, float) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0


def _text(value: object, code: str, *, max_length: int = 4096) -> str:
    if type(value) is not str or not value or len(value) > max_length or any(ord(char) < 0x20 and char not in "\n\t" for char in value) or any(ord(char) == 0x7F for char in value):
        raise _Invalid(code, "handoff package input is invalid")
    return value


def _srt_time(milliseconds: int) -> str:
    seconds, millis = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _render_srt(entries: tuple[Mapping[str, object], ...]) -> bytes:
    chunks: list[str] = []
    elapsed = 0
    for index, entry in enumerate(entries, start=1):
        duration = entry.get("duration_milliseconds")
        narration = _text(entry.get("narration"), "INVALID_CONTRACT_LINEAGE")
        if type(duration) is not int or isinstance(duration, bool) or duration <= 0:
            raise _Invalid("INVALID_CONTRACT_LINEAGE", "Scene Generation Contract lineage is invalid")
        end = elapsed + duration
        chunks.append(f"{index}\n{_srt_time(elapsed)} --> {_srt_time(end)}\n{narration}\n")
        elapsed = end
    content = "\n".join(chunks).encode("utf-8")
    if not content or len(content) > _MAX_TEXT_BYTES:
        raise _Invalid("HANDOFF_OUTPUT_TOO_LARGE", "handoff package output is too large")
    return content


def _render_guide(
    task_id: str,
    references: Mapping[str, ArtifactReference],
    entries: tuple[Mapping[str, object], ...],
) -> bytes:
    lines = [
        "# Creator Handoff Guide",
        "",
        "This package is a pre-generation handoff. Create one generated Scene video per exact filename, then return the files to AI Course Factory for import.",
        "Manual Jimeng/Kling subscription generation occurs outside the application; it creates no application Provider Attempt or charge.",
        "",
        f"Task: {task_id}",
        *[f"{name}: {reference.identity} v{reference.version}" for name, reference in references.items()],
        "",
        "The application-owned narration, SRT and Timeline remain canonical during later composition.",
        "",
    ]
    for index, entry in enumerate(entries, start=1):
        scene_id = _text(entry.get("scene_id"), "INVALID_CONTRACT_LINEAGE", max_length=128)
        filename = _text(entry.get("expected_filename"), "INVALID_CONTRACT_LINEAGE", max_length=128)
        lines.extend((
            f"## {index}. {scene_id} → {filename}",
            f"Duration: {entry.get('duration_milliseconds')} ms",
            f"Narration: {_text(entry.get('narration'), 'INVALID_CONTRACT_LINEAGE')}",
            f"Visual intent: {_text(entry.get('visual_intent'), 'INVALID_CONTRACT_LINEAGE')}",
            f"Character action: {_text(entry.get('character_action'), 'INVALID_CONTRACT_LINEAGE')}",
            f"Continuity: {'; '.join(str(item) for item in entry.get('continuity_notes', ())) }",
            f"Prompt: {_text(entry.get('generation_prompt'), 'INVALID_CONTRACT_LINEAGE')}",
            f"Camera and motion: {_text(entry.get('camera_motion_instruction'), 'INVALID_CONTRACT_LINEAGE')}",
            f"Negative constraints: {', '.join(str(item) for item in entry.get('negative_constraints', ())) }",
            "",
        ))
    content = "\n".join(lines).encode("utf-8")
    if len(content) > _MAX_TEXT_BYTES:
        raise _Invalid("HANDOFF_OUTPUT_TOO_LARGE", "handoff package output is too large")
    return content


def _valid_png(content: bytes) -> bool:
    return len(content) >= 24 and content[:8] == b"\x89PNG\r\n\x1a\n" and content[12:16] == b"IHDR" and int.from_bytes(content[16:20], "big") > 0 and int.from_bytes(content[20:24], "big") > 0


def _valid_jpeg(content: bytes) -> bool:
    return len(content) > 4 and content[:2] == b"\xff\xd8" and content[-2:] == b"\xff\xd9"


def _read_stills(directory: str | Path) -> tuple[dict[str, bytes], HandoffPackageFailure | None]:
    try:
        configured = Path(directory).expanduser()
        info = configured.lstat()
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            return {}, _failure("validation", "HANDOFF_STILLS_DIRECTORY_REQUIRED", "an explicit reference-still directory is required")
        root = configured.resolve()
    except (OSError, TypeError, ValueError):
        return {}, _failure("validation", "HANDOFF_STILLS_DIRECTORY_REQUIRED", "an explicit reference-still directory is required")
    result: dict[str, bytes] = {}
    invalid: list[str] = []
    for name in _STILL_NAMES:
        try:
            path = root / name
            stat_result = path.lstat()
            content = path.read_bytes()
            if stat.S_ISLNK(stat_result.st_mode) or not stat.S_ISREG(stat_result.st_mode) or stat_result.st_size < 1 or stat_result.st_size > _MAX_STILL_BYTES or len(content) != stat_result.st_size or not _valid_png(content) and not _valid_jpeg(content):
                invalid.append(name)
            else:
                result[name] = content
        except (OSError, ValueError):
            invalid.append(name)
    if invalid:
        return {}, _failure("validation", "HANDOFF_STILLS_PREFLIGHT_FAILED", f"Reference stills require valid PNG/JPEG files: {', '.join(invalid)}.")
    return result, None


def _zip(entries: tuple[tuple[str, bytes], ...]) -> bytes:
    output = io.BytesIO()
    try:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
            for name, content in entries:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 0
                info.create_version = 20
                info.extract_version = 20
                info.flag_bits = 0
                info.external_attr = 0o600 << 16
                info.internal_attr = 0
                info.extra = b""
                info.comment = b""
                archive.writestr(info, content)
    except (OSError, ValueError, zipfile.BadZipFile):
        raise _Invalid("HANDOFF_RENDER_FAILED", "handoff package rendering failed") from None
    content = output.getvalue()
    if not content or len(content) > _MAX_PACKAGE_BYTES:
        raise _Invalid("HANDOFF_OUTPUT_TOO_LARGE", "handoff package output is too large")
    return content


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _metadata(renderer: object, preflight: LocalNarrationPreflight) -> dict[str, object]:
    raw = getattr(renderer, "engine_metadata", {})
    metadata = raw if isinstance(raw, Mapping) else {}
    engine = metadata.get("engine", preflight.engine)
    engine_version = metadata.get("engine_version", "v2")
    runtime = metadata.get("runtime", "local GPT-SoVITS runtime")
    reference_provenance = metadata.get("reference_provenance", "local synthetic reference")
    if not all(type(value) is str and value for value in (engine, engine_version, runtime, reference_provenance, preflight.engine, preflight.repository_commit, preflight.model_identifier, preflight.reference_audio, preflight.reference_transcript)):
        raise _Invalid("HANDOFF_NARRATION_PREFLIGHT_FAILED", "local narration runtime facts are invalid")
    return {
        "engine": engine,
        "engine_version": engine_version,
        "repository_commit": preflight.repository_commit,
        "model_identifier": preflight.model_identifier,
        "runtime": runtime,
        "reference_provenance": reference_provenance,
        "reference_transcript": preflight.reference_transcript,
        "application_provider_api_call": False,
        "external_charge_micros": 0,
    }


def _stored_result(version: ArtifactVersion, workspace: WorkspaceAdapter, task_id: str) -> HandoffPackageResult:
    payload = version.payload
    if type(payload) not in (dict, MappingProxyType):
        raise _Invalid("HANDOFF_ARTIFACT_INVALID", "stored handoff package is invalid")
    expected = {"task_id", "source_record_reference", "script_reference", "character_reference", "storyboard_reference", "timeline_reference", "production_request_reference", "scene_generation_contract_reference", "storyboard_decision_id", "narration_references", "output_reference", "file_facts", "local_narration", "manual_generation"}
    if set(payload) != expected or payload.get("task_id") != task_id:
        raise _Invalid("HANDOFF_ARTIFACT_INVALID", "stored handoff package is invalid")
    output_reference = _workspace_from(payload["output_reference"])
    if output_reference.task_id != task_id or output_reference.area != "exports":
        raise _Invalid("HANDOFF_ARTIFACT_INVALID", "stored handoff package is invalid")
    narration = payload["narration_references"]
    if type(narration) is not tuple or len(narration) != 6:
        raise _Invalid("HANDOFF_ARTIFACT_INVALID", "stored handoff package is invalid")
    narration_refs = tuple(_workspace_from(value) for value in narration)
    file_facts = payload["file_facts"]
    if type(file_facts) is not tuple:
        raise _Invalid("HANDOFF_ARTIFACT_INVALID", "stored handoff package is invalid")
    content = workspace.read(output_reference)
    if not isinstance(content, bytes):
        raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "handoff package output is unavailable")
    return HandoffPackageResult(
        task_id,
        _ref(payload["source_record_reference"], "source_record", "HANDOFF_ARTIFACT_INVALID"),
        _ref(payload["script_reference"], "script", "HANDOFF_ARTIFACT_INVALID"),
        _ref(payload["character_reference"], "character", "HANDOFF_ARTIFACT_INVALID"),
        _ref(payload["storyboard_reference"], "storyboard", "HANDOFF_ARTIFACT_INVALID"),
        _ref(payload["timeline_reference"], "timeline", "HANDOFF_ARTIFACT_INVALID"),
        _ref(payload["production_request_reference"], "production_request", "HANDOFF_ARTIFACT_INVALID"),
        _ref(payload["scene_generation_contract_reference"], "scene_generation_contract", "HANDOFF_ARTIFACT_INVALID"),
        _text(payload["storyboard_decision_id"], "HANDOFF_ARTIFACT_INVALID", max_length=256),
        narration_refs,
        version.reference,
        output_reference,
        tuple(file_facts),
        "SUCCESS",
    )


class CreatorHandoffPackageBuilder:
    """Build and commit one deterministic Creator Handoff Package."""

    __slots__ = ("_artifacts", "_storyboard_decisions", "_workspace", "_renderer")

    def __init__(
        self,
        artifact_repository: object,
        storyboard_decisions: object,
        workspace: WorkspaceAdapter,
        narration_renderer: LocalNarrationRenderer,
    ) -> None:
        self._artifacts = artifact_repository
        self._storyboard_decisions = storyboard_decisions
        self._workspace = workspace
        self._renderer = narration_renderer

    def build(
        self,
        task_id: str,
        source_record_reference: ArtifactReference,
        script_reference: ArtifactReference,
        character_reference: ArtifactReference,
        storyboard_reference: ArtifactReference,
        timeline_reference: ArtifactReference,
        production_request_reference: ArtifactReference,
        scene_generation_contract_reference: ArtifactReference,
        storyboard_decision_id: str,
        *,
        reference_stills_directory: str | Path,
        output_reference: WorkspaceFileReference,
        artifact_identity: str = "handoff:episode-1",
        package_commit_id: str = "handoff-package:episode-1",
    ) -> HandoffPackageResult | HandoffPackageFailure:
        package_reference = ArtifactReference(_HANDOFF_ARTIFACT, artifact_identity, 1)
        try:
            self._validate_task(task_id)
            _text(artifact_identity, "INVALID_HANDOFF_IDENTITY", max_length=256)
            _text(package_commit_id, "INVALID_HANDOFF_COMMIT_ID", max_length=256)
            if type(output_reference) is not WorkspaceFileReference or output_reference.task_id != task_id or output_reference.area != "exports":
                raise _Invalid("INVALID_HANDOFF_OUTPUT_REFERENCE", "an exports Workspace Reference is required")
            refs = {
                "source": _ref(source_record_reference, "source_record", "INVALID_HANDOFF_LINEAGE"),
                "script": _ref(script_reference, "script", "INVALID_HANDOFF_LINEAGE"),
                "character": _ref(character_reference, "character", "INVALID_HANDOFF_LINEAGE"),
                "storyboard": _ref(storyboard_reference, "storyboard", "INVALID_HANDOFF_LINEAGE"),
                "timeline": _ref(timeline_reference, "timeline", "INVALID_HANDOFF_LINEAGE"),
                "production_request": _ref(production_request_reference, "production_request", "INVALID_HANDOFF_LINEAGE"),
                "scene_generation_contract": _ref(scene_generation_contract_reference, "scene_generation_contract", "INVALID_HANDOFF_LINEAGE"),
            }
            _text(storyboard_decision_id, "INVALID_HANDOFF_LINEAGE", max_length=256)
            decision = self._storyboard_decisions.get(storyboard_decision_id)
            if type(decision) is not StoryboardDecisionRecord or decision.action != "approve" or decision.storyboard_reference != refs["storyboard"] or decision.script_reference != refs["script"] or decision.character_reference != refs["character"]:
                raise _Invalid("STORYBOARD_APPROVAL_REQUIRED", "an exact approved Storyboard decision is required")
            existing = self._existing(package_reference)
            if existing is not None:
                result = _stored_result(existing, self._workspace, task_id)
                requested = tuple(refs.values())
                stored = (result.source_record_reference, result.script_reference, result.character_reference, result.storyboard_reference, result.timeline_reference, result.production_request_reference, result.scene_generation_contract_reference)
                if requested != stored or result.storyboard_decision_id != storyboard_decision_id:
                    raise _Invalid("HANDOFF_PACKAGE_CONFLICT", "accepted handoff package inputs conflict with the existing package")
                if output_reference != result.output_reference:
                    raise _Invalid("HANDOFF_PACKAGE_CONFLICT", "accepted handoff package output conflicts with the existing package")
                return result

            versions = {name: _version(reference, self._artifacts.get(reference), "INVALID_HANDOFF_LINEAGE") for name, reference in refs.items()}
            self._validate_lineage(refs, versions, decision, storyboard_decision_id)
            stills, still_failure = _read_stills(reference_stills_directory)
            if still_failure is not None:
                return still_failure
            preflight = self._renderer.preflight()
            if isinstance(preflight, ProductionMediaFailure):
                return _failure("validation", preflight.code, "local narration runtime readiness failed; configure the approved local runtime and retry")
            if type(preflight) is not LocalNarrationPreflight:
                raise _Invalid("HANDOFF_NARRATION_PREFLIGHT_FAILED", "local narration runtime facts are invalid")
            narration_metadata = _metadata(self._renderer, preflight)
            contract_payload = versions["scene_generation_contract"].payload
            entries = contract_payload["scene_generation_contract"]["scenes"]
            if type(entries) is not tuple or len(entries) != 6:
                raise _Invalid("INVALID_HANDOFF_LINEAGE", "Scene Generation Contract must contain six Scenes")
            entries = tuple(entry for entry in entries if isinstance(entry, Mapping))
            if len(entries) != 6 or tuple(entry.get("scene_id") for entry in entries) != _SCENE_IDS:
                raise _Invalid("INVALID_HANDOFF_LINEAGE", "Scene Generation Contract order is invalid")
            for entry in entries:
                duration_milliseconds = entry.get("duration_milliseconds")
                if type(duration_milliseconds) is not int or isinstance(duration_milliseconds, bool) or duration_milliseconds <= 0:
                    raise _Invalid("INVALID_HANDOFF_LINEAGE", "Scene Generation Contract duration is invalid")
                _text(entry.get("narration"), "INVALID_HANDOFF_LINEAGE")
            narration_references = tuple(WorkspaceFileReference(task_id, "media", f"handoff-narration-scene-{index}.m4a") for index in range(1, 7))
            language = versions["production_request"].payload["production_request"].get("language", "Simplified Chinese")
            _text(language, "INVALID_HANDOFF_LINEAGE", max_length=128)

            prepared = self._workspace.prepare(task_id)
            if not hasattr(prepared, "task_id"):
                raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "handoff workspace is unavailable")

            # Bind each staged narration to the exact accepted inputs and local
            # runtime facts before any inference begins.  These records stay in
            # task-scoped Workspace staging and are deliberately excluded from
            # the package ZIP and Artifact payload.
            bindings = tuple(
                {
                    "schema_version": 1,
                    "production_request_reference": refs["production_request"],
                    "scene_generation_contract_reference": refs["scene_generation_contract"],
                    "scene_id": entry["scene_id"],
                    "narration": entry["narration"],
                    "duration_seconds": entry["duration_milliseconds"] / 1000,
                    "language": language,
                    "output_reference": output,
                    "local_narration": {**narration_metadata, "reference_audio": preflight.reference_audio},
                }
                for entry, output in zip(entries, narration_references, strict=True)
            )
            binding_references = tuple(
                WorkspaceFileReference(task_id, _HANDOFF_BINDING_AREA, f"handoff-narration-scene-{index}.binding.json")
                for index in range(1, 7)
            )
            binding_bytes = tuple(_canonical_json(binding) for binding in bindings)
            missing_bindings: list[tuple[WorkspaceFileReference, bytes]] = []
            for binding_reference, expected_binding, output in zip(binding_references, binding_bytes, narration_references, strict=True):
                staged_binding = self._workspace.read(binding_reference)
                if isinstance(staged_binding, bytes):
                    if staged_binding != expected_binding:
                        raise _Invalid("HANDOFF_PACKAGE_CONFLICT", "staged narration binding conflicts with the accepted inputs")
                    continue
                if not isinstance(staged_binding, WorkspaceFailure):
                    raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "staged narration binding is unavailable")
                if staged_binding.code != "WORKSPACE_FILE_NOT_FOUND":
                    raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "staged narration binding is unavailable")
                staged_audio = self._workspace.read(output)
                if isinstance(staged_audio, bytes) and staged_audio:
                    raise _Invalid("HANDOFF_PACKAGE_CONFLICT", "staged narration is missing its accepted binding")
                if not isinstance(staged_audio, WorkspaceFailure) or staged_audio.code != "WORKSPACE_FILE_NOT_FOUND":
                    raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "staged narration output is unavailable")
                missing_bindings.append((binding_reference, expected_binding))
            for binding_reference, expected_binding in missing_bindings:
                stored_binding = self._workspace.commit(binding_reference, expected_binding)
                if type(stored_binding) is not WorkspaceFileRecord or stored_binding.reference != binding_reference or stored_binding.size_bytes != len(expected_binding):
                    if isinstance(stored_binding, WorkspaceFailure) and stored_binding.code == "WORKSPACE_FILE_CONFLICT":
                        raise _Invalid("HANDOFF_PACKAGE_CONFLICT", "staged narration binding conflicts with the accepted inputs")
                    raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "staged narration binding could not be stored")

            narration_bytes: list[bytes] = []
            for entry, output in zip(entries, narration_references, strict=True):
                staged = self._workspace.read(output)
                if isinstance(staged, bytes) and staged:
                    narration_bytes.append(staged)
                    continue
                if isinstance(staged, WorkspaceFailure) and staged.code != "WORKSPACE_FILE_NOT_FOUND":
                    raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "staged narration output is unavailable")
                task = LocalNarrationTask(task_id, refs["production_request"], entry["scene_id"], language, entry["duration_milliseconds"] / 1000, entry["narration"], output)
                rendered = self._renderer.render(task)
                if isinstance(rendered, ProductionMediaFailure):
                    return _failure("execution", rendered.code, "local narration failed safely; no Handoff Package Artifact was committed")
                if type(rendered) is not LocalNarrationResult or rendered.task_id != task_id or rendered.scene_id != entry["scene_id"] or rendered.output_reference != output or rendered.media_type != _AUDIO_MEDIA_TYPE or rendered.result_code != "SUCCESS":
                    raise _Invalid("HANDOFF_NARRATION_INVALID", "local narration result is invalid")
                if not _valid_duration(rendered.duration_seconds) or rendered.duration_seconds != task.duration_seconds:
                    raise _Invalid("HANDOFF_NARRATION_INVALID", "local narration result duration is invalid")
                content = self._workspace.read(output)
                if not isinstance(content, bytes) or not content:
                    raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "local narration output was not durably stored")
                narration_bytes.append(content)

            contract_json = _canonical_json(versions["scene_generation_contract"].payload)
            timeline_json = _canonical_json(versions["timeline"].payload)
            subtitles = _render_srt(entries)
            guide = _render_guide(task_id, refs, entries)
            provenance_document = {
                "schema_version": 1,
                "task_id": task_id,
                "source_reference": refs["source"],
                "script_reference": refs["script"],
                "storyboard_reference": refs["storyboard"],
                "timeline_reference": refs["timeline"],
                "production_request_reference": refs["production_request"],
                "scene_generation_contract_reference": refs["scene_generation_contract"],
                "storyboard_decision_id": storyboard_decision_id,
                "local_tts": narration_metadata,
                "manual_generation": {
                    "outside_application": True,
                    "providers": ["Jimeng", "Kling"],
                    "application_provider_attempt": False,
                    "application_charge_micros": 0,
                    "subscription_cost_controlled": False,
                },
            }
            provenance = _canonical_json(provenance_document)
            still_readme = b"# Optional reference stills\n\nThese stills are optional visual references only. They are not generated Scene clips or final media.\n"
            preliminary = (
                ("generation-guide.md", guide),
                ("scene-generation-contract.json", contract_json),
                ("timeline.json", timeline_json),
                ("subtitles.srt", subtitles),
                *( (f"narration/scene-{index}.m4a", content) for index, content in enumerate(narration_bytes, start=1) ),
                ("provenance.json", provenance),
                ("reference-stills/README.md", still_readme),
                *( (f"reference-stills/scene-{index}.png", stills[name]) for index, name in enumerate(_STILL_NAMES, start=1) ),
            )
            file_facts = tuple(MappingProxyType({"name": name, "media_type": "application/json" if name.endswith(".json") else "text/markdown" if name.endswith(".md") else "text/plain" if name.endswith(".srt") else _AUDIO_MEDIA_TYPE if name.endswith(".m4a") else "image/png", "size_bytes": len(content), "sha256": _sha(content)}) for name, content in preliminary)
            manifest = _canonical_json({
                "schema_version": 1,
                "task_id": task_id,
                "references": {name: reference for name, reference in refs.items()},
                "storyboard_decision_id": storyboard_decision_id,
                "scenes": tuple({"scene_id": entry["scene_id"], "expected_filename": entry["expected_filename"], "duration_milliseconds": entry["duration_milliseconds"], "narration_path": f"narration/scene-{index}.m4a"} for index, entry in enumerate(entries, start=1)),
                "files": file_facts,
                "manual_generation": {"outside_application": True, "application_provider_attempt": False, "application_charge_micros": 0, "subscription_cost_controlled": False},
            })
            entries_with_manifest = (*preliminary, ("handoff-manifest.json", manifest))
            package_bytes = _zip(entries_with_manifest)
            stored_package = self._workspace.commit(output_reference, package_bytes)
            if type(stored_package) is not WorkspaceFileRecord or stored_package.size_bytes != len(package_bytes):
                if isinstance(stored_package, WorkspaceFailure) and stored_package.code == "WORKSPACE_FILE_CONFLICT":
                    return _failure("validation", "HANDOFF_PACKAGE_CONFLICT", "accepted handoff package bytes conflict with prior staged output")
                raise _Invalid("HANDOFF_PACKAGE_STORAGE_FAILED", "handoff package output could not be stored")
            payload = {
                "task_id": task_id,
                "source_record_reference": refs["source"],
                "script_reference": refs["script"],
                "character_reference": refs["character"],
                "storyboard_reference": refs["storyboard"],
                "timeline_reference": refs["timeline"],
                "production_request_reference": refs["production_request"],
                "scene_generation_contract_reference": refs["scene_generation_contract"],
                "storyboard_decision_id": storyboard_decision_id,
                "narration_references": tuple(_workspace_json(reference) for reference in narration_references),
                "output_reference": _workspace_json(output_reference),
                "file_facts": file_facts,
                "local_narration": narration_metadata,
                "manual_generation": {"outside_application": True, "application_provider_attempt": False, "application_charge_micros": 0, "subscription_cost_controlled": False},
            }
            candidate = ArtifactCandidate(_HANDOFF_ARTIFACT, artifact_identity, payload, (provenance_document,), tuple(refs.values()), True, package_commit_id)
            try:
                committed = self._artifacts.commit(candidate)
            except Exception as error:
                code = getattr(error, "code", "HANDOFF_ARTIFACT_COMMIT_FAILED")
                return _failure("validation" if code == "COMMIT_CONFLICT" else "execution", "HANDOFF_PACKAGE_CONFLICT" if code == "COMMIT_CONFLICT" else "HANDOFF_ARTIFACT_COMMIT_FAILED", "Handoff Package Artifact persistence failed safely")
            if type(committed) is not ArtifactReference or committed != package_reference:
                raise _Invalid("HANDOFF_ARTIFACT_COMMIT_FAILED", "Handoff Package Artifact persistence failed safely")
            return HandoffPackageResult(task_id, refs["source"], refs["script"], refs["character"], refs["storyboard"], refs["timeline"], refs["production_request"], refs["scene_generation_contract"], storyboard_decision_id, narration_references, committed, output_reference, file_facts, "SUCCESS")
        except _Invalid as error:
            return _failure("validation", error.code, error.message)
        except Exception:
            return _failure("execution", "HANDOFF_PACKAGE_FAILED", "Creator Handoff Package could not be prepared safely")

    def _existing(self, reference: ArtifactReference) -> ArtifactVersion | None:
        try:
            value = self._artifacts.get(reference)
        except Exception as error:
            if type(error) is ArtifactNotFoundError:
                return None
            raise _Invalid("HANDOFF_ARTIFACT_STORAGE_FAILED", "handoff Artifact replay lookup failed safely") from None
        if type(value) is not ArtifactVersion or type(value.reference) is not ArtifactReference or value.reference != reference:
            raise _Invalid("HANDOFF_ARTIFACT_STORAGE_FAILED", "handoff Artifact replay lookup returned invalid data")
        return value

    @staticmethod
    def _validate_task(task_id: object) -> None:
        if type(task_id) is not str or not task_id or len(task_id) > 128 or task_id[0] not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789":
            raise _Invalid("INVALID_TASK_ID", "task identity is invalid")

    def _validate_lineage(self, refs: Mapping[str, ArtifactReference], versions: Mapping[str, ArtifactVersion], decision: StoryboardDecisionRecord, decision_id: str) -> None:
        source_payload = versions["source"].payload
        if type(source_payload) not in (dict, MappingProxyType) or source_payload.get("source_kind") != "github":
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Source lineage is invalid")
        if not self._reachable(versions["script"].reference, refs["source"]):
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Source is not reachable from the exact Script")
        storyboard = versions["storyboard"]
        timeline = versions["timeline"]
        request = versions["production_request"]
        contract = versions["scene_generation_contract"]
        if storyboard.dependencies != (refs["script"], refs["character"]):
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Storyboard lineage is invalid")
        if timeline.dependencies != (refs["script"], refs["character"], refs["storyboard"]):
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Timeline lineage is invalid")
        if request.dependencies != (refs["script"], refs["character"], refs["storyboard"], refs["timeline"]):
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Production Request lineage is invalid")
        if contract.dependencies != (refs["script"], refs["character"], refs["storyboard"], refs["timeline"], refs["production_request"]):
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Scene Generation Contract lineage is invalid")
        timeline_payload = timeline.payload
        request_payload = request.payload
        if (
            type(timeline_payload) not in (dict, MappingProxyType)
            or timeline_payload.get("script_reference") != refs["script"]
            or timeline_payload.get("character_reference") != refs["character"]
            or timeline_payload.get("storyboard_reference") != refs["storyboard"]
            or timeline_payload.get("timeline_reference") is not None and timeline_payload.get("timeline_reference") != refs["timeline"]
            or type(request_payload) not in (dict, MappingProxyType)
            or request_payload.get("script_reference") != refs["script"]
            or request_payload.get("character_reference") != refs["character"]
            or request_payload.get("storyboard_reference") != refs["storyboard"]
            or request_payload.get("timeline_reference") != refs["timeline"]
        ):
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Timeline or Production Request lineage is invalid")
        payload = contract.payload
        if set(payload) != {"script_reference", "approval_decision_id", "character_reference", "storyboard_reference", "storyboard_decision_id", "timeline_reference", "production_request_reference", "scene_generation_contract"} or payload["script_reference"] != refs["script"] or payload["character_reference"] != refs["character"] or payload["storyboard_reference"] != refs["storyboard"] or payload["timeline_reference"] != refs["timeline"] or payload["production_request_reference"] != refs["production_request"] or payload["approval_decision_id"] != decision.script_approval_decision_id or payload["storyboard_decision_id"] != decision_id:
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Scene Generation Contract references are invalid")

        entries = payload["scene_generation_contract"].get("scenes") if isinstance(payload.get("scene_generation_contract"), Mapping) else None
        if type(entries) is not tuple or len(entries) != 6 or tuple(entry.get("scene_id") for entry in entries if isinstance(entry, Mapping)) != _SCENE_IDS:
            raise _Invalid("INVALID_HANDOFF_LINEAGE", "Scene Generation Contract scenes are invalid")

    def _reachable(self, start: ArtifactReference, target: ArtifactReference) -> bool:
        pending = [start]
        seen: set[ArtifactReference] = set()
        for _ in range(256):
            if not pending:
                return False
            reference = pending.pop(0)
            if reference == target:
                return True
            if reference in seen:
                continue
            seen.add(reference)
            try:
                version = self._artifacts.get(reference)
            except Exception:
                return False
            if type(version) is not ArtifactVersion or type(version.dependencies) is not tuple:
                return False
            pending.extend(item for item in version.dependencies if type(item) is ArtifactReference)
        return False


__all__ = ["CreatorHandoffPackageBuilder", "HandoffPackageFailure", "HandoffPackageResult"]
