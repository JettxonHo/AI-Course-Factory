# AI Course Factory MVP Phase 1.4 Implementation Goal v1.0

## 1. Goal Status

| Field | Value |
| --- | --- |
| Goal ID | `GOAL-P1.4-VS-001` |
| Status | Blocked — GitHub Issue creation authorization required |
| Initialized | 2026-08-10 |
| Owner | Product Owner |
| Coordinator | ORCHESTRATOR_REVIEWER |
| Scope Authorization | Granted with Vertical-Slice scope |
| Coding | Not Started |

## 2. Objective

Build the smallest complete Phase 1.4 proof that turns a validated source into immutable Knowledge and Script Artifacts and reaches a resumable Mandatory Script Review Gate with an approved exact Script Version, while preserving the frozen AI Course Factory architecture and product scope.

## 3. Target Business Closure

```text
Source Input
    ↓
Source Validation
    ↓
Source Record
    ↓
Knowledge Agent Candidate
    ↓
Knowledge Artifact Commit
    ↓
Content Agent Script Candidate
    ↓
Script Artifact Commit
    ↓
Mandatory Script Review Gate
    ↓
Approve / Reject / Revise
    ↓
Approved exact Script Version
```

## 4. Contracts to Prove

- Source Connector Boundary.
- Knowledge Agent Candidate contract.
- Content Agent Script Candidate contract.
- Candidate → Validation → Artifact Commit boundary.
- Immutable Artifact Version and exact Artifact Reference.
- Workflow control state separated from Artifact payload.
- Checkpoint / Resume at a Mandatory Human Gate.
- Creator Approve / Reject / Revise separated from AI Review facts.

## 5. Goal Milestones

| Milestone | Goal Contribution | Current State |
| --- | --- | --- |
| M0 — Planning and Coding Gate | Accept Step 1–12, resolve Gate order and grant scoped authorization. | Complete |
| M1 — Artifact and Workflow Control Spine | Establish only the control seams required by the target Slice. | In Progress — task preparation |
| M2 — Source to Approved Script | Deliver the end-to-end Creator-verifiable closure. | Pending M1 evidence |
| M3–M8 | Remaining full-MVP outcomes. | Outside this Goal |

## 6. Completion Criteria

This Goal is complete only when all of the following are demonstrated with executable evidence:

### Artifact

- A Source Record can be committed.
- A grounded Knowledge Artifact can be committed.
- A Script Artifact can be committed.
- Every cross-stage input uses an exact immutable Reference.
- Revision never overwrites historical versions.

### Workflow

- Current lifecycle stage can be saved.
- Workflow can resume using selected exact References.
- Workflow pauses at Mandatory Script Review.
- Artifact payload is not duplicated into Workflow State.

### Agent

- Knowledge Agent returns a Candidate, not an Artifact Reference.
- Content Agent consumes an exact Knowledge Reference and returns a Script Candidate.
- Neither Agent owns Workflow transition, Approval or Artifact Commit.

### Review

- Creator can Approve an exact Script Version.
- Creator can Reject an exact Script Version.
- Revise / regenerate creates a new Script Version and preserves history.
- A Hard Block cannot be bypassed by Creator Approval.

## 7. Explicit Non-goals

- Omni, TTS, Video, Audio Composer, Media Composer or Packaging.
- Production Agent, Production Orchestrator or production recovery.
- Multi-user, multi-course, SaaS authorization or commercialization.
- Microservices, event bus, distributed workers, dynamic workflow builder or multi-provider routing.
- New Agent, Skill, Provider, Renderer, Knowledge Source or product capability.
- GitHub repository creation, external Issue creation, Branch or PR unless separately authorized.

## 8. Stop Conditions

Stop and escalate if the Goal requires:

- a changed Artifact Model or Workflow ownership;
- a new product Agent or Skill;
- a major dependency not required by the current Slice;
- external paid Provider access;
- a product-scope change;
- implicit latest, silent overwrite or Artifact payload in Workflow State;
- implementation without an approved bounded task and eligible execution route.

## 9. Current Next Action

W1 and `W1-T001` preparation are complete, and the execution repository is now `JettxonHo/AI-Course-Factory`. Resume implementation only after the Product Owner authorizes creating the real GitHub Issue from the approved Issue Specification; the Issue-bound Task Package and formal assignment follow that action.
