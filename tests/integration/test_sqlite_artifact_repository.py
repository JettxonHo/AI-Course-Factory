"""Durability, transaction and serialization evidence for SQLite Artifacts."""

import sqlite3
import tempfile
import unittest
from pathlib import Path

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactStorageError,
    CommitConflictError,
    RevisionMismatchError,
    ArtifactNotFoundError,
    ArtifactReference,
    SQLiteArtifactRepository,
)


def _candidate(
    *,
    identity: str = "episode:sqlite",
    payload: object | None = None,
    commit_id: str = "sqlite-v1",
    prior_reference: ArtifactReference | None = None,
) -> ArtifactCandidate:
    if payload is None:
        payload = {"text": "first"}
    return ArtifactCandidate(
        artifact_type="script",
        identity=identity,
        payload=payload,
        provenance=("source:v1",),
        dependencies=(),
        validated=True,
        commit_id=commit_id,
        prior_reference=prior_reference,
    )


class SQLiteArtifactRepositoryIntegrationTests(unittest.TestCase):
    def test_close_and_reopen_preserves_versions_revision_and_logical_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "artifacts.sqlite3"
            first_candidate = _candidate()
            repository = SQLiteArtifactRepository(database)
            first = repository.commit(first_candidate)
            second_candidate = _candidate(
                payload={"text": "second"},
                commit_id="sqlite-v2",
                prior_reference=first,
            )
            second = repository.commit(second_candidate)
            repository.close()

            reopened = SQLiteArtifactRepository(database)
            try:
                self.assertEqual(reopened.get(first).payload, {"text": "first"})
                self.assertEqual(reopened.get(second).payload, {"text": "second"})
                self.assertEqual(reopened.commit(first_candidate), first)
                with self.assertRaises(CommitConflictError):
                    reopened.commit(_candidate(payload={"text": "changed"}))
                with self.assertRaises(RevisionMismatchError):
                    reopened.commit(
                        _candidate(
                            payload={"text": "stale"},
                            commit_id="sqlite-v3",
                            prior_reference=first,
                        )
                    )
                with self.assertRaises(ArtifactNotFoundError):
                    reopened.get(ArtifactReference("script", "episode:sqlite", 3))
            finally:
                reopened.close()

    def test_two_open_instances_observe_commits_and_serialize_revision_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "artifacts.sqlite3"
            first_repository = SQLiteArtifactRepository(database)
            second_repository = SQLiteArtifactRepository(database)
            try:
                first = first_repository.commit(_candidate())
                self.assertEqual(second_repository.get(first).payload, {"text": "first"})
                second = second_repository.commit(
                    _candidate(
                        payload={"text": "second"},
                        commit_id="sqlite-v2",
                        prior_reference=first,
                    )
                )
                self.assertEqual(first_repository.get(second).version, 2)
                self.assertEqual(first_repository.commit(_candidate(payload={"text": "first"})), first)
                with self.assertRaises(RevisionMismatchError):
                    second_repository.commit(
                        _candidate(
                            payload={"text": "stale"},
                            commit_id="sqlite-v3",
                            prior_reference=first,
                        )
                    )
                with self.assertRaises(ArtifactNotFoundError):
                    first_repository.get(ArtifactReference("script", "episode:sqlite", 3))
            finally:
                first_repository.close()
                second_repository.close()

    def test_typed_json_round_trips_full_frozen_value_domain_deterministically(self):
        dependency = ArtifactReference("source_record", "source:one", 7)
        payload = {
            "none": None,
            "bool": True,
            "integer": 10**100 + 7,
            "float": 1.25,
            "string": "中文",
            "bytes": b"\\x00\\xff",
            "reference": dependency,
            "mapping": {"b": 2, "a": 1},
            "list": [1, 2],
            "tuple": ("x", 3),
            "set": {"z", "a"},
            "frozenset": frozenset({2, 1}),
        }
        reordered_payload = dict(reversed(tuple(payload.items())))
        reordered_payload["mapping"] = {"a": 1, "b": 2}
        reordered_payload["set"] = {"a", "z"}

        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "artifacts.sqlite3"
            repository = SQLiteArtifactRepository(database)
            try:
                first = repository.commit(_candidate(identity="episode:typed-a", payload=payload, commit_id="typed-a"))
                second = repository.commit(
                    _candidate(
                        identity="episode:typed-b",
                        payload=reordered_payload,
                        commit_id="typed-b",
                    )
                )
                restored = repository.get(first).payload
                self.assertEqual(restored["integer"], 10**100 + 7)
                self.assertIsInstance(restored["bytes"], bytes)
                self.assertEqual(restored["reference"], dependency)
                self.assertIsInstance(restored["list"], tuple)
                self.assertIsInstance(restored["set"], frozenset)
                self.assertIsInstance(restored["frozenset"], frozenset)
                self.assertEqual(restored["mapping"], {"a": 1, "b": 2})
            finally:
                repository.close()

            with sqlite3.connect(database) as connection:
                payload_rows = connection.execute(
                    "SELECT payload_json FROM artifact_versions WHERE identity IN (?, ?) ORDER BY identity",
                    ("episode:typed-a", "episode:typed-b"),
                ).fetchall()
            self.assertEqual(payload_rows[0][0], payload_rows[1][0])
            self.assertNotIn("pickle", payload_rows[0][0].lower())
            self.assertEqual(second.version, 1)

    def test_invalid_stored_json_and_unsupported_schema_fail_closed_without_raw_details(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "artifacts.sqlite3"
            repository = SQLiteArtifactRepository(database)
            reference = repository.commit(_candidate())
            repository.close()

            with sqlite3.connect(database) as connection:
                connection.execute(
                    "UPDATE artifact_versions SET payload_json = ? WHERE artifact_type = ? AND identity = ? AND version = ?",
                    ("not-json", reference.artifact_type, reference.identity, reference.version),
                )
                connection.commit()
            reopened = SQLiteArtifactRepository(database)
            try:
                with self.assertRaises(ArtifactStorageError) as commit_context:
                    reopened.commit(_candidate())
                self.assertEqual(commit_context.exception.code, "ARTIFACT_STORAGE_ERROR")
                with self.assertRaises(ArtifactStorageError) as context:
                    reopened.get(reference)
                self.assertEqual(context.exception.code, "ARTIFACT_STORAGE_ERROR")
                self.assertEqual(str(context.exception), "artifact storage operation failed")
            finally:
                reopened.close()

            with sqlite3.connect(database) as connection:
                connection.execute("UPDATE artifact_schema SET version = 999 WHERE singleton = 1")
                connection.commit()
            with self.assertRaises(ArtifactStorageError) as context:
                SQLiteArtifactRepository(database)
            self.assertEqual(context.exception.code, "ARTIFACT_STORAGE_ERROR")
            self.assertEqual(str(context.exception), "artifact storage operation failed")

    def test_corrupt_logical_fingerprint_index_fails_safe_for_replay_and_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            original_database = Path(directory) / "original.sqlite3"
            changed_database = Path(directory) / "changed.sqlite3"

            original_repository = SQLiteArtifactRepository(original_database)
            original_reference = original_repository.commit(_candidate())
            original_repository.close()

            changed_repository = SQLiteArtifactRepository(changed_database)
            changed_repository.commit(_candidate(payload={"text": "changed"}))
            changed_repository.close()

            with sqlite3.connect(changed_database) as connection:
                changed_fingerprint = connection.execute(
                    """
                    SELECT fingerprint_json FROM artifact_logical_commits
                    WHERE artifact_type = ? AND identity = ? AND commit_id = ?
                    """,
                    ("script", "episode:sqlite", "sqlite-v1"),
                ).fetchone()[0]
            with sqlite3.connect(original_database) as connection:
                connection.execute(
                    """
                    UPDATE artifact_logical_commits SET fingerprint_json = ?
                    WHERE artifact_type = ? AND identity = ? AND commit_id = ?
                    """,
                    (changed_fingerprint, "script", "episode:sqlite", "sqlite-v1"),
                )
                connection.commit()

            reopened = SQLiteArtifactRepository(original_database)
            try:
                for candidate in (
                    _candidate(),
                    _candidate(payload={"text": "changed"}),
                ):
                    with self.subTest(payload=candidate.payload):
                        with self.assertRaises(ArtifactStorageError) as context:
                            reopened.commit(candidate)
                        self.assertEqual(context.exception.code, "ARTIFACT_STORAGE_ERROR")
                        self.assertEqual(str(context.exception), "artifact storage operation failed")
                self.assertEqual(reopened.get(original_reference).payload, {"text": "first"})
            finally:
                reopened.close()

    def test_sqlite_open_failure_is_normalized(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ArtifactStorageError) as context:
                SQLiteArtifactRepository(directory)
        self.assertEqual(context.exception.code, "ARTIFACT_STORAGE_ERROR")
        self.assertNotIn("sqlite", str(context.exception).lower())


if __name__ == "__main__":
    unittest.main()
