"""Runtime-checkable seams for provider-neutral media generation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .model import (
    LocalNarrationPreflight,
    LocalNarrationResult,
    LocalNarrationTask,
    MediaCompositionResult,
    MediaCompositionTask,
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VoiceSynthesisTask,
)


@runtime_checkable
class VisualGenerator(Protocol):
    def generate(self, task: VisualGenerationTask) -> MediaGenerationResult | ProductionMediaFailure: ...


@runtime_checkable
class VoiceGenerator(Protocol):
    def synthesize(self, task: VoiceSynthesisTask) -> MediaGenerationResult | ProductionMediaFailure: ...


@runtime_checkable
class LocalNarrationRenderer(Protocol):
    """Small local-only seam used by the Creator Handoff Package."""

    def preflight(self) -> LocalNarrationPreflight | ProductionMediaFailure: ...

    def render(self, task: LocalNarrationTask) -> LocalNarrationResult | ProductionMediaFailure: ...


@runtime_checkable
class MediaComposer(Protocol):
    def compose(self, task: MediaCompositionTask) -> MediaCompositionResult | ProductionMediaFailure: ...


__all__ = ["LocalNarrationRenderer", "MediaComposer", "VisualGenerator", "VoiceGenerator"]
