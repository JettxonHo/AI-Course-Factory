"""Public contract tests for the additive Task media projection seam."""

import unittest
from dataclasses import fields
from dataclasses import replace

from ai_course_factory.application import (
    TaskDeliveryMediaSelection,
    TaskMediaOperationResult,
    TaskMediaProjectionService,
    TaskMediaProjectionChange,
    TaskMediaRepository,
    TaskMediaRepositoryFailure,
    TaskMediaImpact,
    TaskMediaSnapshot,
    TaskSceneMediaSelection,
)
from ai_course_factory.artifacts import ArtifactCandidate, ArtifactCommitBoundary, ArtifactReference


def _fixture():
    store = ArtifactCommitBoundary()
    request_ref = ArtifactReference("production_request", "episode-1", 1)
    timeline_ref = ArtifactReference("timeline", "episode-1", 1)
    script = ArtifactReference("script", "episode-1", 1)
    character = ArtifactReference("character", "episode-1", 1)
    storyboard = ArtifactReference("storyboard", "episode-1", 1)
    scenes = (
        {"scene_id": "scene-2", "start_seconds": 0.0, "duration_seconds": 1.0, "end_seconds": 1.0,
         "narration": "二", "visual_intent": "二", "character_action": "二", "continuity_notes": ("二",)},
        {"scene_id": "scene-1", "start_seconds": 1.0, "duration_seconds": 1.0, "end_seconds": 2.0,
         "narration": "一", "visual_intent": "一", "character_action": "一", "continuity_notes": ("一",)},
    )
    timeline = {"script_reference": script, "approval_decision_id": "approval-1", "character_reference": character,
                "storyboard_reference": storyboard, "storyboard_decision_id": "storyboard-1",
                "timeline": {"duration_seconds": 2.0, "scenes": tuple({k: s[k] for k in ("scene_id", "start_seconds", "duration_seconds", "end_seconds")} for s in scenes)}}
    store.commit(ArtifactCandidate("timeline", "episode-1", timeline, (), (script, character, storyboard), True, "timeline-1"))
    request = {"script_reference": script, "approval_decision_id": "approval-1", "character_reference": character,
               "storyboard_reference": storyboard, "storyboard_decision_id": "storyboard-1", "timeline_reference": timeline_ref,
               "production_request": {"language": "zh-CN", "aspect_ratio": "9:16", "duration_seconds": 2.0, "scenes": scenes}}
    store.commit(ArtifactCandidate("production_request", "episode-1", request, (), (script, character, storyboard, timeline_ref), True, "request-1"))
    return store, request_ref, timeline_ref, scenes


