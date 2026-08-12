"""Public behavior tests for product-path production composition."""

import unittest
from dataclasses import fields, replace
from datetime import datetime, timezone

from ai_course_factory.artifacts import ArtifactCandidate, ArtifactCommitBoundary, ArtifactCommitError, ArtifactNotFoundError, ArtifactReference
from ai_course_factory.persistence import WorkspaceFileReference
from ai_course_factory.production import (
    MediaCompositionResult,
    MediaCompositionScene,
    MediaCompositionTask,
    MediaGenerationResult,
    ProductionCompositionResult,
    ProductionMediaFailure,
    ProductionOrchestrator,
    ProviderAttemptRecord,
)

from tests.production.test_orchestrator import _authorization_and_request, _record, _reservation


class _Ledger:
    def __init__(self, records):
        self.records = records
        self.get_calls = []

    def get(self, attempt_id):
        self.get_calls.append(attempt_id)
        return self.records[attempt_id]


class _Composer:
    def __init__(self):
        self.calls = []

    def compose(self, task):
        self.calls.append(task)
        return MediaCompositionResult(
            task.composition_id,
            task.production_request_reference,
            task.timeline_reference,
            tuple(scene.scene_id for scene in task.scenes),
            "test-composer",
            task.output_reference,
            "video/mp4",
            task.scenes[-1].end_milliseconds,
            "SUCCESS",
        )


class _AlwaysEqual:
    def __eq__(self, _other):
        return True

    def __hash__(self):
        return 0


class _EvilString(str):
    def __eq__(self, _other):
        return True

    def __hash__(self):
        return str.__hash__(self)


class _RepositorySpy:
    def __init__(self, repository, *, fail_video=False):
        self.repository = repository
        self.fail_video = fail_video
        self.commit_calls = []
        self.get_calls = []

    def commit(self, candidate):
        self.commit_calls.append(candidate)
        if self.fail_video and candidate.artifact_type == "video":
            raise ArtifactCommitError("forced video commit failure")
        return self.repository.commit(candidate)

    def get(self, reference):
        self.get_calls.append(reference)
        return self.repository.get(reference)


class _FailingReadRepository:
    def commit(self, _candidate):
        raise AssertionError("read failure must stop before commit")

    def get(self, _reference):
        raise ArtifactCommitError("forced read failure")


class _ForgedCommitRepository:
    def __init__(self, repository):
        self.repository = repository

    def commit(self, candidate):
        return self.repository.commit(candidate)

    def get(self, reference):
        version = self.repository.get(reference)
        if reference.artifact_type == "scene_clip":
            return replace(version, payload={"forged": True})
        return version


class _MutableSnapshotRepository:
    def __init__(self, repository):
        self.repository = repository

    def commit(self, candidate):
        return self.repository.commit(candidate)

    def get(self, reference):
        version = self.repository.get(reference)
        if reference.artifact_type == "scene_clip":
            return replace(version, payload=dict(version.payload))
        return version


class _ForgedComposer:
    def __init__(self):
        self.calls = 0

    def compose(self, task):
        self.calls += 1
        return MediaCompositionResult(
            task.composition_id, task.production_request_reference, task.timeline_reference,
            ("forged",), "test-composer", task.output_reference, "video/mp4",
            task.scenes[-1].end_milliseconds, "SUCCESS",
        )


