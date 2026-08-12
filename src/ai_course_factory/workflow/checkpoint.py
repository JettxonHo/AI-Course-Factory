"""LangGraph checkpoint adapters for the local workflow control spine."""

from __future__ import annotations

import os
import re
import sqlite3
from copy import deepcopy
from typing import Any, Protocol, runtime_checkable

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

from .model import decode_reference


_STORAGE_ERROR_MESSAGE = "workflow checkpoint persistence failed"
_DEFAULT_CHECKPOINT_NAMESPACE = ""
_MAX_CHECKPOINT_NAMESPACE_LENGTH = 128
_CHECKPOINT_NAMESPACE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}\Z")


class CheckpointNotFoundError(KeyError):
    """No workflow checkpoint exists for the requested thread."""


class CheckpointStorageError(RuntimeError):
    """Safe public error for checkpoint open, read, write and close failures."""

    code = "CHECKPOINT_STORAGE_ERROR"

    def __init__(self) -> None:
        super().__init__(_STORAGE_ERROR_MESSAGE)


@runtime_checkable
class CheckpointAdapter(Protocol):
    """Public seam used by the Script Review Workflow."""

    @property
    def saver(self) -> BaseCheckpointSaver: ...

    def config(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, dict[str, str]]: ...

    def has_checkpoint(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> bool: ...

    def values(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, Any]: ...

    def inspect(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, Any]: ...


def _validate_checkpoint_namespace(checkpoint_ns: object) -> str:
    """Validate a bounded saver namespace before touching the saver."""

    if (
        type(checkpoint_ns) is not str
        or len(checkpoint_ns) > _MAX_CHECKPOINT_NAMESPACE_LENGTH
        or checkpoint_ns == ""
        and checkpoint_ns != _DEFAULT_CHECKPOINT_NAMESPACE
        or checkpoint_ns != _DEFAULT_CHECKPOINT_NAMESPACE
        and _CHECKPOINT_NAMESPACE_PATTERN.fullmatch(checkpoint_ns) is None
    ):
        raise CheckpointStorageError()
    return checkpoint_ns


def _detached_values(checkpoint: Any) -> dict[str, Any]:
    values = checkpoint.checkpoint.get("channel_values", {})
    if not isinstance(values, dict):
        raise CheckpointStorageError()
    return deepcopy(values)


def _inspect_values(values: dict[str, Any]) -> dict[str, Any]:
    try:
        result = deepcopy(values)
        for selected_key in ("selected_script_ref", "selected_video_ref"):
            if selected_key in result:
                result[selected_key] = decode_reference(result[selected_key])
        for key in ("decision", "command_record"):
            record = result.get(key)
            if isinstance(record, dict) and "script_reference" in record:
                record = dict(record)
                record["script_reference"] = decode_reference(record["script_reference"])
            if isinstance(record, dict) and "video_reference" in record:
                record = dict(record)
                record["video_reference"] = decode_reference(record["video_reference"])
            if isinstance(record, dict):
                result[key] = record
        return result
    except Exception as exc:
        raise _storage_error(exc) from None


def _storage_error(exc: BaseException) -> CheckpointStorageError:
    return CheckpointStorageError()


class InMemoryCheckpointAdapter:
    """Small adapter that owns the in-memory LangGraph checkpointer."""

    def __init__(self, saver: InMemorySaver | None = None) -> None:
        self._saver = saver or InMemorySaver()

    @property
    def saver(self) -> InMemorySaver:
        """The configured LangGraph checkpointer used during graph compilation."""

        return self._saver

    @staticmethod
    def config(
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, dict[str, str]]:
        namespace = _validate_checkpoint_namespace(checkpoint_ns)
        return {"configurable": {"thread_id": thread_id, "checkpoint_ns": namespace}}

    def has_checkpoint(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> bool:
        try:
            return self._saver.get_tuple(self.config(thread_id, checkpoint_ns)) is not None
        except Exception as exc:
            raise _storage_error(exc) from None

    def values(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, Any]:
        """Return detached control values for infrastructure-level auditing."""

        try:
            checkpoint = self._saver.get_tuple(self.config(thread_id, checkpoint_ns))
            if checkpoint is None:
                raise CheckpointNotFoundError(thread_id)
            return _detached_values(checkpoint)
        except CheckpointNotFoundError:
            raise
        except CheckpointStorageError:
            raise CheckpointStorageError() from None
        except Exception as exc:
            raise _storage_error(exc) from None

    def inspect(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, Any]:
        """Return a normalized, payload-free control projection."""

        try:
            return _inspect_values(self.values(thread_id, checkpoint_ns))
        except CheckpointNotFoundError:
            raise
        except CheckpointStorageError:
            raise CheckpointStorageError() from None
        except Exception as exc:
            raise _storage_error(exc) from None


class SQLiteCheckpointAdapter:
    """Durable adapter backed by the official synchronous ``SqliteSaver``."""

    def __init__(self, database_path: str | os.PathLike[str]) -> None:
        self._closed = False
        self._connection: sqlite3.Connection | None = None
        try:
            self._connection = sqlite3.connect(os.fspath(database_path), check_same_thread=False)
            self._saver = SqliteSaver(self._connection)
            self._saver.setup()
        except Exception as exc:
            self._closed = True
            if self._connection is not None:
                try:
                    self._connection.close()
                except Exception:
                    pass
            raise _storage_error(exc) from None

    @property
    def saver(self) -> SqliteSaver:
        self._require_open()
        return self._saver

    def config(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, dict[str, str]]:
        self._require_open()
        namespace = _validate_checkpoint_namespace(checkpoint_ns)
        return {"configurable": {"thread_id": thread_id, "checkpoint_ns": namespace}}

    def has_checkpoint(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> bool:
        try:
            return self._saver.get_tuple(self.config(thread_id, checkpoint_ns)) is not None
        except CheckpointStorageError:
            raise CheckpointStorageError() from None
        except Exception as exc:
            raise _storage_error(exc) from None

    def values(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, Any]:
        try:
            checkpoint = self._saver.get_tuple(self.config(thread_id, checkpoint_ns))
            if checkpoint is None:
                raise CheckpointNotFoundError(thread_id)
            return _detached_values(checkpoint)
        except CheckpointNotFoundError:
            raise
        except CheckpointStorageError:
            raise CheckpointStorageError() from None
        except Exception as exc:
            raise _storage_error(exc) from None

    def inspect(
        self,
        thread_id: str,
        checkpoint_ns: str = _DEFAULT_CHECKPOINT_NAMESPACE,
    ) -> dict[str, Any]:
        try:
            return _inspect_values(self.values(thread_id, checkpoint_ns))
        except CheckpointNotFoundError:
            raise
        except CheckpointStorageError:
            raise CheckpointStorageError() from None
        except Exception as exc:
            raise _storage_error(exc) from None

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        try:
            if self._connection is not None:
                self._connection.close()
        except Exception as exc:
            raise _storage_error(exc) from None

    def __enter__(self) -> SQLiteCheckpointAdapter:
        self._require_open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _require_open(self) -> None:
        if self._closed or self._connection is None:
            raise CheckpointStorageError()
