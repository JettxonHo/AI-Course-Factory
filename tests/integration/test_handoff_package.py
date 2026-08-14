"""Real FFmpeg integration for the deterministic handoff package."""

from pathlib import Path
from tempfile import TemporaryDirectory
import base64
import io
import json
import shutil
import subprocess
import unittest
import zipfile

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.persistence import WorkspaceFileReference
from ai_course_factory.production import (
    FFmpegFixtureVoiceGenerator,
    LocalNarrationPreflight,
    LocalNarrationResult,
    VoiceSynthesisTask,
)

from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL


_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")


class _FFmpegNarrationRenderer:
    def __init__(self, workspace, ffmpeg: str, ffprobe: str):
        self.workspace = workspace
        self.delegate = FFmpegFixtureVoiceGenerator(workspace, ffmpeg_executable=ffmpeg, ffprobe_executable=ffprobe)
        self.calls = 0

    def preflight(self):
        return LocalNarrationPreflight("fixture-commit", "fixture-model", "reference audio", "你好。")

    def render(self, task):
        self.calls += 1
        result = self.delegate.synthesize(VoiceSynthesisTask(task.task_id, f"local:{task.scene_id}", task.production_request_reference, task.scene_id, task.language, task.duration_seconds, task.narration, task.output_reference))
        if not hasattr(result, "output_reference"):
            raise AssertionError(result)
        return LocalNarrationResult(task.task_id, task.scene_id, result.output_reference, result.media_type, result.duration_seconds, result.result_code)


class HandoffPackageIntegrationTests(unittest.TestCase):
    def test_real_ffmpeg_narrations_are_aac_48khz_mono_and_zip_is_replayable(self):
        ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG)
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), visual_import_dir=still_dir)
            renderer = _FFmpegNarrationRenderer(app.workspace, ffmpeg, ffprobe)
            app.local_narration_renderer = renderer
            app.start_source(SUPPORTED_REPOSITORY_URL)
            app.submit_script_decision("approve")
            app.advance_planning()
            app.submit_storyboard_decision("approve")
            prepared = app.prepare_handoff_package()
            self.assertEqual(prepared.status, "success", prepared.error_message)
            self.assertEqual(renderer.calls, 6)
            package = app.read_output("handoff_package")
            self.assertIsNotNone(package)
            with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
                manifest = json.loads(archive.read("handoff-manifest.json"))
                self.assertEqual(len(manifest["files"]), 18)
                for index in range(1, 7):
                    content = archive.read(f"narration/scene-{index}.m4a")
                    probe = subprocess.run([ffprobe, "-v", "error", "-show_entries", "stream=codec_type,codec_name,sample_rate,channels", "-of", "json", "-"], input=content, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
                    self.assertEqual(probe.returncode, 0)
                    stream = json.loads(probe.stdout)["streams"][0]
                    self.assertEqual((stream["codec_type"], stream["codec_name"], stream["sample_rate"], stream["channels"]), ("audio", "aac", "48000", 1))
            app.close()


if __name__ == "__main__":
    unittest.main()
