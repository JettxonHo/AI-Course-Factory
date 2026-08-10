"""Staged, provider-neutral Content Agent boundary."""

from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Any, Mapping

from ai_course_factory.artifacts import ArtifactCandidate, ArtifactReference, ArtifactVersion

from .runtime import (
    ContentModelRuntimeResult,
    ModelRuntimeFailure,
    ModelRuntimePort,
    ModelRuntimeRequest,
)


_MAX_TEXT_LENGTH = 4096
_MAX_PLAN_KEYS = 32
_MAX_PLAN_COLLECTION = 64
_MAX_PLAN_DEPTH = 4
_MAX_SCENES = 6
_MAX_SCENE_ID_LENGTH = 128
_MAX_CLAIM_IDS_PER_SCENE = 32
_MAX_CLAIM_IDS_PER_PLAN = 32
_PURPOSE_PLANNING = "content_planning"
_PURPOSE_SCRIPTING = "content_scripting"
_KNOWLEDGE_BOUNDARY = "knowledge-artifact-only"


@dataclass(frozen=True, slots=True)
class ContentTaskContext:
    """Explicit content constraints for one Course / Episode invocation."""

    audience: str
    series: str
    episode_number: int
    episode_title: str
    language: str
    learning_goal: str

    def as_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "audience": self.audience,
                "series": self.series,
                "episode_number": self.episode_number,
                "episode_title": self.episode_title,
                "language": self.language,
                "learning_goal": self.learning_goal,
            }
        )


@dataclass(frozen=True, slots=True)
class EpisodeTemplateConstraint:
    """Fixed MVP episode constraint, kept outside Workflow state shape."""

    scene_count: int
    target_duration_seconds: int | float
    aspect_ratio: str

    def as_mapping(self) -> Mapping[str, Any]:
        return MappingProxyType(
            {
                "scene_count": self.scene_count,
                "target_duration_seconds": self.target_duration_seconds,
                "aspect_ratio": self.aspect_ratio,
            }
        )


@dataclass(frozen=True, slots=True)
class ContentRevisionContext:
    """Explicit Creator decision and exact prior Script Version for revision."""

    prior_reference: ArtifactReference
    prior_version: ArtifactVersion
    creator_decision_id: str
    instruction: str


@dataclass(frozen=True, slots=True)
class ContentPlanCandidateSet:
    """The two plan Candidates returned by one planning invocation."""

    course: ArtifactCandidate
    episode: ArtifactCandidate


@dataclass(frozen=True, slots=True)
class ContentAgentFailure:
    """Safe validation or execution failure returned by Content Agent."""

    kind: str
    code: str
    message: str


