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

## Decision D-003 — Accept Scene-Scoped Task Media Projection Architecture

| Field | Value |
| --- | --- |
| Status | Accepted |
| Decision Date | 2026-08-13 |
| Decision Owner | Product Owner |
| Applies To | M3 Task media lifecycle and bounded scene recovery |
| Source Decision | Issue #107, accepted Option A on 2026-08-13 |
| Recording Task | Issue #108 / M3-010A (docs-only) |

### Context

The durable Task projection currently represents the planning stages through Production Budget with ten singleton selections. The merged production path now creates per-Scene Clip and Scene Audio Artifacts plus singleton Subtitle, logical Master Audio, Video, Artifact Manifest and Publish Package Artifacts. The Provider Attempt Ledger records execution history and budget enforcement, while the Decision repository and Workflow checkpoint own review gates. The next architecture must make selected/current media state explicit without changing those ownership boundaries or pretending that a later implementation already exists.

### Decision

Accept **Option A — explicit scene-scoped Task media selections** from Issue #107:

1. Preserve the existing ten singleton planning selections and their persisted compatibility.
2. Add an additive structured Task media projection; do not encode Scene identity as dynamic `scene_clip:<scene_id>` or `scene_audio:<scene_id>` slot strings.
3. Represent one exact `ArtifactReference` per Scene for Clip and Audio with `current|stale` projection state.
4. Represent singleton delivery media selections for Subtitle, logical Master Audio, Video, Artifact Manifest and Publish Package.
5. Bind Scene ordering to the exact Timeline/Production Request order, never lexical Scene ID order.
6. Absence means not yet selected; do not create a mutable or pseudo-Artifact `missing` status.
7. Keep ownership separated: the Artifact repository owns immutable Versions; the Task application projection owns selected/current/stale facts; the Attempt Ledger owns execution history and budget enforcement; Decision and Workflow repositories own gates.
8. A later retry/replace operation replaces only one exact Scene media selection and marks only exact downstream Master Audio, Video, Artifact Manifest and Publish Package facts stale; unaffected Scene media remains current.
9. Final Video decisions remain Decision Records and Workflow checkpoint state, not Artifact selections.

The accepted architecture is a documentation baseline only. Issue #108 does not freeze implementation method signatures, execute schema migration, authorize retry execution, call a Provider, incur fees, or provide code, test or runtime evidence. A separate implementation Issue/Task Contract must be frozen after this docs-only alignment.

### Rejected Alternatives

- **Aggregate-only projection (Option B):** cannot represent selected Scene media before a Video exists and would derive exact Scene impact outside the generic Task projection.
- **Dynamic slot strings:** would encode Scene identity in an untyped slot namespace and weaken ordering, uniqueness and compatibility invariants.
- **Attempt Ledger as selected-state owner:** execution history and budget enforcement are not the Task projection's selected/current/stale facts.

### Consequences

- The canonical terms are **Task media projection**, **scene media selection** and **delivery media selection**.
- System and Implementation Specs must describe an additive, typed, frozen/slotted value seam and backward-readable planning snapshots without inventing a concrete public API in this decision.
- The later implementation Task Contract must choose the smallest verified application seam and backward-compatible SQLite schema evolution or additive table; no migration is performed by D-003.

## Decision D-004 — Rebaseline Remaining Work to a Vertical FAST-MVP

| Field | Value |
| --- | --- |
| Status | Accepted |
| Decision Date | 2026-08-13 |
| Decision Owner | Product Owner |
| Applies To | Remaining Core MVP work after M3-009 |
| Supersedes | Remaining M3–M6 sequencing in Goal v1.0 |

### Context

The repository has a strong offline backend but no user-operable workspace or real Visual/TTS end-to-end path. Planning and defensive validation grew faster than product closure: many small PRs proved increasingly narrow repository, corruption, exact-type and concurrency cases while the Creator still could not complete the job through a UI.

The Product Owner asked for the smallest end-to-end MVP that preserves all core user value and explicitly approved the FAST-MVP rebaseline.

### Decision

