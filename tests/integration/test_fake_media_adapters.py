"""Offline integration evidence for deterministic Fake media adapters."""

from dataclasses import dataclass, replace
import inspect
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import (
    FilesystemWorkspace,
    WorkspaceFailure,
    WorkspaceFileRecord,
    WorkspaceFileReference,
)
from ai_course_factory.production import (
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VoiceSynthesisTask,
)
from ai_course_factory.production.adapters import (
    DeterministicFakeVisualGenerator,
    DeterministicFakeVoiceGenerator,
)
from ai_course_factory.production.adapters import fake as fake_module


def _tasks():
    request = ArtifactReference("production_request", "episode-1", 1)
    return (
        VisualGenerationTask(
            "task:offline", "attempt:visual:1", request, "scene-1", "9:16", 2.5,
            "show the lesson", "wave", WorkspaceFileReference("task:offline", "media", "scene-1.visual.json"),
        ),
        VoiceSynthesisTask(
            "task:offline", "attempt:voice:1", request, "scene-1", "zh-CN", 2.5,
            "你好，课程开始了。", WorkspaceFileReference("task:offline", "media", "scene-1.voice.json"),
        ),
    )


def _canonical_json(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


class FakeMediaAdapterIntegrationTests(unittest.TestCase):
    def test_filesystem_workspace_produces_explicit_non_playable_visual_and_voice_fixtures(self):
        with TemporaryDirectory() as directory:
            workspace = FilesystemWorkspace(Path(directory) / "workspace")
            self.assertEqual(workspace.prepare("task:offline").task_id, "task:offline")
            visual_task, voice_task = _tasks()
            visual = DeterministicFakeVisualGenerator(workspace).generate(visual_task)
            voice = DeterministicFakeVoiceGenerator(workspace).synthesize(voice_task)

            self.assertIsInstance(visual, MediaGenerationResult)
            self.assertIsInstance(voice, MediaGenerationResult)
            self.assertEqual(
                visual,
                MediaGenerationResult(
                    "attempt:visual:1",
                    "scene-1",
                    "visual",
                    "fake-visual-v1",
                    visual_task.output_reference,
                    "application/x-ai-course-factory-fake-visual",
                    2.5,
                    "SUCCESS",
                ),
            )
            self.assertEqual(
                voice,
                MediaGenerationResult(
                    "attempt:voice:1",
                    "scene-1",
                    "voice",
                    "fake-voice-v1",
                    voice_task.output_reference,
                    "application/x-ai-course-factory-fake-voice",
                    2.5,
                    "SUCCESS",
                ),
            )
            visual_bytes = workspace.read(visual_task.output_reference)
            voice_bytes = workspace.read(voice_task.output_reference)
            self.assertIsInstance(visual_bytes, bytes)
            self.assertIsInstance(voice_bytes, bytes)
            visual_json = json.loads(visual_bytes.decode("utf-8"))
            voice_json = json.loads(voice_bytes.decode("utf-8"))
            expected_visual_json = {
                "format": "ai-course-factory-fake-media",
                "media_type": "application/x-ai-course-factory-fake-visual",
                "operation": "visual",
                "provider": "fake-visual-v1",
                "task": {
                    "aspect_ratio": "9:16",
                    "attempt_id": "attempt:visual:1",
                    "character_action": "wave",
                    "duration_seconds": 2.5,
                    "output_reference": {
                        "area": "media",
                        "name": "scene-1.visual.json",
                        "task_id": "task:offline",
                    },
                    "production_request_reference": {
                        "artifact_type": "production_request",
                        "identity": "episode-1",
                        "version": 1,
                    },
                    "scene_id": "scene-1",
                    "task_id": "task:offline",
                    "visual_intent": "show the lesson",
                },
                "version": 1,
            }
            expected_voice_json = {
                "format": "ai-course-factory-fake-media",
                "media_type": "application/x-ai-course-factory-fake-voice",
                "operation": "voice",
                "provider": "fake-voice-v1",
                "task": {
                    "attempt_id": "attempt:voice:1",
                    "duration_seconds": 2.5,
                    "language": "zh-CN",
                    "narration": "你好，课程开始了。",
                    "output_reference": {
                        "area": "media",
                        "name": "scene-1.voice.json",
                        "task_id": "task:offline",
                    },
                    "production_request_reference": {
                        "artifact_type": "production_request",
                        "identity": "episode-1",
                        "version": 1,
                    },
                    "scene_id": "scene-1",
                    "task_id": "task:offline",
                },
                "version": 1,
            }
            self.assertEqual(set(visual_json), {"format", "media_type", "operation", "provider", "task", "version"})
            self.assertEqual(set(visual_json["task"]), {
                "aspect_ratio", "attempt_id", "character_action", "duration_seconds",
                "output_reference", "production_request_reference", "scene_id", "task_id",
                "visual_intent",
            })
            self.assertEqual(set(voice_json), {"format", "media_type", "operation", "provider", "task", "version"})
            self.assertEqual(set(voice_json["task"]), {
                "attempt_id", "duration_seconds", "language", "narration", "output_reference",
                "production_request_reference", "scene_id", "task_id",
            })
            self.assertEqual(visual_json, expected_visual_json)
            self.assertEqual(voice_json, expected_voice_json)
            self.assertEqual(visual_bytes, _canonical_json(expected_visual_json))
            self.assertEqual(voice_bytes, _canonical_json(expected_voice_json))
            self.assertLessEqual(len(visual_bytes), 32 * 1024)
            self.assertLessEqual(len(voice_bytes), 32 * 1024)
            self.assertNotIn(b"ftyp", visual_bytes)
            self.assertNotIn(b"ftyp", voice_bytes)

    def test_reconstructed_adapters_replay_and_changed_task_conflicts_without_overwrite(self):
        with TemporaryDirectory() as directory:
            root = Path(directory) / "workspace"
            workspace = FilesystemWorkspace(root)
            workspace.prepare("task:offline")
            visual_task, voice_task = _tasks()
            first = DeterministicFakeVisualGenerator(workspace).generate(visual_task)
            original = workspace.read(visual_task.output_reference)
            replay = DeterministicFakeVisualGenerator(FilesystemWorkspace(root)).generate(visual_task)
            self.assertEqual(replay, first)
            changed = replace(visual_task, visual_intent="different lesson")
            conflict = DeterministicFakeVisualGenerator(FilesystemWorkspace(root)).generate(changed)
            self.assertIsInstance(conflict, ProductionMediaFailure)
            self.assertEqual(conflict.code, "MEDIA_OUTPUT_CONFLICT")
            self.assertEqual(FilesystemWorkspace(root).read(visual_task.output_reference), original)

            first_voice = DeterministicFakeVoiceGenerator(workspace).synthesize(voice_task)
            original_voice = workspace.read(voice_task.output_reference)
            replay_voice = DeterministicFakeVoiceGenerator(FilesystemWorkspace(root)).synthesize(voice_task)
            self.assertEqual(replay_voice, first_voice)
            changed_voice = replace(voice_task, narration="改写后的课程旁白。")
            voice_conflict = DeterministicFakeVoiceGenerator(FilesystemWorkspace(root)).synthesize(changed_voice)
            self.assertIsInstance(voice_conflict, ProductionMediaFailure)
            self.assertEqual(voice_conflict.code, "MEDIA_OUTPUT_CONFLICT")
            self.assertEqual(FilesystemWorkspace(root).read(voice_task.output_reference), original_voice)

    def test_invalid_lineage_and_malformed_workspace_success_fail_before_or_at_commit(self):
        class SpyWorkspace:
            def __init__(self, result=None, error=None):
                self.calls = 0
                self.result = result
                self.error = error

            def commit(self, reference, content):
                self.calls += 1
                if self.error is not None:
                    raise self.error
                return self.result if self.result is not None else WorkspaceFileRecord(reference, len(content))

        visual_task, _ = _tasks()
        invalid_workspace = SpyWorkspace()
        invalid = replace(
            visual_task,
            production_request_reference=ArtifactReference("script", "episode-1", 1),
        )
        result = DeterministicFakeVisualGenerator(invalid_workspace).generate(invalid)
        self.assertIsInstance(result, ProductionMediaFailure)
        self.assertEqual(result.kind, "validation")
        self.assertEqual(invalid_workspace.calls, 0)

        malformed_workspace = SpyWorkspace(result=object())
        malformed = DeterministicFakeVisualGenerator(malformed_workspace).generate(visual_task)
        self.assertEqual(malformed.code, "MEDIA_STORAGE_FAILED")

        exception_workspace = SpyWorkspace(error=RuntimeError("secret provider path"))
        failed = DeterministicFakeVisualGenerator(exception_workspace).generate(visual_task)
        self.assertEqual(failed.code, "MEDIA_STORAGE_FAILED")
        self.assertNotIn("secret provider path", failed.message)

    def test_workspace_conflict_is_normalized_and_non_conflict_failure_is_safe(self):
        visual_task, _ = _tasks()

        class ConflictWorkspace:
            def commit(self, reference, content):
                return WorkspaceFailure("WORKSPACE_FILE_CONFLICT", "raw path")

        conflict = DeterministicFakeVisualGenerator(ConflictWorkspace()).generate(visual_task)
        self.assertEqual(conflict, ProductionMediaFailure(
            "execution", "MEDIA_OUTPUT_CONFLICT",
            "media output reference conflicts with existing Fixture bytes",
        ))

        class StorageWorkspace:
            def commit(self, reference, content):
                return WorkspaceFailure("WORKSPACE_STORAGE_ERROR", "raw path")

        failed = DeterministicFakeVisualGenerator(StorageWorkspace()).generate(visual_task)
        self.assertEqual(failed, ProductionMediaFailure(
            "execution", "MEDIA_STORAGE_FAILED", "media output storage failed",
        ))

    def test_bounded_duration_rejects_huge_integer_for_visual_and_voice_without_commit(self):
        visual_task, voice_task = _tasks()
        for task, adapter, method_name in (
            (visual_task, DeterministicFakeVisualGenerator, "generate"),
            (voice_task, DeterministicFakeVoiceGenerator, "synthesize"),
        ):
            class SpyWorkspace:
                def __init__(self):
                    self.calls = 0

                def commit(self, reference, content):
                    self.calls += 1
                    return WorkspaceFileRecord(reference, len(content))

            workspace = SpyWorkspace()
            result = getattr(adapter(workspace), method_name)(replace(task, duration_seconds=10**10000))
            self.assertEqual(result, ProductionMediaFailure(
                "validation", "INVALID_DURATION", "media generation task is invalid",
            ))
            self.assertEqual(workspace.calls, 0)

    def test_exact_task_lineage_and_workspace_shapes_reject_subclasses_without_commit(self):
        visual_task, voice_task = _tasks()

        @dataclass(frozen=True, slots=True)
        class ForgedVisualTask(VisualGenerationTask):
            sdk_response: str = "raw-sdk-response"

        @dataclass(frozen=True, slots=True)
        class ForgedVoiceTask(VoiceSynthesisTask):
            sdk_response: str = "raw-sdk-response"

        @dataclass(frozen=True, slots=True)
        class ForgedArtifactReference(ArtifactReference):
            sdk_raw: str = "raw-sdk-response"

        @dataclass(frozen=True, slots=True)
        class ForgedWorkspaceFileReference(WorkspaceFileReference):
            sdk_raw: str = "raw-sdk-response"

        forged_visual = ForgedVisualTask(
            visual_task.task_id,
            visual_task.attempt_id,
            visual_task.production_request_reference,
            visual_task.scene_id,
            visual_task.aspect_ratio,
            visual_task.duration_seconds,
            visual_task.visual_intent,
            visual_task.character_action,
            visual_task.output_reference,
        )
        forged_voice = ForgedVoiceTask(
            voice_task.task_id,
            voice_task.attempt_id,
            voice_task.production_request_reference,
            voice_task.scene_id,
            voice_task.language,
            voice_task.duration_seconds,
            voice_task.narration,
            voice_task.output_reference,
        )
        cases = (
            (DeterministicFakeVisualGenerator, "generate", forged_visual, "INVALID_VISUAL_TASK"),
            (DeterministicFakeVoiceGenerator, "synthesize", forged_voice, "INVALID_VOICE_TASK"),
            (
                DeterministicFakeVisualGenerator,
                "generate",
                replace(
                    visual_task,
                    production_request_reference=ForgedArtifactReference(
                        "production_request", "episode-1", 1,
                    ),
                ),
                "INVALID_PRODUCTION_REQUEST_REFERENCE",
            ),
            (
                DeterministicFakeVoiceGenerator,
                "synthesize",
                replace(
                    voice_task,
                    production_request_reference=ForgedArtifactReference(
                        "production_request", "episode-1", 1,
                    ),
                ),
                "INVALID_PRODUCTION_REQUEST_REFERENCE",
            ),
            (
                DeterministicFakeVisualGenerator,
                "generate",
                replace(
                    visual_task,
                    output_reference=ForgedWorkspaceFileReference(
                        "task:offline", "media", "scene-1.visual.json",
                    ),
                ),
                "INVALID_OUTPUT_REFERENCE",
            ),
            (
                DeterministicFakeVoiceGenerator,
                "synthesize",
                replace(
                    voice_task,
                    output_reference=ForgedWorkspaceFileReference(
                        "task:offline", "media", "scene-1.voice.json",
                    ),
                ),
                "INVALID_OUTPUT_REFERENCE",
            ),
        )
        for adapter, method_name, task, expected_code in cases:
            class SpyWorkspace:
                def __init__(self):
                    self.calls = 0

                def commit(self, reference, content):
                    self.calls += 1
                    return WorkspaceFileRecord(reference, len(content))

            workspace = SpyWorkspace()
            result = getattr(adapter(workspace), method_name)(task)
            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.kind, "validation")
            self.assertEqual(result.code, expected_code)
            self.assertEqual(workspace.calls, 0)

    def test_fake_adapter_module_exposes_no_forbidden_external_execution_seam(self):
        source = inspect.getsource(fake_module).casefold()
        for forbidden in (
            "http", "requests", "httpx", "urllib", "aiohttp", "sdk", "subprocess",
            "ffmpeg", "providerattempt", "orchestrator",
        ):
            self.assertNotIn(forbidden, source)
        self.assertEqual(
            set(fake_module.__all__),
            {"DeterministicFakeVisualGenerator", "DeterministicFakeVoiceGenerator"},
        )

        class CommitOnlyWorkspace:
            def __init__(self):
                self.calls = []

            def commit(self, reference, content):
                self.calls.append((reference, content))
                return WorkspaceFileRecord(reference, len(content))

            def __getattr__(self, name):
                raise AssertionError(f"unexpected workspace execution seam: {name}")

        visual_task, voice_task = _tasks()
        workspace = CommitOnlyWorkspace()
        self.assertIsInstance(
            DeterministicFakeVisualGenerator(workspace).generate(visual_task),
            MediaGenerationResult,
        )
        self.assertIsInstance(
            DeterministicFakeVoiceGenerator(workspace).synthesize(voice_task),
            MediaGenerationResult,
        )
        self.assertEqual(len(workspace.calls), 2)


if __name__ == "__main__":
    unittest.main()
