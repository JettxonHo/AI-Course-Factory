"""Offline product-path composition through durable local stores."""

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.artifacts import ArtifactCandidate, ArtifactCommitError, ArtifactNotFoundError, ArtifactReference, SQLiteArtifactRepository
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetDecisionOutcome,
    BudgetModule,
    FFmpegFixtureVisualGenerator,
    FFmpegFixtureVoiceGenerator,
    FFmpegMediaComposer,
    MediaCompositionScene,
    MediaCompositionTask,
    MediaGenerationResult,
    ProductionCompositionResult,
    ProductionExecutionResult,
    ProductionOrchestrator,
    ProviderAttemptLedger,
    ProviderAttemptReservation,
    SQLiteBudgetAuthorizationRepository,
    SQLiteProviderAttemptRepository,
    RetryPolicy,
    VisualGenerationTask,
    VoiceSynthesisTask,
)
from ai_course_factory.production.adapters.ffmpeg_composer import _binding

from tests.production.test_budget import fixture_snapshot, production_request_parts


_FFMPEG = "/opt/homebrew/bin/ffmpeg"
_FFPROBE = "/opt/homebrew/bin/ffprobe"
_RESERVED_AT = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


class _FailVideoRepository:
    def __init__(self, repository):
        self.repository = repository

    def commit(self, candidate):
        if candidate.artifact_type == "video":
            raise ArtifactCommitError("forced video commit failure")
        return self.repository.commit(candidate)

    def get(self, reference):
        return self.repository.get(reference)


