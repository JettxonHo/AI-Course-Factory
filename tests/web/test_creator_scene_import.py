from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import json
import sqlite3
import shutil
import subprocess
import unittest

from fastapi.testclient import TestClient

from ai_course_factory.web import create_app
from tests.integration.test_handoff_package import _FFmpegNarrationRenderer, _PNG
from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL


def _post(client: TestClient, path: str, data: dict[str, str]):
    return client.post(path, data=data, headers={"Origin": "http://127.0.0.1"}, follow_redirects=False)


def _creator_media_signature(data_dir: Path):
    with sqlite3.connect(data_dir / "factory.sqlite3") as connection:
        row = connection.execute("SELECT state_json FROM application_state WHERE singleton = 1").fetchone()
    assert row is not None
    state = json.loads(row[0])
    composition = state["composition"]
    return (
        tuple(composition["scene_clip_references"]),
        tuple(composition["scene_audio_references"]),
        composition["subtitle_reference"],
        composition["master_audio_reference"],
        composition["video_reference"],
    )


def _artifact_counts(data_dir: Path):
    kinds = ("scene_clip", "scene_audio", "subtitle", "master_audio", "video")
    with sqlite3.connect(data_dir / "factory.sqlite3") as connection:
        rows = connection.execute(
            "SELECT artifact_type, COUNT(*) FROM artifact_versions WHERE artifact_type IN (?, ?, ?, ?, ?) GROUP BY artifact_type",
            kinds,
        ).fetchall()
    counts = dict(rows)
    return tuple((kind, counts.get(kind, 0)) for kind in kinds)


class CreatorSceneImportWebTests(unittest.TestCase):
    def test_review_import_action_has_no_path_field_and_final_allows_only_scene_two(self) -> None:
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
            app = create_app(root / "data", source_connector=FixtureSourceConnector(), visual_import_dir=stills, generated_clips_directory=clips)
            client = TestClient(app, base_url="http://127.0.0.1")
            # The app creates the facade lazily; inject the deterministic local
            # narration renderer before the handoff POST.
            client.get("/")
            client.app.state.course_factory.local_narration_renderer = _FFmpegNarrationRenderer(client.app.state.course_factory.workspace, ffmpeg, ffprobe)
            self.assertEqual(_post(client, "/start/source", {"repository_url": SUPPORTED_REPOSITORY_URL}).status_code, 303)
            self.assertEqual(_post(client, "/start/script", {"action": "approve_script"}).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "advance_planning"}).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "approve_storyboard"}).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "prepare_handoff_package"}).status_code, 303)

            review = client.get("/review")
            self.assertEqual(review.status_code, 200)
            self.assertIn("import_generated_scene_clips", review.text)
            self.assertIn('class="button button-primary" name="action" value="import_generated_scene_clips">导入 6 段场景视频', review.text)
            self.assertIn('class="button button-secondary" href="/media/handoff_package"', review.text)
            self.assertNotIn(str(clips), review.text)
            self.assertNotIn("generated_clips_directory", review.text)
            first_import = _post(client, "/review/action", {"action": "import_generated_scene_clips"})
            self.assertEqual(first_import.status_code, 303)
            self.assertEqual(first_import.headers["location"], "/review")
            imported_review = client.get("/review")
            self.assertIn("前往终审", imported_review.text)

            before_refs = _creator_media_signature(root / "data")
            before_counts = _artifact_counts(root / "data")

            repeated_import = _post(client, "/review/action", {"action": "import_generated_scene_clips"})
            self.assertEqual(repeated_import.status_code, 303)
            self.assertEqual(repeated_import.headers["location"], "/review")
            self.assertEqual(_creator_media_signature(root / "data"), before_refs)
            self.assertEqual(_artifact_counts(root / "data"), before_counts)

            final = client.get("/final")
            self.assertEqual(final.status_code, 200)
            self.assertIn("scene-1.mp4", final.text)
            self.assertIn("scene-6.mp4", final.text)
            self.assertIn('name="scene_id" value="scene-2"', final.text)
            self.assertNotIn('name="scene_id" value="scene-1"', final.text)
            rejected_path_form = _post(client, "/review/action", {"action": "import_generated_scene_clips", "generated_clips_directory": str(clips)})
            self.assertEqual(rejected_path_form.status_code, 400)

            client.close()
            recreated_app = create_app(root / "data", source_connector=FixtureSourceConnector(), visual_import_dir=stills)
            recreated = TestClient(recreated_app, base_url="http://127.0.0.1")
            try:
                reopened = recreated.get("/review")
                self.assertEqual(reopened.status_code, 200)
                self.assertIn("scene-1.mp4", reopened.text)
                repeated_after_restart = _post(recreated, "/review/action", {"action": "import_generated_scene_clips"})
                self.assertEqual(repeated_after_restart.status_code, 303)
                self.assertEqual(repeated_after_restart.headers["location"], "/review")
                self.assertEqual(_creator_media_signature(root / "data"), before_refs)
                self.assertEqual(_artifact_counts(root / "data"), before_counts)
            finally:
                recreated.close()


if __name__ == "__main__":
    unittest.main()
