from __future__ import annotations

from collections.abc import Iterable

from ai_course_factory.knowledge import SourceAcquisitionResult, SourceConnectorFailure, SourceFile


SUPPORTED_REPOSITORY_URL = "https://github.com/microsoft/AI-For-Beginners"
REAL_SHAPED_COMMIT = "0123456789abcdef0123456789abcdef01234567"
REAL_SHAPED_BLOB = "abcdef0123456789abcdef0123456789abcdef01"
LESSON_PATH = "lessons/1-Intro/README.md"
LESSON_TEXT = "# Lesson 1\n\n## AI is practical\n\nAI is not magic; it is a practical tool built from data and methods.\n"


class FixtureSourceConnector:
    """Explicit test-only source boundary; production never imports this."""

    def __init__(self, failures: Iterable[SourceConnectorFailure] = ()) -> None:
        self.calls: list[tuple[str, tuple[str, ...]]] = []
        self.failures = list(failures)

    def acquire(self, repository_url: str, paths: list[str] | tuple[str, ...]) -> SourceAcquisitionResult | SourceConnectorFailure:
        self.calls.append((repository_url, tuple(paths)))
        if self.failures:
            return self.failures.pop(0)
        return SourceAcquisitionResult(
            repository_url=SUPPORTED_REPOSITORY_URL,
            repository_identity="microsoft/AI-For-Beginners",
            commit_sha=REAL_SHAPED_COMMIT,
            files=(SourceFile(LESSON_PATH, REAL_SHAPED_BLOB, LESSON_TEXT, len(LESSON_TEXT.encode("utf-8"))),),
            total_size_bytes=len(LESSON_TEXT.encode("utf-8")),
        )


def ensure_source(application: object) -> object:
    """Start the explicit test source when a legacy flow needs a task."""
    create_or_open = getattr(application, "create_or_open")
    result = create_or_open()
    if result.status == "source_required":
        started = application.start_source(SUPPORTED_REPOSITORY_URL)
        if started.status != "success":
            raise AssertionError(started.error_message)
        return started
    return result
