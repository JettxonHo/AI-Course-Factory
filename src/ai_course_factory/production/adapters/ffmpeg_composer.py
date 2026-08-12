"""Local FFmpeg MediaComposer for validated playable Fixture media."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import (
    WorkspaceAdapter,
    WorkspaceFileReference,
)

from ..model import (
    MediaCompositionResult,
    MediaCompositionScene,
    MediaCompositionTask,
    MediaGenerationResult,
    ProductionMediaFailure,
)
from . import fake as _fake
from . import ffmpeg_fixture as _fixture


_COMPOSER = "ffmpeg-composer-v1"
_MEDIA_TYPE = "video/mp4"
_MAX_SCENES = 32
_MAX_DURATION_MILLISECONDS = 3_600_000
_MAX_MEDIA_BYTES = 64 * 1024 * 1024
_INPUT_DURATION_TOLERANCE = 0.10
_OUTPUT_DURATION_TOLERANCE = 0.15
_BINDING_PREFIX = "ai-course-factory-ffmpeg-composer-v1:"
_MP4_FORMAT = "mov,mp4,m4a,3gp,3g2,mj2"


def _failure(kind: str, code: str, message: str) -> ProductionMediaFailure:
    return ProductionMediaFailure(kind, code, message)


def _invalid_task() -> ProductionMediaFailure:
    return _failure("validation", "INVALID_COMPOSITION_TASK", "media composition task is invalid")

def _tool_unavailable() -> ProductionMediaFailure:
    return _failure("validation", "MEDIA_TOOL_UNAVAILABLE", "media tool configuration is unavailable")


def _timeout_invalid() -> ProductionMediaFailure:
    return _failure("validation", "INVALID_MEDIA_TOOL_TIMEOUT", "media tool timeout is invalid")


def _composition_failed() -> ProductionMediaFailure:
    return _failure("execution", "MEDIA_COMPOSITION_FAILED", "local media composition failed")


def _safe_identity(value: object, limit: int = 256) -> bool:
    return (
        type(value) is str
        and bool(value.strip())
        and len(value) <= limit
        and value.strip().casefold() not in {"latest", "current"}
        and all(ord(character) >= 32 and ord(character) != 127 for character in value)
    )


def _safe_subtitle(value: object) -> bool:
    return (
        type(value) is str
        and bool(value.strip())
        and len(value) <= 4096
        and all(ord(character) >= 32 and ord(character) != 127 for character in value)
    )


def _safe_artifact_reference(value: object, artifact_type: str) -> bool:
    return (
        type(value) is ArtifactReference
        and type(value.artifact_type) is str
        and value.artifact_type == artifact_type
        and _safe_identity(value.identity)
        and type(value.version) is int
        and 1 <= value.version <= 2**63 - 1
    )


def _safe_workspace_reference(value: object, task_id: str) -> bool:
    if (
        type(value) is not WorkspaceFileReference
        or type(value.task_id) is not str
        or type(value.area) is not str
        or type(value.name) is not str
    ):
        return False
    try:
        _fake._safe_output_reference(value, task_id)
    except Exception:
        return False
    return True


def _workspace_key(value: WorkspaceFileReference) -> tuple[str, str, str]:
    return (value.task_id, value.area, value.name)


def _duration_seconds(value: object) -> float | None:
    if type(value) is int or type(value) is float:
        try:
            number = float(value)
        except (OverflowError, ValueError):
            return None
        if math.isfinite(number) and number > 0 and number <= 3600:
            return number
    return None

def _duration_milliseconds(value: object) -> bool:
    return type(value) is int and 0 <= value <= _MAX_DURATION_MILLISECONDS


def _result_valid(
    result: object,
    scene_id: str,
    task_id: str,
    operation: str,
    media_type: str,
    start_milliseconds: int,
    end_milliseconds: int,
) -> bool:
    if type(result) is not MediaGenerationResult:
        return False
    if (
        not _safe_identity(result.attempt_id)
        or result.scene_id != scene_id
        or type(result.scene_id) is not str
        or result.operation != operation
        or type(result.operation) is not str
        or not _safe_identity(result.provider)
        or result.media_type != media_type
        or type(result.media_type) is not str
        or result.result_code != "SUCCESS"
        or type(result.result_code) is not str
        or not _safe_workspace_reference(result.output_reference, task_id)
    ):
        return False
    duration = _duration_seconds(result.duration_seconds)
    expected = (end_milliseconds - start_milliseconds) / 1000
    return duration is not None and abs(duration - expected) <= _INPUT_DURATION_TOLERANCE


def _task_valid(task: object) -> bool:
    if type(task) is not MediaCompositionTask:
        return False
    if not _safe_identity(task.task_id) or not _safe_identity(task.composition_id):
        return False
    try:
        _fake._safe_workspace_task(task.task_id)
    except Exception:
        return False
    if (
        not _safe_artifact_reference(task.production_request_reference, "production_request")
        or not _safe_artifact_reference(task.timeline_reference, "timeline")
        or not _safe_workspace_reference(task.output_reference, task.task_id)
        or type(task.scenes) is not tuple
        or not 1 <= len(task.scenes) <= _MAX_SCENES
    ):
        return False
    if type(task.output_reference) is not WorkspaceFileReference:
        return False
    scene_ids: set[str] = set()
    expected_start = 0
    for scene in task.scenes:
        if type(scene) is not MediaCompositionScene:
            return False
        if not _safe_identity(scene.scene_id, 128) or scene.scene_id in scene_ids:
            return False
        scene_ids.add(scene.scene_id)
        if (
            not _duration_milliseconds(scene.start_milliseconds)
            or not _duration_milliseconds(scene.end_milliseconds)
            or scene.start_milliseconds != expected_start
            or scene.end_milliseconds <= scene.start_milliseconds
            or not _safe_subtitle(scene.subtitle_text)
        ):
            return False
        if (
            not _result_valid(
                scene.visual_result, scene.scene_id, task.task_id, "visual", "video/mp4",
                scene.start_milliseconds, scene.end_milliseconds,
            )
            or not _result_valid(
                scene.voice_result, scene.scene_id, task.task_id, "voice", "audio/mp4",
                scene.start_milliseconds, scene.end_milliseconds,
            )
        ):
            return False
        visual_key = _workspace_key(scene.visual_result.output_reference)
        voice_key = _workspace_key(scene.voice_result.output_reference)
        if visual_key == voice_key or visual_key == _workspace_key(task.output_reference) or voice_key == _workspace_key(task.output_reference):
            return False
        expected_start = scene.end_milliseconds
    return 0 < expected_start <= _MAX_DURATION_MILLISECONDS


def _reference_payload(reference: ArtifactReference) -> dict[str, object]:
    return {
        "artifact_type": reference.artifact_type,
        "identity": reference.identity,
        "version": reference.version,
    }


def _workspace_payload(reference: WorkspaceFileReference) -> dict[str, str]:
    return {"area": reference.area, "name": reference.name, "task_id": reference.task_id}


def _result_payload(result: MediaGenerationResult) -> dict[str, object]:
    return {
        "attempt_id": result.attempt_id,
        "duration_seconds": result.duration_seconds,
        "media_type": result.media_type,
        "operation": result.operation,
        "output_reference": _workspace_payload(result.output_reference),
        "provider": result.provider,
        "result_code": result.result_code,
        "scene_id": result.scene_id,
    }


def _task_payload(task: MediaCompositionTask) -> dict[str, object]:
    return {
        "composition_id": task.composition_id,
        "output_reference": _workspace_payload(task.output_reference),
        "production_request_reference": _reference_payload(task.production_request_reference),
        "scenes": [
            {
                "end_milliseconds": scene.end_milliseconds,
                "scene_id": scene.scene_id,
                "start_milliseconds": scene.start_milliseconds,
                "subtitle_text": scene.subtitle_text,
                "visual_result": _result_payload(scene.visual_result),
                "voice_result": _result_payload(scene.voice_result),
            }
            for scene in task.scenes
        ],
        "task_id": task.task_id,
        "timeline_reference": _reference_payload(task.timeline_reference),
    }


def _binding(task: MediaCompositionTask) -> str:
    encoded = json.dumps(
        _task_payload(task), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    ).encode("utf-8")
    return _BINDING_PREFIX + hashlib.sha256(encoded).hexdigest()


def _input_probe_valid(
    probe: Mapping[str, Any], result: MediaGenerationResult, expected_seconds: float,
) -> float | None:
    streams = probe.get("streams")
    format_value = probe.get("format")
    if (
        type(streams) is not list
        or len(streams) != 1
        or not isinstance(streams[0], Mapping)
        or not isinstance(format_value, Mapping)
        or format_value.get("format_name") != _MP4_FORMAT
    ):
        return None
    stream = streams[0]
    duration = _fixture._number(stream.get("duration"))
    if duration is None or abs(duration - expected_seconds) > _INPUT_DURATION_TOLERANCE:
        return None
    if result.operation == "visual":
        valid = (
            stream.get("codec_type") == "video"
            and stream.get("codec_name") == "h264"
            and type(stream.get("width")) is int
            and type(stream.get("height")) is int
            and stream.get("width") == 540
            and stream.get("height") == 960
            and stream.get("pix_fmt") == "yuv420p"
            and _fixture._is_24_fps(stream.get("r_frame_rate"))
            and _fixture._is_24_fps(stream.get("avg_frame_rate"))
        )
    else:
        valid = (
            stream.get("codec_type") == "audio"
            and stream.get("codec_name") == "aac"
            and stream.get("sample_rate") in {"48000", 48000}
            and type(stream.get("channels")) is int
            and stream.get("channels") == 1
        )
    return duration if valid else None


def _final_probe_valid(probe: Mapping[str, Any], binding: str, expected_seconds: float) -> bool:
    streams = probe.get("streams")
    format_value = probe.get("format")
    if (
        type(streams) is not list
        or len(streams) != 3
        or not isinstance(format_value, Mapping)
        or format_value.get("format_name") != _MP4_FORMAT
        or not _fixture._tags_contain_binding(probe, binding)
    ):
        return False
    videos = [stream for stream in streams if isinstance(stream, Mapping) and stream.get("codec_type") == "video"]
    audios = [stream for stream in streams if isinstance(stream, Mapping) and stream.get("codec_type") == "audio"]
    subtitles = [stream for stream in streams if isinstance(stream, Mapping) and stream.get("codec_type") == "subtitle"]
    if len(videos) != 1 or len(audios) != 1 or len(subtitles) != 1:
        return False
    video, audio, subtitle = videos[0], audios[0], subtitles[0]
    video_duration = _fixture._number(video.get("duration"))
    format_duration = _fixture._number(format_value.get("duration"))
    return (
        video.get("codec_name") == "h264"
        and type(video.get("width")) is int and video.get("width") == 540
        and type(video.get("height")) is int and video.get("height") == 960
        and video.get("pix_fmt") == "yuv420p"
        and _fixture._is_24_fps(video.get("r_frame_rate"))
        and _fixture._is_24_fps(video.get("avg_frame_rate"))
        and audio.get("codec_name") == "aac"
        and audio.get("sample_rate") in {"48000", 48000}
        and type(audio.get("channels")) is int and audio.get("channels") == 1
        and subtitle.get("codec_name") == "mov_text"
        and video_duration is not None
        and abs(video_duration - expected_seconds) <= _OUTPUT_DURATION_TOLERANCE
        and format_duration is not None
        and abs(format_duration - expected_seconds) <= _OUTPUT_DURATION_TOLERANCE
    )


def _srt_timestamp(milliseconds: int) -> str:
    seconds, millis = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _srt_content(task: MediaCompositionTask) -> str:
    cues: list[str] = []
    for index, scene in enumerate(task.scenes, start=1):
        cues.extend(
            (
                str(index),
                f"{_srt_timestamp(scene.start_milliseconds)} --> {_srt_timestamp(scene.end_milliseconds)}",
                scene.subtitle_text,
                "",
            )
        )
    return "\n".join(cues)


class FFmpegMediaComposer:
    """Compose ordered playable local Fixture scenes into one MP4."""

    __slots__ = ("_workspace", "_ffmpeg_executable", "_ffprobe_executable", "_timeout_seconds")

    def __init__(
        self,
        workspace: WorkspaceAdapter,
        *,
        ffmpeg_executable: str,
        ffprobe_executable: str,
        timeout_seconds: int | float = 60,
    ) -> None:
        self._workspace = workspace
        self._ffmpeg_executable = ffmpeg_executable
        self._ffprobe_executable = ffprobe_executable
        self._timeout_seconds = timeout_seconds

    def _configuration_failure(self) -> ProductionMediaFailure | None:
        if not _fixture._tools_valid(self._ffmpeg_executable, self._ffprobe_executable):
            return _tool_unavailable()
        if not _fixture._timeout_valid(self._timeout_seconds):
            return _timeout_invalid()
        return None

    def _compose(self, task: MediaCompositionTask) -> bytes | ProductionMediaFailure:
        total_seconds = task.scenes[-1].end_milliseconds / 1000
        binding = _binding(task)
        with TemporaryDirectory(prefix="acf-ffmpeg-compose-") as directory:
            root = Path(directory)
            visual_paths: list[Path] = []
            voice_paths: list[Path] = []
            durations: list[tuple[float, float]] = []
            for index, scene in enumerate(task.scenes):
                visual = self._read_input(scene.visual_result.output_reference)
                voice = self._read_input(scene.voice_result.output_reference)
                if isinstance(visual, ProductionMediaFailure) or isinstance(voice, ProductionMediaFailure):
                    return _composition_failed()
                visual_path = root / f"scene-{index:02d}-visual.mp4"
                voice_path = root / f"scene-{index:02d}-voice.m4a"
                try:
                    visual_path.write_bytes(visual)
                    voice_path.write_bytes(voice)
                    visual_probe = _fixture._probe(visual_path, self._ffprobe_executable, self._timeout_seconds)
                    voice_probe = _fixture._probe(voice_path, self._ffprobe_executable, self._timeout_seconds)
                except Exception:
                    return _composition_failed()
                expected = (scene.end_milliseconds - scene.start_milliseconds) / 1000
                visual_duration = (
                    _input_probe_valid(visual_probe, scene.visual_result, expected)
                    if visual_probe is not None else None
                )
                voice_duration = (
                    _input_probe_valid(voice_probe, scene.voice_result, expected)
                    if voice_probe is not None else None
                )
                if visual_duration is None or voice_duration is None:
                    return _composition_failed()
                visual_paths.append(visual_path)
                voice_paths.append(voice_path)
                durations.append((visual_duration, voice_duration))
            srt_path = root / "subtitles.srt"
            output_path = root / "composition.mp4"
            try:
                srt_path.write_text(_srt_content(task), encoding="utf-8", newline="\n")
            except (OSError, ValueError):
                return _composition_failed()
            filter_parts: list[str] = []
            video_labels: list[str] = []
            audio_labels: list[str] = []
            for index, scene in enumerate(task.scenes):
                target = (scene.end_milliseconds - scene.start_milliseconds) / 1000
                visual_duration, voice_duration = durations[index]
                visual_pad = max(0.0, target - visual_duration)
                voice_pad = max(0.0, target - voice_duration)
                visual_chain = f"[{2 * index}:v:0]setpts=PTS-STARTPTS,fps=24"
                if visual_pad > 0:
                    visual_chain += f",tpad=stop_mode=clone:stop_duration={visual_pad:.6f}"
                visual_chain += f",trim=duration={target:.6f},setpts=PTS-STARTPTS[v{index}]"
                audio_chain = f"[{2 * index + 1}:a:0]asetpts=PTS-STARTPTS,aresample=48000"
                if voice_pad > 0:
                    audio_chain += f",apad=pad_dur={voice_pad:.6f}"
                audio_chain += f",atrim=duration={target:.6f},asetpts=PTS-STARTPTS[a{index}]"
                filter_parts.extend((visual_chain, audio_chain))
                video_labels.append(f"[v{index}]")
                audio_labels.append(f"[a{index}]")
            filter_parts.append("".join(video_labels) + f"concat=n={len(video_labels)}:v=1:a=0[vout]")
            filter_parts.append("".join(audio_labels) + f"concat=n={len(audio_labels)}:v=0:a=1[aout]")
            argv: list[str] = [
                self._ffmpeg_executable, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
            ]
            for visual_path, voice_path in zip(visual_paths, voice_paths):
                argv.extend(("-i", str(visual_path), "-i", str(voice_path)))
            argv.extend(("-f", "srt", "-i", str(srt_path), "-filter_complex", ";".join(filter_parts)))
            subtitle_index = 2 * len(task.scenes)
            argv.extend(
                (
                    "-map", "[vout]", "-map", "[aout]", "-map", f"{subtitle_index}:s:0",
                    "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1", "-pix_fmt", "yuv420p", "-r", "24",
                    "-c:a", "aac", "-b:a", "64k", "-ar", "48000", "-ac", "1", "-c:s", "mov_text",
                    "-t", f"{total_seconds:.6f}", "-map_metadata", "-1", "-metadata", f"comment={binding}",
                    "-movflags", "+faststart", str(output_path),
                )
            )
            if _fixture._run(argv, self._timeout_seconds, capture_stdout=False) is None:
                return _composition_failed()
            output = _fixture._safe_result_bytes(output_path)
            if output is None:
                return _composition_failed()
            try:
                probe = _fixture._probe(output_path, self._ffprobe_executable, self._timeout_seconds)
            except Exception:
                return _composition_failed()
            if probe is None or not _final_probe_valid(probe, binding, total_seconds):
                return _composition_failed()
            return output

    def _read_input(self, reference: WorkspaceFileReference) -> bytes | ProductionMediaFailure:
        try:
            content = self._workspace.read(reference)
        except Exception:
            return _composition_failed()
        if type(content) is not bytes or not 1 <= len(content) <= _MAX_MEDIA_BYTES:
            return _composition_failed()
        return content

    def compose(self, task: MediaCompositionTask) -> MediaCompositionResult | ProductionMediaFailure:
        if not _task_valid(task):
            return _invalid_task()
        configuration_failure = self._configuration_failure()
        if configuration_failure is not None:
            return configuration_failure
        try:
            output = self._compose(task)
            if isinstance(output, ProductionMediaFailure):
                return output
            failure = _fake._commit_fixture(self._workspace, task.output_reference, output)
            if failure is not None:
                return failure
            return MediaCompositionResult(
                task.composition_id,
                task.production_request_reference,
                task.timeline_reference,
                tuple(scene.scene_id for scene in task.scenes),
                _COMPOSER,
                task.output_reference,
                _MEDIA_TYPE,
                task.scenes[-1].end_milliseconds,
                "SUCCESS",
            )
        except Exception:
            return _composition_failed()


__all__ = ["FFmpegMediaComposer"]
