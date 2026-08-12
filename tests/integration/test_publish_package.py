"""Durable SQLite + Filesystem evidence for the approved-video package."""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zipfile

from ai_course_factory.artifacts import (
    ArtifactNotFoundError,
    ArtifactReference,
    FinalVideoDecisionFailure,
    SQLiteArtifactRepository,
    SQLiteFinalVideoDecisionRepository,
)
from ai_course_factory.packaging import PackagingFailure, PublishPackageBuilder, PublishPackageResult
from ai_course_factory.persistence import FilesystemWorkspace

from tests.test_packaging_builder import (
    PACKAGE_OUTPUT,
    SOURCE,
    SUBTITLE,
    TASK_ID,
    VIDEO,
    seed_stores,
)


class FailManifestOnceRepository:
    def __init__(self, repository):
        self.repository = repository
        self.failed = False

    def get(self, reference):
        return self.repository.get(reference)

    def commit(self, candidate):
        if candidate.artifact_type == "artifact_manifest" and not self.failed:
            self.failed = True
            raise RuntimeError("injected manifest failure")
        return self.repository.commit(candidate)


class PublishPackageIntegrationTests(unittest.TestCase):
    @staticmethod
    def _playable_video(root: Path) -> bytes:
        executable = "/opt/homebrew/bin/ffmpeg"
        if not Path(executable).exists():
            executable = shutil.which("ffmpeg") or ""
        if not executable:
            raise unittest.SkipTest("ffmpeg is unavailable")
        output = root / "fixture.mp4"
        subprocess.run(
            [
                executable,
                "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "color=c=blue:s=540x960:r=24:d=1",
                "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                str(output),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return output.read_bytes()

    def test_sqlite_restart_independent_zip_parse_replay_and_staged_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "factory.sqlite3"
            workspace_root = root / "workspace"
            playable = self._playable_video(root)
            artifacts = SQLiteArtifactRepository(database)
            decisions = SQLiteFinalVideoDecisionRepository(database)
            workspace = FilesystemWorkspace(workspace_root)
            video, _decision_store, decision = seed_stores(artifacts, workspace, decisions, playable)
            self.assertEqual(decision.action, "approve")
            builder = PublishPackageBuilder(artifacts, decisions, workspace)
            first = builder.build(
                TASK_ID, SOURCE, SUBTITLE, VIDEO, decision.decision_id,
                artifact_identity="delivery:episode-1",
                manifest_commit_id="manifest-commit-1",
                package_commit_id="package-commit-1",
                output_reference=PACKAGE_OUTPUT,
            )
            self.assertIsInstance(first, PublishPackageResult)
            package = workspace.read(PACKAGE_OUTPUT)
            self.assertIsInstance(package, bytes)
            with zipfile.ZipFile(io.BytesIO(package)) as archive:
                self.assertEqual(archive.namelist(), ["video.mp4", "subtitles.srt", "source-attribution.json", "artifact-manifest.json"])
                self.assertEqual(archive.read("video.mp4"), playable)
                self.assertEqual(archive.read("subtitles.srt"), "1\n00:00:00,000 --> 00:00:01,000\n你好，AI。\n".encode("utf-8"))
                attribution = json.loads(archive.read("source-attribution.json"))
                self.assertEqual(attribution["repository_identity"], "microsoft/AI-For-Beginners")
                self.assertNotIn("AI Course Factory", json.dumps(attribution, ensure_ascii=False))
                manifest = json.loads(archive.read("artifact-manifest.json"))
                self.assertEqual(manifest["final_video_decision_id"], decision.decision_id)
                entries = {item["name"]: item for item in manifest["files"]}
                self.assertEqual(set(entries), {"video.mp4", "subtitles.srt", "source-attribution.json"})
                for name, fact in entries.items():
                    content = archive.read(name)
                    self.assertEqual(fact["size_bytes"], len(content))
                    self.assertEqual(fact["sha256"], hashlib.sha256(content).hexdigest())

            # Parse the delivered video independently with ffprobe and retain byte equality.
            ffprobe = "/opt/homebrew/bin/ffprobe"
            if not Path(ffprobe).exists():
                ffprobe = shutil.which("ffprobe") or ""
            if ffprobe:
                materialized = root / "from-package.mp4"
                materialized.write_bytes(playable)
                probe = subprocess.run(
                    [ffprobe, "-v", "error", "-show_entries", "format=format_name", "-of", "default=nw=1", str(materialized)],
                    check=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ).stdout.decode("utf-8")
                self.assertIn("format_name=mov,mp4", probe)

            artifacts.close()
            decisions.close()
            reopened_artifacts = SQLiteArtifactRepository(database)
            reopened_decisions = SQLiteFinalVideoDecisionRepository(database)
            reopened_workspace = FilesystemWorkspace(workspace_root)
            try:
                replay = PublishPackageBuilder(reopened_artifacts, reopened_decisions, reopened_workspace).build(
                    TASK_ID, SOURCE, SUBTITLE, VIDEO, decision.decision_id,
                    artifact_identity="delivery:episode-1",
                    manifest_commit_id="manifest-commit-1",
                    package_commit_id="package-commit-1",
                    output_reference=PACKAGE_OUTPUT,
                )
                self.assertEqual(replay, first)
                self.assertEqual(reopened_workspace.read(PACKAGE_OUTPUT), package)
                with self.assertRaises(ArtifactNotFoundError):
                    reopened_artifacts.get(ArtifactReference("artifact_manifest", "delivery:episode-1", 2))
                with self.assertRaises(ArtifactNotFoundError):
                    reopened_artifacts.get(ArtifactReference("publish_package", "delivery:episode-1", 2))
            finally:
                reopened_artifacts.close()
                reopened_decisions.close()

            # A staged Manifest failure is retryable without rewriting the immutable ZIP.
            retry_artifacts = SQLiteArtifactRepository(database)
            retry_decisions = SQLiteFinalVideoDecisionRepository(database)
            retry_workspace = FilesystemWorkspace(workspace_root)
            try:
                failing = FailManifestOnceRepository(retry_artifacts)
                failed = PublishPackageBuilder(failing, retry_decisions, retry_workspace).build(
                    TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1",
                    artifact_identity="delivery:retry",
                    manifest_commit_id="manifest-retry",
                    package_commit_id="package-retry",
                    output_reference=PACKAGE_OUTPUT,
                )
                self.assertIsInstance(failed, PackagingFailure)
                self.assertEqual(failed.code, "MANIFEST_COMMIT_FAILED")
                self.assertEqual(retry_workspace.read(PACKAGE_OUTPUT), package)
                recovered = PublishPackageBuilder(retry_artifacts, retry_decisions, retry_workspace).build(
                    TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1",
                    artifact_identity="delivery:retry",
                    manifest_commit_id="manifest-retry",
                    package_commit_id="package-retry",
                    output_reference=PACKAGE_OUTPUT,
                )
                self.assertIsInstance(recovered, PublishPackageResult)
                self.assertEqual(retry_workspace.read(PACKAGE_OUTPUT), package)
            finally:
                retry_artifacts.close()
                retry_decisions.close()


if __name__ == "__main__":
    unittest.main()
