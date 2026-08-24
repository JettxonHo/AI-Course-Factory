"""Bounded Creator-authored Script Package intake.

The package is deliberately a small value boundary.  It validates the complete
file before an Artifact or application-state mutation and keeps the accepted
JSON value intact for replay and provenance inspection.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any

from ai_course_factory.artifacts import ArtifactCandidate, ArtifactReference, ArtifactVersion


PACKAGE_SCHEMA = "ai-course-factory.creator-script-package"
PACKAGE_VERSION = 1
PACKAGE_FILENAME = "creator-script.json"
MAX_PACKAGE_BYTES = 256 * 1024
MAX_ITEMS = 256
MAX_TEXT_LENGTH = 16_384
MAX_ID_LENGTH = 256
MAX_PROVENANCE_STRING_LENGTH = 512
MAX_REVISION_NOTE_LENGTH = 4096
_TOP_LEVEL_FIELDS = frozenset(
    {
        "schema",
        "version",
        "script_package_id",
        "source",
        "claims",
        "narration_units",
        "creator_provenance",
        "revision_note",
    }
)
_SOURCE_FIELDS = frozenset({"repository_url", "repository_identity", "commit_sha", "files"})
_SOURCE_FILE_FIELDS = frozenset({"path", "blob_sha"})
_CLAIM_FIELDS = frozenset({"claim_id", "statement", "evidence_locators"})
_UNIT_FIELDS = frozenset({"unit_id", "text", "claim_ids"})
_PROVENANCE_REQUIRED = frozenset({"creator_declared_name", "creator_role", "tool_name"})
_PROVENANCE_OPTIONAL = frozenset({"tool_version", "session", "project"})
_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_ID_RE = re.compile(r"^[^\x00-\x1f\x7f]+$")


@dataclass(frozen=True, slots=True)
class CreatorScriptClaim:
    claim_id: str
    statement: str
    evidence_locators: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CreatorScriptNarrationUnit:
    unit_id: str
    text: str
    claim_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CreatorScriptProvenance:
    creator_declared_name: str
    creator_role: str
    tool_name: str
    tool_version: object = None
    session: object = None
    project: object = None
    tool_version_present: bool = False
    session_present: bool = False
    project_present: bool = False

    def as_payload(self) -> dict[str, object]:
        value: dict[str, object] = {
            "creator_declared_name": self.creator_declared_name,
            "creator_role": self.creator_role,
            "tool_name": self.tool_name,
        }
        for name, item, present in (
            ("tool_version", self.tool_version, self.tool_version_present),
            ("session", self.session, self.session_present),
            ("project", self.project, self.project_present),
        ):
            if present:
                value[name] = item
        return value


@dataclass(frozen=True, slots=True)
class CreatorScriptPackage:
    """Accepted package plus typed projections; ``payload`` is complete."""

    payload: Mapping[str, object]
    script_package_id: str
    source: Mapping[str, object]
    claims: tuple[CreatorScriptClaim, ...]
    narration_units: tuple[CreatorScriptNarrationUnit, ...]
    creator_provenance: CreatorScriptProvenance
    revision_note: str | None

    @property
    def canonical_value(self) -> Mapping[str, object]:
        return self.payload


@dataclass(frozen=True, slots=True)
class CreatorScriptPackageFailure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class CreatorScriptPackageResult:
    package: CreatorScriptPackage | None = None
    candidate: ArtifactCandidate | None = None
    reference: ArtifactReference | None = None
    failure: CreatorScriptPackageFailure | None = None

    @property
    def status(self) -> str:
        return "success" if self.package is not None and self.failure is None else "failure"

    @property
    def error_code(self) -> str | None:
        return self.failure.code if self.failure else None


class _PackageError(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _freeze(item) for key, item in value.items()}
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _PackageError("DUPLICATE_JSON_KEY", "creator Script Package contains duplicate object keys")
        result[key] = value
    return result


def _text(value: object, *, field: str, maximum: int = MAX_TEXT_LENGTH, nonempty: bool = True) -> str:
    if not isinstance(value, str) or len(value) > maximum or (nonempty and not value.strip()):
        raise _PackageError("INVALID_PACKAGE_FIELD", f"creator Script Package field {field} is invalid")
    if any(ord(char) < 0x20 or ord(char) == 0x7f for char in value):
        raise _PackageError("INVALID_PACKAGE_FIELD", f"creator Script Package field {field} contains control characters")
    return value


def _bounded_id(value: object, *, field: str) -> str:
    text = _text(value, field=field, maximum=MAX_ID_LENGTH)
    if not _ID_RE.fullmatch(text) or not text.strip() or text.strip().casefold() == "latest":
        raise _PackageError("INVALID_PACKAGE_FIELD", f"creator Script Package field {field} is invalid")
    return text


def _object(value: object, *, field: str, fields: frozenset[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise _PackageError("INVALID_PACKAGE_SCHEMA", f"creator Script Package {field} object has invalid fields")
    return value


def _validate_provenance(value: object) -> CreatorScriptProvenance:
    if not isinstance(value, dict) or not _PROVENANCE_REQUIRED.issubset(value) or set(value) - (_PROVENANCE_REQUIRED | _PROVENANCE_OPTIONAL):
        raise _PackageError("INVALID_CREATOR_PROVENANCE", "creator provenance fields are invalid")
    required = tuple(_text(value[name], field=f"creator_provenance.{name}", maximum=MAX_PROVENANCE_STRING_LENGTH) for name in sorted(_PROVENANCE_REQUIRED))
    optional: list[object] = []
    present: list[bool] = []
    for name in ("tool_version", "session", "project"):
        if name not in value:
            optional.append(None)
            present.append(False)
        elif value[name] is None:
            optional.append(None)
            present.append(True)
        else:
            optional.append(_text(value[name], field=f"creator_provenance.{name}", maximum=MAX_PROVENANCE_STRING_LENGTH))
            present.append(True)
    # required tuple is sorted alphabetically: creator_declared_name, creator_role, tool_name.
    return CreatorScriptProvenance(
        required[0], required[1], required[2], optional[0], optional[1], optional[2], present[0], present[1], present[2]
    )


def parse_creator_script_package(raw: bytes | bytearray | memoryview) -> CreatorScriptPackage | CreatorScriptPackageFailure:
    """Parse and validate one complete JSON package without source membership."""

    try:
        if not isinstance(raw, (bytes, bytearray, memoryview)):
            raise _PackageError("INVALID_PACKAGE_BYTES", "creator Script Package bytes are required")
        data = bytes(raw)
        if len(data) > MAX_PACKAGE_BYTES:
            raise _PackageError("PACKAGE_TOO_LARGE", "creator Script Package exceeds the 256 KiB limit")
        try:
            decoded = data.decode("utf-8")
        except UnicodeDecodeError:
            raise _PackageError("INVALID_PACKAGE_UTF8", "creator Script Package must be UTF-8 JSON") from None
        try:
            value = json.loads(decoded, object_pairs_hook=_reject_duplicates)
        except _PackageError:
            raise
        except (TypeError, ValueError):
            raise _PackageError("INVALID_PACKAGE_JSON", "creator Script Package is not valid JSON") from None
        if not isinstance(value, dict) or set(value) != _TOP_LEVEL_FIELDS:
            raise _PackageError("INVALID_PACKAGE_SCHEMA", "creator Script Package must contain exactly the eight schema-v1 fields")
        if value["schema"] != PACKAGE_SCHEMA or type(value["schema"]) is not str:
            raise _PackageError("INVALID_PACKAGE_SCHEMA", "creator Script Package discriminator is invalid")
        if value["version"] != PACKAGE_VERSION or type(value["version"]) is not int:
            raise _PackageError("INVALID_PACKAGE_SCHEMA", "creator Script Package version is invalid")
        package_id = _bounded_id(value["script_package_id"], field="script_package_id")
        source = _object(value["source"], field="source", fields=_SOURCE_FIELDS)
        _text(source["repository_url"], field="source.repository_url", maximum=2048)
        _bounded_id(source["repository_identity"], field="source.repository_identity")
        commit = _text(source["commit_sha"], field="source.commit_sha", maximum=64)
        if _SHA_RE.fullmatch(commit) is None:
            raise _PackageError("INVALID_SOURCE_IDENTITY", "creator Script Package commit SHA is invalid")
        files = source["files"]
        if not isinstance(files, list) or not 1 <= len(files) <= MAX_ITEMS:
            raise _PackageError("INVALID_SOURCE_FILES", "creator Script Package source.files is invalid")
        seen_files: set[str] = set()
        for item in files:
            file_value = _object(item, field="source.files[]", fields=_SOURCE_FILE_FIELDS)
            path = _bounded_id(file_value["path"], field="source.files[].path")
            blob = _text(file_value["blob_sha"], field="source.files[].blob_sha", maximum=64)
            if _SHA_RE.fullmatch(blob) is None or path in seen_files:
                raise _PackageError("INVALID_SOURCE_FILES", "creator Script Package source.files contains invalid or duplicate entries")
            seen_files.add(path)
        claims = value["claims"]
        if not isinstance(claims, list) or not 1 <= len(claims) <= MAX_ITEMS:
            raise _PackageError("INVALID_CLAIMS", "creator Script Package claims are invalid")
        typed_claims: list[CreatorScriptClaim] = []
        claim_ids: set[str] = set()
        for item in claims:
            claim = _object(item, field="claims[]", fields=_CLAIM_FIELDS)
            claim_id = _bounded_id(claim["claim_id"], field="claims[].claim_id")
            if claim_id in claim_ids:
                raise _PackageError("INVALID_CLAIMS", "creator Script Package claim IDs must be unique")
            claim_ids.add(claim_id)
            statement = _text(claim["statement"], field="claims[].statement")
            locators = claim["evidence_locators"]
            if not isinstance(locators, list) or not locators:
                raise _PackageError("INVALID_CLAIMS", "every creator claim requires evidence locators")
            typed_locators = tuple(_text(locator, field="claims[].evidence_locators[]", maximum=4096) for locator in locators)
            if len(set(typed_locators)) != len(typed_locators):
                raise _PackageError("INVALID_CLAIMS", "claim evidence locators must be unique")
            typed_claims.append(CreatorScriptClaim(claim_id, statement, typed_locators))
        units = value["narration_units"]
        if not isinstance(units, list) or not 1 <= len(units) <= MAX_ITEMS:
            raise _PackageError("INVALID_NARRATION_UNITS", "creator Script Package narration_units are invalid")
        typed_units: list[CreatorScriptNarrationUnit] = []
        unit_ids: set[str] = set()
        for item in units:
            unit = _object(item, field="narration_units[]", fields=_UNIT_FIELDS)
            unit_id = _bounded_id(unit["unit_id"], field="narration_units[].unit_id")
            if unit_id in unit_ids:
                raise _PackageError("INVALID_NARRATION_UNITS", "creator narration unit IDs must be unique")
            unit_ids.add(unit_id)
            text = _text(unit["text"], field="narration_units[].text")
            refs = unit["claim_ids"]
            if not isinstance(refs, list) or not refs or any(not isinstance(ref, str) for ref in refs):
                raise _PackageError("INVALID_NARRATION_UNITS", "every narration unit requires claim IDs")
            typed_refs = tuple(_bounded_id(ref, field="narration_units[].claim_ids[]") for ref in refs)
            if not set(typed_refs).issubset(claim_ids):
                raise _PackageError("UNKNOWN_CLAIM_ID", "narration unit references an unknown claim")
            typed_units.append(CreatorScriptNarrationUnit(unit_id, text, typed_refs))
        provenance = _validate_provenance(value["creator_provenance"])
        revision_note = value["revision_note"]
        if revision_note is not None:
            revision_note = _text(revision_note, field="revision_note", maximum=MAX_REVISION_NOTE_LENGTH)
        frozen = _freeze(value)
        return CreatorScriptPackage(frozen, package_id, _freeze(source), tuple(typed_claims), tuple(typed_units), provenance, revision_note)
    except _PackageError as exc:
        return CreatorScriptPackageFailure("validation", exc.code, exc.message)
    except Exception:
        return CreatorScriptPackageFailure("execution", "PACKAGE_VALIDATION_FAILED", "creator Script Package validation failed")


def read_creator_script_file(directory: str | os.PathLike[str] | Path) -> bytes | CreatorScriptPackageFailure:
    """Read only the fixed regular, non-symlink package member."""

    try:
        if not isinstance(directory, (str, os.PathLike)):
            raise _PackageError("SCRIPT_PACKAGE_DIRECTORY_REQUIRED", "an explicit Script-package directory is required")
        root_input = Path(directory).expanduser()
        if root_input.is_symlink():
            raise _PackageError("SCRIPT_PACKAGE_DIRECTORY_REQUIRED", "an explicit Script-package directory is required")
        root = root_input.resolve()
        if not root.is_dir():
            raise _PackageError("SCRIPT_PACKAGE_DIRECTORY_REQUIRED", "an explicit Script-package directory is required")
        path = root / PACKAGE_FILENAME
        stat = path.lstat()
        if path.is_symlink() or not path.is_file():
            raise _PackageError("SCRIPT_PACKAGE_FILE_INVALID", "creator-script.json must be one regular non-symlink file")
        if stat.st_size > MAX_PACKAGE_BYTES:
            raise _PackageError("PACKAGE_TOO_LARGE", "creator Script Package exceeds the 256 KiB limit")
        with path.open("rb") as handle:
            data = handle.read(MAX_PACKAGE_BYTES + 1)
        if len(data) > MAX_PACKAGE_BYTES:
            raise _PackageError("PACKAGE_TOO_LARGE", "creator Script Package exceeds the 256 KiB limit")
        return data
    except _PackageError as exc:
        return CreatorScriptPackageFailure("validation", exc.code, exc.message)
    except (OSError, ValueError):
        return CreatorScriptPackageFailure("execution", "SCRIPT_PACKAGE_READ_FAILED", "creator Script Package could not be read")


def validate_source_membership(package: CreatorScriptPackage, source_reference: ArtifactReference, source_version: ArtifactVersion) -> CreatorScriptPackageFailure | None:
    """Check exact GitHub Source identity, projected files and locator membership."""

    try:
        if source_reference.artifact_type != "source_record" or source_version.reference != source_reference:
            raise _PackageError("SOURCE_REFERENCE_INVALID", "current Source Record reference is invalid")
        payload = source_version.payload
        if not isinstance(payload, Mapping) or payload.get("source_kind") != "github":
            raise _PackageError("SOURCE_NOT_GITHUB", "current Source Record must be a GitHub source")
        source = package.source
        for name in ("repository_url", "repository_identity", "commit_sha"):
            if source.get(name) != payload.get(name):
                raise _PackageError("SOURCE_IDENTITY_MISMATCH", "creator Script Package Source does not match the current Source Record")
        units = payload.get("units")
        if not isinstance(units, (tuple, list)) or not units:
            raise _PackageError("SOURCE_UNITS_INVALID", "current Source Record units are invalid")
        projection: list[dict[str, str]] = []
        seen: dict[str, str] = {}
        locators: set[str] = set()
        for unit in units:
            if not isinstance(unit, Mapping):
                raise _PackageError("SOURCE_UNITS_INVALID", "current Source Record units are invalid")
            path, blob = unit.get("path"), unit.get("blob_sha")
            locator = unit.get("locator")
            if not isinstance(path, str) or not isinstance(blob, str) or not isinstance(locator, str):
                raise _PackageError("SOURCE_UNITS_INVALID", "current Source Record units are invalid")
            prior = seen.get(path)
            if prior is not None and prior != blob:
                raise _PackageError("SOURCE_BLOB_CONFLICT", "one Source path maps to multiple blob identities")
            if prior is None:
                seen[path] = blob
                projection.append({"path": path, "blob_sha": blob})
            locators.add(locator)
        if tuple(projection) != tuple(package.source.get("files", ())):
            raise _PackageError("SOURCE_FILES_MISMATCH", "creator Script Package source.files does not match the current Source projection")
        for claim in package.claims:
            if any(locator not in locators for locator in claim.evidence_locators):
                raise _PackageError("FOREIGN_LOCATOR", "creator Script Package claim evidence is not in the current Source")
    except _PackageError as exc:
        return CreatorScriptPackageFailure("validation", exc.code, exc.message)
    except Exception:
        return CreatorScriptPackageFailure("execution", "SOURCE_VALIDATION_FAILED", "creator Script Package Source validation failed")
    return None


class CreatorScriptPackageApplicationService:
    """Parse, preflight and build one immutable Script Artifact candidate."""

    def __init__(self, artifacts: object) -> None:
        self.artifacts = artifacts

    def import_package(
        self,
        directory: str | os.PathLike[str] | Path,
        *,
        source_reference: ArtifactReference,
        source_version: ArtifactVersion,
        script_reference: ArtifactReference | None = None,
        script_version: ArtifactVersion | None = None,
    ) -> CreatorScriptPackageResult:
        raw = read_creator_script_file(directory)
        if isinstance(raw, CreatorScriptPackageFailure):
            return CreatorScriptPackageResult(failure=raw)
        parsed = parse_creator_script_package(raw)
        if isinstance(parsed, CreatorScriptPackageFailure):
            return CreatorScriptPackageResult(failure=parsed)
        invalid_source = validate_source_membership(parsed, source_reference, source_version)
        if invalid_source is not None:
            return CreatorScriptPackageResult(failure=invalid_source)
        prior = script_reference
        if script_version is not None and script_version.payload.get("script_package") == parsed.payload:
            # The facade resolves exact replay before asking Artifact Commit;
            # retaining this branch makes the service safe for direct callers.
            return CreatorScriptPackageResult(package=parsed, reference=script_reference)
        candidate = ArtifactCandidate(
            artifact_type="script",
            identity="script:episode-1",
            payload={"script_package": parsed.payload},
            provenance=(
                {"source_reference": source_reference, "script_package_id": parsed.script_package_id, "creator_provenance": parsed.creator_provenance.as_payload()},
            ),
            dependencies=(source_reference,),
            validated=True,
            commit_id=f"script:episode-1:creator:{parsed.script_package_id}:v{(script_reference.version + 1) if script_reference else 1}",
            prior_reference=prior,
        )
        return CreatorScriptPackageResult(package=parsed, candidate=candidate)


__all__ = [
    "CreatorScriptClaim",
    "CreatorScriptNarrationUnit",
    "CreatorScriptPackage",
    "CreatorScriptPackageApplicationService",
    "CreatorScriptPackageFailure",
    "CreatorScriptPackageResult",
    "CreatorScriptProvenance",
    "MAX_PACKAGE_BYTES",
    "PACKAGE_FILENAME",
    "PACKAGE_SCHEMA",
    "PACKAGE_VERSION",
    "parse_creator_script_package",
    "read_creator_script_file",
    "validate_source_membership",
]
