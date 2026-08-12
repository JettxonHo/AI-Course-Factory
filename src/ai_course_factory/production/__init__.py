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
from .interfaces import VisualGenerator, VoiceGenerator
from .model import (
    MediaGenerationResult,
    ProductionMediaFailure,
    VisualGenerationTask,
    VoiceSynthesisTask,
)
from .adapters import DeterministicFakeVisualGenerator, DeterministicFakeVoiceGenerator

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
    "MediaGenerationResult",
    "ProductionMediaFailure",
    "VisualGenerationTask",
    "VoiceSynthesisTask",
    "VisualGenerator",
    "VoiceGenerator",
    "DeterministicFakeVisualGenerator",
    "DeterministicFakeVoiceGenerator",
]
