"""Public contract tests for deterministic Publish Package building."""

from __future__ import annotations

from dataclasses import fields, replace
import hashlib
import io
import json
from pathlib import Path
import tempfile
from types import MappingProxyType
import unittest
import zipfile

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactCommitBoundary,
    ArtifactReference,
    FinalVideoDecisionBoundary,
    FinalVideoDecisionFailure,
    FinalVideoDecisionRecord,
)
from ai_course_factory.persistence import FilesystemWorkspace, WorkspaceFileReference
from ai_course_factory.packaging import PackagingFailure, PublishPackageBuilder, PublishPackageResult


TASK_ID = "task:episode-1"
SOURCE = ArtifactReference("source_record", "source:episode-1", 1)
REQUEST = ArtifactReference("production_request", "request:episode-1", 1)
TIMELINE = ArtifactReference("timeline", "timeline:episode-1", 1)
CLIP = ArtifactReference("scene_clip", "media:episode-1:scene-1", 1)
SUBTITLE = ArtifactReference("subtitle", "media:episode-1", 1)
MASTER = ArtifactReference("master_audio", "media:episode-1", 1)
VIDEO = ArtifactReference("video", "media:episode-1", 1)
VIDEO_OUTPUT = WorkspaceFileReference(TASK_ID, "media", "composition.mp4")
PACKAGE_OUTPUT = WorkspaceFileReference(TASK_ID, "exports", "episode-1.zip")
MP4_FIXTURE = (
    b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isomiso2"
    b"\x00\x00\x00\x08moov"
    b"\x00\x00\x00\x0fmdatfixture"
)


def _candidate(artifact_type, identity, payload, dependencies=(), commit_id=None):
    return ArtifactCandidate(
        artifact_type,
        identity,
        payload,
        (),
        dependencies,
        True,
        commit_id or f"{artifact_type}-commit-1",
    )


def seed_stores(artifacts, workspace, decision_repository=None, video_bytes=MP4_FIXTURE):
    """Commit one exact source -> video DAG and an approved Final Video decision."""
    source_payload = {
        "source_kind": "github",
        "repository_url": "https://github.com/microsoft/AI-For-Beginners",
        "repository_identity": "microsoft/AI-For-Beginners",
        "commit_sha": "a" * 40,
        "units": ({
            "locator": "microsoft/AI-For-Beginners@" + "a" * 40 + ":README.md#L1-L2",
            "path": "README.md",
            "blob_sha": "b" * 40,
            "heading_path": (),
            "start_line": 1,
            "end_line": 2,
            "text": "# AI Course Factory\n\n",
        },),
    }
    artifacts.commit(_candidate("source_record", SOURCE.identity, source_payload, commit_id="source-commit-1"))
    artifacts.commit(_candidate("production_request", REQUEST.identity, {"kind": "request"}, (SOURCE,), "request-commit-1"))
    artifacts.commit(_candidate("timeline", TIMELINE.identity, {"kind": "timeline"}, (REQUEST,), "timeline-commit-1"))
    artifacts.commit(_candidate("scene_clip", CLIP.identity, {"scene_id": "scene-1"}, (REQUEST,), "clip-commit-1"))
    subtitle_payload = {
        "production_request_reference": REQUEST,
        "timeline_reference": TIMELINE,
        "cues": ({
            "scene_id": "scene-1",
            "start_milliseconds": 0,
            "end_milliseconds": 1000,
            "text": "你好，AI。",
        },),
    }
    artifacts.commit(_candidate("subtitle", SUBTITLE.identity, subtitle_payload, (REQUEST, TIMELINE), "subtitle-commit-1"))
    artifacts.commit(_candidate("master_audio", MASTER.identity, {"duration_milliseconds": 1000}, (REQUEST, TIMELINE), "master-commit-1"))
    video_payload = {
        "production_request_reference": REQUEST,
        "timeline_reference": TIMELINE,
        "composition_id": "composition:episode-1",
        "scene_ids": ("scene-1",),
        "scene_clip_references": (CLIP,),
        "subtitle_reference": SUBTITLE,
        "master_audio_reference": MASTER,
        "composer": "fixture-composer-v1",
        "output_reference": {"task_id": TASK_ID, "area": "media", "name": "composition.mp4"},
        "media_type": "video/mp4",
        "duration_milliseconds": 1000,
    }
    video = artifacts.commit(_candidate("video", VIDEO.identity, video_payload, (REQUEST, TIMELINE, CLIP, SUBTITLE, MASTER), "video-commit-1"))
    if workspace.prepare(TASK_ID).task_id != TASK_ID:
        raise AssertionError("workspace preparation failed")
    if workspace.commit(VIDEO_OUTPUT, video_bytes).size_bytes != len(video_bytes):
        raise AssertionError("video workspace commit failed")
    decision_repository = decision_repository or FinalVideoDecisionBoundary()
    boundary = decision_repository if isinstance(decision_repository, FinalVideoDecisionBoundary) else FinalVideoDecisionBoundary(decision_repository)
    decision = boundary.decide(
        boundary.assess(VIDEO, artifacts.get(video)),
        decision_id="decision-final-1",
        task_id=TASK_ID,
        thread_id="thread:episode-1",
        creator_id="creator-1",
        action="approve",
    )
    if not isinstance(decision, FinalVideoDecisionRecord):
        raise AssertionError(f"decision fixture failed: {decision}")
    return video, decision_repository, decision


