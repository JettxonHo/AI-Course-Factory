# AI Course Factory MVP Phase 1.4 Milestone Tracking v0.1

## 1. Tracking Status

| Field | Value |
| --- | --- |
| Goal | `GOAL-P1.4-VS-001` |
| Status | Active |
| Tracking Date | 2026-08-10 |
| Active Milestone | M2 — Source to Approved Script |
| Active Wave | W2 — Grounded Script Slice |
| Coding | In Progress — W2 bounded task preparation |
| External Provider Calls | Closed |

This tracker is a projection of accepted Milestone and Wave contracts. It does not redefine M0–M8 or W0–W8.

## 2. Milestone Board

| Milestone | State | Entry Evidence | Active Outcome | Exit Evidence |
| --- | --- | --- | --- | --- |
| M0 — Planning and Coding Gate | Complete | Step 1–12 review chain | Consolidated baseline acceptance and scoped coding authorization | Phase 1.3 Baseline Acceptance Record v1.0 |
| M1 — Artifact and Workflow Control Spine | Complete | M0 complete; W1 entry authorized | Exact Reference, immutable Commit, control-only Checkpoint / Resume | W1 Exit Record; Issues #1 / #3 and PRs #2 / #4 |
| M2 — Source to Approved Script | In Progress | W1 Exit Gate passed | Source → Knowledge → Script → Mandatory Review | W2 entry authorized; first task preparing |
| M3 — Production Planning and Budget | Outside current Goal | M2 exit and separate continuation decision | Not planned in this Goal | Not applicable |
| M4 — Safe Production Closure | Outside current Goal | M3 exit | Not planned in this Goal | Not applicable |
| M5 — Provider-backed Production | Outside current Goal | M4 exit plus external side-effect authorization | Not planned in this Goal | Not applicable |
| M6 — Review and Recovery | Outside current Goal | M5 exit | Not planned in this Goal | Not applicable |
| M7 — Workspace and Packaging | Outside current Goal | M6 exit | Not planned in this Goal | Not applicable |
| M8 — MVP Acceptance | Outside current Goal | M7 exit | Not planned in this Goal | Not applicable |

## 3. M1 Ordered Outcomes

Only the next bounded outcome is instantiated. Later outcomes remain ordering markers, not Task Instances.

| Order | Outcome | State | Parallel Rule |
| --- | --- | --- | --- |
| 1 | Artifact Commit Boundary: Candidate validation, immutable Version, exact Reference and duplicate-commit behavior | Complete — Issue #1 / PR #2 merged | Must merge before downstream Artifact consumers |
| 2 | Artifact Storage Adapter seam | Deferred beyond first in-memory Vertical Slice | Persistent replacement must keep the accepted Artifact interface |
| 3 | Minimal Workflow control state and Command / Result | Integration Review Passed — Issue #3 | Cannot redefine exact Reference established by outcome 1 |
| 4 | Checkpoint / Resume at Human Interrupt | Integration Review Passed — 17 / 17 full suite | Requires Workflow control state and exact Reference behavior |
| 5 | W1 integration evidence | Complete — 17 / 17 post-merge suite on `main` | Join after all required M1 outcomes |

## 4. M2 Ordered Outcomes

Only the current bounded outcome may be instantiated; later outcomes remain ordered markers.

1. Public GitHub Source validation and exact-commit acquisition — active task preparation.
2. Source normalization, provenance and Source Record Commit — pending accepted Connector result contract.
3. Knowledge Agent Candidate and Commit.
4. Content Agent Plan / Script Candidates and Commit.
5. Script grounding / completeness guard.
6. Mandatory Script Review interrupt.
7. Approve / Reject / Revise and Resume.
8. Vertical Slice acceptance evidence.

## 5. Gate Tracking

| Gate | State | Evidence / Blocker |
| --- | --- | --- |
| G0 — Baseline Approval | Passed | Phase 1.3 Baseline Acceptance Record v1.0 |
| G1 — Coding Authorization | Passed with scope | Phase 1.4 Vertical Slice directive; no full-MVP or Provider authorization |
| G2 — W1 Entry | Passed for bounded task preparation | W1 Execution Record v0.1 |
| G3 — W1-T001 Readiness | Passed | Issue #1 and Issue-bound Task Package v0.1 |
| Exact luna-worker route | Runtime verified | W1-T001 and W1-T002 executed through exact `luna-worker`; no fallback |
| Git / GitHub execution target | Passed | Local `main` repository bound to public `JettxonHo/AI-Course-Factory` |
| External Side-effect Gate | Closed / Not Applicable | W1-T001 has no external Provider side effect |
| G4 — W1 Exit | Passed | W1 Exit Record; PR #4 merged; 17 / 17 post-merge suite |
| G5 — W2 Entry | Passed with scope | GitHub Source Connector bounded task preparation only |

## 6. Update Rule

Update this tracker only when evidence changes. A Task Contract, worker message or code diff alone cannot mark a Milestone complete; ORCHESTRATOR_REVIEWER must verify the applicable exit criteria.
