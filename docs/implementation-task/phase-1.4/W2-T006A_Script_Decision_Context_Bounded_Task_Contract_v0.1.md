# W2-T006A Script Decision Context — Bounded Task Contract v0.1

## Identity

| Field | Value |
| --- | --- |
| Task | `W2-T006A` |
| Issue | [#17](https://github.com/JettxonHo/AI-Course-Factory/issues/17) |
| Wave / Milestone | W2 / M2 |
| Primary Ownership | Artifact Layer / Approval decision-record seam |
| Responsible Agent | exact `luna-worker`; no fallback |

## Objective

Close the remaining Technical Spec §9.8.3 Approval Record gap by persisting bounded Creator decision context with every immutable Script decision. Reject / Revise intent must not depend on UI memory or chat history.

## Contract

- `ScriptDecisionRecord` stores immutable decision context.
- `reject` and `revise` require non-empty bounded context.
- `approve` may use an empty or bounded context.
- decision context participates in equivalent replay / conflict semantics.
- context does not become Workflow State, Artifact payload, Review Artifact or Content Agent memory.

## Acceptance Criteria

1. Revise with bounded context persists it on the exact Script decision.
2. Reject / Revise with missing, blank, control-character or oversized context fails with no record.
3. Equivalent replay with the same context is idempotent; changed context under the same decision ID conflicts.
4. Existing forged-assessment and Hard Block protections remain intact.
5. No Workflow, Agent, Provider, Commit or product contract changes.
6. Full regression, compile, diff and import checks pass.

## Non-goals / Stop Conditions

No Application coordinator, Workflow resume, content regeneration, UI, API, database, Reviewer or new feature. Stop on any need to change another ownership area.
