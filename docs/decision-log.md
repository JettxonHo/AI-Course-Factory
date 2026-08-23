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

1. Optimize remaining work for one fixed, browser-driven vertical Demo: source -> grounded Script approval -> planning -> Budget approval -> accepted creator-supplied visuals plus real/local TTS -> FFmpeg -> one Scene recovery -> Final approval -> export. (At decision time, the visual path was still to be selected.)
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
6. At decision time this did not select a real Visual/TTS Provider, authorize credentials or fees, or complete F2/F3 acceptance; subsequent Issue #117 / PR #118 independently accepted the F2A creator-supplied visual boundary. F2B local TTS and F3 acceptance remain separate.

### Consequences

- `LocalImportedVisualGenerator` owns the exact-name/decode preflight and conversion policy behind the existing `VisualGenerator` interface.
- The three existing server-rendered views expose six frozen/copyable prompt cards; no upload manager, fourth page or SPA is introduced.
- The safe ledger token `local-import-operator-declared-external-source` is used for machine-readable facts; human wording appears in the UI and package attribution.
- Candidate completion still requires independent review of focused tests, one real local FFmpeg integration path and the full regression evidence.

### Rejected Alternatives

- **Infer files from Downloads/Desktop/latest:** rejected because it is nondeterministic and would make provenance and restart replay unverifiable.
- **Add a new Provider API or cloud SDK:** rejected because Desktop generation is outside the application and `PD-001` is still unresolved.
- **Generate a replacement voice/audio result:** rejected because F2A is a visual-only replacement and must preserve exact predecessor audio references.

## Decision D-006 — PD-002 Local GPT-SoVITS v2 narration

| Field | Value |
| --- | --- |
| Status | Accepted for bounded F2B implementation |
| Decision Date | 2026-08-13 |
| Decision Owner | Product Owner |
| Applies To | Issue #119 / local GPT-SoVITS v2 TTS |
| Product Decision | `PD-002` |

### Context

F2A supplies six creator-generated Desktop ImageGen stills outside the application. The next vertical gap is real spoken narration without introducing cloud credentials, API fees or a heavy dependency into the project Python 3.12 environment.

### Decision

1. Use the official GPT-SoVITS v2 pretrained inference path through an explicitly configured external Python 3.11 environment, repository/model cache and exact repository commit.
2. Require an operator-configured reference WAV and exact transcript `你好，我是小土豆。今天我们一起认识人工智能。`; provenance is `locally generated Qwen3-TTS Serena synthetic reference`, not a user recording or application Provider call.
3. Invoke the official CLI with an argv list and shell disabled; do not start WebUI/API servers, train, upload or read credentials. Preflight Python, repository commit, model/config paths, reference decodeability and output/tool boundaries before the first attempt or media write.
4. Normalize generated narration with local shell-disabled FFmpeg to 48 kHz mono AAC/m4a, padding silence only when needed. Reject invalid or overlong speech without truncation or material speed-up.
5. Keep the existing VoiceGenerator, Workflow, Artifact, Budget and attempt contracts. Record six initial local GPT-SoVITS voice attempts with charged amount zero. Visual-only Scene 2 replacement reuses exact predecessor voice/Scene Audio/Master Audio and does not infer again.
6. Add TTS facts to package attribution while preserving GitHub source and F2A visual assets: engine/version, repo commit/model identifier, local runtime, reference provenance, `application_provider_api_call=false`, and `external_charge_micros=0`.
7. F2.5 remains a separate next milestone; F3 waits for independent F2B acceptance and the F2.5 outcome. F2A creator-supplied visuals already satisfy the FAST-MVP visual asset boundary; automatic cloud Visual Provider work is deferred.

### Consequences

- `GPTSoVITSSyntheticVoiceGenerator` owns runtime preflight, CLI invocation, output validation and normalization behind `VoiceGenerator`.
- The application accepts explicit TTS configuration and keeps the three server-rendered views; no upload manager, SPA or plugin framework is introduced.
- Model weights, reference audio, cache paths and generated binaries remain outside the repository.

## Decision D-007 — Warm Editorial Production Desk for F2.5

| Field | Value |
| --- | --- |
| Status | Accepted for bounded Issue #121 candidate implementation |
| Decision Date | 2026-08-14 |
| Decision Owner | Product Owner |
| Applies To | Exactly-three local server-rendered workspace views and local presentation assets |
| Source Decision | Issue #121 approved Warm Editorial Production Desk direction |

### Context

