from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import re

from fastapi.testclient import TestClient

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.web import create_app
from tests.legacy_v11_fixture import seed_legacy_budget_review, seed_legacy_script_review
from tests.source_fixture import SUPPORTED_REPOSITORY_URL, FixtureSourceConnector


def _client(directory: str, *, source_started: bool = True) -> TestClient:
    if source_started:
        app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())
        if app.start_source(SUPPORTED_REPOSITORY_URL).status != "success":
            raise AssertionError("source initialization failed")
        seed_legacy_script_review(app)
        app.close()
        return TestClient(create_app(Path(directory), source_connector=FixtureSourceConnector()), base_url="http://127.0.0.1")
    client = TestClient(
        create_app(Path(directory), source_connector=FixtureSourceConnector()),
        base_url="http://127.0.0.1",
    )
    if source_started:
        started = client.post(
            "/start/source",
            data={"repository_url": SUPPORTED_REPOSITORY_URL},
            headers={"Origin": "http://127.0.0.1"},
            follow_redirects=False,
        )
        if started.status_code != 303:
            raise AssertionError(started.text)
    return client


def _post(client: TestClient, path: str, data: dict[str, str] | None = None, **kwargs: object):
    headers = {"Origin": "http://127.0.0.1"}
    headers.update(kwargs.pop("headers", {}) or {})
    return client.post(path, data=data, headers=headers, **kwargs)


def _legacy_client(directory: str, **kwargs: object) -> TestClient:
    app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), **kwargs)
    if app.start_source(SUPPORTED_REPOSITORY_URL).status != "success":
        raise AssertionError("source initialization failed")
    seed_legacy_budget_review(app)
    app.close()
    execution = {key: kwargs[key] for key in ("ffmpeg_executable", "ffprobe_executable") if key in kwargs}
    client = TestClient(create_app(Path(directory), source_connector=FixtureSourceConnector()), base_url="http://127.0.0.1")
    if execution:
        client.get("/review")
        for key, value in execution.items():
            setattr(client.app.state.course_factory, key, value)
    return client


