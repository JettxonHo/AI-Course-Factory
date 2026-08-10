# AI Course Factory Decision Log

## Decision D-001 — Engineering Governance Simplification Principles

| Field | Value |
| --- | --- |
| Status | Accepted |
| Decision Date | 2026-08-10 |
| Decision Owner | Product Owner |
| Applies To | Phase 1.4 Vertical Slice implementation |
| Source Directive | AI Course Factory MVP — Phase 1.4 Vertical Slice Implementation Directive |

### Context

Phase 1.3 produced a complete architecture, implementation-planning and engineering-governance chain. Step 12 concluded that the architecture and contracts were ready, while baseline approval, execution ordering, repository targeting and coding authorization still required a Product Owner decision.

The Product Owner has now directed the project to begin Phase 1.4 with the smallest complete proof:

```text
Source Input
    ↓
Source Validation
    ↓
Knowledge Artifact
    ↓
Content Agent
    ↓
Script Artifact
    ↓
Script Review Gate
    ↓
Approved Script
```

The objective is to validate real business contracts, not to extend the architecture or build the entire MVP.

### Decision

Adopt the following Engineering Governance Simplification Principles:

1. **Freeze architecture; deepen only the active seam.** Step 1–11 contracts remain authoritative. Phase 1.4 implementation cannot introduce a new Agent, Skill, Provider, Renderer, product capability or ownership rule.
2. **Use one bounded outcome at a time.** Each implementation task has one primary ownership, one verification target, explicit allowed / forbidden scope and fail-closed stop conditions.
3. **Treat documents as gates, not output volume.** Create only the Goal, Milestone tracking, Wave record, Bounded Task Contract, Issue Specification and execution package required to make the next bounded implementation safe.
4. **Preserve the canonical order.** The accepted execution order is G0 Baseline Approval → G1 scoped Coding Authorization → G2 Wave Entry → G3 Bounded Work Readiness → assignment → implementation → evidence review. Issue and Task Package artifacts do not grant authorization by themselves.
5. **Separate local specification from external GitHub state.** An Issue Specification may exist before a GitHub Issue. It must use `Issue ID: pending` and cannot be represented as an external Issue. A Task Package requiring an existing Issue is not created until an execution repository / GitHub target exists.
6. **Grant coding narrowly.** The Phase 1.4 directive grants coding authorization only for the accepted Vertical Slice and only through approved bounded tasks. It does not authorize the full MVP, external Provider calls, Branch / PR creation, or scope expansion.
7. **Fail closed on execution identity.** Ordinary bounded implementation routes only to exact `luna-worker`. If that route cannot be confirmed when a complete Task Package is ready, record `BLOCKED_LUNA_WORKER_UNAVAILABLE`; do not silently substitute another worker.
8. **Keep external side effects closed.** The first Vertical Slice uses no Omni, TTS, paid media call, deployment or automatic publication.
9. **Stop on contract pressure.** If implementation needs a changed Artifact Model, changed Workflow ownership, new Agent, major dependency or product-scope change, stop and return to Product Owner review.
10. **Evidence advances state.** A task advances only after its functional, contract, test, regression and documentation evidence passes ORCHESTRATOR_REVIEWER review.

### Authorization Interpretation

The 2026-08-10 Phase 1.4 directive is the Product Owner's:

- consolidated acceptance instruction for the Step 1–12 planning chain;
- decision to preserve the Step 8–10 Gate order;
- authorization to initialize the Phase 1.4 Implementation Goal and Milestone tracking;
- task-scoped Coding Authorization for the Source-to-Approved-Script Vertical Slice;
- authorization to create local Bounded Task and Issue Specification artifacts.

It is not authorization to:

- create a GitHub repository or GitHub Issue;
- create a Branch, Worktree, Commit or PR;
- call an external paid Provider;
- implement beyond the current Vertical Slice;
- bypass a missing Task Package or exact worker route.

### Consequences

- Step 12's `ESCALATE_TO_HUMAN` decision is resolved for baseline acceptance, Phase 1.4 entry, Gate order and scoped coding authorization by the Product Owner's later directive.
- Step 12's repository / GitHub target finding remains open. It blocks external Issue, Branch, PR and any Task Package that requires an existing Issue.
- W0 can close once the consolidated Baseline Acceptance Record is created and verified.
- W1 may open for bounded task preparation. Actual implementation begins only when the first task's execution prerequisites are satisfied.
- Existing Step 1–12 files remain unchanged; this log records a later governance decision rather than rewriting historical review documents.

### Rejected Alternatives

#### Continue Phase 1.3 planning

Rejected because the architecture and contract chain is already sufficient for the first Vertical Slice; additional abstract design would not reduce the current implementation risk.

#### Implement the entire Source-to-Approved-Script path as one task

Rejected because Artifact Commit, Workflow control, Source / Knowledge, Content and Human Review have distinct ownership and verification targets. Combining them would violate the bounded-task rules.

#### Bypass GitHub lineage silently

Rejected. Local preparation can continue, but no external Issue, Branch or PR may be claimed until a repository / GitHub target is explicitly established.
