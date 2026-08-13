"""Provider adapters available before real Provider selection."""

from .fake import DeterministicFakeVisualGenerator, DeterministicFakeVoiceGenerator
from .ffmpeg_composer import FFmpegMediaComposer
from .ffmpeg_fixture import FFmpegFixtureVisualGenerator, FFmpegFixtureVoiceGenerator
from .local_imported import (
    LOCAL_IMPORTED_PROVIDER,
    LocalImportedPreflight,
    LocalImportedVisualGenerator,
)
from .gpt_sovits import (
    GPT_SOVITS_GPT_MODEL_BASENAME,
    GPT_SOVITS_INFERENCE_SCRIPT_BASENAME,
    GPT_SOVITS_MODEL_IDENTIFIER,
    GPT_SOVITS_PROVIDER,
    GPT_SOVITS_REFERENCE_PROVENANCE,
    GPT_SOVITS_REFERENCE_TRANSCRIPT,
    GPT_SOVITS_REPOSITORY_COMMIT,
    GPT_SOVITS_SOVITS_MODEL_BASENAME,
    GPTSoVITSConfiguration,
    GPTSoVITSPreflight,
    GPTSoVITSVoiceGenerator,
    GPTSoVITSSyntheticVoiceGenerator,
)

__all__ = [
    "DeterministicFakeVisualGenerator",
    "DeterministicFakeVoiceGenerator",
    "FFmpegMediaComposer",
    "FFmpegFixtureVisualGenerator",
    "FFmpegFixtureVoiceGenerator",
    "LOCAL_IMPORTED_PROVIDER",
    "LocalImportedPreflight",
    "LocalImportedVisualGenerator",
    "GPT_SOVITS_PROVIDER",
    "GPT_SOVITS_MODEL_IDENTIFIER",
    "GPT_SOVITS_GPT_MODEL_BASENAME",
    "GPT_SOVITS_INFERENCE_SCRIPT_BASENAME",
    "GPT_SOVITS_SOVITS_MODEL_BASENAME",
    "GPT_SOVITS_REFERENCE_PROVENANCE",
    "GPT_SOVITS_REFERENCE_TRANSCRIPT",
    "GPT_SOVITS_REPOSITORY_COMMIT",
    "GPTSoVITSConfiguration",
    "GPTSoVITSPreflight",
    "GPTSoVITSVoiceGenerator",
    "GPTSoVITSSyntheticVoiceGenerator",
]
