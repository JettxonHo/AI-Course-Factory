"""Offline integration proof for real local FFmpeg Fixture media."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import subprocess
import unittest

from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetDecisionOutcome,
    FFmpegFixtureVisualGenerator,
    FFmpegFixtureVoiceGenerator,
    ProductionExecutionResult,
    ProductionMediaFailure,
    ProductionOrchestrator,
    ProviderAttemptLedger,
    ProviderAttemptReservation,
    SQLiteBudgetAuthorizationRepository,
    SQLiteProviderAttemptRepository,
    VisualGenerationTask,
    VoiceSynthesisTask,
)

from tests.integration import test_budget_authorization as _budget_fixture


class _ExplodingVisual:
    calls = 0

    def generate(self, _task):
        self.calls += 1
        raise AssertionError("terminal replay must not invoke visual adapter")


class _ExplodingVoice:
    calls = 0

    def synthesize(self, _task):
        self.calls += 1
        raise AssertionError("terminal replay must not invoke voice adapter")


def _probe(path: Path) -> dict:
    result = subprocess.run(
        [
            "/opt/homebrew/bin/ffprobe", "-v", "error", "-show_entries",
            "stream=codec_type,codec_name,width,height,pix_fmt,duration,sample_rate,channels,r_frame_rate,avg_frame_rate:format=format_name,duration:format_tags=comment",
            "-of", "json", str(path),
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=True,
    )
    return json.loads(result.stdout.decode("utf-8"))


class FFmpegFixtureOrchestratorIntegrationTests(unittest.TestCase):
    _reserved_at = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)

    def _fixture(self, directory: str):
        _artifacts, request_reference, request, budget_reference, budget = _budget_fixture.BudgetAuthorizationIntegrationTests()._committed_budget()
        database = Path(directory) / "factory.sqlite3"
        budget_repository = SQLiteBudgetAuthorizationRepository(database)
        decision = BudgetAuthorizationBoundary(budget_repository).decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="decision:ffmpeg",
            authorization_id="authorization:ffmpeg",
            task_id="task:ffmpeg",
            thread_id="thread:ffmpeg",
            creator_id="creator:ffmpeg",
            decided_at=self._reserved_at,
            action="approve",
            maximum_approved_amount_micros=6_000,
            maximum_attempts=2,
        )
        self.assertIsInstance(decision, BudgetDecisionOutcome)
        self.assertIsNotNone(decision.authorization)
        authorization = decision.authorization
        workspace_root = Path(directory) / "workspace"
        workspace = FilesystemWorkspace(workspace_root)
        self.assertEqual(workspace.prepare(authorization.task_id).task_id, authorization.task_id)
        return request_reference, request, authorization, database, workspace_root, budget_repository

    def _reservation(self, authorization, *, attempt_id, operation, provider, scene_id="scene-1"):
        return ProviderAttemptReservation(
            attempt_id,
            authorization.task_id,
            authorization.authorization_id,
            scene_id,
            operation,
            provider,
            f"key:{attempt_id}",
            WorkspaceFileReference(authorization.task_id, "provider-records", f"{attempt_id.replace(':', '-')}.json"),
            self._reserved_at,
        )

    def test_real_fixture_visual_voice_execute_probe_and_terminal_replay(self):
        with TemporaryDirectory() as directory:
            reference, request, authorization, database, workspace_root, budget_repository = self._fixture(directory)
            workspace = FilesystemWorkspace(workspace_root)
            attempt_repository = SQLiteProviderAttemptRepository(database)
            visual_reservation = self._reservation(
                authorization,
                attempt_id="attempt:visual",
                operation="visual",
                provider="ffmpeg-fixture-visual-v1",
            )
            voice_reservation = self._reservation(
                authorization,
                attempt_id="attempt:voice",
                operation="voice",
                provider="ffmpeg-fixture-voice-v1",
            )
            visual_task = VisualGenerationTask(
                authorization.task_id, visual_reservation.attempt_id, reference, "scene-1", "9:16", 30.0,
                "展示小土豆。", "挥手。", WorkspaceFileReference(authorization.task_id, "media", "scene-1.mp4"),
            )
            voice_task = VoiceSynthesisTask(
                authorization.task_id, voice_reservation.attempt_id, reference, "scene-1", "zh-CN", 30.0,
                "你好。", WorkspaceFileReference(authorization.task_id, "media", "scene-1.m4a"),
            )
            kwargs = {
                "ffmpeg_executable": "/opt/homebrew/bin/ffmpeg",
                "ffprobe_executable": "/opt/homebrew/bin/ffprobe",
            }
            orchestrator = ProductionOrchestrator(
                ProviderAttemptLedger(budget_repository, attempt_repository),
                FFmpegFixtureVisualGenerator(workspace, **kwargs),
                FFmpegFixtureVoiceGenerator(workspace, **kwargs),
                clock=lambda: self._reserved_at + timedelta(seconds=1),
            )
            visual_result = orchestrator.execute(reference, request, visual_reservation, visual_task)
            voice_result = orchestrator.execute(reference, request, voice_reservation, voice_task)
            self.assertIsInstance(visual_result, ProductionExecutionResult)
            self.assertIsInstance(voice_result, ProductionExecutionResult)
            self.assertEqual(visual_result.output_reference, visual_task.output_reference)
            self.assertEqual(voice_result.output_reference, voice_task.output_reference)
            self.assertEqual(attempt_repository.get(visual_reservation.attempt_id).charged_amount_micros, 0)
            self.assertEqual(attempt_repository.get(voice_reservation.attempt_id).charged_amount_micros, 0)
            visual_bytes = workspace.read(visual_task.output_reference)
            voice_bytes = workspace.read(voice_task.output_reference)
            self.assertIsInstance(visual_bytes, bytes)
            self.assertIsInstance(voice_bytes, bytes)
            self.assertIn(b"ftyp", visual_bytes[:128])
            self.assertIn(b"ftyp", voice_bytes[:128])

            visual_path = Path(directory) / "scene.mp4"
            voice_path = Path(directory) / "scene.m4a"
            visual_path.write_bytes(visual_bytes)
            voice_path.write_bytes(voice_bytes)
            visual_probe = _probe(visual_path)
            voice_probe = _probe(voice_path)
            self.assertEqual(visual_probe["streams"], [{
                "codec_name": "h264", "codec_type": "video", "width": 540, "height": 960,
                "pix_fmt": "yuv420p", "r_frame_rate": "24/1", "avg_frame_rate": "24/1",
                "duration": "30.000000",
            }])
            self.assertEqual(voice_probe["streams"], [{
                "codec_name": "aac", "codec_type": "audio", "sample_rate": "48000",
                "channels": 1, "r_frame_rate": "0/0", "avg_frame_rate": "0/0", "duration": "30.000000",
            }])
            self.assertEqual(visual_probe["format"]["format_name"], "mov,mp4,m4a,3gp,3g2,mj2")
            self.assertEqual(voice_probe["format"]["format_name"], "mov,mp4,m4a,3gp,3g2,mj2")
            self.assertTrue(visual_probe["format"]["tags"]["comment"].startswith("ai-course-factory-ffmpeg-fixture-v1:"))
            self.assertTrue(voice_probe["format"]["tags"]["comment"].startswith("ai-course-factory-ffmpeg-fixture-v1:"))

            attempt_repository.close()
            budget_repository.close()
            reopened_attempt = SQLiteProviderAttemptRepository(database)
            reopened_budget = SQLiteBudgetAuthorizationRepository(database)
            exploding_visual = _ExplodingVisual()
            exploding_voice = _ExplodingVoice()
            try:
                replay = ProductionOrchestrator(
                    ProviderAttemptLedger(reopened_budget, reopened_attempt),
                    exploding_visual,
                    exploding_voice,
                    clock=lambda: self._reserved_at + timedelta(seconds=2),
                )
                self.assertEqual(replay.execute(reference, request, visual_reservation, visual_task), visual_result)
                self.assertEqual(replay.execute(reference, request, voice_reservation, voice_task), voice_result)
                self.assertEqual(exploding_visual.calls, 0)
                self.assertEqual(exploding_voice.calls, 0)
                self.assertEqual(FilesystemWorkspace(workspace_root).read(visual_task.output_reference), visual_bytes)
                self.assertEqual(FilesystemWorkspace(workspace_root).read(voice_task.output_reference), voice_bytes)
            finally:
                reopened_attempt.close()
                reopened_budget.close()

    def test_tool_failure_after_claim_is_zero_charge_terminal_and_replay_does_not_call_again(self):
        with TemporaryDirectory() as directory:
            reference, request, authorization, database, workspace_root, budget_repository = self._fixture(directory)
            workspace = FilesystemWorkspace(workspace_root)
            attempts = SQLiteProviderAttemptRepository(database)
            reservation = self._reservation(
                authorization,
                attempt_id="attempt:tool-failure",
                operation="visual",
                provider="ffmpeg-fixture-visual-v1",
            )
            task = VisualGenerationTask(
                authorization.task_id, reservation.attempt_id, reference, "scene-1", "9:16", 30.0,
                "展示小土豆。", "挥手。", WorkspaceFileReference(authorization.task_id, "media", "failed.mp4"),
            )
            orchestrator = ProductionOrchestrator(
                ProviderAttemptLedger(budget_repository, attempts),
                FFmpegFixtureVisualGenerator(
                    workspace,
                    ffmpeg_executable="ffmpeg",
                    ffprobe_executable="/opt/homebrew/bin/ffprobe",
                ),
                FFmpegFixtureVoiceGenerator(
                    workspace,
                    ffmpeg_executable="/opt/homebrew/bin/ffmpeg",
                    ffprobe_executable="/opt/homebrew/bin/ffprobe",
                ),
                clock=lambda: self._reserved_at + timedelta(seconds=1),
            )
            result = orchestrator.execute(reference, request, reservation, task)
            self.assertIsInstance(result, ProductionMediaFailure)
            self.assertEqual(result.code, "GENERATION_FAILED")
            record = attempts.get(reservation.attempt_id)
            self.assertEqual(record.status, "failed")
            self.assertEqual(record.charged_amount_micros, 0)
            self.assertEqual(record.output_references, ())
            attempts.close()
            budget_repository.close()
            reopened_attempts = SQLiteProviderAttemptRepository(database)
            reopened_budget = SQLiteBudgetAuthorizationRepository(database)
            exploding_visual = _ExplodingVisual()
            exploding_voice = _ExplodingVoice()
            try:
                replay = ProductionOrchestrator(
                    ProviderAttemptLedger(reopened_budget, reopened_attempts),
                    exploding_visual,
                    exploding_voice,
                    clock=lambda: self._reserved_at + timedelta(seconds=2),
                ).execute(reference, request, reservation, task)
                self.assertEqual(replay, result)
                self.assertEqual(replay, ProductionMediaFailure("execution", "GENERATION_FAILED", "media generation failed"))
                self.assertEqual(exploding_visual.calls, 0)
                self.assertEqual(exploding_voice.calls, 0)
                self.assertEqual(reopened_attempts.get(reservation.attempt_id), record)
                self.assertEqual(reopened_attempts.get(reservation.attempt_id).charged_amount_micros, 0)
                self.assertEqual(reopened_attempts.get(reservation.attempt_id).output_references, ())
                missing = FilesystemWorkspace(workspace_root).read(task.output_reference)
                self.assertEqual(getattr(missing, "code", None), "WORKSPACE_FILE_NOT_FOUND")
            finally:
                reopened_attempts.close()
                reopened_budget.close()


if __name__ == "__main__":
    unittest.main()
