"""Public application behavior for the explicit H1 Storyboard gate."""

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import unittest

from ai_course_factory.application import CourseFactoryApplication

from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL
from tests.legacy_v11_fixture import seed_legacy_script_review


def _app(directory: str | Path) -> CourseFactoryApplication:
    app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())
    started = app.start_source(SUPPORTED_REPOSITORY_URL)
    if started.status != "success":
        raise AssertionError(started.error_message)
    seed_legacy_script_review(app)
    return app


def _artifact_counts(directory: str | Path) -> tuple[int, int, int, int, int]:
    with sqlite3.connect(Path(directory) / "factory.sqlite3") as connection:
        row = connection.execute(
            "SELECT "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='character'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='storyboard'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='timeline'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='production_request'), "
            "(SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='scene_generation_contract')"
        ).fetchone()
    return tuple(row)


class SceneGenerationContractApplicationTests(unittest.TestCase):
    def test_storyboard_approval_is_the_only_transition_to_handoff_readiness(self):
        with TemporaryDirectory() as directory:
            app = _app(directory)
            app.submit_script_decision("approve")

            planning = app.advance_planning()

            self.assertEqual(planning.status, "success")
            self.assertEqual(planning.view.stage, "planning")
            self.assertEqual(planning.view.pending_action, "approve_storyboard")
            self.assertIsNotNone(planning.view.storyboard_reference)
            self.assertIsNone(planning.view.scene_generation_contract_reference)
            self.assertEqual(planning.view.timeline_reference, None)
            self.assertEqual(planning.view.production_request_reference, None)
            self.assertEqual(planning.view.generation_entries, ())
            self.assertEqual(_artifact_counts(directory), (1, 1, 0, 0, 0))

            repeated_advance = app.advance_planning()
            self.assertEqual(repeated_advance.status, "failure")
            self.assertEqual(_artifact_counts(directory), (1, 1, 0, 0, 0))

            approved = app.submit_storyboard_decision("approve")

            self.assertEqual(approved.status, "success")
            self.assertEqual(approved.view.stage, "handoff_readiness")
            self.assertIsNone(approved.view.pending_action)
            self.assertIsNotNone(approved.view.storyboard_reference)
            self.assertIsNotNone(approved.view.scene_generation_contract_reference)
            self.assertEqual(len(approved.view.generation_entries), 6)
            self.assertEqual(
                tuple(entry.expected_filename for entry in approved.view.generation_entries),
                tuple(f"scene-{index}.mp4" for index in range(1, 7)),
            )
            self.assertEqual(approved.view.timeline_reference.artifact_type, "timeline")
            self.assertEqual(approved.view.production_request_reference.artifact_type, "production_request")

    def test_advance_and_approve_are_gate_idempotent_and_reject_preserves_exact_storyboard(self):
        with TemporaryDirectory() as directory:
            app = _app(directory)
            app.submit_script_decision("approve")
            planning = app.advance_planning()
            storyboard_reference = planning.view.storyboard_reference

            repeated_advance = app.advance_planning()
            self.assertEqual(repeated_advance.status, "failure")
            self.assertEqual(repeated_advance.view.stage, "planning")
            self.assertEqual(repeated_advance.view.pending_action, "approve_storyboard")
            self.assertEqual(repeated_advance.view.storyboard_reference, storyboard_reference)

            missing_context = app.submit_storyboard_decision("reject")
            self.assertEqual(missing_context.status, "failure")
            self.assertEqual(missing_context.error_code, "INVALID_DECISION_CONTEXT")

            rejected = app.submit_storyboard_decision("reject", decision_context="Keep the same storyboard for review.")
            self.assertEqual(rejected.status, "success")
            self.assertEqual(rejected.view.stage, "planning")
            self.assertEqual(rejected.view.pending_action, "approve_storyboard")
            self.assertEqual(rejected.view.storyboard_reference, storyboard_reference)
            reject = app.storyboard_decisions.get("decision:storyboard:v1:reject")
            self.assertEqual(reject.action, "reject")
            self.assertEqual(reject.decision_context, "Keep the same storyboard for review.")
            self.assertEqual(_artifact_counts(directory), (1, 1, 0, 0, 0))

            approved = app.submit_storyboard_decision("approve")
            self.assertEqual(approved.status, "success")
            self.assertEqual(approved.view.stage, "handoff_readiness")
            self.assertNotEqual("decision:storyboard:v1:reject", "decision:storyboard:v1:approve")
            final_approve = app.storyboard_decisions.get("decision:storyboard:v1:approve")
            self.assertEqual(final_approve.action, "approve")
            self.assertEqual(final_approve.storyboard_reference, storyboard_reference)
            self.assertEqual(_artifact_counts(directory), (1, 1, 1, 1, 1))

    def test_repeated_storyboard_approval_replays_exact_refs_after_restart(self):
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
            repeated = app.submit_storyboard_decision("approve")
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
            app.close()

            resumed = _app(directory)
            replay = resumed.create_or_open()
            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.stage, "handoff_readiness")
            self.assertIsNone(replay.view.pending_action)
            self.assertEqual(
                (
                    replay.view.storyboard_reference,
                    replay.view.timeline_reference,
                    replay.view.production_request_reference,
                    replay.view.scene_generation_contract_reference,
                ),
                exact,
            )
            replayed_again = resumed.submit_storyboard_decision("approve")
            self.assertEqual(replayed_again.status, "success")
            self.assertEqual(replayed_again.view.scene_generation_contract_reference, exact[-1])

    def test_revised_script_enters_a_new_exact_storyboard_and_contract_lineage(self):
        with TemporaryDirectory() as directory:
            app = _app(directory)
            first = app.create_or_open()
            revised = app.submit_script_decision("revise", decision_context="make the opening clearer")
            self.assertEqual(revised.status, "success")
            self.assertEqual(revised.view.script_reference.version, first.view.script_reference.version + 1)
            self.assertEqual(app.submit_script_decision("approve").status, "success")
            planning = app.advance_planning()
            self.assertEqual(planning.status, "success")
            self.assertEqual(planning.view.pending_action, "approve_storyboard")
            approved = app.submit_storyboard_decision("approve")
            self.assertEqual(approved.status, "success")
            self.assertEqual(approved.view.stage, "handoff_readiness")
            self.assertEqual(approved.view.scene_generation_contract_reference.version, 1)
            contract = app.artifacts.get(approved.view.scene_generation_contract_reference)
            self.assertEqual(contract.payload["script_reference"], approved.view.script_reference)


if __name__ == "__main__":
    unittest.main()
