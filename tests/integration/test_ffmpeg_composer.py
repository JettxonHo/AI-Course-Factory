"""Offline public integration behavior for the local FFmpeg MediaComposer."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFailure, WorkspaceFileReference
from ai_course_factory.production import (
    FFmpegFixtureVisualGenerator,
    FFmpegFixtureVoiceGenerator,
    FFmpegMediaComposer,
    MediaCompositionScene,
    MediaCompositionTask,
    MediaCompositionResult,
    ProductionMediaFailure,
    MediaComposer,
    MediaGenerationResult,
    VisualGenerationTask,
    VoiceSynthesisTask,
)


_FFMPEG = "/opt/homebrew/bin/ffmpeg"
_FFPROBE = "/opt/homebrew/bin/ffprobe"


def _probe(path: Path) -> dict:
    result = subprocess.run(
        [
            _FFPROBE, "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,duration,sample_rate,channels,r_frame_rate,avg_frame_rate:format=format_name,duration:format_tags=comment",
            "-of", "json", str(path),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return json.loads(result.stdout.decode("utf-8"))


def _extract_subtitles(path: Path) -> str:
    result = subprocess.run(
        [_FFMPEG, "-hide_banner", "-nostdin", "-loglevel", "error", "-i", str(path), "-map", "0:s:0", "-f", "srt", "-"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return result.stdout.decode("utf-8")


def _wrapped_probe(path: Path, mutation: str) -> str:
    state = path.with_suffix(".count")
    script = path.with_suffix(".py")
    mutation_line = {
        "stream": 'payload["streams"][0]["codec_name"] = "mpeg4"',
        "fps": 'payload["streams"][0]["r_frame_rate"] = "25/1"',
        "container": 'payload["format"]["format_name"] = "avi"',
        "duration": 'payload["format"]["duration"] = "999"',
        "metadata": 'payload["format"].setdefault("tags", {})["comment"] = "forged"',
    }[mutation]
    script.write_text(
        f"#!{sys.executable}\n"
        "import json, pathlib, subprocess, sys\n"
        f"state = pathlib.Path({str(state)!r})\n"
        "count = int(state.read_text()) if state.exists() else 0\n"
        "state.write_text(str(count + 1))\n"
        f"result = subprocess.run([{_FFPROBE!r}, *sys.argv[1:]], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)\n"
        "payload = json.loads(result.stdout.decode('utf-8'))\n"
        "if count >= 4:\n"
        f"    {mutation_line}\n"
        "print(json.dumps(payload))\n",
        encoding="utf-8",
    )
    script.chmod(0o755)
    return str(script)


def _executable(path: Path, body: str) -> str:
    path.write_text(f"#!{sys.executable}\n{body}\n", encoding="utf-8")
    path.chmod(0o755)
    return str(path)


def _composition_fixture(root: Path) -> tuple[FilesystemWorkspace, MediaCompositionTask]:
    task_id = "task:compose"
    workspace = FilesystemWorkspace(root / "workspace")
    workspace.prepare(task_id)
    request = ArtifactReference("production_request", "episode-1", 1)
    timeline = ArtifactReference("timeline", "episode-1", 1)
    visual_generator = FFmpegFixtureVisualGenerator(
        workspace, ffmpeg_executable=_FFMPEG, ffprobe_executable=_FFPROBE,
    )
    voice_generator = FFmpegFixtureVoiceGenerator(
        workspace, ffmpeg_executable=_FFMPEG, ffprobe_executable=_FFPROBE,
    )
    scenes: list[MediaCompositionScene] = []
    start = 0
    for index, duration in enumerate((800, 1100), start=1):
        end = start + duration
        scene_id = f"scene-{index}"
        visual_result = visual_generator.generate(
            VisualGenerationTask(
                task_id, f"attempt:visual:{index}", request, scene_id, "9:16", duration / 1000,
                "展示小土豆。", "挥手。", WorkspaceFileReference(task_id, "media", f"{scene_id}.mp4"),
            )
        )
        voice_result = voice_generator.synthesize(
            VoiceSynthesisTask(
                task_id, f"attempt:voice:{index}", request, scene_id, "zh-CN", duration / 1000,
                f"第{index}幕。", WorkspaceFileReference(task_id, "media", f"{scene_id}.m4a"),
            )
        )
        if not isinstance(visual_result, MediaGenerationResult) or not isinstance(voice_result, MediaGenerationResult):
            raise AssertionError("fixture generation failed")
        scenes.append(MediaCompositionScene(scene_id, start, end, visual_result, voice_result, f"字幕{index}。"))
        start = end
    return workspace, MediaCompositionTask(
        task_id, "composition:1", request, timeline, tuple(scenes),
        WorkspaceFileReference(task_id, "media", "composition.mp4"),
    )


class FFmpegMediaComposerIntegrationTests(unittest.TestCase):
    def test_composes_real_playable_three_stream_output_and_replays_exact_bytes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, task = _composition_fixture(root)
            composer = FFmpegMediaComposer(
                workspace, ffmpeg_executable=_FFMPEG, ffprobe_executable=_FFPROBE,
            )
            self.assertIsInstance(composer, MediaComposer)
            result = composer.compose(task)
            self.assertIsInstance(result, MediaCompositionResult)
            self.assertEqual(result.composer, "ffmpeg-composer-v1")
            self.assertEqual(result.media_type, "video/mp4")
            self.assertEqual(result.scene_ids, ("scene-1", "scene-2"))
            content = workspace.read(task.output_reference)
            self.assertIsInstance(content, bytes)
            self.assertIn(b"ftyp", content[:128])
            materialized = root / "composition.mp4"
            materialized.write_bytes(content)
            probe = _probe(materialized)
            self.assertEqual(probe["format"]["format_name"], "mov,mp4,m4a,3gp,3g2,mj2")
            self.assertEqual(len(probe["streams"]), 3)
            self.assertEqual(
                {(stream["codec_type"], stream["codec_name"]) for stream in probe["streams"]},
                {("video", "h264"), ("audio", "aac"), ("subtitle", "mov_text")},
            )
            video = next(stream for stream in probe["streams"] if stream["codec_type"] == "video")
            audio = next(stream for stream in probe["streams"] if stream["codec_type"] == "audio")
            self.assertEqual((video["width"], video["height"], video["pix_fmt"]), (540, 960, "yuv420p"))
            self.assertEqual((video["r_frame_rate"], video["avg_frame_rate"]), ("24/1", "24/1"))
            self.assertEqual((audio["codec_name"], audio["sample_rate"], audio["channels"]), ("aac", "48000", 1))
            self.assertAlmostEqual(float(probe["format"]["duration"]), 1.9, delta=0.15)
            self.assertTrue(probe["format"]["tags"]["comment"].startswith("ai-course-factory-ffmpeg-composer-v1:"))
            subtitles = _extract_subtitles(materialized)
            self.assertIn("00:00:00,000 --> 00:00:00,800", subtitles)
            self.assertIn("字幕1。", subtitles)
            self.assertIn("00:00:00,800 --> 00:00:01,900", subtitles)
            self.assertIn("字幕2。", subtitles)

            replay_workspace = FilesystemWorkspace(root / "workspace")
            replay = FFmpegMediaComposer(
                replay_workspace, ffmpeg_executable=_FFMPEG, ffprobe_executable=_FFPROBE,
            ).compose(task)
            self.assertEqual(replay, result)
            self.assertEqual(replay_workspace.read(task.output_reference), content)

    def test_changed_subtitle_or_lineage_conflicts_without_overwrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, task = _composition_fixture(root)
            kwargs = {"ffmpeg_executable": _FFMPEG, "ffprobe_executable": _FFPROBE}
            first = FFmpegMediaComposer(workspace, **kwargs).compose(task)
            original = workspace.read(task.output_reference)
            changed_subtitle = replace(
                task,
                scenes=(replace(task.scenes[0], subtitle_text="改写字幕。"), task.scenes[1]),
            )
            conflict = FFmpegMediaComposer(FilesystemWorkspace(root / "workspace"), **kwargs).compose(changed_subtitle)
            self.assertIsInstance(first, MediaCompositionResult)
            self.assertIsInstance(conflict, ProductionMediaFailure)
            self.assertEqual(conflict.code, "MEDIA_OUTPUT_CONFLICT")
            self.assertEqual(FilesystemWorkspace(root / "workspace").read(task.output_reference), original)
            reordered = replace(
                task,
                scenes=(
                    replace(task.scenes[1], start_milliseconds=0, end_milliseconds=1100),
                    replace(task.scenes[0], start_milliseconds=1100, end_milliseconds=1900),
                ),
            )
            reordered_conflict = FFmpegMediaComposer(FilesystemWorkspace(root / "workspace"), **kwargs).compose(reordered)
            self.assertIsInstance(reordered_conflict, ProductionMediaFailure)
            self.assertEqual(reordered_conflict.code, "MEDIA_OUTPUT_CONFLICT")
            self.assertEqual(FilesystemWorkspace(root / "workspace").read(task.output_reference), original)
            timing = replace(
                task,
                scenes=(
                    replace(
                        task.scenes[0],
                        end_milliseconds=850,
                        visual_result=replace(task.scenes[0].visual_result, duration_seconds=0.85),
                        voice_result=replace(task.scenes[0].voice_result, duration_seconds=0.85),
                    ),
                    replace(
                        task.scenes[1],
                        start_milliseconds=850,
                        end_milliseconds=1900,
                        visual_result=replace(task.scenes[1].visual_result, duration_seconds=1.05),
                        voice_result=replace(task.scenes[1].voice_result, duration_seconds=1.05),
                    ),
                ),
            )
            timing_conflict = FFmpegMediaComposer(FilesystemWorkspace(root / "workspace"), **kwargs).compose(timing)
            self.assertIsInstance(timing_conflict, ProductionMediaFailure)
            self.assertEqual(timing_conflict.code, "MEDIA_OUTPUT_CONFLICT")
            self.assertEqual(FilesystemWorkspace(root / "workspace").read(task.output_reference), original)
            lineage = replace(
                task,
                production_request_reference=ArtifactReference("production_request", "episode-2", 1),
            )
            conflict_lineage = FFmpegMediaComposer(FilesystemWorkspace(root / "workspace"), **kwargs).compose(lineage)
            self.assertIsInstance(conflict_lineage, ProductionMediaFailure)
            self.assertEqual(conflict_lineage.code, "MEDIA_OUTPUT_CONFLICT")

    def test_input_probe_failure_is_generic_and_does_not_commit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace, task = _composition_fixture(root)
            ffprobe = root / "bad-ffprobe"
            ffprobe.write_text(f"#!{sys.executable}\nimport sys\nprint('{{}}')\n", encoding="utf-8")
            ffprobe.chmod(0o755)
            result = FFmpegMediaComposer(
                workspace, ffmpeg_executable=_FFMPEG, ffprobe_executable=str(ffprobe),
            ).compose(task)
            self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_COMPOSITION_FAILED", "local media composition failed"))
            self.assertEqual(getattr(workspace.read(task.output_reference), "code", None), "WORKSPACE_FILE_NOT_FOUND")

    def test_output_probe_mutations_and_ffmpeg_failures_are_generic_and_do_not_commit(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for mutation in ("stream", "fps", "container", "duration", "metadata"):
                workspace, task = _composition_fixture(root / mutation)
                result = FFmpegMediaComposer(
                    workspace,
                    ffmpeg_executable=_FFMPEG,
                    ffprobe_executable=_wrapped_probe(root / mutation / "probe", mutation),
                ).compose(task)
                self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_COMPOSITION_FAILED", "local media composition failed"))
                self.assertEqual(getattr(workspace.read(task.output_reference), "code", None), "WORKSPACE_FILE_NOT_FOUND")
            workspace, task = _composition_fixture(root / "process")
            result = FFmpegMediaComposer(
                workspace,
                ffmpeg_executable=_executable(root / "process" / "ffmpeg", "exit 1"),
                ffprobe_executable=_FFPROBE,
            ).compose(task)
            self.assertEqual(result.code, "MEDIA_COMPOSITION_FAILED")
            self.assertEqual(getattr(workspace.read(task.output_reference), "code", None), "WORKSPACE_FILE_NOT_FOUND")
            workspace, task = _composition_fixture(root / "timeout")
            result = FFmpegMediaComposer(
                workspace,
                ffmpeg_executable=_executable(root / "timeout" / "ffmpeg", "import time; time.sleep(2)"),
                ffprobe_executable=_FFPROBE,
                timeout_seconds=1,
            ).compose(task)
            self.assertEqual(result.code, "MEDIA_COMPOSITION_FAILED")
            self.assertEqual(getattr(workspace.read(task.output_reference), "code", None), "WORKSPACE_FILE_NOT_FOUND")

    def test_malformed_workspace_read_or_commit_success_never_becomes_composition_success(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            real_workspace, task = _composition_fixture(root / "read")
            marker = root / "read-process-called"
            ffmpeg = _executable(root / "read-ffmpeg", f"from pathlib import Path; Path({str(marker)!r}).write_text('called')")

            class MalformedReadWorkspace:
                def read(self, _reference):
                    return bytearray(b"not immutable bytes")

                def commit(self, _reference, _content):
                    raise AssertionError("malformed input must stop before commit")

            result = FFmpegMediaComposer(
                MalformedReadWorkspace(), ffmpeg_executable=ffmpeg, ffprobe_executable=_FFPROBE,
            ).compose(task)
            self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_COMPOSITION_FAILED", "local media composition failed"))
            self.assertFalse(marker.exists())

            class MissingReadWorkspace:
                def read(self, _reference):
                    return WorkspaceFailure("WORKSPACE_FILE_NOT_FOUND", "workspace file was not found")

                def commit(self, _reference, _content):
                    raise AssertionError("missing input must stop before commit")

            result = FFmpegMediaComposer(
                MissingReadWorkspace(), ffmpeg_executable=ffmpeg, ffprobe_executable=_FFPROBE,
            ).compose(task)
            self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_COMPOSITION_FAILED", "local media composition failed"))
            self.assertFalse(marker.exists())

            class MalformedCommitWorkspace:
                def read(self, reference):
                    return real_workspace.read(reference)

                def commit(self, _reference, _content):
                    return object()

            result = FFmpegMediaComposer(
                MalformedCommitWorkspace(), ffmpeg_executable=_FFMPEG, ffprobe_executable=_FFPROBE,
            ).compose(task)
            self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_STORAGE_FAILED", "media output storage failed"))

    def test_invalid_tool_and_timeout_fail_before_workspace_reads(self):
        class SpyWorkspace:
            def __init__(self):
                self.read_calls = 0

            def read(self, _reference):
                self.read_calls += 1
                raise AssertionError("invalid configuration must not read")

            def commit(self, _reference, _content):
                raise AssertionError("invalid configuration must not commit")

        with TemporaryDirectory() as directory:
            _root = Path(directory)
            _workspace, task = _composition_fixture(_root)
            spy = SpyWorkspace()
            result = FFmpegMediaComposer(spy, ffmpeg_executable="ffmpeg", ffprobe_executable=_FFPROBE).compose(task)
            self.assertEqual(result.code, "MEDIA_TOOL_UNAVAILABLE")
            self.assertEqual(spy.read_calls, 0)
            spy = SpyWorkspace()
            result = FFmpegMediaComposer(
                spy, ffmpeg_executable=_FFMPEG, ffprobe_executable=_FFPROBE, timeout_seconds=10**10000,
            ).compose(task)
            self.assertEqual(result.code, "INVALID_MEDIA_TOOL_TIMEOUT")
            self.assertEqual(spy.read_calls, 0)


if __name__ == "__main__":
    unittest.main()