class RecordingWorkspace:
    def __init__(self, workspace):
        self.workspace = workspace
        self.reads = 0
        self.commits = 0

    def prepare(self, task_id):
        return self.workspace.prepare(task_id)

    def read(self, reference):
        self.reads += 1
        return self.workspace.read(reference)

    def commit(self, reference, content):
        self.commits += 1
        return self.workspace.commit(reference, content)


class RecordingArtifactRepository:
    def __init__(self, repository):
        self.repository = repository
        self.commits = 0

    def get(self, reference):
        return self.repository.get(reference)

    def commit(self, candidate):
        self.commits += 1
        return self.repository.commit(candidate)


class ForgedManifestRepository:
    def __init__(self, repository):
        self.repository = repository

    def get(self, reference):
        return self.repository.get(reference)

    def commit(self, candidate):
        reference = self.repository.commit(candidate)
        if candidate.artifact_type == "artifact_manifest":
            return replace(reference, version=2)
        return reference


class FailPackageOnceRepository:
    def __init__(self, repository):
        self.repository = repository
        self.failed = False

    def get(self, reference):
        return self.repository.get(reference)

    def commit(self, candidate):
        if candidate.artifact_type == "publish_package" and not self.failed:
            self.failed = True
            raise RuntimeError("injected package failure")
        return self.repository.commit(candidate)


class MutatingRepository:
    def __init__(self, repository, mutate):
        self.repository = repository
        self.mutate = mutate

    def get(self, reference):
        return self.mutate(reference, self.repository.get(reference))

    def commit(self, candidate):
        return self.repository.commit(candidate)


