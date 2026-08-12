"""Provider adapters available before real Provider selection."""

from .fake import DeterministicFakeVisualGenerator, DeterministicFakeVoiceGenerator

__all__ = ["DeterministicFakeVisualGenerator", "DeterministicFakeVoiceGenerator"]
