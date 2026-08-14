from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import unittest

from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference
from ai_course_factory.production import CreatorSceneClipImporter, CreatorSceneClipImportFailure, CreatorSceneClipImportSuccess


def _ffmpeg() -> str:
    return shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"


def _ffprobe() -> str:
    return shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"


def _make_clip(path: Path, *, audio: bool = False) -> None:
    command = [
        _ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=320x480:r=24:d=1",
    ]
    if audio:
        command.extend(["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:d=1", "-map", "0:v:0", "-map", "1:a:0"])
    else:
        command.extend(["-map", "0:v:0"])
    command.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24"])
    if audio:
        command.extend(["-c:a", "aac", "-shortest"])
    command.append(str(path))
    completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode("utf-8", "replace"))


class CreatorSceneClipImporterTests(unittest.TestCase):
    def test_valid_set_normalizes_to_fixed_playable_contract_and_strips_native_audio(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "generated"
            generated.mkdir()
            for index in range(1, 7):
                _make_clip(generated / f"scene-{index}.mp4", audio=index == 1)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("demo-episode-01")
            importer = CreatorSceneClipImporter(
                workspace,
                generated,
                task_id="demo-episode-01",
                scene_durations=tuple((f"scene-{index}", 1_000) for index in range(1, 7)),
                ffmpeg_executable=_ffmpeg(),
                ffprobe_executable=_ffprobe(),
            )

            result = importer.import_full_set()

            self.assertIsInstance(result, CreatorSceneClipImportSuccess)
            assert isinstance(result, CreatorSceneClipImportSuccess)
            self.assertEqual(tuple(item.declared_filename for item in result.clips), tuple(f"scene-{index}.mp4" for index in range(1, 7)))
            for item in result.clips:
                content = workspace.read(item.output_reference)
                self.assertIsInstance(content, bytes)
                self.assertEqual((item.media_type, item.duration_milliseconds), ("video/mp4", 1_000))
                self.assertEqual(item.creator_provenance["native_audio/subtitles/effects"], "metadata_only")
                self.assertEqual(item.creator_provenance["source_stream_count"], 2 if item.scene_id == "scene-1" else 1)

    def test_invalid_member_is_reported_by_basename_before_any_workspace_write(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "generated"
            generated.mkdir()
            for index in range(1, 7):
                target = generated / f"scene-{index}.mp4"
                if index == 4:
                    target.write_bytes(b"not-an-mp4")
                else:
                    _make_clip(target)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("demo-episode-01")
            result = CreatorSceneClipImporter(
                workspace,
                generated,
                task_id="demo-episode-01",
                scene_durations=tuple((f"scene-{index}", 1_000) for index in range(1, 7)),
                ffmpeg_executable=_ffmpeg(),
                ffprobe_executable=_ffprobe(),
            ).import_full_set()

            self.assertIsInstance(result, CreatorSceneClipImportFailure)
            assert isinstance(result, CreatorSceneClipImportFailure)
            self.assertEqual(result.invalid_filenames, ("scene-4.mp4",))
            self.assertNotIn(str(root), result.message)
            self.assertNotIsInstance(
                workspace.read(WorkspaceFileReference("demo-episode-01", "media", "scene-1.mp4")),
                bytes,
            )

    def test_symlinked_member_is_reported_before_any_workspace_write(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            generated = root / "generated"
            generated.mkdir()
            for index in range(1, 7):
                target = generated / f"scene-{index}.mp4"
                if index == 4:
                    source = root / "scene-4-source.mp4"
                    _make_clip(source)
                    target.symlink_to(source)
                else:
                    _make_clip(target)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("demo-episode-01")
            result = CreatorSceneClipImporter(
                workspace,
                generated,
                task_id="demo-episode-01",
                scene_durations=tuple((f"scene-{index}", 1_000) for index in range(1, 7)),
                ffmpeg_executable=_ffmpeg(),
                ffprobe_executable=_ffprobe(),
            ).import_full_set()

            self.assertIsInstance(result, CreatorSceneClipImportFailure)
            assert isinstance(result, CreatorSceneClipImportFailure)
            self.assertEqual(result.invalid_filenames, ("scene-4.mp4",))
            self.assertNotIsInstance(
                workspace.read(WorkspaceFileReference("demo-episode-01", "media", "scene-1.mp4")),
                bytes,
            )


if __name__ == "__main__":
    unittest.main()
