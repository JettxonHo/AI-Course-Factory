"""Staged, provider-neutral Production Agent boundaries.

The first Production planning step deliberately stops at a Character
``ArtifactCandidate``.  The Agent validates the exact approved Script input and
normalises the model-runtime result, while the existing Artifact boundary owns
validation and Commit of the candidate.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactReference,
    ArtifactVersion,
    ScriptDecisionRecord,
)

from .runtime import (
    ModelRuntimeFailure,
    ModelRuntimePort,
    ModelRuntimeRequest,
    ProductionModelRuntimeResult,
)


_PURPOSE = "character_planning"
_MAX_IDENTITY_LENGTH = 256
_MAX_TEXT_LENGTH = 4096
_MAX_CHARACTER_TRAITS = 32

_CHARACTER_FIELDS = {
    "name",
    "design_version",
    "summary",
    "visual_traits",
    "personality_traits",
    "continuity_rules",
}


@dataclass(frozen=True, slots=True)
class CharacterPlanningConstraints:
    """The fixed two-field Character planning constraint contract."""

    name: str
    design_version: str


@dataclass(frozen=True, slots=True)
class ProductionAgentFailure:
    """Safe validation or execution failure returned by Production Agent."""

    kind: str
    code: str
    message: str


class _ProductionValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _ProductionExecution(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ProductionAgent:
    """Generate provider-neutral production-planning Candidates.

    This boundary never commits an Artifact, advances Workflow state, or
    invokes a media/Provider adapter.  It only invokes the supplied
    provider-neutral model runtime after all exact input and approval checks
    have passed.
    """

    def __init__(self, runtime: ModelRuntimePort) -> None:
        self._runtime = runtime

    def plan_character(
        self,
        script_reference: ArtifactReference,
        resolved_script: ArtifactVersion,
        script_decision: ScriptDecisionRecord,
        *,
        constraints: CharacterPlanningConstraints | Mapping[str, str],
        character_identity: str,
        character_commit_id: str,
    ) -> ArtifactCandidate | ProductionAgentFailure:
        """Return a validated Character Candidate or a normalised failure.
        """

        try:
            normalized_constraints = self._normalize_constraints(constraints)
            self._validate_identity(
                character_identity,
                "INVALID_CHARACTER_IDENTITY",
                "Character identity is required",
            )
            self._validate_identity(
                character_commit_id,
                "INVALID_CHARACTER_COMMIT_ID",
                "logical Commit identity is required",
            )
            upstream = self._validate_script(
                script_reference, resolved_script
            )
            self._validate_approval(script_decision, script_reference, upstream)
            result = self._invoke_runtime(
                ModelRuntimeRequest(
                    purpose=_PURPOSE,
                    inputs=MappingProxyType(
                        {
                            "script_reference": script_reference,
                            "script_payload": resolved_script.payload,
                            "approval_decision_id": script_decision.decision_id,
                        }
                    ),
                    constraints=MappingProxyType(
                        {"character_constraints": normalized_constraints}
                    ),
                )
            )
            character = self._validate_character_result(
                result.character,
                normalized_constraints,
            )
            return ArtifactCandidate(
                artifact_type="character",
                identity=character_identity,
                payload={
                    "script_reference": script_reference,
                    "approval_decision_id": script_decision.decision_id,
                    "character_constraints": normalized_constraints,
                    "character": character,
                },
                provenance=(
                    {
                        "purpose": _PURPOSE,
                        "script_reference": script_reference,
                        "approval_decision_id": script_decision.decision_id,
                    },
                ),
                dependencies=(script_reference,),
                validated=True,
                commit_id=character_commit_id,
            )
        except _ProductionValidation as exc:
            return ProductionAgentFailure("validation", exc.code, exc.message)
        except _ProductionExecution as exc:
            return ProductionAgentFailure("execution", exc.code, exc.message)
        except Exception:
            # Never expose runtime/provider exception text through the Agent
            # boundary, even if an unexpected implementation error occurs.
            return ProductionAgentFailure(
                "execution",
                "PRODUCTION_AGENT_FAILED",
                "production agent execution failed",
            )

    @classmethod
    def _normalize_constraints(
        cls, value: CharacterPlanningConstraints | Mapping[str, str]
    ) -> Mapping[str, Any]:
        if isinstance(value, CharacterPlanningConstraints):
            raw = {"name": value.name, "design_version": value.design_version}
        elif isinstance(value, Mapping) and set(value) == {"name", "design_version"}:
            raw = value
        else:
            raise _ProductionValidation(
                "INVALID_CHARACTER_CONSTRAINTS",
                "character constraints must contain name and design version",
            )
        normalized_name = cls._bounded_text(
            raw["name"], "INVALID_CHARACTER_CONSTRAINTS", "character name is invalid"
        )
        normalized_version = cls._bounded_text(
            raw["design_version"],
            "INVALID_CHARACTER_CONSTRAINTS",
            "character design version is invalid",
        )
        return MappingProxyType(
            {"name": normalized_name, "design_version": normalized_version}
        )

    @classmethod
    def _validate_script(
        cls,
        reference: ArtifactReference,
        version: ArtifactVersion,
    ) -> tuple[ArtifactReference, ArtifactReference, ArtifactReference]:
        if not cls._valid_reference(reference, "script"):
            raise _ProductionValidation(
                "INVALID_SCRIPT_REFERENCE", "an exact script Reference is required"
            )
        if not isinstance(version, ArtifactVersion):
            raise _ProductionValidation(
                "INVALID_SCRIPT_VERSION", "a resolved Script Version is required"
            )
        if version.reference != reference:
            raise _ProductionValidation(
                "SCRIPT_REFERENCE_MISMATCH", "Script Reference does not match Version"
            )
        payload = version.payload
        if not isinstance(payload, Mapping):
            raise _ProductionValidation(
                "INVALID_SCRIPT_PAYLOAD", "resolved Script payload is invalid"
            )
        expected_keys = (
            ("knowledge_reference", "knowledge"),
            ("course_plan_reference", "content_plan"),
            ("episode_plan_reference", "content_plan"),
        )
        upstream: list[ArtifactReference] = []
        for key, artifact_type in expected_keys:
            upstream_reference = payload.get(key)
            if not cls._valid_reference(upstream_reference, artifact_type):
                raise _ProductionValidation(
                    "SCRIPT_LINEAGE_MISMATCH", "Script lineage is invalid"
                )
            upstream.append(upstream_reference)
        expected_dependencies = tuple(upstream)
        if version.dependencies != expected_dependencies:
            raise _ProductionValidation(
                "SCRIPT_LINEAGE_MISMATCH", "Script dependencies are invalid"
            )
        return expected_dependencies[0], expected_dependencies[1], expected_dependencies[2]

    @classmethod
    def _validate_approval(
        cls,
        decision: ScriptDecisionRecord,
        script_reference: ArtifactReference,
        upstream: tuple[ArtifactReference, ArtifactReference, ArtifactReference],
    ) -> None:
        if not isinstance(decision, ScriptDecisionRecord):
            raise _ProductionValidation(
                "INVALID_SCRIPT_APPROVAL", "an approved Script decision is required"
            )
        if (
            decision.gate_kind != "script_review"
            or decision.action != "approve"
            or decision.assessment_disposition != "pass"
            or decision.script_reference != script_reference
            or decision.knowledge_reference != upstream[0]
            or decision.course_plan_reference != upstream[1]
            or decision.episode_plan_reference != upstream[2]
            or decision.finding_codes != ()
        ):
            raise _ProductionValidation(
                "SCRIPT_APPROVAL_MISMATCH", "Script approval does not match exact input"
            )
        cls._validate_identity(
            decision.decision_id,
            "INVALID_SCRIPT_APPROVAL",
            "Script approval identity is invalid",
        )

    def _invoke_runtime(self, request: ModelRuntimeRequest) -> ProductionModelRuntimeResult:
        runtime_invoke = getattr(self._runtime, "invoke", None)
        if not callable(runtime_invoke):
            raise _ProductionValidation("INVALID_RUNTIME", "model runtime is required")
        try:
            result = runtime_invoke(request)
        except Exception:
            raise _ProductionExecution(
                "MODEL_RUNTIME_FAILED", "model runtime execution failed"
            ) from None
        if isinstance(result, ModelRuntimeFailure):
            raise _ProductionExecution(
                "MODEL_RUNTIME_FAILED", "model runtime execution failed"
            )
        if not isinstance(result, ProductionModelRuntimeResult):
            raise _ProductionValidation(
                "INVALID_MODEL_RESULT", "model runtime result is invalid"
            )
        self._validate_diagnostics(result.diagnostics)
        return result

    @classmethod
    def _validate_character_result(
        cls,
        value: object,
        constraints: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping) or set(value) != _CHARACTER_FIELDS:
            raise _ProductionValidation(
                "INVALID_CHARACTER_RESULT", "character result is invalid"
            )
        name = cls._bounded_text(
            value.get("name"),
            "INVALID_CHARACTER_NAME",
            "character name is invalid",
        )
        design_version = cls._bounded_text(
            value.get("design_version"),
            "INVALID_CHARACTER_DESIGN_VERSION",
            "character design version is invalid",
        )
        if name != constraints["name"]:
            raise _ProductionValidation(
                "CHARACTER_NAME_MISMATCH", "character name does not match constraints"
            )
        if design_version != constraints["design_version"]:
            raise _ProductionValidation(
                "CHARACTER_DESIGN_VERSION_MISMATCH",
                "character design version does not match constraints",
            )
        summary = cls._bounded_text(
            value.get("summary"),
            "INVALID_CHARACTER_SUMMARY",
            "character summary is invalid",
        )
        traits: dict[str, tuple[str, ...]] = {}
        for field_name in (
            "visual_traits",
            "personality_traits",
            "continuity_rules",
        ):
            traits[field_name] = cls._trait_values(value.get(field_name), field_name)
        return {
            "name": name,
            "design_version": design_version,
            "summary": summary,
            **traits,
        }

    @classmethod
    def _trait_values(cls, value: object, field_name: str) -> tuple[str, ...]:
        if not isinstance(value, tuple) or not value or len(value) > _MAX_CHARACTER_TRAITS:
            raise _ProductionValidation(
                "INVALID_CHARACTER_TRAITS", f"{field_name} are invalid"
            )
        normalized = tuple(
            cls._bounded_text(item, "INVALID_CHARACTER_TRAITS", f"{field_name} are invalid")
            for item in value
        )
        if len(set(normalized)) != len(normalized):
            raise _ProductionValidation(
                "DUPLICATE_CHARACTER_TRAITS", f"{field_name} must be unique"
            )
        return normalized

    @classmethod
    def _validate_diagnostics(cls, diagnostics: object) -> None:
        if not isinstance(diagnostics, tuple) or len(diagnostics) > _MAX_CHARACTER_TRAITS:
            raise _ProductionValidation(
                "INVALID_MODEL_RESULT", "model runtime result is invalid"
            )
        for diagnostic in diagnostics:
            if not isinstance(diagnostic, str) or len(diagnostic) > _MAX_TEXT_LENGTH:
                raise _ProductionValidation(
                    "INVALID_MODEL_RESULT", "model runtime result is invalid"
                )

    @classmethod
    def _bounded_text(cls, value: object, code: str, message: str) -> str:
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > _MAX_TEXT_LENGTH
            or cls._has_control(value)
        ):
            raise _ProductionValidation(code, message)
        return value

    @classmethod
    def _validate_identity(cls, value: object, code: str, message: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > _MAX_IDENTITY_LENGTH
            or value.strip().casefold() == "latest"
            or cls._has_control(value)
        ):
            raise _ProductionValidation(code, message)

    @classmethod
    def _valid_reference(cls, value: object, artifact_type: str) -> bool:
        return (
            isinstance(value, ArtifactReference)
            and value.artifact_type == artifact_type
            and isinstance(value.identity, str)
            and bool(value.identity.strip())
            and value.identity.strip().casefold() != "latest"
            and len(value.identity) <= _MAX_IDENTITY_LENGTH
            and not cls._has_control(value.identity)
            and isinstance(value.version, int)
            and not isinstance(value.version, bool)
            and value.version > 0
        )

    @staticmethod
    def _has_control(value: str) -> bool:
        return any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
