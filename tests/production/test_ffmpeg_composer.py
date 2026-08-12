"""Public behavior tests for the local FFmpeg MediaComposer."""

from dataclasses import fields, is_dataclass, replace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference
from ai_course_factory.production import (
    MediaCompositionResult,
    MediaCompositionScene,
    MediaCompositionTask,
    MediaComposer,
    MediaGenerationResult,
    ProductionMediaFailure,
    FFmpegMediaComposer,
)


class _SpyWorkspace:
    def __init__(self):
        self.read_calls = 0
        self.commit_calls = 0

    def read(self, _reference):
        self.read_calls += 1
        raise AssertionError("invalid task must not read Workspace")

    def commit(self, _reference, _content):
        self.commit_calls += 1
        raise AssertionError("invalid task must not commit Workspace")


class _AlwaysEqual:
    def __eq__(self, _other):
        return True

    def __hash__(self):
        return 0


class _TaskSubclass(MediaCompositionTask):
    pass


class _SceneSubclass(MediaCompositionScene):
    pass


class _MediaResultSubclass(MediaGenerationResult):
    pass


class _ArtifactReferenceSubclass(ArtifactReference):
    pass


class _WorkspaceFileReferenceSubclass(WorkspaceFileReference):
    pass


def _valid_task():
    task_id = "task:composer"
    request = ArtifactReference("production_request", "episode-1", 1)
    timeline = ArtifactReference("timeline", "episode-1", 1)
    visual = MediaGenerationResult(
        "attempt:visual", "scene-1", "visual", "fixture-visual", WorkspaceFileReference(task_id, "media", "scene-1.mp4"),
        "video/mp4", 1.0, "SUCCESS",
    )
    voice = MediaGenerationResult(
        "attempt:voice", "scene-1", "voice", "fixture-voice", WorkspaceFileReference(task_id, "media", "scene-1.m4a"),
        "audio/mp4", 1.0, "SUCCESS",
    )
    scene = MediaCompositionScene("scene-1", 0, 1000, visual, voice, "第一幕。")
    return MediaCompositionTask(
        task_id, "composition-1", request, timeline, (scene,),
        WorkspaceFileReference(task_id, "media", "composition.mp4"),
    )


def _two_scene_task():
    base = _valid_task()
    first = base.scenes[0]
    second_visual = replace(
        first.visual_result,
        attempt_id="attempt:visual:2",
        scene_id="scene-2",
        output_reference=WorkspaceFileReference(base.task_id, "media", "scene-2.mp4"),
        duration_seconds=1.0,
    )
    second_voice = replace(
        first.voice_result,
        attempt_id="attempt:voice:2",
        scene_id="scene-2",
        output_reference=WorkspaceFileReference(base.task_id, "media", "scene-2.m4a"),
        duration_seconds=1.0,
    )
    second = MediaCompositionScene("scene-2", 1000, 2000, second_visual, second_voice, "第二幕。")
    return replace(base, scenes=(first, second))


