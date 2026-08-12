"""Staged, provider-neutral Production Agent boundaries.

The first Production planning steps stop at provider-neutral Character and
Storyboard ``ArtifactCandidate`` values.  The Agent validates exact approved
inputs and normalises model-runtime results, while the existing Artifact
boundary owns validation and Commit of each candidate.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactReference,
    ArtifactVersion,
    ScriptDecisionRecord,
    StoryboardDecisionRecord,
)

from .runtime import (
    ModelRuntimeFailure,
    ModelRuntimePort,
    ModelRuntimeRequest,
    ProductionModelRuntimeResult,
    ProductionRequestModelRuntimeResult,
    StoryboardModelRuntimeResult,
    TimelineModelRuntimeResult,
)


_PURPOSE = "character_planning"
_MAX_IDENTITY_LENGTH = 256
_MAX_TEXT_LENGTH = 4096
_MAX_CHARACTER_TRAITS = 32
_MAX_STORYBOARD_SCENES = 128
_MAX_CONTINUITY_NOTES = 32
_MAX_SCENE_ID_LENGTH = 128
_TIMELINE_TOLERANCE = 1e-9

_STORYBOARD_PAYLOAD_FIELDS = {
    "script_reference",
    "approval_decision_id",
    "character_reference",
    "storyboard_constraints",
    "storyboard",
}

_TIMELINE_FIELDS = {"duration_seconds", "scenes"}
_TIMELINE_SCENE_FIELDS = {
    "scene_id",
    "start_seconds",
    "duration_seconds",
    "end_seconds",
}
_TIMELINE_PAYLOAD_FIELDS = {
    "script_reference",
    "approval_decision_id",
    "character_reference",
    "storyboard_reference",
    "storyboard_decision_id",
    "timeline",
}
_REQUEST_FIELDS = {"language", "aspect_ratio", "duration_seconds", "scenes"}
_REQUEST_SCENE_FIELDS = {
    "scene_id",
    "start_seconds",
    "duration_seconds",
    "end_seconds",
    "narration",
    "visual_intent",
    "character_action",
    "continuity_notes",
}

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
class StoryboardPlanningConstraints:
    """The sole Storyboard planning constraint."""

    aspect_ratio: str


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
            self._validate_approval(
                script_decision, script_reference, upstream
            )
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

    def plan_storyboard(
        self,
        script_reference: ArtifactReference,
        resolved_script: ArtifactVersion,
        script_decision: ScriptDecisionRecord,
        character_reference: ArtifactReference,
        resolved_character: ArtifactVersion,
        *,
        constraints: StoryboardPlanningConstraints | Mapping[str, str],
        storyboard_identity: str,
        storyboard_commit_id: str,
    ) -> ArtifactCandidate | ProductionAgentFailure:
        """Return a validated provider-neutral Storyboard Candidate.

        Exact input, lineage, approval and constraint checks complete before
        invoking the supplied model runtime.  The Agent never commits a
        Candidate or advances workflow state.
        """

        try:
            normalized_constraints = self._normalize_storyboard_constraints(constraints)
            self._validate_identity(
                storyboard_identity,
                "INVALID_STORYBOARD_IDENTITY",
                "Storyboard identity is required",
            )
            self._validate_identity(
                storyboard_commit_id,
                "INVALID_STORYBOARD_COMMIT_ID",
                "logical Commit identity is required",
            )
            upstream = self._validate_script(script_reference, resolved_script)
            script_aspect_ratio, script_scene_ids = self._validate_storyboard_script(
                resolved_script
            )
            self._validate_approval(script_decision, script_reference, upstream)
            self._validate_character_input(
                character_reference,
                resolved_character,
                script_reference,
                script_decision,
            )
            if normalized_constraints["aspect_ratio"] != script_aspect_ratio:
                raise _ProductionValidation(
                    "STORYBOARD_ASPECT_RATIO_MISMATCH",
                    "Storyboard aspect ratio does not match Script",
                )
            result = self._invoke_storyboard_runtime(
                ModelRuntimeRequest(
                    purpose="storyboard_planning",
                    inputs=MappingProxyType(
                        {
                            "script_reference": script_reference,
                            "script_payload": resolved_script.payload,
                            "character_reference": character_reference,
                            "character_payload": resolved_character.payload,
                            "approval_decision_id": script_decision.decision_id,
                        }
                    ),
                    constraints=MappingProxyType(
                        {"storyboard_constraints": normalized_constraints}
                    ),
                )
            )
            storyboard = self._validate_storyboard_result(
                result.storyboard,
                normalized_constraints,
                script_scene_ids,
            )
            return ArtifactCandidate(
                artifact_type="storyboard",
                identity=storyboard_identity,
                payload={
                    "script_reference": script_reference,
                    "approval_decision_id": script_decision.decision_id,
                    "character_reference": character_reference,
                    "storyboard_constraints": normalized_constraints,
                    "storyboard": storyboard,
                },
                provenance=(
                    {
                        "purpose": "storyboard_planning",
                        "script_reference": script_reference,
                        "character_reference": character_reference,
                        "approval_decision_id": script_decision.decision_id,
                    },
                ),
                dependencies=(script_reference, character_reference),
                validated=True,
                commit_id=storyboard_commit_id,
            )
        except _ProductionValidation as exc:
            return ProductionAgentFailure("validation", exc.code, exc.message)
        except _ProductionExecution as exc:
            return ProductionAgentFailure("execution", exc.code, exc.message)
        except Exception:
            return ProductionAgentFailure(
                "execution",
                "PRODUCTION_AGENT_FAILED",
                "production agent execution failed",
            )

    def plan_timeline(
        self,
        script_reference: ArtifactReference,
        resolved_script: ArtifactVersion,
        script_decision: ScriptDecisionRecord,
        character_reference: ArtifactReference,
        resolved_character: ArtifactVersion,
        storyboard_reference: ArtifactReference,
        resolved_storyboard: ArtifactVersion,
        storyboard_decision: StoryboardDecisionRecord,
        *,
        timeline_identity: str,
        timeline_commit_id: str,
    ) -> ArtifactCandidate | ProductionAgentFailure:
        """Return a validated provider-neutral Timeline Candidate.

        Timeline planning consumes only exact, already committed upstreams and
        a satisfying Storyboard decision.  It does not commit, advance
        workflow state, or invoke a media/provider adapter.
        """

        try:
            self._validate_timeline_identity(
                timeline_identity,
                "INVALID_TIMELINE_IDENTITY",
                "Timeline identity is required",
            )
            self._validate_timeline_identity(
                timeline_commit_id,
                "INVALID_TIMELINE_COMMIT_ID",
                "logical Commit identity is required",
            )
            self._validate_timeline_reference(script_reference, "script")
            self._validate_timeline_reference(character_reference, "character")
            self._validate_timeline_reference(storyboard_reference, "storyboard")

            script_upstream = self._validate_script(script_reference, resolved_script)
            script_duration, script_scenes = self._validate_timeline_script(
                resolved_script
            )
            self._validate_approval(script_decision, script_reference, script_upstream)
            self._validate_timeline_identity(
                script_decision.decision_id,
                "INVALID_SCRIPT_APPROVAL",
                "Script approval identity is invalid",
            )
            self._validate_character_input(
                character_reference,
                resolved_character,
                script_reference,
                script_decision,
            )
            storyboard_scene_ids = self._validate_timeline_storyboard(
                storyboard_reference,
                resolved_storyboard,
                script_reference,
                character_reference,
                script_decision,
                resolved_script,
                script_scenes,
            )
            self._validate_storyboard_decision(
                storyboard_decision,
                storyboard_reference,
                script_reference,
                character_reference,
                script_decision,
            )

            result = self._invoke_timeline_runtime(
                ModelRuntimeRequest(
                    purpose="timeline_planning",
                    inputs=MappingProxyType(
                        {
                            "script_reference": script_reference,
                            "script_payload": resolved_script.payload,
                            "character_reference": character_reference,
                            "character_payload": resolved_character.payload,
                            "storyboard_reference": storyboard_reference,
                            "storyboard_payload": resolved_storyboard.payload,
                            "approval_decision_id": script_decision.decision_id,
                            "storyboard_decision_id": storyboard_decision.decision_id,
                        }
                    ),
                    constraints=MappingProxyType({}),
                )
            )
            timeline = self._validate_timeline_result(
                result.timeline,
                script_duration,
                script_scenes,
                storyboard_scene_ids,
            )
            return ArtifactCandidate(
                artifact_type="timeline",
                identity=timeline_identity,
                payload={
                    "script_reference": script_reference,
                    "approval_decision_id": script_decision.decision_id,
                    "character_reference": character_reference,
                    "storyboard_reference": storyboard_reference,
                    "storyboard_decision_id": storyboard_decision.decision_id,
                    "timeline": timeline,
                },
                provenance=(
                    {
                        "purpose": "timeline_planning",
                        "script_reference": script_reference,
                        "character_reference": character_reference,
                        "storyboard_reference": storyboard_reference,
                        "approval_decision_id": script_decision.decision_id,
                        "storyboard_decision_id": storyboard_decision.decision_id,
                    },
                ),
                dependencies=(
                    script_reference,
                    character_reference,
                    storyboard_reference,
                ),
                validated=True,
                commit_id=timeline_commit_id,
            )
        except _ProductionValidation as exc:
            return ProductionAgentFailure("validation", exc.code, exc.message)
        except _ProductionExecution as exc:
            return ProductionAgentFailure("execution", exc.code, exc.message)
        except Exception:
            return ProductionAgentFailure(
                "execution",
                "PRODUCTION_AGENT_FAILED",
                "production agent execution failed",
            )

    def plan_request(
        self,
        script_reference: ArtifactReference,
        resolved_script: ArtifactVersion,
        script_decision: ScriptDecisionRecord,
        character_reference: ArtifactReference,
        resolved_character: ArtifactVersion,
        storyboard_reference: ArtifactReference,
        resolved_storyboard: ArtifactVersion,
        storyboard_decision: StoryboardDecisionRecord,
        timeline_reference: ArtifactReference,
        resolved_timeline: ArtifactVersion,
        *,
        request_identity: str,
        request_commit_id: str,
    ) -> ArtifactCandidate | ProductionAgentFailure:
        """Return a validated provider-neutral Production Request Candidate."""

        try:
            self._validate_timeline_identity(
                request_identity,
                "INVALID_PRODUCTION_REQUEST_IDENTITY",
                "Production Request identity is required",
            )
            self._validate_timeline_identity(
                request_commit_id,
                "INVALID_PRODUCTION_REQUEST_COMMIT_ID",
                "logical Commit identity is required",
            )
            for reference, artifact_type in (
                (script_reference, "script"),
                (character_reference, "character"),
                (storyboard_reference, "storyboard"),
                (timeline_reference, "timeline"),
            ):
                self._validate_timeline_reference(reference, artifact_type)

            script_upstream = self._validate_script(script_reference, resolved_script)
            language = self._bounded_text(
                resolved_script.payload.get("language"),
                "INVALID_SCRIPT_LANGUAGE",
                "Script language is invalid",
            )
            aspect_ratio, _ = self._validate_storyboard_script(resolved_script)
            script_duration, timed_scenes = self._validate_timeline_script(resolved_script)
            script_scenes = tuple(
                (
                    scene_id,
                    duration,
                    self._bounded_text(
                        scene["narration"],
                        "INVALID_SCRIPT_NARRATION",
                        "Script narration is invalid",
                    ),
                )
                for scene, (scene_id, duration) in zip(
                    resolved_script.payload["scenes"], timed_scenes
                )
            )
            self._validate_approval(script_decision, script_reference, script_upstream)
            self._validate_character_input(
                character_reference,
                resolved_character,
                script_reference,
                script_decision,
            )
            storyboard_scene_ids = self._validate_timeline_storyboard(
                storyboard_reference,
                resolved_storyboard,
                script_reference,
                character_reference,
                script_decision,
                resolved_script,
                timed_scenes,
            )
            self._validate_storyboard_decision(
                storyboard_decision,
                storyboard_reference,
                script_reference,
                character_reference,
                script_decision,
            )
            timeline = self._validate_request_timeline(
                timeline_reference,
                resolved_timeline,
                script_reference,
                character_reference,
                storyboard_reference,
                script_decision,
                storyboard_decision,
                script_duration,
                timed_scenes,
                storyboard_scene_ids,
            )
            result = self._invoke_request_runtime(
                ModelRuntimeRequest(
                    purpose="production_request_planning",
                    inputs=MappingProxyType(
                        {
                            "script_reference": script_reference,
                            "script_payload": resolved_script.payload,
                            "approval_decision_id": script_decision.decision_id,
                            "character_reference": character_reference,
                            "character_payload": resolved_character.payload,
                            "storyboard_reference": storyboard_reference,
                            "storyboard_payload": resolved_storyboard.payload,
                            "storyboard_decision_id": storyboard_decision.decision_id,
                            "timeline_reference": timeline_reference,
                            "timeline_payload": resolved_timeline.payload,
                        }
                    ),
                    constraints=MappingProxyType({}),
                )
            )
            production_request = self._validate_request_result(
                result.production_request,
                language,
                aspect_ratio,
                script_scenes,
                timeline,
                resolved_storyboard,
            )
            return ArtifactCandidate(
                artifact_type="production_request",
                identity=request_identity,
                payload={
                    "script_reference": script_reference,
                    "approval_decision_id": script_decision.decision_id,
                    "character_reference": character_reference,
                    "storyboard_reference": storyboard_reference,
                    "storyboard_decision_id": storyboard_decision.decision_id,
                    "timeline_reference": timeline_reference,
                    "production_request": production_request,
                },
                provenance=(
                    {
                        "purpose": "production_request_planning",
                        "script_reference": script_reference,
                        "character_reference": character_reference,
                        "storyboard_reference": storyboard_reference,
                        "timeline_reference": timeline_reference,
                        "approval_decision_id": script_decision.decision_id,
                        "storyboard_decision_id": storyboard_decision.decision_id,
                    },
                ),
                dependencies=(
                    script_reference,
                    character_reference,
                    storyboard_reference,
                    timeline_reference,
                ),
                validated=True,
                commit_id=request_commit_id,
            )
        except _ProductionValidation as exc:
            return ProductionAgentFailure("validation", exc.code, exc.message)
        except _ProductionExecution as exc:
            return ProductionAgentFailure("execution", exc.code, exc.message)
        except Exception:
            return ProductionAgentFailure(
                "execution",
                "PRODUCTION_AGENT_FAILED",
                "production agent execution failed",
            )

    @classmethod
    def _validate_request_timeline(
        cls,
        reference: ArtifactReference,
        version: ArtifactVersion,
        script_reference: ArtifactReference,
        character_reference: ArtifactReference,
        storyboard_reference: ArtifactReference,
        script_decision: ScriptDecisionRecord,
        storyboard_decision: StoryboardDecisionRecord,
        script_duration: float,
        script_scenes: tuple[tuple[str, float], ...],
        storyboard_scene_ids: tuple[str, ...],
    ) -> Mapping[str, Any]:
        if not isinstance(version, ArtifactVersion):
            raise _ProductionValidation("INVALID_TIMELINE_VERSION", "a resolved Timeline Version is required")
        if version.reference != reference:
            raise _ProductionValidation("TIMELINE_REFERENCE_MISMATCH", "Timeline Reference does not match Version")
        if version.dependencies != (script_reference, character_reference, storyboard_reference):
            raise _ProductionValidation("TIMELINE_LINEAGE_MISMATCH", "Timeline dependencies are invalid")
        payload = version.payload
        if (
            not isinstance(payload, Mapping)
            or set(payload) != _TIMELINE_PAYLOAD_FIELDS
            or payload.get("script_reference") != script_reference
            or payload.get("character_reference") != character_reference
            or payload.get("storyboard_reference") != storyboard_reference
            or payload.get("approval_decision_id") != script_decision.decision_id
            or payload.get("storyboard_decision_id") != storyboard_decision.decision_id
        ):
            raise _ProductionValidation("TIMELINE_LINEAGE_MISMATCH", "Timeline lineage is invalid")
        for value in (payload["approval_decision_id"], payload["storyboard_decision_id"]):
            cls._validate_timeline_identity(
                value, "INVALID_TIMELINE_PAYLOAD", "Timeline decision identity is invalid"
            )
        normalized = cls._validate_timeline_result(
            payload["timeline"], script_duration, script_scenes, storyboard_scene_ids
        )
        if normalized != payload["timeline"]:
            raise _ProductionValidation("INVALID_TIMELINE_PAYLOAD", "Timeline payload is not normalized")
        return normalized

    def _invoke_request_runtime(
        self, request: ModelRuntimeRequest
    ) -> ProductionRequestModelRuntimeResult:
        runtime_invoke = getattr(self._runtime, "invoke", None)
        if not callable(runtime_invoke):
            raise _ProductionValidation("INVALID_RUNTIME", "model runtime is required")
        try:
            result = runtime_invoke(request)
        except Exception:
            raise _ProductionExecution("MODEL_RUNTIME_FAILED", "model runtime execution failed") from None
        if isinstance(result, ModelRuntimeFailure):
            raise _ProductionExecution("MODEL_RUNTIME_FAILED", "model runtime execution failed")
        if not isinstance(result, ProductionRequestModelRuntimeResult):
            raise _ProductionValidation("INVALID_MODEL_RESULT", "model runtime result is invalid")
        self._validate_diagnostics(result.diagnostics)
        if any(self._has_control(item) for item in result.diagnostics):
            raise _ProductionValidation("INVALID_MODEL_RESULT", "model runtime result is invalid")
        return result

    @classmethod
    def _validate_request_result(
        cls,
        value: object,
        language: str,
        aspect_ratio: str,
        script_scenes: tuple[tuple[str, float, str], ...],
        timeline: Mapping[str, Any],
        storyboard_version: ArtifactVersion,
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping) or set(value) != _REQUEST_FIELDS:
            raise _ProductionValidation("INVALID_PRODUCTION_REQUEST_RESULT", "Production Request result is invalid")
        storyboard_payload = storyboard_version.payload
        storyboard_scenes = storyboard_payload["storyboard"]["scenes"]
        expected_scenes = tuple(
            {
                "scene_id": scene_id,
                "start_seconds": timing["start_seconds"],
                "duration_seconds": timing["duration_seconds"],
                "end_seconds": timing["end_seconds"],
                "narration": narration,
                "visual_intent": storyboard_scene["visual_intent"],
                "character_action": storyboard_scene["character_action"],
                "continuity_notes": storyboard_scene["continuity_notes"],
            }
            for (scene_id, _duration, narration), timing, storyboard_scene in zip(
                script_scenes, timeline["scenes"], storyboard_scenes
            )
        )
        expected = {
            "language": language,
            "aspect_ratio": aspect_ratio,
            "duration_seconds": timeline["duration_seconds"],
            "scenes": expected_scenes,
        }
        scenes = value.get("scenes")
        if (
            not isinstance(scenes, tuple)
            or len(scenes) != len(expected_scenes)
            or any(not isinstance(scene, Mapping) or set(scene) != _REQUEST_SCENE_FIELDS for scene in scenes)
            or value != expected
        ):
            raise _ProductionValidation("INVALID_PRODUCTION_REQUEST_RESULT", "Production Request result is invalid")
        return expected

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
    def _normalize_storyboard_constraints(
        cls, value: StoryboardPlanningConstraints | Mapping[str, str]
    ) -> Mapping[str, str]:
        if isinstance(value, StoryboardPlanningConstraints):
            raw = {"aspect_ratio": value.aspect_ratio}
        elif isinstance(value, Mapping) and set(value) == {"aspect_ratio"}:
            raw = value
        else:
            raise _ProductionValidation(
                "INVALID_STORYBOARD_CONSTRAINTS",
                "Storyboard constraints must contain aspect ratio",
            )
        aspect_ratio = cls._bounded_text(
            raw["aspect_ratio"],
            "INVALID_STORYBOARD_CONSTRAINTS",
            "Storyboard aspect ratio is invalid",
        )
        return MappingProxyType({"aspect_ratio": aspect_ratio})

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
    def _validate_storyboard_script(
        cls, version: ArtifactVersion
    ) -> tuple[str, tuple[str, ...]]:
        payload = version.payload
        if not isinstance(payload, Mapping):
            raise _ProductionValidation(
                "INVALID_SCRIPT_PAYLOAD", "resolved Script payload is invalid"
            )
        aspect_ratio = cls._bounded_text(
            payload.get("aspect_ratio"),
            "INVALID_SCRIPT_FORMAT",
            "Script aspect ratio is invalid",
        )
        scenes = payload.get("scenes")
        if (
            not isinstance(scenes, tuple)
            or not scenes
            or len(scenes) > _MAX_STORYBOARD_SCENES
        ):
            raise _ProductionValidation(
                "INVALID_SCRIPT_SCENES", "Script scenes are invalid"
            )
        scene_ids: list[str] = []
        for scene in scenes:
            if not isinstance(scene, Mapping):
                raise _ProductionValidation(
                    "INVALID_SCRIPT_SCENES", "Script scenes are invalid"
                )
            scene_id = scene.get("scene_id")
            if (
                not isinstance(scene_id, str)
                or not scene_id.strip()
                or len(scene_id) > _MAX_SCENE_ID_LENGTH
                or cls._has_control(scene_id)
                or scene_id in scene_ids
            ):
                raise _ProductionValidation(
                    "INVALID_SCRIPT_SCENES", "Script scene identities are invalid"
                )
            scene_ids.append(scene_id)
        return aspect_ratio, tuple(scene_ids)

    @classmethod
    def _validate_character_input(
        cls,
        reference: ArtifactReference,
        version: ArtifactVersion,
        script_reference: ArtifactReference,
        script_decision: ScriptDecisionRecord,
    ) -> None:
        if not cls._valid_reference(reference, "character"):
            raise _ProductionValidation(
                "INVALID_CHARACTER_REFERENCE",
                "an exact character Reference is required",
            )
        if not isinstance(version, ArtifactVersion):
            raise _ProductionValidation(
                "INVALID_CHARACTER_VERSION", "a resolved Character Version is required"
            )
        if version.reference != reference:
            raise _ProductionValidation(
                "CHARACTER_REFERENCE_MISMATCH",
                "Character Reference does not match Version",
            )
        if version.dependencies != (script_reference,):
            raise _ProductionValidation(
                "CHARACTER_LINEAGE_MISMATCH",
                "Character dependencies are invalid",
            )
        payload = version.payload
        if not isinstance(payload, Mapping) or set(payload) != {
            "script_reference",
            "approval_decision_id",
            "character_constraints",
            "character",
        }:
            raise _ProductionValidation(
                "INVALID_CHARACTER_PAYLOAD", "Character payload is invalid"
            )
        if payload.get("script_reference") != script_reference:
            raise _ProductionValidation(
                "CHARACTER_LINEAGE_MISMATCH",
                "Character Script Reference does not match",
            )
        approval_id = payload.get("approval_decision_id")
        cls._validate_identity(
            approval_id,
            "INVALID_CHARACTER_PAYLOAD",
            "Character approval identity is invalid",
        )
        if approval_id != script_decision.decision_id:
            raise _ProductionValidation(
                "CHARACTER_APPROVAL_MISMATCH",
                "Character approval identity does not match",
            )
        character_constraints = cls._normalize_constraints(
            payload.get("character_constraints")
        )
        cls._validate_character_result(payload.get("character"), character_constraints)

    @classmethod
    def _validate_timeline_reference(
        cls, reference: object, artifact_type: str
    ) -> None:
        if (
            not cls._valid_reference(reference, artifact_type)
            or reference.identity.strip().casefold() == "current"
        ):
            raise _ProductionValidation(
                f"INVALID_{artifact_type.upper()}_REFERENCE",
                f"an exact {artifact_type} Reference is required",
            )

    @classmethod
    def _validate_timeline_identity(
        cls, value: object, code: str, message: str
    ) -> None:
        cls._validate_identity(value, code, message)
        if value.strip().casefold() == "current":
            raise _ProductionValidation(code, message)

    @classmethod
    def _validate_timeline_script(
        cls, version: ArtifactVersion
    ) -> tuple[float, tuple[tuple[str, float], ...]]:
        payload = version.payload
        if not isinstance(payload, Mapping):
            raise _ProductionValidation(
                "INVALID_SCRIPT_PAYLOAD", "resolved Script payload is invalid"
            )
        duration = cls._timeline_number(
            payload.get("duration_seconds"),
            "INVALID_SCRIPT_DURATION",
            "Script duration is invalid",
        )
        if duration <= 0:
            raise _ProductionValidation(
                "INVALID_SCRIPT_DURATION", "Script duration is invalid"
            )
        scenes = payload.get("scenes")
        if (
            not isinstance(scenes, tuple)
            or not scenes
            or len(scenes) > _MAX_STORYBOARD_SCENES
        ):
            raise _ProductionValidation(
                "INVALID_SCRIPT_SCENES", "Script scenes are invalid"
            )

        normalized: list[tuple[str, float]] = []
        scene_ids: set[str] = set()
        for scene in scenes:
            if not isinstance(scene, Mapping):
                raise _ProductionValidation(
                    "INVALID_SCRIPT_SCENES", "Script scenes are invalid"
                )
            scene_id = scene.get("scene_id")
            cls._validate_timeline_scene_id(scene_id, "INVALID_SCRIPT_SCENES")
            if scene_id in scene_ids:
                raise _ProductionValidation(
                    "INVALID_SCRIPT_SCENES", "Script scene identities are invalid"
                )
            scene_ids.add(scene_id)
            scene_duration = cls._timeline_number(
                scene.get("duration_seconds"),
                "INVALID_SCRIPT_SCENES",
                "Script scene durations are invalid",
            )
            if scene_duration <= 0:
                raise _ProductionValidation(
                    "INVALID_SCRIPT_SCENES", "Script scene durations are invalid"
                )
            normalized.append((scene_id, scene_duration))

        if not cls._timeline_close(sum(duration_value for _, duration_value in normalized), duration):
            raise _ProductionValidation(
                "SCRIPT_DURATION_MISMATCH", "Script scene durations do not match total"
            )
        return duration, tuple(normalized)

    @classmethod
    def _validate_timeline_storyboard(
        cls,
        reference: ArtifactReference,
        version: ArtifactVersion,
        script_reference: ArtifactReference,
        character_reference: ArtifactReference,
        script_decision: ScriptDecisionRecord,
        script_version: ArtifactVersion,
        script_scenes: tuple[tuple[str, float], ...],
    ) -> tuple[str, ...]:
        if not isinstance(version, ArtifactVersion):
            raise _ProductionValidation(
                "INVALID_STORYBOARD_VERSION",
                "a resolved Storyboard Version is required",
            )
        if version.reference != reference:
            raise _ProductionValidation(
                "STORYBOARD_REFERENCE_MISMATCH",
                "Storyboard Reference does not match Version",
            )
        if version.dependencies != (script_reference, character_reference):
            raise _ProductionValidation(
                "STORYBOARD_LINEAGE_MISMATCH",
                "Storyboard dependencies are invalid",
            )
        payload = version.payload
        if not isinstance(payload, Mapping) or set(payload) != _STORYBOARD_PAYLOAD_FIELDS:
            raise _ProductionValidation(
                "INVALID_STORYBOARD_PAYLOAD", "Storyboard payload is invalid"
            )
        if payload.get("script_reference") != script_reference:
            raise _ProductionValidation(
                "STORYBOARD_LINEAGE_MISMATCH",
                "Storyboard Script Reference does not match",
            )
        if payload.get("character_reference") != character_reference:
            raise _ProductionValidation(
                "STORYBOARD_LINEAGE_MISMATCH",
                "Storyboard Character Reference does not match",
            )
        approval_id = payload.get("approval_decision_id")
        cls._validate_identity(
            approval_id,
            "INVALID_STORYBOARD_PAYLOAD",
            "Storyboard approval identity is invalid",
        )
        if approval_id != script_decision.decision_id:
            raise _ProductionValidation(
                "STORYBOARD_APPROVAL_MISMATCH",
                "Storyboard approval identity does not match",
            )

        script_aspect_ratio = cls._bounded_text(
            script_version.payload.get("aspect_ratio"),
            "INVALID_SCRIPT_FORMAT",
            "Script aspect ratio is invalid",
        )
        storyboard_constraints = cls._normalize_storyboard_constraints(
            payload.get("storyboard_constraints")
        )
        if storyboard_constraints["aspect_ratio"] != script_aspect_ratio:
            raise _ProductionValidation(
                "STORYBOARD_ASPECT_RATIO_MISMATCH",
                "Storyboard aspect ratio does not match Script",
            )
        storyboard = cls._validate_storyboard_result(
            payload.get("storyboard"),
            storyboard_constraints,
            tuple(scene_id for scene_id, _ in script_scenes),
        )
        return tuple(scene["scene_id"] for scene in storyboard["scenes"])

    @classmethod
    def _validate_storyboard_decision(
        cls,
        decision: StoryboardDecisionRecord,
        storyboard_reference: ArtifactReference,
        script_reference: ArtifactReference,
        character_reference: ArtifactReference,
        script_decision: ScriptDecisionRecord,
    ) -> None:
        if not isinstance(decision, StoryboardDecisionRecord):
            raise _ProductionValidation(
                "INVALID_STORYBOARD_DECISION",
                "a Storyboard decision record is required",
            )
        if decision.gate_kind != "storyboard_review":
            raise _ProductionValidation(
                "STORYBOARD_DECISION_MISMATCH",
                "Storyboard decision gate is invalid",
            )
        if decision.storyboard_reference != storyboard_reference:
            raise _ProductionValidation(
                "STORYBOARD_DECISION_MISMATCH",
                "Storyboard decision Reference does not match",
            )
        if decision.script_reference != script_reference:
            raise _ProductionValidation(
                "STORYBOARD_DECISION_MISMATCH",
                "Storyboard decision Script Reference does not match",
            )
        if decision.character_reference != character_reference:
            raise _ProductionValidation(
                "STORYBOARD_DECISION_MISMATCH",
                "Storyboard decision Character Reference does not match",
            )
        if decision.script_approval_decision_id != script_decision.decision_id:
            raise _ProductionValidation(
                "STORYBOARD_DECISION_MISMATCH",
                "Storyboard decision approval identity does not match",
            )
        for value, code, message in (
            (decision.decision_id, "INVALID_STORYBOARD_DECISION", "Storyboard decision identity is invalid"),
            (decision.task_id, "INVALID_STORYBOARD_DECISION", "Storyboard decision task identity is invalid"),
            (decision.thread_id, "INVALID_STORYBOARD_DECISION", "Storyboard decision thread identity is invalid"),
            (decision.creator_id, "INVALID_STORYBOARD_DECISION", "Storyboard decision Creator identity is invalid"),
        ):
            cls._validate_timeline_identity(value, code, message)
        if type(decision.review_enabled) is not bool:
            raise _ProductionValidation(
                "INVALID_STORYBOARD_DECISION",
                "Storyboard decision review mode is invalid",
            )
        if decision.review_enabled is True and decision.action != "approve":
            raise _ProductionValidation(
                "STORYBOARD_GATE_UNSATISFIED",
                "Storyboard Review approval is required",
            )
        if decision.review_enabled is False and decision.action != "skip":
            raise _ProductionValidation(
                "STORYBOARD_GATE_UNSATISFIED",
                "Storyboard Review skip is required when disabled",
            )
        if (
            not isinstance(decision.decision_context, str)
            or len(decision.decision_context) > _MAX_TEXT_LENGTH
            or cls._has_control(decision.decision_context)
        ):
            raise _ProductionValidation(
                "INVALID_STORYBOARD_DECISION",
                "Storyboard decision context is invalid",
            )

    def _invoke_timeline_runtime(
        self, request: ModelRuntimeRequest
    ) -> TimelineModelRuntimeResult:
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
        if not isinstance(result, TimelineModelRuntimeResult):
            raise _ProductionValidation(
                "INVALID_MODEL_RESULT", "model runtime result is invalid"
            )
        self._validate_diagnostics(result.diagnostics)
        if any(self._has_control(item) for item in result.diagnostics):
            raise _ProductionValidation(
                "INVALID_MODEL_RESULT", "model runtime result is invalid"
            )
        return result

    @classmethod
    def _validate_timeline_result(
        cls,
        value: object,
        script_duration: float,
        script_scenes: tuple[tuple[str, float], ...],
        storyboard_scene_ids: tuple[str, ...],
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping) or set(value) != _TIMELINE_FIELDS:
            raise _ProductionValidation(
                "INVALID_TIMELINE_RESULT", "Timeline result is invalid"
            )
        model_duration = cls._timeline_number(
            value.get("duration_seconds"),
            "INVALID_TIMELINE_RESULT",
            "Timeline result is invalid",
        )
        if model_duration <= 0 or not cls._timeline_close(model_duration, script_duration):
            raise _ProductionValidation(
                "TIMELINE_DURATION_MISMATCH", "Timeline duration does not match Script"
            )
        scenes = value.get("scenes")
        if (
            not isinstance(scenes, tuple)
            or not scenes
            or len(scenes) > _MAX_STORYBOARD_SCENES
            or len(scenes) != len(script_scenes)
            or len(storyboard_scene_ids) != len(script_scenes)
        ):
            raise _ProductionValidation(
                "INVALID_TIMELINE_SCENES", "Timeline scenes are invalid"
            )

        expected_scene_ids = tuple(scene_id for scene_id, _ in script_scenes)
        if storyboard_scene_ids != expected_scene_ids:
            raise _ProductionValidation(
                "STORYBOARD_SCENE_ORDER_MISMATCH",
                "Storyboard scene identities must match Script order",
            )

        normalized_scenes: list[dict[str, Any]] = []
        actual_scene_ids: list[str] = []
        previous_end = 0.0
        for index, scene in enumerate(scenes):
            if not isinstance(scene, Mapping) or set(scene) != _TIMELINE_SCENE_FIELDS:
                raise _ProductionValidation(
                    "INVALID_TIMELINE_SCENE", "Timeline scene is invalid"
                )
            scene_id = scene.get("scene_id")
            cls._validate_timeline_scene_id(scene_id, "INVALID_TIMELINE_SCENE")
            if scene_id in actual_scene_ids:
                raise _ProductionValidation(
                    "DUPLICATE_TIMELINE_SCENE", "Timeline scene identities must be unique"
                )
            actual_scene_ids.append(scene_id)
            start = cls._timeline_number(
                scene.get("start_seconds"),
                "INVALID_TIMELINE_SCENE",
                "Timeline scene timing is invalid",
            )
            duration = cls._timeline_number(
                scene.get("duration_seconds"),
                "INVALID_TIMELINE_SCENE",
                "Timeline scene timing is invalid",
            )
            end = cls._timeline_number(
                scene.get("end_seconds"),
                "INVALID_TIMELINE_SCENE",
                "Timeline scene timing is invalid",
            )
            if start < 0 or duration <= 0 or end <= 0:
                raise _ProductionValidation(
                    "INVALID_TIMELINE_SCENE", "Timeline scene timing is invalid"
                )
            if scene_id != expected_scene_ids[index]:
                raise _ProductionValidation(
                    "TIMELINE_SCENE_ORDER_MISMATCH",
                    "Timeline scene identities must match Script order",
                )
            expected_duration = script_scenes[index][1]
            if not cls._timeline_close(duration, expected_duration):
                raise _ProductionValidation(
                    "TIMELINE_SCENE_DURATION_MISMATCH",
                    "Timeline scene duration does not match Script",
                )
            if index == 0:
                if not cls._timeline_close(start, 0.0):
                    raise _ProductionValidation(
                        "TIMELINE_NOT_ZERO_BASED",
                        "Timeline must start at zero",
                    )
            elif not cls._timeline_close(start, previous_end):
                raise _ProductionValidation(
                    "TIMELINE_NOT_CONTIGUOUS",
                    "Timeline scenes must be contiguous",
                )
            if not cls._timeline_close(end, start + duration):
                raise _ProductionValidation(
                    "TIMELINE_END_MISMATCH",
                    "Timeline scene end does not match start plus duration",
                )
            normalized_start = 0.0 if index == 0 else previous_end
            normalized_duration = expected_duration
            normalized_end = normalized_start + normalized_duration
            normalized_scenes.append(
                {
                    "scene_id": scene_id,
                    "start_seconds": normalized_start,
                    "duration_seconds": normalized_duration,
                    "end_seconds": normalized_end,
                }
            )
            previous_end = normalized_end

        if tuple(actual_scene_ids) != expected_scene_ids:
            raise _ProductionValidation(
                "TIMELINE_SCENE_ORDER_MISMATCH",
                "Timeline scene identities must match Script order",
            )
        if not cls._timeline_close(previous_end, script_duration):
            raise _ProductionValidation(
                "TIMELINE_FINAL_END_MISMATCH",
                "Timeline final end does not match Script duration",
            )
        return {
            "duration_seconds": script_duration,
            "scenes": tuple(normalized_scenes),
        }

    @classmethod
    def _validate_timeline_scene_id(cls, value: object, code: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > _MAX_SCENE_ID_LENGTH
            or cls._has_control(value)
        ):
            raise _ProductionValidation(code, "Timeline scene identity is invalid")

    @staticmethod
    def _timeline_number(value: object, code: str, message: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise _ProductionValidation(code, message)
        try:
            normalized = float(value)
        except (OverflowError, ValueError):
            raise _ProductionValidation(code, message) from None
        if not math.isfinite(normalized):
            raise _ProductionValidation(code, message)
        return normalized

    @staticmethod
    def _timeline_close(left: float, right: float) -> bool:
        return math.isclose(
            left,
            right,
            rel_tol=_TIMELINE_TOLERANCE,
            abs_tol=_TIMELINE_TOLERANCE,
        )

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

    def _invoke_storyboard_runtime(
        self, request: ModelRuntimeRequest
    ) -> StoryboardModelRuntimeResult:
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
        if not isinstance(result, StoryboardModelRuntimeResult):
            raise _ProductionValidation(
                "INVALID_MODEL_RESULT", "model runtime result is invalid"
            )
        self._validate_diagnostics(result.diagnostics)
        return result

    @classmethod
    def _validate_storyboard_result(
        cls,
        value: object,
        constraints: Mapping[str, str],
        expected_scene_ids: tuple[str, ...],
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping) or set(value) != {"aspect_ratio", "scenes"}:
            raise _ProductionValidation(
                "INVALID_STORYBOARD_RESULT", "storyboard result is invalid"
            )
        aspect_ratio = cls._bounded_text(
            value.get("aspect_ratio"),
            "INVALID_STORYBOARD_ASPECT_RATIO",
            "Storyboard aspect ratio is invalid",
        )
        if aspect_ratio != constraints["aspect_ratio"]:
            raise _ProductionValidation(
                "STORYBOARD_ASPECT_RATIO_MISMATCH",
                "Storyboard aspect ratio does not match constraints",
            )
        scenes = value.get("scenes")
        if (
            not isinstance(scenes, tuple)
            or not scenes
            or len(scenes) > _MAX_STORYBOARD_SCENES
            or len(scenes) != len(expected_scene_ids)
        ):
            raise _ProductionValidation(
                "INVALID_STORYBOARD_SCENES", "Storyboard scenes are invalid"
            )
        normalized_scenes: list[dict[str, Any]] = []
        actual_scene_ids: list[str] = []
        for scene in scenes:
            if not isinstance(scene, Mapping) or set(scene) != {
                "scene_id",
                "visual_intent",
                "character_action",
                "continuity_notes",
            }:
                raise _ProductionValidation(
                    "INVALID_STORYBOARD_SCENE", "Storyboard scene is invalid"
                )
            scene_id = scene.get("scene_id")
            if (
                not isinstance(scene_id, str)
                or not scene_id.strip()
                or len(scene_id) > _MAX_SCENE_ID_LENGTH
                or cls._has_control(scene_id)
            ):
                raise _ProductionValidation(
                    "INVALID_STORYBOARD_SCENE", "Storyboard scene is invalid"
                )
            actual_scene_ids.append(scene_id)
            visual_intent = cls._bounded_text(
                scene.get("visual_intent"),
                "INVALID_STORYBOARD_SCENE",
                "Storyboard scene is invalid",
            )
            character_action = cls._bounded_text(
                scene.get("character_action"),
                "INVALID_STORYBOARD_SCENE",
                "Storyboard scene is invalid",
            )
            continuity_notes = cls._continuity_notes(scene.get("continuity_notes"))
            normalized_scenes.append(
                {
                    "scene_id": scene_id,
                    "visual_intent": visual_intent,
                    "character_action": character_action,
                    "continuity_notes": continuity_notes,
                }
            )
        if tuple(actual_scene_ids) != expected_scene_ids:
            raise _ProductionValidation(
                "STORYBOARD_SCENE_ORDER_MISMATCH",
                "Storyboard scene identities must match Script order",
            )
        return {"aspect_ratio": aspect_ratio, "scenes": tuple(normalized_scenes)}

    @classmethod
    def _continuity_notes(cls, value: object) -> tuple[str, ...]:
        if (
            not isinstance(value, tuple)
            or not value
            or len(value) > _MAX_CONTINUITY_NOTES
        ):
            raise _ProductionValidation(
                "INVALID_STORYBOARD_SCENE", "Storyboard continuity notes are invalid"
            )
        notes = tuple(
            cls._bounded_text(
                item,
                "INVALID_STORYBOARD_SCENE",
                "Storyboard continuity notes are invalid",
            )
            for item in value
        )
        if len(set(notes)) != len(notes):
            raise _ProductionValidation(
                "DUPLICATE_CONTINUITY_NOTES",
                "Storyboard continuity notes must be unique",
            )
        return notes

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
