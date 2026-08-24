from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.application import CourseFactoryApplication, parse_creator_script_package
from tests.legacy_v11_fixture import seed_legacy_script_review

from tests.source_fixture import (
    LESSON_PATH,
    REAL_SHAPED_BLOB,
    REAL_SHAPED_COMMIT,
    SUPPORTED_REPOSITORY_URL,
    FixtureSourceConnector,
)


def _package(*, schema: str = "ai-course-factory.creator-script-package", provenance: dict[str, object] | None = None, locator: str | None = None) -> dict[str, object]:
    locator = locator or f"microsoft/AI-For-Beginners@{REAL_SHAPED_COMMIT}:{LESSON_PATH}#L1-L1"
    return {
        "schema": schema,
        "version": 1,
        "script_package_id": "episode-1-creator",
        "source": {
            "repository_url": SUPPORTED_REPOSITORY_URL,
            "repository_identity": "microsoft/AI-For-Beginners",
            "commit_sha": REAL_SHAPED_COMMIT,
            "files": [{"path": LESSON_PATH, "blob_sha": REAL_SHAPED_BLOB}],
        },
        "claims": [{"claim_id": "claim-1", "statement": "AI is practical.", "evidence_locators": [locator]}],
        "narration_units": [{"unit_id": "unit-1", "text": "AI 很实用。", "claim_ids": ["claim-1"]}],
        "creator_provenance": provenance or {"creator_declared_name": "Creator", "creator_role": "teacher", "tool_name": "ChatGPT"},
        "revision_note": None,
    }


class CreatorScriptPackageParserTests(unittest.TestCase):
    def test_exact_discriminator_is_required_without_alias_normalization(self) -> None:
        parsed = parse_creator_script_package(json.dumps(_package(schema="creator-script-package")).encode())
        self.assertEqual(parsed.code, "INVALID_PACKAGE_SCHEMA")

    def test_optional_provenance_omitted_null_and_string_remain_distinct(self) -> None:
        omitted = _package(provenance={"creator_declared_name": "Creator", "creator_role": "teacher", "tool_name": "ChatGPT"})
        explicit_null = _package(provenance={**omitted["creator_provenance"], "session": None})
        string_value = _package(provenance={**omitted["creator_provenance"], "session": "s-1"})
        parsed_omitted = parse_creator_script_package(json.dumps(omitted).encode())
        parsed_null = parse_creator_script_package(json.dumps(explicit_null).encode())
        parsed_string = parse_creator_script_package(json.dumps(string_value).encode())
        self.assertEqual(parsed_omitted.creator_provenance.session_present, False)
        self.assertEqual(parsed_null.creator_provenance.session_present, True)
        self.assertIsNone(parsed_null.creator_provenance.session)
        self.assertEqual(parsed_string.creator_provenance.session, "s-1")
        self.assertNotEqual(parsed_omitted.canonical_value, parsed_null.canonical_value)
        self.assertNotEqual(parsed_null.canonical_value, parsed_string.canonical_value)


