# W2-T007 Vertical Slice Integration — Bounded Task Contract v0.1

## Identity

| Field | Value |
| --- | --- |
| Task | `W2-T007` |
| Issue | [#19](https://github.com/JettxonHo/AI-Course-Factory/issues/19) |
| Wave / Milestone | W2 / M2 |
| Category | Application Coordination / Vertical Slice Acceptance |
| Primary Ownership | Application Layer / Script Review coordination seam |
| Responsible Agent | exact `luna-worker`; no fallback |

## Objective and Verification Target

Connect the already accepted seams without changing them:

```text
exact committed Script lineage
    → deterministic Script Gate assessment
    → immutable Creator decision persisted
    → existing LangGraph Script Review resume
```

Then prove the complete offline Phase 1.4 Vertical Slice:

```text
fixture public GitHub input → Source validation / normalization → Source Record
→ Knowledge Candidate / Commit → Course / Episode Plan Commit → Script v1 Commit
→ Mandatory Gate → Reject with durable context → exact-prior Script v2 Commit
→ reconstructed Resume → Approve exact v2 → script_approved
```

The single verification target is an exact approved Script v2 with v1 preserved, a durable Approval Record and control-only resumable Workflow state.

## Application Coordination Contract

- `start` accepts task/thread and one exact Script Reference, resolves its exact Knowledge / Plan lineage from Artifact Storage, obtains an issued assessment, then starts the existing Workflow gate.
- `decide` first validates the existing pending checkpoint and exact selected Script; it then resolves/assesses exact lineage, persists the Creator decision, and only afterward calls Workflow Resume.
- Hard Block Approve returns failure and leaves Workflow pending with no valid decision record.
- Workflow failure after decision persistence is reported without deleting the record; the same command may be retried idempotently.
- Application result may expose control result, assessment and decision record, but never copies Script payload into Workflow state.

## Acceptance Criteria

1. Valid exact Script starts at a mandatory pending gate with Pass assessment.
2. Hard Block cannot Approve and Workflow remains pending.
3. Wrong task/thread/version/pending gate fails before a decision record is created.
4. Decision record is observable before Workflow Resume is invoked.
5. Reject / Revise reaches `script_revision_required`; Approve reaches `script_approved`.
6. Reconstructed Workflow runtime with the same Checkpoint Adapter resumes correctly.
7. Offline end-to-end test uses real module boundaries and controlled fixture adapters, not real network or LLM Provider.
8. End-to-end proof creates Source Record, Knowledge, Course Plan, Episode Plan, Script v1 and Script v2 exact immutable References.
9. Revision instruction is read from the persisted Creator decision context; Script v2 uses v1 as exact prior Version.
10. Final Approval Record and Workflow selected Reference both bind exact Script v2; v1 remains retrievable.
11. No existing Artifact, Workflow, Agent or Knowledge implementation is modified.
12. Full regression, compile, diff and import checks pass.

## Non-goals / Stop Conditions

No UI, API, database, real Provider/network call, Reviewer Agent, Review Artifact, production/media, Packaging or new product capability. Stop if integration requires changing frozen ownership, adding an Agent/Provider or modifying an accepted core module.

## Completion Definition

Application coordinator and complete vertical-slice acceptance test pass independent review with no Critical or Important finding; main post-merge suite passes and W2 exit evidence can be issued.
