# W1-T002 Workflow Control — Issue Specification v0.1

## Issue ID

[#3](https://github.com/JettxonHo/AI-Course-Factory/issues/3)

## Title

Implement resumable LangGraph Script Review control flow

## Wave / Milestone / Category

- W1 — Control Spine
- M1 — Artifact and Workflow Control Spine
- Checkpoint / Resume and Command Processing

## Owner / Agent

- Owner: Workflow Layer / LangGraph Runtime Boundary
- Agent: exact `luna-worker`; no fallback

## Status

`ISSUE_CREATED — PACKAGE_READY`

## Goal

Prove one control-only LangGraph flow can bind an exact Script Reference, pause at a mandatory interrupt, reconstruct from a checkpoint and resume idempotently for Approve, Reject or Revise without containing Script payload or owning Approval Artifacts.

## User Value

The Creator can leave and safely return to the exact Script review decision without losing position, reviewing the wrong Version or silently approving stale content.

## Dependencies

- W1-T001 / Issue #1 complete and PR #2 merged.
- Exact Artifact Commit and retrieval public seam.
- Accepted LangGraph checkpoint / interrupt architecture.

## Change Scope

- Approved LangGraph runtime dependency and minimal Python project configuration.
- Workflow control models, in-memory checkpoint adapter and Script Review graph.
- Offline public behavior tests.

## Non-scope

- Artifact payload / schema changes.
- Source, Agent, Reviewer or Approval Record implementation.
- Script generation or regeneration.
- UI, API, database, production or Provider access.

## Interface Constraints

- Application intent enters through Workflow commands only.
- Graph state is control-only and binds exact Artifact References.
- Human interrupt occurs after pending-gate state is checkpointed.
- Resume uses the same thread and `Command(resume=...)`.
- Side effects are outside the interrupt node.
- Equivalent command replay is idempotent; conflicts fail closed.

## Acceptance and Test Requirements

All ten W1-T002 Bounded Task Contract acceptance criteria must pass through public Workflow runtime methods. Tests must run offline with an in-memory checkpointer and the real LangGraph library; internal node call order must not be asserted.

## Risks / Blockers

- LangGraph API drift: use current official docs and lock the resolved dependency.
- Framework object leakage: do not expose raw graph state as the business API.
- Interrupt re-execution: no pre-interrupt non-idempotent side effect.
- Any need to modify Workflow ownership or store Script payload triggers `SPECIFICATION_REVIEW_REQUIRED`.

## Completion Definition

Code complete, tests pass, checkpoint / resume and interrupt behavior verified, architecture/security review passed, docs synchronized and no scope drift. Completion is not M1 exit until post-merge evidence passes.