The F1/F2 workspace already exercises the durable facade and local production flow, but the three views make stage, provenance and the next human action compete for attention. F2.5 needs to improve the Creator's reading and decision experience without changing the accepted route, form, media, security or application view-model contracts.

### Decision

Keep the existing Start / Current Task, Review / Produce and Final / Export routes and server-rendered Jinja boundary. Apply a warm editorial presentation using a paper background, deep ink, one muted potato-gold accent, local serif heading and humanist sans body stacks, plus a self-hosted text SVG favicon. Derive a semantic Ground → Produce → Deliver track in Jinja from existing `stage`/`pending_action` facts, with one active `aria-current` step and completed/upcoming states. Make task, stage and one next action primary; keep source, budget, attempt, charge, Visual/TTS, version and package provenance compact but readable. Use native `<details>` prompt cards, a Review decision zone/storyboard grid, and a Final 9:16 player with a sticky desktop decision rail that collapses to one column on mobile. Use CSS-only 150–250ms polish with a reduced-motion override.

### Rejected Alternatives

#### Minimal reskin

Rejected because changing colors, type and spacing without a stage/next-action hierarchy would leave the central five-second comprehension problem unresolved. It would also keep provenance and action controls scattered across long panels.

#### SPA or frontend editor

Rejected because a client-side application, build system or editor would expand the public surface, duplicate the facade state and add new keyboard/security/testing failure modes. Drag-and-drop editing and upload management are outside the FAST-MVP product job; normal form posts and server-rendered refreshes are sufficient.

### Consequences

- Only the frozen templates, stylesheet, optional favicon, web presentation tests and approved current-truth docs change; no application/domain/repository/production/packaging code or dependency changes are needed.
- The existing autoescape, same-origin mutation boundary, security headers, POST action names, field names, media endpoints and provenance/fee facts remain authoritative.
- Presentation evidence is local UI evidence only. F2.5 stays candidate/in progress until independent rendered browser review and the required regression gates pass; F3 remains blocked on F2.5.

## Decision D-008 — Reposition near-term delivery around a Creator Handoff Package

| Field | Value |
| --- | --- |
| Status | Accepted; Creator Handoff MVP v1.2 Goal approved 2026-08-14 |
| Decision Date | 2026-08-14 |
| Decision Owner | Product Owner |
| Applies To | Creator Handoff MVP v1.2 Goal and later bounded implementation |
| Recording Task | Issue #129 (docs-only planning candidate) |

### Context

FAST-MVP v1.1 proved the exact public Source, grounded Script, local narration, Timeline/SRT, Scene selection, composition, Final Review and Publish Package chain. Its F2A still-image conversion also proved import, provenance, replacement and FFmpeg mechanics. It did not prove that six animated Scenes have the content quality, motion or visual rhythm expected of a publishable creator video; that output is therefore technical Preview evidence rather than the near-term product-quality result.

At the current low production frequency, the Creator prefers to iterate manually in the subscription interfaces of Jimeng or Kling instead of operating an application-owned API key, resource package and retry control plane. Those products can generate video from text/images and references; Kling can also generate native speech/audio. Their editable subtitle export cannot be assumed to be a stable SRT contract. Provider capabilities and prices may change, so this decision does not assert that an API is always more expensive.

### Canonical Terms

- **Scene Generation Contract** — one immutable, provider-neutral Artifact that binds the exact approved Script, Storyboard, Timeline and Production Request to ordered per-Scene visual intent, prompt, character/style continuity, camera/action instructions, duration and expected import identity.
- **Preview Video** — a locally composed technical/progress video, including the accepted F2A still-image path. It proves wiring and timing but does not satisfy the v1.2 product-quality gate.
- **Creator Handoff Package** — a deterministic, traceable package for manual Scene generation. It contains exact references, per-Scene generation instructions, narration audio, canonical SRT/Timeline and provenance; it is not the Final Publish Package.
- **Imported Generated Scene Clip** — a creator-supplied video bound to one exact Scene Generation Contract entry and explicit file selection, then locally validated/normalized and committed as the selected `scene_clip` Artifact without a fabricated Provider Attempt.
- **Final Video** — the locally composed Video built from the selected Imported Generated Scene Clips plus AI Course Factory's exact approved narration, canonical SRT and Timeline, then bound by the existing Final Video decision.

### Decision

