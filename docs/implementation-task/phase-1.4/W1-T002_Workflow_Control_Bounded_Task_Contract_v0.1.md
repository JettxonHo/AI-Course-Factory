# W1-T002 Workflow Control — Bounded Task Contract v0.1

## Contract Status

| Field | Value |
| --- | --- |
| Task ID | `W1-T002` |
| Wave | W1 — Control Spine |
| Milestone | M1 — Artifact and Workflow Control Spine |
| Ownership | Workflow Layer / LangGraph Runtime Boundary |
| Responsible Role | exact `luna-worker` after Package readiness |
| Status | Ready for Issue Specification |

## Task Objective

Implement the smallest real LangGraph workflow runtime that accepts an exact Script Artifact Reference, checkpoints control-only state, pauses at the Mandatory Script Review interrupt, resumes on an exact-version Creator decision and produces an idempotent normalized Workflow result for Approve, Reject or Revise.

## Frozen References

- Technical Spec §6.2 State Ownership, §6.3 Lifecycle, §6.5 LangGraph Mapping, §6.8 Checkpoint / Resume, §6.9 Human Interrupt, §6.10 Idempotency and §6.11 invariants.
- Technical Spec §9.11 LangGraph State Logical Schema and §9.12 Command / Result.
- Implementation Boundary Spec §1 Workflow mapping, §4 Runtime boundary and §6 Checkpoint Storage.
- Execution Plan W1 Control Spine.
- W1-T001 accepted Artifact public seam.
- Current LangGraph official documentation: [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) and [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).

## Single Verification Target

```text
Exact Script Reference
    ↓
control-only LangGraph state + checkpoint
    ↓
Mandatory Script Review interrupt
    ↓
Command(resume=exact decision)
    ↓
approved or revision-required normalized result
```

## Allowed Changes

- `pyproject.toml` and `uv.lock` only to establish the approved Python/LangGraph runtime and test configuration.
- `src/ai_course_factory/workflow/` for Workflow control models, checkpoint adapter and Script Review graph runtime.
- `tests/workflow/` for behavior tests.
- Minimal package markers.
- W1-T002 Task Record for evidence handoff when requested.

## Forbidden Changes

- Artifact model / Commit interface or W1-T001 tests.
- Source, Knowledge Agent, Content Agent, Reviewer, Production or UI behavior.
- Script payload in LangGraph State.
- Approval Record Artifact, Script regeneration or content modification.
- Dynamic Workflow Builder, Event Bus, distributed execution or persistent database.
- External LLM, Provider, network or credentials.
- An interrupt node that performs a non-idempotent side effect before `interrupt()`.

## Input Contract

- Task / thread identity.
- One exact committed Script Artifact Reference.
- One Creator command with command identity, action (`approve`, `reject`, `revise`) and the same exact Script Reference.

The Workflow may read the Script only to validate that the exact Reference exists. It must not copy the Script payload into graph state.

## Output Contract

- At first invocation: checkpointed `script_review_pending` control state with a pending mandatory gate and exact Script Reference.
- At resume: normalized result with `script_approved` or `script_revision_required` lifecycle state.
- Repeated equivalent command returns the same result; conflicting command identity fails closed.
- Wrong-version, missing-reference or invalid action fails without advancing the graph.

## Acceptance Criteria

1. Uses current LangGraph `StateGraph`, a checkpointer and `interrupt()` / `Command(resume=...)` semantics.
2. Initial execution pauses at Mandatory Script Review and exposes exact target Reference plus allowed actions.
3. Checkpoint state contains control data and exact References only; no Script payload, model history or UI draft.
4. A new Workflow runtime using the same checkpoint adapter can inspect and resume the same thread.
5. Approve reaches `script_approved`; Reject and Revise reach `script_revision_required`.
6. Wrong exact Version, unknown Artifact, unsupported action and command conflict fail closed.
7. Equivalent command replay is idempotent and does not re-execute a completed transition.
8. Interrupt node has no pre-interrupt side effect.
9. Offline deterministic tests cover interrupt, checkpoint inspection, reconstructed runtime resume, all three actions and failure / replay paths.
10. No new product capability, Agent, Provider or Artifact payload duplication is introduced.

## Dependency and Parallel Rule

```text
Depends On: W1-T001 merged
Consumes: exact Script Artifact Reference
Produces: Workflow checkpoint and normalized Script decision result
Blocks: W2 Source-to-Script integration and Mandatory Review closure
Can Parallel With: no task changing Workflow State or exact-reference interface
```

## Stop Conditions

Stop for specification review if current LangGraph behavior cannot preserve control-only state, exact-reference resume or interrupt idempotency without changing the frozen Workflow ownership. Stop before adding any external Provider, persistent database or generic workflow platform.

