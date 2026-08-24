"""Public application behavior for the Creator Handoff Package action."""

from pathlib import Path
from tempfile import TemporaryDirectory
import base64
import hashlib
import io
import sqlite3
import unittest
import zipfile

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.persistence import WorkspaceFileReference
from ai_course_factory.production import LocalNarrationPreflight, LocalNarrationResult

from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL
from tests.legacy_v11_fixture import seed_legacy_script_review


_PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")


class _FakeNarrationRenderer:
    def __init__(self, workspace):
        self.workspace = workspace
        self.calls = 0

    def preflight(self):
        return LocalNarrationPreflight("fake-commit", "fake-model", "reference audio", "你好。")

    def render(self, task):
        self.calls += 1
        content = f"fake-audio-{task.scene_id}".encode("ascii")
        committed = self.workspace.commit(task.output_reference, content)
        if not hasattr(committed, "reference"):
            raise AssertionError("fake narration was not stored")
        return LocalNarrationResult(task.task_id, task.scene_id, task.output_reference, "audio/mp4", task.duration_seconds, "SUCCESS")


def _ready_app(directory: str, still_dir: Path) -> tuple[CourseFactoryApplication, _FakeNarrationRenderer]:
    app = CourseFactoryApplication(
        Path(directory),
        source_connector=FixtureSourceConnector(),
        visual_import_dir=still_dir,
    )
    renderer = _FakeNarrationRenderer(app.workspace)
    app.local_narration_renderer = renderer
    app.start_source(SUPPORTED_REPOSITORY_URL)
    seed_legacy_script_review(app)
    app.submit_script_decision("approve")
    app.advance_planning()
    approved = app.submit_storyboard_decision("approve")
    if approved.status != "success":
        raise AssertionError(approved.error_message)
    return app, renderer


class HandoffPackageApplicationTests(unittest.TestCase):
    def test_prepare_is_deterministic_idempotent_and_has_no_budget_or_attempt_facts(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG)
            ready, renderer = _ready_app(directory, still_dir)
            first = ready.prepare_handoff_package()
            self.assertEqual(first.status, "success", first.error_message)
            self.assertEqual(first.view.stage, "external_generation_pending")
            self.assertEqual(first.view.available_actions, ("download_handoff_package",))
            self.assertEqual(len(first.view.handoff_narration_references), 6)
            self.assertEqual(first.view.tts_engine, "local-gpt-sovits-v2")
            self.assertEqual(renderer.calls, 6)
            package = ready.read_output("handoff_package")
            self.assertIsNotNone(package)
            package_hash = hashlib.sha256(package.content).hexdigest()
            with zipfile.ZipFile(io.BytesIO(package.content)) as archive:
                self.assertEqual(archive.namelist(), [
                    "generation-guide.md", "scene-generation-contract.json", "timeline.json", "subtitles.srt",
                    *(f"narration/scene-{index}.m4a" for index in range(1, 7)),
                    "provenance.json", "reference-stills/README.md",
                    *(f"reference-stills/scene-{index}.png" for index in range(1, 7)), "handoff-manifest.json",
                ])
                self.assertIn(b"optional visual references", archive.read("reference-stills/README.md"))
            replay = ready.prepare_handoff_package()
            self.assertEqual(replay.status, "success")
            self.assertEqual(renderer.calls, 6)
            self.assertEqual(hashlib.sha256(ready.read_output("handoff_package").content).hexdigest(), package_hash)
            with sqlite3.connect(Path(directory) / "factory.sqlite3") as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='creator_handoff_package'").fetchone()[0], 1)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM budget_decisions").fetchone()[0], 0)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM provider_attempts").fetchone()[0], 0)
            ready.close()
            resumed = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())
            replayed = resumed.create_or_open()
            self.assertEqual(replayed.status, "success")
            self.assertEqual(replayed.view.stage, "external_generation_pending")
            self.assertEqual(hashlib.sha256(resumed.read_output("handoff_package").content).hexdigest(), package_hash)
            resumed.close()


if __name__ == "__main__":
    unittest.main()
