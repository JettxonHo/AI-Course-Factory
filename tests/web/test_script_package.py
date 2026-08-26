from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.web import create_app

from tests.application.test_script_package import _package
from tests.source_fixture import (
    FixtureSourceConnector,
    SUPPORTED_REPOSITORY_URL,
)


class CreatorScriptPackageWebTests(unittest.TestCase):
    def test_empty_start_post_imports_and_terminal_approve_replay_redirects(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = create_app(data_dir=directory, source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            with TestClient(app) as client:
                started = client.post(
                    "/start/source", data={"repository_url": SUPPORTED_REPOSITORY_URL}, headers={"host": "127.0.0.1", "origin": "http://127.0.0.1"}, follow_redirects=False
                )
                self.assertEqual(started.status_code, 303)
                # The ASGI request owns its facade connection on its worker
                # thread; reopen the persisted task in this test thread and
                # derive locators from the actual ApplicationView.
                with CourseFactoryApplication(
                    Path(directory),
                    source_connector=FixtureSourceConnector(),
                    script_package_directory=package_dir,
                ) as started_application:
                    started_view = started_application.inspect().view
                    self.assertIsNotNone(started_view)
                    self.assertGreaterEqual(len(started_view.source_evidence), 2)
                    locator, locator_2 = started_view.source_evidence[:2]
                package = _package(locator=locator)
                package["script_package_id"] = "computer-vision-episode-02-preprocessing"
                package["claims"] = [
                    {"claim_id": "claim-1", "statement": "<b>Unsafe & claim</b>", "evidence_locators": [locator, locator_2]},
                    {"claim_id": "claim-2", "statement": "Second ordered claim", "evidence_locators": [locator_2]},
                ]
                package["narration_units"] = [
                    {"unit_id": "unit-1", "text": "First ordered narration", "claim_ids": ["claim-1"]},
                    {"unit_id": "unit-2", "text": "Second ordered narration", "claim_ids": ["claim-2"]},
                ]
                package["creator_provenance"] = {
                    "creator_declared_name": "<i>Creator</i>",
                    "creator_role": "teacher & editor",
                    "tool_name": "Tool <v1>",
                }
                Path(package_dir, "creator-script.json").write_text(
                    json.dumps(package), encoding="utf-8"
                )
                imported = client.post(
                    "/start/script-package", content=b"", headers={"host": "127.0.0.1", "origin": "http://127.0.0.1"}, follow_redirects=False
                )
                self.assertEqual(imported.status_code, 303)
                rendered = client.get("/")
                self.assertEqual(rendered.status_code, 200)
                html = rendered.text
                self.assertIn("AI 如何看懂画面 · computer-vision-episode-02-preprocessing", html)
                self.assertNotIn("第 01 集", html)
                self.assertIn("claim-1", html)
                self.assertIn("claim-2", html)
                self.assertLess(html.index("claim-1"), html.index("claim-2"))
                self.assertLess(html.index("Unsafe"), html.index("Second ordered claim"))
                claim_1_start = html.index("claim-1")
                claim_2_start = html.index("claim-2")
                unit_1_start = html.index("unit-1")
                claim_1_locator = html.find(locator, claim_1_start)
                claim_1_locator_2 = html.find(locator_2, claim_1_start)
                claim_2_locator_2 = html.find(locator_2, claim_2_start)
                self.assertGreater(claim_1_locator, claim_1_start)
                self.assertLess(claim_1_locator, claim_2_start)
                self.assertGreater(claim_1_locator_2, claim_1_start)
                self.assertLess(claim_1_locator_2, claim_2_start)
                self.assertGreater(claim_2_locator_2, claim_2_start)
                self.assertLess(claim_2_locator_2, unit_1_start)
                self.assertLess(html.index("unit-1"), html.index("unit-2"))
                self.assertLess(html.index("First ordered narration"), html.index("Second ordered narration"))
                self.assertIn("创作者声明", html)
                self.assertIn("未验证身份", html)
                self.assertNotIn(package_dir, html)
                self.assertIn("&lt;b&gt;Unsafe &amp; claim&lt;/b&gt;", html)
                self.assertIn("&lt;i&gt;Creator&lt;/i&gt;", html)
                self.assertNotIn("<b>Unsafe & claim</b>", html)
                self.assertNotIn("<i>Creator</i>", html)
                approved = client.post(
                    "/start/script", data={"action": "approve_script", "decision_context": ""}, headers={"host": "127.0.0.1", "origin": "http://127.0.0.1"}, follow_redirects=False
                )
                self.assertEqual(approved.status_code, 303)
                replay = client.post(
                    "/start/script", data={"action": "approve_script", "decision_context": ""}, headers={"host": "127.0.0.1", "origin": "http://127.0.0.1"}, follow_redirects=False
                )
                self.assertEqual(replay.status_code, 303)
                self.assertEqual(replay.headers["location"], "/")


if __name__ == "__main__":
    unittest.main()
