"""Public behavior tests for the Storyboard Creator decision boundary."""

import unittest
from collections.abc import Iterator, Mapping
from dataclasses import fields, replace

from ai_course_factory.artifacts import (
    ArtifactReference,
    ArtifactVersion,
    StoryboardDecisionBoundary,
    StoryboardDecisionRecord,
)


def storyboard_version():
    script_reference = ArtifactReference("script", "script:episode-1", 1)
    character_reference = ArtifactReference("character", "character:potato-v1", 1)
    storyboard_reference = ArtifactReference("storyboard", "storyboard:episode-1", 1)
    version = ArtifactVersion(
        reference=storyboard_reference,
        payload={
            "script_reference": script_reference,
            "approval_decision_id": "script-approval-1",
            "character_reference": character_reference,
            "storyboard_constraints": {"aspect_ratio": "9:16"},
            "storyboard": {"aspect_ratio": "9:16", "scenes": ()},
        },
        provenance=(),
        dependencies=(script_reference, character_reference),
        commit_id="storyboard-commit-1",
    )
    return storyboard_reference, version, script_reference, character_reference


class ExplodingPayload(Mapping):
    def __iter__(self) -> Iterator[str]:
        raise RuntimeError("provider secret detail")

    def __len__(self) -> int:
        return 0

    def __getitem__(self, key: str):
        raise RuntimeError("provider secret detail")


