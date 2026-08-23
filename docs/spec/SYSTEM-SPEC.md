# AI Course Factory Knowledge Video Editorial System Spec v1.3

## 1. Status and authority

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE GOAL — E0 DOCS ONLY; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Approved by Product Owner, 2026-08-24 |
| Exact Goal | Approved by Product Owner on 2026-08-24 |
| Product input | docs/product/PRD.md |
| Planning baseline | main@d301efd8494029e8b8eae5001050974a67778937 |
| Proposal | docs/goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-PROPOSAL.md |

This document records approved v1.3 ownership and gates. E0 changes documentation only; it does not change public interfaces, schemas, stages or dependencies.

`GOAL.md` now records v1.3 as APPROVED / ACTIVE with E0 docs-only IN PROGRESS. Creator Handoff H4 remains PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE. E1 feature implementation remains blocked on E0 merge and a separately approved Task Contract.

## 2. Architecture principle

Reuse accepted truth owners and insert the smallest editorial spine:

~~~text
Creator
  <-> three-view local SSR workspace
        -> Course Factory Application
             -> exact Source + grounded Script + Script Decision
             -> Whole Narration
             -> Acoustic Alignment -> canonical SRT
             -> Visual Edit Plan + Plan Decision
             -> creator-supplied static assets
             -> deterministic Sample Render + Sample Decision
             -> deterministic Full Render
             -> Final Video Decision
             -> Publish Package
        -> Artifact/Decision/Task repositories + local Workspace
~~~

The application remains the only coordinator. The UI never reads repositories or controls renderer/provider SDKs directly. External static-asset creation is creator activity, not an application call.

## 3. Canonical ownership

| Term | Meaning and owner |
| --- | --- |
| Artifact Version/Reference | Immutable business fact/exact address owned by the Artifact repository. No implicit latest. |
| Decision | Human action bound to one exact Script, Visual Edit Plan, Sample Video or Final Video target. |
| Task Snapshot | Current product checkpoint, exact selected refs, pending action and recoverable safe failure. |
| Whole Narration | One continuous audio Artifact for the exact approved Script. |
| Acoustic Alignment | Ordered short-phrase millisecond Artifact whose normalized text covers exact approved narration character-for-character and whose contiguous intervals span the Whole Narration from `0` to exact duration; sole audiovisual clock. |
| Visual Edit Plan | Ordered editorial Artifact bound to Script/Narration/Alignment; every shot/range records A-roll or B-roll plus rationale, evidence, assets/gaps, overlay and motion facts. |
| Creator Static Asset | Explicit creator-supplied character, environment, prop, illustration, diagram or screenshot fact with exact provenance; no Provider Attempt/charge. |
| Deterministic Render Input | Exact committed narration/alignment/approved plan/assets supplied to the renderer. |
| Sample Video | Exact 15–20 second render Artifact requiring a human decision before full render. |
| Final Video | Full deterministic render from the approved lineage, subject to Final Video Decision. |
| Publish Package | Post-approval delivery and provenance package. |

Ownership separation:

- Source/Knowledge planning owns factual grounding.
- Script Decision owns the content gate.
- Narration rendering owns audio bytes, not timing decisions.
- Alignment owns all audiovisual timing and canonical subtitle intervals.
- Visual Edit Plan owns editorial intent, not media bytes.
- Asset intake/provenance owns selected creator inputs, not provider execution.
- Deterministic renderer owns media execution, not approval or lineage.
- Artifact repository commits immutable outputs.
- Decisions own human approvals/returns.
- Task state owns current selected refs/checkpoint.
- Publish builder consumes only exact approved Final lineage.

## 4. Deep module boundaries

### Course Factory Application

Approved responsibilities:

- create/open/inspect the one local task;
- coordinate exact Source and Script decisions;
- request/replay Whole Narration;
- request/inspect Acoustic Alignment and canonical SRT;
- propose and submit exact Visual Edit Plan decisions;
- expose explicit creator asset readiness/provenance;
- request Sample Video only after plan approval;
- submit Sample decision and request full render only after approval;
- submit Final Video decision and export the package;
- restore exact current facts after restart.

It returns presentation values rather than repository/runtime/provider types. Later Task Contracts must choose the smallest additive view fields and operations; this proposal does not freeze method names.

### Source and Script

The existing exact public GitHub connector, normalized Source Record, Knowledge claims and Script Decision semantics remain authoritative. Protected H4 source-grounded content corrections are retained for later disposition, not silently copied or discarded.

### Whole Narration