def _composition_case(task_id="task:composition"):
    request_reference, request, authorization = _authorization_and_request(task_id=task_id)
    timeline_reference = request.payload["timeline_reference"]
    records = {}
    scenes = []
    for index, (scene_id, narration, start, end) in enumerate(
        (("scene-1", "你好。", 0, 30_000), ("scene-2", "再见。", 30_000, 60_000)),
        start=1,
    ):
        visual_reservation = _reservation(authorization, attempt_id=f"attempt:visual-{index}", scene_id=scene_id)
        voice_reservation = _reservation(
            authorization, attempt_id=f"attempt:voice-{index}", operation="voice",
            provider="fake-voice-v1", scene_id=scene_id,
        )
        visual_output = WorkspaceFileReference(authorization.task_id, "media", f"scene-{index}.mp4")
        voice_output = WorkspaceFileReference(authorization.task_id, "media", f"scene-{index}.m4a")
        visual_result = MediaGenerationResult(
            visual_reservation.attempt_id, scene_id, "visual", visual_reservation.provider,
            visual_output, "video/mp4", 30.0, "SUCCESS",
        )
        voice_result = MediaGenerationResult(
            voice_reservation.attempt_id, scene_id, "voice", voice_reservation.provider,
            voice_output, "audio/mp4", 30.0, "SUCCESS",
        )
        completed = datetime(2026, 8, 12, 0, 0, 1, tzinfo=timezone.utc)
        records[visual_reservation.attempt_id] = _record(
            request_reference, visual_reservation, status="succeeded",
            output_references=(visual_output,), result_code="SUCCESS", charged=0, completed_at=completed,
        )
        records[voice_reservation.attempt_id] = _record(
            request_reference, voice_reservation, status="succeeded",
            output_references=(voice_output,), result_code="SUCCESS", charged=0, completed_at=completed,
        )
        scenes.append(MediaCompositionScene(scene_id, start, end, visual_result, voice_result, narration))
    task = MediaCompositionTask(
        authorization.task_id, "composition:episode-1", request_reference, timeline_reference,
        tuple(scenes), WorkspaceFileReference(authorization.task_id, "media", "composition.mp4"),
    )
    repository = ArtifactCommitBoundary()
    repository.commit(ArtifactCandidate(
        "production_request", request.reference.identity, request.payload,
        request.provenance, request.dependencies, True, request.commit_id,
    ))
    repository.commit(ArtifactCandidate(
        "timeline", timeline_reference.identity, {}, (), (), True, "timeline-commit-1",
    ))
    return request_reference, request, task, _Ledger(records), _Composer(), repository


