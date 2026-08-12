"""Public behavior tests for durable task projection coordination."""

import unittest
from dataclasses import fields

from ai_course_factory.application import (
    InMemoryTaskRepository,
    TaskArtifactSelection,
    TaskImpact,
    TaskOperationResult,
    TaskProjectionChange,
    TaskProjectionService,
    TaskRepository,
    TaskRepositoryFailure,
    TaskSnapshot,
)
from ai_course_factory.artifacts import ArtifactCandidate, ArtifactCommitBoundary, ArtifactReference


def _source_store() -> tuple[ArtifactCommitBoundary, ArtifactReference]:
    store = ArtifactCommitBoundary()
    reference = store.commit(ArtifactCandidate(
        artifact_type="source", identity="source:demo", payload={"url": "https://example.test"},
        provenance=("fixture",), dependencies=(), validated=True, commit_id="source-v1",
    ))
    return store, reference


def _committed_lineage() -> tuple[ArtifactCommitBoundary, dict[str, ArtifactReference]]:
    store = ArtifactCommitBoundary()

    def commit(artifact_type: str, identity: str, dependencies: tuple[ArtifactReference, ...] = (), payload=None):
        return store.commit(ArtifactCandidate(
            artifact_type=artifact_type, identity=identity, payload=payload or {"identity": identity},
            provenance=("fixture",), dependencies=dependencies, validated=True, commit_id=f"{identity}-v1",
        ))

    refs: dict[str, ArtifactReference] = {}
    refs["source"] = commit("source", "source:demo", payload={"url": "https://example.test"})
    refs["knowledge"] = commit("knowledge", "knowledge:demo", (refs["source"],))
    refs["course_plan"] = commit(
        "content_plan", "plan:course", (refs["knowledge"],), {"role": "course"}
    )
    refs["episode_plan"] = commit(
        "content_plan", "plan:episode", (refs["knowledge"],), {"role": "episode"}
    )
    refs["script"] = commit(
        "script", "script:demo", (refs["knowledge"], refs["course_plan"], refs["episode_plan"])
    )
    refs["character"] = commit("character", "character:demo", (refs["script"],))
    refs["storyboard"] = commit("storyboard", "storyboard:demo", (refs["character"],))
    refs["timeline"] = commit("timeline", "timeline:demo", (refs["storyboard"],))
    refs["production_request"] = commit(
        "production_request", "request:demo", (refs["timeline"],)
    )
    refs["production_budget"] = commit(
        "production_budget", "budget:demo", (refs["production_request"],)
    )
    return store, refs


