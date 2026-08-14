# AI Course Factory Creator Handoff System Spec v1.2

## 1. Status and Authority

| Field | Value |
| --- | --- |
| Status | Approved Creator Handoff System Baseline |
| Approval | Product Owner, 2026-08-14 |
| Product Input | `docs/product/PRD.md` |
| Planning baseline | `main@bb676a236a32eb9cc03ddca0e5bd71584791097c`; FAST-MVP v1.1 remains complete history |
| Goal contract | `docs/goals/CREATOR-HANDOFF-MVP-v1.2-PROPOSAL.md` |

This document defines the smallest stable system that can deliver the approved product job. Physical files, libraries and task sequencing belong in the Implementation Spec and `GOAL.md`.

## 2. Architecture Principle

Build one local vertical Creator Handoff path. Reuse the existing Artifact, Decision, Task media projection, narration, composition, Final Review and Publish Package capabilities. Add only the approved contract/package seam before manual generation and explicit imported Scene clip boundary afterward.

```text
Creator
  <-> Local Web Workspace
        -> Course Factory Application
             -> Source and Planning
             -> Scene Generation Contract
             -> Creator Handoff Package
                  -> manual Jimeng/Kling subscription UI (outside application)
             -> Explicit Imported Scene Clips
             -> Artifact + Decision + Task State
             -> TTS + FFmpeg Composer
             -> Final Review + Package Export
```

The UI calls only the Course Factory Application. It does not coordinate repositories, Agents or Provider SDKs itself.

## 3. Canonical Terms and Ownership

| Term | Meaning / owner |
| --- | --- |
| Artifact Version | Immutable committed business fact owned by the Artifact repository. |
| Artifact Reference | Exact address of one Artifact Version; no implicit `latest` across stages. |
| Decision | Creator action bound to one exact Script, Storyboard, Budget or Video target. |
| Task Snapshot | Application-owned current stage, selected exact references, pending action and recoverable failure. |
| Provider Attempt | One external execution/cost record owned by the attempt ledger. |
| Operator-declared visual import | Exact creator-supplied stills generated outside the application and converted locally; the import bridge records a zero-charge local-processing marker, not a cloud Provider call. |
| Scene Generation Contract | Immutable provider-neutral Artifact that binds exact approved planning references to ordered per-Scene prompt, continuity, camera/action, duration and expected import identity. |
| Preview Video | Technical/progress composition, including F2A still-image output; it is not v1.2 Final Video quality evidence. |
| Creator Handoff Package | Pre-generation deterministic package of exact references, Scene instructions, narration, SRT/Timeline and provenance; distinct from the Final Publish Package. |
| Imported Generated Scene Clip | Creator-supplied video committed as a discriminated `scene_clip` payload variant, bound to one exact Scene Generation Contract entry and containing no fabricated attempt/provider. |
| Final Video | Composition of exact selected imported Scene Clips with application-owned narration/SRT/Timeline, subject to the existing exact Final Video decision. |
| Scene | Smallest media production and retry unit. |
| Scene media selection | Current selected Clip and Audio references for one ordered Scene. |
| Delivery media selection | Current selected Subtitle, Master Audio, Video, Manifest or Package reference. |

Ownership remains separate:

- Agents propose Candidates; they do not commit, approve or call media Providers.
- The Artifact repository validates and commits immutable Versions.
- Decisions own human approval facts.
- Task state owns the current selection and stage, not Artifact payloads.
- The attempt ledger owns Provider execution and charge history.
- The Production Orchestrator owns execution order, not product approval.
- Manual external generation is creator activity, not a Provider Attempt or application charge. Future application-controlled API adapters return to the existing Budget/Attempt ownership.

## 4. Deep Module Boundaries

### Course Factory Application

Offers the task-level product operations needed by the workspace:

- create/open the Demo task;
- inspect the current stage, evidence, media and available actions;
- advance deterministic stages;
- submit Script, Storyboard and Final Video decisions; retain Budget decisions only for legacy Preview maintenance and future application-controlled paid APIs;
- run authorized production;
- retry or replace one Scene;
- export the Creator Handoff Package and expose its exact readiness/provenance;
- trigger import from the operator-declared generated-clips directory and show per-Scene import/current/stale state;
- export the approved package.

