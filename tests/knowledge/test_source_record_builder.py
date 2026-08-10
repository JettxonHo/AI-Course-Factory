"""Public behavior tests for the Source Record Candidate boundary."""

import unittest
from dataclasses import replace

from ai_course_factory.artifacts.commit import (
    ArtifactCommitBoundary,
    CommitConflictError,
)
from ai_course_factory.artifacts.model import ArtifactCandidate
from ai_course_factory.knowledge.normalization import (
    NormalizedSourceMaterial,
    NormalizedSourceUnit,
)
from ai_course_factory.knowledge.source_record import SourceRecordBuilder, SourceRecordFailure


COMMIT_SHA = "a" * 40
README_BLOB_SHA = "b" * 40
LESSON_BLOB_SHA = "c" * 40
REPOSITORY_URL = "https://github.com/acme/course"
REPOSITORY_IDENTITY = "acme/course"


def normalized_material() -> NormalizedSourceMaterial:
    return NormalizedSourceMaterial(
        repository_url=REPOSITORY_URL,
        repository_identity=REPOSITORY_IDENTITY,
        commit_sha=COMMIT_SHA,
        units=(
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L1-L2",
                path="README.md",
                blob_sha=README_BLOB_SHA,
                heading_path=("Course",),
                start_line=1,
                end_line=2,
                text="# Course\nOverview text.\n",
            ),
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:lessons/intro.md#L1-L2",
                path="lessons/intro.md",
                blob_sha=LESSON_BLOB_SHA,
                heading_path=("Lesson 1",),
                start_line=1,
                end_line=2,
                text="# Lesson 1\nLearn AI.\n",
            ),
        ),
        diagnostics=("source_files=2", "normalized_units=2", "total_bytes=38"),
    )


