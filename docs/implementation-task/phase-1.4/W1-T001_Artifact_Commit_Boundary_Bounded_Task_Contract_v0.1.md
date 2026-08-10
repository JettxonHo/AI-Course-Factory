# W1-T001 Artifact Commit Boundary — Bounded Task Contract v0.1

## 1. Contract Status

| Field | Value |
| --- | --- |
| Task ID | `W1-T001` |
| Wave | W1 — Control Spine |
| Milestone | M1 — Artifact and Workflow Control Spine |
| Ownership | Artifact Layer / Artifact Commit seam |
| Logical Module | Artifact Layer |
| Responsible Role | `luna-worker` after Assignment Readiness |
| Agent Route | exact `luna-worker`; no fallback |
| Status | Ready for ORCHESTRATOR_REVIEWER readiness review |
| Coding | Not Started |

## 2. Baseline References

- `docs/governance/AI_Course_Factory_MVP_Phase_1.3_Baseline_Acceptance_Record_v1.0.md`
- Technical Spec v0.1: §6.7.3 Artifact Commit Semantics; §9.3–§9.7 Artifact identity, versioning, dependency, status and Candidate / Reference model; §9.13 Idempotency Model; §9.15 Invariants.
- Implementation Boundary Spec v0.1: §2 Dependency Rules; §6 Storage Boundary Decision.
- Implementation Plan v0.1: M1 Artifact and Workflow Control Spine.
- Execution Plan v0.1: W1 Control Spine and G0–G3.
- Bounded Task Design v0.1: W1 Artifact Reference / Artifact Commit categories and Task Contract validity gate.
- Issue and Task Package Spec v0.1: Single Ownership and Single Verification Target.

No reference means “latest”; the Phase 1.3 Acceptance Record binds the exact accepted fingerprints.

## 3. Task Objective

Implement one observable Artifact Commit boundary that accepts a validated Artifact Candidate, creates an immutable Artifact Version, returns an exact Artifact Reference, preserves historical Versions, and returns the same business result for an equivalent repeated logical Commit.

## 4. Background

Every later stage depends on exact Artifact References. Source, Knowledge and Script cannot safely form a business chain until the system proves that Candidate is not yet an Artifact, Commit never silently overwrites a Version, and repeated execution does not create duplicate business results.

## 5. Current Preconditions

| Precondition | State |
| --- | --- |
| Phase 1.3 baseline accepted | Passed |
| Scoped Coding Authorization | Passed |
| W1 Entry | Passed |
| Existing implementation | None; current workspace contains documentation only |
| Python runtime | `/opt/homebrew/bin/python3.12` available |
| Git / GitHub execution target | Established: `JettxonHo/AI-Course-Factory` |
| GitHub Issue | Not created |
| Task Package | Not created; Step 10 requires an existing Issue |
| luna-worker route | `RUNTIME_ROUTE_VERIFIED_READ_ONLY`; implementation assignment not performed |

The Contract is approved. Assignment and Coding cannot begin until a real Issue is authorized and created, then an Issue-bound Task Package is assembled and approved.

## 6. Allowed Changes

When assigned, the task may create only the minimal implementation and tests for this Artifact seam under an explicit package scope equivalent to:

- `src/ai_course_factory/artifacts/`
- `tests/artifacts/`

It may define private implementation details necessary for:

- Artifact Candidate representation;
- Artifact identity and exact Version reference;
- validation-before-commit guard;
- immutable commit and exact retrieval;
- logical duplicate-commit recognition;
- explicit revision creating a new Version;
- deterministic in-memory test behavior.

No external package is authorized by this Contract. Standard-library-only implementation is preferred for this first seam.

## 7. Forbidden Changes

- Do not modify Step 1–12, the Acceptance Record or this Contract.
- Do not implement Workflow, Checkpoint, Command, Human Gate, Source Connector, Agent or Review behavior.
- Do not introduce LangGraph, Provider SDK, database, ORM, web framework, event bus or service runtime.
- Do not add Agent, Skill, Provider, Renderer, Source or product capability.
- Do not expose implicit latest lookup.
- Do not let a Candidate become a business fact before successful Commit.
- Do not mutate or delete a committed Artifact Version.
- Do not use UI state, model conversation or provider response as Artifact truth.
- Do not create GitHub objects, Branches, PRs or external side effects without separate authorization.

## 8. Input Contract

The Commit boundary receives:

- one Artifact Candidate produced outside the Artifact Layer;
- a declared Artifact type and stable logical identity;
- provenance and exact upstream dependency References applicable to that Candidate;
- evidence that Candidate validation passed;
- one logical Commit identity suitable for repeat detection;
- optional explicit prior exact Reference when creating a revision.

The boundary must reject incomplete, unvalidated or internally inconsistent input. It must not select an implicit current Version.

## 9. Output Contract