Whole Narration is one audio Artifact derived from the exact approved Script and explicit local runtime/reference facts. It is generated once per exact input binding and replayed durably. The existing GPT-SoVITS boundary may be deepened only after a focused Task proves continuous narration quality, duration and failure behavior without pulling the heavy runtime into core Python 3.12.

Per-Scene narration Artifacts remain readable v1.2 facts but cannot satisfy the Whole Narration contract by concatenation or relabelling without an explicitly accepted compatibility rule.

### Acoustic Alignment

Alignment consumes exact approved Script text plus Whole Narration and returns ordered phrases with start/end milliseconds and exact text identity. It:

- after one declared punctuation/whitespace normalization, covers the approved narration character-for-character in order;
- defaults Chinese boundaries to 5–15 Han characters or an equivalent short phrase, subject to later engine-task validation, and cannot collapse to sentence/paragraph granularity;
- uses nonnegative, strictly ordered, non-overlapping intervals;
- is continuous: first start `0`, every prior end equals the next start, and final end equals exact audio duration;
- assigns engine-reported leading/trailing silence and gaps to adjacent phrases under a declared pause-allocation policy;
- owns canonical SRT timing;
- exposes confidence/quality evidence only as supporting facts;
- may use ASR for timestamp candidates but always uses approved Script narration as displayed text.

Text, interval, continuity, duration or derived-SRT validation failure commits no accepted Alignment and does not open Visual Edit Plan.

The alignment runtime remains an implementation decision for a later bounded Task. Cloud credentials/fees are not authorized.

### Visual Edit Plan

The plan consumes exact Script, Whole Narration and Acoustic Alignment. Every aligned shot/range is covered by ordered editorial instructions:

- A-roll or B-roll role plus the editorial reason;
- teaching evidence intent and claim links;
- creator static asset reference or explicit gap;
- overlay copy/fact and placement intent;
- camera, motion, graphics, transition and hold intent;
- continuity/style constraints.

A-roll is the Xiaotudou/IP presenter layer for hooks, transitions, emotion, physical action and low-information-density spoken delivery. B-roll is the content/evidence layer for concepts, steps, comparisons, processes, charts, source evidence, screenshots and demonstrations. Claim-bearing or information-dense content defaults to B-roll unless an exception reason is recorded. B-roll is never decorative filler: it binds exact narration/alignment and teaching evidence/claims.

A human Decision binds the exact plan before rendering. The plan is not a frontend timeline model and does not embed renderer component trees or Provider request bodies.

### Creator Static Assets

Codex Desktop ImageGen produces creator-owned assets outside the application for the MVP. An eventual bounded intake seam must accept only explicit files/manifest facts, validate them before commit and record provenance/hashes without scanning Desktop/Downloads/latest. It creates no Provider Attempt, Budget Authorization, credential use or charge.

A future ImageGenerationTask → ImageGenerationResult Adapter requires separate Provider/model/credential/price/cap approval and must not become a generic registry.

### Deterministic renderer

The renderer consumes only committed exact Deterministic Render Input. It produces:

- one declared 15–20 second Sample Video from an exact plan range containing at least one A-roll segment, one B-roll segment, their transition and representative overlay/motion behavior;
- one full Final Video after exact Sample approval.

HyperFrames is the preferred evaluation candidate; an equivalent can be chosen only through evidence against the same boundary. Renderer-specific composition trees, motion libraries and CLI details stay inside the adapter/module. No installation or dependency choice occurs in E0.

The renderer never owns Narration, Alignment, SRT or human decisions. Local FFmpeg remains the normalization/package delivery boundary where appropriate.

### Artifact, Decision and Task state

The generic Artifact repository remains unchanged by default. Later Tasks may add exact Artifact types/payload validators only for observed vertical needs.

At minimum, product truth must preserve exact references among:

~~~text
Source -> Script -> Whole Narration -> Acoustic Alignment
       -> Visual Edit Plan -> Sample Video -> Final Video -> Publish Package
~~~

with selected Creator Static Assets referenced by the Plan/Render input. Decisions bind Script, Plan, Sample and Final targets. Task state selects current refs and one next human action.

No generic graph engine, implicit latest lookup, parallel workflow or broad schema migration is implied.

### Three-view workspace

Exactly three local Jinja views remain:

1. Content & Audio;
2. Visual Planning & Production;
3. Final Review & Delivery.

Each state shows one primary human action and progressively discloses evidence. The UI does not become an editor, asset manager or dashboard. Current same-origin POST handling, autoescape, loopback default, security headers, accessible focus/targets and mobile one-column behavior remain essential.

### Packaging

