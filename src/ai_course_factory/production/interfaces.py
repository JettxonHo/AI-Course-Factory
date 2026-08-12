"""Runtime-checkable seams for provider-neutral media generation."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .model import (
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
class MediaComposer(Protocol):
    def compose(self, task: MediaCompositionTask) -> MediaCompositionResult | ProductionMediaFailure: ...


__all__ = ["MediaComposer", "VisualGenerator", "VoiceGenerator"]
