# W2-T006 Script Gate Decision — Bounded Task Contract v0.1

## Identity

| Field | Value |
| --- | --- |
| Task | `W2-T006` |
| Issue | [#15](https://github.com/JettxonHo/AI-Course-Factory/issues/15) |
| Wave / Milestone | W2 / M2 |
| Category | Script Gate Decision Record |
| Primary Ownership | Artifact Layer / Approval decision-record seam |
| Responsible Agent | exact `luna-worker`; no fallback |

## Objective and Verification Target

Implement one local, deterministic boundary that independently assesses a selected exact Script Version and persists the Creator's immutable exact-version decision:

```text
exact Script + exact Knowledge / Course Plan / Episode Plan Versions
    → Pass or Hard Block assessment
Creator decision bound to that assessment and Script Version
    → immutable Approval Record
```

The primary verification target is: a Hard Block can never produce a valid Approve record, while valid Approve / Reject / Revise decisions are immutable, exact-version bound and idempotent.

## Assessment Contract

The deterministic guard checks only frozen MVP requirements:

- all required exact References and matching resolved Versions exist;
- Script dependency order and payload lineage are exactly Knowledge, Course Plan and Episode Plan;
- both Plans retain the selected Knowledge dependency and expected roles;
- all Script Scene claim IDs exist in selected Knowledge;
- Simplified Chinese narration, six Scene template, about 60 second duration and 9:16 format are valid;
- required Scene identity, narration and content-level teaching intent are complete.

Failures produce bounded Hard Block findings. This is a deterministic validation guard, not a Reviewer Agent invocation and not a Review Artifact.

## Decision Record Contract

- accepted actions: `approve`, `reject`, `revise`;
- record binds decision ID, task/thread, Creator identity, exact Script Reference, assessment disposition and action;
- Approve requires a Pass assessment for the same exact Script Version;
- Reject / Revise may be recorded for Pass or Hard Block targets;
- equivalent replay returns the same record; conflicting reuse of decision ID fails;
- record is immutable and retrievable by exact decision identity;
- boundary does not advance Workflow.

## Acceptance Criteria

1. A valid committed Script with exact Knowledge / Plan lineage produces Pass.
2. Foreign claim, missing/mismatched dependency, plan mismatch, wrong format, English-only narration or malformed Scene produces Hard Block.
3. Pass + exact Approve persists one immutable Approval Record.
4. Hard Block + Approve fails and persists no record.
5. Reject and Revise persist exact target records without deleting or modifying the Script.
6. Equivalent decision replay is idempotent; conflicting identity reuse fails closed.
7. Exact Reference / Version mismatch and moving `latest` fail closed.
8. No Review Artifact or Reviewer Agent is created; this follows Technical Spec §7.8 formal Reviewer placement.
9. No Workflow, Agent, Provider or Artifact Commit implementation is changed or called.
10. Full regression, compileall, import and diff checks pass.

## Non-goals / Stop Conditions

No Workflow resume, UI, Reviewer Agent, Warning evaluation, Content regeneration, Provider, database, API, status/stale graph or new product capability. Stop if decision persistence cannot precede Workflow without changing the existing Workflow contract, or if a new Reviewer invocation is required.

## Completion Definition

Hard Block assessment, immutable Creator decision persistence, idempotency, tests and independent review pass with no Critical or Important finding.