It coordinates existing modules and returns a stable view model. It must not expose repository mechanics or Provider SDK types to the UI.

The F2.5 presentation and approved H3.5 D-009 redesign keep the workspace at exactly three server-rendered views and consume the existing `ApplicationView` without a route or public-view-model expansion. A semantic three-phase track derives active/completed/upcoming state from the existing `stage` and `pending_action`, mapping fine-grained H3 states to readable Simplified-Chinese work statuses. Direction A uses compact phase navigation, a current-work main area and a contextual status/action/evidence rail on desktop, then status → work → primary action → evidence on mobile. Native details disclosure, local CSS and a self-hosted text favicon are presentation concerns; JavaScript, external assets, SPA/editor behavior and upload management remain out of scope.

The approved v1.2 workspace adds Handoff download, one Review-page full-set import/re-import trigger, readiness and product-quality review facts inside the existing three-view surface. H3.5 adds only the D-009 presentation hierarchy and fixed Simplified-Chinese copy; it does not add a route or public view-model seam. The generated-clips directory is supplied at application startup/configuration, not through the POST. It does not authorize multipart upload, a generic file manager, platform automation, a fourth page or H4 quality behavior.

### Source and Planning

Acquires the supported public GitHub source at an exact commit and produces grounded Knowledge, Script, Character, Storyboard, Timeline and a provider-neutral Production Request. Each downstream Artifact consumes exact committed upstream references.

### Artifact, Decision and Task State

Persists immutable Versions, exact human decisions and the one-task current projection. The current projection may select one media result per Scene and singleton delivery results. Updating one Scene selection preserves the others and makes only its exact derived delivery selections stale.

`scene_clip` keeps its existing Artifact type, per-Scene identity/version chain and Task-selection role. Its payload becomes a discriminated union: the legacy generated/Preview variant retains the current attempt/provider fields, while the creator-import variant binds exact Production Request and Scene Generation Contract References, `scene_id`, declared filename, creator provenance, normalized output, media type and duration, with no `attempt_id` or `provider`. Task selection and lineage validation must read both exact variants; compatibility does not make a Preview Clip eligible for v1.2 Final Review.

### Budget and Production Orchestrator

Accepts an exact Production Request, matching Budget Authorization, explicit Scene scope and idempotency key. It checks/reserves an attempt before the Provider call, records the result or uncertain failure, commits valid media and composes the selected set. It never calls a paid Adapter without sufficient remaining authorization.

This path remains authoritative for legacy Preview maintenance and future application-controlled paid API work. The v1.2 manual path does not enter Budget Review: manual Jimeng/Kling generation is not invoked by the Orchestrator, reserves no attempt and consumes no application Budget. Local TTS, handoff and import use non-monetary runtime/input preflight; the UI states that external subscription cost is not controlled by AI Course Factory. H2 must retain durable/idempotent local narration without fabricating Budget Authorization or weakening the paid-attempt contract; exact persistence wiring belongs to its later Task Contract.

### Scene Generation Contract and Creator Handoff Package

The Scene Generation Contract is an immutable Artifact derived from exact approved Script, Character, Storyboard, Timeline and Production Request references. Its ordered entries own provider-neutral generation instructions and expected import identity, not Provider SDK payloads.

The Creator Handoff Package consumes that contract plus exact narration, canonical SRT/Timeline and source/provenance facts. It is an immutable pre-generation package Artifact written through Workspace, not a Decision and not a Publish Package. An explicit Storyboard `approve` is the approved v1.2 readiness gate.

### Generated Scene Clip Import

The import boundary receives one operator-declared generated-clips directory at application startup/configuration. A Review-page POST first preflights the complete exact set `scene-1.mp4` through `scene-6.mp4`, then imports/commits it as one bounded action; exact `scene-2-replacement.mp4` is the only first-slice re-import filename. The POST carries no path or multipart file. The boundary never scans Downloads/Desktop, infers `latest`, calls a platform API or manufactures Provider Attempts.

