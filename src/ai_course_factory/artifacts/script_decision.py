"""Deterministic Script Gate assessment and Creator decision seam."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from .model import ArtifactReference, ArtifactVersion


@dataclass(frozen=True, slots=True)
class ScriptGateFinding:
    """One deterministic Hard Block finding for the selected Script Version."""

    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ScriptGateAssessment:
    """Deterministic Pass or Hard Block assessment for exact input Versions."""

    script_reference: ArtifactReference
    knowledge_reference: ArtifactReference
    course_plan_reference: ArtifactReference
    episode_plan_reference: ArtifactReference
    disposition: str
    findings: tuple[ScriptGateFinding, ...]


@dataclass(frozen=True, slots=True)
class ScriptDecisionFailure:
    """Safe validation or execution failure for the decision seam."""

    kind: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ScriptDecisionRecord:
    """Immutable Creator decision bound to one exact Script assessment."""

    decision_id: str
    task_id: str
    thread_id: str
    creator_id: str
    gate_kind: str
    script_reference: ArtifactReference
    knowledge_reference: ArtifactReference
    course_plan_reference: ArtifactReference
    episode_plan_reference: ArtifactReference
    assessment_disposition: str
    finding_codes: tuple[str, ...]
    action: str


class _DecisionValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ScriptDecisionBoundary:
    """Assess exact Script lineage without Reviewer, Workflow or Commit calls."""

    def __init__(self) -> None:
        self._records: dict[str, ScriptDecisionRecord] = {}
        self._assessments: dict[int, ScriptGateAssessment] = {}

    def assess(
        self,
        script_reference: ArtifactReference,
        resolved_script: ArtifactVersion,
        knowledge_reference: ArtifactReference,
        resolved_knowledge: ArtifactVersion,
        course_plan_reference: ArtifactReference,
        resolved_course_plan: ArtifactVersion,
        episode_plan_reference: ArtifactReference,
        resolved_episode_plan: ArtifactVersion,
    ) -> ScriptGateAssessment | ScriptDecisionFailure:
        try:
            self._validate_reference(script_reference, "script")
            self._validate_reference(knowledge_reference, "knowledge")
            self._validate_reference(course_plan_reference, "content_plan")
            self._validate_reference(episode_plan_reference, "content_plan")
            self._validate_version(script_reference, resolved_script, "SCRIPT")
            self._validate_version(knowledge_reference, resolved_knowledge, "KNOWLEDGE")
            self._validate_version(course_plan_reference, resolved_course_plan, "COURSE_PLAN")
            self._validate_version(episode_plan_reference, resolved_episode_plan, "EPISODE_PLAN")
            findings = self._findings(
                resolved_script,
                knowledge_reference,
                resolved_knowledge,
                course_plan_reference,
                resolved_course_plan,
                episode_plan_reference,
                resolved_episode_plan,
            )
            assessment = ScriptGateAssessment(
                script_reference=script_reference,
                knowledge_reference=knowledge_reference,
                course_plan_reference=course_plan_reference,
                episode_plan_reference=episode_plan_reference,
                disposition="hard_block" if findings else "pass",
                findings=tuple(findings),
            )
            self._assessments[id(assessment)] = assessment
            return assessment
        except _DecisionValidation as exc:
            return ScriptDecisionFailure("validation", exc.code, exc.message)
        except Exception:
            return ScriptDecisionFailure(
                "execution", "SCRIPT_DECISION_FAILED", "script decision assessment failed"
            )

    def decide(
        self,
        assessment: ScriptGateAssessment,
        *,
        decision_id: str,
        task_id: str,
        thread_id: str,
        creator_id: str,
        action: str,
    ) -> ScriptDecisionRecord | ScriptDecisionFailure:
        try:
            if self._assessments.get(id(assessment)) is not assessment:
                raise _DecisionValidation(
                    "ASSESSMENT_NOT_ISSUED",
                    "decision must use an assessment issued by this boundary",
                )
            self._validate_assessment(assessment)
            self._validate_identity(decision_id, "INVALID_DECISION_ID", "decision identity is required")
            self._validate_identity(task_id, "INVALID_TASK_ID", "task identity is required")
            self._validate_identity(thread_id, "INVALID_THREAD_ID", "thread identity is required")
            self._validate_identity(creator_id, "INVALID_CREATOR_ID", "Creator identity is required")
            if action not in {"approve", "reject", "revise"}:
                raise _DecisionValidation("INVALID_DECISION_ACTION", "decision action is invalid")
            if assessment.disposition == "hard_block" and action == "approve":
                raise _DecisionValidation(
                    "HARD_BLOCK_APPROVAL_FORBIDDEN",
                    "Hard Block Script cannot be approved",
                )
            record = ScriptDecisionRecord(
                decision_id=decision_id,
                task_id=task_id,
                thread_id=thread_id,
                creator_id=creator_id,
                gate_kind="script_review",
                script_reference=assessment.script_reference,
                knowledge_reference=assessment.knowledge_reference,
                course_plan_reference=assessment.course_plan_reference,
                episode_plan_reference=assessment.episode_plan_reference,
                assessment_disposition=assessment.disposition,
                finding_codes=tuple(finding.code for finding in assessment.findings),
                action=action,
            )
            existing = self._records.get(decision_id)
            if existing is not None:
                if existing == record:
                    return existing
                raise _DecisionValidation(
                    "DECISION_CONFLICT",
                    "decision identity was already used with different input",
                )
            self._records[decision_id] = record
            return record
        except _DecisionValidation as exc:
            return ScriptDecisionFailure("validation", exc.code, exc.message)
        except Exception:
            return ScriptDecisionFailure(
                "execution", "SCRIPT_DECISION_FAILED", "script decision could not be recorded"
            )

    def get(self, decision_id: str) -> ScriptDecisionRecord | ScriptDecisionFailure:
        """Retrieve one decision by its exact decision identity."""

        if not isinstance(decision_id, str) or not decision_id.strip():
            return ScriptDecisionFailure("validation", "INVALID_DECISION_ID", "decision identity is required")
        try:
            return self._records[decision_id]
        except KeyError:
            return ScriptDecisionFailure("validation", "DECISION_NOT_FOUND", "decision record does not exist")

    @staticmethod
    def _validate_reference(reference: object, artifact_type: str) -> None:
        if (
            not isinstance(reference, ArtifactReference)
            or reference.artifact_type != artifact_type
            or not isinstance(reference.identity, str)
            or not reference.identity.strip()
            or reference.identity.strip().casefold() == "latest"
            or not isinstance(reference.version, int)
            or isinstance(reference.version, bool)
            or reference.version <= 0
        ):
            raise _DecisionValidation(
                f"INVALID_{artifact_type.upper()}_REFERENCE",
                f"an exact {artifact_type} Reference is required",
            )

    @classmethod
    def _validate_assessment(cls, assessment: object) -> None:
        if not isinstance(assessment, ScriptGateAssessment):
            raise _DecisionValidation("INVALID_ASSESSMENT", "Script Gate assessment is required")
        cls._validate_reference(assessment.script_reference, "script")
        cls._validate_reference(assessment.knowledge_reference, "knowledge")
        cls._validate_reference(assessment.course_plan_reference, "content_plan")
        cls._validate_reference(assessment.episode_plan_reference, "content_plan")
        if assessment.disposition not in {"pass", "hard_block"}:
            raise _DecisionValidation("INVALID_ASSESSMENT", "Script Gate assessment disposition is invalid")
        if not isinstance(assessment.findings, tuple) or any(
            not isinstance(finding, ScriptGateFinding)
            or not isinstance(finding.code, str)
            or not finding.code.strip()
            for finding in assessment.findings
        ):
            raise _DecisionValidation("INVALID_ASSESSMENT", "Script Gate assessment findings are invalid")
        if assessment.disposition == "pass" and assessment.findings:
            raise _DecisionValidation("INVALID_ASSESSMENT", "Pass assessment cannot contain findings")
        if assessment.disposition == "hard_block" and not assessment.findings:
            raise _DecisionValidation("INVALID_ASSESSMENT", "Hard Block assessment requires findings")

    @staticmethod
    def _validate_identity(value: object, code: str, message: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.strip().casefold() == "latest"
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        ):
            raise _DecisionValidation(code, message)

    @staticmethod
    def _validate_version(
        reference: ArtifactReference, version: object, label: str
    ) -> None:
        if not isinstance(version, ArtifactVersion):
            raise _DecisionValidation(
                f"INVALID_{label}_VERSION", f"a resolved {label.title()} Version is required"
            )
        if version.reference != reference:
            raise _DecisionValidation(
                f"{label}_REFERENCE_MISMATCH", f"{label.title()} Reference does not match Version"
            )

    @classmethod
    def _findings(
        cls,
        script_version: ArtifactVersion,
        knowledge_reference: ArtifactReference,
        knowledge_version: ArtifactVersion,
        course_plan_reference: ArtifactReference,
        course_plan_version: ArtifactVersion,
        episode_plan_reference: ArtifactReference,
        episode_plan_version: ArtifactVersion,
    ) -> list[ScriptGateFinding]:
        findings: list[ScriptGateFinding] = []
        expected_dependencies = (
            knowledge_reference,
            course_plan_reference,
            episode_plan_reference,
        )
        if script_version.dependencies != expected_dependencies:
            cls._add(
                findings,
                "SCRIPT_LINEAGE_MISMATCH",
                "Script dependencies must be Knowledge, Course Plan and Episode Plan in order",
            )

        script_payload = script_version.payload
        if not isinstance(script_payload, Mapping):
            cls._add(findings, "INVALID_SCRIPT_PAYLOAD", "Script payload is invalid")
            return findings
        if script_payload.get("knowledge_reference") != knowledge_reference:
            cls._add(findings, "SCRIPT_LINEAGE_MISMATCH", "Script Knowledge Reference does not match")
        if script_payload.get("course_plan_reference") != course_plan_reference:
            cls._add(findings, "SCRIPT_LINEAGE_MISMATCH", "Script Course Plan Reference does not match")
        if script_payload.get("episode_plan_reference") != episode_plan_reference:
            cls._add(findings, "SCRIPT_LINEAGE_MISMATCH", "Script Episode Plan Reference does not match")

        cls._plan_findings(
            findings,
            course_plan_version,
            course_plan_reference,
            knowledge_reference,
            "course",
        )
        cls._plan_findings(
            findings,
            episode_plan_version,
            episode_plan_reference,
            knowledge_reference,
            "episode",
        )
        claim_ids = cls._knowledge_claim_ids(knowledge_version.payload, findings)
        cls._script_findings(findings, script_payload, claim_ids)
        return findings

    @classmethod
    def _plan_findings(
        cls,
        findings: list[ScriptGateFinding],
        version: ArtifactVersion,
        reference: ArtifactReference,
        knowledge_reference: ArtifactReference,
        expected_role: str,
    ) -> None:
        payload = version.payload
        if not isinstance(payload, Mapping):
            cls._add(findings, "INVALID_PLAN_PAYLOAD", f"{expected_role.title()} Plan payload is invalid")
            return
        if payload.get("role") != expected_role:
            cls._add(findings, "PLAN_ROLE_MISMATCH", f"{expected_role.title()} Plan role is invalid")
        if payload.get("knowledge_reference") != knowledge_reference:
            cls._add(
                findings,
                "PLAN_KNOWLEDGE_MISMATCH",
                f"{expected_role.title()} Plan Knowledge Reference does not match",
            )
        if version.reference != reference or version.dependencies != (knowledge_reference,):
            cls._add(
                findings,
                "PLAN_LINEAGE_MISMATCH",
                f"{expected_role.title()} Plan lineage is invalid",
            )

    @classmethod
    def _knowledge_claim_ids(
        cls, payload: object, findings: list[ScriptGateFinding]
    ) -> set[str]:
        if not isinstance(payload, Mapping) or not isinstance(payload.get("claims"), tuple):
            cls._add(findings, "INVALID_KNOWLEDGE_PAYLOAD", "Knowledge claims are invalid")
            return set()
        identifiers: set[str] = set()
        for claim in payload["claims"]:
            if not isinstance(claim, Mapping):
                cls._add(findings, "INVALID_KNOWLEDGE_PAYLOAD", "Knowledge claims are invalid")
                continue
            claim_id = claim.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id.strip() or claim_id in identifiers:
                cls._add(findings, "INVALID_KNOWLEDGE_PAYLOAD", "Knowledge claim identities are invalid")
                continue
            identifiers.add(claim_id)
        if not identifiers:
            cls._add(findings, "INVALID_KNOWLEDGE_PAYLOAD", "Knowledge claims are invalid")
        return identifiers

    @classmethod
    def _script_findings(
        cls,
        findings: list[ScriptGateFinding],
        payload: Mapping[str, object],
        claim_ids: set[str],
    ) -> None:
        template = payload.get("template_constraint")
        if not isinstance(template, Mapping):
            cls._add(findings, "INVALID_TEMPLATE_CONSTRAINT", "Script template constraint is invalid")
            template = {}
        if template.get("scene_count") != 6:
            cls._add(findings, "INVALID_SCENE_TEMPLATE", "Script must use the fixed six-scene template")
        if template.get("aspect_ratio") != "9:16":
            cls._add(findings, "INVALID_SCRIPT_FORMAT", "Script aspect ratio must be 9:16")
        target_duration = template.get("target_duration_seconds")
        if not cls._about_sixty_seconds(target_duration):
            cls._add(findings, "INVALID_SCRIPT_DURATION", "Script target duration must be about 60 seconds")

        if payload.get("aspect_ratio") != "9:16" or payload.get("aspect_ratio") != template.get("aspect_ratio"):
            cls._add(findings, "INVALID_SCRIPT_FORMAT", "Script aspect ratio is invalid")
        duration = payload.get("duration_seconds")
        if not cls._about_sixty_seconds(duration):
            cls._add(findings, "INVALID_SCRIPT_DURATION", "Script duration must be about 60 seconds")
        language = payload.get("language")
        if not cls._simplified_chinese(language):
            cls._add(findings, "INVALID_SCRIPT_LANGUAGE", "Script language must be Simplified Chinese")

        scenes = payload.get("scenes")
        if not isinstance(scenes, tuple) or len(scenes) != 6:
            cls._add(findings, "INVALID_SCENE_TEMPLATE", "Script must contain exactly six scenes")
            return

        seen_scene_ids: set[str] = set()
        total_duration = 0.0
        total_is_valid = True
        for scene in scenes:
            if not isinstance(scene, Mapping):
                cls._add(findings, "INVALID_SCENE", "Script scene is invalid")
                total_is_valid = False
                continue
            required = {"scene_id", "duration_seconds", "narration", "teaching_intent", "knowledge_claim_ids"}
            if not required <= set(scene):
                cls._add(findings, "INVALID_SCENE", "Script scene is incomplete")
                total_is_valid = False
                continue
            scene_id = scene.get("scene_id")
            if not isinstance(scene_id, str) or not scene_id.strip() or scene_id in seen_scene_ids:
                cls._add(findings, "INVALID_SCENE_ID", "Scene identity is invalid")
            else:
                seen_scene_ids.add(scene_id)
            scene_duration = scene.get("duration_seconds")
            if (
                not isinstance(scene_duration, (int, float))
                or isinstance(scene_duration, bool)
                or not math.isfinite(scene_duration)
                or scene_duration <= 0
            ):
                cls._add(findings, "INVALID_SCENE_DURATION", "Scene duration is invalid")
                total_is_valid = False
            else:
                total_duration += float(scene_duration)
            narration = scene.get("narration")
            if not isinstance(narration, str) or not narration.strip():
                cls._add(findings, "INVALID_SCENE_NARRATION", "Scene narration is required")
            elif cls._simplified_chinese(language) and not cls._contains_han(narration):
                cls._add(findings, "INVALID_SCRIPT_LANGUAGE", "Simplified Chinese narration must contain Han text")
            teaching_intent = scene.get("teaching_intent")
            if not isinstance(teaching_intent, str) or not teaching_intent.strip():
                cls._add(findings, "INVALID_SCENE_TEACHING_INTENT", "Scene teaching intent is required")
            scene_claim_ids = scene.get("knowledge_claim_ids")
            if (
                not isinstance(scene_claim_ids, tuple)
                or not scene_claim_ids
                or any(not isinstance(claim_id, str) or claim_id not in claim_ids for claim_id in scene_claim_ids)
            ):
                cls._add(findings, "UNTRACEABLE_SCENE", "Scene claims must be grounded in Knowledge")
        if total_is_valid and isinstance(duration, (int, float)) and not isinstance(duration, bool):
            if not math.isfinite(duration) or abs(total_duration - float(duration)) > 0.01:
                cls._add(findings, "INVALID_SCENE_DURATION", "Scene durations must match Script duration")

    @staticmethod
    def _add(findings: list[ScriptGateFinding], code: str, message: str) -> None:
        if not any(finding.code == code for finding in findings):
            findings.append(ScriptGateFinding(code, message))

    @staticmethod
    def _about_sixty_seconds(value: object) -> bool:
        return (
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            and value > 0
            and abs(float(value) - 60.0) <= 6.0
        )

    @staticmethod
    def _simplified_chinese(value: object) -> bool:
        return isinstance(value, str) and value.strip().casefold() in {
            "simplified chinese",
            "zh-cn",
            "zh-hans",
            "简体中文",
        }

    @staticmethod
    def _contains_han(value: str) -> bool:
        return any("\u3400" <= character <= "\u9fff" for character in value)
