"""Deterministic provider-neutral Scene Generation Contract planning.

The planner is deliberately narrower than the media production boundary.  It
only reads exact, already committed planning Versions and exact Creator
decision records, then proposes one immutable Artifact Candidate.  The
Artifact repository remains the only owner allowed to commit that Candidate.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math
from typing import Any

from ai_course_factory.artifacts import (
    ArtifactCandidate,
    ArtifactReference,
    ArtifactVersion,
    ScriptDecisionRecord,
    StoryboardDecisionRecord,
)


_SCENE_COUNT = 6
_CONTRACT_PAYLOAD_FIELDS = {
    "script_reference",
    "approval_decision_id",
    "character_reference",
    "storyboard_reference",
    "storyboard_decision_id",
    "timeline_reference",
    "production_request_reference",
    "scene_generation_contract",
}
_CONTRACT_FIELDS = {"scenes"}
_ENTRY_FIELDS = {
    "scene_id",
    "duration_milliseconds",
    "narration_identity",
    "narration",
    "visual_intent",
    "character_action",
    "continuity_notes",
    "generation_prompt",
    "camera_motion_instruction",
    "negative_constraints",
    "expected_filename",
}
_MAX_TEXT_LENGTH = 4096
_MAX_SCENE_ID_LENGTH = 128
_MAX_IDENTITY_LENGTH = 256


@dataclass(frozen=True, slots=True)
class SceneGenerationContractFailure:
    """Safe validation or execution failure from the contract seam."""

    kind: str
    code: str
    message: str


class _ContractValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SceneGenerationContractPlanner:
    """Propose one exact provider-neutral Scene Generation Contract."""

    def plan(
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
        production_request_reference: ArtifactReference,
        resolved_production_request: ArtifactVersion,
        *,
        contract_identity: str,
        contract_commit_id: str,
    ) -> ArtifactCandidate | SceneGenerationContractFailure:
        """Return a validated Candidate or a bounded failure.

        All input Versions and both approval records are checked before any
        prompt or entry is built.  No runtime, Provider or repository is
        invoked here.
        """

        try:
            self._validate_identity(contract_identity, "INVALID_CONTRACT_IDENTITY")
            self._validate_identity(contract_commit_id, "INVALID_CONTRACT_COMMIT_ID")
            self._validate_reference(script_reference, "script")
            self._validate_reference(character_reference, "character")
            self._validate_reference(storyboard_reference, "storyboard")
            self._validate_reference(timeline_reference, "timeline")
            self._validate_reference(production_request_reference, "production_request")
            self._validate_version(script_reference, resolved_script, "script")
            self._validate_version(character_reference, resolved_character, "character")
            self._validate_version(storyboard_reference, resolved_storyboard, "storyboard")
            self._validate_version(timeline_reference, resolved_timeline, "timeline")
            self._validate_version(production_request_reference, resolved_production_request, "production_request")
            self._validate_script_approval(script_reference, script_decision)
            storyboard = self._validate_storyboard_approval(
                script_reference,
                character_reference,
                storyboard_reference,
                script_decision,
                storyboard_decision,
                resolved_storyboard,
            )
            timeline = self._validate_timeline(
                script_reference,
                character_reference,
                storyboard_reference,
                timeline_reference,
                script_decision,
                storyboard_decision,
                resolved_timeline,
                resolved_script,
                storyboard,
            )
            request = self._validate_production_request(
                script_reference,
                character_reference,
                storyboard_reference,
                timeline_reference,
                production_request_reference,
                script_decision,
                storyboard_decision,
                resolved_production_request,
                resolved_script,
                storyboard,
                timeline,
            )
            entries = self._build_entries(resolved_script, storyboard, timeline, request)
            payload = {
                "script_reference": script_reference,
                "approval_decision_id": script_decision.decision_id,
                "character_reference": character_reference,
                "storyboard_reference": storyboard_reference,
                "storyboard_decision_id": storyboard_decision.decision_id,
                "timeline_reference": timeline_reference,
                "production_request_reference": production_request_reference,
                "scene_generation_contract": {"scenes": entries},
            }
            provenance = (
                {
                    "purpose": "scene_generation_contract_planning",
                    "script_reference": script_reference,
                    "character_reference": character_reference,
                    "storyboard_reference": storyboard_reference,
                    "timeline_reference": timeline_reference,
                    "production_request_reference": production_request_reference,
                    "script_approval_decision_id": script_decision.decision_id,
                    "storyboard_approval_decision_id": storyboard_decision.decision_id,
                },
            )
            return ArtifactCandidate(
                artifact_type="scene_generation_contract",
                identity=contract_identity,
                payload=payload,
                provenance=provenance,
                dependencies=(
                    script_reference,
                    character_reference,
                    storyboard_reference,
                    timeline_reference,
                    production_request_reference,
                ),
                validated=True,
                commit_id=contract_commit_id,
            )
        except _ContractValidation as exc:
            return SceneGenerationContractFailure("validation", exc.code, exc.message)
        except Exception:
            return SceneGenerationContractFailure(
                "execution",
                "SCENE_GENERATION_CONTRACT_FAILED",
                "scene generation contract planning failed",
            )

    @classmethod
    def _validate_identity(cls, value: object, code: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or len(value) > _MAX_IDENTITY_LENGTH
            or value.strip().casefold() in {"latest", "current"}
            or cls._has_control(value)
        ):
            raise _ContractValidation(code, "a bounded exact identity is required")

    @classmethod
    def _validate_reference(cls, value: object, artifact_type: str) -> None:
        if (
            not isinstance(value, ArtifactReference)
            or value.artifact_type != artifact_type
            or not isinstance(value.identity, str)
            or not value.identity.strip()
            or value.identity.strip().casefold() in {"latest", "current"}
            or not isinstance(value.version, int)
            or isinstance(value.version, bool)
            or value.version <= 0
        ):
            raise _ContractValidation(
                f"INVALID_{artifact_type.upper()}_REFERENCE",
                f"an exact {artifact_type} Reference is required",
            )

    @staticmethod
    def _validate_version(reference: ArtifactReference, version: object, label: str) -> None:
        if not isinstance(version, ArtifactVersion) or version.reference != reference:
            raise _ContractValidation(
                f"{label.upper()}_REFERENCE_MISMATCH",
                f"{label} Reference does not match Version",
            )

    @classmethod
    def _validate_script_approval(cls, reference: ArtifactReference, decision: object) -> None:
        if (
            not isinstance(decision, ScriptDecisionRecord)
            or decision.action != "approve"
            or decision.script_reference != reference
        ):
            raise _ContractValidation(
                "SCRIPT_APPROVAL_REQUIRED",
                "an exact approved Script decision is required",
            )
        cls._validate_identity(decision.decision_id, "INVALID_SCRIPT_APPROVAL_ID")

    @classmethod
    def _validate_storyboard_approval(
        cls,
        script_reference: ArtifactReference,
        character_reference: ArtifactReference,
        storyboard_reference: ArtifactReference,
        script_decision: ScriptDecisionRecord,
        decision: object,
        version: ArtifactVersion,
    ) -> Mapping[str, Any]:
        if (
            not isinstance(decision, StoryboardDecisionRecord)
            or decision.action != "approve"
            or decision.storyboard_reference != storyboard_reference
            or decision.script_reference != script_reference
            or decision.character_reference != character_reference
            or decision.script_approval_decision_id != script_decision.decision_id
        ):
            raise _ContractValidation(
                "STORYBOARD_APPROVAL_REQUIRED",
                "an exact approved Storyboard decision is required",
            )
        cls._validate_identity(decision.decision_id, "INVALID_STORYBOARD_APPROVAL_ID")
        if version.dependencies != (script_reference, character_reference):
            raise _ContractValidation("STORYBOARD_LINEAGE_MISMATCH", "Storyboard dependencies are invalid")
        payload = version.payload
        if (
            not isinstance(payload, Mapping)
            or set(payload) != {"script_reference", "approval_decision_id", "character_reference", "storyboard_constraints", "storyboard"}
            or payload.get("script_reference") != script_reference
            or payload.get("approval_decision_id") != script_decision.decision_id
            or payload.get("character_reference") != character_reference
            or not isinstance(payload.get("storyboard"), Mapping)
        ):
            raise _ContractValidation("STORYBOARD_LINEAGE_MISMATCH", "Storyboard lineage is invalid")
        storyboard = payload["storyboard"]
        if set(storyboard) != {"aspect_ratio", "scenes"} or not isinstance(storyboard.get("scenes"), tuple):
            raise _ContractValidation("INVALID_STORYBOARD_PAYLOAD", "Storyboard payload is invalid")
        if len(storyboard["scenes"]) != _SCENE_COUNT:
            raise _ContractValidation("INVALID_STORYBOARD_SCENES", "Storyboard must contain six ordered Scenes")
        return storyboard

    @classmethod
    def _validate_timeline(
        cls,
        script_reference: ArtifactReference,
        character_reference: ArtifactReference,
        storyboard_reference: ArtifactReference,
        timeline_reference: ArtifactReference,
        script_decision: ScriptDecisionRecord,
        storyboard_decision: StoryboardDecisionRecord,
        version: ArtifactVersion,
        script_version: ArtifactVersion,
        storyboard: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if version.dependencies != (script_reference, character_reference, storyboard_reference):
            raise _ContractValidation("TIMELINE_LINEAGE_MISMATCH", "Timeline dependencies are invalid")
        payload = version.payload
        if (
            not isinstance(payload, Mapping)
            or set(payload) != {"script_reference", "approval_decision_id", "character_reference", "storyboard_reference", "storyboard_decision_id", "timeline"}
            or payload.get("script_reference") != script_reference
            or payload.get("approval_decision_id") != script_decision.decision_id
            or payload.get("character_reference") != character_reference
            or payload.get("storyboard_reference") != storyboard_reference
            or payload.get("storyboard_decision_id") != storyboard_decision.decision_id
            or not isinstance(payload.get("timeline"), Mapping)
        ):
            raise _ContractValidation("TIMELINE_LINEAGE_MISMATCH", "Timeline lineage is invalid")
        timeline = payload["timeline"]
        if set(timeline) != {"duration_seconds", "scenes"} or not isinstance(timeline.get("scenes"), tuple):
            raise _ContractValidation("INVALID_TIMELINE_PAYLOAD", "Timeline payload is invalid")
        if len(timeline["scenes"]) != _SCENE_COUNT:
            raise _ContractValidation("INVALID_TIMELINE_SCENES", "Timeline must contain six ordered Scenes")
        script_scenes = script_version.payload.get("scenes") if isinstance(script_version.payload, Mapping) else None
        storyboard_scenes = storyboard["scenes"]
        for index, (script_scene, storyboard_scene, timeline_scene) in enumerate(zip(script_scenes or (), storyboard_scenes, timeline["scenes"], strict=True), start=1):
            if not all(isinstance(item, Mapping) for item in (script_scene, storyboard_scene, timeline_scene)):
                raise _ContractValidation("INVALID_TIMELINE_SCENES", "Timeline Scenes are invalid")
            expected_scene_id = script_scene.get("scene_id")
            if timeline_scene.get("scene_id") != expected_scene_id or storyboard_scene.get("scene_id") != expected_scene_id:
                raise _ContractValidation("SCENE_ORDER_MISMATCH", f"Scene {index} order does not match exact upstreams")
            cls._milliseconds(timeline_scene.get("duration_seconds"))
        return timeline

    @classmethod
    def _validate_production_request(
        cls,
        script_reference: ArtifactReference,
        character_reference: ArtifactReference,
        storyboard_reference: ArtifactReference,
        timeline_reference: ArtifactReference,
        request_reference: ArtifactReference,
        script_decision: ScriptDecisionRecord,
        storyboard_decision: StoryboardDecisionRecord,
        version: ArtifactVersion,
        script_version: ArtifactVersion,
        storyboard: Mapping[str, Any],
        timeline: Mapping[str, Any],
    ) -> Mapping[str, Any]:
        if version.dependencies != (script_reference, character_reference, storyboard_reference, timeline_reference):
            raise _ContractValidation("PRODUCTION_REQUEST_LINEAGE_MISMATCH", "Production Request dependencies are invalid")
        payload = version.payload
        expected_keys = {"script_reference", "approval_decision_id", "character_reference", "storyboard_reference", "storyboard_decision_id", "timeline_reference", "production_request"}
        if (
            not isinstance(payload, Mapping)
            or set(payload) != expected_keys
            or payload.get("script_reference") != script_reference
            or payload.get("approval_decision_id") != script_decision.decision_id
            or payload.get("character_reference") != character_reference
            or payload.get("storyboard_reference") != storyboard_reference
            or payload.get("storyboard_decision_id") != storyboard_decision.decision_id
            or payload.get("timeline_reference") != timeline_reference
            or not isinstance(payload.get("production_request"), Mapping)
        ):
            raise _ContractValidation("PRODUCTION_REQUEST_LINEAGE_MISMATCH", "Production Request lineage is invalid")
        request = payload["production_request"]
        if set(request) != {"language", "aspect_ratio", "duration_seconds", "scenes"} or not isinstance(request.get("scenes"), tuple):
            raise _ContractValidation("INVALID_PRODUCTION_REQUEST_PAYLOAD", "Production Request payload is invalid")
        if len(request["scenes"]) != _SCENE_COUNT:
            raise _ContractValidation("INVALID_PRODUCTION_REQUEST_SCENES", "Production Request must contain six ordered Scenes")
        for request_scene, timeline_scene in zip(request["scenes"], timeline["scenes"], strict=True):
            if not isinstance(request_scene, Mapping) or request_scene.get("scene_id") != timeline_scene.get("scene_id"):
                raise _ContractValidation("SCENE_ORDER_MISMATCH", "Production Request Scene order is invalid")
            cls._milliseconds(request_scene.get("duration_seconds"))
        return request

    @classmethod
    def _build_entries(
        cls,
        script_version: ArtifactVersion,
        storyboard: Mapping[str, Any],
        timeline: Mapping[str, Any],
        request: Mapping[str, Any],
    ) -> tuple[Mapping[str, Any], ...]:
        script_scenes = script_version.payload["scenes"]
        entries: list[Mapping[str, Any]] = []
        for index, (script_scene, storyboard_scene, timeline_scene, request_scene) in enumerate(
            zip(script_scenes, storyboard["scenes"], timeline["scenes"], request["scenes"], strict=True),
            start=1,
        ):
            scene_id = cls._scene_id(script_scene.get("scene_id"))
            if any(item.get("scene_id") != scene_id for item in (storyboard_scene, timeline_scene, request_scene)):
                raise _ContractValidation("SCENE_ORDER_MISMATCH", "Scene order is invalid")
            narration = cls._text(request_scene.get("narration"), "INVALID_SCENE_NARRATION")
            visual_intent = cls._text(request_scene.get("visual_intent"), "INVALID_SCENE_VISUAL_INTENT")
            character_action = cls._text(request_scene.get("character_action"), "INVALID_SCENE_ACTION")
            continuity = cls._notes(request_scene.get("continuity_notes"), "INVALID_SCENE_CONTINUITY")
            duration_ms = cls._milliseconds(request_scene.get("duration_seconds"))
            continuity_text = "; ".join(continuity)
            prompt = (
                f"{visual_intent} Action: {character_action}. "
                f"Continuity: {continuity_text}. Vertical 9:16 educational scene."
            )
            camera_motion = "Medium vertical framing; gentle camera motion; preserve character continuity."
            negative = ("no text", "no watermark", "no extra characters")
            entries.append(
                {
                    "scene_id": scene_id,
                    "duration_milliseconds": duration_ms,
                    "narration_identity": f"narration:{scene_id}",
                    "narration": narration,
                    "visual_intent": visual_intent,
                    "character_action": character_action,
                    "continuity_notes": continuity,
                    "generation_prompt": prompt,
                    "camera_motion_instruction": camera_motion,
                    "negative_constraints": negative,
                    "expected_filename": f"scene-{index}.mp4",
                }
            )
        if len(entries) != _SCENE_COUNT:
            raise _ContractValidation("INVALID_SCENE_GENERATION_CONTRACT_SCENES", "Contract must contain six ordered Scenes")
        return tuple(entries)

    @classmethod
    def _scene_id(cls, value: object) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_SCENE_ID_LENGTH or cls._has_control(value):
            raise _ContractValidation("INVALID_SCENE_ID", "Scene identity is invalid")
        return value

    @classmethod
    def _text(cls, value: object, code: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > _MAX_TEXT_LENGTH or cls._has_control(value):
            raise _ContractValidation(code, "Scene text is invalid")
        return value

    @classmethod
    def _notes(cls, value: object, code: str) -> tuple[str, ...]:
        if not isinstance(value, tuple) or not value or len(value) > 32:
            raise _ContractValidation(code, "Scene continuity notes are invalid")
        return tuple(cls._text(item, code) for item in value)

    @classmethod
    def _milliseconds(cls, value: object) -> int:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)) or value <= 0:
            raise _ContractValidation("INVALID_SCENE_DURATION", "Scene duration is invalid")
        milliseconds = round(float(value) * 1000)
        if milliseconds <= 0:
            raise _ContractValidation("INVALID_SCENE_DURATION", "Scene duration is invalid")
        return milliseconds

    @staticmethod
    def _has_control(value: str) -> bool:
        return any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)


__all__ = ["SceneGenerationContractFailure", "SceneGenerationContractPlanner"]
