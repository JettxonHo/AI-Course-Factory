"""Public checkpoint adapter contract tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

from ai_course_factory.artifacts import ArtifactReference
from ai_course_factory.workflow import (
    CheckpointAdapter,
    CheckpointNotFoundError,
    InMemoryCheckpointAdapter,
    SQLiteCheckpointAdapter,
)


class CheckpointAdapterContractTests(unittest.TestCase):
    def test_in_memory_and_sqlite_adapters_conform_to_public_contract(self):
        adapters = [InMemoryCheckpointAdapter()]
        with tempfile.TemporaryDirectory() as directory:
            adapters.append(SQLiteCheckpointAdapter(Path(directory) / "workflow.sqlite3"))

            for adapter in adapters:
                with self.subTest(adapter=type(adapter).__name__):
                    self.assertIsInstance(adapter, CheckpointAdapter)
            adapters[-1].close()

    def test_missing_lookup_and_inspection_are_detached_and_decode_exact_references(self):
        with tempfile.TemporaryDirectory() as directory:
            adapters = [
                InMemoryCheckpointAdapter(),
                SQLiteCheckpointAdapter(Path(directory) / "workflow.sqlite3"),
            ]
            try:
                for adapter in adapters:
                    with self.subTest(adapter=type(adapter).__name__):
                        self.assertFalse(adapter.has_checkpoint("thread-1"))
                        with self.assertRaises(CheckpointNotFoundError):
                            adapter.values("thread-1")
                        with self.assertRaises(CheckpointNotFoundError):
                            adapter.inspect("thread-1")

                        adapter.saver.put(
                            {
                                "configurable": {
                                    "thread_id": "thread-1",
                                    "checkpoint_ns": "",
                                }
                            },
                            {
                                "v": 1,
                                "id": "checkpoint-1",
                                "ts": "2026-08-12T00:00:00+00:00",
                                "channel_values": {
                                    "selected_script_ref": {
                                        "artifact_type": "script",
                                        "identity": "script:one",
                                        "version": 2,
                                    },
                                    "allowed_actions": ["approve"],
                                    "decision": {
                                        "script_reference": {
                                            "artifact_type": "script",
                                            "identity": "script:one",
                                            "version": 2,
                                        }
                                    },
                                    "command_record": {
                                        "script_reference": {
                                            "artifact_type": "script",
                                            "identity": "script:one",
                                            "version": 2,
                                        }
                                    },
                                },
                                "channel_versions": {
                                    "selected_script_ref": 1,
                                    "allowed_actions": 1,
                                    "decision": 1,
                                    "command_record": 1,
                                },
                                "versions_seen": {},
                                "updated_channels": None,
                            },
                            {"source": "input", "step": 0, "writes": {}},
                            {
                                "selected_script_ref": 1,
                                "allowed_actions": 1,
                                "decision": 1,
                                "command_record": 1,
                            },
                        )
                        values = adapter.values("thread-1")
                        values["allowed_actions"].append("revise")
                        self.assertEqual(adapter.values("thread-1")["allowed_actions"], ["approve"])
                        inspected = adapter.inspect("thread-1")
                        self.assertEqual(
                            inspected["selected_script_ref"],
                            ArtifactReference("script", "script:one", 2),
                        )
                        self.assertEqual(
                            inspected["decision"]["script_reference"],
                            ArtifactReference("script", "script:one", 2),
                        )
                        self.assertEqual(
                            inspected["command_record"]["script_reference"],
                            ArtifactReference("script", "script:one", 2),
                        )
            finally:
                adapters[-1].close()

    def test_sqlite_lifecycle_and_storage_failures_are_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "workflow.sqlite3"
            with SQLiteCheckpointAdapter(database) as adapter:
                self.assertIs(adapter.__enter__(), adapter)
                adapter.__exit__(None, None, None)
                with self.assertRaisesRegex(
                    RuntimeError,
                    "^workflow checkpoint persistence failed$",
                ) as context:
                    adapter.values("thread-1")
                self.assertEqual(context.exception.code, "CHECKPOINT_STORAGE_ERROR")
                self.assertIsNone(context.exception.__cause__)
                with self.assertRaisesRegex(RuntimeError, "^workflow checkpoint persistence failed$"):
                    _ = adapter.saver

            with self.assertRaisesRegex(RuntimeError, "^workflow checkpoint persistence failed$") as context:
                SQLiteCheckpointAdapter(Path(directory) / "missing" / "workflow.sqlite3")
            self.assertEqual(context.exception.code, "CHECKPOINT_STORAGE_ERROR")
            self.assertIsNone(context.exception.__cause__)
            self.assertNotIn(str(directory), str(context.exception))

    def test_read_failure_is_normalized_without_raw_storage_detail(self):
        class FailingSaver(InMemorySaver):
            def get_tuple(self, config):
                raise RuntimeError("/private/workflow.sqlite3: malformed checkpoint")

        adapter = InMemoryCheckpointAdapter(FailingSaver())
        with self.assertRaisesRegex(
            RuntimeError,
            "^workflow checkpoint persistence failed$",
        ) as context:
            adapter.values("thread-1")
        self.assertEqual(context.exception.code, "CHECKPOINT_STORAGE_ERROR")
        self.assertIsNone(context.exception.__cause__)
        self.assertNotIn("private", str(context.exception))


if __name__ == "__main__":
    unittest.main()
