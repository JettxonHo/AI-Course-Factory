from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference
from ai_course_factory.production import (
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
)
from ai_course_factory.production.adapters import LocalImportedVisualGenerator


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def _ffprobe() -> str:
    return shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"


def _write_png(path: Path, colour: str = "red") -> None:
    subprocess.run(
        [
            _ffmpeg(),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={colour}:s=32x32",
            "-frames:v",
            "1",
            str(path),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class LocalImportedVisualGeneratorTests(unittest.TestCase):
    def test_preflight_requires_exact_six_names_and_reports_safe_missing_names(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("demo-episode-01")
            for index in range(1, 6):
                _write_png(root / f"scene-{index}.png")
            adapter = LocalImportedVisualGenerator(
                workspace,
                root,
                ffmpeg_executable=_ffmpeg(),
                ffprobe_executable=_ffprobe(),
            )

            result = adapter.preflight()

            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "LOCAL_IMPORT_PREFLIGHT_FAILED")
            self.assertIn("scene-6.png", result.message)
            self.assertNotIn(str(root), result.message)
            self.assertNotIsInstance(
                workspace.read(WorkspaceFileReference("demo-episode-01", "media", "scene-1.mp4")),
                bytes,
            )

    def test_valid_png_maps_scene_name_and_produces_playable_h264_clip(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("demo-episode-01")
            _write_png(root / "scene-1.png", "blue")
            adapter = LocalImportedVisualGenerator(
                workspace,
                root,
                ffmpeg_executable=_ffmpeg(),
                ffprobe_executable=_ffprobe(),
            )
            task = VisualGenerationTask(
                "demo-episode-01",
                "attempt:local-import:visual:1",
                ArtifactReference("production_request", "production-request:episode-1", 1),
                "scene-1",
                "9:16",
                1,
                "show the lesson",
                "wave",
                WorkspaceFileReference("demo-episode-01", "media", "scene-1.mp4"),
            )

            result = adapter.generate(task)

            self.assertIsInstance(result, MediaGenerationResult)
            self.assertEqual(result.provider, "local-import-operator-declared-external-source")
            output = workspace.read(task.output_reference)
            self.assertIsInstance(output, bytes)
            output_path = root / "scene-1.mp4"
            output_path.write_bytes(output)
            probe = subprocess.run(
                [
                    _ffprobe(),
                    "-v",
                    "error",
                    "-show_entries",
                    "stream=codec_name,width,height,pix_fmt,r_frame_rate:format=format_name",
                    "-of",
                    "json",
                    str(output_path),
                ],
                check=True,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            ).stdout.decode("utf-8")
            self.assertIn('"codec_name": "h264"', probe)
            self.assertIn('"width": 540', probe)
            self.assertIn('"height": 960', probe)
            self.assertIn('"pix_fmt": "yuv420p"', probe)
            self.assertIn('"r_frame_rate": "24/1"', probe)

    def test_replacement_requires_exact_filename_and_maps_only_scene_two(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("demo-episode-01")
            adapter = LocalImportedVisualGenerator(
                workspace,
                root,
                ffmpeg_executable=_ffmpeg(),
                ffprobe_executable=_ffprobe(),
            )

            missing = adapter.preflight(replacement=True)

            self.assertIsInstance(missing, ProductionMediaFailure)
            self.assertIn("scene-2-replacement.png", missing.message)
            _write_png(root / "scene-2-replacement.png", "green")
            ready = adapter.preflight(replacement=True)
            self.assertEqual(ready.filenames, ("scene-2-replacement.png",))


if __name__ == "__main__":
    unittest.main()