def _probe(path: Path) -> dict:
    completed = subprocess.run(
        [
            _FFPROBE,
            "-v",
            "error",
            "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,sample_rate,channels,r_frame_rate,avg_frame_rate,duration:format=format_name,duration:format_tags=comment",
            "-of",
            "json",
            str(path),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return json.loads(completed.stdout.decode("utf-8"))


class ProductPathCompositionIntegrationTests(unittest.TestCase):
    def _stores(self, root: Path):
        database = root / "factory.sqlite3"
        artifacts = SQLiteArtifactRepository(database)
        request_reference, request = production_request_parts()
        committed_request = artifacts.commit(
            ArtifactCandidate(
                "production_request",
                request_reference.identity,
                request.payload,
                request.provenance,
                request.dependencies,
                True,
                request.commit_id,
            )
        )
        request = artifacts.get(committed_request)
        timeline_reference = request.payload["timeline_reference"]
        artifacts.commit(
            ArtifactCandidate(
                "timeline",
                timeline_reference.identity,
                {},
                (),
                (),
                True,
                "timeline-commit:episode-1",
            )
        )
        budget_candidate = BudgetModule.estimate(
            committed_request,
            request,
            price_snapshot=fixture_snapshot(committed_request),
            retry_policy=RetryPolicy(2),
            budget_identity="budget:episode-1",
            budget_commit_id="budget-commit:episode-1",
        )
        budget_reference = artifacts.commit(budget_candidate)
        budget = artifacts.get(budget_reference)
        budget_repository = SQLiteBudgetAuthorizationRepository(database)
        decision = BudgetAuthorizationBoundary(budget_repository).decide(
            committed_request,
            request,
            budget_reference,
            budget,
            decision_id="decision:composition",
            authorization_id="authorization:composition",
            task_id="task:composition",
            thread_id="thread:composition",
            creator_id="creator:composition",
            decided_at=_RESERVED_AT,
            action="approve",
            maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(decision, BudgetDecisionOutcome)
        self.assertIsNotNone(decision.authorization)
        return database, artifacts, budget_repository, committed_request, request, decision.authorization

    def test_durable_product_path_compose_commits_probeable_artifacts_and_replays(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            database, artifacts, budget_repository, request_reference, request, authorization = self._stores(root)
            workspace_root = root / "workspace"
            workspace = FilesystemWorkspace(workspace_root)
            self.assertEqual(workspace.prepare(authorization.task_id).task_id, authorization.task_id)
            attempts = SQLiteProviderAttemptRepository(database)
            ledger = ProviderAttemptLedger(budget_repository, attempts)
            kwargs = {"ffmpeg_executable": _FFMPEG, "ffprobe_executable": _FFPROBE}
            orchestrator = ProductionOrchestrator(
                ledger,
                FFmpegFixtureVisualGenerator(workspace, **kwargs),
                FFmpegFixtureVoiceGenerator(workspace, **kwargs),
                clock=lambda: _RESERVED_AT + timedelta(seconds=1),
            )
            scenes = []
            for index, (scene_id, narration, visual_intent, action, start, end) in enumerate(
                (
                    ("scene-1", "你好。", "展示小土豆。", "挥手。", 0, 30_000),
                    ("scene-2", "再见。", "小土豆离开。", "转身。", 30_000, 60_000),
                ),
                start=1,
            ):
                visual_reservation = ProviderAttemptReservation(
                    f"attempt:visual-{index}", authorization.task_id, authorization.authorization_id,
                    scene_id, "visual", "ffmpeg-fixture-visual-v1", f"key:visual-{index}",
                    WorkspaceFileReference(authorization.task_id, "provider-records", f"visual-{index}.json"), _RESERVED_AT,
                )
                voice_reservation = ProviderAttemptReservation(
                    f"attempt:voice-{index}", authorization.task_id, authorization.authorization_id,
                    scene_id, "voice", "ffmpeg-fixture-voice-v1", f"key:voice-{index}",
                    WorkspaceFileReference(authorization.task_id, "provider-records", f"voice-{index}.json"), _RESERVED_AT,
                )
                visual_task = VisualGenerationTask(
                    authorization.task_id, visual_reservation.attempt_id, request_reference, scene_id,
                    "9:16", 30.0, visual_intent, action,
                    WorkspaceFileReference(authorization.task_id, "media", f"scene-{index}.mp4"),
                )
                voice_task = VoiceSynthesisTask(
                    authorization.task_id, voice_reservation.attempt_id, request_reference, scene_id,
                    "zh-CN", 30.0, narration,
                    WorkspaceFileReference(authorization.task_id, "media", f"scene-{index}.m4a"),
                )
                visual_result = orchestrator.execute(request_reference, request, visual_reservation, visual_task)
                voice_result = orchestrator.execute(request_reference, request, voice_reservation, voice_task)
                self.assertIsInstance(visual_result, ProductionExecutionResult)
                self.assertIsInstance(voice_result, ProductionExecutionResult)
                scenes.append(MediaCompositionScene(scene_id, start, end, MediaGenerationResult(
                    visual_result.attempt_id, scene_id, "visual", visual_result.provider, visual_result.output_reference, "video/mp4", 30.0, "SUCCESS",
                ), MediaGenerationResult(
                    voice_result.attempt_id, scene_id, "voice", voice_result.provider, voice_result.output_reference, "audio/mp4", 30.0, "SUCCESS",
                ), narration))
            composition_task = MediaCompositionTask(
                authorization.task_id,
                "composition:episode-1",
                request_reference,
                request.payload["timeline_reference"],
                tuple(scenes),
                WorkspaceFileReference(authorization.task_id, "media", "composition.mp4"),
            )
            composer = FFmpegMediaComposer(workspace, **kwargs)
            orchestrator = ProductionOrchestrator(
                ledger,
                object(),
                object(),
                clock=lambda: _RESERVED_AT + timedelta(seconds=1),
                media_composer=composer,
                artifact_repository=artifacts,
            )
            result = orchestrator.compose(
                request_reference,
                request,
                composition_task,
                artifact_identity="media:episode-1",
                composition_commit_id="composition-commit-1",
            )
            self.assertIsInstance(result, ProductionCompositionResult)
            self.assertEqual(result.result_code, "SUCCESS")
            self.assertEqual(len(result.scene_clip_references), 2)
            self.assertEqual(len(result.scene_audio_references), 2)
            timeline_reference = request.payload["timeline_reference"]
            for index, scene in enumerate(scenes, start=1):
                for artifact_type, media_result, reference, purpose, media_type, output_name in (
                    ("scene_clip", scene.visual_result, result.scene_clip_references[index - 1], "production_composition_scene_clip", "video/mp4", f"scene-{index}.mp4"),
                    ("scene_audio", scene.voice_result, result.scene_audio_references[index - 1], "production_composition_scene_audio", "audio/mp4", f"scene-{index}.m4a"),
                ):
                    version = artifacts.get(reference)
                    self.assertEqual(version.reference, reference)
                    self.assertEqual(version.payload, {
                        "production_request_reference": request_reference,
                        "scene_id": scene.scene_id,
                        "attempt_id": media_result.attempt_id,
                        "provider": media_result.provider,
                        "output_reference": {"task_id": authorization.task_id, "area": "media", "name": output_name},
                        "media_type": media_type,
                        "duration_milliseconds": scene.end_milliseconds - scene.start_milliseconds,
                    })
                    self.assertEqual(version.provenance, ({
                        "purpose": purpose,
                        "production_request_reference": request_reference,
                        "scene_id": scene.scene_id,
                        "attempt_id": media_result.attempt_id,
                    },))
                    self.assertEqual(version.dependencies, (request_reference,))
            subtitle = artifacts.get(result.subtitle_reference)
            self.assertEqual(subtitle.payload, {
                "production_request_reference": request_reference,
                "timeline_reference": timeline_reference,
                "cues": tuple({
                    "scene_id": scene.scene_id,
                    "start_milliseconds": scene.start_milliseconds,
                    "end_milliseconds": scene.end_milliseconds,
                    "text": scene.subtitle_text,
                } for scene in scenes),
            })
            self.assertEqual(subtitle.provenance, ({
                "purpose": "production_composition_subtitle",
                "production_request_reference": request_reference,
                "timeline_reference": timeline_reference,
            },))
            self.assertEqual(subtitle.dependencies, (request_reference, timeline_reference))
            master = artifacts.get(result.master_audio_reference)
            self.assertEqual(master.payload, {
                "production_request_reference": request_reference,
                "timeline_reference": timeline_reference,
                "scene_audio_references": result.scene_audio_references,
                "duration_milliseconds": 60_000,
            })
            self.assertEqual(master.provenance, ({
                "purpose": "production_composition_master_audio",
                "production_request_reference": request_reference,
                "timeline_reference": timeline_reference,
                "scene_audio_references": result.scene_audio_references,
            },))
            self.assertEqual(master.dependencies, (request_reference, timeline_reference, *result.scene_audio_references))
            video = artifacts.get(result.video_reference)
            self.assertEqual(video.payload, {
                "production_request_reference": request_reference,
                "timeline_reference": timeline_reference,
                "composition_id": composition_task.composition_id,
                "scene_ids": tuple(scene.scene_id for scene in scenes),
                "scene_clip_references": result.scene_clip_references,
                "subtitle_reference": result.subtitle_reference,
                "master_audio_reference": result.master_audio_reference,
                "composer": "ffmpeg-composer-v1",
                "output_reference": {"task_id": authorization.task_id, "area": "media", "name": "composition.mp4"},
                "media_type": "video/mp4",
                "duration_milliseconds": 60_000,
            })
            self.assertEqual(video.provenance, ({
                "purpose": "production_composition_video",
                "production_request_reference": request_reference,
                "timeline_reference": timeline_reference,
                "composition_id": composition_task.composition_id,
            },))
            self.assertEqual(video.dependencies, (request_reference, timeline_reference, *result.scene_clip_references, result.subtitle_reference, result.master_audio_reference))
            output = workspace.read(result.output_reference)
            output_path = root / "composition.mp4"
            output_path.write_bytes(output)
            probe = _probe(output_path)
            self.assertEqual(len(probe["streams"]), 3)
            self.assertEqual({stream["codec_type"] for stream in probe["streams"]}, {"video", "audio", "subtitle"})
            self.assertEqual(probe["format"]["format_name"], "mov,mp4,m4a,3gp,3g2,mj2")
            streams = {stream["codec_type"]: stream for stream in probe["streams"]}
            self.assertEqual(streams["video"]["codec_name"], "h264")
            self.assertEqual((streams["video"]["width"], streams["video"]["height"], streams["video"]["pix_fmt"]), (540, 960, "yuv420p"))
            self.assertEqual((streams["video"]["r_frame_rate"], streams["video"]["avg_frame_rate"]), ("24/1", "24/1"))
            self.assertEqual(streams["audio"]["codec_name"], "aac")
            self.assertEqual((streams["audio"]["sample_rate"], streams["audio"]["channels"]), ("48000", 1))
            self.assertEqual(streams["subtitle"]["codec_name"], "mov_text")
            self.assertAlmostEqual(float(streams["video"]["duration"]), 60.0, delta=0.15)
            self.assertAlmostEqual(float(probe["format"]["duration"]), 60.0, delta=0.15)
            self.assertEqual(probe["format"]["tags"]["comment"], _binding(composition_task))
            failed = ProductionOrchestrator(
                ledger,
                object(),
                object(),
                clock=lambda: _RESERVED_AT + timedelta(seconds=1),
                media_composer=composer,
                artifact_repository=_FailVideoRepository(artifacts),
            ).compose(
                request_reference,
                request,
                composition_task,
                artifact_identity="media:episode-recovery",
                composition_commit_id="composition-commit-recovery",
            )
            self.assertEqual(failed.code, "MEDIA_ARTIFACT_COMMIT_FAILED")
            self.assertEqual(workspace.read(result.output_reference), output)
            attempts.close()
            budget_repository.close()
            artifacts.close()
            replay_artifacts = SQLiteArtifactRepository(database)
            replay_budget = SQLiteBudgetAuthorizationRepository(database)
            replay_attempts = SQLiteProviderAttemptRepository(database)
            try:
                replay_workspace = FilesystemWorkspace(workspace_root)
                replay_orchestrator = ProductionOrchestrator(
                    ProviderAttemptLedger(replay_budget, replay_attempts),
                    object(),
                    object(),
                    clock=lambda: _RESERVED_AT + timedelta(seconds=2),
                    media_composer=FFmpegMediaComposer(replay_workspace, **kwargs),
                    artifact_repository=replay_artifacts,
                )
                replay = replay_orchestrator.compose(
                    request_reference,
                    replay_artifacts.get(request_reference),
                    composition_task,
                    artifact_identity="media:episode-1",
                    composition_commit_id="composition-commit-1",
                )
                self.assertEqual(replay, result)
                self.assertEqual(replay_workspace.read(result.output_reference), output)
                self.assertEqual(len(replay_artifacts.get(result.video_reference).dependencies), 6)
                with self.assertRaises(ArtifactNotFoundError):
                    replay_artifacts.get(ArtifactReference("video", "media:episode-1", 2))
                recovered = replay_orchestrator.compose(
                    request_reference,
                    replay_artifacts.get(request_reference),
                    composition_task,
                    artifact_identity="media:episode-recovery",
                    composition_commit_id="composition-commit-recovery",
                )
                self.assertIsInstance(recovered, ProductionCompositionResult)
                self.assertEqual(
                    recovered.scene_clip_references,
                    tuple(ArtifactReference("scene_clip", f"media:episode-recovery:{scene.scene_id}", 1) for scene in scenes),
                )
                self.assertEqual(
                    recovered.scene_audio_references,
                    tuple(ArtifactReference("scene_audio", f"media:episode-recovery:{scene.scene_id}", 1) for scene in scenes),
                )
                self.assertEqual(recovered.subtitle_reference, ArtifactReference("subtitle", "media:episode-recovery", 1))
                self.assertEqual(recovered.master_audio_reference, ArtifactReference("master_audio", "media:episode-recovery", 1))
                self.assertEqual(recovered.video_reference, ArtifactReference("video", "media:episode-recovery", 1))
                for reference in (
                    *recovered.scene_clip_references,
                    *recovered.scene_audio_references,
                    recovered.subtitle_reference,
                    recovered.master_audio_reference,
                    recovered.video_reference,
                ):
                    self.assertEqual(replay_artifacts.get(reference).reference, reference)
                    with self.assertRaises(ArtifactNotFoundError):
                        replay_artifacts.get(ArtifactReference(reference.artifact_type, reference.identity, 2))
                self.assertEqual(recovered.output_reference, result.output_reference)
                self.assertEqual(replay_workspace.read(recovered.output_reference), output)
            finally:
                replay_attempts.close()
                replay_budget.close()
                replay_artifacts.close()


if __name__ == "__main__":
    unittest.main()