class SourceRecordBuilderTests(unittest.TestCase):
    def test_accepted_material_returns_validated_source_record_candidate(self):
        candidate = SourceRecordBuilder().build(
            normalized_material(),
            identity="source:acme-course",
            commit_id="source-record-1",
        )

        self.assertIsInstance(candidate, ArtifactCandidate)
        self.assertEqual(candidate.artifact_type, "source_record")
        self.assertEqual(candidate.identity, "source:acme-course")
        self.assertEqual(candidate.commit_id, "source-record-1")
        self.assertTrue(candidate.validated)
        self.assertEqual(candidate.dependencies, ())
        self.assertEqual(
            candidate.payload,
            {
                "source_kind": "github",
                "repository_url": REPOSITORY_URL,
                "repository_identity": REPOSITORY_IDENTITY,
                "commit_sha": COMMIT_SHA,
                "units": (
                    {
                        "locator": f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L1-L2",
                        "path": "README.md",
                        "blob_sha": README_BLOB_SHA,
                        "heading_path": ("Course",),
                        "start_line": 1,
                        "end_line": 2,
                        "text": "# Course\nOverview text.\n",
                    },
                    {
                        "locator": f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:lessons/intro.md#L1-L2",
                        "path": "lessons/intro.md",
                        "blob_sha": LESSON_BLOB_SHA,
                        "heading_path": ("Lesson 1",),
                        "start_line": 1,
                        "end_line": 2,
                        "text": "# Lesson 1\nLearn AI.\n",
                    },
                ),
            },
        )
        self.assertEqual(
            candidate.provenance,
            (
                {
                    "repository_url": REPOSITORY_URL,
                    "repository_identity": REPOSITORY_IDENTITY,
                    "commit_sha": COMMIT_SHA,
                },
                {"locator": f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L1-L2"},
                {"locator": f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:lessons/intro.md#L1-L2"},
            ),
        )

    def test_candidate_commits_as_exact_immutable_reference_and_replays_idempotently(self):
        boundary = ArtifactCommitBoundary()
        builder = SourceRecordBuilder()
        candidate = builder.build(
            normalized_material(),
            identity="source:acme-course",
            commit_id="source-record-1",
        )

        reference = boundary.commit(candidate)
        self.assertEqual(reference.artifact_type, "source_record")
        self.assertEqual(reference.identity, "source:acme-course")
        self.assertEqual(reference.version, 1)
        committed = boundary.get(reference)
        self.assertEqual(committed.payload["commit_sha"], COMMIT_SHA)
        self.assertEqual(committed.payload["units"][1]["text"], "# Lesson 1\nLearn AI.\n")

        candidate.payload["units"][0]["text"] = "mutated after candidate creation"
        self.assertEqual(boundary.get(reference).payload["units"][0]["text"], "# Course\nOverview text.\n")

        replay = boundary.commit(
            builder.build(
                normalized_material(),
                identity="source:acme-course",
                commit_id="source-record-1",
            )
        )
        self.assertEqual(replay, reference)
        with self.assertRaises(CommitConflictError):
            boundary.commit(
                builder.build(
                    replace(
                        normalized_material(),
                        units=(
                            replace(normalized_material().units[0], text="# Changed\nOverview text.\n"),
                            normalized_material().units[1],
                        ),
                    ),
                    identity="source:acme-course",
                    commit_id="source-record-1",
                )
            )

    def test_invalid_material_provenance_and_explicit_identities_fail_without_candidate(self):
        builder = SourceRecordBuilder()
        valid = normalized_material()
        cases = (
            ("INVALID_INPUT_TYPE", object()),
            ("REPOSITORY_IDENTITY_MISMATCH", replace(valid, repository_url="https://github.com/other/course")),
            ("INVALID_COMMIT_SHA", replace(valid, commit_sha="not-a-sha")),
            (
                "INVALID_SOURCE_PATH",
                replace(valid, units=(replace(valid.units[0], path="../README.md"), valid.units[1])),
            ),
            (
                "INVALID_BLOB_SHA",
                replace(valid, units=(replace(valid.units[0], blob_sha="bad"), valid.units[1])),
            ),
            (
                "INVALID_UNIT_LOCATOR",
                replace(valid, units=(replace(valid.units[0], locator="wrong-locator"), valid.units[1])),
            ),
            (
                "NON_CONTIGUOUS_LINES",
                replace(valid, units=(replace(valid.units[0], end_line=3), valid.units[1])),
            ),
            ("INVALID_ARTIFACT_IDENTITY", valid),
            ("INVALID_COMMIT_ID", valid),
        )
        for expected_code, material in cases:
            with self.subTest(expected_code=expected_code):
                kwargs = {
                    "identity": "source:acme-course",
                    "commit_id": "source-record-1",
                }
                if expected_code == "INVALID_ARTIFACT_IDENTITY":
                    kwargs["identity"] = ""
                if expected_code == "INVALID_COMMIT_ID":
                    kwargs["commit_id"] = ""
                failure = builder.build(material, **kwargs)
                self.assertIsInstance(failure, SourceRecordFailure)
                self.assertEqual(failure.kind, "validation")
                self.assertEqual(failure.code, expected_code)

    def test_units_must_be_file_ordered_contiguous_and_blob_consistent(self):
        builder = SourceRecordBuilder()
        valid = normalized_material()
        first_file_units = (
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L1-L1",
                path="README.md",
                blob_sha=README_BLOB_SHA,
                heading_path=("Course",),
                start_line=1,
                end_line=1,
                text="# Course\n",
            ),
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L2-L2",
                path="README.md",
                blob_sha=LESSON_BLOB_SHA,
                heading_path=("Course", "Details"),
                start_line=2,
                end_line=2,
                text="Overview text.\n",
            ),
        )
        mixed_blob = replace(valid, units=first_file_units + (valid.units[1],))
        failure = builder.build(mixed_blob, identity="source:acme-course", commit_id="source-record-1")
        self.assertIsInstance(failure, SourceRecordFailure)
        self.assertEqual(failure.code, "BLOB_IDENTITY_MISMATCH")

        repeated_path = replace(valid, units=(valid.units[0], valid.units[1], valid.units[0]))
        failure = builder.build(repeated_path, identity="source:acme-course", commit_id="source-record-1")
        self.assertIsInstance(failure, SourceRecordFailure)
        self.assertEqual(failure.code, "UNIT_ORDER_INVALID")

    def test_multiple_units_from_one_file_remain_ordered_with_one_blob_identity(self):
        units = (
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L1-L1",
                path="README.md",
                blob_sha=README_BLOB_SHA,
                heading_path=("Course",),
                start_line=1,
                end_line=1,
                text="# Course\n",
            ),
            NormalizedSourceUnit(
                locator=f"{REPOSITORY_IDENTITY}@{COMMIT_SHA}:README.md#L2-L2",
                path="README.md",
                blob_sha=README_BLOB_SHA,
                heading_path=("Course", "Details"),
                start_line=2,
                end_line=2,
                text="Overview text.\n",
            ),
        )
        material = replace(normalized_material(), units=units)
        candidate = SourceRecordBuilder().build(
            material,
            identity="source:acme-course",
            commit_id="source-record-1",
        )

        self.assertIsInstance(candidate, ArtifactCandidate)
        self.assertEqual(
            [unit["locator"] for unit in candidate.payload["units"]],
            [unit.locator for unit in units],
        )

    def test_heading_line_and_latest_identity_errors_fail_closed(self):
        builder = SourceRecordBuilder()
        material = normalized_material()
        malformed_heading = replace(
            material,
            units=(replace(material.units[0], heading_path=["Course"]), material.units[1]),
        )
        failure = builder.build(malformed_heading, identity="source:acme-course", commit_id="source-record-1")
        self.assertIsInstance(failure, SourceRecordFailure)
        self.assertEqual(failure.code, "INVALID_HEADING_PATH")

        malformed_start = replace(
            material,
            units=(replace(material.units[0], start_line=2), material.units[1]),
        )
        failure = builder.build(malformed_start, identity="source:acme-course", commit_id="source-record-1")
        self.assertIsInstance(failure, SourceRecordFailure)
        self.assertEqual(failure.code, "NON_CONTIGUOUS_LINES")

        for identity, commit_id, expected_code in (
            ("latest", "source-record-1", "INVALID_ARTIFACT_IDENTITY"),
            ("source:acme-course", "latest", "INVALID_COMMIT_ID"),
        ):
            with self.subTest(identity=identity, commit_id=commit_id):
                failure = builder.build(material, identity=identity, commit_id=commit_id)
                self.assertIsInstance(failure, SourceRecordFailure)
                self.assertEqual(failure.code, expected_code)


if __name__ == "__main__":
    unittest.main()
