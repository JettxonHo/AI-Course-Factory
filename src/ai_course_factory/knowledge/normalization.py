"""Deterministic, provenance-preserving source normalization seam."""

from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from .source import SourceAcquisitionResult, SourceFile


_GIT_SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
_IDENTITY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
_ATX_HEADING_PATTERN = re.compile(r"^[ \t]{0,3}(#{1,6})(?:[ \t]+(.*?)[ \t]*|[ \t]*)$")
_FENCE_PATTERN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
_MAX_PATH_LENGTH = 1024


@dataclass(frozen=True, slots=True)
class NormalizedSourceUnit:
    """One lossless structural unit with exact source provenance."""

    locator: str
    path: str
    blob_sha: str
    heading_path: tuple[str, ...]
    start_line: int
    end_line: int
    text: str


@dataclass(frozen=True, slots=True)
class NormalizedSourceMaterial:
    """Provider-neutral ordered source material returned by normalization."""

    repository_url: str
    repository_identity: str
    commit_sha: str
    units: tuple[NormalizedSourceUnit, ...]
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class NormalizationFailure:
    """Stable, safe failure returned without partial normalized units."""

    kind: str
    code: str
    message: str


class _NormalizationValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SourceNormalizer:
    """Normalize one complete acquisition result without fetching or interpreting it."""

    def normalize(
        self, acquisition: SourceAcquisitionResult
    ) -> NormalizedSourceMaterial | NormalizationFailure:
        try:
            self._validate_acquisition(acquisition)
            units: list[NormalizedSourceUnit] = []
            for source_file in acquisition.files:
                units.extend(self._normalize_file(acquisition, source_file))
            if not units:
                raise _NormalizationValidation(
                    "EMPTY_NORMALIZED_MATERIAL", "source material contains no consumable units"
                )
            return NormalizedSourceMaterial(
                repository_url=acquisition.repository_url,
                repository_identity=acquisition.repository_identity,
                commit_sha=acquisition.commit_sha,
                units=tuple(units),
                diagnostics=(
                    f"source_files={len(acquisition.files)}",
                    f"normalized_units={len(units)}",
                    f"total_bytes={acquisition.total_size_bytes}",
                ),
            )
        except _NormalizationValidation as exc:
            return NormalizationFailure("validation", exc.code, exc.message)
        except Exception:
            return NormalizationFailure(
                "execution", "NORMALIZATION_FAILED", "source normalization failed"
            )

    @classmethod
    def _validate_acquisition(cls, acquisition: SourceAcquisitionResult) -> None:
        if not isinstance(acquisition, SourceAcquisitionResult):
            raise _NormalizationValidation(
                "INVALID_INPUT_TYPE", "SourceAcquisitionResult input is required"
            )
        repository_url, repository_identity = cls._validate_repository_provenance(acquisition)
        if not isinstance(acquisition.commit_sha, str) or not _GIT_SHA_PATTERN.fullmatch(acquisition.commit_sha):
            raise _NormalizationValidation("INVALID_COMMIT_SHA", "source commit identity is invalid")
        if not isinstance(acquisition.files, tuple) or not acquisition.files:
            raise _NormalizationValidation(
                "INVALID_SOURCE_FILES", "a non-empty ordered source file tuple is required"
            )
        if (
            not isinstance(acquisition.total_size_bytes, int)
            or isinstance(acquisition.total_size_bytes, bool)
            or acquisition.total_size_bytes < 0
        ):
            raise _NormalizationValidation("INVALID_TOTAL_SIZE", "source total size is invalid")

        seen_paths: set[str] = set()
        total_size = 0
        for source_file in acquisition.files:
            cls._validate_source_file(source_file, seen_paths)
            total_size += source_file.size_bytes
        if total_size != acquisition.total_size_bytes:
            raise _NormalizationValidation(
                "TOTAL_SIZE_MISMATCH", "source total size does not match its files"
            )
        # Assignments above deliberately keep the input values in the
        # validation path; these checks make the intent explicit for callers.
        if not repository_url or not repository_identity:
            raise _NormalizationValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            )

    @staticmethod
    def _validate_repository_provenance(
        acquisition: SourceAcquisitionResult,
    ) -> tuple[str, str]:
        if not isinstance(acquisition.repository_url, str) or not isinstance(
            acquisition.repository_identity, str
        ):
            raise _NormalizationValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            )
        try:
            parsed = urlsplit(acquisition.repository_url)
            port = parsed.port
        except ValueError:
            raise _NormalizationValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            ) from None
        if (
            parsed.scheme != "https"
            or parsed.hostname != "github.com"
            or parsed.username is not None
            or parsed.password is not None
            or port is not None
            or parsed.query
            or parsed.fragment
            or not parsed.path.startswith("/")
            or parsed.path.endswith("/")
        ):
            raise _NormalizationValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            )
        segments = parsed.path[1:].split("/")
        if len(segments) != 2 or not all(_IDENTITY_PATTERN.fullmatch(segment) for segment in segments):
            raise _NormalizationValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            )
        identity = "/".join(segments)
        canonical_url = f"https://github.com/{identity}"
        if acquisition.repository_url != canonical_url:
            raise _NormalizationValidation(
                "NON_CANONICAL_REPOSITORY_URL", "source repository URL is not canonical"
            )
        if acquisition.repository_identity != identity:
            raise _NormalizationValidation(
                "REPOSITORY_IDENTITY_MISMATCH", "source repository identity does not match its URL"
            )
        return acquisition.repository_url, identity

    @staticmethod
    def _validate_source_file(source_file: SourceFile, seen_paths: set[str]) -> None:
        if not isinstance(source_file, SourceFile):
            raise _NormalizationValidation("INVALID_SOURCE_FILE", "source file provenance is invalid")
        path = source_file.path
        if (
            not isinstance(path, str)
            or not path
            or len(path) > _MAX_PATH_LENGTH
            or path.startswith("/")
            or path.endswith("/")
            or "\\" in path
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in path)
            or any(part in ("", ".", "..") for part in path.split("/"))
        ):
            raise _NormalizationValidation("INVALID_SOURCE_PATH", "source file path is invalid")
        if path in seen_paths:
            raise _NormalizationValidation("DUPLICATE_SOURCE_PATH", "source file paths must be unique")
        seen_paths.add(path)
        if not isinstance(source_file.blob_sha, str) or not _GIT_SHA_PATTERN.fullmatch(source_file.blob_sha):
            raise _NormalizationValidation("INVALID_BLOB_SHA", "source blob identity is invalid")
        if not isinstance(source_file.text, str):
            raise _NormalizationValidation("INVALID_SOURCE_TEXT", "source file text is invalid")
        if not source_file.text.strip():
            raise _NormalizationValidation("EMPTY_SOURCE_FILE", "source file has no consumable text")
        if (
            not isinstance(source_file.size_bytes, int)
            or isinstance(source_file.size_bytes, bool)
            or source_file.size_bytes < 0
        ):
            raise _NormalizationValidation("INVALID_SOURCE_SIZE", "source file size is invalid")
        try:
            encoded_size = len(source_file.text.encode("utf-8"))
        except UnicodeEncodeError:
            raise _NormalizationValidation("INVALID_SOURCE_TEXT", "source file text is not valid UTF-8") from None
        if encoded_size != source_file.size_bytes:
            raise _NormalizationValidation(
                "SOURCE_SIZE_MISMATCH", "source file size does not match its text"
            )

    @classmethod
    def _normalize_file(
        cls, acquisition: SourceAcquisitionResult, source_file: SourceFile
    ) -> tuple[NormalizedSourceUnit, ...]:
        lines = source_file.text.splitlines(keepends=True)
        if not lines:
            raise _NormalizationValidation("EMPTY_SOURCE_FILE", "source file has no consumable text")
        boundaries: list[tuple[int, tuple[str, ...]]] = []
        headings: list[tuple[int, tuple[str, ...]]] = []
        active_fence: tuple[str, int] | None = None
        heading_stack: list[tuple[int, str]] = []
        for line_index, line in enumerate(lines):
            line_without_ending = line.rstrip("\r\n")
            fence = _FENCE_PATTERN.match(line_without_ending)
            if active_fence is not None:
                if (
                    fence is not None
                    and fence.group(1)[0] == active_fence[0]
                    and len(fence.group(1)) >= active_fence[1]
                    and not fence.group(2).strip()
                ):
                    active_fence = None
                continue
            if fence is not None:
                active_fence = (fence.group(1)[0], len(fence.group(1)))
                continue
            heading = _ATX_HEADING_PATTERN.match(line_without_ending)
            if heading is None:
                continue
            level = len(heading.group(1))
            title = (heading.group(2) or "").strip()
            title = re.sub(r"[ \t]+#+[ \t]*$", "", title).strip()
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, title))
            headings.append((line_index, tuple(item[1] for item in heading_stack)))

        boundaries.extend(headings)

        if not boundaries or boundaries[0][0] > 0:
            boundaries.insert(0, (0, ()))
        units: list[NormalizedSourceUnit] = []
        for boundary_index, (start_index, heading_path) in enumerate(boundaries):
            end_index = boundaries[boundary_index + 1][0] - 1 if boundary_index + 1 < len(boundaries) else len(lines) - 1
            text = "".join(lines[start_index : end_index + 1])
            units.append(
                NormalizedSourceUnit(
                    locator=cls._locator(acquisition, source_file, start_index + 1, end_index + 1),
                    path=source_file.path,
                    blob_sha=source_file.blob_sha,
                    heading_path=heading_path,
                    start_line=start_index + 1,
                    end_line=end_index + 1,
                    text=text,
                )
            )
        return tuple(units)

    @staticmethod
    def _locator(
        acquisition: SourceAcquisitionResult,
        source_file: SourceFile,
        start_line: int,
        end_line: int,
    ) -> str:
        return (
            f"{acquisition.repository_identity}@{acquisition.commit_sha}:"
            f"{source_file.path}#L{start_line}-L{end_line}"
        )
