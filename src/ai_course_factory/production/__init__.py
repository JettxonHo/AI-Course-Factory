"""Provider-neutral production contracts."""

from .budget import (
    BudgetAuthorizationBoundary,
    BudgetAuthorizationRepository,
    BudgetAuthorizationRecord,
    BudgetDecisionOutcome,
    BudgetDecisionRecord,
    BudgetFailure,
    BudgetModule,
    PriceLineItem,
    PriceSnapshot,
    RetryPolicy,
)
from .sqlite_budget import SQLiteBudgetAuthorizationRepository
from .attempt import (
    ProviderAttemptClaim,
    ProviderAttemptFailure,
    ProviderAttemptLedger,
    ProviderAttemptOutcome,
    ProviderAttemptRecord,
    ProviderAttemptRepository,
    ProviderAttemptReservation,
)
from .sqlite_attempt import SQLiteProviderAttemptRepository
from .interfaces import MediaComposer, VisualGenerator, VoiceGenerator
from .model import (
    MediaCompositionResult,
    MediaCompositionScene,
    MediaCompositionTask,
    MediaGenerationResult,
    ProductionCompositionResult,
    ProductionExecutionResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VoiceSynthesisTask,
)
from .adapters import (
    DeterministicFakeVisualGenerator,
    DeterministicFakeVoiceGenerator,
    FFmpegMediaComposer,
    FFmpegFixtureVisualGenerator,
    FFmpegFixtureVoiceGenerator,
)
from .orchestrator import ProductionOrchestrator

__all__ = [
    "BudgetAuthorizationBoundary",
    "BudgetAuthorizationRepository",
    "BudgetAuthorizationRecord",
    "BudgetDecisionOutcome",
    "BudgetDecisionRecord",
    "BudgetFailure",
    "BudgetModule",
    "PriceLineItem",
    "PriceSnapshot",
    "RetryPolicy",
    "SQLiteBudgetAuthorizationRepository",
    "ProviderAttemptClaim",
    "ProviderAttemptFailure",
    "ProviderAttemptLedger",
    "ProviderAttemptOutcome",
    "ProviderAttemptRecord",
    "ProviderAttemptRepository",
    "ProviderAttemptReservation",
    "SQLiteProviderAttemptRepository",
    "MediaCompositionResult",
    "MediaCompositionScene",
    "MediaCompositionTask",
    "MediaComposer",
    "MediaGenerationResult",
    "ProductionCompositionResult",
    "ProductionExecutionResult",
    "ProductionMediaFailure",
    "VisualGenerationTask",
    "VoiceSynthesisTask",
    "VisualGenerator",
    "VoiceGenerator",
    "DeterministicFakeVisualGenerator",
    "DeterministicFakeVoiceGenerator",
    "FFmpegMediaComposer",
    "FFmpegFixtureVisualGenerator",
    "FFmpegFixtureVoiceGenerator",
    "ProductionOrchestrator",
]
