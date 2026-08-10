# W2 Grounded Script Slice — Wave Exit Record v1.0

## Exit Status

| Field | Value |
| --- | --- |
| Wave | W2 — Grounded Script Slice |
| Milestone | M2 — Source to Approved Script |
| Status | Complete |
| Date | 2026-08-10 |
| Reviewer | ORCHESTRATOR_REVIEWER |

## Accepted Business Closure

```text
Microsoft AI-For-Beginners Source locator
    → exact source commit and normalized material
    → immutable Source Record
    → grounded Knowledge Candidate / Artifact
    → exact Course and Episode Plan Artifacts
    → grounded six-scene Script v1
    → Mandatory Script Review
    → Creator Reject with durable context
    → exact-prior Script v2
    → reconstructed Workflow Resume
    → Creator Approve exact Script v2
```

The final Workflow lifecycle state is `script_approved`. The Approval Record and Workflow-selected input both bind to the exact Script v2 Reference, while Script v1 remains immutable and retrievable.

## Accepted Outcomes

1. The public GitHub Connector validates the frozen Microsoft repository locator, resolves an exact commit and returns bounded source material without owning Artifact Commit.
2. Source normalization preserves lossless text and exact provenance while keeping prompt-like source text inert.
3. Source Record, Knowledge, Course Plan, Episode Plan and Script outputs cross module boundaries only as validated Candidates or exact immutable Artifact References.
4. Knowledge claims remain traceable to the selected Source Record; Content plans and Script scenes may select only those claims.
5. The Content Agent produces the fixed six-scene, approximately 60-second, 9:16 Simplified Chinese Script required by the MVP Episode Template without owning approval, workflow or commit.
6. Deterministic Script assessment records Hard Blocks separately from the Creator decision. A forged or real Hard Block cannot be approved.
7. Reject / Revise decision context is durable, bounded and part of idempotent replay semantics; it is not sourced from UI memory or chat history.
8. Application coordination persists the Creator decision before Workflow resume and can retry a post-persistence Workflow failure without duplicating the decision.
9. Workflow Checkpoints remain control-only, store exact selected References and support reconstruction with the accepted checkpoint adapter.

## Evidence

| Task | Issue / PR | Post-merge or accepted suite |
| --- | --- | --- |
| W2-T001 — GitHub Source Connector | [#5](https://github.com/JettxonHo/AI-Course-Factory/issues/5) / [#6](https://github.com/JettxonHo/AI-Course-Factory/pull/6) | 24 tests; public read smoke passed |
| W2-T002 — Source Normalization | [#7](https://github.com/JettxonHo/AI-Course-Factory/issues/7) / [#8](https://github.com/JettxonHo/AI-Course-Factory/pull/8) | 31 tests |
| W2-T003 — Source Record Candidate | [#9](https://github.com/JettxonHo/AI-Course-Factory/issues/9) / [#10](https://github.com/JettxonHo/AI-Course-Factory/pull/10) | 37 tests |
| W2-T004 — Knowledge Agent | [#11](https://github.com/JettxonHo/AI-Course-Factory/issues/11) / [#12](https://github.com/JettxonHo/AI-Course-Factory/pull/12) | 42 tests |
| W2-T005 — Content Agent | [#13](https://github.com/JettxonHo/AI-Course-Factory/issues/13) / [#14](https://github.com/JettxonHo/AI-Course-Factory/pull/14) | 51 tests |
| W2-T006 — Script Gate Decision | [#15](https://github.com/JettxonHo/AI-Course-Factory/issues/15) / [#16](https://github.com/JettxonHo/AI-Course-Factory/pull/16) | 57 tests |
| W2-T006A — Decision Context | [#17](https://github.com/JettxonHo/AI-Course-Factory/issues/17) / [#18](https://github.com/JettxonHo/AI-Course-Factory/pull/18) | 59 tests |
| W2-T007 — Vertical Slice Integration | [#19](https://github.com/JettxonHo/AI-Course-Factory/issues/19) / [#20](https://github.com/JettxonHo/AI-Course-Factory/pull/20) | 66 tests |

Final post-merge verification on `main`:

```text
Full suite: 66 / 66 passed
Vertical Slice integration test: passed
Python 3.12 compilation: passed
Working tree: clean
```

## Boundary Audit

- Artifact First, immutable Version and exact Reference rules are preserved.
- Workflow owns lifecycle, interrupt and resume; it does not own Creator Approval facts or Artifact payloads.
- Knowledge and Content Agents return Candidates and use provider-neutral runtime ports; no Agent performs Artifact Commit or Workflow transition.
- No new Agent, Skill, Provider, Renderer, Knowledge Source or product capability was introduced.
- No real model Provider, paid service, media production, Packaging, UI, API, database or distributed infrastructure was implemented.
- The first end-to-end proof intentionally uses controlled offline model runtimes. W2-T001 separately verified the public GitHub read path.
- The accepted in-memory Artifact and Checkpoint implementations remain Vertical Slice details, not production persistence claims.

No Critical or Important findings remain.

## Exit Decision

```text
G5_INTEGRATION_REVIEW_PASSED
G6_W2_EXIT_GATE_PASSED
M2_COMPLETE
PHASE_1_4_VERTICAL_SLICE_GOAL_ACCEPTANCE_ALLOWED
M3_NOT_AUTHORIZED
```
