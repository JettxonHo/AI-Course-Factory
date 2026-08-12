"""Local, deterministic FFmpeg Fixture media adapters.

These adapters intentionally produce artificial media.  They are useful for the
offline production path, but are not evidence of a real visual or TTS provider.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from ai_course_factory.persistence import WorkspaceAdapter, WorkspaceFileReference

from ..interfaces import VisualGenerator, VoiceGenerator
from ..model import (
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VoiceSynthesisTask,
)
from . import fake as _fake


_VISUAL_PROVIDER = "ffmpeg-fixture-visual-v1"
_VOICE_PROVIDER = "ffmpeg-fixture-voice-v1"
_VISUAL_MEDIA_TYPE = "video/mp4"
_VOICE_MEDIA_TYPE = "audio/mp4"
_MAX_MEDIA_BYTES = 64 * 1024 * 1024
_MAX_PROBE_BYTES = 1 * 1024 * 1024
_DURATION_TOLERANCE = 0.10
_TOOL_TIMEOUT_MIN = 1
_TOOL_TIMEOUT_MAX = 120
_BINDING_PREFIX = "ai-course-factory-ffmpeg-fixture-v1:"
_GENERATION_FAILURE = "MEDIA_GENERATION_FAILED"
_MP4_FORMAT = "mov,mp4,m4a,3gp,3g2,mj2"


def _failure(kind: str, code: str, message: str) -> ProductionMediaFailure:
    return ProductionMediaFailure(kind, code, message)


def _tool_unavailable() -> ProductionMediaFailure:
    return _failure("validation", "MEDIA_TOOL_UNAVAILABLE", "media tool configuration is unavailable")


def _generation_failure() -> ProductionMediaFailure:
    return _failure("execution", _GENERATION_FAILURE, "local Fixture media generation failed")


def _timeout_valid(value: object) -> bool:
    if type(value) is int:
        return _TOOL_TIMEOUT_MIN <= value <= _TOOL_TIMEOUT_MAX
    return type(value) is float and math.isfinite(value) and _TOOL_TIMEOUT_MIN <= value <= _TOOL_TIMEOUT_MAX


def _tool_valid(value: object) -> bool:
    if type(value) is not str or not value or not os.path.isabs(value):
        return False
    try:
        info = os.stat(value)
        return stat.S_ISREG(info.st_mode) and os.access(value, os.X_OK)
    except (OSError, ValueError):
        return False


def _tools_valid(ffmpeg_executable: object, ffprobe_executable: object) -> bool:
    if not _tool_valid(ffmpeg_executable) or not _tool_valid(ffprobe_executable):
        return False
    try:
        return os.path.realpath(ffmpeg_executable) != os.path.realpath(ffprobe_executable)
    except (OSError, ValueError):
        return False


def _reference_payload(reference: object) -> dict[str, object]:
    return {
        "artifact_type": reference.artifact_type,
        "identity": reference.identity,
        "version": reference.version,
    }


def _workspace_payload(reference: WorkspaceFileReference) -> dict[str, str]:
    return {"area": reference.area, "name": reference.name, "task_id": reference.task_id}


def _task_payload(task: VisualGenerationTask | VoiceSynthesisTask) -> dict[str, object]:
    payload: dict[str, object] = {
        "attempt_id": task.attempt_id,
        "duration_seconds": task.duration_seconds,
        "output_reference": _workspace_payload(task.output_reference),
        "production_request_reference": _reference_payload(task.production_request_reference),
        "scene_id": task.scene_id,
        "task_id": task.task_id,
    }
    if type(task) is VisualGenerationTask:
        payload.update(
            {
                "aspect_ratio": task.aspect_ratio,
                "character_action": task.character_action,
                "visual_intent": task.visual_intent,
            }
        )
    else:
        payload.update({"language": task.language, "narration": task.narration})
    return payload


def _binding(task: VisualGenerationTask | VoiceSynthesisTask) -> str:
    encoded = json.dumps(
        _task_payload(task),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return _BINDING_PREFIX + hashlib.sha256(encoded).hexdigest()


def _duration_text(value: int | float) -> str:
    text = format(value, ".6f").rstrip("0").rstrip(".")
    return text if text else "0"


def _safe_result_bytes(path: Path) -> bytes | None:
    try:
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size < 1 or info.st_size > _MAX_MEDIA_BYTES:
            return None
        content = path.read_bytes()
        if type(content) is not bytes or len(content) != info.st_size or len(content) > _MAX_MEDIA_BYTES:
            return None
        return content
    except (OSError, ValueError):
        return None


def _run(argv: list[str], timeout_seconds: int | float, *, capture_stdout: bool) -> bytes | None:
    try:
        result = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE if capture_stdout else subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            timeout=timeout_seconds,
            check=False,
        )
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    if type(result.returncode) is not int or result.returncode != 0:
        return None
    if not capture_stdout:
        return b""
    stdout = result.stdout
    if type(stdout) is not bytes or len(stdout) > _MAX_PROBE_BYTES:
        return None
    return stdout


def _probe(path: Path, ffprobe_executable: str, timeout_seconds: int | float) -> Mapping[str, Any] | None:
    stdout = _run(
        [
            ffprobe_executable,
            "-hide_banner",
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,duration,sample_rate,channels,r_frame_rate,avg_frame_rate:format=format_name,duration:format_tags=comment",
            "-of",
            "json",
            str(path),
        ],
        timeout_seconds,
        capture_stdout=True,
    )
    if stdout is None:
        return None
    try:
        parsed = json.loads(stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return None
    return parsed if isinstance(parsed, Mapping) else None


def _number(value: object) -> float | None:
    if type(value) is int or type(value) is float:
        number = float(value)
    elif type(value) is str:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return None
    else:
        return None
    return number if math.isfinite(number) else None


def _duration_matches(value: object, expected: int | float) -> bool:
    actual = _number(value)
    return actual is not None and abs(actual - float(expected)) <= _DURATION_TOLERANCE


def _is_24_fps(value: object) -> bool:
    if type(value) is not str or value.count("/") != 1:
        return False
    numerator_text, denominator_text = value.split("/")
    if (
        not numerator_text or not denominator_text or len(numerator_text) > 20 or len(denominator_text) > 20
        or not all("0" <= char <= "9" for char in numerator_text + denominator_text)
    ):
        return False
    try:
        numerator, denominator = int(numerator_text), int(denominator_text)
    except (TypeError, ValueError, OverflowError):
        return False
    return denominator > 0 and numerator == 24 * denominator


def _tags_contain_binding(probe: Mapping[str, Any], binding: str) -> bool:
    containers: list[object] = []
    format_value = probe.get("format")
    if isinstance(format_value, Mapping):
        containers.append(format_value.get("tags"))
    streams = probe.get("streams")
    if isinstance(streams, list):
        containers.extend(stream.get("tags") for stream in streams if isinstance(stream, Mapping))
    for tags in containers:
        if isinstance(tags, Mapping) and tags.get("comment") == binding:
            return True
    return False


def _valid_visual_probe(probe: Mapping[str, Any], task: VisualGenerationTask, binding: str) -> bool:
    streams = probe.get("streams")
    if type(streams) is not list or len(streams) != 1 or not isinstance(streams[0], Mapping):
        return False
    stream = streams[0]
    return (
        stream.get("codec_type") == "video"
        and stream.get("codec_name") == "h264"
        and type(stream.get("width")) is int
        and type(stream.get("height")) is int
        and stream.get("width") == 540
        and stream.get("height") == 960
        and stream.get("pix_fmt") == "yuv420p"
        and _is_24_fps(stream.get("r_frame_rate"))
        and _is_24_fps(stream.get("avg_frame_rate"))
        and _duration_matches(stream.get("duration"), task.duration_seconds)
        and isinstance(probe.get("format"), Mapping)
        and probe["format"].get("format_name") == _MP4_FORMAT
        and _tags_contain_binding(probe, binding)
    )


def _valid_voice_probe(probe: Mapping[str, Any], task: VoiceSynthesisTask, binding: str) -> bool:
    streams = probe.get("streams")
    if type(streams) is not list or len(streams) != 1 or not isinstance(streams[0], Mapping):
        return False
    stream = streams[0]
    sample_rate = stream.get("sample_rate")
    channels = stream.get("channels")
    return (
        stream.get("codec_type") == "audio"
        and stream.get("codec_name") == "aac"
        and (sample_rate == "48000" or sample_rate == 48000)
        and type(channels) is int
        and channels == 1
        and _duration_matches(stream.get("duration"), task.duration_seconds)
        and isinstance(probe.get("format"), Mapping)
        and probe["format"].get("format_name") == _MP4_FORMAT
        and _tags_contain_binding(probe, binding)
    )


def _commit(
    workspace: WorkspaceAdapter,
    reference: WorkspaceFileReference,
    content: bytes,
) -> ProductionMediaFailure | None:
    try:
        return _fake._commit_fixture(workspace, reference, content)
    except Exception:
        return _generation_failure()


class _FFmpegFixtureBase:
    __slots__ = ("_workspace", "_ffmpeg_executable", "_ffprobe_executable", "_timeout_seconds")

    def __init__(
        self,
        workspace: WorkspaceAdapter,
        *,
        ffmpeg_executable: str,
        ffprobe_executable: str,
        timeout_seconds: int | float = 30,
    ) -> None:
        self._workspace = workspace
        self._ffmpeg_executable = ffmpeg_executable
        self._ffprobe_executable = ffprobe_executable
        self._timeout_seconds = timeout_seconds

    def _configuration_failure(self) -> ProductionMediaFailure | None:
        if not _tools_valid(self._ffmpeg_executable, self._ffprobe_executable):
            return _tool_unavailable()
        if not _timeout_valid(self._timeout_seconds):
            return _failure("validation", "INVALID_MEDIA_TOOL_TIMEOUT", "media tool timeout is invalid")
        return None

    def _run_fixture(
        self,
        task: VisualGenerationTask | VoiceSynthesisTask,
        operation: str,
    ) -> bytes | ProductionMediaFailure:
        binding = _binding(task)
        duration = _duration_text(task.duration_seconds)
        visual = operation == "visual"
        source = (
            f"color=c=0x172554:s=540x960:r=24:d={duration}"
            if visual else f"sine=frequency=440:sample_rate=48000:duration={duration}"
        )
        output_name = "scene.mp4" if visual else "scene.m4a"
        profile = (
            ["-map", "0:v:0", "-an", "-c:v", "libx264", "-preset", "ultrafast", "-threads", "1", "-pix_fmt", "yuv420p", "-r", "24"]
            if visual else
            ["-map", "0:a:0", "-vn", "-c:a", "aac", "-b:a", "64k", "-ar", "48000", "-ac", "1"]
        )
        with TemporaryDirectory(prefix="acf-ffmpeg-fixture-") as temporary:
            output = Path(temporary) / output_name
            argv = [
                self._ffmpeg_executable, "-hide_banner", "-nostdin", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", source, *profile, "-t", duration,
                "-map_metadata", "-1", "-metadata", "creation_time=1970-01-01T00:00:00Z",
                "-metadata", f"comment={binding}", "-movflags", "+faststart", str(output),
            ]
            if _run(argv, self._timeout_seconds, capture_stdout=False) is None:
                return _generation_failure()
            content = _safe_result_bytes(output)
            probe = _probe(output, self._ffprobe_executable, self._timeout_seconds) if content is not None else None
            valid = (
                _valid_visual_probe(probe, task, binding) if visual and probe is not None else
                _valid_voice_probe(probe, task, binding) if not visual and probe is not None else False
            )
            return content if valid else _generation_failure()

    def _result(
        self,
        task: VisualGenerationTask | VoiceSynthesisTask,
        operation: str,
        provider: str,
        media_type: str,
    ) -> MediaGenerationResult | ProductionMediaFailure:
        content = self._run_fixture(task, operation)
        if isinstance(content, ProductionMediaFailure):
            return content
        failure = _commit(self._workspace, task.output_reference, content)
        if failure is not None:
            return failure
        return MediaGenerationResult(
            task.attempt_id, task.scene_id, operation, provider, task.output_reference,
            media_type, task.duration_seconds, "SUCCESS",
        )


class FFmpegFixtureVisualGenerator(_FFmpegFixtureBase):
    """Generate deterministic H.264/yuv420p 9:16 visual Fixture clips."""

    def generate(self, task: VisualGenerationTask) -> MediaGenerationResult | ProductionMediaFailure:
        try:
            task = _fake._validate_visual(task)
        except _fake._InvalidTask as error:
            return _fake._invalid(error.code)
        except Exception:
            return _fake._invalid("INVALID_VISUAL_TASK")
        configuration_failure = self._configuration_failure()
        if configuration_failure is not None:
            return configuration_failure
        try:
            return self._result(task, "visual", _VISUAL_PROVIDER, _VISUAL_MEDIA_TYPE)
        except Exception:
            return _generation_failure()


class FFmpegFixtureVoiceGenerator(_FFmpegFixtureBase):
    """Generate deterministic AAC/48-kHz mono artificial-tone Fixtures."""

    def synthesize(self, task: VoiceSynthesisTask) -> MediaGenerationResult | ProductionMediaFailure:
        try:
            task = _fake._validate_voice(task)
        except _fake._InvalidTask as error:
            return _fake._invalid(error.code)
        except Exception:
            return _fake._invalid("INVALID_VOICE_TASK")
        configuration_failure = self._configuration_failure()
        if configuration_failure is not None:
            return configuration_failure
        try:
            return self._result(task, "voice", _VOICE_PROVIDER, _VOICE_MEDIA_TYPE)
        except Exception:
            return _generation_failure()


__all__ = ["FFmpegFixtureVisualGenerator", "FFmpegFixtureVoiceGenerator"]
