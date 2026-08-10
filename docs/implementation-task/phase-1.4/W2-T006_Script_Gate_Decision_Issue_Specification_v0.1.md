# W2-T006 Script Gate Decision — Issue Specification v0.1

## Issue Identity

| Field | Value |
| --- | --- |
| Issue | [#15](https://github.com/JettxonHo/AI-Course-Factory/issues/15) |
| Title | W2-T006: implement Script Gate and Creator decision record boundary |
| Wave / Milestone | W2 / M2 |
| Category | Script Gate Decision Record |
| Owner | ORCHESTRATOR_REVIEWER |
| Responsible Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Background and Goal

W2-T005 commits a grounded Script, but Agent validation cannot be the approval authority. Before the existing Human Gate advances, the system needs an Artifact Layer decision-record seam that rechecks mandatory constraints and durably binds the Creator action to one exact Script Version.

## Dependencies and Preconditions

- W2-T005 merged by PR #14; 51-test post-merge suite passed.
- Technical Spec Review / Approval separation and Step 6 persistence ordering remain frozen.
- Existing Artifact Commit and Workflow implementations are accepted and are non-modification scope.

## Modification Scope

Only a new Artifact Layer Script decision module, its public exports and public behavior tests. No existing Artifact Commit, Workflow, Agent, Knowledge or dependency implementation may change.

## Acceptance and Test Requirements

- valid lineage Pass, representative Hard Blocks, exact immutable decision records and idempotency are public behavior tests;
- Hard Block approval bypass is mutation-sensitive tested;
- Reject / Revise retain the original Script;
- full regression, compile and boundary audits pass.

## Completion Definition

Code completed, tests passed, contract verified, documentation updated and no scope drift; then ORCHESTRATOR_REVIEWER may enter PR Review.