class CreatorScriptApplicationStartupTests(unittest.TestCase):
    def test_fresh_source_enters_creator_package_intake_without_legacy_script_or_runtime(self) -> None:
        with TemporaryDirectory() as directory:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector())
            result = app.start_source(SUPPORTED_REPOSITORY_URL)
            self.assertEqual(result.status, "success")
            self.assertEqual(result.view.stage, "script_review")
            self.assertEqual(result.view.pending_action, "import_creator_script")
            self.assertIsNone(result.view.script_reference)
            self.assertEqual(result.view.scenes, ())

    def test_creator_package_import_is_the_only_mutating_script_transition(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            package_path = Path(package_dir) / "creator-script.json"
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            self.assertEqual(started.status, "success")
            package_path.write_text(json.dumps(_package(locator=started.view.source_evidence[0])), encoding="utf-8")
            before = app.inspect()
            importer = getattr(app, "import_creator_script_package")
            imported = importer()
            self.assertEqual(imported.status, "success")
            self.assertEqual(imported.view.script_reference.version, 1)
            self.assertEqual(imported.view.pending_action, "approve_script")
            self.assertNotEqual(before.view.script_reference, imported.view.script_reference)

    def test_legacy_script_cannot_be_migrated_by_creator_package_import(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(
                Path(directory),
                source_connector=FixtureSourceConnector(),
                script_package_directory=package_dir,
            )
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            self.assertEqual(started.status, "success")
            seed_legacy_script_review(app)
            legacy = app.inspect()
            self.assertIsNotNone(legacy.view.script_reference)
            self.assertEqual(legacy.view.pending_action, "approve_script")
            Path(package_dir, "creator-script.json").write_text(
                json.dumps(_package(locator=started.view.source_evidence[0])),
                encoding="utf-8",
            )
            raw_before = app._state_connection.execute(
                "SELECT state_json FROM application_state WHERE singleton=1"
            ).fetchone()[0]
            script_count = app.artifacts._connection.execute(
                "SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='script'"
            ).fetchone()[0]
            decision_count = app.creator_script_decisions.count()

            imported = app.import_creator_script_package()

            self.assertEqual(imported.status, "failure")
            self.assertEqual(imported.error_code, "CREATOR_SCRIPT_LEGACY_SCRIPT_CONFLICT")
            self.assertEqual(imported.view.script_reference, legacy.view.script_reference)
            self.assertEqual(
                app._state_connection.execute(
                    "SELECT state_json FROM application_state WHERE singleton=1"
                ).fetchone()[0],
                raw_before,
            )
            self.assertEqual(
                app.artifacts._connection.execute(
                    "SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='script'"
                ).fetchone()[0],
                script_count,
            )
            self.assertEqual(app.creator_script_decisions.count(), decision_count)
            self.assertEqual(app.advance_planning().error_code, "PLANNING_NOT_READY")

    def test_source_only_import_rejects_downstream_state_without_script(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(
                Path(directory),
                source_connector=FixtureSourceConnector(),
                script_package_directory=package_dir,
            )
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            self.assertEqual(started.status, "success")
            Path(package_dir, "creator-script.json").write_text(
                json.dumps(_package(locator=started.view.source_evidence[0])),
                encoding="utf-8",
            )
            raw = app._state_connection.execute(
                "SELECT state_json FROM application_state WHERE singleton=1"
            ).fetchone()[0]
            malformed = json.loads(raw)
            malformed["stage"] = "planning"
            malformed["pending_action"] = None
            app._state_connection.execute(
                "UPDATE application_state SET state_json = ? WHERE singleton=1",
                (json.dumps(malformed, separators=(",", ":")),),
            )
            raw_before = app._state_connection.execute(
                "SELECT state_json FROM application_state WHERE singleton=1"
            ).fetchone()[0]

            imported = app.import_creator_script_package()

            self.assertEqual(imported.status, "failure")
            self.assertEqual(imported.error_code, "CREATOR_SCRIPT_SOURCE_ONLY_GATE_REQUIRED")
            self.assertEqual(
                app._state_connection.execute(
                    "SELECT state_json FROM application_state WHERE singleton=1"
                ).fetchone()[0],
                raw_before,
            )

    def test_creator_approval_retries_missing_state_transition_after_decision_durable(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            Path(package_dir, "creator-script.json").write_text(json.dumps(_package(locator=started.view.source_evidence[0])), encoding="utf-8")
            self.assertEqual(app.import_creator_script_package().status, "success")
            original_save = app._save_state
            raw_before = app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0]

            def fail_once(_state: object) -> None:
                raise OSError("state unavailable")

            app._save_state = fail_once
            failed = app.submit_script_decision("approve")
            self.assertEqual(failed.status, "failure")
            self.assertEqual(app.creator_script_decisions.count(), 1)
            durable = app.creator_script_decisions.get("decision:creator-script:v1")
            self.assertIsNotNone(durable)
            app._save_state = original_save
            conflict = app.submit_script_decision("reject", decision_context="revise externally")
            self.assertEqual(conflict.status, "failure")
            self.assertEqual(conflict.error_code, "CREATOR_SCRIPT_DECISION_CONFLICT")
            self.assertEqual(app.creator_script_decisions.count(), 1)
            self.assertEqual(
                app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0],
                raw_before,
            )
            retried = app.submit_script_decision("approve")
            self.assertEqual(retried.status, "success")
            self.assertEqual(retried.view.stage, "planning")
            self.assertEqual(retried.view.creator_script_decision_id, "decision:creator-script:v1")
            self.assertEqual(app.creator_script_decisions.count(), 1)

    def test_creator_approve_replay_restart_and_conflicts_are_zero_mutation(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            Path(package_dir, "creator-script.json").write_text(json.dumps(_package(locator=started.view.source_evidence[0])), encoding="utf-8")
            app.import_creator_script_package()
            first = app.submit_script_decision("approve", decision_context="")
            self.assertEqual(first.status, "success")
            raw_before = app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0]
            decision_count = app.creator_script_decisions.count()
            replay = app.submit_script_decision("approve", decision_context="")
            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.stage, "planning")
            self.assertEqual(app.creator_script_decisions.count(), decision_count)
            raw_after = app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0]
            self.assertEqual(raw_after, raw_before)
            conflict_action = app.submit_script_decision("reject", decision_context="change it")
            conflict_context = app.submit_script_decision("approve", decision_context="different")
            self.assertEqual(conflict_action.error_code, "CREATOR_SCRIPT_DECISION_CONFLICT")
            self.assertEqual(conflict_context.error_code, "CREATOR_SCRIPT_DECISION_CONFLICT")
            self.assertEqual(app.creator_script_decisions.count(), decision_count)
            self.assertEqual(app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0], raw_before)
            app.close()
            reopened = CourseFactoryApplication(Path(directory), script_package_directory=None)
            restarted = reopened.submit_script_decision("approve", decision_context="")
            self.assertEqual(restarted.status, "success")
            self.assertEqual(restarted.view.stage, "planning")
            self.assertEqual(reopened.creator_script_decisions.count(), decision_count)

    def test_creator_reject_replay_restart_preserves_version_and_decision(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            Path(package_dir, "creator-script.json").write_text(json.dumps(_package(locator=started.view.source_evidence[0])), encoding="utf-8")
            app.import_creator_script_package()
            first = app.submit_script_decision("reject", decision_context="revise externally")
            self.assertEqual(first.status, "success")
            reference = first.view.script_reference
            decision_id = first.view.creator_script_decision_id
            raw_before = app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0]
            replay = app.submit_script_decision("reject", decision_context="revise externally")
            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.pending_action, "import_creator_script")
            self.assertEqual(replay.view.script_reference, reference)
            self.assertEqual(replay.view.creator_script_decision_id, decision_id)
            self.assertEqual(app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0], raw_before)
            app.close()
            reopened = CourseFactoryApplication(Path(directory))
            restarted = reopened.submit_script_decision("reject", decision_context="revise externally")
            self.assertEqual(restarted.status, "success")
            self.assertEqual(restarted.view.pending_action, "import_creator_script")
            self.assertEqual(restarted.view.script_reference, reference)

    def test_changed_valid_package_reimports_v2_with_prior_lineage_and_new_decision(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            package = _package(locator=started.view.source_evidence[0])
            Path(package_dir, "creator-script.json").write_text(json.dumps(package), encoding="utf-8")
            first = app.import_creator_script_package()
            approved = app.submit_script_decision("approve")
            first_reference = first.view.script_reference
            first_decision = approved.view.creator_script_decision_id
            package["revision_note"] = "external revision"
            Path(package_dir, "creator-script.json").write_text(json.dumps(package, indent=2, sort_keys=True), encoding="utf-8")
            second = app.import_creator_script_package()
            self.assertEqual(second.status, "success")
            self.assertEqual(second.view.script_reference.version, 2)
            self.assertEqual(app.artifacts.get(second.view.script_reference).prior_reference, first_reference)
            self.assertIsNone(second.view.creator_script_decision_id)
            self.assertEqual(app.creator_script_decisions.count(), 1)
            approved_v2 = app.submit_script_decision("approve")
            self.assertEqual(approved_v2.status, "success")
            self.assertNotEqual(approved_v2.view.creator_script_decision_id, first_decision)
            self.assertEqual(app.creator_script_decisions.count(), 2)

    def test_same_canonical_package_reimports_without_new_version_even_with_reordered_json(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            package = _package(locator=started.view.source_evidence[0])
            Path(package_dir, "creator-script.json").write_text(json.dumps(package), encoding="utf-8")
            first = app.import_creator_script_package()
            app.submit_script_decision("approve")
            version_count = app.artifacts._connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='script'").fetchone()[0]
            reordered = {key: package[key] for key in reversed(tuple(package))}
            Path(package_dir, "creator-script.json").write_text(json.dumps(reordered, indent=4), encoding="utf-8")
            replay = app.import_creator_script_package()
            self.assertEqual(replay.status, "success")
            self.assertEqual(replay.view.script_reference, first.view.script_reference)
            self.assertEqual(app.artifacts._connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='script'").fetchone()[0], version_count)

    def test_different_package_id_and_invalid_package_preserve_selected_script_and_state(self) -> None:
        with TemporaryDirectory() as directory, TemporaryDirectory() as package_dir:
            app = CourseFactoryApplication(Path(directory), source_connector=FixtureSourceConnector(), script_package_directory=package_dir)
            started = app.start_source(SUPPORTED_REPOSITORY_URL)
            package = _package(locator=started.view.source_evidence[0])
            Path(package_dir, "creator-script.json").write_text(json.dumps(package), encoding="utf-8")
            first = app.import_creator_script_package()
            before = app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0]
            package["script_package_id"] = "other-id"
            Path(package_dir, "creator-script.json").write_text(json.dumps(package), encoding="utf-8")
            conflict = app.import_creator_script_package()
            self.assertEqual(conflict.error_code, "SCRIPT_PACKAGE_ID_CONFLICT")
            self.assertEqual(app.inspect().view.script_reference, first.view.script_reference)
            self.assertEqual(app._state_connection.execute("SELECT state_json FROM application_state WHERE singleton=1").fetchone()[0], before)
            Path(package_dir, "creator-script.json").write_text(json.dumps({"schema": "wrong"}), encoding="utf-8")
            invalid = app.import_creator_script_package()
            self.assertEqual(invalid.error_code, "INVALID_PACKAGE_SCHEMA")
            self.assertEqual(app.inspect().view.script_reference, first.view.script_reference)


if __name__ == "__main__":
    unittest.main()
