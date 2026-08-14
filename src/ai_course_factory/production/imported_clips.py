"""Explicit creator-generated Scene video import and local normalization.

The directory is supplied by the operator at application startup.  This
module owns only the untrusted file boundary: it preflights the complete set,
normalizes every clip to the existing playable video contract, and returns
ordered Workspace references.  Artifact and Task commits remain application
responsibilities so a failed preflight cannot expose a partial selection.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import stat
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from ai_course_factory.persistence import WorkspaceAdapter, WorkspaceFileReference, WorkspaceFailure, WorkspaceFileRecord

from .adapters import ffmpeg_fixture as _fixture
from .model import ProductionMediaFailure


_MEDIA_TYPE = "video/mp4"
_MAX_MEDIA_BYTES = 256 * 1024 * 1024
_INPUT_DURATION_TOLERANCE = 0.25
_OUTPUT_DURATION_TOLERANCE = 0.08
_TOOL_TIMEOUT_MIN = 1
_TOOL_TIMEOUT_MAX = 120
_SCENE_IDS = tuple(f"scene-{index}" for index in range(1, 7))
_INITIAL_NAMES = tuple(f"scene-{index}.mp4" for index in range(1, 7))
_REPLACEMENT_NAME = "scene-2-replacement.mp4"


@dataclass(frozen=True, slots=True)
class ImportedSceneClip:
    scene_id: str
    declared_filename: str
    output_reference: WorkspaceFileReference
    media_type: str
    duration_milliseconds: int
    creator_provenance: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class CreatorSceneClipImportSuccess:
    task_id: str
    clips: tuple[ImportedSceneClip, ...]
    result_code: str = "SUCCESS"

    def __post_init__(self) -> None:
        object.__setattr__(self, "clips", tuple(self.clips))

    @property
    def output_references(self) -> tuple[WorkspaceFileReference, ...]:
        return tuple(item.output_reference for item in self.clips)


@dataclass(frozen=True, slots=True)
class CreatorSceneClipImportFailure:
    kind: str
    code: str
    message: str
    invalid_filenames: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "invalid_filenames", tuple(self.invalid_filenames))


@dataclass(frozen=True, slots=True)
class CreatorSceneImportSpec:
    scene_id: str
    duration_milliseconds: int
    declared_filename: str
    output_reference: WorkspaceFileReference


def _failure(code: str, message: str, filenames: tuple[str, ...] = ()) -> CreatorSceneClipImportFailure:
    return CreatorSceneClipImportFailure("validation", code, message, filenames)


def _number(value: object) -> float | None:
    if type(value) in (int, float) and not isinstance(value, bool):
        result = float(value)
    elif type(value) is str:
        try:
            result = float(value)
        except (TypeError, ValueError):
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def _duration_matches(value: object, expected_milliseconds: int, tolerance: float = _INPUT_DURATION_TOLERANCE) -> bool:
    actual = _number(value)
    return actual is not None and abs(actual - expected_milliseconds / 1000) <= tolerance


def _safe_tools(ffmpeg: object, ffprobe: object, timeout: object) -> bool:
    if not isinstance(ffmpeg, str) or not isinstance(ffprobe, str) or not ffmpeg or not ffprobe:
        return False
    if not Path(ffmpeg).is_absolute() or not Path(ffprobe).is_absolute() or ffmpeg == ffprobe:
        return False
    try:
        ffmpeg_info = Path(ffmpeg).stat()
        ffprobe_info = Path(ffprobe).stat()
        if not stat.S_ISREG(ffmpeg_info.st_mode) or not stat.S_ISREG(ffprobe_info.st_mode):
            return False
        if not (Path(ffmpeg).stat().st_mode & 0o111 and Path(ffprobe).stat().st_mode & 0o111):
            return False
    except (OSError, ValueError):
        return False
    return type(timeout) in (int, float) and not isinstance(timeout, bool) and _TOOL_TIMEOUT_MIN <= float(timeout) <= _TOOL_TIMEOUT_MAX


def _stream_contract(probe: Mapping[str, Any] | None, duration_milliseconds: int) -> bool:
    if not isinstance(probe, Mapping):
        return False
    streams = probe.get("streams")
    format_value = probe.get("format")
    if type(streams) is not list or not isinstance(format_value, Mapping) or format_value.get("format_name") != "mov,mp4,m4a,3gp,3g2,mj2":
        return False
    videos = [item for item in streams if isinstance(item, Mapping) and item.get("codec_type") == "video"]
    if len(videos) != 1:
        return False
    stream = videos[0]
    # The imported source must have one decodable video stream.  Audio,
    # subtitle and effect streams are intentionally ignored by normalization.
    return (
        _duration_matches(stream.get("duration"), duration_milliseconds)
        and type(stream.get("width")) is int and stream.get("width") > 0
        and type(stream.get("height")) is int and stream.get("height") > 0
    )


def _normalized_contract(probe: Mapping[str, Any] | None, duration_milliseconds: int) -> bool:
    if not isinstance(probe, Mapping):
        return False
    streams = probe.get("streams")
    format_value = probe.get("format")
    if type(streams) is not list or len(streams) != 1 or not isinstance(streams[0], Mapping) or not isinstance(format_value, Mapping):
        return False
    stream = streams[0]
    return (
        format_value.get("format_name") == "mov,mp4,m4a,3gp,3g2,mj2"
        and stream.get("codec_type") == "video"
        and stream.get("codec_name") == "h264"
        and stream.get("width") == 540
        and stream.get("height") == 960
        and stream.get("pix_fmt") == "yuv420p"
        and _fixture._is_24_fps(stream.get("r_frame_rate"))
        and _fixture._is_24_fps(stream.get("avg_frame_rate"))
        and _duration_matches(stream.get("duration"), duration_milliseconds, _OUTPUT_DURATION_TOLERANCE)
        and _duration_matches(format_value.get("duration"), duration_milliseconds, _OUTPUT_DURATION_TOLERANCE)
    )


class CreatorSceneClipImporter:
    """Preflight and normalize exact creator-generated MP4 names."""

    __slots__ = (
        "_workspace", "_directory", "_task_id", "_specs", "_ffmpeg", "_ffprobe", "_timeout",
    )

    def __init__(
        self,
        workspace: WorkspaceAdapter,
        import_directory: str | Path,
        *,
        task_id: str,
        scene_durations: tuple[tuple[str, int], ...] | None = None,
        ffmpeg_executable: str,
        ffprobe_executable: str,
        timeout_seconds: int | float = 60,
    ) -> None:
        self._workspace = workspace
        try:
            self._directory = Path(import_directory).expanduser().resolve()
        except (OSError, TypeError, ValueError):
            self._directory = Path("\0")
        self._task_id = task_id
        durations = scene_durations or tuple((scene_id, 10_000) for scene_id in _SCENE_IDS)
        self._specs = tuple(
            CreatorSceneImportSpec(scene_id, duration, f"{scene_id}.mp4", WorkspaceFileReference(task_id, "media", f"{scene_id}.mp4"))
            for scene_id, duration in durations
        )
        self._ffmpeg = ffmpeg_executable
        self._ffprobe = ffprobe_executable
        self._timeout = timeout_seconds

    @property
    def import_directory(self) -> Path:
        return self._directory

    def import_full_set(self) -> CreatorSceneClipImportSuccess | CreatorSceneClipImportFailure:
        return self._import(tuple(self._specs), "CREATOR_SCENE_IMPORT_PREFLIGHT_FAILED")

    def replace_scene_two(self) -> CreatorSceneClipImportSuccess | CreatorSceneClipImportFailure:
        spec = next((item for item in self._specs if item.scene_id == "scene-2"), None)
        if spec is None:
            return _failure("CREATOR_SCENE_REPLACEMENT_PREFLIGHT_FAILED", "Scene 2 is not part of the exact contract", (_REPLACEMENT_NAME,))
        replacement = CreatorSceneImportSpec("scene-2", spec.duration_milliseconds, _REPLACEMENT_NAME, WorkspaceFileReference(self._task_id, "media", _REPLACEMENT_NAME))
        return self._import((replacement,), "CREATOR_SCENE_REPLACEMENT_PREFLIGHT_FAILED")

    def _import(self, specs: tuple[CreatorSceneImportSpec, ...], error_code: str) -> CreatorSceneClipImportSuccess | CreatorSceneClipImportFailure:
        if not _safe_tools(self._ffmpeg, self._ffprobe, self._timeout):
            return _failure("MEDIA_TOOL_UNAVAILABLE", "media tool configuration is unavailable")
        if not self._directory_valid():
            return _failure(error_code, "Generated Scene import requires an explicit directory.", tuple(spec.declared_filename for spec in specs))
        invalid: list[str] = []
        probes: list[tuple[CreatorSceneImportSpec, Path, Mapping[str, Any]]] = []
        for spec in specs:
            path = self._directory / spec.declared_filename
            probe = self._probe_input(path)
            if probe is None or not _stream_contract(probe, spec.duration_milliseconds) or not self._decode(path):
                invalid.append(spec.declared_filename)
            else:
                probes.append((spec, path, probe))
        if invalid:
            return _failure(error_code, f"Generated Scene import requires valid MP4 files: {', '.join(invalid)}.", tuple(invalid))

        # Normalize into an isolated temporary directory first.  No task
        # Workspace bytes are written until every member has passed validation.
        normalized: list[tuple[CreatorSceneImportSpec, bytes, Mapping[str, Any]]] = []
        with TemporaryDirectory(prefix="acf-creator-scene-import-") as temporary:
            root = Path(temporary)
            for spec, source, source_probe in probes:
                output = root / spec.declared_filename
                if not self._normalize(source, output, spec.duration_milliseconds):
                    return _failure(error_code, f"Generated Scene import requires valid MP4 files: {spec.declared_filename}.", (spec.declared_filename,))
                content = _fixture._safe_result_bytes(output)
                normalized_probe = _fixture._probe(output, self._ffprobe, self._timeout) if content is not None else None
                if content is None or not _normalized_contract(normalized_probe, spec.duration_milliseconds) or not self._decode(output):
                    return _failure(error_code, f"Generated Scene import requires valid MP4 files: {spec.declared_filename}.", (spec.declared_filename,))
                normalized.append((spec, content, source_probe))

        clips: list[ImportedSceneClip] = []
        for spec, content, source_probe in normalized:
            stored = self._workspace.commit(spec.output_reference, content)
            if not isinstance(stored, WorkspaceFileRecord) or stored.reference != spec.output_reference or stored.size_bytes != len(content):
                if isinstance(stored, WorkspaceFailure) and stored.code == "WORKSPACE_FILE_CONFLICT":
                    return CreatorSceneClipImportFailure("execution", "CREATOR_SCENE_IMPORT_CONFLICT", "normalized Scene output conflicts with existing task media", (spec.declared_filename,))
                return CreatorSceneClipImportFailure("execution", "CREATOR_SCENE_IMPORT_STORAGE_FAILED", "normalized Scene media could not be stored", (spec.declared_filename,))
            clips.append(
                ImportedSceneClip(
                    spec.scene_id,
                    spec.declared_filename,
                    spec.output_reference,
                    _MEDIA_TYPE,
                    spec.duration_milliseconds,
                    {
                        "supplied_by": "creator",
                        "generated_outside_application": True,
                        "application_provider_attempt": False,
                        "application_charge_micros": 0,
                        "native_audio/subtitles/effects": "metadata_only",
                        "source_stream_count": len(source_probe.get("streams", ())) if isinstance(source_probe, Mapping) else 0,
                    },
                )
            )
        return CreatorSceneClipImportSuccess(self._task_id, tuple(clips))

    def _directory_valid(self) -> bool:
        try:
            info = self._directory.lstat()
            return stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode)
        except (OSError, ValueError):
            return False

    def _probe_input(self, path: Path) -> Mapping[str, Any] | None:
        try:
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_size < 1 or info.st_size > _MAX_MEDIA_BYTES:
                return None
            return _fixture._probe(path, self._ffprobe, self._timeout)
        except (OSError, ValueError):
            return None

    def _decode(self, path: Path) -> bool:
        try:
            return _fixture._run(
                [self._ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-i", str(path), "-map", "0:v:0", "-f", "null", "-"],
                self._timeout,
                capture_stdout=False,
            ) is not None
        except Exception:
            return False

    def _normalize(self, source: Path, output: Path, duration_milliseconds: int) -> bool:
        duration = f"{duration_milliseconds / 1000:.6f}"
        argv = [
            self._ffmpeg, "-hide_banner", "-nostdin", "-loglevel", "error", "-y", "-i", str(source),
            "-map", "0:v:0", "-an", "-sn", "-dn",
            "-vf", "scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
            "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1", "-pix_fmt", "yuv420p", "-r", "24", "-t", duration,
            "-map_metadata", "-1", "-movflags", "+faststart", str(output),
        ]
        try:
            return _fixture._run(argv, self._timeout, capture_stdout=False) is not None
        except Exception:
            return False


__all__ = [
    "CreatorSceneClipImporter",
    "CreatorSceneClipImportFailure",
    "CreatorSceneClipImportSuccess",
    "CreatorSceneImportSpec",
    "ImportedSceneClip",
]
