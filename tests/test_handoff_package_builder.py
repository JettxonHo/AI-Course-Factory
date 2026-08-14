"""Public behavior tests for the Creator Handoff Package builder."""

from dataclasses import fields
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.artifacts import ArtifactReference, ArtifactVersion
from ai_course_factory.persistence import WorkspaceFileReference, WorkspaceFailure
from ai_course_factory.packaging import CreatorHandoffPackageBuilder, HandoffPackageFailure, HandoffPackageResult
from ai_course_factory.production import LocalNarrationPreflight, LocalNarrationRenderer, LocalNarrationResult, LocalNarrationTask, ProductionMediaFailure

from tests.application.test_handoff_package import _PNG, _ready_app


class _PartialFailureRenderer:
    def __init__(self, workspace, *, model_identifier="fake-model"):
        self.workspace = workspace
        self.model_identifier = model_identifier
        self.fail_scene = "scene-2"
        self.calls = []

    def preflight(self):
        return LocalNarrationPreflight("fake-commit", self.model_identifier, "reference audio", "你好。")

    def render(self, task):
        self.calls.append(task.scene_id)
        if self.fail_scene == task.scene_id:
            return ProductionMediaFailure("execution", "FAKE_RENDER_FAILED", "controlled narration failure")
        content = f"accepted-audio-{task.scene_id}".encode("ascii")
        stored = self.workspace.commit(task.output_reference, content)
        if not hasattr(stored, "reference"):
            raise AssertionError("fake narration was not stored")
        return LocalNarrationResult(task.task_id, task.scene_id, task.output_reference, "audio/mp4", task.duration_seconds, "SUCCESS")


class _ReplayLookupFailure:
    def __init__(self, delegate, *, wrong_reference=False):
        self.delegate = delegate
        self.commit_calls = 0
        self.wrong_reference = wrong_reference

    def get(self, reference):
        if reference.artifact_type == "creator_handoff_package":
            if self.wrong_reference:
                wrong = ArtifactReference("creator_handoff_package", "handoff:wrong", 1)
                return ArtifactVersion(wrong, {}, (), (), "malformed-replay")
            raise RuntimeError("closed artifact repository")
        return self.delegate.get(reference)

    def commit(self, candidate):
        self.commit_calls += 1
        return self.delegate.commit(candidate)


class _RejectedDecisionRepository:
    def get(self, decision_id):
        return object()