class TaskProjectionPublicContractTests(unittest.TestCase):
    def test_public_projection_records_are_frozen_slotted_and_repository_is_runtime_checkable(self):
        self.assertTrue(TaskArtifactSelection.__dataclass_params__.frozen)
        self.assertTrue(TaskSnapshot.__dataclass_params__.frozen)
        self.assertTrue(TaskImpact.__dataclass_params__.frozen)
        self.assertTrue(TaskOperationResult.__dataclass_params__.frozen)
        self.assertEqual(
            tuple(field.name for field in fields(TaskArtifactSelection)),
            ("slot", "reference", "status"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(TaskSnapshot)),
            ("task_id", "revision", "lifecycle_state", "selections", "last_command_id"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(TaskImpact)),
            ("task_id", "slot", "previous_reference", "replacement_reference", "direct", "transitive"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(TaskOperationResult)),
            ("status", "snapshot", "impact", "error_code", "error_message"),
        )
        self.assertEqual(
            tuple(field.name for field in fields(TaskProjectionChange)),
            ("task_id", "command_id", "expected_revision", "snapshot", "impact"),
        )
        self.assertEqual(tuple(field.name for field in fields(TaskRepositoryFailure)), ("code", "message"))
        for record in (TaskArtifactSelection, TaskSnapshot, TaskImpact, TaskOperationResult,
                       TaskProjectionChange, TaskRepositoryFailure):
            self.assertTrue(hasattr(record, "__slots__"))
        self.assertIsInstance(TaskProjectionService, type)
        self.assertIsInstance(InMemoryTaskRepository(), TaskRepository)

    def test_create_select_inspect_and_replay_return_exact_immutable_projection(self):
        store, source = _source_store()
        service = TaskProjectionService(store)

        created = service.create("task-demo", "create-1")
        selected = service.select("task-demo", "select-source", 1, "source", source)
        replay = service.select("task-demo", "select-source", 1, "source", source)
        inspected = service.inspect("task-demo")

        self.assertEqual(created.status, "success")
        self.assertEqual(selected.status, "success")
        self.assertEqual(replay, selected)
        self.assertEqual(inspected.snapshot, selected.snapshot)
        self.assertEqual(selected.snapshot.revision, 2)
        self.assertEqual(selected.snapshot.lifecycle_state, "source_ready")
        self.assertEqual(selected.snapshot.selections, (
            TaskArtifactSelection("source", source, "current"),
        ))
        with self.assertRaises(AttributeError):
            selected.snapshot.revision = 4

    def test_canonical_selection_requires_exact_current_dependencies_and_projects_lifecycle(self):
        store, refs = _committed_lineage()
        service = TaskProjectionService(store)
        self.assertEqual(service.create("task-lineage", "create-lineage").status, "success")

        revision = 1
        for index, slot in enumerate((
            "source", "knowledge", "course_plan", "episode_plan", "script", "character",
            "storyboard", "timeline", "production_request", "production_budget",
        ), start=1):
            result = service.select("task-lineage", f"select-{index}", revision, slot, refs[slot])
            self.assertEqual(result.status, "success", result)
            revision += 1

        current = service.inspect("task-lineage").snapshot
        self.assertEqual(current.revision, 11)
        self.assertEqual(current.lifecycle_state, "budget_review_pending")
        self.assertEqual(tuple(item.slot for item in current.selections), tuple(refs))
        self.assertTrue(all(item.status == "current" for item in current.selections))

        wrong_role = service.select("task-lineage", "wrong-role", current.revision, "course_plan", refs["episode_plan"])
        self.assertEqual(wrong_role.status, "failure")
        self.assertEqual(wrong_role.error_code, "TASK_SLOT_TYPE_MISMATCH")
        self.assertEqual(service.inspect("task-lineage").snapshot.revision, current.revision)

    def test_preview_and_apply_replace_upstream_with_exact_direct_transitive_stale_impact(self):
        store, refs = _committed_lineage()
        service = TaskProjectionService(store)
        service.create("task-impact", "create-impact")
        revision = 1
        for index, slot in enumerate((
            "source", "knowledge", "course_plan", "episode_plan", "script", "character",
            "storyboard", "timeline", "production_request", "production_budget",
        ), start=1):
            self.assertEqual(service.select("task-impact", f"select-impact-{index}", revision, slot, refs[slot]).status, "success")
            revision += 1

        replacement = store.commit(ArtifactCandidate(
            artifact_type="knowledge", identity="knowledge:demo", payload={"identity": "knowledge:demo", "revision": 2},
            provenance=("fixture",), dependencies=(refs["source"],), validated=True,
            commit_id="knowledge:demo-v2", prior_reference=refs["knowledge"],
        ))
        preview = service.preview_selection("task-impact", "knowledge", replacement)
        self.assertEqual(preview.status, "success")
        self.assertEqual(preview.snapshot.revision, revision)
        self.assertEqual(tuple(item.slot for item in preview.impact.direct), ("course_plan", "episode_plan", "script"))
        self.assertEqual(
            tuple(item.slot for item in preview.impact.transitive),
            ("character", "storyboard", "timeline", "production_request", "production_budget"),
        )
        self.assertTrue(all(item.status == "current" for item in preview.impact.direct + preview.impact.transitive))
        self.assertEqual(service.inspect("task-impact").snapshot.revision, revision)

        applied = service.select("task-impact", "replace-knowledge", revision, "knowledge", replacement)
        self.assertEqual(applied.status, "success", applied)
        self.assertEqual(applied.snapshot.lifecycle_state, "knowledge_ready")
        self.assertEqual(applied.impact, TaskImpact(
            "task-impact", "knowledge", refs["knowledge"], replacement,
            tuple(TaskArtifactSelection(slot, refs[slot], "stale") for slot in ("course_plan", "episode_plan", "script")),
            tuple(TaskArtifactSelection(slot, refs[slot], "stale") for slot in (
                "character", "storyboard", "timeline", "production_request", "production_budget",
            )),
        ))
        self.assertEqual(store.get(refs["knowledge"]).reference, refs["knowledge"])

    def test_conflicts_stale_dependencies_and_invalid_revisions_are_atomic(self):
        store, refs = _committed_lineage()
        service = TaskProjectionService(store)
        self.assertEqual(service.create("task-a", "global-command").status, "success")
        conflict = service.create("task-b", "global-command")
        self.assertEqual(conflict.error_code, "TASK_COMMAND_CONFLICT")
        self.assertEqual(service.inspect("task-b").error_code, "TASK_NOT_FOUND")

        service.create("task-stale", "create-stale")
        self.assertEqual(service.select("task-stale", "source-stale", 1, "source", refs["source"]).status, "success")
        self.assertEqual(service.select("task-stale", "knowledge-stale", 2, "knowledge", refs["knowledge"]).status, "success")
        replacement = store.commit(ArtifactCandidate(
            artifact_type="knowledge", identity="knowledge:demo", payload={"revision": 2},
            provenance=("fixture",), dependencies=(refs["source"],), validated=True,
            commit_id="knowledge:demo-v2", prior_reference=refs["knowledge"],
        ))
        self.assertEqual(service.select("task-stale", "replace-stale", 3, "knowledge", replacement).status, "success")
        stale_script = store.commit(ArtifactCandidate(
            artifact_type="script", identity="script:demo", payload={"revision": 2},
            provenance=("fixture",), dependencies=(refs["knowledge"], refs["course_plan"], refs["episode_plan"]),
            validated=True, commit_id="script:demo-v2", prior_reference=refs["script"],
        ))
        rejected = service.select("task-stale", "stale-script", 4, "script", stale_script)
        self.assertEqual(rejected.error_code, "TASK_SELECTION_LINEAGE_MISMATCH")
        self.assertEqual(service.inspect("task-stale").snapshot.revision, 4)

        source_v2 = store.commit(ArtifactCandidate(
            artifact_type="source", identity="source:demo", payload={"revision": 2},
            provenance=("fixture",), dependencies=(), validated=True,
            commit_id="source:demo-v2", prior_reference=refs["source"],
        ))
        stale_revision = service.select("task-stale", "wrong-revision", 2, "source", source_v2)
        self.assertEqual(stale_revision.error_code, "TASK_REVISION_CONFLICT")
        self.assertEqual(service.inspect("task-stale").snapshot.revision, 4)

    def test_repository_and_service_fail_closed_for_forged_success_and_impact(self):
        store, source = _source_store()
        forged_snapshot = TaskSnapshot("task-forged", 1, "created", (), "create-forged")
        wrong_result_snapshot = TaskSnapshot("task-forged", 9, "created", (), "other-command")
        malformed_snapshot = TaskSnapshot("task-forged", 1, "not-a-lifecycle", (), "create-forged")

        class ForgedRepository:
            def save(self, change):
                return TaskOperationResult("success", wrong_result_snapshot, None)

            def get(self, task_id, revision=None):
                return malformed_snapshot

        service = TaskProjectionService(store, ForgedRepository())
        self.assertEqual(service.create("task-forged", "create-forged").error_code, "TASK_REPOSITORY_FAILED")
        self.assertEqual(service.inspect("task-forged").error_code, "TASK_REPOSITORY_FAILED")

        repository = InMemoryTaskRepository()
        replacement = ArtifactReference("source", "source:demo", 3)
        forged_impact = TaskImpact(
            "task-impact-forged", "source", source, replacement, (), ()
        )
        forged_change = TaskProjectionChange(
            "task-impact-forged", "replace-forged", 1,
            TaskSnapshot(
                "task-impact-forged", 2, "source_ready",
                (TaskArtifactSelection("source", replacement, "current"),), "replace-forged",
            ),
            forged_impact,
        )
        failure = repository.save(forged_change)
        self.assertEqual(failure.error_code, "TASK_REPOSITORY_FAILED")

    def test_direct_repository_transition_rejects_wrong_prior_and_disjoint_selection_atomically(self):
        store, source = _source_store()
        repository = InMemoryTaskRepository()
        service = TaskProjectionService(store, repository)
        self.assertEqual(service.create("task-transition", "create-transition").status, "success")
        self.assertEqual(service.select("task-transition", "select-v1", 1, "source", source).status, "success")

        forged_v2 = ArtifactReference("source", "source:demo", 2)
        forged_v3 = ArtifactReference("source", "source:demo", 3)
        wrong_prior_change = TaskProjectionChange(
            "task-transition", "wrong-prior", 2,
            TaskSnapshot(
                "task-transition", 3, "source_ready",
                (TaskArtifactSelection("source", forged_v3, "current"),), "wrong-prior",
            ),
            TaskImpact("task-transition", "source", forged_v2, forged_v3, (), ()),
        )
        self.assertEqual(repository.save(wrong_prior_change).error_code, "TASK_REPOSITORY_FAILED")

        disjoint_change = TaskProjectionChange(
            "task-transition", "disjoint-change", 2,
            TaskSnapshot(
                "task-transition", 3, "knowledge_ready",
                (
                    TaskArtifactSelection("source", forged_v2, "current"),
                    TaskArtifactSelection("knowledge", ArtifactReference("knowledge", "knowledge:foreign", 1), "current"),
                ), "disjoint-change",
            ),
            TaskImpact("task-transition", "source", source, forged_v2, (), ()),
        )
        self.assertEqual(repository.save(disjoint_change).error_code, "TASK_REPOSITORY_FAILED")
        self.assertEqual(service.inspect("task-transition").snapshot.revision, 2)

    def test_lifecycle_regresses_to_replacement_slot_with_unrelated_later_current_selection(self):
        store, refs = _committed_lineage()
        unrelated_request = store.commit(ArtifactCandidate(
            "production_request", "request:unrelated", {"identity": "request:unrelated"},
            ("fixture",), (), True, "request:unrelated-v1",
        ))
        unrelated_budget = store.commit(ArtifactCandidate(
            "production_budget", "budget:unrelated", {"identity": "budget:unrelated"},
            ("fixture",), (unrelated_request,), True, "budget:unrelated-v1",
        ))
        service = TaskProjectionService(store)
        service.create("task-branch", "create-branch")
        revision = 1
        for index, slot in enumerate(("source", "knowledge", "course_plan", "episode_plan", "script"), start=1):
            self.assertEqual(service.select("task-branch", f"branch-{index}", revision, slot, refs[slot]).status, "success")
            revision += 1
        self.assertEqual(service.select("task-branch", "branch-request", revision, "production_request", unrelated_request).status, "success")
        revision += 1
        self.assertEqual(service.select("task-branch", "branch-budget", revision, "production_budget", unrelated_budget).status, "success")
        revision += 1

        replacement = store.commit(ArtifactCandidate(
            "knowledge", "knowledge:demo", {"identity": "knowledge:demo", "revision": 2},
            ("fixture",), (refs["source"],), True, "knowledge:demo-v2", refs["knowledge"],
        ))
        result = service.select("task-branch", "replace-branch-knowledge", revision, "knowledge", replacement)
        self.assertEqual(result.status, "success", result)
        self.assertEqual(result.snapshot.lifecycle_state, "knowledge_ready")
        self.assertEqual(next(item.status for item in result.snapshot.selections if item.slot == "production_budget"), "current")
        self.assertEqual(next(item.status for item in result.snapshot.selections if item.slot == "script"), "stale")

    def test_lifecycle_uses_replacement_slot_when_unrelated_later_slots_remain_current(self):
        store = ArtifactCommitBoundary()

        def commit(artifact_type, identity, dependencies=(), payload=None, commit_id=None, prior_reference=None):
            return store.commit(ArtifactCandidate(
                artifact_type=artifact_type,
                identity=identity,
                payload=payload or {"identity": identity},
                provenance=("fixture",),
                dependencies=dependencies,
                validated=True,
                commit_id=commit_id or f"{identity}-v1",
                prior_reference=prior_reference,
            ))

        source = commit("source", "source:edge", payload={"url": "https://example.test"})
        knowledge = commit("knowledge", "knowledge:edge", (source,))
        character = commit("character", "character:edge")
        storyboard = commit("storyboard", "storyboard:edge")
        timeline = commit("timeline", "timeline:edge", (knowledge,))
        replacement = commit(
            "knowledge", "knowledge:edge", (source,), {"revision": 2},
            "knowledge:edge-v2", knowledge,
        )
        service = TaskProjectionService(store)
        self.assertEqual(service.create("task-edge", "create-edge").status, "success")
        revision = 1
        for index, (slot, reference) in enumerate(
            (("source", source), ("knowledge", knowledge), ("character", character),
             ("storyboard", storyboard), ("timeline", timeline)), start=1
        ):
            self.assertEqual(
                service.select("task-edge", f"edge-{index}", revision, slot, reference).status,
                "success",
            )
            revision += 1

        result = service.select("task-edge", "replace-edge-knowledge", revision, "knowledge", replacement)
        self.assertEqual(result.status, "success", result)
        self.assertEqual(result.snapshot.lifecycle_state, "knowledge_ready")
        self.assertEqual(result.impact.direct, (
            TaskArtifactSelection("timeline", timeline, "stale"),
        ))
        self.assertEqual(
            {item.slot: item.status for item in result.snapshot.selections},
            {"source": "current", "knowledge": "current", "character": "current",
             "storyboard": "current", "timeline": "stale"},
        )

    def test_stale_course_plan_can_be_replaced_with_current_dependency(self):
        store, refs = _committed_lineage()
        repository = InMemoryTaskRepository()
        service = TaskProjectionService(store, repository)
        self.assertEqual(service.create("task-regenerate", "create-regenerate").status, "success")
        revision = 1
        for index, slot in enumerate(("source", "knowledge", "course_plan", "episode_plan", "script"), start=1):
            self.assertEqual(
                service.select("task-regenerate", f"regenerate-{index}", revision, slot, refs[slot]).status,
                "success",
            )
            revision += 1

        knowledge_v2 = store.commit(ArtifactCandidate(
            artifact_type="knowledge", identity="knowledge:demo", payload={"revision": 2},
            provenance=("fixture",), dependencies=(refs["source"],), validated=True,
            commit_id="knowledge:demo-v2", prior_reference=refs["knowledge"],
        ))
        replaced = service.select("task-regenerate", "regenerate-knowledge", revision, "knowledge", knowledge_v2)
        self.assertEqual(replaced.status, "success", replaced)
        revision += 1

        course_v2 = store.commit(ArtifactCandidate(
            artifact_type="content_plan", identity="plan:course", payload={"role": "course", "revision": 2},
            provenance=("fixture",), dependencies=(knowledge_v2,), validated=True,
            commit_id="plan:course-v2", prior_reference=refs["course_plan"],
        ))
        forged = TaskProjectionChange(
            "task-regenerate", "forged-stale-impact", revision,
            TaskSnapshot(
                "task-regenerate", revision + 1, "knowledge_ready",
                tuple(
                    TaskArtifactSelection(item.slot, course_v2, "current")
                    if item.slot == "course_plan" else item
                    for item in replaced.snapshot.selections
                ),
                "forged-stale-impact",
            ),
            TaskImpact(
                "task-regenerate", "course_plan", refs["course_plan"], course_v2,
                (TaskArtifactSelection("episode_plan", refs["episode_plan"], "stale"),), (),
            ),
        )
        self.assertEqual(repository.save(forged).error_code, "TASK_REPOSITORY_FAILED")
        self.assertEqual(service.inspect("task-regenerate").snapshot.revision, revision)

        regenerated = service.select("task-regenerate", "regenerate-course", revision, "course_plan", course_v2)
        self.assertEqual(regenerated.status, "success", regenerated)
        self.assertEqual(regenerated.snapshot.revision, revision + 1)
        self.assertEqual(regenerated.snapshot.lifecycle_state, "knowledge_ready")
        selections = {item.slot: item for item in regenerated.snapshot.selections}
        self.assertEqual(selections["course_plan"], TaskArtifactSelection("course_plan", course_v2, "current"))
        self.assertEqual(selections["episode_plan"].status, "stale")
        self.assertEqual(selections["script"].status, "stale")
        self.assertEqual(regenerated.impact.direct, ())
        self.assertEqual(regenerated.impact.transitive, ())


if __name__ == "__main__":
    unittest.main()
