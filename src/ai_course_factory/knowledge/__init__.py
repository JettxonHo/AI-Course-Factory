"""Knowledge Layer source acquisition contracts."""

from .github_connector import GitHubSourceConnector
from .normalization import (
    NormalizationFailure,
    NormalizedSourceMaterial,
    NormalizedSourceUnit,
    SourceNormalizer,
)
from .source_record import SourceRecordBuilder, SourceRecordFailure
from .source import SourceAcquisitionResult, SourceConnectorFailure, SourceFile

__all__ = [
    "GitHubSourceConnector",
    "NormalizationFailure",
    "NormalizedSourceMaterial",
    "NormalizedSourceUnit",
    "SourceAcquisitionResult",
    "SourceConnectorFailure",
    "SourceFile",
    "SourceNormalizer",
    "SourceRecordBuilder",
    "SourceRecordFailure",
]