class _ContentValidation(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class _ContentExecution(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ContentAgent:
    """Generate plan and script Candidates without committing or approving them."""

    def __init__(self, runtime: ModelRuntimePort) -> None:
        self._runtime = runtime

    def plan(
        self,
        knowledge_reference: ArtifactReference,
        resolved_knowledge: ArtifactVersion,
        *,
        context: ContentTaskContext | Mapping[str, Any],
        template: EpisodeTemplateConstraint | Mapping[str, Any],
        course_identity: str,
        episode_identity: str,
        course_commit_id: str,
        episode_commit_id: str,
    ) -> ContentPlanCandidateSet | ContentAgentFailure:
        """Return Course / Episode plan Candidates or a normalized failure."""

        try:
            context_values, template_values, claim_ids = self._validate_common_inputs(
                knowledge_reference, resolved_knowledge, context, template
            )
            self._validate_identity(course_identity, "INVALID_COURSE_IDENTITY")
            self._validate_identity(episode_identity, "INVALID_EPISODE_IDENTITY")
            self._validate_identity(course_commit_id, "INVALID_COURSE_COMMIT_ID")
            self._validate_identity(episode_commit_id, "INVALID_EPISODE_COMMIT_ID")
            result = self._invoke_runtime(
                ModelRuntimeRequest(
                    purpose=_PURPOSE_PLANNING,
                    task_context=context_values,
                    knowledge_boundary=_KNOWLEDGE_BOUNDARY,
                    inputs=MappingProxyType(
                        {
                            "knowledge_reference": knowledge_reference,
                            "knowledge_payload": resolved_knowledge.payload,
                        }
                    ),
                    constraints=MappingProxyType(
                        {
                            "content_context": context_values,
                            "template_constraint": template_values,
                        }
                    ),
                )
            )
            content = self._content_payload(result)
            if set(content) != {"course_plan", "episode_plan"}:
                raise _ContentValidation("INVALID_PLAN_RESULT", "content plan result is invalid")
            course_plan = self._validate_plan(content["course_plan"], claim_ids)
            episode_plan = self._validate_plan(content["episode_plan"], claim_ids)
            return ContentPlanCandidateSet(
                course=self._plan_candidate(
                    role="course",
                    plan=course_plan,
                    identity=course_identity,
                    commit_id=course_commit_id,
                    knowledge_reference=knowledge_reference,
                    context=context_values,
                    template=template_values,
                ),
                episode=self._plan_candidate(
                    role="episode",
                    plan=episode_plan,
                    identity=episode_identity,
                    commit_id=episode_commit_id,
                    knowledge_reference=knowledge_reference,
                    context=context_values,
                    template=template_values,
                ),
            )
        except _ContentValidation as exc:
            return ContentAgentFailure("validation", exc.code, exc.message)
        except _ContentExecution as exc:
            return ContentAgentFailure("execution", exc.code, exc.message)
        except Exception:
            return ContentAgentFailure(
                "execution", "CONTENT_AGENT_FAILED", "content agent execution failed"
            )

    def script(
        self,
        knowledge_reference: ArtifactReference,
        resolved_knowledge: ArtifactVersion,
        course_plan_reference: ArtifactReference,
        resolved_course_plan: ArtifactVersion,
        episode_plan_reference: ArtifactReference,
        resolved_episode_plan: ArtifactVersion,
        *,
        context: ContentTaskContext | Mapping[str, Any],
        template: EpisodeTemplateConstraint | Mapping[str, Any],
        script_identity: str,
        script_commit_id: str,
        revision: ContentRevisionContext | None = None,
    ) -> ArtifactCandidate | ContentAgentFailure:
        """Return a grounded Script Candidate or a normalized failure."""

        try:
            context_values, template_values, claim_ids = self._validate_common_inputs(
                knowledge_reference, resolved_knowledge, context, template
            )
            self._validate_plan_version(
                course_plan_reference,
                resolved_course_plan,
                knowledge_reference,
                role="course",
            )
            self._validate_plan_version(
                episode_plan_reference,
                resolved_episode_plan,
                knowledge_reference,
                role="episode",
            )
            self._validate_identity(script_identity, "INVALID_SCRIPT_IDENTITY")
            self._validate_identity(script_commit_id, "INVALID_SCRIPT_COMMIT_ID")
            revision_values = self._validate_revision(revision, script_identity)
            result = self._invoke_runtime(
                ModelRuntimeRequest(
                    purpose=_PURPOSE_SCRIPTING,
                    task_context=context_values,
                    knowledge_boundary=_KNOWLEDGE_BOUNDARY,
                    inputs=MappingProxyType(
                        {
                            "knowledge_reference": knowledge_reference,
                            "knowledge_payload": resolved_knowledge.payload,
                            "course_plan_reference": course_plan_reference,
                            "course_plan_payload": resolved_course_plan.payload,
                            "episode_plan_reference": episode_plan_reference,
                            "episode_plan_payload": resolved_episode_plan.payload,
                        }
                    ),
                    constraints=MappingProxyType(
                        {
                            "content_context": context_values,
                            "template_constraint": template_values,
                            "revision_context": revision_values,
                        }
                    ),
                )
            )
            content = self._content_payload(result)
            if set(content) != {"script"}:
                raise _ContentValidation("INVALID_SCRIPT_RESULT", "content script result is invalid")
            script_payload = self._validate_script(
                content["script"], template_values, claim_ids, context_values["language"]
            )
            provenance = (
                {
                    "purpose": _PURPOSE_SCRIPTING,
                    "knowledge_reference": knowledge_reference,
                    "course_plan_reference": course_plan_reference,
                    "episode_plan_reference": episode_plan_reference,
                },
            )
            if revision is not None:
                provenance = provenance + (
                    {
                        "prior_script_reference": revision.prior_reference,
                        "creator_decision_id": revision.creator_decision_id,
                    },
                )
            return ArtifactCandidate(
                artifact_type="script",
                identity=script_identity,
                payload={
                    "knowledge_reference": knowledge_reference,
                    "course_plan_reference": course_plan_reference,
                    "episode_plan_reference": episode_plan_reference,
                    "language": context_values["language"],
                    "content_context": context_values,
                    "template_constraint": template_values,
                    **script_payload,
                },
                provenance=provenance,
                dependencies=(
                    knowledge_reference,
                    course_plan_reference,
                    episode_plan_reference,
                ),
                validated=True,
                commit_id=script_commit_id,
                prior_reference=revision.prior_reference if revision is not None else None,
            )
        except _ContentValidation as exc:
            return ContentAgentFailure("validation", exc.code, exc.message)
        except _ContentExecution as exc:
            return ContentAgentFailure("execution", exc.code, exc.message)
        except Exception:
            return ContentAgentFailure(
                "execution", "CONTENT_AGENT_FAILED", "content agent execution failed"
            )

    @classmethod
    def _validate_common_inputs(
        cls,
        knowledge_reference: ArtifactReference,
        resolved_knowledge: ArtifactVersion,
        context: ContentTaskContext | Mapping[str, Any],
        template: EpisodeTemplateConstraint | Mapping[str, Any],
    ) -> tuple[Mapping[str, Any], Mapping[str, Any], frozenset[str]]:
        if not cls._valid_reference(knowledge_reference, "knowledge"):
            raise _ContentValidation(
                "INVALID_KNOWLEDGE_REFERENCE", "an exact knowledge Reference is required"
            )
        if not isinstance(resolved_knowledge, ArtifactVersion):
            raise _ContentValidation(
                "INVALID_KNOWLEDGE_PAYLOAD", "a resolved Knowledge Version is required"
            )
        if resolved_knowledge.reference != knowledge_reference:
            raise _ContentValidation(
                "KNOWLEDGE_REFERENCE_MISMATCH", "Knowledge Reference does not match resolved payload"
            )
        if not isinstance(resolved_knowledge.payload, Mapping):
            raise _ContentValidation("INVALID_KNOWLEDGE_PAYLOAD", "resolved Knowledge payload is invalid")
        claim_ids = cls._knowledge_claim_ids(resolved_knowledge.payload)
        context_values = cls._normalize_context(context)
        template_values = cls._normalize_template(template)
        return context_values, template_values, claim_ids

    def _invoke_runtime(self, request: ModelRuntimeRequest) -> ContentModelRuntimeResult:
        runtime_invoke = getattr(self._runtime, "invoke", None)
        if not callable(runtime_invoke):
            raise _ContentValidation("INVALID_RUNTIME", "model runtime is required")
        try:
            result = runtime_invoke(request)
        except Exception:
            raise _ContentExecution(
                "MODEL_RUNTIME_FAILED", "model runtime execution failed"
            ) from None
        if isinstance(result, ModelRuntimeFailure):
            raise _ContentExecution("MODEL_RUNTIME_FAILED", "model runtime execution failed")
        if not isinstance(result, ContentModelRuntimeResult):
            raise _ContentValidation("INVALID_MODEL_RESULT", "model runtime result is invalid")
        return result

    @staticmethod
    def _content_payload(result: ContentModelRuntimeResult) -> Mapping[str, Any]:
        if not isinstance(result.content, Mapping) or not result.content:
            raise _ContentValidation("INVALID_MODEL_RESULT", "model runtime result is invalid")
        return result.content

    @classmethod
    def _plan_candidate(
        cls,
        *,
        role: str,
        plan: Mapping[str, Any],
        identity: str,
        commit_id: str,
        knowledge_reference: ArtifactReference,
        context: Mapping[str, Any],
        template: Mapping[str, Any],
    ) -> ArtifactCandidate:
        return ArtifactCandidate(
            artifact_type="content_plan",
            identity=identity,
            payload={
                "role": role,
                "knowledge_reference": knowledge_reference,
                "content_context": context,
                "template_constraint": template,
                "plan": dict(plan),
            },
            provenance=(
                {"purpose": _PURPOSE_PLANNING, "knowledge_reference": knowledge_reference},
            ),
            dependencies=(knowledge_reference,),
            validated=True,
            commit_id=commit_id,
        )

    @classmethod
    def _validate_plan_version(
        cls,
        reference: ArtifactReference,
        version: ArtifactVersion,
        knowledge_reference: ArtifactReference,
        *,
        role: str,
    ) -> None:
        if not cls._valid_reference(reference, "content_plan"):
            raise _ContentValidation("INVALID_PLAN_REFERENCE", "an exact content plan Reference is required")
        if not isinstance(version, ArtifactVersion):
            raise _ContentValidation("INVALID_PLAN_PAYLOAD", "a resolved content plan Version is required")
        if version.reference != reference:
            raise _ContentValidation("PLAN_REFERENCE_MISMATCH", "plan Reference does not match payload")
        payload = version.payload
        if not isinstance(payload, Mapping) or payload.get("role") != role:
            raise _ContentValidation("INVALID_PLAN_PAYLOAD", "content plan role is invalid")
        if payload.get("knowledge_reference") != knowledge_reference:
            raise _ContentValidation(
                "PLAN_KNOWLEDGE_MISMATCH", "content plan Knowledge dependency is invalid"
            )
        if version.dependencies != (knowledge_reference,):
            raise _ContentValidation(
                "PLAN_LINEAGE_MISMATCH", "content plan dependencies are invalid"
            )

    @classmethod
    def _validate_revision(
        cls, revision: ContentRevisionContext | None, script_identity: str
    ) -> Mapping[str, Any] | None:
        if revision is None:
            return None
        if not cls._valid_reference(revision.prior_reference, "script"):
            raise _ContentValidation(
                "INVALID_PRIOR_SCRIPT_REFERENCE", "an exact prior Script Reference is required"
            )
        if revision.prior_reference.identity != script_identity:
            raise _ContentValidation(
                "SCRIPT_IDENTITY_MISMATCH", "Script revision must reuse its identity"
            )
        if not isinstance(revision.prior_version, ArtifactVersion):
            raise _ContentValidation(
                "INVALID_PRIOR_SCRIPT_VERSION", "a resolved prior Script Version is required"
            )
        if revision.prior_version.reference != revision.prior_reference:
            raise _ContentValidation(
                "PRIOR_SCRIPT_REFERENCE_MISMATCH", "prior Script Reference does not match payload"
            )
        cls._validate_identity(revision.creator_decision_id, "INVALID_CREATOR_DECISION")
        if not isinstance(revision.instruction, str) or not revision.instruction.strip():
            raise _ContentValidation("INVALID_REVISION_INSTRUCTION", "revision instruction is required")
        return MappingProxyType(
            {
                "prior_reference": revision.prior_reference,
                "prior_payload": revision.prior_version.payload,
                "creator_decision_id": revision.creator_decision_id,
                "instruction": revision.instruction,
            }
        )

    @classmethod
    def _validate_script(
        cls,
        value: object,
        template: Mapping[str, Any],
        claim_ids: frozenset[str],
        language: str,
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise _ContentValidation("INVALID_SCRIPT", "script result is invalid")
        required = {"duration_seconds", "aspect_ratio", "scenes"}
        if set(value) != required:
            raise _ContentValidation("INVALID_SCRIPT", "script result is invalid")
        duration = value["duration_seconds"]
        if (
            not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(duration)
            or duration <= 0
        ):
            raise _ContentValidation("INVALID_SCRIPT_DURATION", "script duration is invalid")
        if value["aspect_ratio"] != template["aspect_ratio"]:
            raise _ContentValidation("INVALID_SCRIPT_FORMAT", "script aspect ratio is invalid")
        scenes = value["scenes"]
        if not isinstance(scenes, tuple) or len(scenes) != template["scene_count"]:
            raise _ContentValidation(
                "INVALID_SCENE_TEMPLATE", "script scene count does not match the template"
            )
        normalized_scenes: list[dict[str, Any]] = []
        seen_scene_ids: set[str] = set()
        total_duration = 0.0
        for scene in scenes:
            if not isinstance(scene, Mapping) or set(scene) != {
                "scene_id",
                "duration_seconds",
                "narration",
                "teaching_intent",
                "knowledge_claim_ids",
            }:
                raise _ContentValidation("INVALID_SCENE", "script scene is invalid")
            scene_id = scene["scene_id"]
            scene_duration = scene["duration_seconds"]
            narration = scene["narration"]
            teaching_intent = scene["teaching_intent"]
            scene_claim_ids = scene["knowledge_claim_ids"]
            if (
                not isinstance(scene_id, str)
                or not scene_id.strip()
                or len(scene_id) > _MAX_SCENE_ID_LENGTH
                or scene_id in seen_scene_ids
            ):
                raise _ContentValidation("INVALID_SCENE_ID", "scene identity is invalid")
            if (
                not isinstance(scene_duration, (int, float))
                or isinstance(scene_duration, bool)
                or not math.isfinite(scene_duration)
                or scene_duration <= 0
            ):
                raise _ContentValidation("INVALID_SCENE_DURATION", "scene duration is invalid")
            if not isinstance(narration, str) or not narration.strip() or len(narration) > _MAX_TEXT_LENGTH:
                raise _ContentValidation("INVALID_SCENE_NARRATION", "scene narration is invalid")
            if cls._requires_han(language) and not cls._contains_han(narration):
                raise _ContentValidation(
                    "INVALID_SCRIPT_LANGUAGE", "Simplified Chinese narration must contain Han text"
                )
            if not isinstance(teaching_intent, str) or not teaching_intent.strip() or len(teaching_intent) > _MAX_TEXT_LENGTH:
                raise _ContentValidation("INVALID_SCENE_TEACHING_INTENT", "scene teaching intent is invalid")
            if (
                not isinstance(scene_claim_ids, tuple)
                or not scene_claim_ids
                or len(scene_claim_ids) > _MAX_CLAIM_IDS_PER_SCENE
                or any(
                    not isinstance(claim_id, str)
                    or not claim_id.strip()
                    or claim_id not in claim_ids
                    for claim_id in scene_claim_ids
                )
            ):
                raise _ContentValidation(
                    "UNTRACEABLE_SCENE", "scene claim grounding is invalid"
                )
            seen_scene_ids.add(scene_id)
            total_duration += float(scene_duration)
            normalized_scenes.append(
                {
                    "scene_id": scene_id,
                    "duration_seconds": scene_duration,
                    "narration": narration,
                    "teaching_intent": teaching_intent,
                    "knowledge_claim_ids": scene_claim_ids,
                }
            )
        target = float(template["target_duration_seconds"])
        if abs(float(duration) - target) > max(1.0, target * 0.1):
            raise _ContentValidation("INVALID_SCRIPT_DURATION", "script duration is outside the template constraint")
        if abs(total_duration - float(duration)) > 0.01:
            raise _ContentValidation("INVALID_SCENE_DURATION", "scene durations do not match script duration")
        return {
            "duration_seconds": duration,
            "aspect_ratio": value["aspect_ratio"],
            "scenes": tuple(normalized_scenes),
        }

    @staticmethod
    def _requires_han(language: object) -> bool:
        return isinstance(language, str) and language.strip().casefold() in {
            "simplified chinese",
            "zh-cn",
            "zh-hans",
            "简体中文",
        }

    @staticmethod
    def _contains_han(text: str) -> bool:
        return any("\u3400" <= character <= "\u9fff" for character in text)

    @classmethod
    def _validate_plan(
        cls, value: object, claim_ids: frozenset[str]
    ) -> Mapping[str, Any]:
        if not isinstance(value, Mapping) or not value or len(value) > _MAX_PLAN_KEYS:
            raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
        if any(not isinstance(key, str) or not key.strip() for key in value):
            raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
        for item in value.values():
            cls._validate_plan_value(item)
        plan_claim_ids = value.get("knowledge_claim_ids")
        if (
            not isinstance(plan_claim_ids, tuple)
            or not plan_claim_ids
            or len(plan_claim_ids) > _MAX_CLAIM_IDS_PER_PLAN
            or any(
                not isinstance(claim_id, str)
                or not claim_id.strip()
                or claim_id not in claim_ids
                for claim_id in plan_claim_ids
            )
        ):
            raise _ContentValidation(
                "UNTRACEABLE_PLAN", "content plan Knowledge grounding is invalid"
            )
        return dict(value)

    @classmethod
    def _validate_plan_value(cls, value: object, depth: int = 0) -> None:
        if depth > _MAX_PLAN_DEPTH:
            raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
        if isinstance(value, ArtifactReference):
            if not cls._valid_reference(value, value.artifact_type):
                raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
            return
        if isinstance(value, str):
            if len(value) > _MAX_TEXT_LENGTH:
                raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
            return
        if isinstance(value, (int, float, bool)) or value is None:
            if isinstance(value, float) and not math.isfinite(value):
                raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
            return
        if isinstance(value, Mapping):
            if len(value) > _MAX_PLAN_KEYS or any(
                not isinstance(key, str) or not key.strip() for key in value
            ):
                raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
            for item in value.values():
                cls._validate_plan_value(item, depth + 1)
            return
        if isinstance(value, tuple):
            if len(value) > _MAX_PLAN_COLLECTION:
                raise _ContentValidation("INVALID_PLAN", "content plan is invalid")
            for item in value:
                cls._validate_plan_value(item, depth + 1)
            return
        raise _ContentValidation("INVALID_PLAN", "content plan is invalid")

    @classmethod
    def _knowledge_claim_ids(cls, payload: Mapping[str, Any]) -> frozenset[str]:
        claims = payload.get("claims")
        if not isinstance(claims, tuple) or not claims:
            raise _ContentValidation("INVALID_KNOWLEDGE_PAYLOAD", "Knowledge claims are invalid")
        identifiers: set[str] = set()
        for claim in claims:
            if not isinstance(claim, Mapping):
                raise _ContentValidation("INVALID_KNOWLEDGE_PAYLOAD", "Knowledge claims are invalid")
            claim_id = claim.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id.strip() or claim_id in identifiers:
                raise _ContentValidation("INVALID_KNOWLEDGE_PAYLOAD", "Knowledge claim identities are invalid")
            identifiers.add(claim_id)
        return frozenset(identifiers)

    @classmethod
    def _normalize_context(
        cls, context: ContentTaskContext | Mapping[str, Any]
    ) -> Mapping[str, Any]:
        required = {
            "audience",
            "series",
            "episode_number",
            "episode_title",
            "language",
            "learning_goal",
        }
        if isinstance(context, ContentTaskContext):
            values = context.as_mapping()
        elif isinstance(context, Mapping) and set(context) == required:
            values = MappingProxyType(dict(context))
        else:
            raise _ContentValidation("INVALID_CONTENT_CONTEXT", "explicit content context is required")
        if (
            any(
                not isinstance(values[field], str)
                or not values[field].strip()
                or len(values[field]) > _MAX_TEXT_LENGTH
                for field in required - {"episode_number"}
            )
            or not isinstance(values["episode_number"], int)
            or isinstance(values["episode_number"], bool)
            or values["episode_number"] <= 0
        ):
            raise _ContentValidation("INVALID_CONTENT_CONTEXT", "explicit content context is required")
        return values

    @classmethod
    def _normalize_template(
        cls, template: EpisodeTemplateConstraint | Mapping[str, Any]
    ) -> Mapping[str, Any]:
        required = {"scene_count", "target_duration_seconds", "aspect_ratio"}
        if isinstance(template, EpisodeTemplateConstraint):
            values = template.as_mapping()
        elif isinstance(template, Mapping) and set(template) == required:
            values = MappingProxyType(dict(template))
        else:
            raise _ContentValidation("INVALID_TEMPLATE_CONSTRAINT", "episode template constraint is required")
        duration = values["target_duration_seconds"]
        if (
            values["scene_count"] != _MAX_SCENES
            or not isinstance(duration, (int, float))
            or isinstance(duration, bool)
            or not math.isfinite(duration)
            or duration < 45
            or duration > 90
            or values["aspect_ratio"] != "9:16"
        ):
            raise _ContentValidation("INVALID_TEMPLATE_CONSTRAINT", "MVP template constraint is invalid")
        return values

    @staticmethod
    def _valid_reference(reference: object, artifact_type: str) -> bool:
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
    def _validate_identity(value: object, code: str) -> None:
        if (
            not isinstance(value, str)
            or not value.strip()
            or value.casefold() == "latest"
            or any(ord(char) < 0x20 or ord(char) == 0x7F for char in value)
        ):
            raise _ContentValidation(code, "Artifact identity is invalid")
