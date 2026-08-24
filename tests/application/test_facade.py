from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.knowledge import SourceConnectorFailure

from tests.source_fixture import (
    LESSON_PATH,
    REAL_SHAPED_COMMIT,
    SUPPORTED_REPOSITORY_URL,
    FixtureSourceConnector,
)
from tests.legacy_v11_fixture import seed_legacy_script_review, seed_legacy_budget_review


def _app(directory: str | Path, **kwargs: object) -> CourseFactoryApplication:
    app = CourseFactoryApplication(Path(directory), source_connector=kwargs.pop("source_connector", FixtureSourceConnector()), **kwargs)
    if app.create_or_open().status == "source_required":
        started = app.start_source(SUPPORTED_REPOSITORY_URL)
        if started.status != "success":
            raise AssertionError(started.error_message)
        seed_legacy_script_review(app)
    return app


class CourseFactoryApplicationTests(unittest.TestCase):
    def test_fresh_create_or_open_requires_source_before_initializing_demo(self) -> None:
        with TemporaryDirectory() as directory:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())

            result = app.create_or_open()

            self.assertEqual(result.status, "source_required")
            self.assertIsNone(result.view)
            self.assertFalse((Path(directory) / "workspace").exists())

    def test_source_start_uses_injected_connector_and_persists_real_source_identity(self) -> None:
        with TemporaryDirectory() as directory:
            connector = FixtureSourceConnector()
            app = CourseFactoryApplication(Path(directory), source_connector=connector)

            result = app.start_source(SUPPORTED_REPOSITORY_URL)

            self.assertEqual(result.status, "success")
            self.assertEqual(connector.calls, [(SUPPORTED_REPOSITORY_URL, (LESSON_PATH,))])
            self.assertEqual(result.view.source_commit, REAL_SHAPED_COMMIT)
            self.assertIn(f"@{REAL_SHAPED_COMMIT}:{LESSON_PATH}", result.view.source_locator)
            self.assertFalse(result.view.source_commit in {"a" * 40, "b" * 40})

    def test_invalid_source_url_is_rejected_without_connector_or_state_write(self) -> None:
        with TemporaryDirectory() as directory:
            connector = FixtureSourceConnector()
            app = CourseFactoryApplication(Path(directory), source_connector=connector)

            result = app.start_source("https://github.com/example/other-course")

            self.assertEqual(result.status, "failure")
            self.assertEqual(result.error_code, "UNSUPPORTED_REPOSITORY")
            self.assertEqual(connector.calls, [])
            self.assertEqual(app.create_or_open().status, "source_required")
            self.assertFalse((Path(directory) / "workspace").exists())

    def test_source_connector_failure_is_atomic_and_retryable(self) -> None:
        failure = SourceConnectorFailure("source_access", "TRANSPORT_ERROR", "network unavailable")
        with TemporaryDirectory() as directory:
            connector = FixtureSourceConnector([failure])
            app = CourseFactoryApplication(Path(directory), source_connector=connector)

            failed = app.start_source(SUPPORTED_REPOSITORY_URL)

            self.assertEqual(failed.status, "failure")
            self.assertEqual(failed.error_code, "TRANSPORT_ERROR")
            self.assertEqual(app.create_or_open().status, "source_required")
            self.assertFalse((Path(directory) / "workspace").exists())

            retried = app.start_source(SUPPORTED_REPOSITORY_URL)

            self.assertEqual(retried.status, "success")
            self.assertEqual(len(connector.calls), 2)

    def test_source_success_refresh_and_restart_do_not_repeat_connector_call(self) -> None:
        with TemporaryDirectory() as directory:
            connector = FixtureSourceConnector()
            app = CourseFactoryApplication(Path(directory), source_connector=connector)
            first = app.start_source(SUPPORTED_REPOSITORY_URL)
            self.assertEqual(first.status, "success")

            refreshed = app.create_or_open()
            self.assertEqual(refreshed.status, "success")
            self.assertEqual(len(connector.calls), 1)
            app.close()

            restarted_connector = FixtureSourceConnector()
            resumed = CourseFactoryApplication(Path(directory), source_connector=restarted_connector)
            replay = resumed.create_or_open()

            self.assertEqual(replay.status, "success")
            self.assertEqual(restarted_connector.calls, [])
            self.assertEqual(replay.view.source_commit, REAL_SHAPED_COMMIT)

    def test_create_or_open_starts_the_fixed_demo_at_script_review(self) -> None:
        with TemporaryDirectory() as directory:
            app = _app(directory)

            result = app.create_or_open()

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.task_id, "demo-episode-01")
            self.assertEqual(result.view.stage, "script_review")
            self.assertEqual(result.view.pending_action, "approve_script")
            self.assertTrue(result.view.source_commit)
            self.assertEqual(len(result.view.scenes), 6)
            self.assertEqual(result.view.visual_mode, "fixture")
            self.assertEqual(result.view.prompt_cards, ())

    def test_script_approval_persists_and_moves_to_planning(self) -> None:
        with TemporaryDirectory() as directory:
            app = _app(directory)
            app.create_or_open()

            result = app.submit_script_decision("approve")

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.stage, "planning")
            self.assertEqual(result.view.pending_action, "advance_planning")

            app.close()
            resumed = _app(directory)
            replay = resumed.create_or_open()
            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.stage, "planning")
            self.assertEqual(replay.view.pending_action, "advance_planning")

    def test_script_revision_commits_v2_and_v2_can_be_approved(self) -> None:
        with TemporaryDirectory() as directory:
            app = _app(directory)
            first = app.create_or_open()
            first_reference = first.view.script_reference

            revised = app.submit_script_decision("revise", decision_context="make the opening clearer")

            self.assertEqual(revised.status, "success")
            self.assertEqual(revised.view.script_reference.version, first_reference.version + 1)
            self.assertEqual(revised.view.pending_action, "approve_script")
            self.assertIn("reject_script", revised.view.available_actions)
            self.assertEqual(app.artifacts.get(revised.view.script_reference).prior_reference, first_reference)

            approved = app.submit_script_decision("approve")

            self.assertEqual(approved.status, "success")
            self.assertEqual(approved.view.stage, "planning")

    def test_script_rejection_requires_context_and_also_creates_revision_v2(self) -> None:
        with TemporaryDirectory() as directory:
            app = _app(directory)
            app.create_or_open()

            missing = app.submit_script_decision("reject")
            self.assertEqual(missing.status, "failure")
            self.assertEqual(missing.error_code, "INVALID_DECISION_CONTEXT")

            rejected = app.submit_script_decision("reject", decision_context="replace unsupported claim wording")

            self.assertEqual(rejected.status, "success")
            self.assertEqual(rejected.view.script_reference.version, 2)
            self.assertEqual(rejected.view.pending_action, "approve_script")

    def test_planning_pauses_for_explicit_storyboard_approval_and_exact_script_source(self) -> None:
        with TemporaryDirectory() as directory:
            app = _app(directory)
            app.create_or_open()
            app.submit_script_decision("approve")

            result = app.advance_planning()

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.stage, "planning")
            self.assertEqual(result.view.pending_action, "approve_storyboard")
            self.assertEqual(result.view.source_commit, REAL_SHAPED_COMMIT)
            self.assertIsNone(result.view.budget_maximum_amount_micros)
            self.assertIsNone(result.view.budget_maximum_attempts)

    def test_budget_approval_is_explicit_before_offline_production(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))

            result = app.submit_budget_decision("approve")

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.stage, "production")
            self.assertEqual(result.view.pending_action, "produce_offline")
            self.assertTrue(result.view.budget_approved)

    def test_explicit_zero_amount_fails_closed_without_budget_or_production_side_effect(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))

            result = app.submit_budget_decision("approve", maximum_approved_amount_micros=0)

            self.assertEqual(result.status, "failure")
            self.assertEqual(result.error_code, "INVALID_APPROVED_AMOUNT")
            self.assertEqual(result.view.stage, "budget_review")
            self.assertEqual(result.view.pending_action, "approve_budget")
            self.assertFalse(result.view.budget_approved)
            self.assertEqual(result.view.provider_attempt_count, 0)
            self.assertEqual(result.view.provider_attempt_statuses, ())
            self.assertEqual(result.view.provider_attempt_charged_amount_micros, 0)
            self.assertEqual(app.budget_decisions.get_decision("decision:budget:offline").code, "DECISION_NOT_FOUND")
            self.assertEqual(app.budget_decisions.get_authorization("authorization:offline").code, "AUTHORIZATION_NOT_FOUND")

            production = app.produce_offline()

            self.assertEqual(production.status, "failure")
            self.assertEqual(production.error_code, "BUDGET_APPROVAL_REQUIRED")
            self.assertEqual(production.view.stage, "budget_review")
            self.assertEqual(production.view.provider_attempt_count, 0)

    def test_explicit_zero_attempts_fails_closed_without_budget_or_production_side_effect(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))

            result = app.submit_budget_decision("approve", maximum_attempts=0)

            self.assertEqual(result.status, "failure")
            self.assertEqual(result.error_code, "INVALID_MAXIMUM_ATTEMPTS")
            self.assertEqual(result.view.stage, "budget_review")
            self.assertEqual(result.view.pending_action, "approve_budget")
            self.assertFalse(result.view.budget_approved)
            self.assertEqual(result.view.provider_attempt_count, 0)
            self.assertEqual(result.view.provider_attempt_statuses, ())
            self.assertEqual(result.view.provider_attempt_charged_amount_micros, 0)
            self.assertEqual(app.budget_decisions.get_decision("decision:budget:offline").code, "DECISION_NOT_FOUND")
            self.assertEqual(app.budget_decisions.get_authorization("authorization:offline").code, "AUTHORIZATION_NOT_FOUND")

            production = app.produce_offline()

            self.assertEqual(production.status, "failure")
            self.assertEqual(production.error_code, "BUDGET_APPROVAL_REQUIRED")
            self.assertEqual(production.view.stage, "budget_review")
            self.assertEqual(production.view.provider_attempt_count, 0)

    def test_offline_production_reaches_final_review_with_playable_video(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")

            result = app.produce_offline()

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.stage, "final_review")
            self.assertEqual(result.view.pending_action, "approve_final")
            self.assertIsNotNone(result.view.video_reference)
            self.assertIsNotNone(result.view.subtitle_reference)

    def test_production_replay_and_restart_preserve_exact_delivery_references(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            first = app.produce_offline()
            video_reference = first.view.video_reference
            subtitle_reference = first.view.subtitle_reference

            replay = app.produce_offline()

            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.video_reference, video_reference)
            self.assertEqual(replay.view.subtitle_reference, subtitle_reference)

            app.close()
            resumed = _app(directory)
            continued = resumed.create_or_open()
            self.assertEqual(continued.status, "success")
            self.assertEqual(continued.view.stage, "final_review")
            self.assertEqual(continued.view.video_reference, video_reference)

    def test_final_approval_moves_to_export_without_changing_video(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            produced = app.produce_offline()
            video_reference = produced.view.video_reference

            result = app.submit_final_decision("approve")

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.pending_action, "export_package")
            self.assertEqual(result.view.available_actions, ("export_package",))
            self.assertEqual(result.view.video_reference, video_reference)

    def test_local_scene_replacement_revises_only_selected_scene_and_is_one_shot(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            produced = app.produce_offline()
            before = {scene.scene_id: scene.selected_clip_reference for scene in produced.view.scenes}

            result = app.replace_scene("scene-2")

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.stage, "final_review")
            self.assertTrue(result.view.replacement_done)
            self.assertEqual(result.view.available_actions, ("approve_final", "reject_final"))
            self.assertEqual(result.view.scenes[0].selected_clip_reference, before["scene-1"])
            self.assertNotEqual(result.view.scenes[1].selected_clip_reference, before["scene-2"])

            replay = app.replace_scene("scene-2")
            self.assertEqual(replay.status, "failure")
            self.assertEqual(replay.error_code, "SCENE_REPLACEMENT_UNAVAILABLE")

    def test_replacement_keeps_original_provider_attempt_facts_unchanged(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            produced = app.produce_offline()
            before_count = produced.view.provider_attempt_count
            before_statuses = produced.view.provider_attempt_statuses
            before_charged = produced.view.provider_attempt_charged_amount_micros

            replaced = app.replace_scene("scene-2")

            self.assertEqual(replaced.status, "success")
            self.assertEqual(replaced.view.provider_attempt_count, before_count)
            self.assertEqual(replaced.view.provider_attempt_statuses, before_statuses)
            self.assertEqual(replaced.view.provider_attempt_charged_amount_micros, before_charged)
            self.assertEqual(before_charged, 0)
            self.assertIn("not a Provider attempt", replaced.view.local_replacement_label)

    def test_final_rejection_is_context_bound_and_blocks_export_after_replacement(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            app.produce_offline()
            app.replace_scene("scene-2")

            missing = app.submit_final_decision("reject")
            self.assertEqual(missing.status, "failure")
            self.assertEqual(missing.error_code, "INVALID_DECISION_CONTEXT")

            rejected = app.submit_final_decision("reject", decision_context="replacement still fails quality")

            self.assertEqual(rejected.status, "success")
            self.assertEqual(rejected.view.stage, "rejected")
            self.assertEqual(rejected.view.available_actions, ())
            self.assertEqual(app.export_package().error_code, "FINAL_APPROVAL_REQUIRED")

    def test_failed_local_media_uses_safe_category_and_preserves_production_action(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory, ffmpeg_executable="/missing/ffmpeg", ffprobe_executable="/missing/ffprobe"))
            app.submit_budget_decision("approve")

            result = app.produce_offline()

            self.assertEqual(result.status, "failure")
            self.assertEqual(result.view.failure_category, "generation_failure")
            self.assertEqual(result.view.available_actions, ("produce_offline",))
            self.assertNotIn("/missing", result.error_message or "")
            self.assertNotIn("Traceback", result.error_message or "")

    def test_replacement_survives_restart_with_rebuilt_video(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            app.produce_offline()
            replaced = app.replace_scene("scene-3")
            replacement_video = replaced.view.video_reference

            app.close()
            resumed = _app(directory)
            replay = resumed.create_or_open()

            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.stage, "final_review")
            self.assertTrue(replay.view.replacement_done)
            self.assertEqual(replay.view.video_reference, replacement_video)
            self.assertEqual(resumed.replace_scene("scene-3").error_code, "SCENE_REPLACEMENT_UNAVAILABLE")

    def test_final_approved_video_exports_a_durable_package(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            app.produce_offline()
            app.replace_scene("scene-2")
            app.submit_final_decision("approve")

            result = app.export_package()

            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.stage, "exported")
            self.assertIsNotNone(result.view.package_reference)
            self.assertIsNotNone(result.view.package_output)

    def test_export_package_replays_after_restart_without_rebuilding(self) -> None:
        with TemporaryDirectory() as directory:
            app = seed_legacy_budget_review(_app(directory))
            app.submit_budget_decision("approve")
            app.produce_offline()
            app.submit_final_decision("approve")
            exported = app.export_package()
            package_reference = exported.view.package_reference

            app.close()
            resumed = _app(directory)
            replay = resumed.create_or_open()

            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.stage, "exported")
            self.assertEqual(replay.view.package_reference, package_reference)


if __name__ == "__main__":
    unittest.main()