1. Optimize remaining work for one fixed, browser-driven vertical Demo: source -> grounded Script approval -> planning -> Budget approval -> real Visual/TTS -> FFmpeg -> one Scene recovery -> Final approval -> export.
2. Preserve six release-blocking invariants: source traceability, exact Script/Final decisions, authorized spend, safe uncertain paid attempts, unaffected Scene preservation and playable evidenced export.
3. Treat other corruption, concurrency, mutation and future-schema defenses as task-specific only when a concrete changed boundary carries that risk.
4. Reuse accepted M0–M3-009 work; do not reopen it or refactor broadly before the vertical flow works.
5. Give the in-flight Issue #110 candidate one bounded review/full regression. Merge if it fits without architectural rework; otherwise park it intact and implement only the vertical workspace's minimum need.
6. Deliver F1 as one offline vertical workspace Issue/PR. Implement Visual and TTS Adapters only after separate Provider and spend decisions, then run one real acceptance Demo.
7. Put routine Goal/STATUS synchronization in feature PRs instead of standalone status PRs.

### Consequences

- The PRD, both Specs, Goal, STATUS, workflow and Agent rules use the compact FAST-MVP v1.1 baseline.
- Existing detailed historical evidence remains in Git/GitHub and is not duplicated in daily STATUS.
- Main-agent independent review and exact Luna routing remain mandatory.
- This decision authorizes F0/F1 offline work, but not Provider selection, credentials, fees, deployment or publication.

### Rejected Alternatives

- **Continue horizontal hardening before UI:** rejected because it delays validation of the primary user job.
- **Discard the current backend and rewrite:** rejected because the existing planning, persistence, production, composition and packaging seams are reusable.
- **Remove all safeguards:** rejected because claim accuracy, money, exact approvals, Scene recovery and export integrity are real MVP risks.

## Decision D-005 — PD-001A Creator-supplied Desktop ImageGen visual bridge

| Field | Value |
| --- | --- |
| Status | Accepted for bounded F2A implementation |
| Decision Date | 2026-08-13 |
| Decision Owner | Product Owner |
| Applies To | Issue #117 / F2A local visual-import mode |
| Product Decision | `PD-001A` |

### Context

The real Visual Provider/model/credential decision (`PD-001`) remains open, while the Creator needs a truthful path to exercise the local production, replacement, restart and package contracts. ChatGPT Desktop ImageGen can supply still images outside the application without introducing a cloud SDK, credential or application-side Provider call.

### Decision

1. Add one explicit application mode selected with `--visual-import-dir` (or the equivalent `create_app`/facade argument). Never infer Downloads, Desktop, a newest file or an alternate extension.
2. Require the exact initial names `scene-1.png` through `scene-6.png`, plus exact `scene-2-replacement.png` for the bounded replacement. Decode every required file in one preflight before any Provider-attempt record, workspace media write or Artifact commit; report only safe actionable basenames.
3. Convert imported stills locally with the existing shell-disabled FFmpeg/ffprobe path into H.264 `yuv420p` 540x960 24fps MP4 at each Scene duration. Budget approval remains required, but the local-processing marker has zero external charge and is not a ChatGPT Provider attempt.
4. Scene 2 replacement is visual-only: reuse the exact predecessor voice result and Scene Audio/Master Audio references, rebuild stale Video, and preserve all other Scene visual/audio selections. Missing or invalid replacement input changes no state.
5. Restart replays committed imported production/replacement/final/package state without reconversion. Package source attribution must retain the exact GitHub repository URL, commit SHA and units while adding only honest visual facts: creator-supplied via ChatGPT Desktop ImageGen, generated outside application, model version not verified by application, no application Provider API call, zero external charge and the selected replacement basename.
6. This decision does not select a real Visual/TTS Provider, authorize credentials or fees, or complete F2/F3 acceptance. It is candidate evidence for F2A only.

### Consequences

- `LocalImportedVisualGenerator` owns the exact-name/decode preflight and conversion policy behind the existing `VisualGenerator` interface.
- The three existing server-rendered views expose six frozen/copyable prompt cards; no upload manager, fourth page or SPA is introduced.
- The safe ledger token `local-import-operator-declared-external-source` is used for machine-readable facts; human wording appears in the UI and package attribution.
- Candidate completion still requires independent review of focused tests, one real local FFmpeg integration path and the full regression evidence.

### Rejected Alternatives

- **Infer files from Downloads/Desktop/latest:** rejected because it is nondeterministic and would make provenance and restart replay unverifiable.
- **Add a new Provider API or cloud SDK:** rejected because Desktop generation is outside the application and `PD-001` is still unresolved.
- **Generate a replacement voice/audio result:** rejected because F2A is a visual-only replacement and must preserve exact predecessor audio references.
