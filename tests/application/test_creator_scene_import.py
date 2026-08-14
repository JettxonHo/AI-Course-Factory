from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import sqlite3
import shutil
import subprocess
import unittest

from ai_course_factory.application import CourseFactoryApplication
from ai_course_factory.artifacts import ArtifactReference, ArtifactVersion
from ai_course_factory.production import CreatorImportedFinalCandidateGate, CreatorImportedFinalCandidateGateResult, ProductionMediaFailure

from tests.source_fixture import FixtureSourceConnector, SUPPORTED_REPOSITORY_URL
from tests.integration.test_handoff_package import _FFmpegNarrationRenderer, _PNG


def _creator_gate_fixture(*, mixed_clip: int | None = None, output_name_mutation: int | None = None):
    request = ArtifactReference("production_request", "request:episode-1", 1)
    timeline = ArtifactReference("timeline", "timeline:episode-1", 1)
    contract = ArtifactReference("scene_generation_contract", "contract:episode-1", 1)
    subtitle = ArtifactReference("subtitle", "media:episode-1", 1)
    master_audio = ArtifactReference("master_audio", "media:episode-1", 1)
    clip_refs = tuple(ArtifactReference("scene_clip", f"media:episode-1:scene-{index}", 1) for index in range(1, 7))
    versions: dict[ArtifactReference, ArtifactVersion] = {
        contract: ArtifactVersion(
            contract,
            {
                "production_request_reference": request,
                "timeline_reference": timeline,
                "scene_generation_contract": {
                    "scenes": tuple({"scene_id": f"scene-{index}", "duration_milliseconds": 10_000, "expected_filename": f"scene-{index}.mp4"} for index in range(1, 7)),
                },
            },
            (),
            (),
            "contract-1",
        )
    }
    for index, reference in enumerate(clip_refs, start=1):
        filename = f"scene-{index}.mp4"
        if output_name_mutation == index:
            filename = f"scene-{index}-forged.mp4"
        versions[reference] = ArtifactVersion(
            reference,
            {
                "source_kind": "legacy_attempt" if mixed_clip == index else "creator_import",
                "production_request_reference": request,
                "scene_generation_contract_reference": contract,
                "scene_id": f"scene-{index}",
                "declared_filename": f"scene-{index}.mp4",
                "creator_provenance": {
                    "supplied_by": "creator",
                    "generated_outside_application": True,
                    "application_provider_attempt": False,
                    "application_charge_micros": 0,
                    "native_audio/subtitles/effects": "metadata_only",
                },
                "output_reference": {"task_id": "demo-episode-01", "area": "media", "name": filename},
                "media_type": "video/mp4",
                "duration_milliseconds": 10_000,
            },
            (),
            (request,) if mixed_clip == index else (request, contract),
            f"clip-{index}",
        )
    video = ArtifactReference("video", "media:episode-1", 1)
    versions[video] = ArtifactVersion(
        video,
        {
            "production_request_reference": request,
            "timeline_reference": timeline,
            "composition_id": "composition:episode-1",
            "scene_ids": tuple(f"scene-{index}" for index in range(1, 7)),
            "scene_clip_references": clip_refs,
            "subtitle_reference": subtitle,
            "master_audio_reference": master_audio,
            "composer": "ffmpeg",
            "output_reference": {"task_id": "demo-episode-01", "area": "media", "name": "composition.mp4"},
            "media_type": "video/mp4",
            "duration_milliseconds": 60_000,
        },
        (),
        (request, timeline, *clip_refs, subtitle, master_audio),
        "video-1",
    )

    class Repository:
        def get(self, reference: ArtifactReference) -> ArtifactVersion:
            return versions[reference]

    return Repository(), video, contract


