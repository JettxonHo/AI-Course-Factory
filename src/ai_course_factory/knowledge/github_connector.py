"""Safe, read-only GitHub Source Connector for explicit public paths."""

from __future__ import annotations

import base64
from collections.abc import Callable, Mapping
from dataclasses import dataclass
import json
import math
import re
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .source import SourceAcquisitionResult, SourceConnectorFailure, SourceFile


MAX_FILE_COUNT = 20
MAX_PATH_LENGTH = 1024
MAX_FILE_BYTES = 1_048_576
MAX_TOTAL_BYTES = 4_194_304
MAX_API_RESPONSE_BYTES = 8_388_608
DEFAULT_TIMEOUT_SECONDS = 10.0
GITHUB_API_ORIGIN = "https://api.github.com"
_IDENTITY_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")
_GIT_SHA_PATTERN = re.compile(r"^[0-9a-fA-F]{40}$")


class GitHubTransportError(Exception):
    """Internal transport error with no raw response body."""


class GitHubHTTPError(GitHubTransportError):
    """Internal HTTP status error used for normalized failures."""

    def __init__(self, status: int) -> None:
        super().__init__(f"GitHub HTTP status {status}")
        self.status = status


class GitHubResponseLimitError(GitHubTransportError):
    """The bounded local response reader rejected an oversized response."""


class GitHubTransport(Protocol):
    def request(self, api_path: str) -> Any:
        ...


class _SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, new: str):
        target = urlsplit(new)
        if (
            target.scheme != "https"
            or target.hostname != "api.github.com"
            or target.username is not None
            or target.password is not None
            or target.port is not None
            or target.query
            or target.fragment
        ):
            raise GitHubTransportError("redirect outside the fixed GitHub API boundary")
        return super().redirect_request(req, fp, code, msg, headers, new)