On success, the boundary returns an exact Artifact Reference containing stable Artifact identity and exact Version semantics.

Observable outcomes are limited to:

- new immutable Version committed and exact Reference returned;
- equivalent logical Commit already exists and the existing exact Reference is returned;
- validation / conflict / persistence failure returned with no new exact Reference bound.

The boundary does not return a Workflow transition, Human Approval or Provider result.

## 10. Dependencies

```text
Depends On:
- Phase 1.3 Baseline Acceptance Record v1.0
- W1 Entry Record v0.1

Required Contract:
- Artifact First
- Candidate != Artifact
- exact Artifact ID + Version Reference
- Version immutable
- duplicate logical Commit returns the same business result

Consumes:
- Validated Artifact Candidate
- logical Commit identity
- exact upstream References

Produces:
- exact immutable Artifact Reference or bounded Commit failure
- executable contract evidence

Blocks:
- Artifact Storage Adapter integration
- Workflow selected-reference behavior
- Source / Knowledge / Script Artifact commits

Can Parallel With:
- Documentation-only work that does not modify the same Contract or files
```

No implementation task may concurrently change the Artifact identity or Commit interface.

## 11. Non-goals

- Full Artifact Graph, stale propagation or Impact Preview.
- Persistent database implementation.
- Workflow lifecycle or LangGraph State.
- Source, Knowledge, Content or Review logic.
- Approval status policy beyond preserving immutable history.
- Production Artifact or Provider Execution Record.

## 12. Acceptance Criteria

### Functional

1. A valid first Candidate Commit returns an exact Reference for Version 1.
2. The committed Version can be retrieved only by an exact Reference.
3. An explicit revision creates the next Version and leaves Version 1 unchanged and retrievable.
4. An equivalent repeated logical Commit returns the existing exact Reference and does not create another Version.
5. An invalid or unvalidated Candidate returns a bounded failure and creates no Version.

### Contract

6. Candidate and Artifact Version are distinct observable concepts.
7. No public operation selects implicit latest.
8. A committed payload and its provenance / dependencies cannot be mutated through returned values.
9. Commit does not advance Workflow or create Approval / Review facts.

### Testing

10. Deterministic tests cover first Commit, exact retrieval, revision, historical preservation, duplicate Commit and invalid Candidate.
11. Tests run without network access, Provider credentials or paid calls.

### Regression

12. No existing upstream document is modified.
13. No code outside the approved Artifact file scope is changed, except minimal package markers explicitly listed in the future Task Package.

### Documentation

14. The implementation seam and test command are recorded in the worker handoff; no frozen Contract is rewritten.

## 13. Verification Requirements

The future Task Package must provide exact executable commands after the implementation environment is established. Expected evidence classes:

- automated unit-test output;
- file-scope diff;
- proof that duplicate Commit leaves version count unchanged;
- proof that revision preserves and retrieves the prior Version;
- proof that no implicit-latest public operation exists;
- proof that tests perform no external call.

## 14. Risk

- Accidentally treating content equality as the whole business identity.
- Returning mutable payload objects that can change committed history.
- Conflating Artifact identity, Version and logical Commit identity.
- Hiding an implicit latest lookup in a convenience method.
- Choosing a storage detail that leaks into the core-owned interface.

## 15. Escalation Conditions

Stop and return to ORCHESTRATOR_REVIEWER if implementation requires:

- a change to the Step 5 Artifact Model;
- a second ownership such as Workflow or persistent Storage Adapter;
- an external dependency or major toolchain decision;
- database, network, Provider or credential access;
- a public implicit-latest operation;
- files outside the future Package scope;
- fallback from exact `luna-worker`.

## 16. Expected Handoff

The assigned worker must return one of:

- `READY_FOR_INTEGRATION_REVIEW` with files, behavior, tests, contract evidence and residual risks;
- `BLOCKED_WITH_EVIDENCE`;
- `SPECIFICATION_REVIEW_REQUIRED`;
- `BLOCKED_LUNA_WORKER_UNAVAILABLE` before assignment if the exact route fails.

## 17. Readiness Review

| Contract Gate | Result |
| --- | --- |
| Single ownership | Passed |
| Single verification target | Passed |
| Exact baseline | Passed |
| Allowed / forbidden scope | Passed |
| Observable acceptance | Passed |
| No external side effect | Passed |
| Coding Authorization | Passed with Vertical-Slice scope |
| W1 Entry | Passed |
| GitHub Issue / Issue-bound Package | Pending Product Owner Issue-creation authorization |
| Exact luna-worker route | Passed for read-only verification; implementation assignment pending Package |

```text
CONTRACT STATUS: READY_FOR_ISSUE_SPECIFICATION
ASSIGNMENT STATUS: BLOCKED_PENDING_ISSUE_AND_TASK_PACKAGE
CODING STATUS: NOT_STARTED
```