class StoryboardDecisionBoundaryTests(unittest.TestCase):
    def test_enabled_approve_records_and_retrieves_exact_record(self):
        storyboard_reference, storyboard, script_reference, character_reference = (
            storyboard_version()
        )
        boundary = StoryboardDecisionBoundary()

        result = boundary.decide(
            storyboard_reference,
            storyboard,
            review_enabled=True,
            decision_id="decision-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )

        self.assertIsInstance(result, StoryboardDecisionRecord)
        self.assertEqual(result.decision_id, "decision-1")
        self.assertEqual(result.task_id, "task-1")
        self.assertEqual(result.thread_id, "thread-1")
        self.assertEqual(result.creator_id, "creator-1")
        self.assertEqual(result.gate_kind, "storyboard_review")
        self.assertEqual(result.storyboard_reference, storyboard_reference)
        self.assertEqual(result.script_reference, script_reference)
        self.assertEqual(result.character_reference, character_reference)
        self.assertEqual(result.script_approval_decision_id, "script-approval-1")
        self.assertIs(result.review_enabled, True)
        self.assertEqual(result.action, "approve")
        self.assertEqual(result.decision_context, "")
        self.assertIs(boundary.get("decision-1"), result)

    def test_enabled_actions_require_context_and_skip_fails_closed(self):
        storyboard_reference, storyboard, _script_reference, _character_reference = (
            storyboard_version()
        )
        boundary = StoryboardDecisionBoundary()

        for action in ("reject", "revise"):
            result = boundary.decide(
                storyboard_reference,
                storyboard,
                review_enabled=True,
                decision_id=f"{action}-1",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action=action,
                decision_context=f"Creator requested {action}.",
            )
            self.assertIsInstance(result, StoryboardDecisionRecord)
            self.assertEqual(result.action, action)

        skipped = boundary.decide(
            storyboard_reference,
            storyboard,
            review_enabled=True,
            decision_id="enabled-skip",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="skip",
        )
        self.assertEqual(skipped.code, "INVALID_DECISION_ACTION")
        self.assertEqual(boundary.get("enabled-skip").code, "DECISION_NOT_FOUND")

        for action in ("reject", "revise"):
            result = boundary.decide(
                storyboard_reference,
                storyboard,
                review_enabled=True,
                decision_id=f"empty-{action}",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action=action,
            )
            self.assertEqual(result.code, "INVALID_DECISION_CONTEXT")

    def test_disabled_review_requires_explicit_skip_and_preserves_mode(self):
        storyboard_reference, storyboard, _script_reference, _character_reference = (
            storyboard_version()
        )
        boundary = StoryboardDecisionBoundary()

        skipped = boundary.decide(
            storyboard_reference,
            storyboard,
            review_enabled=False,
            decision_id="disabled-skip",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="skip",
            decision_context="",
        )
        self.assertIsInstance(skipped, StoryboardDecisionRecord)
        self.assertIs(skipped.review_enabled, False)
        self.assertEqual(skipped.action, "skip")

        for action in ("approve", "reject", "revise"):
            result = boundary.decide(
                storyboard_reference,
                storyboard,
                review_enabled=False,
                decision_id=f"disabled-{action}",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action=action,
                decision_context="required context" if action != "approve" else "",
            )
            self.assertEqual(result.code, "INVALID_DECISION_ACTION")

        for value in (1, 0, "true", None):
            result = boundary.decide(
                storyboard_reference,
                storyboard,
                review_enabled=value,
                decision_id=f"non-bool-{type(value).__name__}",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="skip",
            )
            self.assertEqual(result.code, "INVALID_REVIEW_ENABLED")

    def test_context_and_identities_are_safe_bounded_and_get_is_exact(self):
        storyboard_reference, storyboard, _script_reference, _character_reference = (
            storyboard_version()
        )
        boundary = StoryboardDecisionBoundary()

        for index, context in enumerate(("\n", "\t", "x" * 4097, None)):
            result = boundary.decide(
                storyboard_reference,
                storyboard,
                review_enabled=True,
                decision_id=f"unsafe-context-{index}",
                task_id="task-1",
                thread_id="thread-1",
                creator_id="creator-1",
                action="approve",
                decision_context=context,
            )
            self.assertEqual(result.code, "INVALID_DECISION_CONTEXT")

        for field_name in ("decision_id", "task_id", "thread_id", "creator_id"):
            values = {
                "decision_id": "identity-1",
                "task_id": "task-1",
                "thread_id": "thread-1",
                "creator_id": "creator-1",
                "action": "approve",
            }
            values[field_name] = "current"
            result = boundary.decide(
                storyboard_reference,
                storyboard,
                review_enabled=True,
                decision_context="",
                **values,
            )
            self.assertEqual(result.code, f"INVALID_{field_name.upper()}")

        self.assertEqual(boundary.get("unknown").code, "DECISION_NOT_FOUND")
        self.assertEqual(boundary.get("latest").code, "INVALID_DECISION_ID")
        self.assertEqual(boundary.get(None).code, "INVALID_DECISION_ID")

    def test_replay_is_idempotent_and_changed_input_keeps_original_record(self):
        storyboard_reference, storyboard, _script_reference, _character_reference = (
            storyboard_version()
        )
        boundary = StoryboardDecisionBoundary()
        first = boundary.decide(
            storyboard_reference,
            storyboard,
            review_enabled=True,
            decision_id="replay-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        replay = boundary.decide(
            storyboard_reference,
            storyboard,
            review_enabled=True,
            decision_id="replay-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertIs(replay, first)

        conflict = boundary.decide(
            storyboard_reference,
            storyboard,
            review_enabled=True,
            decision_id="replay-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="revise",
            decision_context="Use a different beat.",
        )
        self.assertEqual(conflict.code, "DECISION_CONFLICT")
        self.assertIs(boundary.get("replay-1"), first)

        self.assertEqual(
            tuple(field.name for field in fields(StoryboardDecisionRecord)),
            (
                "decision_id",
                "task_id",
                "thread_id",
                "creator_id",
                "gate_kind",
                "storyboard_reference",
                "script_reference",
                "character_reference",
                "script_approval_decision_id",
                "review_enabled",
                "action",
                "decision_context",
            ),
        )
        with self.assertRaises((AttributeError, TypeError)):
            first.action = "revise"

    def test_target_and_lineage_mutations_fail_atomically(self):
        storyboard_reference, storyboard, script_reference, character_reference = (
            storyboard_version()
        )
        boundary = StoryboardDecisionBoundary()

        cases = (
            (
                "wrong target type",
                replace(storyboard_reference, artifact_type="script"),
                storyboard,
                "INVALID_STORYBOARD_REFERENCE",
            ),
            (
                "latest target",
                replace(storyboard_reference, identity="latest"),
                storyboard,
                "INVALID_STORYBOARD_REFERENCE",
            ),
            (
                "current target",
                replace(storyboard_reference, identity="current"),
                storyboard,
                "INVALID_STORYBOARD_REFERENCE",
            ),
            (
                "version mismatch",
                replace(storyboard_reference, version=2),
                storyboard,
                "STORYBOARD_REFERENCE_MISMATCH",
            ),
            (
                "dependency order",
                storyboard_reference,
                replace(storyboard, dependencies=(character_reference, script_reference)),
                "STORYBOARD_LINEAGE_MISMATCH",
            ),
            (
                "script payload mismatch",
                storyboard_reference,
                replace(
                    storyboard,
                    payload={
                        **storyboard.payload,
                        "script_reference": ArtifactReference("script", "other", 1),
                    },
                ),
                "STORYBOARD_LINEAGE_MISMATCH",
            ),
            (
                "character payload mismatch",
                storyboard_reference,
                replace(
                    storyboard,
                    payload={
                        **storyboard.payload,
                        "character_reference": ArtifactReference("character", "other", 1),
                    },
                ),
                "STORYBOARD_LINEAGE_MISMATCH",
            ),
            (
                "missing payload field",
                storyboard_reference,
                replace(
                    storyboard,
                    payload={
                        key: value
                        for key, value in storyboard.payload.items()
                        if key != "storyboard"
                    },
                ),
                "INVALID_STORYBOARD_PAYLOAD",
            ),
            (
                "extra payload field",
                storyboard_reference,
                replace(storyboard, payload={**storyboard.payload, "extra": "forbidden"}),
                "INVALID_STORYBOARD_PAYLOAD",
            ),
            (
                "invalid approval identity",
                storyboard_reference,
                replace(
                    storyboard,
                    payload={**storyboard.payload, "approval_decision_id": "latest"},
                ),
                "INVALID_SCRIPT_APPROVAL_ID",
            ),
        )
        for index, (_label, target, resolved, code) in enumerate(cases):
            with self.subTest(label=_label):
                decision_id = f"mutation-{index}"
                result = boundary.decide(
                    target,
                    resolved,
                    review_enabled=True,
                    decision_id=decision_id,
                    task_id="task-1",
                    thread_id="thread-1",
                    creator_id="creator-1",
                    action="approve",
                )
                self.assertEqual(result.code, code)
                self.assertEqual(boundary.get(decision_id).code, "DECISION_NOT_FOUND")

    def test_unexpected_payload_exception_is_normalized_without_raw_details(self):
        storyboard_reference, storyboard, _script_reference, _character_reference = (
            storyboard_version()
        )
        boundary = StoryboardDecisionBoundary()
        result = boundary.decide(
            storyboard_reference,
            replace(storyboard, payload=ExplodingPayload()),
            review_enabled=True,
            decision_id="unexpected-1",
            task_id="task-1",
            thread_id="thread-1",
            creator_id="creator-1",
            action="approve",
        )
        self.assertEqual(result.kind, "execution")
        self.assertEqual(result.code, "STORYBOARD_DECISION_FAILED")
        self.assertNotIn("provider secret detail", result.message)
        self.assertEqual(boundary.get("unexpected-1").code, "DECISION_NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