class FFmpegMediaComposerContractTests(unittest.TestCase):
    def test_public_composition_records_are_frozen_slotted_and_protocol_is_runtime_checkable(self):
        for record in (MediaCompositionScene, MediaCompositionTask, MediaCompositionResult):
            self.assertTrue(is_dataclass(record))
            self.assertTrue(getattr(record, "__dataclass_params__").frozen)
            self.assertTrue(hasattr(record, "__slots__"))
            self.assertEqual(
                tuple(field.name for field in fields(record)),
                {
                    MediaCompositionScene: ("scene_id", "start_milliseconds", "end_milliseconds", "visual_result", "voice_result", "subtitle_text"),
                    MediaCompositionTask: ("task_id", "composition_id", "production_request_reference", "timeline_reference", "scenes", "output_reference"),
                    MediaCompositionResult: ("composition_id", "production_request_reference", "timeline_reference", "scene_ids", "composer", "output_reference", "media_type", "duration_milliseconds", "result_code"),
                }[record],
            )
        self.assertTrue(getattr(MediaComposer, "_is_runtime_protocol", False))

    def test_huge_duration_and_whitespace_alias_fail_before_workspace_or_process(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            ffmpeg = root / "ffmpeg-spy"
            ffprobe = root / "ffprobe-spy"
            marker = root / "called"
            for tool in (ffmpeg, ffprobe):
                tool.write_text(f"#!/bin/sh\nprintf x > '{marker}'\nexit 0\n", encoding="utf-8")
                tool.chmod(0o755)
            base = _valid_task()
            huge = replace(
                base,
                scenes=(replace(base.scenes[0], visual_result=replace(base.scenes[0].visual_result, duration_seconds=10**10000)),),
            )
            alias = replace(
                base,
                production_request_reference=ArtifactReference("production_request", " latest ", 1),
            )
            for task in (huge, alias):
                workspace = _SpyWorkspace()
                result = FFmpegMediaComposer(
                    workspace, ffmpeg_executable=str(ffmpeg), ffprobe_executable=str(ffprobe),
                ).compose(task)
                self.assertIsInstance(result, ProductionMediaFailure)
                self.assertEqual(result.code, "INVALID_COMPOSITION_TASK")
                self.assertEqual(workspace.read_calls, 0)
                self.assertEqual(workspace.commit_calls, 0)
                self.assertFalse(marker.exists())

    def test_public_validation_rejects_non_exact_records_and_malformed_composition_shapes(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "called"
            ffmpeg = root / "ffmpeg-spy"
            ffprobe = root / "ffprobe-spy"
            for tool in (ffmpeg, ffprobe):
                tool.write_text(f"#!/bin/sh\nprintf x > '{marker}'\nexit 0\n", encoding="utf-8")
                tool.chmod(0o755)
            base = _valid_task()
            scene = base.scenes[0]
            two_scene = _two_scene_task()
            first, second = two_scene.scenes
            visual = scene.visual_result
            voice = scene.voice_result
            invalid_tasks = (
                ("scenes-list", replace(base, scenes=[scene])),
                ("task-subclass", _TaskSubclass(base.task_id, base.composition_id, base.production_request_reference, base.timeline_reference, base.scenes, base.output_reference)),
                ("task-always-equal", _AlwaysEqual()),
                ("scene-subclass", replace(base, scenes=(_SceneSubclass(scene.scene_id, scene.start_milliseconds, scene.end_milliseconds, scene.visual_result, scene.voice_result, scene.subtitle_text),))),
                ("scene-always-equal", replace(base, scenes=(_AlwaysEqual(),))),
                ("result-subclass", replace(base, scenes=(replace(scene, visual_result=_MediaResultSubclass(visual.attempt_id, visual.scene_id, visual.operation, visual.provider, visual.output_reference, visual.media_type, visual.duration_seconds, visual.result_code)),))),
                ("result-always-equal", replace(base, scenes=(replace(scene, visual_result=_AlwaysEqual()),))),
                ("artifact-subclass", replace(base, production_request_reference=_ArtifactReferenceSubclass("production_request", "episode-1", 1))),
                ("artifact-always-equal", replace(base, production_request_reference=_AlwaysEqual())),
                ("workspace-ref-subclass", replace(base, output_reference=_WorkspaceFileReferenceSubclass(base.task_id, "media", "composition.mp4"))),
                ("workspace-ref-always-equal", replace(base, output_reference=_AlwaysEqual())),
                ("bool-milliseconds", replace(base, scenes=(replace(scene, start_milliseconds=True),))),
                ("gap-noncontiguous", replace(two_scene, scenes=(first, replace(second, start_milliseconds=1100)))),
                ("duplicate-scene-id", replace(two_scene, scenes=(first, replace(second, scene_id=first.scene_id)))),
                ("control-subtitle", replace(base, scenes=(replace(scene, subtitle_text="bad\x00subtitle"),))),
                ("wrong-operation", replace(base, scenes=(replace(scene, visual_result=replace(visual, operation="voice")),))),
                ("wrong-media-type", replace(base, scenes=(replace(scene, visual_result=replace(visual, media_type="audio/mp4")),))),
                ("wrong-result-code", replace(base, scenes=(replace(scene, visual_result=replace(visual, result_code="FAILED")),))),
                ("duration-mismatch", replace(base, scenes=(replace(scene, visual_result=replace(visual, duration_seconds=0.5)),))),
                ("output-equals-input", replace(base, output_reference=visual.output_reference)),
            )
            for label, task in invalid_tasks:
                workspace = _SpyWorkspace()
                result = FFmpegMediaComposer(
                    workspace, ffmpeg_executable=str(ffmpeg), ffprobe_executable=str(ffprobe),
                ).compose(task)
                self.assertEqual(result, ProductionMediaFailure("validation", "INVALID_COMPOSITION_TASK", "media composition task is invalid"), label)
                self.assertEqual(workspace.read_calls, 0, label)
                self.assertEqual(workspace.commit_calls, 0, label)
                self.assertFalse(marker.exists(), label)


if __name__ == "__main__":
    unittest.main()
