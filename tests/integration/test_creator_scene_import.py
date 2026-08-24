from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import shutil
import subprocess
import unittest

from ai_course_factory.application import CourseFactoryApplication
from tests.integration.test_handoff_package import _FFmpegNarrationRenderer, _PNG
from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL
from tests.legacy_v11_fixture import seed_legacy_script_review


class CreatorSceneImportRestartIntegrationTests(unittest.TestCase):
    def test_final_video_and_srt_survive_restart_without_generated_clips_directory(self) -> None:
        ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
        with TemporaryDirectory() as directory, TemporaryDirectory() as still_directory:
            root = Path(directory)
            clips = root / "generated-clips"
            clips.mkdir()
            stills = Path(still_directory)
            for index in range(1, 7):
                (stills / f"scene-{index}.png").write_bytes(_PNG)
                completed = subprocess.run(
                    [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=blue:s=540x960:r=24:d=10", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24", str(clips / f"scene-{index}.mp4")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
            first = CourseFactoryApplication(root / "data", source_connector=FixtureSourceConnector(), generated_clips_directory=clips, visual_import_dir=stills)
            first.local_narration_renderer = _FFmpegNarrationRenderer(first.workspace, ffmpeg, ffprobe)
            started = first.start_source(SUPPORTED_REPOSITORY_URL)
            self.assertEqual(started.status, "success", started.error_message)
            seed_legacy_script_review(first)
            for result in (
                first.submit_script_decision("approve"),
                first.advance_planning(),
                first.submit_storyboard_decision("approve"),
                first.prepare_handoff_package(),
                first.import_generated_scene_clips(),
            ):
                self.assertEqual(result.status, "success", result.error_message)
            before = first.inspect()
            self.assertEqual(before.view.stage, "final_review")
            before_video = before.view.video_reference
            before_facts = before.view.imported_scene_facts
            self.assertEqual(len(before_facts), 6)
            before_scene_clips = tuple(scene.selected_clip_reference for scene in before.view.scenes)
            before_scene_audio = tuple(scene.selected_audio_reference for scene in before.view.scenes)
            before_subtitle = before.view.subtitle_reference
            shutil.copyfile(clips / "scene-2.mp4", clips / "scene-2-replacement.mp4")
            replaced = first.replace_scene("scene-2")
            self.assertEqual(replaced.status, "success", (replaced.error_code, replaced.error_message))
            self.assertTrue(replaced.view.replacement_done)
            self.assertEqual(replaced.view.video_reference.version, before_video.version + 1)
            self.assertEqual(tuple(scene.selected_audio_reference for scene in replaced.view.scenes), before_scene_audio)
            self.assertEqual(replaced.view.subtitle_reference, before_subtitle)
            after_scene_clips = tuple(scene.selected_clip_reference for scene in replaced.view.scenes)
            self.assertEqual(after_scene_clips[0], before_scene_clips[0])
            self.assertEqual(after_scene_clips[2:], before_scene_clips[2:])
            self.assertEqual(after_scene_clips[1].version, before_scene_clips[1].version + 1)
            first.close()

            resumed = CourseFactoryApplication(root / "data", source_connector=FixtureSourceConnector())
            inspected = resumed.inspect()

            self.assertEqual(inspected.status, "success")
            self.assertEqual(inspected.view.stage, "final_review")
            self.assertEqual(inspected.view.video_reference.version, before_video.version + 1)
            self.assertEqual(len(inspected.view.imported_scene_facts), 6)
            self.assertIsNotNone(resumed.read_output("video"))
            self.assertIsNotNone(resumed.read_output("subtitle"))
            repeated = resumed.import_generated_scene_clips()
            self.assertEqual(repeated.status, "success")
            self.assertEqual(repeated.view.video_reference, inspected.view.video_reference)
            resumed.close()


if __name__ == "__main__":
    unittest.main()
