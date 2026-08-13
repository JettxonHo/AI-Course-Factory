from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from ai_course_factory.web import create_app


def _client(directory: str) -> TestClient:
    return TestClient(create_app(Path(directory)), base_url="http://127.0.0.1")


def _post(client: TestClient, path: str, data: dict[str, str] | None = None, **kwargs: object):
    headers = {"Origin": "http://127.0.0.1"}
    headers.update(kwargs.pop("headers", {}) or {})
    return client.post(path, data=data, headers=headers, **kwargs)


class OfflineWorkspaceWebTests(unittest.TestCase):
    def test_start_view_is_server_rendered_and_exposes_three_view_kinds(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)

            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn("Start / Current Task", response.text)
            self.assertIn('data-view-kind="start"', response.text)
            self.assertNotIn("{{", response.text)
            self.assertEqual(response.headers["x-content-type-options"], "nosniff")
            self.assertEqual(response.headers["referrer-policy"], "same-origin")

    def test_script_approval_posts_through_facade_and_redirects_to_review(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)

            response = _post(client, "/start/script", {"action": "approve_script"}, follow_redirects=False)

            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/review")
            review = client.get("/review")
            self.assertEqual(review.status_code, 200)
            self.assertIn("planning", review.text)

    def test_script_revise_and_reject_actions_require_context_and_expose_v2_gate(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)
            client.get("/")

            missing = _post(client, "/start/script", {"action": "revise_script"})
            self.assertEqual(missing.status_code, 400)
            revised = _post(client, "/start/script", {"action": "revise_script", "decision_context": "clarify the opening"}, follow_redirects=False)
            self.assertEqual(revised.status_code, 303)
            self.assertEqual(revised.headers["location"], "/")
            start = client.get("/")
            self.assertIn("script:episode-1 v2", start.text)
            self.assertIn("Reject and revise", start.text)

            rejected = _post(client, "/start/script", {"action": "reject_script", "decision_context": "remove unsupported wording"}, follow_redirects=False)
            self.assertEqual(rejected.status_code, 303)
            self.assertIn("script:episode-1 v3", client.get("/").text)

    def test_form_boundary_rejects_unknown_scene_without_calling_internal_paths(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)

            response = _post(client, "/final/action", {"action": "replace_scene", "scene_id": "../../etc/passwd"})

            self.assertEqual(response.status_code, 400)
            self.assertNotIn("etc/passwd", response.text)
            self.assertNotIn("Traceback", response.text)

    def test_static_css_and_download_routes_have_safe_not_found_responses(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)

            css = client.get("/static/style.css")
            missing = client.get("/media/not-a-file")

            self.assertEqual(css.status_code, 200)
            self.assertIn("prefers-reduced-motion", css.text)
            self.assertEqual(missing.status_code, 404)
            self.assertEqual(missing.text, "Not found.")

    def test_three_view_loop_reaches_video_and_package_downloads(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)
            client.get("/")
            self.assertEqual(_post(client, "/start/script", {"action": "approve_script"}, follow_redirects=False).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "advance_planning"}, follow_redirects=False).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "approve_budget"}, follow_redirects=False).status_code, 303)
            produced = _post(client, "/review/action", {"action": "produce_offline"}, follow_redirects=False)

            self.assertEqual(produced.status_code, 303)
            self.assertEqual(produced.headers["location"], "/final")
            final = client.get("/final")
            self.assertEqual(final.status_code, 200)
            self.assertIn("/media/video", final.text)
            video = client.get("/media/video")
            subtitle = client.get("/media/subtitle")
            self.assertEqual(video.status_code, 200)
            self.assertEqual(video.headers["content-type"], "video/mp4")
            self.assertTrue(video.content.startswith(b"\x00\x00\x00"))
            self.assertIn(b"ftyp", video.content[:64])
            self.assertEqual(subtitle.status_code, 200)
            self.assertEqual(subtitle.headers["content-type"], "application/x-subrip; charset=utf-8")
            self.assertTrue(subtitle.content.strip())

            replacement = _post(client, "/final/action", {"action": "replace_scene", "scene_id": "scene-2"}, follow_redirects=False)
            self.assertEqual(replacement.status_code, 303)
            replaced_final = client.get("/final")
            self.assertIn('value="approve_final"', replaced_final.text)
            replaced_video = client.get("/media/video")
            replaced_subtitle = client.get("/media/subtitle")
            self.assertEqual(replaced_video.status_code, 200)
            self.assertEqual(replaced_video.headers["content-type"], "video/mp4")
            self.assertIn(b"ftyp", replaced_video.content[:64])
            self.assertEqual(replaced_subtitle.status_code, 200)
            self.assertTrue(replaced_subtitle.content.strip())
            self.assertEqual(_post(client, "/final/action", {"action": "approve_final"}, follow_redirects=False).status_code, 303)
            approved_final = client.get("/final")
            self.assertIn("Available actions:</strong> export_package", approved_final.text)
            exported = _post(client, "/final/action", {"action": "export_package"}, follow_redirects=False)
            self.assertEqual(exported.status_code, 303)
            self.assertEqual(client.get("/media/video").status_code, 200)
            self.assertEqual(client.get("/media/subtitle").status_code, 200)
            package = client.get("/media/package")
            self.assertEqual(package.status_code, 200)
            self.assertEqual(package.headers["content-type"], "application/zip")

    def test_final_reject_requires_context_and_blocks_export(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)
            client.get("/")
            _post(client, "/start/script", {"action": "approve_script"})
            _post(client, "/review/action", {"action": "advance_planning"})
            _post(client, "/review/action", {"action": "approve_budget"})
            _post(client, "/review/action", {"action": "produce_offline"})

            missing = _post(client, "/final/action", {"action": "reject_final"})
            self.assertEqual(missing.status_code, 400)
            rejected = _post(client, "/final/action", {"action": "reject_final", "decision_context": "quality remains insufficient"}, follow_redirects=False)
            self.assertEqual(rejected.status_code, 303)
            final = client.get("/final")
            self.assertIn("replace_scene", final.text)
            self.assertNotIn("Approve final video", final.text)
            self.assertNotIn("Export package", final.text)

    def test_web_failure_exposes_safe_category_and_recovery_action(self) -> None:
        with TemporaryDirectory() as directory:
            app = create_app(Path(directory))
            client = TestClient(app, base_url="http://127.0.0.1")
            client.get("/")
            app.state.course_factory.ffmpeg_executable = "/missing/ffmpeg"
            app.state.course_factory.ffprobe_executable = "/missing/ffprobe"
            _post(client, "/start/script", {"action": "approve_script"})
            _post(client, "/review/action", {"action": "advance_planning"})
            _post(client, "/review/action", {"action": "approve_budget"})
            failed = _post(client, "/review/action", {"action": "produce_offline"})

            self.assertEqual(failed.status_code, 400)
            self.assertIn("generation_failure", failed.text)
            self.assertIn("Produce offline Fixture", failed.text)
            self.assertNotIn("/missing/ffmpeg", failed.text)
            self.assertNotIn("Traceback", failed.text)

    def test_browser_process_reconstruction_keeps_the_current_gate(self) -> None:
        with TemporaryDirectory() as directory:
            first_app = create_app(Path(directory))
            first_client = TestClient(first_app, base_url="http://127.0.0.1")
            first_client.get("/")
            _post(first_client, "/start/script", {"action": "approve_script"})
            first_app.state.course_factory.close()

            resumed_client = TestClient(create_app(Path(directory)), base_url="http://127.0.0.1")
            review = resumed_client.get("/review")

            self.assertEqual(review.status_code, 200)
            self.assertIn("planning", review.text)
            self.assertIn("Build production plan", review.text)

    def test_mutation_requires_loopback_same_origin_before_facade(self) -> None:
        with TemporaryDirectory() as directory:
            app = create_app(Path(directory))
            client = TestClient(app, base_url="http://127.0.0.1")

            missing = client.post("/start/script", data={"action": "approve_script"})
            foreign = client.post("/start/script", data={"action": "approve_script"}, headers={"Origin": "https://evil.example"})
            foreign_referer = client.post("/start/script", data={"action": "approve_script"}, headers={"Referer": "https://evil.example/start"})
            hostile = client.post("/start/script", data={"action": "approve_script"}, headers={"Host": "evil.example", "Origin": "http://evil.example"})

            self.assertEqual((missing.status_code, foreign.status_code, foreign_referer.status_code, hostile.status_code), (400, 400, 400, 400))
            self.assertEqual(missing.text, "Request unavailable.")
            self.assertIsNone(app.state.course_factory)

    def test_mutation_accepts_same_origin_referer_without_origin(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)
            client.get("/")

            response = client.post(
                "/start/script",
                data={"action": "approve_script"},
                headers={"Referer": "http://127.0.0.1/start"},
                follow_redirects=False,
            )

            self.assertEqual(response.status_code, 303)

    def test_mutation_accepts_same_origin_fetch_metadata_without_origin(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)
            client.get("/")

            fallback = client.post(
                "/start/script",
                data={"action": "approve_script"},
                headers={"Sec-Fetch-Site": "same-origin", "Sec-Fetch-Mode": "navigate"},
                follow_redirects=False,
            )
            foreign = client.post(
                "/review/action",
                data={"action": "advance_planning"},
                headers={"Origin": "https://evil.example", "Sec-Fetch-Site": "same-origin"},
            )

            self.assertEqual(fallback.status_code, 303)
            self.assertEqual(foreign.status_code, 400)


if __name__ == "__main__":
    unittest.main()
