"""Operator-declared local image imports converted to playable Scene clips.

The image-generation step happens outside the application (for example in
ChatGPT Desktop ImageGen).  This adapter owns the narrow bridge from the
operator's explicit directory to the existing provider-neutral ``VisualGenerator``
seam.  It never searches a home folder, infers a newest file, or calls a cloud
Provider.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
import stat
from tempfile import TemporaryDirectory
from typing import Any, Mapping

from ai_course_factory.persistence import WorkspaceAdapter, WorkspaceFileReference

from ..interfaces import VisualGenerator
from ..model import MediaGenerationResult, ProductionMediaFailure, VisualGenerationTask
from . import fake as _fake
from . import ffmpeg_fixture as _fixture


LOCAL_IMPORTED_PROVIDER = "local-import-operator-declared-external-source"
_MEDIA_TYPE = "video/mp4"
_MAX_MEDIA_BYTES = 64 * 1024 * 1024
_BINDING_PREFIX = "ai-course-factory-local-import-v1:"
_INITIAL_FILENAMES = tuple(f"scene-{index}.png" for index in range(1, 7))
_REPLACEMENT_FILENAME = "scene-2-replacement.png"
_VALID_IMAGE_FORMATS = frozenset({"png_pipe", "jpeg_pipe"})
_VALID_IMAGE_CODECS = frozenset({"png", "mjpeg"})


@dataclass(frozen=True, slots=True)
class LocalImportedPreflight:
    """Safe result of validating one exact import set.

    Only basenames are exposed so actionable errors never disclose the
    operator's local directory path.
    """

    filenames: tuple[str, ...]


def _failure(code: str, message: str) -> ProductionMediaFailure:
    return ProductionMediaFailure("validation", code, message)


def _safe_image_message(filenames: tuple[str, ...]) -> str:
    joined = ", ".join(filenames)
    return f"Local visual import requires valid PNG/JPEG files: {joined}."


def _duration_text(value: int | float) -> str:
    text = format(value, ".6f").rstrip("0").rstrip(".")
    return text if text else "0"


def _image_probe_valid(probe: Mapping[str, Any] | None) -> bool:
    if not isinstance(probe, Mapping):
        return False
    streams = probe.get("streams")
    format_value = probe.get("format")
    if type(streams) is not list or len(streams) != 1 or not isinstance(streams[0], Mapping):
        return False
    if not isinstance(format_value, Mapping):
        return False
    stream = streams[0]
    return (
        stream.get("codec_type") == "video"
        and stream.get("codec_name") in _VALID_IMAGE_CODECS
        and type(stream.get("width")) is int
        and stream.get("width") > 0
        and type(stream.get("height")) is int
        and stream.get("height") > 0
        and format_value.get("format_name") in _VALID_IMAGE_FORMATS
    )


class LocalImportedVisualGenerator(VisualGenerator):
    """Convert exact operator-supplied PNG/JPEG stills into Scene MP4 clips."""

    __slots__ = (
        "_workspace",
        "_import_directory",
        "_ffmpeg_executable",
        "_ffprobe_executable",
        "_timeout_seconds",
    )

    def __init__(
        self,
        workspace: WorkspaceAdapter,
        import_directory: str | Path,
        *,
        ffmpeg_executable: str,
        ffprobe_executable: str,
        timeout_seconds: int | float = 60,
    ) -> None:
        self._workspace = workspace
        try:
            self._import_directory = Path(import_directory).expanduser().resolve()
        except (OSError, TypeError, ValueError):
            self._import_directory = Path("\0")
        self._ffmpeg_executable = ffmpeg_executable
        self._ffprobe_executable = ffprobe_executable
        self._timeout_seconds = timeout_seconds

    @property
    def import_directory(self) -> Path:
        """Return the configured directory for diagnostics and tests."""

        return self._import_directory

    def preflight(self, *, replacement: bool = False) -> LocalImportedPreflight | ProductionMediaFailure:
        """Validate all exact files before any workspace or Artifact side effect."""

        names = (_REPLACEMENT_FILENAME,) if replacement else _INITIAL_FILENAMES
        configuration_failure = self._configuration_failure()
        if configuration_failure is not None:
            return configuration_failure
        invalid: list[str] = []
        for name in names:
            if not self._image_valid(name):
                invalid.append(name)
        if invalid:
            code = "LOCAL_IMPORT_REPLACEMENT_PREFLIGHT_FAILED" if replacement else "LOCAL_IMPORT_PREFLIGHT_FAILED"
            return _failure(code, _safe_image_message(tuple(invalid)))
        return LocalImportedPreflight(tuple(names))

    def generate(self, task: VisualGenerationTask) -> MediaGenerationResult | ProductionMediaFailure:
        try:
            task = _fake._validate_visual(task)
            source_name = self._source_filename(task)
        except _fake._InvalidTask as error:
            return ProductionMediaFailure("validation", error.code, "media generation task is invalid")
        except Exception:
            return ProductionMediaFailure("validation", "INVALID_VISUAL_TASK", "media generation task is invalid")
        configuration_failure = self._configuration_failure()
        if configuration_failure is not None:
            return configuration_failure
        if not self._image_valid(source_name):
            return _failure("LOCAL_IMPORT_PREFLIGHT_FAILED", _safe_image_message((source_name,)))
        try:
            source = self._import_directory / source_name
            binding = self._binding(task, source_name)
            duration = _duration_text(task.duration_seconds)
            with TemporaryDirectory(prefix="acf-local-import-") as directory:
                output = Path(directory) / "scene.mp4"
                argv = [
                    self._ffmpeg_executable,
                    "-hide_banner",
                    "-nostdin",
                    "-loglevel",
                    "error",
                    "-y",
                    "-loop",
                    "1",
                    "-i",
                    str(source),
                    "-an",
                    "-vf",
                    "scale=540:960:force_original_aspect_ratio=decrease,pad=540:960:(ow-iw)/2:(oh-ih)/2:color=black,format=yuv420p",
                    "-c:v",
                    "libx264",
                    "-preset",
                    "ultrafast",
                    "-threads",
                    "1",
                    "-pix_fmt",
                    "yuv420p",
                    "-r",
                    "24",
                    "-t",
                    duration,
                    "-map_metadata",
                    "-1",
                    "-metadata",
                    "creation_time=1970-01-01T00:00:00Z",
                    "-metadata",
                    f"comment={binding}",
                    "-movflags",
                    "+faststart",
                    str(output),
                ]
                if _fixture._run(argv, self._timeout_seconds, capture_stdout=False) is None:
                    return ProductionMediaFailure("execution", "LOCAL_IMPORT_CONVERSION_FAILED", "local visual conversion failed")
                content = _fixture._safe_result_bytes(output)
                probe = _fixture._probe(output, self._ffprobe_executable, self._timeout_seconds) if content is not None else None
                if content is None or probe is None or not _fixture._valid_visual_probe(probe, task, binding):
                    return ProductionMediaFailure("execution", "LOCAL_IMPORT_CONVERSION_FAILED", "local visual conversion failed")
                committed = _fake._commit_fixture(self._workspace, task.output_reference, content)
                if committed is not None:
                    return committed
                return MediaGenerationResult(
                    task.attempt_id,
                    task.scene_id,
                    "visual",
                    LOCAL_IMPORTED_PROVIDER,
                    task.output_reference,
                    _MEDIA_TYPE,
                    task.duration_seconds,
                    "SUCCESS",
                )
        except Exception:
            return ProductionMediaFailure("execution", "LOCAL_IMPORT_CONVERSION_FAILED", "local visual conversion failed")

    def _configuration_failure(self) -> ProductionMediaFailure | None:
        if not self._directory_valid():
            return _failure("LOCAL_IMPORT_DIRECTORY_REQUIRED", "an explicit local visual import directory is required")
        if not _fixture._tools_valid(self._ffmpeg_executable, self._ffprobe_executable):
            return ProductionMediaFailure("validation", "MEDIA_TOOL_UNAVAILABLE", "media tool configuration is unavailable")
        if not _fixture._timeout_valid(self._timeout_seconds):
            return ProductionMediaFailure("validation", "INVALID_MEDIA_TOOL_TIMEOUT", "media tool timeout is invalid")
        return None

    def _directory_valid(self) -> bool:
        try:
            info = self._import_directory.stat()
            return stat.S_ISDIR(info.st_mode) and not self._import_directory.is_symlink()
        except (OSError, ValueError):
            return False

    def _image_valid(self, name: str) -> bool:
        if name not in _INITIAL_FILENAMES and name != _REPLACEMENT_FILENAME:
            return False
        try:
            path = self._import_directory / name
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or info.st_size < 1 or info.st_size > _MAX_MEDIA_BYTES:
                return False
            probe = _fixture._probe(path, self._ffprobe_executable, self._timeout_seconds)
            if not _image_probe_valid(probe):
                return False
            decoded = _fixture._run(
                [
                    self._ffmpeg_executable,
                    "-hide_banner",
                    "-nostdin",
                    "-loglevel",
                    "error",
                    "-i",
                    str(path),
                    "-frames:v",
                    "1",
                    "-f",
                    "null",
                    "-",
                ],
                self._timeout_seconds,
                capture_stdout=False,
            )
            return decoded is not None
        except (OSError, ValueError, TypeError):
            return False

    @staticmethod
    def _source_filename(task: VisualGenerationTask) -> str:
        name = task.output_reference.name
        if name == "scene-2-replacement.mp4":
            if task.scene_id != "scene-2":
                raise _fake._InvalidTask("INVALID_OUTPUT_REFERENCE")
            return _REPLACEMENT_FILENAME
        expected = {f"scene-{index}.mp4": f"scene-{index}.png" for index in range(1, 7)}
        source = expected.get(name)
        if source is None:
            raise _fake._InvalidTask("INVALID_OUTPUT_REFERENCE")
        if source.removesuffix(".png") != task.scene_id:
            raise _fake._InvalidTask("INVALID_OUTPUT_REFERENCE")
        return source

    @staticmethod
    def _binding(task: VisualGenerationTask, source_name: str) -> str:
        encoded = f"{task.task_id}:{task.scene_id}:{task.duration_seconds}:{source_name}".encode("utf-8")
        return _BINDING_PREFIX + hashlib.sha256(encoded).hexdigest()


__all__ = ["LOCAL_IMPORTED_PROVIDER", "LocalImportedPreflight", "LocalImportedVisualGenerator"]
