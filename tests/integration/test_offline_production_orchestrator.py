"""Offline integration evidence for the claim-gated Production Orchestrator."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileRecord, WorkspaceFileReference
from ai_course_factory.production import (
    BudgetAuthorizationBoundary,
    BudgetDecisionOutcome,
    DeterministicFakeVisualGenerator,
    DeterministicFakeVoiceGenerator,
    MediaGenerationResult,
    ProductionExecutionResult,
    ProductionMediaFailure,
    ProductionOrchestrator,
    ProviderAttemptClaim,
    ProviderAttemptLedger,
    ProviderAttemptOutcome,
    ProviderAttemptRecord,
    ProviderAttemptReservation,
    SQLiteBudgetAuthorizationRepository,
    SQLiteProviderAttemptRepository,
    VisualGenerationTask,
    VoiceSynthesisTask,
)

from tests.integration import test_budget_authorization as _budget_fixture


class _ExplodingVisual:
    def __init__(self):
        self.calls = 0

    def generate(self, _task):
        self.calls += 1
        raise AssertionError("terminal replay must not invoke visual adapter")


class _ExplodingVoice:
    def __init__(self):
        self.calls = 0

    def synthesize(self, _task):
        self.calls += 1
        raise AssertionError("terminal replay must not invoke voice adapter")


class _MalformedVisual:
    def __init__(self, mode):
        self.mode = mode
        self.calls = 0

    def generate(self, _task):
        self.calls += 1
        if self.mode == "raise":
            raise RuntimeError("provider secret/path detail")
        return object()


class OfflineProductionOrchestratorIntegrationTests(unittest.TestCase):
    _reserved_at = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)

    def _fixture(self, directory: str):
        artifacts, request_reference, request, budget_reference, budget = _budget_fixture.BudgetAuthorizationIntegrationTests()._committed_budget()
        database = Path(directory) / "factory.sqlite3"
        budget_repository = SQLiteBudgetAuthorizationRepository(database)
        decision = BudgetAuthorizationBoundary(budget_repository).decide(
            request_reference,
            request,
            budget_reference,
            budget,
            decision_id="decision:orchestrator",
            authorization_id="authorization:orchestrator",
            task_id="task:orchestrator",
            thread_id="thread:orchestrator",
            creator_id="creator:orchestrator",
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

    def test_fake_visual_voice_execute_persist_and_terminal_replay_after_restart(self):
        with TemporaryDirectory() as directory:
            reference, request, authorization, database, workspace_root, budget_repository = self._fixture(directory)
            workspace = FilesystemWorkspace(workspace_root)
            attempt_repository = SQLiteProviderAttemptRepository(database)
            visual_reservation = self._reservation(
                authorization,
                attempt_id="attempt:visual",
                operation="visual",
                provider="fake-visual-v1",
            )
            voice_reservation = self._reservation(
                authorization,
                attempt_id="attempt:voice",
                operation="voice",
                provider="fake-voice-v1",
            )
            visual_task = VisualGenerationTask(
                authorization.task_id,
                visual_reservation.attempt_id,
                reference,
                "scene-1",
                "9:16",
                30.0,
                "展示小土豆。",
                "挥手。",
                WorkspaceFileReference(authorization.task_id, "media", "scene-1.visual.json"),
            )
            voice_task = VoiceSynthesisTask(
                authorization.task_id,
                voice_reservation.attempt_id,
                reference,
                "scene-1",
                "zh-CN",
                30.0,
                "你好。",
                WorkspaceFileReference(authorization.task_id, "media", "scene-1.voice.json"),
            )
            orchestrator = ProductionOrchestrator(
                ProviderAttemptLedger(budget_repository, attempt_repository),
                DeterministicFakeVisualGenerator(workspace),
                DeterministicFakeVoiceGenerator(workspace),
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
            self.assertNotIn(b"ftyp", visual_bytes)
            self.assertNotIn(b"ftyp", voice_bytes)

            attempt_repository.close()
            budget_repository.close()
            reopened_attempt = SQLiteProviderAttemptRepository(database)
            reopened_budget = SQLiteBudgetAuthorizationRepository(database)
            exploding_visual = _ExplodingVisual()
            exploding_voice = _ExplodingVoice()
            try:
                replay_orchestrator = ProductionOrchestrator(
                    ProviderAttemptLedger(reopened_budget, reopened_attempt),
                    exploding_visual,
                    exploding_voice,
                    clock=lambda: self._reserved_at + timedelta(seconds=2),
                )
                self.assertEqual(replay_orchestrator.execute(reference, request, visual_reservation, visual_task), visual_result)
                self.assertEqual(replay_orchestrator.execute(reference, request, voice_reservation, voice_task), voice_result)
                self.assertEqual(exploding_visual.calls, 0)
                self.assertEqual(exploding_voice.calls, 0)
                self.assertEqual(reopened_attempt.get(visual_reservation.attempt_id).status, "succeeded")
                self.assertEqual(reopened_attempt.get(voice_reservation.attempt_id).status, "succeeded")
            finally:
                reopened_attempt.close()
                reopened_budget.close()

    def test_started_invalid_and_malformed_execution_paths_are_safe_and_nonduplicating(self):
        with TemporaryDirectory() as directory:
            reference, request, authorization, database, workspace_root, budget_repository = self._fixture(directory)
            workspace = FilesystemWorkspace(workspace_root)
            attempt_repository = SQLiteProviderAttemptRepository(database)
            reservation = self._reservation(
                authorization,
                attempt_id="attempt:started",
                operation="visual",
                provider="fake-visual-v1",
            )
            task = VisualGenerationTask(
                authorization.task_id,
                reservation.attempt_id,
                reference,
                "scene-1",
                "9:16",
                30.0,
                "展示小土豆。",
                "挥手。",
                WorkspaceFileReference(authorization.task_id, "media", "started.visual.json"),
            )
            ledger = ProviderAttemptLedger(budget_repository, attempt_repository)
            self.assertIsInstance(ledger.claim(reservation), ProviderAttemptClaim)
            exploding = _ExplodingVisual()
            started_result = ProductionOrchestrator(
                ledger,
                exploding,
                _ExplodingVoice(),
                clock=lambda: self._reserved_at + timedelta(seconds=1),
            ).execute(reference, request, reservation, task)
            self.assertEqual(started_result.code, "ATTEMPT_IN_PROGRESS")
            self.assertEqual(exploding.calls, 0)
            self.assertIsInstance(
                ledger.complete(
                    ProviderAttemptOutcome(
                        reservation.attempt_id,
                        "failed",
                        self._reserved_at + timedelta(seconds=1),
                        0,
                        "TIMEOUT",
                        None,
                        (),
                    )
                ),
                ProviderAttemptRecord,
            )

            invalid_task = VisualGenerationTask(
                task.task_id,
                "attempt:invalid",
                reference,
                task.scene_id,
                task.aspect_ratio,
                task.duration_seconds,
                "changed",
                task.character_action,
                WorkspaceFileReference(task.task_id, "media", "invalid.visual.json"),
            )
            invalid_reservation = self._reservation(
                authorization,
                attempt_id="attempt:invalid",
                operation="visual",
                provider="fake-visual-v1",
            )
            invalid_result = ProductionOrchestrator(
                ledger,
                exploding,
                _ExplodingVoice(),
                clock=lambda: self._reserved_at + timedelta(seconds=1),
            ).execute(reference, request, invalid_reservation, invalid_task)
            self.assertEqual(invalid_result.code, "MEDIA_TASK_MISMATCH")
            self.assertEqual(attempt_repository.get(invalid_reservation.attempt_id).code, "ATTEMPT_NOT_FOUND")

            for index, (mode, attempt_id) in enumerate((("object", "attempt:malformed"), ("raise", "attempt:exception"))):
                scene_id = "scene-1" if index == 0 else "scene-2"
                visual_intent = "展示小土豆。" if scene_id == "scene-1" else "小土豆离开。"
                character_action = "挥手。" if scene_id == "scene-1" else "转身。"
                malformed_reservation = self._reservation(
                    authorization,
                    attempt_id=attempt_id,
                    operation="visual",
                    provider="fake-visual-v1",
                    scene_id=scene_id,
                )
                malformed_task = VisualGenerationTask(
                    authorization.task_id,
                    attempt_id,
                    reference,
                    scene_id,
                    "9:16",
                    30.0,
                    visual_intent,
                    character_action,
                    WorkspaceFileReference(authorization.task_id, "media", f"{attempt_id.replace(':', '-')}.json"),
                )
                adapter = _MalformedVisual(mode)
                malformed_result = ProductionOrchestrator(
                    ledger,
                    adapter,
                    _ExplodingVoice(),
                    clock=lambda: self._reserved_at + timedelta(seconds=1),
                ).execute(reference, request, malformed_reservation, malformed_task)
                self.assertEqual(malformed_result.code, "GENERATION_FAILED")
                self.assertEqual(adapter.calls, 1)
                stored = attempt_repository.get(attempt_id)
                self.assertIsInstance(stored, ProviderAttemptRecord)
                self.assertEqual(stored.status, "failed")
                self.assertEqual(stored.charged_amount_micros, 0)
                self.assertEqual(stored.output_references, ())
                replay_adapter = _ExplodingVisual()
                replay = ProductionOrchestrator(
                    ProviderAttemptLedger(budget_repository, attempt_repository),
                    replay_adapter,
                    _ExplodingVoice(),
                    clock=lambda: self._reserved_at + timedelta(seconds=2),
                ).execute(reference, request, malformed_reservation, malformed_task)
                self.assertEqual(replay.code, "GENERATION_FAILED")
                self.assertEqual(replay_adapter.calls, 0)
            attempt_repository.close()
            budget_repository.close()


if __name__ == "__main__":
    unittest.main()