class PublishPackageBuilderTests(unittest.TestCase):
    def _builder(self, repository=None, workspace=None, decisions=None):
        repository = repository or ArtifactCommitBoundary()
        workspace = workspace or RecordingWorkspace(FilesystemWorkspace(Path(tempfile.mkdtemp()) / "workspace"))
        video, decision_store, _decision = seed_stores(repository, workspace, decisions)
        workspace.commits = 0
        repository = RecordingArtifactRepository(repository)
        return repository, workspace, PublishPackageBuilder(repository, decision_store, workspace), video

    def test_public_records_are_frozen_slotted_and_success_has_exact_fields(self):
        self.assertEqual(tuple(field.name for field in fields(PackagingFailure)), ("kind", "code", "message"))
        self.assertEqual(tuple(field.name for field in fields(PublishPackageResult)), (
            "task_id", "source_record_reference", "subtitle_reference", "video_reference",
            "final_video_decision_id", "manifest_reference", "package_reference", "output_reference", "result_code",
        ))
        for record_type in (PackagingFailure, PublishPackageResult):
            self.assertTrue(record_type.__dataclass_params__.frozen)
            self.assertTrue(hasattr(record_type, "__slots__"))

    def test_deterministic_zip_contains_exact_order_and_manifest_without_source_text(self):
        repository, workspace, builder, _video = self._builder()
        result = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:episode-1", manifest_commit_id="manifest-commit-1", package_commit_id="package-commit-1", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(result, PublishPackageResult)
        package = workspace.workspace.read(PACKAGE_OUTPUT)
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            self.assertEqual(archive.namelist(), ["video.mp4", "subtitles.srt", "source-attribution.json", "artifact-manifest.json"])
            for info in archive.infolist():
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual((info.create_system, info.create_version, info.extract_version), (0, 20, 20))
                self.assertEqual((info.compress_type, info.flag_bits, info.external_attr, info.internal_attr), (zipfile.ZIP_STORED, 0, 0o600 << 16, 0))
                self.assertEqual((info.extra, info.comment), (b"", b""))
            self.assertEqual(archive.read("video.mp4"), MP4_FIXTURE)
            self.assertEqual(archive.read("subtitles.srt"), "1\n00:00:00,000 --> 00:00:01,000\n你好，AI。\n".encode("utf-8"))
            attribution = json.loads(archive.read("source-attribution.json"))
            self.assertEqual(attribution["repository_url"], "https://github.com/microsoft/AI-For-Beginners")
            self.assertNotIn("text", json.dumps(attribution, ensure_ascii=False))
            manifest = json.loads(archive.read("artifact-manifest.json"))
            self.assertEqual(manifest["schema_version"], 1)
            self.assertEqual(manifest["task_id"], TASK_ID)
            self.assertEqual([item["name"] for item in manifest["files"]], ["video.mp4", "subtitles.srt", "source-attribution.json"])
            self.assertEqual(manifest["files"][0]["sha256"], hashlib.sha256(MP4_FIXTURE).hexdigest())
        replay = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:episode-1", manifest_commit_id="manifest-commit-1", package_commit_id="package-commit-1", output_reference=PACKAGE_OUTPUT)
        self.assertEqual(replay, result)
        with self.assertRaises(Exception):
            repository.get(ArtifactReference("artifact_manifest", "delivery:episode-1", 2))
        self.assertEqual(workspace.workspace.read(PACKAGE_OUTPUT), package)

    def test_tts_attribution_is_additive_and_preserves_github_source(self):
        repository, workspace, builder, _video = self._builder()
        result = builder.build(
            TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1",
            artifact_identity="delivery:tts-attribution",
            manifest_commit_id="manifest-tts-attribution",
            package_commit_id="package-tts-attribution",
            output_reference=PACKAGE_OUTPUT,
            tts_attribution={
                "engine": "local-gpt-sovits-v2",
                "engine_version": "v2",
                "repository_commit": "d523079fc05d9a8028d6085bffe4a2757c32abb6",
                "model_identifier": "gsv-v2final-pretrained",
                "runtime": "external Python 3.11 + GPT-SoVITS repository",
                "reference_provenance": "locally generated Qwen3-TTS Serena synthetic reference",
                "reference_transcript": "你好，我是小土豆。今天我们一起认识人工智能。",
                "application_provider_api_call": False,
                "external_charge_micros": 0,
            },
        )
        self.assertIsInstance(result, PublishPackageResult)
        package = workspace.workspace.read(PACKAGE_OUTPUT)
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            attribution = json.loads(archive.read("source-attribution.json"))
        self.assertEqual(attribution["repository_url"], "https://github.com/microsoft/AI-For-Beginners")
        self.assertEqual(attribution["tts"]["engine"], "local-gpt-sovits-v2")
        self.assertFalse(attribution["tts"]["application_provider_api_call"])
        self.assertEqual(attribution["tts"]["external_charge_micros"], 0)

    def test_malformed_tts_attribution_fails_before_workspace_or_artifact_side_effects(self):
        for malformed in (
            {
                "engine": "local-gpt-sovits-v2",
                "engine_version": "v2",
                "repository_commit": "d523079fc05d9a8028d6085bffe4a2757c32abb6",
                "model_identifier": "gsv-v2final-pretrained",
                "runtime": "external Python 3.11 + GPT-SoVITS repository",
                "reference_provenance": "locally generated Qwen3-TTS Serena synthetic reference",
                "reference_transcript": "你好，我是小土豆。今天我们一起认识人工智能。",
                "application_provider_api_call": False,
                "external_charge_micros": 0,
                "local_model_path": "/outside/project",
            },
            {
                "engine": "local-gpt-sovits-v2",
                "engine_version": "v2",
                "repository_commit": "d523079fc05d9a8028d6085bffe4a2757c32abb6",
                "model_identifier": "gsv-v2final-pretrained",
                "runtime": "external Python 3.11 + GPT-SoVITS repository",
                "reference_provenance": "locally generated Qwen3-TTS Serena synthetic reference",
                "reference_transcript": "你好，我是小土豆。今天我们一起认识人工智能。",
                "application_provider_api_call": False,
                "external_charge_micros": 1,
            },
        ):
            repository, workspace, builder, _video = self._builder()
            failure = builder.build(
                TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1",
                artifact_identity="delivery:invalid-tts",
                manifest_commit_id="manifest-invalid-tts",
                package_commit_id="package-invalid-tts",
                output_reference=PACKAGE_OUTPUT,
                tts_attribution=malformed,
            )
            self.assertIsInstance(failure, PackagingFailure)
            self.assertEqual(failure.code, "INVALID_TTS_ATTRIBUTION")
            self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))

    def test_approval_lineage_and_media_validation_happen_before_workspace_read(self):
        repository, workspace, builder, _video = self._builder()
        foreign_decision = replace(builder._decisions.get("decision-final-1"), task_id="foreign-task")
        builder._decisions = type("DecisionStore", (), {"get": lambda _self, _id: foreign_decision})()
        failure = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:foreign", manifest_commit_id="manifest-foreign", package_commit_id="package-foreign", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(failure, PackagingFailure)
        self.assertEqual(failure.code, "FINAL_VIDEO_APPROVAL_REQUIRED")
        self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))

    def test_workspace_malformed_video_is_safe(self):
        for label, content in (
            ("bytes", b"malformed"),
            ("missing-moov", b"\x00\x00\x00\x08ftyp\x00\x00\x00\x08mdat"),
            ("missing-mdat", b"\x00\x00\x00\x08ftyp\x00\x00\x00\x08moov"),
        ):
            with self.subTest(label=label):
                repository, workspace, builder, _video = self._builder()
                original_read = workspace.workspace.read
                workspace.workspace.read = lambda reference, value=content: value if reference == VIDEO_OUTPUT else original_read(reference)
                failure = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity=f"delivery:malformed-{label}", manifest_commit_id=f"manifest-malformed-{label}", package_commit_id=f"package-malformed-{label}", output_reference=PACKAGE_OUTPUT)
                self.assertEqual(failure.code, "INVALID_VIDEO_OUTPUT")
                self.assertEqual((workspace.reads, workspace.commits, repository.commits), (1, 0, 0))

    def test_workspace_output_conflict_is_safe(self):
        repository, workspace, builder, _video = self._builder()
        self.assertEqual(workspace.workspace.commit(PACKAGE_OUTPUT, b"changed").size_bytes, 7)
        failure = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:conflict", manifest_commit_id="manifest-conflict", package_commit_id="package-conflict", output_reference=PACKAGE_OUTPUT)
        self.assertEqual(failure.code, "PACKAGE_OUTPUT_CONFLICT")
        self.assertEqual(workspace.workspace.read(PACKAGE_OUTPUT), b"changed")

    def test_forged_manifest_reference_is_rejected_after_commit_and_package_is_not_created(self):
        repository = ArtifactCommitBoundary()
        workspace = RecordingWorkspace(FilesystemWorkspace(Path(tempfile.mkdtemp()) / "workspace"))
        video, decisions, _decision = seed_stores(repository, workspace)
        forged = ForgedManifestRepository(repository)
        builder = PublishPackageBuilder(forged, decisions, workspace)
        failure = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:forged", manifest_commit_id="manifest-forged", package_commit_id="package-forged", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(failure, PackagingFailure)
        self.assertEqual(failure.code, "MANIFEST_COMMIT_FAILED")
        with self.assertRaises(Exception):
            repository.get(ArtifactReference("publish_package", "delivery:forged", 1))

    def test_exact_mutations_and_mp4_box_requirements_fail_before_side_effects(self):
        repository, workspace, builder, _video = self._builder()

        class EvilString(str):
            def __eq__(self, _other):
                return True
            __hash__ = str.__hash__

        for label, task_id, output in (
            ("task-subclass", EvilString(TASK_ID), PACKAGE_OUTPUT),
            ("area-subclass", TASK_ID, WorkspaceFileReference(TASK_ID, EvilString("exports"), "episode-evil.zip")),
            ("name-subclass", TASK_ID, WorkspaceFileReference(TASK_ID, "exports", EvilString("episode-evil.zip"))),
            ("non-zip", TASK_ID, WorkspaceFileReference(TASK_ID, "exports", "episode-evil.mp4")),
        ):
            invalid_output = builder.build(task_id, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity=f"delivery:{label}", manifest_commit_id=f"manifest-{label}", package_commit_id=f"package-{label}", output_reference=output)
            self.assertIsInstance(invalid_output, PackagingFailure)
            self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))

        repository, workspace, _builder, _video = self._builder()
        source_version = repository.get(SOURCE)
        evil_source = replace(source_version, payload=MappingProxyType({EvilString(key): value for key, value in source_version.payload.items()}))
        mutated_repository = MutatingRepository(repository, lambda reference, version: evil_source if reference == SOURCE else version)
        mutated_builder = PublishPackageBuilder(mutated_repository, _builder._decisions, workspace)
        failure = mutated_builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:evil-source", manifest_commit_id="manifest-evil-source", package_commit_id="package-evil-source", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(failure, PackagingFailure)
        self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))
        request_version = repository.get(REQUEST)
        evil_reference = ArtifactReference(EvilString("source_record"), EvilString(SOURCE.identity), 1)
        evil_request = replace(request_version, dependencies=(evil_reference,))
        mutated_repository = MutatingRepository(repository, lambda reference, version: evil_request if reference == REQUEST else version)
        mutated_builder = PublishPackageBuilder(mutated_repository, _builder._decisions, workspace)
        failure = mutated_builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:evil-lineage", manifest_commit_id="manifest-evil-lineage", package_commit_id="package-evil-lineage", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(failure, PackagingFailure)
        self.assertEqual(failure.code, "SOURCE_LINEAGE_MISMATCH")
        self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))

        subtitle_version = repository.get(SUBTITLE)
        cue = MappingProxyType({**subtitle_version.payload["cues"][0], "text": "bad\x7f"})
        bad_subtitle = replace(subtitle_version, payload=MappingProxyType({**subtitle_version.payload, "cues": (cue,)}))
        mutated_repository = MutatingRepository(repository, lambda reference, version: bad_subtitle if reference == SUBTITLE else version)
        mutated_builder = PublishPackageBuilder(mutated_repository, _builder._decisions, workspace)
        failure = mutated_builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:bad-del", manifest_commit_id="manifest-bad-del", package_commit_id="package-bad-del", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(failure, PackagingFailure)
        self.assertEqual(failure.code, "INVALID_SUBTITLE")
        self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))

    def test_manifest_and_package_payloads_are_literal_and_staged_package_retry_is_safe(self):
        repository, workspace, builder, _video = self._builder()
        result = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:literal", manifest_commit_id="manifest-literal", package_commit_id="package-literal", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(result, PublishPackageResult)
        manifest = repository.get(result.manifest_reference)
        package = repository.get(result.package_reference)
        expected_srt = "1\n00:00:00,000 --> 00:00:01,000\n你好，AI。\n".encode()
        expected_attribution = json.dumps({
            "commit_sha": "a" * 40, "repository_identity": "microsoft/AI-For-Beginners",
            "repository_url": "https://github.com/microsoft/AI-For-Beginners",
            "units": [{"blob_sha": "b" * 40, "end_line": 2, "locator": "microsoft/AI-For-Beginners@" + "a" * 40 + ":README.md#L1-L2", "path": "README.md", "start_line": 1}],
        }, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        self.assertEqual(manifest.reference.version, 1)
        self.assertEqual(manifest.reference, ArtifactReference("artifact_manifest", "delivery:literal", 1))
        self.assertEqual(set(manifest.payload), {"schema_version", "task_id", "source_record_reference", "subtitle_reference", "video_reference", "final_video_decision_id", "files"})
        self.assertEqual(dict(manifest.payload), {
            "schema_version": 1, "task_id": TASK_ID,
            "source_record_reference": SOURCE, "subtitle_reference": SUBTITLE, "video_reference": VIDEO,
            "final_video_decision_id": "decision-final-1",
            "files": manifest.payload["files"],
        })
        self.assertEqual(tuple(manifest.payload["files"]), (
            {"name": "video.mp4", "media_type": "video/mp4", "size_bytes": len(MP4_FIXTURE), "sha256": hashlib.sha256(MP4_FIXTURE).hexdigest()},
            {"name": "subtitles.srt", "media_type": "application/x-subrip", "size_bytes": len(expected_srt), "sha256": hashlib.sha256(expected_srt).hexdigest()},
            {"name": "source-attribution.json", "media_type": "application/json", "size_bytes": len(expected_attribution), "sha256": hashlib.sha256(expected_attribution).hexdigest()},
        ))
        self.assertEqual(set(manifest.provenance[0]), {"purpose", "task_id", "final_video_decision_id"})
        self.assertEqual(dict(manifest.provenance[0]), {"purpose": "publish_package_manifest", "task_id": TASK_ID, "final_video_decision_id": "decision-final-1"})
        self.assertEqual(manifest.dependencies, (SOURCE, SUBTITLE, VIDEO))
        self.assertEqual((manifest.commit_id, manifest.prior_reference), ("manifest-literal", None))
        self.assertEqual(package.reference.version, 1)
        self.assertEqual(package.reference, ArtifactReference("publish_package", "delivery:literal", 1))
        self.assertEqual(set(package.payload), {"manifest_reference", "source_record_reference", "subtitle_reference", "video_reference", "final_video_decision_id", "output_reference", "format"})
        self.assertEqual(package.payload["manifest_reference"], result.manifest_reference)
        self.assertEqual(dict(package.payload), {
            "manifest_reference": result.manifest_reference, "source_record_reference": SOURCE,
            "subtitle_reference": SUBTITLE, "video_reference": VIDEO, "final_video_decision_id": "decision-final-1",
            "output_reference": {"task_id": TASK_ID, "area": "exports", "name": "episode-1.zip"}, "format": "zip",
        })
        self.assertEqual(set(package.provenance[0]), {"purpose", "task_id", "manifest_reference", "final_video_decision_id"})
        self.assertEqual(dict(package.provenance[0]), {"purpose": "publish_package", "task_id": TASK_ID, "manifest_reference": result.manifest_reference, "final_video_decision_id": "decision-final-1"})
        self.assertEqual(package.dependencies, (result.manifest_reference, SOURCE, SUBTITLE, VIDEO))
        self.assertEqual((package.commit_id, package.prior_reference), ("package-literal", None))
        original_bytes = workspace.workspace.read(PACKAGE_OUTPUT)
        failing_repo = FailPackageOnceRepository(repository)
        retry_output = WorkspaceFileReference(TASK_ID, "exports", "retry-package.zip")
        failed = PublishPackageBuilder(failing_repo, builder._decisions, workspace).build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:retry-package", manifest_commit_id="manifest-retry-package", package_commit_id="package-retry-package", output_reference=retry_output)
        self.assertIsInstance(failed, PackagingFailure)
        self.assertEqual(failed.code, "PACKAGE_COMMIT_FAILED")
        staged_manifest = repository.get(ArtifactReference("artifact_manifest", "delivery:retry-package", 1))
        self.assertEqual((staged_manifest.reference.version, staged_manifest.commit_id), (1, "manifest-retry-package"))
        retry_bytes = workspace.workspace.read(retry_output)
        recovered = PublishPackageBuilder(repository, builder._decisions, workspace).build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:retry-package", manifest_commit_id="manifest-retry-package", package_commit_id="package-retry-package", output_reference=retry_output)
        self.assertIsInstance(recovered, PublishPackageResult)
        self.assertEqual(recovered.manifest_reference, staged_manifest.reference)
        self.assertEqual(workspace.workspace.read(retry_output), retry_bytes)
        with self.assertRaises(Exception): repository.get(ArtifactReference("artifact_manifest", "delivery:retry-package", 2))
        with self.assertRaises(Exception): repository.get(ArtifactReference("publish_package", "delivery:retry-package", 2))
        self.assertEqual(workspace.workspace.read(PACKAGE_OUTPUT), original_bytes)

    def test_reused_commit_ids_with_changed_inputs_conflict_without_v2(self):
        repository, workspace, builder, _video = self._builder()
        first = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:conflict-input", manifest_commit_id="manifest-conflict-input", package_commit_id="package-conflict-input", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(first, PublishPackageResult)
        original_manifest = repository.get(first.manifest_reference)
        original_decision = builder._decisions.get("decision-final-1")
        builder._decisions = type("DecisionStore", (), {"get": lambda _self, _id: replace(original_decision, decision_id="decision-final-2")})()
        conflict = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-2", artifact_identity="delivery:conflict-input", manifest_commit_id="manifest-conflict-input", package_commit_id="package-conflict-input", output_reference=WorkspaceFileReference(TASK_ID, "exports", "conflict-input-2.zip"))
        self.assertIsInstance(conflict, PackagingFailure)
        self.assertEqual(conflict.code, "MANIFEST_COMMIT_CONFLICT")
        with self.assertRaises(Exception):
            repository.get(ArtifactReference("artifact_manifest", "delivery:conflict-input", 2))
        with self.assertRaises(Exception):
            repository.get(ArtifactReference("publish_package", "delivery:conflict-input", 2))
        preserved_manifest = repository.get(first.manifest_reference)
        self.assertEqual((preserved_manifest.reference, preserved_manifest.payload, preserved_manifest.provenance, preserved_manifest.dependencies, preserved_manifest.commit_id, preserved_manifest.prior_reference), (original_manifest.reference, original_manifest.payload, original_manifest.provenance, original_manifest.dependencies, original_manifest.commit_id, original_manifest.prior_reference))
        repository, workspace, builder, _video = self._builder()
        first = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:package-conflict", manifest_commit_id="manifest-package-conflict", package_commit_id="package-package-conflict", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(first, PublishPackageResult)
        original_package = repository.get(first.package_reference)
        package_conflict = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:package-conflict", manifest_commit_id="manifest-package-conflict", package_commit_id="package-package-conflict", output_reference=WorkspaceFileReference(TASK_ID, "exports", "package-conflict-2.zip"))
        self.assertIsInstance(package_conflict, PackagingFailure)
        self.assertEqual(package_conflict.code, "PACKAGE_COMMIT_CONFLICT")
        with self.assertRaises(Exception):
            repository.get(ArtifactReference("publish_package", "delivery:package-conflict", 2))
        preserved_package = repository.get(first.package_reference)
        self.assertEqual((preserved_package.reference, preserved_package.payload, preserved_package.provenance, preserved_package.dependencies, preserved_package.commit_id, preserved_package.prior_reference), (original_package.reference, original_package.payload, original_package.provenance, original_package.dependencies, original_package.commit_id, original_package.prior_reference))

    def test_decision_reject_hard_block_revise_malformed_and_storage_fail_before_read(self):
        for label, mutate in (
            ("invalid-input", lambda record: record),
            ("reject", lambda record: replace(record, action="reject", decision_context="reject")),
            ("revise", lambda record: replace(record, action="revise", decision_context="revise")),
            ("hard", lambda record: replace(record, assessment_disposition="hard_block", finding_codes=("VIDEO_BLOCK",), action="reject", decision_context="blocked")),
            ("malformed", lambda record: FinalVideoDecisionFailure("validation", "DECISION_NOT_FOUND", "missing")),
        ):
            with self.subTest(label=label):
                repository, workspace, builder, _video = self._builder()
                original = builder._decisions.get("decision-final-1")
                forged = mutate(original)
                builder._decisions = type("DecisionStore", (), {"get": lambda _self, _id, value=forged: value})()
                task_id = "" if label == "invalid-input" else TASK_ID
                result = builder.build(task_id, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity=f"delivery:decision-{label}", manifest_commit_id=f"manifest-decision-{label}", package_commit_id=f"package-decision-{label}", output_reference=PACKAGE_OUTPUT)
                self.assertIsInstance(result, PackagingFailure)
                self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))
        repository, workspace, builder, _video = self._builder()
        builder._decisions = type("DecisionStore", (), {"get": lambda _self, _id: (_ for _ in ()).throw(RuntimeError("storage"))})()
        result = builder.build(TASK_ID, SOURCE, SUBTITLE, VIDEO, "decision-final-1", artifact_identity="delivery:decision-storage", manifest_commit_id="manifest-decision-storage", package_commit_id="package-decision-storage", output_reference=PACKAGE_OUTPUT)
        self.assertIsInstance(result, PackagingFailure)
        self.assertEqual((workspace.reads, workspace.commits, repository.commits), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
