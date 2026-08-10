"""Provider-neutral model runtime contracts for Agent invocations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Protocol

from ai_course_factory.artifacts import ArtifactReference


@dataclass(frozen=True, slots=True)
class ModelRuntimeRequest:
    """Explicit, provider-neutral inputs for one Agent model invocation."""

    purpose: str
    source_record_reference: ArtifactReference
    source_record_payload: Mapping[str, Any]
    task_context: Mapping[str, str]
    knowledge_boundary: str


@dataclass(frozen=True, slots=True)
class ModelRuntimeResult:
    """Normalized model output consumed by the Knowledge Agent."""

    repository_summary: str
    lesson_focus: str
    claims: tuple[Mapping[str, Any], ...]
    gaps: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelRuntimeFailure:
    """Normalized technical failure returned by a model runtime."""

    kind: str
    code: str
    message: str


class ModelRuntimePort(Protocol):
    """Minimal logical port implemented by a configured model runtime."""

    def invoke(self, request: ModelRuntimeRequest) -> ModelRuntimeResult | ModelRuntimeFailure:
        """Return a normalized result or normalized technical failure."""

