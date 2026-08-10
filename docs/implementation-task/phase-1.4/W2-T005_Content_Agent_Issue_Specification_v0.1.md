# W2-T005 Content Agent — Issue Specification v0.1

## Issue Identity

| Field | Value |
| --- | --- |
| Issue | [#13](https://github.com/JettxonHo/AI-Course-Factory/issues/13) |
| Title | W2-T005: implement grounded Content Agent and Script Candidate |
| Wave / Milestone | W2 / M2 |
| Category | Content Agent Runtime |
| Owner | ORCHESTRATOR_REVIEWER |
| Responsible Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Background and Goal

W2-T004 now commits an exact, source-grounded Knowledge Version. This task converts that Version into committed Course / Episode Plans and a reviewable Script Version without weakening Knowledge grounding or giving the Agent Commit, Workflow or Approval ownership.

## Dependencies and Preconditions

- W2-T004 merged by PR #12; 42-test post-merge suite passed.
- Artifact Candidate / Commit and exact Reference contracts are accepted.
- Content Agent and Model Runtime boundaries in Technical Spec Step 3 and Implementation Boundary Step 6 remain frozen.
- Real LLM Provider and credentials remain unauthorized.

## Modification Scope

Only Content Agent, provider-neutral content runtime value contracts, their public exports and public behavior tests. Existing Artifact / Workflow / Knowledge implementation and dependencies are non-modification scope.

## Artifact / Workflow Impact

Produces `content_plan` and `script` Candidates only. External tests Commit them and verify exact lineage. It does not start the Mandatory Review Gate, approve Script, update selected references or mutate Workflow State.

## Acceptance and Test Requirements

- Planning, exact Plan Commit, grounded Script, exact Script Commit and immutable Script revision are public-behavior tested.
- Malformed context, lineage, grounding, Scene structure, duration and runtime failures fail closed.
- Full regression and compile checks pass.
- No new Agent, Skill, Provider, Renderer, dependency or product capability.

## Risks and Stop Conditions

The key risk is weakening exact Plan lineage by predicting uncommitted References. The implementation must stage planning and scripting around external Plan Commit. Stop on any need to modify Artifact or Workflow ownership.

## Completion Definition

Code completed, tests passed, contract verified, task documentation updated and no scope drift; then ORCHESTRATOR_REVIEWER may enter PR Review.