def _media(store, request_ref, timeline_ref, scenes):
    refs = {}
    for scene in scenes:
        for role in ("scene_clip", "scene_audio"):
            identity = f"media:episode-1:{scene['scene_id']}"
            refs[(scene["scene_id"], role)] = store.commit(ArtifactCandidate(
                role, identity, {"production_request_reference": request_ref, "scene_id": scene["scene_id"],
                "attempt_id": f"attempt-{role}-{scene['scene_id']}", "provider": "fixture", "output_reference": {"task_id": "task-1", "area": "media", "name": f"{role}-{scene['scene_id']}.mp4"},
                "media_type": "video/mp4" if role == "scene_clip" else "audio/mp4", "duration_milliseconds": 1000},
                (), (request_ref,), True, f"{role}-{scene['scene_id']}-1"))
    cues = tuple({"scene_id": s["scene_id"], "start_milliseconds": i * 1000,
                  "end_milliseconds": (i + 1) * 1000, "text": s["narration"]} for i, s in enumerate(scenes))
    refs["subtitle"] = store.commit(ArtifactCandidate("subtitle", "media:episode-1", {
        "production_request_reference": request_ref, "timeline_reference": timeline_ref, "cues": cues}, (),
        (request_ref, timeline_ref), True, "subtitle-1"))
    audio = tuple(refs[(s["scene_id"], "scene_audio")] for s in scenes)
    refs["master_audio"] = store.commit(ArtifactCandidate("master_audio", "media:episode-1", {
        "production_request_reference": request_ref, "timeline_reference": timeline_ref,
        "scene_audio_references": audio, "duration_milliseconds": 2000}, (), (request_ref, timeline_ref, *audio), True, "master-1"))
    clips = tuple(refs[(s["scene_id"], "scene_clip")] for s in scenes)
    refs["video"] = store.commit(ArtifactCandidate("video", "media:episode-1", {
        "production_request_reference": request_ref, "timeline_reference": timeline_ref, "composition_id": "composition-1",
        "scene_ids": tuple(s["scene_id"] for s in scenes), "scene_clip_references": clips, "subtitle_reference": refs["subtitle"],
        "master_audio_reference": refs["master_audio"], "composer": "fixture", "output_reference": {"task_id": "task-1", "area": "media", "name": "video.mp4"},
        "media_type": "video/mp4", "duration_milliseconds": 2000}, (), (request_ref, timeline_ref, *clips, refs["subtitle"], refs["master_audio"]), True, "video-1"))
    source = store.commit(ArtifactCandidate("source_record", "source-1", {"url": "https://example.test"}, (), (), True, "source-1"))
    refs["artifact_manifest"] = store.commit(ArtifactCandidate("artifact_manifest", "media:episode-1", {
        "schema_version": 1, "task_id": "task-1", "source_record_reference": source, "subtitle_reference": refs["subtitle"],
        "video_reference": refs["video"], "final_video_decision_id": "final-1", "files": ()}, (),
        (source, refs["subtitle"], refs["video"]), True, "manifest-1"))
    refs["publish_package"] = store.commit(ArtifactCandidate("publish_package", "media:episode-1", {
        "manifest_reference": refs["artifact_manifest"], "source_record_reference": source, "subtitle_reference": refs["subtitle"],
        "video_reference": refs["video"], "final_video_decision_id": "final-1", "output_reference": {"task_id": "task-1", "area": "exports", "name": "package.zip"}, "format": "zip"}, (),
        (refs["artifact_manifest"], source, refs["subtitle"], refs["video"]), True, "package-1"))
    return refs


