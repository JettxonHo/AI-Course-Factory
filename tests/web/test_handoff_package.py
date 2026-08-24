"""Public three-view HTTP behavior for the Creator Handoff Package."""

from pathlib import Path
from tempfile import TemporaryDirectory
import base64
import unittest

from fastapi.testclient import TestClient

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.persistence import FilesystemWorkspace
from ai_course_factory.production import LocalNarrationPreflight, LocalNarrationResult
from ai_course_factory.web import create_app

from tests.legacy_v11_fixture import seed_legacy_script_review
from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL


_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")


class _FakeNarrationRenderer:
    def __init__(self, workspace):
        self.workspace = workspace

    def preflight(self):
        return LocalNarrationPreflight("fake-commit", "fake-model", "reference audio", "你好。")

    def render(self, task):
        content = f"fake-audio-{task.scene_id}".encode("ascii")
        if not hasattr(self.workspace.commit(task.output_reference, content), "reference"):
            raise AssertionError
        return LocalNarrationResult(task.task_id, task.scene_id, task.output_reference, "audio/mp4", task.duration_seconds, "SUCCESS")


class HandoffPackageWebTests(unittest.TestCase):
    def test_review_prepare_and_safe_download_keep_three_view_contract(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG)
            seed_app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())
            self.assertEqual(seed_app.start_source(SUPPORTED_REPOSITORY_URL).status, "success")
            seed_legacy_script_review(seed_app)
            seed_app.close()
            renderer = _FakeNarrationRenderer(FilesystemWorkspace(Path(directory) / "workspace"))
            client = TestClient(create_app(Path(directory), source_connector=FixtureSourceConnector(), visual_import_dir=still_dir, local_narration_renderer=renderer), base_url="http://127.0.0.1")
            headers = {"Origin": "http://127.0.0.1"}
            self.assertEqual(client.post("/start/source", data={"repository_url": SUPPORTED_REPOSITORY_URL}, headers=headers, follow_redirects=False).status_code, 303)
            self.assertEqual(client.post("/start/script", data={"action": "approve_script", "decision_context": ""}, headers=headers, follow_redirects=False).status_code, 303)
            self.assertEqual(client.post("/review/action", data={"action": "advance_planning", "decision_context": ""}, headers=headers, follow_redirects=False).status_code, 303)
            self.assertEqual(client.post("/review/action", data={"action": "approve_storyboard", "decision_context": ""}, headers=headers, follow_redirects=False).status_code, 303)
            review = client.get("/review")
            self.assertEqual(review.status_code, 200)
            self.assertIn("准备创作交接包", review.text)
            self.assertIn("外部生成边界", review.text)
            self.assertNotIn("等待预算", review.text)
            self.assertIn("手动交接无需预算授权", review.text)
            self.assertIn("手动交接", review.text)
            self.assertNotIn(str(still_dir), review.text)
            prepared = client.post("/review/action", data={"action": "prepare_handoff_package", "decision_context": ""}, headers=headers, follow_redirects=False)
            self.assertEqual(prepared.status_code, 303)
            completed = client.get("/review")
            self.assertEqual(completed.status_code, 200)
            self.assertIn("下载创作交接包", completed.text)
            self.assertIn('class="button button-primary" href="/media/handoff_package"', completed.text)
            self.assertIn("handoff-narration-scene-1.m4a", completed.text)
            self.assertIn("handoff-narration-scene-6.m4a", completed.text)
            self.assertNotIn(str(directory), completed.text)
            self.assertIn("外部生成边界", completed.text)
            self.assertNotIn("等待预算", completed.text)
            self.assertIn("手动交接无需预算授权", completed.text)
            self.assertIn("手动交接", completed.text)
            download = client.get("/media/handoff_package")
            self.assertEqual(download.status_code, 200)
            self.assertEqual(download.headers["content-type"], "application/zip")
            self.assertIn("attachment", download.headers["content-disposition"])
            self.assertGreater(len(download.content), 100)
            for route in ("/", "/review", "/final"):
                self.assertEqual(client.get(route).status_code, 200)
            client.close()


if __name__ == "__main__":
    unittest.main()
