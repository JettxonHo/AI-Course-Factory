"""Public contract tests for provider-neutral production media seams."""

import unittest
from dataclasses import FrozenInstanceError, fields
import json

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference
from ai_course_factory.production import (
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VisualGenerator,
    VoiceSynthesisTask,
    VoiceGenerator,
)
from ai_course_factory.production.adapters import (
    DeterministicFakeVisualGenerator,
    DeterministicFakeVoiceGenerator,
)
from ai_course_factory.persistence import WorkspaceFileRecord


class MediaInterfaceContractTests(unittest.TestCase):
    def test_visual_generator_protocol_is_runtime_checkable(self):
        class Generator:
            def generate(self, task):
                return task

        self.assertIsInstance(Generator(), VisualGenerator)

    def test_voice_generator_protocol_is_runtime_checkable(self):
        class Generator:
            def synthesize(self, task):
                return task

        self.assertIsInstance(Generator(), VoiceGenerator)

    def test_media_records_are_exact_frozen_slotted_public_shapes(self):
        records = (
            VisualGenerationTask,
            VoiceSynthesisTask,
            MediaGenerationResult,
            ProductionMediaFailure,
        )
        expected_fields = (
            (
                "task_id", "attempt_id", "production_request_reference", "scene_id",
                "aspect_ratio", "duration_seconds", "visual_intent", "character_action",
                "output_reference",
            ),
            (
                "task_id", "attempt_id", "production_request_reference", "scene_id",
                "language", "duration_seconds", "narration", "output_reference",
            ),
            (
                "attempt_id", "scene_id", "operation", "provider", "output_reference",
                "media_type", "duration_seconds", "result_code",
            ),
            ("kind", "code", "message"),
        )
        for record, names in zip(records, expected_fields):
            self.assertTrue(record.__dataclass_params__.frozen)
            self.assertTrue(hasattr(record, "__slots__"))
            self.assertEqual(tuple(field.name for field in fields(record)), names)

        reference = ArtifactReference("production_request", "episode-1", 1)
        output = WorkspaceFileReference("task-1", "media", "visual.json")
        task = VisualGenerationTask(
            "task-1", "attempt-1", reference, "scene-1", "9:16", 2.5,
            "show the lesson", "wave", output,
        )
        with self.assertRaises(FrozenInstanceError):
            task.task_id = "other"

    def test_fake_visual_and_voice_are_explicit_runtime_injected_adapters(self):
        class Workspace:
            def __init__(self):
                self.calls = []

            def commit(self, reference, content):
                self.calls.append((reference, content))
                return WorkspaceFileRecord(reference, len(content))

        workspace = Workspace()
        request = ArtifactReference("production_request", "episode-1", 1)
        visual_reference = WorkspaceFileReference("task-1", "media", "scene-1.visual.json")
        voice_reference = WorkspaceFileReference("task-1", "media", "scene-1.voice.json")
        visual = VisualGenerationTask(
            "task-1", "attempt-1", request, "scene-1", "9:16", 2.5,
            "show the lesson", "wave", visual_reference,
        )
        voice = VoiceSynthesisTask(
            "task-1", "attempt-2", request, "scene-1", "zh-CN", 2.5,
            "你好。", voice_reference,
        )

        visual_adapter = DeterministicFakeVisualGenerator(workspace)
        voice_adapter = DeterministicFakeVoiceGenerator(workspace)
        self.assertIsInstance(visual_adapter, VisualGenerator)
        self.assertIsInstance(voice_adapter, VoiceGenerator)
        visual_result = visual_adapter.generate(visual)
        voice_result = voice_adapter.synthesize(voice)
        self.assertEqual(visual_result.operation, "visual")
        self.assertEqual(visual_result.provider, "fake-visual-v1")
        self.assertEqual(voice_result.operation, "voice")
        self.assertEqual(voice_result.provider, "fake-voice-v1")
        self.assertEqual(len(workspace.calls), 2)
        visual_payload = json.loads(workspace.calls[0][1].decode("utf-8"))
        voice_payload = json.loads(workspace.calls[1][1].decode("utf-8"))
        self.assertEqual(visual_payload["format"], "ai-course-factory-fake-media")
        self.assertEqual(visual_payload["version"], 1)
        self.assertEqual(visual_payload["operation"], "visual")
        self.assertEqual(voice_payload["operation"], "voice")


if __name__ == "__main__":
    unittest.main()
