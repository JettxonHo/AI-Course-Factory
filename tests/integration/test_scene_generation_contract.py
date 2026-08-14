"""Durable H1 Storyboard approval and replay evidence."""

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from ai_course_factory.application import CourseFactoryApplication
from tests.legacy_v11_fixture import seed_legacy_budget_review
from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL


def _app(directory: str | Path) -> CourseFactoryApplication:
    app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())
    started = app.start_source(SUPPORTED_REPOSITORY_URL)
    if started.status != "success":
        raise AssertionError(started.error_message)
    return app


def _counts(path: Path) -> tuple[int, int, int, int, int]:
    with sqlite3.connect(path / "factory.sqlite3") as connection:
        row = connection.execute(
            "SELECT "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='character'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='storyboard'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='timeline'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='production_request'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='scene_generation_contract')"
        ).fetchone()
    return tuple(row)


class SceneGenerationContractDurableIntegrationTests(unittest.TestCase):
    def test_approval_replay_after_process_restart_reuses_one_exact_contract(self):
        with TemporaryDirectory() as directory:
            app = _app(directory)
            app.submit_script_decision("approve")
            app.advance_planning()
            approved = app.submit_storyboard_decision("approve")
            exact = (
                approved.view.storyboard_reference,
                approved.view.timeline_reference,
                approved.view.production_request_reference,
                approved.view.scene_generation_contract_reference,
            )
            before = _counts(Path(directory))
            self.assertEqual(before, (1, 1, 1, 1, 1))
            app.close()

            resumed = _app(directory)
            replay = resumed.create_or_open()
            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.stage, "handoff_readiness")
            repeated = resumed.submit_storyboard_decision("approve")
            self.assertEqual(repeated.status, "success")
            self.assertEqual(
                (
                    repeated.view.storyboard_reference,
                    repeated.view.timeline_reference,
                    repeated.view.production_request_reference,
                    repeated.view.scene_generation_contract_reference,
                ),
                exact,
            )
            self.assertEqual(_counts(Path(directory)), before)

    def test_legacy_schema_one_budget_checkpoint_reopens_without_contract(self):
        with TemporaryDirectory() as directory:
            app = _app(directory)
            seed_legacy_budget_review(app)
            app.close()

            resumed = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())
            replay = resumed.create_or_open()
            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.stage, "budget_review")
            self.assertEqual(replay.view.pending_action, "approve_budget")
            self.assertIsNone(replay.view.scene_generation_contract_reference)


if __name__ == "__main__":
    unittest.main()