class CreatorHandoffPackageBuilderTests(unittest.TestCase):
    def test_handoff_public_values_are_frozen_slotted_and_builder_is_public(self):
        self.assertTrue(hasattr(LocalNarrationRenderer, "render"))
        self.assertTrue(hasattr(LocalNarrationRenderer, "preflight"))
        for record_type in (LocalNarrationTask, LocalNarrationResult, LocalNarrationPreflight, HandoffPackageFailure, HandoffPackageResult):
            self.assertTrue(record_type.__dataclass_params__.frozen)
            self.assertTrue(hasattr(record_type, "__slots__"))
        self.assertTrue(callable(CreatorHandoffPackageBuilder))
        self.assertGreater(len(fields(HandoffPackageResult)), 0)

    def test_partial_render_failure_retries_with_exact_staged_bytes_and_changed_binding_conflicts(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG)
            app, _unused_renderer = _ready_app(directory, still_dir)
            renderer = _PartialFailureRenderer(app.workspace)
            app.local_narration_renderer = renderer
            first = app.prepare_handoff_package()
            self.assertEqual(first.status, "failure")
            self.assertEqual(first.error_code, "FAKE_RENDER_FAILED")
            self.assertEqual(renderer.calls, ["scene-1", "scene-2"])
            task_id = first.view.task_id
            scene_one = WorkspaceFileReference(task_id, "media", "handoff-narration-scene-1.m4a")
            accepted_before_retry = app.workspace.read(scene_one)
            self.assertEqual(accepted_before_retry, b"accepted-audio-scene-1")

            renderer.fail_scene = None
            second = app.prepare_handoff_package()
            self.assertEqual(second.status, "success", second.error_message)
            self.assertEqual(renderer.calls, ["scene-1", "scene-2", "scene-2", "scene-3", "scene-4", "scene-5", "scene-6"])
            self.assertEqual(app.workspace.read(scene_one), accepted_before_retry)
            with sqlite3.connect(Path(directory) / "factory.sqlite3") as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='creator_handoff_package'").fetchone()[0], 1)

            app.close()

            with TemporaryDirectory() as changed_directory:
                changed_app, _unused_changed_renderer = _ready_app(changed_directory, still_dir)
                first_changed_renderer = _PartialFailureRenderer(changed_app.workspace)
                changed_app.local_narration_renderer = first_changed_renderer
                changed_first = changed_app.prepare_handoff_package()
                self.assertEqual(changed_first.status, "failure")
                changed_renderer = _PartialFailureRenderer(changed_app.workspace, model_identifier="changed-model")
                changed_app.local_narration_renderer = changed_renderer
                changed = changed_app.prepare_handoff_package()
                self.assertEqual(changed.status, "failure")
                self.assertEqual(changed.error_code, "HANDOFF_PACKAGE_CONFLICT")
                self.assertEqual(changed_renderer.calls, [])
                self.assertIsInstance(
                    changed_app.workspace.read(WorkspaceFileReference(changed_first.view.task_id, "exports", "creator-handoff-package.zip")),
                    WorkspaceFailure,
                )
                with sqlite3.connect(Path(changed_directory) / "factory.sqlite3") as connection:
                    self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='creator_handoff_package'").fetchone()[0], 0)
                changed_app.close()

    def test_invalid_reference_still_fails_before_renderer_workspace_or_artifact_side_effect(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG if index != 4 else b"not-an-image")
            app, renderer = _ready_app(directory, still_dir)
            result = app.prepare_handoff_package()
            self.assertEqual(result.status, "failure")
            self.assertEqual(result.error_code, "HANDOFF_STILLS_PREFLIGHT_FAILED")
            self.assertEqual(renderer.calls, 0)
            self.assertIsInstance(
                app.workspace.read(WorkspaceFileReference(result.view.task_id, "exports", "creator-handoff-package.zip")),
                WorkspaceFailure,
            )
            self.assertIsInstance(
                app.workspace.read(WorkspaceFileReference(result.view.task_id, "provider-records", "handoff-narration-scene-1.binding.json")),
                WorkspaceFailure,
            )
            with sqlite3.connect(Path(directory) / "factory.sqlite3") as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='creator_handoff_package'").fetchone()[0], 0)
            app.close()

    def test_artifact_replay_lookup_failure_stops_before_renderer_or_workspace_mutation(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG)
            app, renderer = _ready_app(directory, still_dir)
            failing = _ReplayLookupFailure(app.artifacts)
            app.artifacts = failing
            result = app.prepare_handoff_package()
            self.assertEqual(result.status, "failure")
            self.assertEqual(result.error_code, "HANDOFF_ARTIFACT_STORAGE_FAILED")
            self.assertEqual(renderer.calls, 0)
            self.assertEqual(failing.commit_calls, 0)
            self.assertIsInstance(
                app.workspace.read(WorkspaceFileReference(result.view.task_id, "exports", "creator-handoff-package.zip")),
                WorkspaceFailure,
            )
            app.close()

    def test_wrong_artifact_replay_reference_fails_closed_before_renderer_or_workspace_mutation(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG)
            app, renderer = _ready_app(directory, still_dir)
            malformed = _ReplayLookupFailure(app.artifacts, wrong_reference=True)
            app.artifacts = malformed
            result = app.prepare_handoff_package()
            self.assertEqual(result.status, "failure")
            self.assertEqual(result.error_code, "HANDOFF_ARTIFACT_STORAGE_FAILED")
            self.assertEqual(renderer.calls, 0)
            self.assertEqual(malformed.commit_calls, 0)
            self.assertIsInstance(
                app.workspace.read(WorkspaceFileReference(result.view.task_id, "exports", "creator-handoff-package.zip")),
                WorkspaceFailure,
            )
            app.close()

    def test_existing_replay_requires_approved_decision_before_reusing_package(self):
        with TemporaryDirectory() as directory, TemporaryDirectory() as stills:
            still_dir = Path(stills)
            for index in range(1, 7):
                (still_dir / f"scene-{index}.png").write_bytes(_PNG)
            app, renderer = _ready_app(directory, still_dir)
            first = app.prepare_handoff_package()
            self.assertEqual(first.status, "success", first.error_message)
            state = app._load_state()
            package_before = app.read_output("handoff_package").content
            builder = CreatorHandoffPackageBuilder(app.artifacts, _RejectedDecisionRepository(), app.workspace, renderer)
            result = builder.build(
                state.task_id,
                state.refs["source"],
                state.refs["script"],
                state.refs["character"],
                state.refs["storyboard"],
                state.refs["timeline"],
                state.refs["production_request"],
                state.refs["scene_generation_contract"],
                state.decision_ids["storyboard"],
                reference_stills_directory=still_dir,
                output_reference=state.handoff_package_output,
            )
            self.assertEqual(result.code, "STORYBOARD_APPROVAL_REQUIRED")
            self.assertEqual(renderer.calls, 6)
            self.assertEqual(app.read_output("handoff_package").content, package_before)
            with sqlite3.connect(Path(directory) / "factory.sqlite3") as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type='creator_handoff_package'").fetchone()[0], 1)
            app.close()


if __name__ == "__main__":
    unittest.main()