Publish Package remains post-Final-approval delivery. It must add exact Whole Narration/Alignment/Edit Plan/Sample/asset provenance to existing Source/Script/Final facts. Creator Handoff Package remains a readable historical pre-generation package and is not overloaded as the v1.3 delivery package.

## 5. Conceptual product checkpoints

These names describe product gates only; they are not approved public stage/schema values:

~~~text
source intake
  -> script review
  -> narration readiness
  -> alignment review
  -> visual edit review
  -> sample review
  -> full render
  -> final review
  -> exported
~~~

Mandatory gates:

| Gate | Exact target | Rule |
| --- | --- | --- |
| Script Review | Script Version | Grounded exact approve/reject/revise. |
| Alignment Readiness | Whole Narration + Acoustic Alignment | Exact text/time/audio binding; no visual plan before accepted readiness. |
| Visual Edit Review | Visual Edit Plan Version | Human approval before sample rendering. |
| Sample Review | Sample Video Version + exact plan range | Human approval before full rendering. |
| Final Review | Final Video Version | Named-human normal-speed findings before export. |

Paid Budget Review remains only for separately authorized application-controlled calls. The proposed local/static/deterministic path creates no Budget Authorization or Provider Attempt.

## 6. Essential invariants

1. Source and teaching claim locators remain exact.
2. Cross-stage consumption uses committed exact References.
3. Script/Plan/Sample/Final decisions bind exact targets.
4. Whole Narration is one continuous audio fact for one exact approved Script.
5. Acoustic Alignment is the only audiovisual clock and canonical SRT timing source: normalized exact text coverage and contiguous non-overlapping intervals span `0` through exact audio duration.
6. Visual Edit Plan covers every aligned shot/range, records A/B-roll rationale, defaults claim-bearing/information-dense content to evidence-bound B-roll and keeps every selected asset explicit/provenanced.
7. Full render cannot start before Sample approval.
8. Final Video derives from the same approved plan/alignment/assets as the sample lineage.
9. Creator static assets and local deterministic rendering create no Provider Attempt or application charge.
10. Historical v1.2 media remains readable but cannot satisfy v1.3 gates.

## 7. Failure and recovery

- Validation/runtime failures preserve the last accepted checkpoint and exact refs.
- Failed narration creates no accepted narration or alignment.
- Failed alignment or derived-SRT validation creates no accepted Alignment, plan or SRT timing.
- Failed asset/preflight/sample/full render does not replace accepted upstream selections.
- A returned Sample leaves full rendering unavailable.
- GET/refresh remains read-only and does not invoke narration/alignment/rendering.
- Restart replays accepted bytes/facts without repeating costly local work.

User-facing failures remain safe and actionable. This proposal does not authorize a generic recovery, corruption or concurrency framework.

## 8. Security and external effects

- Bind UI to loopback by default.
- Keep runtimes/assets under explicit operator configuration and task workspace boundaries.
- Do not scan common folders or infer latest assets.
- Use argv/shell-disabled subprocess execution for local tools.
- Keep model/runtime caches, generated assets/media and evidence outside the repository.
- Make no video-generation API call or subscription-credit action.
- Require separate Product Owner approval for Provider/model/credentials/fees/cap/deployment.

## 9. Compatibility and parked paths

- D-008 Scene Generation Contract, Creator Handoff Package and H3 creator-import facts remain readable.
- The six-MP4 plus Scene-2 replacement flow is PARKED as a primary Goal, not deleted.
- v1.2 per-Scene narration and fixed Timeline remain historical/compatibility facts.
- The protected H4 dirty candidate remains intact pending line-level reuse/compatibility/park disposition after Goal approval.
- No migration, cleanup or Issue closure is implied by this proposal.

## 10. Verification by risk

- Source/lineage: exact reference/locator tests.
- Whole Narration: audio validity, exact binding, failure and restart replay.
- Alignment: exact text coverage, monotonic millisecond bounds, duration/SRT derivation and human inspection.
- Plan: exact interval coverage, evidence/assets, human decision and replay.
- Renderer: exact committed input, sample-before-full denial, deterministic replay and playable media.
- UI: three-view route/form/security/accessibility and one-primary-action browser checks.
- Product quality: named-human full normal-speed watch/listen; automation cannot substitute.

## 11. Deferred architecture

Cloud image/video generation, Provider registry/routing, multi-user/task, professional editor, generic asset manager, distributed rendering, new frontend stack, deployment/publication and broad graph/schema rewrites remain deferred.

The exact Goal is approved and active. Issue #143 is E0 documentation only; its merge and E0 completion are not prewritten, and no E1 implementation is authorized.