1. Reposition the near-term product around `Source -> grounded Script -> Storyboard -> Scene Generation Contract -> exact narration/SRT -> Creator Handoff Package -> manual external Scene generation -> explicit Scene clip import -> local Final Video -> Final Review -> Publish Package`.
2. Keep manual Jimeng/Kling generation outside the application. It creates no Provider Attempt and no application charge; store creator-supplied provenance only.
3. Keep exact narration audio, SRT and Timeline application-owned. Native external audio, dialogue, subtitles or effects may be recorded as imported facts or future optional tracks, but they do not replace the canonical narration/SRT by default.
4. For the first vertical slice, accept one operator-declared generated-clips directory supplied at application startup/configuration. A Review-page POST triggers atomic full-set preflight/import of exact `scene-1.mp4` through `scene-6.mp4`; one Scene re-import uses exact `scene-2-replacement.mp4`. Never accept multipart upload, scan Downloads/Desktop, infer the newest file or guess an alternate Scene.
5. Preserve the existing Artifact repository, exact References, Script/Storyboard/Final decisions, Scene identities/Versions, Task selection/stale impact, FFmpeg composition behavior and Final Publish Package. H3 may add only the honest imported-clip payload/input and Final lineage expansions described below, after an approved Goal and bounded Task Contract.
6. Treat the F2A static-image path as Preview Video/technical evidence for v1.2. Preserve its completed v1.1 history rather than rewriting old acceptance.
7. A future `JimengVideoAdapter` or `KlingVideoAdapter` may consume the same Scene Generation Contract. Only application-controlled API execution enters the Budget Authorization and Provider Attempt path; Provider/model/credential/price/cap choices require a separate Product Owner decision.
8. Require human product-quality acceptance: a reviewer watches and listens to the complete result for claim fidelity, spoken naturalness, visual continuity/action and pacing. Codec, FFprobe, ASR and automated tests are necessary technical evidence, not substitutes for this gate.
9. The manual Creator Handoff path does not enter Budget Review. Local runtime/input readiness is a non-monetary preflight; the application explicitly states that external subscription cost is not controlled by AI Course Factory. Existing Budget/Attempt semantics remain for v1.1 Preview maintenance and future application-controlled paid APIs. Local narration must remain durable/idempotent without a fabricated monetary authorization; its exact persistence wiring is deferred to the H2 Task Contract.

### Stage and Ownership Consequences

- The Artifact repository owns immutable Scene Generation Contract, Handoff Package, imported Scene Clip and Final Video Versions.
- Existing Script and Storyboard Decision records own content/readiness choices; the existing Final Video Decision owns final approval. Package generation and clip import are not Decisions.
- Task state owns the current handoff/import stage plus selected/current/stale Scene and delivery references.
- The workspace owns configured input/output files; it never becomes the authority for Artifact identity.
- The existing Publish Package still consumes only an exact approved Final Video. The Creator Handoff Package is a separate earlier package with different eligibility and contents.
- `scene_clip` remains the Artifact type and retains its existing identity/version/Task-selection role, but gains a discriminated creator-import payload variant. That variant binds the exact Scene Generation Contract, Scene, declared filename, creator provenance and normalized output; it contains no fake `attempt_id` or `provider`.
- v1.2 Final Review resolves all six selected Scene Clip Versions and accepts only creator-import variants bound to the same exact Scene Generation Contract. Legacy generated/Preview payloads remain readable but cannot satisfy that gate.

### Rejected Alternatives

#### Keep the six-still composition as the final product-quality output

Rejected because it proves mechanics but does not establish animated content quality, action continuity or visual rhythm. Keeping the evidence is useful; representing it as final creator output is not.

#### Integrate Jimeng/Kling APIs now

Rejected for the near term because current manual iteration does not justify an application-owned credential, resource/cost control plane and retry semantics. This is a sequencing decision, not a claim that API prices are permanently higher.

#### Build a separate end-to-end creator workflow or overload the Final Publish Package

Rejected because a parallel workflow would duplicate accepted Source/Artifact/Decision/Task behavior, while overloading the final package would mix pre-generation instructions with post-approval delivery evidence. One additive handoff package and one explicit clip-import seam are smaller and clearer.

#### Reuse the attempt-shaped Scene Clip payload with placeholder provider fields

Rejected because the existing generated payload requires `attempt_id` and `provider`. Manual creator import has neither; inventing them would falsify provenance and weaken Budget/Attempt truth. The additive creator-import variant is the smallest honest compatibility expansion.

### Authorization Boundary