Each imported Version uses the creator-import `scene_clip` payload variant. Its exact dependencies include the Production Request and Scene Generation Contract References. A full-set preflight failure creates no imported Clip, Task-selection or normalized-media side effect; a replacement failure preserves the prior selection.

External native dialogue/audio/subtitles/effects may be stored as provenance or optional unselected facts. The canonical final mix continues to use exact AI Course Factory narration, Scene Audio/Master Audio and SRT unless a later Product Owner decision changes that contract.

### Provider and Composer Adapters

- Visual Adapter: one Scene visual task -> normalized Clip result.
- TTS Adapter: one Scene narration task -> normalized Audio result.
- FFmpeg Composer: ordered selected media + Timeline -> Video, SRT and media facts. H3 adds an imported-clip input/reference variant so creator imports never pass through `MediaGenerationResult` with fake attempt/provider fields.

Provider-specific request/response objects stay inside the corresponding Adapter. Fake Adapters support offline development; exactly one real Adapter for each paid media role is sufficient for FAST-MVP.

The bounded F2A local-import Visual adapter is an explicit exception to the paid-provider path: it accepts only `scene-1.png` through `scene-6.png` from the operator-declared directory (and exact `scene-2-replacement.png` for the one visual replacement), decodes the complete set before any production side effect, then uses local FFmpeg/ffprobe to create playable clips. It does not search Downloads/Desktop, call a Visual Provider API or infer a latest file. Budget approval still gates the conversion, its charge is zero, and package attribution records the external source honestly.

The F2B local GPT-SoVITS adapter is a second bounded local implementation behind `VoiceGenerator`. It requires explicit external Python 3.11, official repository commit/model/config paths, exact reference audio/transcript and local FFmpeg tools; it performs complete preflight before the first attempt, invokes the official CLI with `shell=False`, normalizes narration to 48 kHz mono AAC/m4a and records zero external charge. It never starts a WebUI/API server, reads credentials or falls back to Fixture voice. F2A creator-supplied visuals remain the accepted visual asset boundary; automatic cloud Visual Provider work is deferred.

### Packaging

The Creator Handoff Package is produced before external Scene generation and cannot represent delivery completion. The existing Publish Package continues to consume the exact approved Final Video and delivery evidence, then writes local MP4/SRT/source/Manifest output. Neither package publishes externally.

## 5. Product State

```text
source
  -> script_review
  -> planning
  -> handoff_readiness
  -> narration_and_handoff
  -> external_generation_pending
  -> scene_clip_import
  -> final_composition
  -> final_review
  -> exported
```

A failure leaves the last valid checkpoint and exposes one actionable recovery. The workspace does not need a general-purpose workflow editor or a complete historical graph.

Mandatory gates:

| Gate | Exact target | Rule |
| --- | --- | --- |
| Script Review | Script Version | Approve/reject/revise; Hard Blocks prevent approve. |
| Handoff Readiness | Exact approved Script/Storyboard/Scene Generation Contract + local preflight | Requires Storyboard approve and non-monetary runtime/input readiness; it is not Budget Authorization. |
| Budget Review (legacy/future API only) | Production Request + budget facts | Required before an application-controlled paid call; not entered by the manual handoff path. |
| Final Review | Video Version | Required before final export/completion. |

Storyboard review was optional for FAST-MVP v1.1; approve or skip remains readable. The approved v1.2 Goal requires explicit Storyboard approval before Handoff export.

## 6. Essential System Invariants

