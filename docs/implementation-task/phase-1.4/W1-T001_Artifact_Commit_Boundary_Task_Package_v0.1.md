# W1-T001 Artifact Commit Boundary — Task Package v0.1

## Task Package ID

`W1-T001-TP-v0.1`

## Issue

[GitHub Issue #1](https://github.com/JettxonHo/AI-Course-Factory/issues/1)

## Wave

W1 — Control Spine

## Milestone

M1 — Artifact and Workflow Control Spine

## 负责 Agent

`luna-worker`

No fallback is allowed. If the exact route cannot execute, return `BLOCKED_LUNA_WORKER_UNAVAILABLE`.

## 任务目标

Implement the minimal Artifact Commit public boundary in which a validated Candidate becomes an immutable Artifact Version and exact Artifact Reference, explicit revision preserves history, equivalent repeated logical Commit returns the same Reference, and invalid input creates no Version.

## 背景

This is the first executable seam of the Phase 1.4 Vertical Slice. Source, Knowledge, Script and Workflow selected-reference behavior all depend on it. The task intentionally excludes Workflow and Agents so the Artifact ownership can be implemented and verified independently.

## 必须阅读

1. `docs/governance/AI_Course_Factory_MVP_Phase_1.3_Baseline_Acceptance_Record_v1.0.md`
2. `docs/technical-spec/AI_Course_Factory_MVP_Technical_Spec_v0.1.md` — §6.7.3, §9.3–§9.7, §9.13, §9.15
3. `docs/technical-spec/AI_Course_Factory_MVP_Implementation_Boundary_Spec_v0.1.md` — §2, §6
4. `docs/implementation-task/phase-1.4/W1-T001_Artifact_Commit_Boundary_Bounded_Task_Contract_v0.1.md`
5. `docs/implementation-task/phase-1.4/W1-T001_Artifact_Commit_Boundary_Issue_Specification_v0.1.md`
6. GitHub Issue #1

## 当前已有实现

- Repository: public `JettxonHo/AI-Course-Factory`.
- Branch: `agent/w1-t001-artifact-commit`.
- No application code or tests exist.
- Python 3.12.13 is available at `/opt/homebrew/bin/python3.12`.
- No external runtime dependency is approved for this task.
- Existing project files are planning/governance documents and must be preserved.

## TDD Public Seam

Tests must observe only the Artifact Layer's public behavior:

- commit a validated Candidate;
- retrieve a committed Version using its exact Reference;
- commit an explicit revision;
- repeat the same logical Commit;
- reject an invalid Candidate.

Tests must not assert private call order, private storage layout, internal counters or implementation-only helpers.

## 允许修改

- `src/ai_course_factory/__init__.py`
- `src/ai_course_factory/artifacts/__init__.py`
- `src/ai_course_factory/artifacts/model.py`
- `src/ai_course_factory/artifacts/commit.py`
- `tests/__init__.py`
- `tests/artifacts/__init__.py`
- `tests/artifacts/test_commit_boundary.py`
- this Task Record only for evidence/status handoff if requested by ORCHESTRATOR_REVIEWER

Minimal package-marker files may be omitted when Python namespace packages work cleanly. Do not create other files without escalation.

## 禁止修改

- Step 1–12 documents, Decision Log, Acceptance Record or other Task Contracts.
- Workflow, Checkpoint, Command, Source, Agent or Review modules.
- GitHub Issue scope, branch policy, Provider, database, API or deployment.
- Any external dependency, SDK or network call.
- Any public implicit-latest operation.
- Any existing committed Artifact mutation or deletion behavior.

## 输入 Contract

The public Commit boundary receives a Candidate with:

- declared Artifact type;
- stable logical Artifact identity;
- immutable payload input;
- provenance associations;
- exact upstream dependency References;
- explicit validation state;
- logical Commit identity;
- optional explicit prior exact Reference for a revision.

Incomplete, unvalidated or revision-mismatched input must fail closed.

## 输出 Contract

The public boundary returns exactly one normalized outcome:

- a new exact Artifact Reference;
- the existing exact Artifact Reference for an equivalent repeated logical Commit; or
- a bounded validation / conflict / not-found failure with no new Version.

It returns no Workflow transition, Human Approval, implicit latest or Provider result.

## 依赖

```text
Depends On:
- Phase 1.3 Accepted Baseline
- W1 Entry
- GitHub Issue #1

Consumes:
- Validated Artifact Candidate
- exact dependency References
- logical Commit identity

Produces:
- immutable Artifact Version
- exact Artifact Reference
- deterministic test evidence

Blocks:
- Workflow selected-reference implementation
- Source / Knowledge / Script Artifact commits

Can Parallel With:
- nothing that changes Artifact identity or Commit interface
```

## 执行步骤

Use strict red → green cycles:

1. Add one failing behavior test for first Commit and exact retrieval; run it and capture the expected failure.
2. Implement only enough public behavior to pass.
3. Add one failing revision/history test; implement only enough to pass.
4. Add one failing duplicate logical Commit test; implement only enough to pass.
5. Add one failing invalid Candidate / revision mismatch test; implement only enough to pass.
6. Run the complete suite.
7. Inspect the diff for scope, mutability, implicit latest and dependency leakage.

Do not batch all tests before implementation.

## 验收标准

All fourteen Acceptance Criteria in the Bounded Task Contract §12 must pass. In particular:

- first Commit returns Version 1 exact Reference;
- exact retrieval succeeds;
- explicit revision returns the next Version and preserves Version 1;
- equivalent repeated logical Commit returns the original exact Reference without a new Version;
- invalid / unvalidated / revision-mismatched Candidate creates no Version;
- Candidate and committed Artifact are observably distinct;
- committed payload, provenance and dependencies are immutable from caller mutation;
- there is no public implicit-latest operation;
- no Workflow or external side effect exists.

## 测试命令

```text
PYTHONPATH=src /opt/homebrew/bin/python3.12 -m unittest discover -s tests -p 'test_*.py' -v
```

The worker must report red evidence for each cycle and final green output.

## 风险

- Python containers may remain transitively mutable if only the outer object is frozen.
- Commit identity may be confused with Artifact identity or content equality.
- Revision may accidentally select latest rather than require an exact prior Reference.
- Convenience retrieval may expose implicit latest.
- Error classes may reveal storage implementation instead of bounded domain semantics.

## 停止条件

Stop and return `SPECIFICATION_REVIEW_REQUIRED` if implementation needs:

- a changed frozen Artifact Contract;
- Workflow or Storage Adapter ownership;
- a third-party package;
- files outside the allowed list;
- network, database or Provider access;
- implicit latest or mutation of committed history.

## 需要升级事项

Only ORCHESTRATOR_REVIEWER may decide a Contract or file-scope change. Product Owner approval is required for architecture or product-scope changes.

## 交付格式

Return:

1. Status: `READY_FOR_INTEGRATION_REVIEW`, `BLOCKED_WITH_EVIDENCE` or `SPECIFICATION_REVIEW_REQUIRED`.
2. Files changed.
3. Public behavior implemented.
4. Red → green evidence.
5. Final test command and output summary.
6. Contract/security/scope evidence.
7. Remaining risks or assumptions.

