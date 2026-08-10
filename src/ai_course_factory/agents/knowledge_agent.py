"""Grounded Knowledge Agent boundary for the first vertical slice."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping

from ai_course_factory.artifacts import ArtifactCandidate, ArtifactReference, ArtifactVersion

from .runtime import ModelRuntimeFailure, ModelRuntimePort, ModelRuntimeRequest, ModelRuntimeResult


_PURPOSE = "knowledge_generation"
_MAX_CLAIMS = 128
_MAX_CLAIM_ID_LENGTH = 128
_MAX_STATEMENT_LENGTH = 4096
_MAX_EVIDENCE_PER_CLAIM = 16
_MAX_LOCATOR_LENGTH = 2048
_MAX_GAPS = 64
_MAX_DIAGNOSTICS = 64
_MAX_TEXT_LENGTH = 4096


@dataclass(frozen=True, slots=True)
class KnowledgeTaskContext:
    """Committed task constraints required by Knowledge Agent invocation."""

    course: str
    lesson_scope: str
    language: str
    audience: str

    def as_mapping(self) -> Mapping[str, str]:
        return MappingProxyType(
            {
                "course": self.course,
                "lesson_scope": self.lesson_scope,
                "language": self.language,
                "audience": self.audience,
            }
        )


@dataclass(frozen=True, slots=True)
class KnowledgeAgentFailure:
    """Safe validation or execution failure returned by Knowledge Agent."""

    kind: str
    code: str
    message: str


class _KnowledgeValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class KnowledgeAgent:
    """Generate a grounded Knowledge Artifact Candidate without committing it."""

    def __init__(self, runtime: ModelRuntimePort) -> None:
        self._runtime = runtime

    def invoke(
        self,
        source_record_reference: ArtifactReference,
        resolved_source_record: ArtifactVersion,
        *,
        context: KnowledgeTaskContext | Mapping[str, str],
        identity: str,
        commit_id: str,
        knowledge_boundary: str,
    ) -> ArtifactCandidate | KnowledgeAgentFailure:
        """Return a validated Candidate or a normalized safe failure."""

        try:
            normalized_context = self._validate_inputs(
                source_record_reference,
                resolved_source_record,
                context,
                identity,
                commit_id,
                knowledge_boundary,
            )
            runtime_invoke = getattr(self._runtime, "invoke", None)
            if not callable(runtime_invoke):
                raise _KnowledgeValidation("INVALID_RUNTIME", "model runtime is required")

            request = ModelRuntimeRequest(
                purpose=_PURPOSE,
                source_record_reference=source_record_reference,
                source_record_payload=resolved_source_record.payload,
                task_context=normalized_context,
                knowledge_boundary=knowledge_boundary,
            )
            result = runtime_invoke(request)
            if isinstance(result, ModelRuntimeFailure):
                return KnowledgeAgentFailure(
                    "execution", "MODEL_RUNTIME_FAILED", "model runtime execution failed"
                )
            if not isinstance(result, ModelRuntimeResult):
                raise _KnowledgeValidation("INVALID_MODEL_RESULT", "model runtime result is invalid")
            return self._candidate(
                source_record_reference,
                resolved_source_record,
                normalized_context,
                knowledge_boundary,
                identity,
                commit_id,
                result,
            )
        except _KnowledgeValidation as exc:
            return KnowledgeAgentFailure("validation", exc.code, exc.message)
        except Exception:
            return KnowledgeAgentFailure(
                "execution", "KNOWLEDGE_AGENT_FAILED", "knowledge agent execution failed"
            )

    @classmethod
    def _validate_inputs(
        cls,
        source_record_reference: ArtifactReference,
        resolved_source_record: ArtifactVersion,
        context: KnowledgeTaskContext | Mapping[str, str],
        identity: str,
        commit_id: str,
        knowledge_boundary: str,
    ) -> Mapping[str, str]:
        if not cls._valid_reference(source_record_reference, artifact_type="source_record"):
            raise _KnowledgeValidation(
                "INVALID_SOURCE_REFERENCE", "an exact source_record Reference is required"
            )
        if not isinstance(resolved_source_record, ArtifactVersion):
            raise _KnowledgeValidation(
                "INVALID_SOURCE_PAYLOAD", "a resolved Source Record Version is required"
            )
        if resolved_source_record.reference != source_record_reference:
            raise _KnowledgeValidation(
                "SOURCE_REFERENCE_MISMATCH", "source Reference does not match resolved payload"
            )
        payload = resolved_source_record.payload
        if not isinstance(payload, Mapping):
            raise _KnowledgeValidation("INVALID_SOURCE_PAYLOAD", "resolved source payload is invalid")
        cls._validate_source_units(payload)

        normalized_context = cls._normalize_context(context)
        cls._validate_identity(identity, "INVALID_ARTIFACT_IDENTITY", "Knowledge identity is required")
        cls._validate_identity(commit_id, "INVALID_COMMIT_ID", "logical Commit identity is required")
        if (
            not isinstance(knowledge_boundary, str)
            or not knowledge_boundary.strip()
            or len(knowledge_boundary) > _MAX_TEXT_LENGTH
        ):
            raise _KnowledgeValidation(
                "INVALID_KNOWLEDGE_BOUNDARY", "knowledge boundary is required"
            )
        return normalized_context

    @classmethod
    def _candidate(
        cls,
        source_record_reference: ArtifactReference,
        resolved_source_record: ArtifactVersion,
        context: Mapping[str, str],
        knowledge_boundary: str,
        identity: str,
        commit_id: str,
        result: ModelRuntimeResult,
    ) -> ArtifactCandidate:
        source_payload = resolved_source_record.payload
        known_locators = cls._source_locators(source_payload)
        claims = cls._validate_claims(result.claims, known_locators)
        repository_summary = cls._bounded_text(result.repository_summary, "INVALID_REPOSITORY_SUMMARY")
        lesson_focus = cls._bounded_text(result.lesson_focus, "INVALID_LESSON_FOCUS")
        gaps = cls._validate_text_sequence(result.gaps, _MAX_GAPS, "INVALID_GAPS")
        diagnostics = cls._validate_text_sequence(
            result.diagnostics, _MAX_DIAGNOSTICS, "INVALID_DIAGNOSTICS"
        )
        evidence_locators = tuple(
            locator
            for claim in claims
            for locator in claim["evidence_locators"]
        )
        unique_evidence = tuple(dict.fromkeys(evidence_locators))
        provenance = (
            {
                "purpose": _PURPOSE,
                "source_record_reference": source_record_reference,
            },
            *({"locator": locator} for locator in unique_evidence),
        )
        return ArtifactCandidate(
            artifact_type="knowledge",
            identity=identity,
            payload={
                "source_record_reference": source_record_reference,
                "repository_url": source_payload.get("repository_url"),
                "repository_identity": source_payload.get("repository_identity"),
                "commit_sha": source_payload.get("commit_sha"),
                "course": context["course"],
                "lesson_scope": context["lesson_scope"],
                "language": context["language"],
                "audience": context["audience"],
                "knowledge_boundary": knowledge_boundary,
                "repository_summary": repository_summary,
                "lesson_focus": lesson_focus,
                "claims": claims,
                "gaps": gaps,
                "diagnostics": diagnostics,
            },
            provenance=provenance,
            dependencies=(source_record_reference,),
            validated=True,
            commit_id=commit_id,
        )

    @classmethod
    def _validate_claims(
        cls,
        claims: object,
        known_locators: frozenset[str],
    ) -> tuple[dict[str, Any], ...]:
        if not isinstance(claims, tuple) or not claims or len(claims) > _MAX_CLAIMS:
            raise _KnowledgeValidation("INVALID_CLAIMS", "knowledge claims are invalid")
        seen_ids: set[str] = set()
        normalized: list[dict[str, Any]] = []
        for claim in claims:
            if not isinstance(claim, Mapping):
                raise _KnowledgeValidation("INVALID_CLAIM", "knowledge claim is invalid")
            if set(claim) != {"claim_id", "statement", "confidence", "evidence_locators"}:
                raise _KnowledgeValidation("INVALID_CLAIM", "knowledge claim is invalid")
            claim_id = claim.get("claim_id")
            statement = claim.get("statement")
            confidence = claim.get("confidence")
            evidence = claim.get("evidence_locators")
            if (
                not isinstance(claim_id, str)
                or not claim_id.strip()
                or len(claim_id) > _MAX_CLAIM_ID_LENGTH
                or claim_id in seen_ids
            ):
                raise _KnowledgeValidation("INVALID_CLAIM_ID", "knowledge claim identity is invalid")
            if not isinstance(statement, str) or not statement.strip() or len(statement) > _MAX_STATEMENT_LENGTH:
                raise _KnowledgeValidation("INVALID_CLAIM_STATEMENT", "knowledge claim statement is invalid")
            if (
                not isinstance(confidence, (int, float))
                or isinstance(confidence, bool)
                or not math.isfinite(confidence)
                or confidence < 0
                or confidence > 1
            ):
                raise _KnowledgeValidation("INVALID_CLAIM_CONFIDENCE", "knowledge claim confidence is invalid")
            if not isinstance(evidence, tuple) or not evidence or len(evidence) > _MAX_EVIDENCE_PER_CLAIM:
                raise _KnowledgeValidation("INVALID_CLAIM_EVIDENCE", "knowledge claim evidence is invalid")
            if any(
                not isinstance(locator, str)
                or not locator
                or len(locator) > _MAX_LOCATOR_LENGTH
                or locator not in known_locators
                for locator in evidence
            ):
                raise _KnowledgeValidation(
                    "UNTRACEABLE_CLAIM", "knowledge claim evidence is not in the Source Record"
                )
            seen_ids.add(claim_id)
            normalized.append(
                {
                    "claim_id": claim_id,
                    "statement": statement,
                    "confidence": confidence,
                    "evidence_locators": evidence,
                }
            )
        return tuple(normalized)

    @staticmethod
    def _validate_source_units(payload: Mapping[str, Any]) -> None:
        units = payload.get("units")
        if not isinstance(units, tuple) or not units:
            raise _KnowledgeValidation("INVALID_SOURCE_PAYLOAD", "resolved source units are invalid")
        for unit in units:
            if not isinstance(unit, Mapping):
                raise _KnowledgeValidation("INVALID_SOURCE_PAYLOAD", "resolved source units are invalid")
            locator = unit.get("locator")
            if not isinstance(locator, str) or not locator or len(locator) > _MAX_LOCATOR_LENGTH:
                raise _KnowledgeValidation("INVALID_SOURCE_PAYLOAD", "resolved source locator is invalid")
            if not isinstance(unit.get("text"), str):
                raise _KnowledgeValidation("INVALID_SOURCE_PAYLOAD", "resolved source text is invalid")

    @staticmethod
    def _source_locators(payload: Mapping[str, Any]) -> frozenset[str]:
        return frozenset(unit["locator"] for unit in payload["units"])

    @classmethod
    def _normalize_context(
        cls, context: KnowledgeTaskContext | Mapping[str, str]
    ) -> Mapping[str, str]:
        if isinstance(context, KnowledgeTaskContext):
            values = context.as_mapping()
        elif isinstance(context, Mapping):
            if set(context) != {"course", "lesson_scope", "language", "audience"}:
                raise _KnowledgeValidation("INVALID_TASK_CONTEXT", "explicit task context is required")
            values = MappingProxyType(dict(context))
        else:
            raise _KnowledgeValidation("INVALID_TASK_CONTEXT", "explicit task context is required")
        for value in values.values():
            if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TEXT_LENGTH:
                raise _KnowledgeValidation("INVALID_TASK_CONTEXT", "explicit task context is required")
        return values

    @staticmethod
    def _valid_reference(reference: object, *, artifact_type: str) -> bool:
        return (
            isinstance(reference, ArtifactReference)
            and reference.artifact_type == artifact_type
            and isinstance(reference.identity, str)
            and bool(reference.identity.strip())
            and reference.identity.casefold() != "latest"
            and isinstance(reference.version, int)
            and not isinstance(reference.version, bool)
            and reference.version > 0
        )

    @staticmethod
    def _validate_identity(value: object, code: str, message: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.casefold() == "latest"
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        ):
            raise _KnowledgeValidation(code, message)

    @staticmethod
    def _bounded_text(value: object, code: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TEXT_LENGTH:
            raise _KnowledgeValidation(code, "model result text is invalid")
        return value

    @staticmethod
    def _validate_text_sequence(value: object, limit: int, code: str) -> tuple[str, ...]:
        if not isinstance(value, tuple) or len(value) > limit or any(
            not isinstance(item, str) or not item.strip() or len(item) > _MAX_TEXT_LENGTH for item in value
        ):
            raise _KnowledgeValidation(code, "model result text sequence is invalid")
        return value