class _UrllibGitHubTransport:
    """Default read-only transport; only receives connector-built API paths."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT_SECONDS) -> None:
        self._timeout = timeout
        self._opener = build_opener(_SafeRedirectHandler())

    def request(self, api_path: str) -> bytes:
        if not isinstance(api_path, str) or not api_path.startswith("/") or "://" in api_path:
            raise GitHubTransportError("invalid connector API path")
        url = f"{GITHUB_API_ORIGIN}{api_path}"
        request = Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "ai-course-factory-source-connector/0.1",
            },
            method="GET",
        )
        try:
            with self._opener.open(request, timeout=self._timeout) as response:
                content_length = response.headers.get("Content-Length")
                if content_length is not None:
                    try:
                        if int(content_length) > MAX_API_RESPONSE_BYTES:
                            raise GitHubResponseLimitError("API response exceeds the configured limit")
                    except ValueError as exc:
                        raise GitHubResponseLimitError("invalid API response length") from exc
                body = response.read(MAX_API_RESPONSE_BYTES + 1)
                if len(body) > MAX_API_RESPONSE_BYTES:
                    raise GitHubResponseLimitError("API response exceeds the configured limit")
                return body
        except HTTPError as exc:
            raise GitHubHTTPError(exc.code) from None
        except (URLError, TimeoutError, OSError) as exc:
            raise GitHubTransportError("GitHub transport failed") from exc


@dataclass(frozen=True, slots=True)
class _ValidatedLocator:
    owner: str
    repository: str
    canonical_url: str

    @property
    def identity(self) -> str:
        return f"{self.owner}/{self.repository}"


class _AcquireFailure(Exception):
    def __init__(self, failure: SourceConnectorFailure) -> None:
        super().__init__(failure.message)
        self.failure = failure


class GitHubSourceConnector:
    """Acquire explicit public GitHub text files at one exact commit."""

    def __init__(
        self,
        transport: GitHubTransport | Callable[[str], Any] | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError("timeout must be a finite positive number")
        self._transport = transport or _UrllibGitHubTransport(float(timeout))

    def acquire(self, repository_url: str, paths: list[str] | tuple[str, ...]) -> SourceAcquisitionResult | SourceConnectorFailure:
        """Return a complete immutable result or one normalized safe failure."""

        try:
            locator = self._validate_locator(repository_url)
            requested_paths = self._validate_paths(paths)
            metadata = self._request_json(f"/repos/{locator.owner}/{locator.repository}", "repository")
            default_branch = self._read_default_branch(metadata)
            commit_sha = self._resolve_commit(locator, default_branch)

            files: list[SourceFile] = []
            total_size = 0
            for path in requested_paths:
                file_response = self._request_json(
                    f"/repos/{locator.owner}/{locator.repository}/contents/{quote(path, safe='/')}?ref={quote(commit_sha, safe='')}",
                    "file",
                )
                source_file = self._decode_file(file_response, path)
                total_size += source_file.size_bytes
                if total_size > MAX_TOTAL_BYTES:
                    raise _AcquireFailure(
                        SourceConnectorFailure("execution", "TOTAL_CONTENT_TOO_LARGE", "requested source content exceeds the total size limit")
                    )
                files.append(source_file)
            return SourceAcquisitionResult(
                repository_url=locator.canonical_url,
                repository_identity=locator.identity,
                commit_sha=commit_sha,
                files=tuple(files),
                total_size_bytes=total_size,
            )
        except _AcquireFailure as exc:
            return exc.failure
        except GitHubTransportError:
            return SourceConnectorFailure("source_access", "TRANSPORT_ERROR", "GitHub source acquisition failed")
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return SourceConnectorFailure("execution", "CONNECTOR_EXECUTION_FAILED", "GitHub source acquisition failed")
        except Exception:
            # The public boundary never leaks provider objects, response bodies
            # or implementation stack traces.
            return SourceConnectorFailure("execution", "CONNECTOR_EXECUTION_FAILED", "GitHub source acquisition failed")

    @staticmethod
    def _validate_locator(repository_url: str) -> _ValidatedLocator:
        if not isinstance(repository_url, str) or any(ord(char) < 0x20 or ord(char) == 0x7F for char in repository_url):
            raise _AcquireFailure(SourceConnectorFailure("validation", "INVALID_REPOSITORY_LOCATOR", "repository locator is invalid"))
        try:
            parsed = urlsplit(repository_url)
            hostname = parsed.hostname
            port = parsed.port
        except ValueError:
            raise _AcquireFailure(
                SourceConnectorFailure("validation", "INVALID_REPOSITORY_LOCATOR", "repository locator is invalid")
            ) from None
        if (
            parsed.scheme != "https"
            or hostname != "github.com"
            or parsed.username is not None
            or parsed.password is not None
            or port is not None
            or parsed.query
            or parsed.fragment
            or not parsed.path.startswith("/")
            or parsed.path.endswith("/")
        ):
            raise _AcquireFailure(SourceConnectorFailure("validation", "INVALID_REPOSITORY_LOCATOR", "repository locator is invalid"))
        segments = parsed.path[1:].split("/")
        if len(segments) != 2 or not all(_IDENTITY_PATTERN.fullmatch(part) for part in segments):
            raise _AcquireFailure(SourceConnectorFailure("validation", "INVALID_REPOSITORY_LOCATOR", "repository locator is invalid"))
        owner, repository = segments
        return _ValidatedLocator(owner, repository, f"https://github.com/{owner}/{repository}")

    @staticmethod
    def _validate_paths(paths: list[str] | tuple[str, ...]) -> tuple[str, ...]:
        if isinstance(paths, (str, bytes)) or not isinstance(paths, (list, tuple)) or not paths:
            raise _AcquireFailure(SourceConnectorFailure("validation", "INVALID_PATHS", "explicit source paths are required"))
        if len(paths) > MAX_FILE_COUNT:
            raise _AcquireFailure(SourceConnectorFailure("validation", "FILE_COUNT_LIMIT", "too many source paths were requested"))
        validated: list[str] = []
        seen: set[str] = set()
        for path in paths:
            if not isinstance(path, str) or not path or len(path) > MAX_PATH_LENGTH:
                raise _AcquireFailure(SourceConnectorFailure("validation", "INVALID_PATHS", "source paths are invalid"))
            if path in seen or path.startswith("/") or "\\" in path or any(ord(char) < 0x20 or ord(char) == 0x7F for char in path):
                raise _AcquireFailure(SourceConnectorFailure("validation", "INVALID_PATHS", "source paths are invalid"))
            parts = path.split("/")
            if any(part in ("", ".", "..") for part in parts):
                raise _AcquireFailure(SourceConnectorFailure("validation", "INVALID_PATHS", "source paths are invalid"))
            seen.add(path)
            validated.append(path)
        return tuple(validated)

    def _request_json(self, api_path: str, operation: str) -> Any:
        try:
            if hasattr(self._transport, "request"):
                response = self._transport.request(api_path)  # type: ignore[union-attr]
            else:
                response = self._transport(api_path)  # type: ignore[operator]
        except GitHubHTTPError as exc:
            code = {
                "repository": "REPOSITORY_NOT_FOUND",
                "commit": "COMMIT_NOT_FOUND",
                "file": "FILE_NOT_FOUND",
            }.get(operation, "HTTP_ERROR") if exc.status == 404 else "HTTP_ERROR"
            raise _AcquireFailure(SourceConnectorFailure("source_access", code, "GitHub source request failed")) from None
        except GitHubResponseLimitError:
            raise _AcquireFailure(SourceConnectorFailure("execution", "API_RESPONSE_TOO_LARGE", "GitHub source response exceeds the size limit")) from None
        except GitHubTransportError:
            raise _AcquireFailure(SourceConnectorFailure("source_access", "TRANSPORT_ERROR", "GitHub source request failed")) from None
        except Exception:
            raise _AcquireFailure(SourceConnectorFailure("source_access", "TRANSPORT_ERROR", "GitHub source request failed")) from None

        if isinstance(response, Mapping) or isinstance(response, list):
            return response
        if isinstance(response, str):
            raw = response.encode("utf-8")
        elif isinstance(response, bytes):
            raw = response
        else:
            raise _AcquireFailure(SourceConnectorFailure("execution", "MALFORMED_RESPONSE", "GitHub source response is invalid"))
        if len(raw) > MAX_API_RESPONSE_BYTES:
            raise _AcquireFailure(SourceConnectorFailure("execution", "API_RESPONSE_TOO_LARGE", "GitHub source response exceeds the size limit"))
        try:
            return json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise _AcquireFailure(SourceConnectorFailure("execution", "MALFORMED_RESPONSE", "GitHub source response is invalid")) from None

    @staticmethod
    def _read_default_branch(metadata: Any) -> str:
        if not isinstance(metadata, Mapping) or not isinstance(metadata.get("default_branch"), str):
            raise _AcquireFailure(SourceConnectorFailure("execution", "MALFORMED_REPOSITORY_RESPONSE", "GitHub repository response is invalid"))
        branch = metadata["default_branch"]
        if not branch or len(branch) > 256 or any(ord(char) < 0x20 or ord(char) == 0x7F for char in branch):
            raise _AcquireFailure(SourceConnectorFailure("execution", "MALFORMED_REPOSITORY_RESPONSE", "GitHub repository response is invalid"))
        return branch

    def _resolve_commit(self, locator: _ValidatedLocator, default_branch: str) -> str:
        response = self._request_json(
            f"/repos/{locator.owner}/{locator.repository}/commits?sha={quote(default_branch, safe='')}&per_page=1",
            "commit",
        )
        sha: Any = None
        if isinstance(response, list) and response and isinstance(response[0], Mapping):
            sha = response[0].get("sha")
        elif isinstance(response, Mapping):
            sha = response.get("sha")
            if sha is None and isinstance(response.get("object"), Mapping):
                sha = response["object"].get("sha")
        if not isinstance(sha, str) or not _GIT_SHA_PATTERN.fullmatch(sha):
            raise _AcquireFailure(SourceConnectorFailure("execution", "MALFORMED_COMMIT_RESPONSE", "GitHub commit response is invalid"))
        return sha

    @staticmethod
    def _decode_file(response: Any, requested_path: str) -> SourceFile:
        if not isinstance(response, Mapping):
            raise _AcquireFailure(SourceConnectorFailure("execution", "MALFORMED_FILE_RESPONSE", "GitHub file response is invalid"))
        if response.get("type") != "file" or response.get("path") != requested_path:
            raise _AcquireFailure(SourceConnectorFailure("execution", "FILE_METADATA_MISMATCH", "GitHub file metadata is invalid"))
        blob_sha = response.get("sha")
        encoding = response.get("encoding")
        content = response.get("content")
        size = response.get("size")
        if (
            not isinstance(blob_sha, str)
            or not _GIT_SHA_PATTERN.fullmatch(blob_sha)
            or encoding != "base64"
            or not isinstance(content, str)
            or not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
        ):
            raise _AcquireFailure(SourceConnectorFailure("execution", "FILE_METADATA_MISMATCH", "GitHub file metadata is invalid"))
        if size > MAX_FILE_BYTES:
            raise _AcquireFailure(SourceConnectorFailure("execution", "FILE_CONTENT_TOO_LARGE", "source file exceeds the size limit"))
        # GitHub may wrap base64 with CR/LF; other whitespace is not silently
        # discarded because it would weaken malformed-content validation.
        compact_content = content.replace("\r", "").replace("\n", "")
        try:
            decoded = base64.b64decode(compact_content, validate=True)
        except (ValueError, base64.binascii.Error):
            raise _AcquireFailure(SourceConnectorFailure("execution", "INVALID_BASE64", "source file encoding is invalid")) from None
        if len(decoded) != size:
            raise _AcquireFailure(SourceConnectorFailure("execution", "FILE_METADATA_MISMATCH", "GitHub file metadata is invalid"))
        try:
            text = decoded.decode("utf-8")
        except UnicodeDecodeError:
            raise _AcquireFailure(SourceConnectorFailure("execution", "INVALID_UTF8", "source file is not valid UTF-8 text")) from None
        return SourceFile(path=requested_path, blob_sha=blob_sha, text=text, size_bytes=size)
