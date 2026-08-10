"""Source Record Artifact Candidate boundary."""

from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlsplit

from ai_course_factory.artifacts.model import ArtifactCandidate

from .normalization import NormalizedSourceMaterial, NormalizedSourceUnit


_GIT_SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")
_IDENTITY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
_MAX_PATH_LENGTH = 1024


@dataclass(frozen=True, slots=True)
class SourceRecordFailure:
    """Safe failure returned when a Source Record Candidate cannot be built."""

    kind: str
    code: str
    message: str


class _SourceRecordValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SourceRecordBuilder:
    """Build validated Source Record Candidates without committing them."""

    def build(
        self,
        material: NormalizedSourceMaterial,
        *,
        identity: str,
        commit_id: str,
    ) -> ArtifactCandidate | SourceRecordFailure:
        try:
            self._validate_material(material)
            self._validate_identity(identity, "INVALID_ARTIFACT_IDENTITY", "Source Record identity is required")
            self._validate_identity(commit_id, "INVALID_COMMIT_ID", "logical Commit identity is required")
            return self._candidate(material, identity, commit_id)
        except _SourceRecordValidation as exc:
            return SourceRecordFailure("validation", exc.code, exc.message)
        except Exception:
            return SourceRecordFailure(
                "execution", "SOURCE_RECORD_BUILD_FAILED", "source record candidate build failed"
            )

    @classmethod
    def _candidate(
        cls,
        material: NormalizedSourceMaterial,
        identity: str,
        commit_id: str,
    ) -> ArtifactCandidate:
        payload_units = tuple(
            {
                "locator": unit.locator,
                "path": unit.path,
                "blob_sha": unit.blob_sha,
                "heading_path": unit.heading_path,
                "start_line": unit.start_line,
                "end_line": unit.end_line,
                "text": unit.text,
            }
            for unit in material.units
        )
        provenance = (
            {
                "repository_url": material.repository_url,
                "repository_identity": material.repository_identity,
                "commit_sha": material.commit_sha,
            },
            *({"locator": unit.locator} for unit in material.units),
        )
        return ArtifactCandidate(
            artifact_type="source_record",
            identity=identity,
            payload={
                "source_kind": "github",
                "repository_url": material.repository_url,
                "repository_identity": material.repository_identity,
                "commit_sha": material.commit_sha,
                "units": payload_units,
            },
            provenance=provenance,
            dependencies=(),
            validated=True,
            commit_id=commit_id,
        )

    @classmethod
    def _validate_material(cls, material: NormalizedSourceMaterial) -> None:
        if not isinstance(material, NormalizedSourceMaterial):
            raise _SourceRecordValidation(
                "INVALID_INPUT_TYPE", "normalized source material is required"
            )
        cls._validate_repository(material.repository_url, material.repository_identity)
        if not isinstance(material.commit_sha, str) or not _GIT_SHA_PATTERN.fullmatch(material.commit_sha):
            raise _SourceRecordValidation("INVALID_COMMIT_SHA", "source commit identity is invalid")
        if not isinstance(material.units, tuple) or not material.units:
            raise _SourceRecordValidation(
                "EMPTY_NORMALIZED_MATERIAL", "normalized source material must contain units"
            )

        closed_paths: set[str] = set()
        current_path: str | None = None
        current_blob: str | None = None
        previous_end: int | None = None
        for unit in material.units:
            if not isinstance(unit, NormalizedSourceUnit):
                raise _SourceRecordValidation("INVALID_SOURCE_UNIT", "normalized source unit is invalid")
            cls._validate_path(unit.path)
            if not isinstance(unit.blob_sha, str) or not _GIT_SHA_PATTERN.fullmatch(unit.blob_sha):
                raise _SourceRecordValidation("INVALID_BLOB_SHA", "source unit blob identity is invalid")
            if not isinstance(unit.heading_path, tuple) or not all(
                isinstance(title, str) for title in unit.heading_path
            ):
                raise _SourceRecordValidation("INVALID_HEADING_PATH", "source unit heading path is invalid")
            if not isinstance(unit.start_line, int) or isinstance(unit.start_line, bool) or unit.start_line < 1:
                raise _SourceRecordValidation("INVALID_LINE_RANGE", "source unit line range is invalid")
            if not isinstance(unit.end_line, int) or isinstance(unit.end_line, bool) or unit.end_line < unit.start_line:
                raise _SourceRecordValidation("INVALID_LINE_RANGE", "source unit line range is invalid")
            if not isinstance(unit.text, str) or not unit.text:
                raise _SourceRecordValidation("INVALID_SOURCE_TEXT", "source unit text is invalid")
            try:
                line_count = len(unit.text.splitlines(keepends=True))
                unit.text.encode("utf-8")
            except UnicodeError:
                raise _SourceRecordValidation("INVALID_SOURCE_TEXT", "source unit text is invalid") from None
            if line_count != unit.end_line - unit.start_line + 1:
                raise _SourceRecordValidation(
                    "NON_CONTIGUOUS_LINES", "source unit text and line range are inconsistent"
                )

            expected_locator = (
                f"{material.repository_identity}@{material.commit_sha}:"
                f"{unit.path}#L{unit.start_line}-L{unit.end_line}"
            )
            if unit.locator != expected_locator:
                raise _SourceRecordValidation(
                    "INVALID_UNIT_LOCATOR", "source unit locator is inconsistent"
                )

            if unit.path != current_path:
                if unit.path in closed_paths:
                    raise _SourceRecordValidation(
                        "UNIT_ORDER_INVALID", "normalized source units must remain file ordered"
                    )
                if current_path is not None:
                    closed_paths.add(current_path)
                current_path = unit.path
                current_blob = unit.blob_sha
                previous_end = None
                if unit.start_line != 1:
                    raise _SourceRecordValidation(
                        "NON_CONTIGUOUS_LINES", "each source file must begin at line one"
                    )
            elif unit.blob_sha != current_blob:
                raise _SourceRecordValidation(
                    "BLOB_IDENTITY_MISMATCH", "all units for a file must keep one blob identity"
                )

            if previous_end is not None and unit.start_line != previous_end + 1:
                raise _SourceRecordValidation(
                    "NON_CONTIGUOUS_LINES", "source units for a file must be line contiguous"
                )
            previous_end = unit.end_line

    @staticmethod
    def _validate_repository(repository_url: object, repository_identity: object) -> None:
        if not isinstance(repository_url, str) or not isinstance(repository_identity, str):
            raise _SourceRecordValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            )
        try:
            parsed = urlsplit(repository_url)
            port = parsed.port
        except ValueError:
            raise _SourceRecordValidation(
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
            raise _SourceRecordValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            )
        segments = parsed.path[1:].split("/")
        if len(segments) != 2 or not all(_IDENTITY_PATTERN.fullmatch(segment) for segment in segments):
            raise _SourceRecordValidation(
                "INVALID_REPOSITORY_PROVENANCE", "source repository provenance is invalid"
            )
        identity = "/".join(segments)
        if repository_url != f"https://github.com/{identity}":
            raise _SourceRecordValidation(
                "NON_CANONICAL_REPOSITORY_URL", "source repository URL is not canonical"
            )
        if repository_identity != identity:
            raise _SourceRecordValidation(
                "REPOSITORY_IDENTITY_MISMATCH", "source repository identity does not match its URL"
            )

    @staticmethod
    def _validate_path(path: object) -> None:
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
            raise _SourceRecordValidation("INVALID_SOURCE_PATH", "source unit path is invalid")

    @staticmethod
    def _validate_identity(value: object, code: str, message: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().casefold() == "latest"
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        ):
            raise _SourceRecordValidation(code, message)
