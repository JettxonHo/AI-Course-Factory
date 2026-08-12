"""Public behavior tests for the local FFmpeg Fixture adapters."""

from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference
from ai_course_factory.production import (
    FFmpegFixtureVisualGenerator,
    FFmpegFixtureVoiceGenerator,
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VisualGenerator,
    VoiceGenerator,
    VoiceSynthesisTask,
)


def _tasks(task_id="task:fixture"):
    request = ArtifactReference("production_request", "episode-1", 1)
    return (
        VisualGenerationTask(
            task_id, "attempt:visual:1", request, "scene-1", "9:16", 1.0,
            "show the lesson", "wave", WorkspaceFileReference(task_id, "media", "scene-1.mp4"),
        ),
        VoiceSynthesisTask(
            task_id, "attempt:voice:1", request, "scene-1", "zh-CN", 1.0,
            "你好。", WorkspaceFileReference(task_id, "media", "scene-1.m4a"),
        ),
    )


def _probe(path):
    result = subprocess.run(
        [
            "/opt/homebrew/bin/ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,duration,sample_rate,channels,r_frame_rate,avg_frame_rate:format=format_name,duration:format_tags=comment",
            "-of", "json", str(path),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return json.loads(result.stdout.decode("utf-8"))


def _wrapped_probe(directory: Path, mutation: str) -> str:
    path = directory / f"ffprobe-{mutation}.py"
    mutation_line = (
        'payload["streams"][0]["r_frame_rate"] = "25/1"'
        if mutation == "fps"
        else 'payload["format"]["format_name"] = "avi"'
    )
    path.write_text(
        f"#!{sys.executable}\n"
        "import json, subprocess, sys\n"
        "result = subprocess.run(['/opt/homebrew/bin/ffprobe', *sys.argv[1:]], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, check=True)\n"
        "payload = json.loads(result.stdout.decode('utf-8'))\n"
        f"{mutation_line}\n"
        "print(json.dumps(payload))\n",
        encoding="utf-8",
    )
    path.chmod(0o755)
    return str(path)


class FFmpegFixtureAdapterTests(unittest.TestCase):
    def test_visual_fixture_is_playable_probeable_and_uses_public_contract(self):
        with TemporaryDirectory() as directory:
            workspace = FilesystemWorkspace(Path(directory) / "workspace")
            self.assertIsNotNone(workspace.prepare("task:fixture"))
            output = WorkspaceFileReference("task:fixture", "media", "scene-1.mp4")
            task = VisualGenerationTask(
                "task:fixture",
                "attempt:visual:1",
                ArtifactReference("production_request", "episode-1", 1),
                "scene-1",
                "9:16",
                1.0,
                "show the lesson",
                "wave",
                output,
            )

            adapter = FFmpegFixtureVisualGenerator(
                workspace,
                ffmpeg_executable="/opt/homebrew/bin/ffmpeg",
                ffprobe_executable="/opt/homebrew/bin/ffprobe",
            )
            self.assertIsInstance(adapter, VisualGenerator)
            result = adapter.generate(task)

            self.assertIsInstance(result, MediaGenerationResult)
            self.assertEqual(result.provider, "ffmpeg-fixture-visual-v1")
            self.assertEqual(result.media_type, "video/mp4")
            self.assertEqual(result.output_reference, output)
            media = workspace.read(output)
            self.assertIsInstance(media, bytes)
            self.assertIn(b"ftyp", media[:128])
            materialized = Path(directory) / "scene.mp4"
            materialized.write_bytes(media)
            probe = _probe(materialized)
            self.assertEqual(probe["streams"][0]["r_frame_rate"], "24/1")
            self.assertEqual(probe["streams"][0]["avg_frame_rate"], "24/1")
            self.assertEqual(probe["format"]["format_name"], "mov,mp4,m4a,3gp,3g2,mj2")

    def test_voice_fixture_is_playable_probeable_and_has_artificial_profile(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:fixture")
            _visual, task = _tasks()
            adapter = FFmpegFixtureVoiceGenerator(
                workspace,
                ffmpeg_executable="/opt/homebrew/bin/ffmpeg",
                ffprobe_executable="/opt/homebrew/bin/ffprobe",
            )
            self.assertIsInstance(adapter, VoiceGenerator)
            result = adapter.synthesize(task)
            self.assertIsInstance(result, MediaGenerationResult)
            self.assertEqual(result.operation, "voice")
            self.assertEqual(result.provider, "ffmpeg-fixture-voice-v1")
            self.assertEqual(result.media_type, "audio/mp4")
            media = workspace.read(task.output_reference)
            self.assertIsInstance(media, bytes)
            self.assertIn(b"ftyp", media[:128])
            materialized = root / "scene.m4a"
            materialized.write_bytes(media)
            probe = _probe(materialized)
            self.assertEqual(len(probe["streams"]), 1)
            stream = probe["streams"][0]
            self.assertEqual(stream["codec_type"], "audio")
            self.assertEqual(stream["codec_name"], "aac")
            self.assertEqual(stream["sample_rate"], "48000")
            self.assertEqual(stream["channels"], 1)
            self.assertNotIn("video", {item["codec_type"] for item in probe["streams"]})
            self.assertEqual(probe["format"]["format_name"], "mov,mp4,m4a,3gp,3g2,mj2")

    def test_replay_is_byte_exact_and_changed_input_conflicts_without_overwrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            workspace = FilesystemWorkspace(root / "workspace")
            workspace.prepare("task:fixture")
            visual_task, voice_task = _tasks()
            kwargs = {
                "ffmpeg_executable": "/opt/homebrew/bin/ffmpeg",
                "ffprobe_executable": "/opt/homebrew/bin/ffprobe",
            }
            visual_adapter = FFmpegFixtureVisualGenerator(workspace, **kwargs)
            first = visual_adapter.generate(visual_task)
            original = workspace.read(visual_task.output_reference)
            replay = FFmpegFixtureVisualGenerator(FilesystemWorkspace(root / "workspace"), **kwargs).generate(visual_task)
            self.assertEqual(replay, first)
            self.assertEqual(FilesystemWorkspace(root / "workspace").read(visual_task.output_reference), original)
            conflict = FFmpegFixtureVisualGenerator(FilesystemWorkspace(root / "workspace"), **kwargs).generate(
                replace(visual_task, visual_intent="different lesson")
            )
            self.assertIsInstance(conflict, ProductionMediaFailure)
            self.assertEqual(conflict.code, "MEDIA_OUTPUT_CONFLICT")
            self.assertEqual(FilesystemWorkspace(root / "workspace").read(visual_task.output_reference), original)

            first_voice = FFmpegFixtureVoiceGenerator(workspace, **kwargs).synthesize(voice_task)
            original_voice = workspace.read(voice_task.output_reference)
            replay_voice = FFmpegFixtureVoiceGenerator(FilesystemWorkspace(root / "workspace"), **kwargs).synthesize(voice_task)
            self.assertEqual(replay_voice, first_voice)
            conflict_voice = FFmpegFixtureVoiceGenerator(FilesystemWorkspace(root / "workspace"), **kwargs).synthesize(
                replace(voice_task, narration="改写后的旁白。")
            )
            self.assertIsInstance(conflict_voice, ProductionMediaFailure)
            self.assertEqual(conflict_voice.code, "MEDIA_OUTPUT_CONFLICT")
            self.assertEqual(FilesystemWorkspace(root / "workspace").read(voice_task.output_reference), original_voice)

    def test_invalid_configuration_timeout_and_task_fail_before_workspace_commit(self):
        class SpyWorkspace:
            def __init__(self):
                self.calls = 0

            def commit(self, _reference, _content):
                self.calls += 1
                raise AssertionError("invalid input must not commit")

        task, voice_task = _tasks()
        for adapter in (
            FFmpegFixtureVisualGenerator(SpyWorkspace(), ffmpeg_executable="ffmpeg", ffprobe_executable="/opt/homebrew/bin/ffprobe"),
            FFmpegFixtureVoiceGenerator(SpyWorkspace(), ffmpeg_executable="/opt/homebrew/bin/ffmpeg", ffprobe_executable="ffprobe"),
        ):
            result = adapter.generate(task) if isinstance(adapter, VisualGenerator) else adapter.synthesize(voice_task)
            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "MEDIA_TOOL_UNAVAILABLE")
        for timeout in (True, False, 0, 121, 10**10_000, float("inf"), float("nan")):
            workspace = SpyWorkspace()
            result = FFmpegFixtureVisualGenerator(
                workspace,
                ffmpeg_executable="/opt/homebrew/bin/ffmpeg",
                ffprobe_executable="/opt/homebrew/bin/ffprobe",
                timeout_seconds=timeout,
            ).generate(task)
            self.assertEqual(result.code, "INVALID_MEDIA_TOOL_TIMEOUT")
            self.assertEqual(workspace.calls, 0)
        workspace = SpyWorkspace()
        invalid = replace(task, production_request_reference=ArtifactReference("script", "episode-1", 1))
        result = FFmpegFixtureVisualGenerator(
            workspace,
            ffmpeg_executable="/opt/homebrew/bin/ffmpeg",
            ffprobe_executable="/opt/homebrew/bin/ffprobe",
        ).generate(invalid)
        self.assertEqual(result.code, "INVALID_PRODUCTION_REQUEST_REFERENCE")
        self.assertEqual(workspace.calls, 0)

    def test_wrong_probe_frame_rate_or_container_fails_without_workspace_commit(self):
        class SpyWorkspace:
            def __init__(self):
                self.calls = 0

            def commit(self, _reference, _content):
                self.calls += 1
                raise AssertionError("invalid probe must not commit")

        task, _voice_task = _tasks()
        with TemporaryDirectory() as directory:
            root = Path(directory)
            for mutation in ("fps", "container"):
                workspace = SpyWorkspace()
                result = FFmpegFixtureVisualGenerator(
                    workspace,
                    ffmpeg_executable="/opt/homebrew/bin/ffmpeg",
                    ffprobe_executable=_wrapped_probe(root, mutation),
                ).generate(task)
                self.assertIsInstance(result, ProductionMediaFailure)
                self.assertEqual(result.code, "MEDIA_GENERATION_FAILED")
                self.assertEqual(workspace.calls, 0)


if __name__ == "__main__":
    unittest.main()