D-008 and the exact Creator Handoff MVP v1.2 Goal are approved. Issue #129 owns H0 documentation integration only; H1-H4 code still requires a bounded Task Contract and exact Luna dispatch per milestone. No Jimeng/Kling API/model/credential/price/cap, external fee, deployment or publication is authorized.

## Decision D-009 — Guided Creator Workbench in Simplified Chinese

| Field | Value |
| --- | --- |
| Status | Product Owner approved Direction A; H3.5 Issue #139 implementation in progress |
| Decision Date | 2026-08-15 |
| Decision Owner | Product Owner |
| Applies To | Exactly three local server-rendered Creator workspace views and their local presentation assets |
| Recording Task | Issue #139 |

### Context

H3 is complete at `main@cbdd150c` through Issue #137 / PR #138 with accepted 458-test regression evidence. The existing three-view workspace already exposes the H3 Scene Generation Contract, Handoff Package, explicit creator-import action and Final Review facts, but its English stage/action vocabulary and page-specific card stacks make the Creator workbench harder to orient. H3.5 needs a presentation-only information-architecture change while preserving H3 lineage, route and security behavior.

### Decision

1. Keep exactly the existing `/`, `/review` and `/final` server-rendered Jinja routes. Use fixed Simplified Chinese copy; do not add a language switch or i18n framework.
2. Use Direction A — a stable three-zone desktop workbench with compact phase navigation, a current-work canvas and a contextual status/action/evidence rail. On mobile, render status → current work → primary action → evidence in one column.
3. Derive presentation phases only from existing `stage`, `pending_action`, route and available facts. Map `source_required`/`script_review` to 内容定稿; `planning`/`handoff_readiness`/`external_generation_pending`/legacy `budget_review`/`production` to 制作与回导; and `final_review`/`exported`/`rejected`/final export to 终审交付. No public stage or backend/view-model seam is added.
4. Render one visual primary action for each actionable state. Reject, re-import and secondary downloads remain lower hierarchy. At `external_generation_pending`, make 导入 6 段场景视频 primary only when `available_actions` contains `import_generated_scene_clips`; otherwise make 下载创作交接包 primary. Never infer that a package was already downloaded.
5. Keep exact POST action values/fields, routes, media URLs, Jinja autoescape, same-origin mutation checks, security headers and every source, Artifact, narration, attempt, charge, provenance and failure fact. Use readable Chinese summaries plus semantic `details`/`aside` disclosures; raw internal tokens may appear only in the secondary 运行事实 disclosure when needed.
6. Keep the Warm Editorial paper/ink/potato-gold identity, local font stacks, local favicon and one local CSS stylesheet with visible focus, 44px targets, reduced-motion handling, long-content wrapping and a mobile breakpoint. No JavaScript, external resources, SPA, upload manager, fourth view, Provider/API/model/credential/fee/cap or H4 quality claim is authorized.

### Consequences

- H3.5 changes only the frozen templates, stylesheet, focused web compatibility tests and current-truth docs in the Issue #139 allowlist; application/domain/repository/production/package code remains untouched.
- The H3 contract remains the source of truth for imported Scene media and Final Review. This candidate's focused 30-test web evidence is local presentation/compatibility evidence only; independent browser review, full regression and merge remain with the main controller.

### Authorization Boundary

D-009 records the approved presentation direction for Issue #139. It does not mark H3.5 complete, authorize H4 human-quality acceptance, or authorize Provider/API calls, credentials, fees, deployment or publication.

## Decision D-010 — Rebaseline the primary path around a narration-led editorial spine

| Field | Value |
| --- | --- |
| Status | Accepted; exact v1.3 Goal approved and E0 activated on 2026-08-24 |
| Decision Date | 2026-08-24 |
| Decision Owner | Product Owner |
| Applies To | Approved Knowledge Video Editorial MVP v1.3 and Issue #143 E0 authority integration |
| Supersedes | D-008 only as the near-term primary production path; D-008/D-009 history and implementation evidence remain valid |

### Context

Creator Handoff v1.2 proved exact Source/Script lineage, local narration, a Scene Generation Contract, deterministic handoff files, creator-import lineage, local composition, restart/replay and a three-view Chinese workspace. Its H4 acceptance did not complete. Before external video credits were spent, product review found that the application still lacked a single narration clock and a human-reviewable editorial plan capable of controlling teaching evidence, A/B-roll choice and rhythm before full production.

