# W1-T001 Artifact Commit Boundary — Issue Specification v0.1

## Issue ID

`pending` — the GitHub target is established, but a real Issue has not been authorized or created; this file is not a GitHub Issue.

## Title

Implement the immutable Artifact Commit Boundary with exact References

## 所属 Wave

W1 — Control Spine

## 所属 Milestone

M1 — Artifact and Workflow Control Spine

## 所属 Task Category

Artifact Commit, consuming the Artifact Reference contract required by the same seam

## Owner

Artifact Layer / Artifact Commit seam

## 负责 Agent

exact `luna-worker`; no fallback

## 状态

`READY_FOR_ISSUE_CREATION — AUTHORIZATION_REQUIRED`

## 背景

Source, Knowledge and Script stages cannot form a trustworthy Artifact chain until the implementation proves validation-before-commit, immutable Version history, exact Reference retrieval and idempotent duplicate Commit behavior.

## 目标

Deliver one observable Artifact Commit boundary in which a validated Candidate becomes an immutable Artifact Version and an exact Reference, while an equivalent repeated logical Commit returns the same exact Reference without producing a duplicate Version.

## 用户价值

This boundary makes the first Creator-visible Source-to-Approved-Script flow resumable and auditable. It prevents a regenerated Script or resumed Workflow from silently selecting or overwriting the wrong business result.

## 技术目标

Provide the minimal core-owned Artifact behavior required by W1-T001 without introducing Workflow, Storage product, Provider or platform infrastructure.

## 依赖

```text
Depends On:
- Phase 1.3 Baseline Acceptance Record v1.0
- W1 Control Spine Wave Entry Record v0.1
- W1-T001 Bounded Task Contract v0.1

Required Contract:
- Artifact First
- Candidate != Artifact
- exact Reference only
- immutable Version
- duplicate Commit idempotency

Consumes:
- Validated Artifact Candidate
- exact upstream References
- logical Commit identity

Produces:
- exact immutable Artifact Reference or bounded failure
- automated contract evidence

Blocks:
- Artifact Storage Adapter integration
- Workflow selected-reference behavior
- Source / Knowledge / Script Commit paths

Can Parallel With:
- Non-overlapping documentation-only work
```

## 前置条件

- G0 baseline approval passed.
- G1 scoped coding authorization passed.
- G2 W1 entry passed.
- Bounded Task Contract readiness passed.
- Repository / GitHub target is established as public `JettxonHo/AI-Course-Factory`.
- Before external Issue creation: Product Owner must explicitly authorize creating the real Issue from this Specification.
- Before assignment: an actual Issue, complete Task Package and exact `luna-worker` route must be valid.

## 输入文档

- Phase 1.3 Baseline Acceptance Record v1.0.
- Technical Spec v0.1 §6.7.3, §9.3–§9.7, §9.13 and §9.15.
- Implementation Boundary Spec v0.1 §2 and §6.
- Implementation Plan v0.1 M1.
- Execution Plan v0.1 W1 and G0–G3.
- Bounded Task Design v0.1 W1 Artifact Reference / Commit categories.
- Issue and Task Package Spec v0.1.
- W1-T001 Bounded Task Contract v0.1.

## 修改范围

Future assigned implementation is limited to the minimal Artifact module and its deterministic tests under the exact file scope set by the Task Package, expected to be within:

- `src/ai_course_factory/artifacts/`
- `tests/artifacts/`

## 非修改范围

- Step 1–12 and governance baselines.
- Workflow, Checkpoint, Command, Source, Agent and Human Review implementation.
- Artifact dependency / stale graph beyond direct exact input References.
- Production, Provider, Skill, UI and Packaging.
- Database, microservice, event bus or external dependency.
- GitHub object, Branch or PR creation without separate authorization.

## 接口约束

- Commit accepts only an explicitly validated Candidate and exact dependency References.
- Commit success returns an exact Artifact ID + Version Reference.
- A revision is explicit and creates a new immutable Version.
- An equivalent repeated logical Commit returns the existing exact Reference.
- No public implicit-latest selection is allowed.
- Commit returns no Workflow transition, Approval or Provider result.

## Artifact / Workflow 影响

- Creates Artifact Versions and exact Artifact References only after successful validation and Commit.
- Preserves all historical Versions.
- Does not update Workflow State, selected refs, lifecycle, gate or checkpoint.
- Does not propagate stale in this task.

## 验收标准

### Functional

- First Commit, exact retrieval, explicit revision, historical retrieval, duplicate Commit and invalid Candidate behavior all pass.

### Contract

- Candidate remains distinct from Artifact.
- Version is immutable and no implicit latest operation exists.
- No Workflow, Approval or external Provider behavior enters the seam.

### Testing

- Deterministic offline automated tests cover success and failure paths.

### Regression

- No upstream document or out-of-scope implementation is changed.

### Documentation

- Worker handoff records file scope, test command, evidence and residual risk.

## 测试要求

The future Task Package must bind exact executable commands to the selected local toolchain. Tests must be offline, deterministic and runnable with the approved Python 3.12 environment or another separately approved runtime.

## 风险

- Mutability leaking through returned payloads.
- Artifact identity confused with Commit identity.
- Storage-specific detail leaking into the core interface.
- Convenience lookup reintroducing implicit latest.
- Scope expanding into Workflow or full Artifact Graph.

## 阻塞条件

- Product Owner has not yet authorized the external GitHub Issue creation action.
- Task Package cannot bind an actual Issue.
- Exact `luna-worker` route fails or reports a model mismatch.
- Implementation needs a changed Artifact Contract, second ownership, major dependency or external side effect.

## 完成定义

The future implementation can enter Integration Review only when code is complete, all specified tests pass, frozen Artifact contracts are verified, handoff documentation is complete and no scope drift occurred. This does not equal PR creation, merge, Wave Exit or Milestone completion.

## Issue Readiness Result

```text
ISSUE SPECIFICATION: COMPLETE
GITHUB ISSUE: NOT CREATED
EXTERNAL ISSUE CREATION: READY_PENDING_AUTHORIZATION
TASK PACKAGE: NOT CREATED
AGENT ASSIGNMENT: NOT STARTED
CODING: NOT STARTED
```