class CreatorSceneImportApplicationTests(unittest.TestCase):
    def test_invalid_full_set_is_a_safe_public_failure_with_no_media_side_effect(self) -> None:
        ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
        with TemporaryDirectory() as directory, TemporaryDirectory() as still_directory:
            clips = Path(directory) / "generated-clips"
            clips.mkdir()
            stills = Path(still_directory)
            for index in range(1, 7):
                (stills / f"scene-{index}.png").write_bytes(_PNG)
            app = CourseFactoryApplication(
                Path(directory) / "data",
                source_connector=FixtureSourceConnector(),
                generated_clips_directory=clips,
                visual_import_dir=stills,
            )
            app.local_narration_renderer = _FFmpegNarrationRenderer(app.workspace, ffmpeg, ffprobe)
            app.start_source(SUPPORTED_REPOSITORY_URL)
            app.submit_script_decision("approve")
            app.advance_planning()
            app.submit_storyboard_decision("approve")
            self.assertEqual(app.prepare_handoff_package().status, "success")

            result = app.import_generated_scene_clips()

            self.assertEqual(result.status, "failure")
            self.assertTrue(result.error_code)
            self.assertIn("scene-1.mp4", result.error_message)
            self.assertIn("scene-6.mp4", result.error_message)
            self.assertNotIn(str(clips), result.error_message)
            self.assertIsNotNone(result.view)
            with sqlite3.connect(Path(directory) / "data" / "factory.sqlite3") as connection:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM artifact_versions WHERE artifact_type IN ('scene_clip', 'video')").fetchone()[0],
                    0,
                )
            app.close()

    def test_mixed_legacy_clip_set_is_rejected_before_final_review(self) -> None:
        repository, video, contract = _creator_gate_fixture(mixed_clip=4)

        result = CreatorImportedFinalCandidateGate(repository).validate(video, contract)

        self.assertIsInstance(result, ProductionMediaFailure)
        assert isinstance(result, ProductionMediaFailure)
        self.assertEqual(result.code, "CREATOR_FINAL_GATE_LINEAGE_MISMATCH")

    def test_creator_import_final_gate_accepts_complete_valid_fixture(self) -> None:
        repository, video, contract = _creator_gate_fixture()

        result = CreatorImportedFinalCandidateGate(repository).validate(video, contract)

        self.assertIsInstance(result, CreatorImportedFinalCandidateGateResult)
        assert isinstance(result, CreatorImportedFinalCandidateGateResult)
        self.assertEqual(result.result_code, "SUCCESS")

    def test_creator_import_final_gate_rejects_clip_output_name_mutation(self) -> None:
        repository, video, contract = _creator_gate_fixture(output_name_mutation=3)

        result = CreatorImportedFinalCandidateGate(repository).validate(video, contract)

        self.assertIsInstance(result, ProductionMediaFailure)
        assert isinstance(result, ProductionMediaFailure)
        self.assertEqual(result.code, "CREATOR_FINAL_GATE_LINEAGE_MISMATCH")

    def test_h2_local_narration_without_attempt_enters_committed_composition(self) -> None:
        ffmpeg = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
        ffprobe = shutil.which("ffprobe") or "/opt/homebrew/bin/ffprobe"
        with TemporaryDirectory() as directory, TemporaryDirectory() as still_directory:
            root = Path(directory)
            clips = root / "generated-clips"
            clips.mkdir()
            stills = Path(still_directory)
            for index in range(1, 7):
                (stills / f"scene-{index}.png").write_bytes(_PNG)
                completed = subprocess.run(
                    [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "color=c=blue:s=540x960:r=24:d=10", "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "24", str(clips / f"scene-{index}.mp4")],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8", "replace"))
            app = CourseFactoryApplication(root / "data", source_connector=FixtureSourceConnector(), generated_clips_directory=clips, visual_import_dir=stills)
            app.local_narration_renderer = _FFmpegNarrationRenderer(app.workspace, ffmpeg, ffprobe)
            self.assertEqual(app.start_source(SUPPORTED_REPOSITORY_URL).status, "success")
            self.assertEqual(app.submit_script_decision("approve").status, "success")
            self.assertEqual(app.advance_planning().status, "success")
            self.assertEqual(app.submit_storyboard_decision("approve").status, "success")
            self.assertEqual(app.prepare_handoff_package().status, "success")

            imported = app.import_generated_scene_clips()

            self.assertEqual(imported.status, "success", imported.error_message)
            self.assertEqual(imported.view.stage, "final_review")
            self.assertEqual(imported.view.visual_mode, "creator_import")
            self.assertEqual(len(imported.view.scenes), 6)
            for scene in imported.view.scenes:
                self.assertIsNotNone(scene.selected_audio_reference)
                audio = app.artifacts.get(scene.selected_audio_reference)
                self.assertEqual(audio.payload["source_kind"], "local_narration")
                self.assertNotIn("attempt_id", audio.payload)
                self.assertNotIn("provider", audio.payload)
                self.assertEqual(len(audio.dependencies), 3)
            with sqlite3.connect(root / "data" / "factory.sqlite3") as connection:
                attempts = connection.execute("SELECT COUNT(*) FROM provider_attempts").fetchone()[0]
                self.assertEqual(attempts, 0)
            app.close()


if __name__ == "__main__":
    unittest.main()