The Product Owner chose a narration-led editorial workflow and explicitly parked the six-external-MP4 path. The MVP should use Codex Desktop ImageGen for creator-supplied static assets and deterministic local rendering for motion, graphics, camera and timing. Jimeng, Kling and Seedance may later enhance exceptional shots, but they are not the primary dependency.

### Decision

1. Make the approved grounded Script feed one continuous Whole Narration.
2. Make phrase-level millisecond Acoustic Alignment the sole continuous audiovisual timing authority and derive canonical SRT from it. After declared punctuation/whitespace normalization, its short phrase text covers exact approved narration character-for-character; non-overlapping intervals span `0` through exact audio duration under a declared pause-allocation policy. ASR may propose timestamps but cannot replace approved text.
3. Require a human-reviewable Visual Edit Plan bound to exact Script, narration and alignment facts. Every shot/range owns an A/B-roll role and rationale, evidence intent, selected assets or gaps, overlays and deterministic motion/camera instructions. A-roll is the Xiaotudou/IP presenter layer for hooks/transitions/emotion/action/low-density delivery; B-roll is the content/evidence layer. Information-dense or claim-bearing content defaults to evidence-bound B-roll unless an exception reason is recorded.
4. Keep static character/environment/prop/illustration/diagram/screenshot creation outside the application through Codex Desktop ImageGen for the MVP. Record creator-supplied provenance; create no application Provider Attempt, credential use or charge.
5. Put HyperFrames, or one separately justified equivalent, behind a small deterministic rendering boundary. No renderer installation or selection is authorized by this documentation task.
6. Require an exact 15–20 second Sample Video containing A-roll, B-roll, their transition and representative overlay/motion behavior, with approval before full rendering.
7. Reuse exact Source/Script, Artifact/Decision, Workspace, Final Review and Publish Package ownership. Keep the existing three SSR/Jinja views as a Human-in-the-loop control plane with responsibilities: Content & Audio; Visual Planning & Production; Final Review & Delivery.
8. Park manual Jimeng/Kling/Seedance six-clip generation/import as a future optional special-shot capability. Do not generate/import the seven H4 MP4 files or consume subscription credits for the proposed MVP.
9. Preserve D-008/D-009, H0–H3.5 implementation and H4 evidence as historical/foundation facts. Creator Handoff v1.2 is not retroactively marked complete.

### Rejected alternatives

#### Keep six fixed Scenes as the editorial clock

Rejected because separately rendered narration/visual clips and fixed ten-second slots create a competing clock and make phrase timing, evidence coverage and edit rhythm secondary.

#### Continue manual external video generation as the primary path

Rejected for the current MVP because it consumes scarce external iteration before the application has validated the narration, edit plan and sample. This does not remove the implemented import seam or prohibit a future special-shot enhancement.

#### Outsource the complete edit and import one final MP4

Rejected because the application would lose ownership of alignment, canonical SRT, edit lineage and the sample-before-full-render gate.

#### Replace Jinja with a frontend editor stack

Rejected because the product needs three review/control surfaces, not a professional timeline, asset manager, SPA or fourth page. React/Tailwind/shadcn references do not justify a stack rewrite.

### Consequences

- Whole Narration, Acoustic Alignment, Visual Edit Plan and Sample Video become the canonical v1.3 product facts.
- Existing per-Scene narration, Scene Generation Contract, Creator Handoff Package and imported clip facts remain backward-readable compatibility/foundation evidence but are no longer the v1.3 primary Final gate.
- Frontend design must follow the approved research sequence: 8–12 real references, 2–3 IA directions, Product Owner selection, `DESIGN.md`, implementation, then AI-Slop audit.
- Later implementation requires bounded Task Contracts for alignment, whole narration, plan approval, renderer evaluation/sample and full acceptance. A general Provider registry, API integration or broad Artifact/Workflow rewrite is not implied.

### Authorization boundary

The Product Owner approved the exact v1.3 Goal and E0 activation on 2026-08-24. Issue #143 therefore owns one nine-file authoritative docs PR including `GOAL.md`. E0 may commit/push/review/merge those docs and truthfully park the superseded H4 Issues after merge. No Luna dispatch, feature code, UI change, dependency install, HyperFrames/alignment run, Provider/API/model/credential/fee/cap action, external clip generation/import, deployment or publication is authorized.

Creator Handoff H4 remains PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE. Its exact six-file dirty candidate and repo-external evidence stay preserved for a later line-level salvage/compatibility review; E0 neither resets nor merges them. E1 becomes eligible for planning only after E0 actually merges and still requires an independently approved Task Contract before code or Luna dispatch.
