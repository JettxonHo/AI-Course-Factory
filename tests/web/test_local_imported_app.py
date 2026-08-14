from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unittest

from fastapi.testclient import TestClient

from ai_course_factory.web import create_app
from tests.source_fixture import SUPPORTED_REPOSITORY_URL, FixtureSourceConnector


def _tool(name: str, fallback: str) -> str:
    return shutil.which(name) or fallback


def _write_png(path: Path, colour: str) -> None:
    subprocess.run(
        [
            _tool("ffmpeg", "/opt/homebrew/bin/ffmpeg"),
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={colour}:s=32x32",
            "-frames:v",
            "1",
            str(path),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _post(client: TestClient, path: str, data: dict[str, str]):
    return client.post(
        path,
        data=data,
        headers={"Origin": "http://127.0.0.1"},
        follow_redirects=False,
    )


class LocalImportedWebTests(unittest.TestCase):
    def test_imported_mode_renders_prompt_cards_and_local_processing_label(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            imports = root / "desktop-assets"
            imports.mkdir()
            for index, colour in enumerate(("red", "blue", "green", "yellow", "purple", "orange"), start=1):
                _write_png(imports / f"scene-{index}.png", colour)
            client = TestClient(create_app(root / "data", source_connector=FixtureSourceConnector(), visual_import_dir=imports), base_url="http://127.0.0.1")

            started = _post(client, "/start/source", {"repository_url": SUPPORTED_REPOSITORY_URL})
            self.assertEqual(started.status_code, 303)
            start = client.get("/")
            self.assertEqual(start.status_code, 200)
            self.assertIn("no application Provider API call", start.text)
            self.assertNotIn("deterministic Fixture media", start.text)
            for index in range(1, 7):
                self.assertIn(f"scene-{index}.png", start.text)
            self.assertIn("scene-1", start.text)
            self.assertIn("scene-2", start.text)
            self.assertNotEqual(start.text.find("scene-1"), start.text.find("scene-2"))

            self.assertEqual(_post(client, "/start/script", {"action": "approve_script"}).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "advance_planning"}).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "approve_budget"}).status_code, 303)
            review = client.get("/review")
            self.assertIn("Local imported visual run", review.text)
            self.assertIn("Produce imported visuals", review.text)
            self.assertNotIn("Produce offline Fixture", review.text)
            self.assertIn("outside the application", review.text)
            self.assertIn("no ChatGPT or other Visual Provider API call", review.text)

            self.assertEqual(_post(client, "/review/action", {"action": "produce_offline"}).status_code, 303)
            final = client.get("/final")
            self.assertEqual(final.status_code, 200)
            self.assertIn("Local processing attempts:", final.text)
            self.assertNotIn("<strong>Provider attempts:</strong>", final.text)
            self.assertIn("creator-supplied via ChatGPT Desktop ImageGen", final.text)
            self.assertEqual(final.text.count("Replace scene-2 visual"), 1)
            self.assertNotIn("Replace locally", final.text)
            self.assertIn("local imported visual evidence", final.text)
            self.assertNotIn("local Fixture evidence", final.text)

    def test_imported_preflight_failure_renders_safe_exact_filenames_without_path(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            imports = root / "desktop-assets"
            imports.mkdir()
            client = TestClient(create_app(root / "data", source_connector=FixtureSourceConnector(), visual_import_dir=imports), base_url="http://127.0.0.1")
            self.assertEqual(_post(client, "/start/source", {"repository_url": SUPPORTED_REPOSITORY_URL}).status_code, 303)
            self.assertEqual(_post(client, "/start/script", {"action": "approve_script"}).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "advance_planning"}).status_code, 303)
            self.assertEqual(_post(client, "/review/action", {"action": "approve_budget"}).status_code, 303)

            failed = _post(client, "/review/action", {"action": "produce_offline"})

            self.assertEqual(failed.status_code, 400)
            self.assertIn("scene-1.png", failed.text)
            self.assertIn("scene-6.png", failed.text)
            self.assertNotIn(str(imports), failed.text)
            self.assertNotIn("Traceback", failed.text)


if __name__ == "__main__":
    unittest.main()
