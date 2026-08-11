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

## Decision D-002 — Consolidate Daily Development Truth Sources

| Field | Value |
| --- | --- |
| Status | Accepted |
| Decision Date | 2026-08-12 |
| Decision Owner | Product Owner |
| Applies To | AI Course Factory planning and all future Goals |
| Source Directive | Product Owner approval of controlled rebaseline and Goal/Luna workflow |

### Context

The repository accumulated more than 7,000 lines across PRD, Technical Spec, Implementation Boundary, plans, execution records and task packages. Later acceptance records resolved many older status fields without updating those files. The same future task could therefore appear both approved and unauthorized depending on which document Codex read first.

The code has a healthy 66-test Source-to-approved-Script slice, but document volume and duplicated task contracts now exceed the amount required to direct the next implementation safely.

### Alternatives

#### Continue Phase Addendums

Small immediate change, but each new stage would add another source of status and authority drift.

#### Add Only a Master Index

Preserves all existing baselines, but Codex would still need to interpret several overlapping product, architecture and implementation contracts.

#### Controlled Rebaseline

Create one PRD, one System Spec, one Implementation Spec, one Development Workflow, one active Goal and one current STATUS. Preserve all old files as historical evidence.

### Decision

Adopt the controlled rebaseline.

Daily development truth is split by question:

- PRD: product value, behavior, scope and acceptance；
- System Spec: domain language, Artifact, state, gates and module interfaces；
- Implementation Spec: code/runtime mapping, persistence, adapters and testing；
- Development Workflow/AGENTS: Goal, model routing, Issue, PR and Review；
- GOAL: current authorized scope and stopping condition；
- STATUS: verified current facts。

Historical Phase documents remain in place and must not be deleted. They are no longer daily implementation entry points unless a current truth source explicitly references them.

### Agent Routing Decision

- ORCHESTRATOR_REVIEWER uses project configuration `gpt-5.6-sol / xhigh`.
- Bounded code implementation uses exact custom Agent `luna-worker`, configured `gpt-5.6-luna / max`.
- No automatic Terra/default-worker fallback is allowed.
- Configuration evidence and runtime model evidence remain separate.

### Consequences

- New implementation tasks need one authoritative Issue/Task Contract, not four parallel task documents.
- Goal and STATUS are updated after accepted progress; Specs change only when their corresponding contract changes.
- Existing Phase 1.5 untracked files are protected until the Product Owner chooses archive or commit treatment.
- The proposed Core MVP Goal still requires separate approval before feature coding.
- Real Provider selection, credentials and budget remain separate human decisions.
