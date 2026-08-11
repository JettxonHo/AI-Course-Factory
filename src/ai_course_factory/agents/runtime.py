"""Provider-neutral model runtime contracts for Agent invocations."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol

from ai_course_factory.artifacts import ArtifactReference


@dataclass(frozen=True, slots=True)
class ModelRuntimeRequest:
    """Explicit, provider-neutral inputs for one Agent model invocation."""

    purpose: str
    source_record_reference: ArtifactReference | None = None
    source_record_payload: Mapping[str, Any] | None = None
    task_context: Mapping[str, Any] = field(default_factory=dict)
    knowledge_boundary: str = ""
    inputs: Mapping[str, Any] = field(default_factory=dict)
    constraints: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ModelRuntimeResult:
    """Normalized model output consumed by the Knowledge Agent."""

    repository_summary: str
    lesson_focus: str
    claims: tuple[Mapping[str, Any], ...]
    gaps: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ContentModelRuntimeResult:
    """Provider-neutral normalized output envelope for Content Agent stages."""

    content: Mapping[str, Any]
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProductionModelRuntimeResult:
    """Provider-neutral normalized output envelope for Production Agent stages."""

    character: Mapping[str, Any]
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StoryboardModelRuntimeResult:
    """Provider-neutral normalized output for Storyboard planning."""

    storyboard: Mapping[str, Any]
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModelRuntimeFailure:
    """Normalized technical failure returned by a model runtime."""

    kind: str
    code: str
    message: str


class ModelRuntimePort(Protocol):
    """Minimal logical port implemented by a configured model runtime."""

    def invoke(
        self, request: ModelRuntimeRequest
    ) -> (
        ModelRuntimeResult
        | ContentModelRuntimeResult
        | ProductionModelRuntimeResult
        | StoryboardModelRuntimeResult
        | ModelRuntimeFailure
    ):
        """Return a normalized result or normalized technical failure."""
