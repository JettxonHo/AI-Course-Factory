"""Deterministic, approval-gated Publish Package construction."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import hashlib
import io
import json
from types import MappingProxyType
import zipfile

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactReference,
    ArtifactVersion,
    FinalVideoDecisionRecord,
)
from ai_course_factory.artifacts.model import freeze_value
from ai_course_factory.persistence import WorkspaceFileRecord, WorkspaceFileReference, WorkspaceFailure


_MAX_IDENTITY = 256
_MAX_COMPONENT = 128
_MAX_GRAPH_NODES = 256
_MAX_VIDEO_BYTES = 128 * 1024 * 1024
_MAX_JSON_BYTES = 4 * 1024 * 1024
_MAX_DURATION_MS = 24 * 60 * 60 * 1000
_HEX = frozenset("0123456789abcdefABCDEF")
_ALNUM = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
_TOKEN = _ALNUM | frozenset("._-:")
_LOCAL_IMPORTED_PROVIDER = "local-import-operator-declared-external-source"
_TTS_ATTRIBUTION_KEYS = frozenset({
    "engine",
    "engine_version",
    "repository_commit",
    "model_identifier",
    "runtime",
    "reference_provenance",
    "reference_transcript",
    "application_provider_api_call",
    "external_charge_micros",
})
_TTS_ATTRIBUTION_VALUES = {
    "engine": "local-gpt-sovits-v2",
    "engine_version": "v2",
    "repository_commit": "d523079fc05d9a8028d6085bffe4a2757c32abb6",
    "model_identifier": "gsv-v2final-pretrained",
    "runtime": "external Python 3.11 + GPT-SoVITS repository",
    "reference_provenance": "locally generated Qwen3-TTS Serena synthetic reference",
    "reference_transcript": "你好，我是小土豆。今天我们一起认识人工智能。",
}


@dataclass(frozen=True, slots=True)
class PackagingFailure:
    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class PublishPackageResult:
    task_id: str
    source_record_reference: ArtifactReference
    subtitle_reference: ArtifactReference
    video_reference: ArtifactReference
    final_video_decision_id: str
    manifest_reference: ArtifactReference
    package_reference: ArtifactReference
    output_reference: WorkspaceFileReference
    result_code: str


class _Invalid(Exception):
    def __init__(self, code: str, message: str = "publish package input is invalid") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
def _failure(kind: str, code: str, message: str) -> PackagingFailure:
    return PackagingFailure(kind, code, message)


def _tts_attribution(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or any(type(key) is not str for key in value) or set(value) != _TTS_ATTRIBUTION_KEYS:
        raise _Invalid("INVALID_TTS_ATTRIBUTION")
    for key, expected in _TTS_ATTRIBUTION_VALUES.items():
        if type(value.get(key)) is not str or value[key] != expected:
            raise _Invalid("INVALID_TTS_ATTRIBUTION")
    if type(value.get("application_provider_api_call")) is not bool or value["application_provider_api_call"] is not False:
        raise _Invalid("INVALID_TTS_ATTRIBUTION")
    if type(value.get("external_charge_micros")) is not int or isinstance(value["external_charge_micros"], bool) or value["external_charge_micros"] != 0:
        raise _Invalid("INVALID_TTS_ATTRIBUTION")
    return {key: value[key] for key in _TTS_ATTRIBUTION_KEYS}


def _text(value: object, *, code: str, limit: int = _MAX_IDENTITY, token: bool = False) -> str:
    if type(value) is not str or not value.strip() or len(value) > limit:
        raise _Invalid(code)
    if value.strip().casefold() in {"latest", "current"}:
        raise _Invalid(code)
    if any(ord(char) < 0x20 or ord(char) == 0x7F for char in value):
        raise _Invalid(code)
    if token and (value[0] not in _ALNUM or any(char not in _TOKEN for char in value)):
        raise _Invalid(code)
    return value
def _same_ref(first: object, second: object) -> bool:
    return (
        type(first) is ArtifactReference
        and type(second) is ArtifactReference
        and type(first.artifact_type) is str
        and type(first.identity) is str
        and type(first.version) is int
        and not isinstance(first.version, bool)
        and type(second.artifact_type) is str
        and type(second.identity) is str
        and type(second.version) is int
        and not isinstance(second.version, bool)
        and (first.artifact_type, first.identity, first.version)
        == (second.artifact_type, second.identity, second.version)
    )


def _refs_equal(first: object, second: object) -> bool:
    return type(first) is tuple and type(second) is tuple and len(first) == len(second) and all(_same_ref(left, right) for left, right in zip(first, second))


def _reference(value: object, artifact_type: str, code: str) -> ArtifactReference:
    if type(value) is not ArtifactReference or type(value.artifact_type) is not str or type(value.identity) is not str or type(value.version) is not int or isinstance(value.version, bool):
        raise _Invalid(code)
    _text(value.artifact_type, code=code, token=True)
    _text(value.identity, code=code, token=True)
    if value.artifact_type != artifact_type or value.version < 1:
        raise _Invalid(code)
    return value


def _mapping(value: object, keys: set[str], code: str) -> MappingProxyType:
    if type(value) is not MappingProxyType or any(type(key) is not str for key in value) or set(value) != keys:
        raise _Invalid(code)
    return value


def _version(value: object, reference: ArtifactReference, code: str) -> ArtifactVersion:
    if type(value) is not ArtifactVersion or not _same_ref(value.reference, reference):
        raise _Invalid(code)
    if type(value.payload) is not MappingProxyType or type(value.provenance) is not tuple or type(value.dependencies) is not tuple:
        raise _Invalid(code)
    for dependency in value.dependencies:
        if type(dependency) is not ArtifactReference:
            raise _Invalid(code)
        _reference(dependency, dependency.artifact_type, code)
    _text(value.commit_id, code=code)
    if value.prior_reference is not None: _reference(value.prior_reference, value.reference.artifact_type, code)
    return value


def _safe_workspace(value: object, task_id: str, area: str, code: str, suffix: str | None = None) -> WorkspaceFileReference:
    if type(value) is not WorkspaceFileReference or type(value.task_id) is not str or type(value.area) is not str or type(value.name) is not str:
        raise _Invalid(code)
    _text(value.task_id, code=code, token=True)
    _text(value.area, code=code, token=True)
    _text(value.name, code=code, limit=_MAX_COMPONENT, token=True)
    if value.task_id != task_id or value.area != area or suffix is not None and not value.name.endswith(suffix):
        raise _Invalid(code)
    return value


def _ref_json(reference: ArtifactReference) -> dict[str, object]:
    return {
        "artifact_type": reference.artifact_type,
        "identity": reference.identity,
        "version": reference.version,
    }


def _canonical_json(value: object) -> bytes:
    try:
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        result = encoded.encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        raise _Invalid("CANONICAL_JSON_FAILED") from None
    if len(result) > _MAX_JSON_BYTES:
        raise _Invalid("PACKAGE_OUTPUT_TOO_LARGE")
    return result


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source_version(reference: ArtifactReference, version: ArtifactVersion) -> dict[str, object]:
    _version(version, reference, "INVALID_SOURCE_VERSION")
    payload = _mapping(
        version.payload,
        {"source_kind", "repository_url", "repository_identity", "commit_sha", "units"},
        "INVALID_SOURCE_RECORD",
    )
    if type(payload["source_kind"]) is not str or payload["source_kind"] != "github":
        raise _Invalid("INVALID_SOURCE_RECORD")
    repository_url = _text(payload["repository_url"], code="INVALID_SOURCE_RECORD")
    repository_identity = _text(payload["repository_identity"], code="INVALID_SOURCE_RECORD")
    owner, separator, repo = repository_identity.partition("/")
    if (not separator or not owner or not repo or any(not item or item[0] not in _ALNUM or any(char not in (_ALNUM | frozenset("._-")) for char in item) for item in (owner, repo)) or repository_url != f"https://github.com/{repository_identity}"):
        raise _Invalid("INVALID_SOURCE_RECORD")
    commit_sha = payload["commit_sha"]
    if type(commit_sha) is not str or len(commit_sha) != 40 or any(char not in _HEX for char in commit_sha):
        raise _Invalid("INVALID_SOURCE_RECORD")
    units = payload["units"]
    if type(units) is not tuple or not units:
        raise _Invalid("INVALID_SOURCE_RECORD")
    facts: list[dict[str, object]] = []
    prior_path: str | None = None
    prior_end: int | None = None
    prior_blob: str | None = None
    closed: set[str] = set()
    for unit in units:
        unit = _mapping(
            unit,
            {"locator", "path", "blob_sha", "heading_path", "start_line", "end_line", "text"},
            "INVALID_SOURCE_RECORD",
        )
        path = _text(unit["path"], code="INVALID_SOURCE_RECORD", limit=1024)
        if path.startswith("/") or "\\" in path or any(part in {"", ".", ".."} for part in path.split("/")):
            raise _Invalid("INVALID_SOURCE_RECORD")
        blob = unit["blob_sha"]
        if type(blob) is not str or len(blob) != 40 or any(char not in _HEX for char in blob):
            raise _Invalid("INVALID_SOURCE_RECORD")
        heading = unit["heading_path"]
        if type(heading) is not tuple or any(type(item) is not str for item in heading):
            raise _Invalid("INVALID_SOURCE_RECORD")
        start, end = unit["start_line"], unit["end_line"]
        if type(start) is not int or isinstance(start, bool) or type(end) is not int or isinstance(end, bool) or start < 1 or end < start:
            raise _Invalid("INVALID_SOURCE_RECORD")
        text = unit["text"]
        if type(text) is not str or not text or any(ord(char) in {0, 0x7F} for char in text):
            raise _Invalid("INVALID_SOURCE_RECORD")
        try:
            text.encode("utf-8")
        except UnicodeError:
            raise _Invalid("INVALID_SOURCE_RECORD") from None
        line_count = len(text.splitlines())
        if line_count != end - start + 1:
            raise _Invalid("INVALID_SOURCE_RECORD")
        locator = unit["locator"]
        expected = f"{repository_identity}@{commit_sha}:{path}#L{start}-L{end}"
        if type(locator) is not str or locator != expected:
            raise _Invalid("INVALID_SOURCE_RECORD")
        if prior_path != path:
            if path in closed or start != 1:
                raise _Invalid("INVALID_SOURCE_RECORD")
            if prior_path is not None:
                closed.add(prior_path)
            prior_path, prior_blob, prior_end = path, blob, None
        elif blob != prior_blob:
            raise _Invalid("INVALID_SOURCE_RECORD")
        if prior_end is not None and start != prior_end + 1:
            raise _Invalid("INVALID_SOURCE_RECORD")
        prior_end = end
        facts.append({"locator": locator, "path": path, "blob_sha": blob, "start_line": start, "end_line": end})
    attribution = {
        "repository_url": repository_url,
        "repository_identity": repository_identity,
        "commit_sha": commit_sha,
        "units": facts,
    }
    return attribution


def _visual_import_attribution(repository: object, video_payload: MappingProxyType) -> dict[str, object] | None:
    clips = video_payload.get("scene_clip_references")
    scene_ids = video_payload.get("scene_ids")
    if type(clips) is not tuple or type(scene_ids) is not tuple or len(clips) != len(scene_ids):
        return None
    assets: list[dict[str, object]] = []
    for scene_id, reference in zip(scene_ids, clips):
        try:
            clip = repository.get(reference)
        except Exception:
            return None
        payload = clip.payload if type(clip) is ArtifactVersion else None
        if not isinstance(payload, MappingProxyType) or payload.get("provider") != _LOCAL_IMPORTED_PROVIDER:
            return None
        output = payload.get("output_reference")
        if not isinstance(output, MappingProxyType):
            return None
        output_name = output.get("name")
        if type(output_name) is not str or not output_name.endswith(".mp4"):
            return None
        target = output_name.removesuffix(".mp4") + ".png"
        assets.append({"scene_id": scene_id, "target_filename": target})
    return {
        "creator_supplied_via": "creator-supplied via ChatGPT Desktop ImageGen",
        "generated_outside_application": True,
        "model_version": "not verified by application",
        "application_provider_api_call": False,
        "external_charge_micros": 0,
        "selected_assets": tuple(assets),
    }


def _subtitle_version(reference: ArtifactReference, version: ArtifactVersion, video_payload: MappingProxyType) -> tuple[dict[str, object], ...]:
    _version(version, reference, "INVALID_SUBTITLE_VERSION")
    payload = _mapping(version.payload, {"production_request_reference", "timeline_reference", "cues"}, "INVALID_SUBTITLE")
    request = _reference(payload["production_request_reference"], "production_request", "INVALID_SUBTITLE")
    timeline = _reference(payload["timeline_reference"], "timeline", "INVALID_SUBTITLE")
    if not _same_ref(request, video_payload["production_request_reference"]) or not _same_ref(timeline, video_payload["timeline_reference"]):
        raise _Invalid("SUBTITLE_LINEAGE_MISMATCH")
    if not _refs_equal(version.dependencies, (request, timeline)):
        raise _Invalid("SUBTITLE_LINEAGE_MISMATCH")
    cues = payload["cues"]
    if type(cues) is not tuple or not cues:
        raise _Invalid("INVALID_SUBTITLE")
    ids = video_payload["scene_ids"]
    if type(ids) is not tuple or tuple() == ids or len(cues) != len(ids):
        raise _Invalid("SUBTITLE_LINEAGE_MISMATCH")
    facts: list[dict[str, object]] = []
    prior_end = 0
    text_bytes = 0
    for cue, expected_id in zip(cues, ids):
        cue = _mapping(cue, {"scene_id", "start_milliseconds", "end_milliseconds", "text"}, "INVALID_SUBTITLE")
        scene_id = cue["scene_id"]
        _text(scene_id, code="INVALID_SUBTITLE", limit=_MAX_COMPONENT, token=True)
        start, end = cue["start_milliseconds"], cue["end_milliseconds"]
        if scene_id != expected_id or type(start) is not int or isinstance(start, bool) or type(end) is not int or isinstance(end, bool) or start != prior_end or end <= start or end > _MAX_DURATION_MS:
            raise _Invalid("INVALID_SUBTITLE")
        text = cue["text"]
        if type(text) is not str or not text or "\r" in text or any((ord(char) < 0x20 and char not in "\n\t") or ord(char) == 0x7F for char in text):
            raise _Invalid("INVALID_SUBTITLE")
        try:
            text_bytes += len(text.encode("utf-8"))
        except UnicodeError:
            raise _Invalid("INVALID_SUBTITLE") from None
        if text_bytes > _MAX_JSON_BYTES:
            raise _Invalid("PACKAGE_OUTPUT_TOO_LARGE")
        facts.append({"scene_id": scene_id, "start_milliseconds": start, "end_milliseconds": end, "text": text})
        prior_end = end
    if prior_end != video_payload["duration_milliseconds"]:
        raise _Invalid("SUBTITLE_LINEAGE_MISMATCH")
    return tuple(facts)


def _video_version(reference: ArtifactReference, version: ArtifactVersion, task_id: str, subtitle_reference: ArtifactReference) -> tuple[MappingProxyType, WorkspaceFileReference]:
    _version(version, reference, "INVALID_VIDEO_VERSION")
    payload = _mapping(
        version.payload,
        {"production_request_reference", "timeline_reference", "composition_id", "scene_ids", "scene_clip_references", "subtitle_reference", "master_audio_reference", "composer", "output_reference", "media_type", "duration_milliseconds"},
        "INVALID_VIDEO",
    )
    _reference(payload["production_request_reference"], "production_request", "INVALID_VIDEO")
    _reference(payload["timeline_reference"], "timeline", "INVALID_VIDEO")
    if not _same_ref(payload["subtitle_reference"], subtitle_reference):
        raise _Invalid("VIDEO_LINEAGE_MISMATCH")
    _reference(payload["subtitle_reference"], "subtitle", "INVALID_VIDEO")
    _reference(payload["master_audio_reference"], "master_audio", "INVALID_VIDEO")
    _text(payload["composition_id"], code="INVALID_VIDEO", token=True)
    _text(payload["composer"], code="INVALID_VIDEO", token=True)
    ids, clips = payload["scene_ids"], payload["scene_clip_references"]
    if type(ids) is not tuple or not ids or type(clips) is not tuple or len(ids) != len(clips):
        raise _Invalid("INVALID_VIDEO")
    seen: set[tuple[str, str, int]] = set()
    for scene_id, clip in zip(ids, clips):
        _text(scene_id, code="INVALID_VIDEO", limit=_MAX_COMPONENT, token=True)
        clip = _reference(clip, "scene_clip", "INVALID_VIDEO")
        if clip.identity != f"{reference.identity}:{scene_id}" or (clip.artifact_type, clip.identity, clip.version) in seen:
            raise _Invalid("VIDEO_LINEAGE_MISMATCH")
        seen.add((clip.artifact_type, clip.identity, clip.version))
    output = _mapping(payload["output_reference"], {"task_id", "area", "name"}, "INVALID_VIDEO_OUTPUT")
    output_ref = WorkspaceFileReference(output["task_id"], output["area"], output["name"])
    _safe_workspace(output_ref, task_id, "media", "INVALID_VIDEO_OUTPUT")
    if type(payload["media_type"]) is not str or payload["media_type"] != "video/mp4":
        raise _Invalid("INVALID_VIDEO")
    duration = payload["duration_milliseconds"]
    if type(duration) is not int or isinstance(duration, bool) or not 0 < duration <= _MAX_DURATION_MS:
        raise _Invalid("INVALID_VIDEO")
    expected_dependencies = (payload["production_request_reference"], payload["timeline_reference"], *clips, subtitle_reference, payload["master_audio_reference"])
    if not _refs_equal(version.dependencies, expected_dependencies):
        raise _Invalid("VIDEO_LINEAGE_MISMATCH")
    return payload, output_ref


def _reachable(repository: object, start: ArtifactVersion, source: ArtifactReference) -> bool:
    pending = list(start.dependencies)
    seen: set[tuple[str, str, int]] = set()
    count = 0
    while pending and count < _MAX_GRAPH_NODES:
        reference = pending.pop(0)
        if type(reference) is not ArtifactReference:
            return False
        if not _same_ref(reference, reference):
            return False
        key = (reference.artifact_type, reference.identity, reference.version)
        if _same_ref(reference, source):
            return True
        if key in seen:
            continue
        seen.add(key)
        try:
            version = repository.get(reference)
        except Exception:
            return False
        if type(version) is not ArtifactVersion or not _same_ref(version.reference, reference) or type(version.dependencies) is not tuple:
            return False
        if any(type(item) is not ArtifactReference for item in version.dependencies):
            return False
        pending.extend(version.dependencies)
        count += 1
    return False


def _valid_mp4(content: bytes) -> bool:
    if type(content) is not bytes or not content or len(content) > _MAX_VIDEO_BYTES:
        return False
    offset = 0
    ftyp = False
    moov = mdat = False
    try:
        while offset + 8 <= len(content):
            size = int.from_bytes(content[offset : offset + 4], "big")
            kind = content[offset + 4 : offset + 8]
            if size == 0:
                size = len(content) - offset
            elif size == 1:
                if offset + 16 > len(content):
                    return False
                size = int.from_bytes(content[offset + 8 : offset + 16], "big")
            if size < 8 or offset + size > len(content):
                return False
            ftyp = ftyp or kind == b"ftyp"
            moov = moov or kind == b"moov"
            mdat = mdat or kind == b"mdat"
            offset += size
        return ftyp and moov and mdat and offset == len(content)
    except Exception:
        return False


def _srt_time(milliseconds: int) -> str:
    seconds, millis = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{millis:03d}"


def _render_srt(cues: tuple[dict[str, object], ...]) -> bytes:
    chunks: list[str] = []
    for index, cue in enumerate(cues, start=1):
        chunks.append(f"{index}\n{_srt_time(cue['start_milliseconds'])} --> {_srt_time(cue['end_milliseconds'])}\n{cue['text']}\n")
    result = "\n".join(chunks).encode("utf-8")
    if len(result) > _MAX_JSON_BYTES:
        raise _Invalid("PACKAGE_OUTPUT_TOO_LARGE")
    return result


def _zip(entries: tuple[tuple[str, str, bytes], ...]) -> bytes:
    output = io.BytesIO()
    try:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_STORED, allowZip64=False) as archive:
            for name, _media_type, content in entries:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_STORED
                info.create_system = 0
                info.create_version = 20
                info.extract_version = 20
                info.flag_bits = 0
                info.external_attr = 0o600 << 16
                info.internal_attr = 0
                info.extra = b""
                info.comment = b""
                archive.writestr(info, content)
    except (OSError, ValueError, zipfile.BadZipFile):
        raise _Invalid("PACKAGE_BUILD_FAILED") from None
    result = output.getvalue()
    if not result or len(result) > _MAX_VIDEO_BYTES + _MAX_JSON_BYTES:
        raise _Invalid("PACKAGE_OUTPUT_TOO_LARGE")
    return result


def _commit_error(prefix: str, error: Exception) -> PackagingFailure:
    code = getattr(error, "code", "")
    if code == "COMMIT_CONFLICT":
        return _failure("validation", f"{prefix}_COMMIT_CONFLICT", "Artifact commit identity conflicts with prior input")
    return _failure("execution", f"{prefix}_COMMIT_FAILED", "Artifact persistence failed")


def _same_text(first: object, second: object) -> bool:
    return type(first) is str and type(second) is str and first == second


def _same_value(first: object, second: object) -> bool:
    if type(first) is not type(second):
        return False
    if type(first) is ArtifactReference:
        return _same_ref(first, second)
    if type(first) is MappingProxyType:
        if len(first) != len(second):
            return False
        for key, value in first.items():
            if type(key) is not str:
                return False
            matching = next((other for other in second if type(other) is str and other == key), None)
            if matching is None or not _same_value(value, second[matching]):
                return False
        return True
    if type(first) is tuple:
        return len(first) == len(second) and all(_same_value(left, right) for left, right in zip(first, second))
    return first == second


def _same_workspace(first: object, second: WorkspaceFileReference, size: object, expected_size: int) -> bool:
    return (
        type(first) is WorkspaceFileRecord
        and type(first.reference) is WorkspaceFileReference
        and type(first.reference.task_id) is str
        and type(first.reference.area) is str
        and type(first.reference.name) is str
        and _same_text(first.reference.task_id, second.task_id)
        and _same_text(first.reference.area, second.area)
        and _same_text(first.reference.name, second.name)
        and type(size) is int
        and not isinstance(size, bool)
        and size == expected_size
    )


def _expected_version(candidate: ArtifactCandidate, reference: ArtifactReference) -> ArtifactVersion:
    return ArtifactVersion(
        reference,
        freeze_value(candidate.payload),
        tuple(freeze_value(item) for item in candidate.provenance or ()),
        tuple(candidate.dependencies or ()),
        candidate.commit_id,
        candidate.prior_reference,
    )


def _decision_valid(record: object) -> bool:
    if type(record) is not FinalVideoDecisionRecord:
        return False
    try:
        for value in (record.decision_id, record.task_id, record.thread_id, record.creator_id):
            _text(value, code="INVALID_DECISION")
        _reference(record.video_reference, "video", "INVALID_DECISION")
        if type(record.gate_kind) is not str or record.gate_kind != "final_video_review" or type(record.assessment_disposition) is not str or record.assessment_disposition not in {"pass", "hard_block"}:
            return False
        codes = record.finding_codes
        if type(codes) is not tuple or len(codes) > 9 or any(type(code) is not str for code in codes): return False
        for code in codes: _text(code, code="INVALID_DECISION", limit=_MAX_COMPONENT)
        if len(set(codes)) != len(codes) or bool(codes) != (record.assessment_disposition == "hard_block"): return False
        if type(record.action) is not str or record.action not in {"approve", "reject", "revise"} or record.assessment_disposition == "hard_block" and record.action == "approve": return False
        return type(record.decision_context) is str and len(record.decision_context) <= 4096 and not any(ord(char) < 0x20 or ord(char) == 0x7F for char in record.decision_context)
    except Exception: return False


def _decision_matches(record: FinalVideoDecisionRecord, decision_id: str, task_id: str | None = None, video_reference: ArtifactReference | None = None) -> bool:
    if not _decision_valid(record):
        return False
    if not _same_text(record.decision_id, decision_id):
        return False
    return task_id is None or (_same_text(record.task_id, task_id) and _same_text(record.gate_kind, "final_video_review") and _same_ref(record.video_reference, video_reference) and _same_text(record.assessment_disposition, "pass") and not record.finding_codes and _same_text(record.action, "approve"))


class PublishPackageBuilder:
    """Build one exact approved-video package through injected local seams."""

    def __init__(self, artifact_repository: object, decision_repository: object, workspace: object) -> None:
        self._artifacts = artifact_repository
        self._decisions = decision_repository
        self._workspace = workspace

    def build(
        self,
        task_id: str,
        source_record_reference: ArtifactReference,
        subtitle_reference: ArtifactReference,
        video_reference: ArtifactReference,
        final_video_decision_id: str,
        *,
        artifact_identity: str,
        manifest_commit_id: str,
        package_commit_id: str,
        output_reference: WorkspaceFileReference,
        tts_attribution: Mapping[str, object] | None = None,
    ) -> PublishPackageResult | PackagingFailure:
        try:
            _text(task_id, code="INVALID_TASK_ID", token=True)
            source_record_reference = _reference(source_record_reference, "source_record", "INVALID_SOURCE_REFERENCE")
            subtitle_reference = _reference(subtitle_reference, "subtitle", "INVALID_SUBTITLE_REFERENCE")
            video_reference = _reference(video_reference, "video", "INVALID_VIDEO_REFERENCE")
            _text(final_video_decision_id, code="INVALID_DECISION_ID")
            _text(artifact_identity, code="INVALID_ARTIFACT_IDENTITY", token=True)
            _text(manifest_commit_id, code="INVALID_MANIFEST_COMMIT_ID")
            _text(package_commit_id, code="INVALID_PACKAGE_COMMIT_ID")
            output_reference = _safe_workspace(output_reference, task_id, "exports", "INVALID_OUTPUT_REFERENCE", ".zip")
            validated_tts_attribution = _tts_attribution(tts_attribution)

            source = self._get(source_record_reference, "SOURCE_NOT_FOUND")
            subtitle = self._get(subtitle_reference, "SUBTITLE_NOT_FOUND")
            video = self._get(video_reference, "VIDEO_NOT_FOUND")
            decision = self._decision(final_video_decision_id)
            if not _decision_matches(decision, final_video_decision_id, task_id, video_reference):
                raise _Invalid("FINAL_VIDEO_APPROVAL_REQUIRED")
            video_payload, video_output = _video_version(video_reference, video, task_id, subtitle_reference)
            source_attribution = _source_version(source_record_reference, source)
            imported_visuals = _visual_import_attribution(self._artifacts, video_payload)
            if imported_visuals is not None:
                source_attribution = {**source_attribution, "visual_assets": imported_visuals}
            if validated_tts_attribution is not None:
                source_attribution = {**source_attribution, "tts": validated_tts_attribution}
            cues = _subtitle_version(subtitle_reference, subtitle, video_payload)
            if not _reachable(self._artifacts, video, source_record_reference):
                raise _Invalid("SOURCE_LINEAGE_MISMATCH")

            raw_video = self._workspace.read(video_output)
            if type(raw_video) is not bytes or not _valid_mp4(raw_video):
                raise _Invalid("INVALID_VIDEO_OUTPUT")
            srt = _render_srt(cues)
            attribution = _canonical_json(source_attribution)
            facts = (
                {"name": "video.mp4", "media_type": "video/mp4", "size_bytes": len(raw_video), "sha256": _sha(raw_video)},
                {"name": "subtitles.srt", "media_type": "application/x-subrip", "size_bytes": len(srt), "sha256": _sha(srt)},
                {"name": "source-attribution.json", "media_type": "application/json", "size_bytes": len(attribution), "sha256": _sha(attribution)},
            )
            manifest_document = {
                "schema_version": 1,
                "task_id": task_id,
                "source_record_reference": _ref_json(source_record_reference),
                "subtitle_reference": _ref_json(subtitle_reference),
                "video_reference": _ref_json(video_reference),
                "final_video_decision_id": final_video_decision_id,
                "files": facts,
            }
            manifest_bytes = _canonical_json(manifest_document)
            package_bytes = _zip((
                ("video.mp4", "video/mp4", raw_video),
                ("subtitles.srt", "application/x-subrip", srt),
                ("source-attribution.json", "application/json", attribution),
                ("artifact-manifest.json", "application/json", manifest_bytes),
            ))
            stored = self._workspace.commit(output_reference, package_bytes)
            if type(stored) is WorkspaceFailure:
                if stored.code == "WORKSPACE_FILE_CONFLICT":
                    return _failure("validation", "PACKAGE_OUTPUT_CONFLICT", "package output reference conflicts with existing bytes")
                return _failure("execution", "WORKSPACE_COMMIT_FAILED", "package output could not be stored")
            if not _same_workspace(stored, output_reference, getattr(stored, "size_bytes", None), len(package_bytes)):
                return _failure("execution", "WORKSPACE_COMMIT_FAILED", "package output could not be stored")

            manifest_payload = {
                **manifest_document,
                "source_record_reference": source_record_reference,
                "subtitle_reference": subtitle_reference,
                "video_reference": video_reference,
                "files": tuple(facts),
            }
            manifest_candidate = ArtifactCandidate(
                "artifact_manifest", artifact_identity, manifest_payload,
                ({"purpose": "publish_package_manifest", "task_id": task_id, "final_video_decision_id": final_video_decision_id},),
                (source_record_reference, subtitle_reference, video_reference), True, manifest_commit_id,
            )
            manifest_reference = self._commit(manifest_candidate, "artifact_manifest", artifact_identity, "MANIFEST")
            if type(manifest_reference) is PackagingFailure:
                return manifest_reference

            package_payload = {
                "manifest_reference": manifest_reference,
                "source_record_reference": source_record_reference,
                "subtitle_reference": subtitle_reference,
                "video_reference": video_reference,
                "final_video_decision_id": final_video_decision_id,
                "output_reference": {"task_id": task_id, "area": "exports", "name": output_reference.name},
                "format": "zip",
            }
            package_candidate = ArtifactCandidate(
                "publish_package", artifact_identity, package_payload,
                ({"purpose": "publish_package", "task_id": task_id, "manifest_reference": manifest_reference, "final_video_decision_id": final_video_decision_id},),
                (manifest_reference, source_record_reference, subtitle_reference, video_reference), True, package_commit_id,
            )
            package_reference = self._commit(package_candidate, "publish_package", artifact_identity, "PACKAGE")
            if type(package_reference) is PackagingFailure:
                return package_reference
            return PublishPackageResult(task_id, source_record_reference, subtitle_reference, video_reference, final_video_decision_id, manifest_reference, package_reference, output_reference, "SUCCESS")
        except _Invalid as error:
            return _failure("validation", error.code, error.message)
        except Exception:
            return _failure("execution", "PACKAGING_FAILED", "publish package build failed")

    def _commit(self, candidate: ArtifactCandidate, artifact_type: str, identity: str, prefix: str) -> ArtifactReference | PackagingFailure:
        try:
            reference = self._artifacts.commit(candidate)
            _reference(reference, artifact_type, f"{prefix}_COMMIT_FAILED")
            if reference.version != 1 or not _same_text(reference.identity, identity):
                raise _Invalid(f"{prefix}_COMMIT_FAILED")
            stored = self._artifacts.get(reference)
            expected = _expected_version(candidate, reference)
            actual = _version(stored, reference, f"{prefix}_COMMIT_FAILED")
            if not (_same_value(actual.payload, expected.payload) and _same_value(actual.provenance, expected.provenance) and _same_value(actual.dependencies, expected.dependencies) and _same_text(actual.commit_id, expected.commit_id) and _same_value(actual.prior_reference, expected.prior_reference)):
                raise _Invalid(f"{prefix}_COMMIT_FAILED")
            return reference
        except _Invalid as error:
            return _failure("execution", error.code, "Artifact persistence failed")
        except Exception as error:
            return _commit_error(prefix, error)

    def _get(self, reference: ArtifactReference, not_found_code: str) -> ArtifactVersion:
        try:
            result = self._artifacts.get(reference)
        except Exception:
            raise _Invalid(not_found_code) from None
        return _version(result, reference, not_found_code)

    def _decision(self, decision_id: str) -> FinalVideoDecisionRecord:
        try:
            result = self._decisions.get(decision_id)
        except Exception:
            raise _Invalid("DECISION_NOT_FOUND") from None
        if not _decision_matches(result, decision_id):
            raise _Invalid("DECISION_NOT_FOUND")
        return result


__all__ = ["PackagingFailure", "PublishPackageResult", "PublishPackageBuilder"]
