"""Shared in-memory LangGraph checkpoint adapter for the MVP control spine."""

from __future__ import annotations

from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from .model import decode_reference


class CheckpointNotFoundError(KeyError):
    """No workflow checkpoint exists for the requested thread."""


class InMemoryCheckpointAdapter:
    """Small adapter that owns the checkpointer, not business Artifact data.

    The adapter is intentionally reusable across ``ScriptReviewWorkflow``
    instances.  Reconstructing a runtime with the same adapter therefore reads
    the same LangGraph thread checkpoint.
    """

    def __init__(self, saver: InMemorySaver | None = None) -> None:
        self._saver = saver or InMemorySaver()

    @property
    def saver(self) -> InMemorySaver:
        """The configured LangGraph checkpointer used during graph compilation."""

        return self._saver

    @staticmethod
    def config(thread_id: str) -> dict[str, dict[str, str]]:
        return {"configurable": {"thread_id": thread_id}}

    def has_checkpoint(self, thread_id: str) -> bool:
        return self._saver.get_tuple(self.config(thread_id)) is not None

    def values(self, thread_id: str) -> dict[str, Any]:
        """Return the latest control values for infrastructure-level auditing."""

        checkpoint_tuple = self._saver.get_tuple(self.config(thread_id))
        if checkpoint_tuple is None:
            raise CheckpointNotFoundError(thread_id)
        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        if not isinstance(values, dict):
            return {}
        return dict(values)

    def inspect(self, thread_id: str) -> dict[str, Any]:
        """Return a normalized, payload-free control projection for tests."""

        values = self.values(thread_id)
        result = dict(values)
        if "selected_script_ref" in result:
            result["selected_script_ref"] = decode_reference(result["selected_script_ref"])
        if "decision" in result and isinstance(result["decision"], dict):
            decision = dict(result["decision"])
            if "script_reference" in decision:
                decision["script_reference"] = decode_reference(decision["script_reference"])
            result["decision"] = decision
        if "command_record" in result and isinstance(result["command_record"], dict):
            record = dict(result["command_record"])
            if "script_reference" in record:
                record["script_reference"] = decode_reference(record["script_reference"])
            result["command_record"] = record
        return result