class TaskMediaProjectionContractTests(unittest.TestCase):
    def test_public_records_are_frozen_slotted_and_exactly_typed(self):
        scene = TaskSceneMediaSelection(
            "scene-2",
            "scene_clip",
            ArtifactReference("scene_clip", "media:episode:scene-2", 1),
            "current",
        )
        delivery = TaskDeliveryMediaSelection(
            "subtitle",
            ArtifactReference("subtitle", "media:episode", 1),
            "current",
        )
        snapshot = TaskMediaSnapshot(
            "task-1",
            1,
            "production_ready",
            ArtifactReference("production_request", "episode-1", 1),
            ArtifactReference("timeline", "episode-1", 1),
            ("scene-2",),
            (scene,),
            (delivery,),
            "command-1",
        )

        self.assertIs(type(scene), TaskSceneMediaSelection)
        self.assertIs(type(delivery), TaskDeliveryMediaSelection)
        self.assertIs(type(snapshot), TaskMediaSnapshot)
        self.assertTrue(hasattr(scene, "__slots__"))
        self.assertTrue(hasattr(delivery, "__slots__"))
        self.assertTrue(hasattr(snapshot, "__slots__"))
        with self.assertRaises((AttributeError, TypeError)):
            scene.status = "stale"
        self.assertIsNotNone(TaskMediaProjectionService)

    def test_all_public_records_have_literal_fields_and_protocol_is_runtime_checkable(self):
        expected = {
            TaskSceneMediaSelection: ("scene_id", "role", "reference", "status"),
            TaskDeliveryMediaSelection: ("role", "reference", "status"),
            TaskMediaSnapshot: ("task_id", "revision", "lifecycle_state", "production_request_reference", "timeline_reference", "scene_ids", "scene_selections", "delivery_selections", "last_command_id"),
            TaskMediaImpact: ("task_id", "role", "scene_id", "previous_reference", "replacement_reference", "direct", "transitive"),
            TaskMediaOperationResult: ("status", "snapshot", "impact", "error_code", "error_message"),
            TaskMediaRepositoryFailure: ("code", "message"),
            TaskMediaProjectionChange: ("task_id", "command_id", "expected_revision", "snapshot", "impact"),
        }
        for record, names in expected.items():
            self.assertEqual(tuple(field.name for field in fields(record)), names)
            self.assertTrue(record.__dataclass_params__.frozen)
        self.assertTrue(isinstance(__import__("ai_course_factory.application", fromlist=["InMemoryTaskMediaRepository"]).InMemoryTaskMediaRepository(), TaskMediaRepository))

    def test_forged_repository_success_and_failure_outcomes_are_rejected(self):
        store, request, timeline, scenes = _fixture()

        class ForgedRepository:
            def __init__(self, save_result):
                self.save_result = save_result

            def save(self, change):
                return self.save_result

            def get(self, task_id, revision=None):
                return TaskMediaRepositoryFailure("TASK_MEDIA_NOT_FOUND", "task media projection does not exist")

        forged_success = ForgedRepository(TaskMediaOperationResult("success", snapshot=object()))
        created = TaskMediaProjectionService(store, forged_success).create("task-forged-success", "create-1", request)
        self.assertEqual(created.error_code, "TASK_MEDIA_REPOSITORY_FAILED")

        forged_failure = ForgedRepository(TaskMediaOperationResult("failure", error_code="forged", error_message=None))
        created = TaskMediaProjectionService(store, forged_failure).create("task-forged-failure", "create-1", request)
        self.assertEqual(created.error_code, "TASK_MEDIA_REPOSITORY_FAILED")

    def test_timeline_right_side_bool_timing_is_rejected_before_repository_save(self):
        store, request, timeline, scenes = _fixture()
        original = store.get(timeline)
        timeline_payload = dict(original.payload)
        timeline_nested = dict(timeline_payload["timeline"])
        first_scene = dict(timeline_nested["scenes"][0])
        first_scene["duration_seconds"] = True
        timeline_nested["scenes"] = (first_scene, *timeline_nested["scenes"][1:])
        timeline_payload["timeline"] = timeline_nested

        class MutatedTimelineRepository:
            def get(self, reference):
                version = store.get(reference)
                same_timeline = type(reference) is ArtifactReference and (reference.artifact_type, reference.identity, reference.version) == (timeline.artifact_type, timeline.identity, timeline.version)
                return replace(version, payload=timeline_payload) if same_timeline else version

        service = TaskMediaProjectionService(MutatedTimelineRepository())
        result = service.create("task-bad-timeline", "create-1", request)
        self.assertEqual(result.error_code, "TASK_MEDIA_LINEAGE_MISMATCH")
        self.assertEqual(service.inspect("task-bad-timeline").error_code, "TASK_MEDIA_NOT_FOUND")

    def test_invalid_request_and_forged_exact_types_fail_without_repository_mutation(self):
        store, request, timeline, scenes = _fixture()
        service = TaskMediaProjectionService(store)
        invalid = service.create("task-1", "create-1", ArtifactReference("production_request", "missing", 1))
        self.assertEqual(invalid.error_code, "TASK_MEDIA_ARTIFACT_NOT_FOUND")
        forged = ArtifactReference("production_request", "episode-1", True)
        self.assertEqual(service.create("task-2", "create-2", forged).error_code, "INVALID_PRODUCTION_REQUEST_REFERENCE")
        self.assertEqual(service.inspect("task-1").error_code, "TASK_MEDIA_NOT_FOUND")

    def test_invalid_roles_refs_and_direct_repository_transition_fail_closed(self):
        store, request, timeline, scenes = _fixture()
        service = TaskMediaProjectionService(store)
        self.assertEqual(service.create("task-1", "create-1", request).status, "success")
        ref = ArtifactReference("scene_audio", "media:episode-1:scene-1", 1)
        self.assertEqual(service.select_scene("task-1", "bad-role", 1, "scene-1", "scene_video", ref).error_code, "INVALID_MEDIA_ROLE")
        snapshot = service.inspect("task-1").snapshot
        forged = TaskMediaProjectionChange("task-1", "forged", 1, replace(snapshot, revision=2, last_command_id="forged", lifecycle_state="final_review_pending", scene_selections=(TaskSceneMediaSelection("scene-1", "scene_audio", ref, "current"),)), TaskMediaImpact("task-1", "scene_audio", "scene-1", None, ref, (), ()))
        self.assertEqual(service._repository.save(forged).error_code, "TASK_MEDIA_REPOSITORY_FAILED")

    def test_lifecycle_transitions_and_audio_replacement_impact_preserve_unaffected_scene(self):
        store, request, timeline, scenes = _fixture()
        refs = _media(store, request, timeline, scenes)
        service = TaskMediaProjectionService(store)
        current = service.create("task-1", "create-1", request).snapshot
        for command, sid, role in (("audio-2", "scene-2", "scene_audio"), ("clip-2", "scene-2", "scene_clip"), ("audio-1", "scene-1", "scene_audio"), ("clip-1", "scene-1", "scene_clip")):
            result = service.select_scene("task-1", command, current.revision, sid, role, refs[(sid, role)])
            self.assertEqual(result.status, "success"); current = result.snapshot
        for command, role in (("subtitle", "subtitle"), ("master", "master_audio"), ("video", "video")):
            result = service.select_delivery("task-1", command, current.revision, role, refs[role]); self.assertEqual(result.status, "success"); current = result.snapshot
        self.assertEqual(current.lifecycle_state, "final_review_pending")
        replacement = store.commit(ArtifactCandidate("scene_audio", refs[("scene-2", "scene_audio")].identity, {**store.get(refs[("scene-2", "scene_audio")]).payload, "attempt_id": "audio-v2"}, (), (request,), True, "audio-v2", refs[("scene-2", "scene_audio")]))
        preview = service.preview_scene_selection("task-1", "scene-2", "scene_audio", replacement)
        self.assertEqual(tuple(item.role for item in preview.impact.direct), ("master_audio",))
        self.assertEqual(tuple(item.role for item in preview.impact.transitive), ("video",))
        result = service.select_scene("task-1", "replace-audio", current.revision, "scene-2", "scene_audio", replacement)
        self.assertEqual(result.status, "success")
        self.assertEqual(result.snapshot.lifecycle_state, "producing")
        unaffected = {(item.scene_id, item.role): item.status for item in result.snapshot.scene_selections}
        self.assertEqual(unaffected[("scene-1", "scene_audio")], "current")

    def test_subtitle_and_video_replacement_have_exact_direct_impact(self):
        store, request, timeline, scenes = _fixture(); refs = _media(store, request, timeline, scenes)
        service = TaskMediaProjectionService(store); current = service.create("task-1", "create-1", request).snapshot
        for command, sid, role in (("a2", "scene-2", "scene_audio"), ("c2", "scene-2", "scene_clip"), ("a1", "scene-1", "scene_audio"), ("c1", "scene-1", "scene_clip")):
            selected = service.select_scene("task-1", command, current.revision, sid, role, refs[(sid, role)])
            self.assertEqual(selected.status, "success")
            current = selected.snapshot
        for command, role in (("sub", "subtitle"), ("master", "master_audio"), ("video", "video"), ("manifest", "artifact_manifest"), ("package", "publish_package")):
            selected = service.select_delivery("task-1", command, current.revision, role, refs[role])
            self.assertEqual(selected.status, "success")
            current = selected.snapshot
        subtitle_v2 = store.commit(ArtifactCandidate("subtitle", refs["subtitle"].identity, store.get(refs["subtitle"]).payload, (), store.get(refs["subtitle"]).dependencies, True, "subtitle-v2", refs["subtitle"]))
        impact = service.preview_delivery_selection("task-1", "subtitle", subtitle_v2).impact
        self.assertEqual(tuple(item.role for item in impact.direct), ("video", "artifact_manifest", "publish_package"))
        self.assertEqual(impact.transitive, ())
        video_v2 = store.commit(ArtifactCandidate("video", refs["video"].identity, {**store.get(refs["video"]).payload, "composition_id": "composition-2"}, (), store.get(refs["video"]).dependencies, True, "video-v2", refs["video"]))
        impact = service.preview_delivery_selection("task-1", "video", video_v2).impact
        self.assertEqual(tuple(item.role for item in impact.direct), ("artifact_manifest", "publish_package"))
        self.assertEqual(impact.transitive, ())

    def test_exact_replay_conflict_and_revision_conflict(self):
        store, request, timeline, scenes = _fixture(); refs = _media(store, request, timeline, scenes)
        service = TaskMediaProjectionService(store)
        first = service.create("task-1", "create-1", request)
        selected = service.select_scene("task-1", "scene-1", 1, "scene-1", "scene_clip", refs[("scene-1", "scene_clip")])
        replay = service._repository.save(TaskMediaProjectionChange("task-1", "scene-1", 1, selected.snapshot, selected.impact))
        self.assertEqual(replay, selected)
        conflict = service.select_scene("task-1", "other", 1, "scene-1", "scene_clip", refs[("scene-1", "scene_clip")])
        self.assertEqual(conflict.error_code, "TASK_MEDIA_REVISION_CONFLICT")

    def test_non_lexical_scene_order_lifecycle_and_exact_downstream_impact(self):
        store, request, timeline, scenes = _fixture()
        refs = _media(store, request, timeline, scenes)
        service = TaskMediaProjectionService(store)
        created = service.create("task-1", "create-1", request)
        self.assertEqual(created.status, "success")
        self.assertEqual(created.snapshot.scene_ids, ("scene-2", "scene-1"))
        revision = created.snapshot.revision
        selected = service.select_scene("task-1", "audio-2", revision, "scene-2", "scene_audio", refs[("scene-2", "scene_audio")])
        self.assertEqual(selected.status, "success")
        revision = selected.snapshot.revision
        selected = service.select_scene("task-1", "clip-1", revision, "scene-1", "scene_clip", refs[("scene-1", "scene_clip")])
        self.assertEqual(tuple((item.scene_id, item.role) for item in selected.snapshot.scene_selections), (("scene-2", "scene_audio"), ("scene-1", "scene_clip")))
        revision = selected.snapshot.revision
        for command, sid, role in (("audio-1", "scene-1", "scene_audio"), ("clip-2", "scene-2", "scene_clip")):
            selected = service.select_scene("task-1", command, revision, sid, role, refs[(sid, role)])
            self.assertEqual(selected.status, "success"); revision = selected.snapshot.revision
        for command, role in (("subtitle-1", "subtitle"), ("master-1", "master_audio"), ("video-1", "video"), ("manifest-1", "artifact_manifest"), ("package-1", "publish_package")):
            selected = service.select_delivery("task-1", command, revision, role, refs[role])
            self.assertEqual(selected.status, "success"); revision = selected.snapshot.revision
        self.assertEqual(selected.snapshot.lifecycle_state, "packaged")
        replacement = store.commit(ArtifactCandidate("scene_clip", refs[("scene-2", "scene_clip")].identity, {
            **store.get(refs[("scene-2", "scene_clip")]).payload, "attempt_id": "attempt-scene_clip-scene-2-v2"}, (), (request,), True, "scene-2-clip-v2", refs[("scene-2", "scene_clip")]))
        preview = service.preview_scene_selection("task-1", "scene-2", "scene_clip", replacement)
        self.assertEqual(preview.status, "success")
        self.assertEqual(tuple(item.role for item in preview.impact.direct), ("video",))
        self.assertEqual(tuple(item.role for item in preview.impact.transitive), ("artifact_manifest", "publish_package"))
        self.assertEqual(service.inspect("task-1").snapshot.revision, revision)
        updated = service.select_scene("task-1", "replace-1", revision, "scene-2", "scene_clip", replacement)
        self.assertEqual(updated.status, "success")
        self.assertEqual(updated.snapshot.lifecycle_state, "producing")
        self.assertEqual(updated.snapshot.scene_selections[0].status, "current")
        self.assertEqual(updated.snapshot.scene_selections[1].status, "current")


if __name__ == "__main__":
    unittest.main()