class ProductionCompositionOrchestratorTests(unittest.TestCase):
    def test_composition_result_is_frozen_slotted_and_has_exact_public_shape(self):
        self.assertTrue(ProductionCompositionResult.__dataclass_params__.frozen)
        self.assertTrue(hasattr(ProductionCompositionResult, "__slots__"))
        self.assertEqual(
            tuple(field.name for field in fields(ProductionCompositionResult)),
            (
                "task_id",
                "composition_id",
                "production_request_reference",
                "timeline_reference",
                "scene_clip_references",
                "scene_audio_references",
                "subtitle_reference",
                "master_audio_reference",
                "video_reference",
                "output_reference",
                "result_code",
            ),
        )

    def test_compose_commits_ordered_media_artifacts_and_returns_exact_references(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        result = ProductionOrchestrator(
            ledger,
            object(),
            object(),
            clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer,
            artifact_repository=repository,
        ).compose(
            request_reference,
            request,
            task,
            artifact_identity="media:episode-1",
            composition_commit_id="composition-commit-1",
        )
        self.assertIsInstance(result, ProductionCompositionResult)
        self.assertEqual(len(result.scene_clip_references), 2)
        self.assertEqual(len(result.scene_audio_references), 2)
        self.assertEqual(result.result_code, "SUCCESS")
        self.assertEqual(len(composer.calls), 1)
        self.assertEqual(len(ledger.get_calls), 4)
        for reference in (*result.scene_clip_references, *result.scene_audio_references):
            version = repository.get(reference)
            self.assertEqual(version.dependencies, (request_reference,))
            self.assertEqual(version.provenance[0]["production_request_reference"], request_reference)
            self.assertEqual(version.payload["output_reference"]["task_id"], task.task_id)
            self.assertEqual(version.payload["output_reference"]["area"], "media")
        subtitle = repository.get(result.subtitle_reference)
        self.assertEqual(subtitle.dependencies, (request_reference, task.timeline_reference))
        self.assertEqual(
            tuple((cue["scene_id"], cue["start_milliseconds"], cue["end_milliseconds"], cue["text"])
                  for cue in subtitle.payload["cues"]),
            (("scene-1", 0, 30_000, "你好。"), ("scene-2", 30_000, 60_000, "再见。")),
        )
        master = repository.get(result.master_audio_reference)
        self.assertEqual(master.dependencies, (request_reference, task.timeline_reference, *result.scene_audio_references))
        self.assertEqual(tuple(master.payload["scene_audio_references"]), result.scene_audio_references)
        video = repository.get(result.video_reference)
        self.assertEqual(video.dependencies, (request_reference, task.timeline_reference, *result.scene_clip_references, result.subtitle_reference, result.master_audio_reference))
        self.assertEqual(tuple(video.payload["scene_clip_references"]), result.scene_clip_references)
        self.assertEqual(video.payload["output_reference"], {"task_id": task.task_id, "area": "media", "name": "composition.mp4"})

    def test_invalid_context_and_attempt_state_fail_before_commit_or_composer(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        repository = _RepositorySpy(repository)
        invalid_task = replace(task, scenes=())
        result = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=repository,
        ).compose(request_reference, request, invalid_task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertEqual(result.code, "INVALID_COMPOSITION_CONTEXT")
        self.assertEqual(ledger.get_calls, [])
        self.assertEqual(repository.commit_calls, [])
        self.assertEqual(composer.calls, [])

    def test_precommit_exact_types_and_terminal_attempt_states_fail_closed(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        invalid_task = replace(
            task,
            scenes=(replace(task.scenes[0], start_milliseconds=True), task.scenes[1]),
        )
        spy = _RepositorySpy(repository)
        invalid = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=spy,
        ).compose(request_reference, request, invalid_task, artifact_identity="media:bool", composition_commit_id="composition-commit-bool")
        self.assertEqual(invalid, ProductionMediaFailure("validation", "INVALID_COMPOSITION_CONTEXT", "media composition context is invalid"))
        self.assertEqual(ledger.get_calls, [])
        self.assertEqual(spy.commit_calls, [])
        self.assertEqual(composer.calls, [])

        terminal_cases = (
            ("started", lambda record: replace(record, status="started", result_code=None, charged_amount_micros=None)),
            ("failed", lambda record: replace(record, status="failed", result_code="FAILED", charged_amount_micros=0)),
            ("charged", lambda record: replace(record, charged_amount_micros=1)),
            ("foreign", lambda record: replace(
                record,
                output_references=(WorkspaceFileReference("task:foreign", "media", "foreign.mp4"),),
            )),
            ("always-equal", lambda _record: _AlwaysEqual()),
        )
        for label, update in terminal_cases:
            request_reference, request, task, ledger, composer, repository = _composition_case(task_id=f"task:{label}")
            attempt_id = task.scenes[0].visual_result.attempt_id
            ledger.records[attempt_id] = update(ledger.records[attempt_id])
            spy = _RepositorySpy(repository)
            result = ProductionOrchestrator(
                ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
                media_composer=composer, artifact_repository=spy,
            ).compose(request_reference, request, task, artifact_identity=f"media:{label}", composition_commit_id=f"composition-commit-{label}")
            self.assertEqual(result, ProductionMediaFailure("execution", "ATTEMPT_STORAGE_FAILED", "provider attempt persistence failed"), label)
            self.assertEqual(spy.commit_calls, [], label)
            self.assertEqual(composer.calls, [], label)

        request_reference, request, task, ledger, composer, repository = _composition_case()
        missing_attempt = task.scenes[0].visual_result.attempt_id
        del ledger.records[missing_attempt]
        repository = _RepositorySpy(repository)
        result = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=repository,
        ).compose(request_reference, request, task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertEqual(result, ProductionMediaFailure("execution", "ATTEMPT_STORAGE_FAILED", "provider attempt persistence failed"))
        self.assertEqual(repository.commit_calls, [])
        self.assertEqual(composer.calls, [])

    def test_repository_read_failure_is_safe_and_happens_before_attempt_lookup(self):
        request_reference, request, task, ledger, composer, _repository = _composition_case()
        result = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=_FailingReadRepository(),
        ).compose(request_reference, request, task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_ARTIFACT_COMMIT_FAILED", "media Artifact persistence failed"))
        self.assertEqual(ledger.get_calls, [])
        self.assertEqual(composer.calls, [])

    def test_video_commit_failure_preserves_upstream_and_exact_retry_reuses_them(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        failing_repository = _RepositorySpy(repository, fail_video=True)
        orchestrator = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=failing_repository,
        )
        failed = orchestrator.compose(request_reference, request, task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertEqual(failed.code, "MEDIA_ARTIFACT_COMMIT_FAILED")
        self.assertEqual([candidate.artifact_type for candidate in failing_repository.commit_calls], ["scene_clip", "scene_audio", "scene_clip", "scene_audio", "subtitle", "master_audio", "video"])
        retry_composer = _Composer()
        retry = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=retry_composer, artifact_repository=repository,
        ).compose(request_reference, request, task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertIsInstance(retry, ProductionCompositionResult)
        self.assertEqual(retry_composer.calls, [task])

    def test_forged_repository_success_fails_closed_before_composer(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        forged_repository = _ForgedCommitRepository(repository)
        result = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=forged_repository,
        ).compose(request_reference, request, task, artifact_identity="media:forged", composition_commit_id="composition-commit-forged")
        self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_ARTIFACT_COMMIT_FAILED", "media Artifact persistence failed"))
        self.assertEqual(composer.calls, [])

    def test_mutable_repository_snapshot_fails_closed_before_composer(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        result = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=_MutableSnapshotRepository(repository),
        ).compose(request_reference, request, task, artifact_identity="media:mutable", composition_commit_id="composition-commit-mutable")
        self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_ARTIFACT_COMMIT_FAILED", "media Artifact persistence failed"))
        self.assertEqual(composer.calls, [])

    def test_forged_committed_request_scalar_fails_before_repository_or_attempt_side_effects(self):
        request_reference, request, task, ledger, composer, repository = _composition_case(task_id="task:evil-request")
        request_payload = dict(request.payload)
        production_request = dict(request_payload["production_request"])
        production_request["scenes"] = tuple(
            dict(scene, narration=_EvilString(scene["narration"])) if scene["scene_id"] == "scene-1" else dict(scene)
            for scene in production_request["scenes"]
        )
        request_payload["production_request"] = production_request
        evil_reference = repository.commit(ArtifactCandidate(
            "production_request",
            request.reference.identity,
            request_payload,
            request.provenance,
            request.dependencies,
            True,
            "request-commit-evil",
            request.reference,
        ))
        evil_version = repository.get(evil_reference)
        for attempt_id, record in tuple(ledger.records.items()):
            ledger.records[attempt_id] = replace(record, production_request_reference=evil_reference)
        spy = _RepositorySpy(repository)
        result = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=spy,
        ).compose(
            evil_reference,
            evil_version,
            replace(task, production_request_reference=evil_reference),
            artifact_identity="media:evil-request",
            composition_commit_id="composition-commit-evil-request",
        )
        self.assertEqual(result, ProductionMediaFailure("validation", "INVALID_COMPOSITION_CONTEXT", "media composition context is invalid"))
        self.assertEqual(spy.commit_calls, [])
        self.assertEqual(spy.get_calls, [])
        self.assertEqual(ledger.get_calls, [])
        self.assertEqual(composer.calls, [])

    def test_forged_composer_success_is_rejected_without_video_commit(self):
        request_reference, request, task, ledger, _composer, repository = _composition_case()
        forged = _ForgedComposer()
        repository = _RepositorySpy(repository)
        result = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=forged, artifact_repository=repository,
        ).compose(request_reference, request, task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertEqual(result, ProductionMediaFailure("execution", "MEDIA_COMPOSITION_FAILED", "local media composition failed"))
        self.assertEqual(forged.calls, 1)
        self.assertNotIn("video", [candidate.artifact_type for candidate in repository.commit_calls])

    def test_changed_attempt_output_conflicts_without_new_versions_or_composer_call(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        first = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=repository,
        ).compose(request_reference, request, task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertIsInstance(first, ProductionCompositionResult)
        scene = task.scenes[0]
        changed_output = WorkspaceFileReference(task.task_id, "media", "scene-1-changed.mp4")
        ledger.records[scene.visual_result.attempt_id] = replace(
            ledger.records[scene.visual_result.attempt_id], output_references=(changed_output,)
        )
        changed_scene = replace(scene, visual_result=replace(scene.visual_result, output_reference=changed_output))
        changed_task = replace(task, scenes=(changed_scene, *task.scenes[1:]))
        conflict = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=repository,
        ).compose(request_reference, request, changed_task, artifact_identity="media:episode-1", composition_commit_id="composition-commit-1")
        self.assertEqual(conflict, ProductionMediaFailure("execution", "MEDIA_ARTIFACT_CONFLICT", "media Artifact identity conflicts with existing input"))
        self.assertEqual(len(composer.calls), 1)
        with self.assertRaises(ArtifactNotFoundError):
            repository.get(ArtifactReference("scene_clip", "media:episode-1:scene-1", 2))

    def test_changed_committed_request_conflicts_before_composer_and_preserves_facts(self):
        request_reference, request, task, ledger, composer, repository = _composition_case()
        first = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=repository,
        ).compose(
            request_reference, request, task,
            artifact_identity="media:request-change", composition_commit_id="composition-commit-request-change",
        )
        self.assertIsInstance(first, ProductionCompositionResult)
        original_versions = {
            reference: repository.get(reference)
            for reference in (
                *first.scene_clip_references,
                *first.scene_audio_references,
                first.subtitle_reference,
                first.master_audio_reference,
                first.video_reference,
            )
        }
        changed_payload = dict(request.payload)
        changed_request = dict(changed_payload["production_request"])
        changed_scenes = tuple(
            dict(scene, narration="新的字幕。") if scene["scene_id"] == "scene-1" else dict(scene)
            for scene in changed_request["scenes"]
        )
        changed_request["scenes"] = changed_scenes
        changed_payload["production_request"] = changed_request
        changed_reference = repository.commit(ArtifactCandidate(
            "production_request", request.reference.identity, changed_payload,
            request.provenance, request.dependencies, True, "request-commit-2", request.reference,
        ))
        changed_version = repository.get(changed_reference)
        for attempt_id, record in tuple(ledger.records.items()):
            ledger.records[attempt_id] = replace(record, production_request_reference=changed_reference)
        changed_task = replace(
            task,
            production_request_reference=changed_reference,
            scenes=(replace(task.scenes[0], subtitle_text="新的字幕。"), task.scenes[1]),
        )
        conflict = ProductionOrchestrator(
            ledger, object(), object(), clock=lambda: datetime(2026, 8, 12, tzinfo=timezone.utc),
            media_composer=composer, artifact_repository=repository,
        ).compose(
            changed_reference, changed_version, changed_task,
            artifact_identity="media:request-change", composition_commit_id="composition-commit-request-change",
        )
        self.assertEqual(conflict, ProductionMediaFailure("execution", "MEDIA_ARTIFACT_CONFLICT", "media Artifact identity conflicts with existing input"))
        self.assertEqual(len(composer.calls), 1)
        for reference, version in original_versions.items():
            self.assertEqual(repository.get(reference), version)
            with self.assertRaises(ArtifactNotFoundError):
                repository.get(ArtifactReference(reference.artifact_type, reference.identity, 2))


if __name__ == "__main__":
    unittest.main()