class OfflineWorkspaceWebTests(unittest.TestCase):
    def test_fresh_get_renders_source_intake_without_connector_or_task_write(self) -> None:
        with TemporaryDirectory() as directory:
            connector = FixtureSourceConnector()
            app = create_app(Path(directory), source_connector=connector)
            client = TestClient(app, base_url="http://127.0.0.1")

            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn("输入公开课程仓库", response.text)
            self.assertIn('name="repository_url"', response.text)
            self.assertEqual(response.text.count('name="repository_url"'), 1)
            self.assertEqual(connector.calls, [])
            self.assertFalse((Path(directory) / "workspace").exists())

    def test_source_post_rejects_unsupported_url_without_connector_or_task_write(self) -> None:
        with TemporaryDirectory() as directory:
            connector = FixtureSourceConnector()
            app = create_app(Path(directory), source_connector=connector)
            client = TestClient(app, base_url="http://127.0.0.1")

            response = _post(client, "/start/source", {"repository_url": "https://github.com/example/course"})

            self.assertEqual(response.status_code, 400)
            self.assertIn("Only https://github.com/microsoft/AI-For-Beginners is supported", response.text)
            self.assertEqual(connector.calls, [])
            self.assertFalse((Path(directory) / "workspace").exists())

    def test_source_post_redirects_and_renders_real_commit_and_locator(self) -> None:
        with TemporaryDirectory() as directory:
            connector = FixtureSourceConnector()
            app = create_app(Path(directory), source_connector=connector)
            client = TestClient(app, base_url="http://127.0.0.1")

            response = _post(
                client,
                "/start/source",
                {"repository_url": SUPPORTED_REPOSITORY_URL},
                follow_redirects=False,
            )

            self.assertEqual(response.status_code, 303)
            self.assertEqual(response.headers["location"], "/")
            start = client.get("/")
            self.assertIn(SUPPORTED_REPOSITORY_URL, start.text)
            self.assertIn("0123456789abcdef0123456789abcdef01234567", start.text)
            self.assertIn("lessons/1-Intro/README.md", start.text)
            self.assertIn("Creator-authored Script Package", start.text)
            self.assertIn("import_creator_script", start.text)
            self.assertEqual(len(connector.calls), 1)

    def test_warm_editorial_workspace_surfaces_stage_track_and_next_action(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)

            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn('aria-label="制作阶段"', response.text)
            self.assertIn('aria-current="step"', response.text)
            self.assertIn("下一步", response.text)
            self.assertIn('aria-current="page"', response.text)
            self.assertIn('/static/favicon.svg', response.text)

    def test_guided_workbench_uses_fixed_simplified_chinese_rendered_shell(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)

            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn('<html lang="zh-CN">', response.text)
            self.assertIn("AI 课程工厂", response.text)
            self.assertIn("内容定稿", response.text)
            self.assertIn("待确认脚本", response.text)
            self.assertIn("通过脚本", response.text)
            self.assertNotIn("<h1>Your course, one clear next move.</h1>", response.text)

    def test_review_view_surfaces_current_gate_and_production_facts(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)
            _post(client, "/start/script", {"action": "approve_script"})

            review = client.get("/review")

            self.assertEqual(review.status_code, 200)
            self.assertIn('data-view-kind="review"', review.text)
            self.assertIn('aria-current="page"', review.text)
            self.assertIn('aria-current="step"', review.text)
            self.assertIn('data-stage-state="completed"', review.text)
            self.assertIn('data-stage-state="current"', review.text)
            self.assertIn('data-stage-state="upcoming"', review.text)
            self.assertEqual(review.text.count('class="button button-primary"'), 1)
            self.assertIn("来源提交", review.text)
            self.assertIn("应用费用", review.text)

    def test_review_uses_chinese_workbench_hierarchy_for_planning(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)
            _post(client, "/start/script", {"action": "approve_script"})

            review = client.get("/review")

            self.assertEqual(review.status_code, 200)
            self.assertIn('data-view-kind="review"', review.text)
            self.assertIn("制作与回导", review.text)
            self.assertIn("生成分镜方案", review.text)
            self.assertIn("当前状态", review.text)
            self.assertNotIn("Available actions:", review.text)
            self.assertNotIn("Build production plan", review.text)
            self.assertEqual(review.text.count('class="button button-primary"'), 1)

    def test_workbench_slots_keep_mobile_primary_before_secondary_evidence(self) -> None:
        def assert_slots(markup: str) -> None:
            positions = []
            for slot in ("status", "work", "action", "evidence"):
                marker = f'data-workbench-slot="{slot}"'
                self.assertIn(marker, markup)
                positions.append(markup.index(marker))
            self.assertEqual(positions, sorted(positions))
            self.assertEqual(markup.count('class="button button-primary"'), 1)

        with TemporaryDirectory() as directory:
            client = _client(directory)
            start = client.get("/")
            self.assertEqual(start.status_code, 200)
            assert_slots(start.text)

            _post(client, "/start/script", {"action": "approve_script"})
            _post(client, "/review/action", {"action": "advance_planning"})
            _post(client, "/review/action", {"action": "approve_storyboard"})
            _post(client, "/review/action", {"action": "prepare_handoff_package"})
            review = client.get("/review")
            self.assertEqual(review.status_code, 200)
            assert_slots(review.text)

            css = client.get("/static/style.css")
            self.assertEqual(css.status_code, 200)
            self.assertIn("grid-template-areas", css.text)
            self.assertIn('.workbench-layout > .work-column { grid-area: work; }', css.text)

        with TemporaryDirectory() as directory:
            client = _legacy_client(directory)
            _post(client, "/review/action", {"action": "approve_budget"})
            _post(client, "/review/action", {"action": "produce_offline"})
            final = client.get("/final")
            self.assertEqual(final.status_code, 200)
            assert_slots(final.text)

    def test_final_view_preserves_decision_forms_and_technical_facts(self) -> None:
        with TemporaryDirectory() as directory:
            client = _legacy_client(directory)
            _post(client, "/review/action", {"action": "approve_budget"})
            _post(client, "/review/action", {"action": "produce_offline"})

            final = client.get("/final")

            self.assertEqual(final.status_code, 200)
            self.assertIn('data-view-kind="final"', final.text)
            self.assertIn('aria-current="page"', final.text)
            self.assertIn('aria-current="step"', final.text)
            self.assertIn('controls preload="metadata"', final.text)
            self.assertIn('action="/final/action"', final.text)
            self.assertIn('name="action" value="replace_scene"', final.text)
            self.assertIn('name="action" value="approve_final"', final.text)
            self.assertIn('name="action" value="reject_final"', final.text)
            self.assertIn('name="scene_id" value="scene-2"', final.text)
            self.assertIn('name="decision_context"', final.text)
            self.assertIn("来源提交", final.text)
            self.assertIn("script:episode-1 v1", final.text)
            self.assertIn("视频 v1", final.text)
            self.assertIn("执行次数", final.text)
            self.assertIn("累计费用", final.text)

    def test_final_uses_chinese_review_and_delivery_hierarchy(self) -> None:
        with TemporaryDirectory() as directory:
            client = _legacy_client(directory)
            _post(client, "/review/action", {"action": "approve_budget"})
            _post(client, "/review/action", {"action": "produce_offline"})

            final = client.get("/final")

            self.assertEqual(final.status_code, 200)
            self.assertIn("终审与交付", final.text)
            self.assertIn("通过终审", final.text)
            self.assertIn("生成交付包", final.text)
            self.assertNotIn("Available actions:", final.text)
            self.assertNotIn("Approve or replace", final.text)
            self.assertEqual(final.text.count('class="button button-primary"'), 1)

    def test_start_view_is_server_rendered_and_exposes_three_view_kinds(self) -> None:
        with TemporaryDirectory() as directory:
            client = _client(directory)

            response = client.get("/")

            self.assertEqual(response.status_code, 200)
            self.assertIn("内容与脚本", response.text)
            self.assertIn('data-view-kind="start"', response.text)
            self.assertNotIn("Desktop ImageGen", response.text)
            self.assertIn("应用不调用 Provider API", response.text)
            self.assertNotIn("deterministic Fixture media", response.text)
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
            self.assertIn("退回脚本", start.text)

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
            favicon = client.get("/static/favicon.svg")
            missing = client.get("/media/not-a-file")

            self.assertEqual(css.status_code, 200)
            self.assertEqual(favicon.status_code, 200)
            self.assertEqual(favicon.headers["content-type"], "image/svg+xml")
            self.assertTrue(favicon.text.lstrip().startswith("<svg"))
            self.assertNotRegex(css.text, re.compile(r"(?i)(?:@import|https?://|url\(|<script|src=|href=)"))
            self.assertIn("prefers-reduced-motion", css.text)
            self.assertIn("a:focus-visible", css.text)
            self.assertIn("@media (max-width: 767px)", css.text)
            self.assertIn("overflow-wrap: anywhere", css.text)
            self.assertIn("position: sticky", css.text)
            self.assertIn(".decision-rail { position: static; }", css.text)
            self.assertIn("--accent: #8a622d;", css.text)
            self.assertIn("--muted: #6e6b62;", css.text)
            self.assertEqual(missing.status_code, 404)
            self.assertEqual(missing.text, "Not found.")

    def test_three_view_loop_reaches_video_and_package_downloads(self) -> None:
        with TemporaryDirectory() as directory:
            client = _legacy_client(directory)
            self.assertEqual(_post(client, "/review/action", {"action": "approve_budget"}, follow_redirects=False).status_code, 303)
            produced = _post(client, "/review/action", {"action": "produce_offline"}, follow_redirects=False)

            self.assertEqual(produced.status_code, 303)
            self.assertEqual(produced.headers["location"], "/final")
            final = client.get("/final")
            self.assertEqual(final.status_code, 200)
            self.assertIn("本地 Fixture 证据", final.text)
            self.assertNotIn("生成导入画面", final.text)
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
            self.assertIn("<code>export_package</code>", approved_final.text)
            exported = _post(client, "/final/action", {"action": "export_package"}, follow_redirects=False)
            self.assertEqual(exported.status_code, 303)
            self.assertEqual(client.get("/media/video").status_code, 200)
            self.assertEqual(client.get("/media/subtitle").status_code, 200)
            package = client.get("/media/package")
            self.assertEqual(package.status_code, 200)
            self.assertEqual(package.headers["content-type"], "application/zip")

    def test_final_reject_requires_context_and_blocks_export(self) -> None:
        with TemporaryDirectory() as directory:
            client = _legacy_client(directory)
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
            client = _legacy_client(directory, ffmpeg_executable="/missing/ffmpeg", ffprobe_executable="/missing/ffprobe")
            _post(client, "/review/action", {"action": "approve_budget"})
            failed = _post(client, "/review/action", {"action": "produce_offline"})

            self.assertEqual(failed.status_code, 400)
            self.assertIn("generation_failure", failed.text)
            self.assertIn("生成本地成片", failed.text)
            self.assertNotIn("/missing/ffmpeg", failed.text)
            self.assertNotIn("Traceback", failed.text)

    def test_browser_process_reconstruction_keeps_the_current_gate(self) -> None:
        with TemporaryDirectory() as directory:
            first_client = _client(directory)
            first_app = first_client.app
            _post(first_client, "/start/script", {"action": "approve_script"})
            first_app.state.course_factory.close()

            resumed_client = TestClient(create_app(Path(directory)), base_url="http://127.0.0.1")
            review = resumed_client.get("/review")

            self.assertEqual(review.status_code, 200)
            self.assertIn("planning", review.text)
            self.assertIn("生成分镜方案", review.text)

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