1. Source commit and factual teaching claim locators remain exact and inspectable.
2. Cross-stage consumption uses exact committed references.
3. Script and Final decisions bind the exact selected Version.
4. When an application-controlled paid call exists, Budget approval binds the exact Production Request, price snapshot, amount and attempt limit; the manual v1.2 path creates no such authorization.
5. The attempt is reserved before an external paid call; an uncertain result requires explicit recovery and cannot be blindly replayed.
6. Replacing one Scene preserves unaffected selected Scene media and invalidates only exact downstream delivery results.
7. Export uses the exact approved Video and produces a playable file plus required evidence.
8. Manual external generation creates no Provider Attempt or application charge; future application-controlled API generation requires the existing Budget/Attempt gates.
9. A Preview Video cannot satisfy the v1.2 Final Video quality gate; Final composition consumes exact selected Imported Generated Scene Clips plus canonical narration/SRT.
10. Before v1.2 Final Review, the gate resolves all six selected Scene Clip Versions and requires the creator-import variant for each exact Scene, all bound to the same exact Scene Generation Contract. Legacy Preview payloads remain readable but ineligible.

These are product invariants, not a requirement to build a general dependency graph, distributed transaction system or universal corruption detector.

## 7. Failure and Recovery Contract

User-facing failures use four categories:

- `provider_error`: external service/configuration failure;
- `generation_failure`: no valid media result;
- `quality_failure`: media exists but requires Creator action;
- `budget_limit`: next paid action is unauthorized.

For a known safe failure, the workspace may offer bounded retry. For an uncertain paid attempt, it shows the attempt and requires reconciliation or explicit human action. Restart must restore the one Demo task, decisions, selected media and next action; multi-process coordination and arbitrary hostile-database repair are outside FAST-MVP.

## 8. Security and Side Effects

- Bind the local UI to loopback by default.
- Keep credentials outside repository and Artifact payloads.
- Limit reads/writes to the configured source checkout and task workspace.
- Validate user-provided URLs and workspace-relative paths at the real trust boundary.
- Require an explicit visual import directory for F2A; accept no implicit Downloads/Desktop/latest-file inference and expose only safe input basenames in failures.
- Require an explicit generated-clip import directory/file selection and exact manifest/Scene binding; do not scan common folders or infer a newest clip.
- Require separate Product Owner approval for Provider selection, credentials, spend and deployment.

## 9. Verification by Risk

- Product flow: browser-driven Source-to-Handoff-to-import-to-Final path using creator-generated Scene videos and the accepted local TTS.
- Money/external effects: authorization, cap, attempt reservation and uncertain-retry tests.
- Data lineage: exact source/decision/media/export assertions.
- Scene recovery: one retry/replace integration test proving unaffected media is retained.
- Preview path: retain F2A image/decode/FFmpeg checks as technical evidence without treating it as final-quality acceptance.
- Handoff/import: deterministic handoff contents, explicit no-attempt manual provenance, exact Scene/file binding, one-Scene re-import and restart/package replay.
- Human quality: full normal-speed watch/listen verdict for grounded content, narration naturalness/completeness, visual action/continuity and edit rhythm; FFprobe/ASR remain supporting checks only.
- Persistence: one process-restart continuation test.
- UI: primary-path and actionable-failure browser checks.

Issue #123 / PR #124 supplied partial product-level media evidence but did not prove the browser-submitted URL and default live GitHub acquisition. Issue #125 corrected that boundary and repeated the full same-task flow: a live immutable GitHub source, exact Script v2 and Video v2 decisions, 12 zero-charge local attempts, playable 60-second H.264/AAC/mov_text output, visual-only Scene 2 replacement with preserved voice/audio/unaffected media, two restart replays and the exact four-file package.

Concurrency races, mutation campaigns, legacy-schema matrices and malformed-database suites are added only when a concrete change makes that risk part of the MVP path.

## 10. Deferred Architecture

Jimeng/Kling API adapters, Provider routing/failover, native external track selection, multi-user identity, distributed workers, multiple concurrent tasks, generic Artifact graph traversal, plug-in marketplaces, cloud deployment and broad backward-compatibility frameworks remain deferred until separate decisions and product evidence justify them.

This architecture is approved by the active v1.2 Goal. H0-H3 are complete through their bounded contracts; H3.5 Issue #139 is the active presentation-only Task Contract under D-009, and H4 still requires its own bounded Task Contract and independent review.
