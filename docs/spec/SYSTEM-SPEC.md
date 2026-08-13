# AI Course Factory FAST-MVP System Spec v1.1

## 1. Status and Authority

| Field | Value |
| --- | --- |
| Status | Approved FAST-MVP System Baseline |
| Approval | Product Owner, 2026-08-13 |
| Product Input | `docs/product/PRD.md` |
| Accepted local baseline | `main@e155d193032aad6a9c98e1e8cbebd4e10febdbc6` plus Issue #123 acceptance evidence |
| Supersedes | System Spec v1.0 for daily development |

This document defines the smallest stable system that can deliver the approved product job. Physical files, libraries and task sequencing belong in the Implementation Spec and `GOAL.md`.

## 2. Architecture Principle

Build one local vertical product path. Reuse the existing Artifact, decision, workflow, budget, production, workspace and packaging capabilities behind one application-facing interface. Add a seam only when the MVP has a second real implementation or when it isolates an external side effect.

```text
Creator
  <-> Local Web Workspace
        -> Course Factory Application
             -> Source and Planning
             -> Artifact + Decision + Task State
             -> Budget + Production Orchestrator
                  -> Visual Adapter
                  -> TTS Adapter
                  -> FFmpeg Composer
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

## 4. Deep Module Boundaries

### Course Factory Application

Offers the task-level product operations needed by the workspace:

- create/open the Demo task;
- inspect the current stage, evidence, media and available actions;
- advance deterministic stages;
- submit Script, Storyboard, Budget and Final Video decisions;
- run authorized production;
- retry or replace one Scene;
- export the approved package.

It coordinates existing modules and returns a stable view model. It must not expose repository mechanics or Provider SDK types to the UI.

The F2.5 presentation keeps the workspace at exactly three server-rendered views and consumes the existing `ApplicationView` without a route or public-view-model expansion. A semantic Ground → Produce → Deliver track derives active/completed/upcoming state from the existing `stage` and `pending_action`. Start prioritizes the script and source evidence, Review prioritizes one decision zone plus consolidated production facts/storyboard, and Final pairs the playable 9:16 video with a desktop decision rail that becomes one column on mobile. Native details disclosure, local CSS and a self-hosted text favicon are presentation concerns; JavaScript, external assets, SPA/editor behavior and upload management remain out of scope.

### Source and Planning

Acquires the supported public GitHub source at an exact commit and produces grounded Knowledge, Script, Character, Storyboard, Timeline and a provider-neutral Production Request. Each downstream Artifact consumes exact committed upstream references.

### Artifact, Decision and Task State

Persists immutable Versions, exact human decisions and the one-task current projection. The current projection may select one media result per Scene and singleton delivery results. Updating one Scene selection preserves the others and makes only its exact derived delivery selections stale.

### Budget and Production Orchestrator

Accepts an exact Production Request, matching Budget Authorization, explicit Scene scope and idempotency key. It checks/reserves an attempt before the Provider call, records the result or uncertain failure, commits valid media and composes the selected set. It never calls a paid Adapter without sufficient remaining authorization.

### Provider and Composer Adapters

- Visual Adapter: one Scene visual task -> normalized Clip result.
- TTS Adapter: one Scene narration task -> normalized Audio result.
- FFmpeg Composer: ordered selected media + Timeline -> Video, SRT and media facts.

Provider-specific request/response objects stay inside the corresponding Adapter. Fake Adapters support offline development; exactly one real Adapter for each paid media role is sufficient for FAST-MVP.

The bounded F2A local-import Visual adapter is an explicit exception to the paid-provider path: it accepts only `scene-1.png` through `scene-6.png` from the operator-declared directory (and exact `scene-2-replacement.png` for the one visual replacement), decodes the complete set before any production side effect, then uses local FFmpeg/ffprobe to create playable clips. It does not search Downloads/Desktop, call a Visual Provider API or infer a latest file. Budget approval still gates the conversion, its charge is zero, and package attribution records the external source honestly.

The F2B local GPT-SoVITS adapter is a second bounded local implementation behind `VoiceGenerator`. It requires explicit external Python 3.11, official repository commit/model/config paths, exact reference audio/transcript and local FFmpeg tools; it performs complete preflight before the first attempt, invokes the official CLI with `shell=False`, normalizes narration to 48 kHz mono AAC/m4a and records zero external charge. It never starts a WebUI/API server, reads credentials or falls back to Fixture voice. F2A creator-supplied visuals remain the accepted visual asset boundary; automatic cloud Visual Provider work is deferred.

### Packaging

Consumes the exact approved Video and delivery evidence, then writes the local MP4/SRT/source/Manifest package. It does not regenerate media or publish externally.

## 5. Product State

```text
source
  -> script_review
  -> planning
  -> budget_review
  -> production
  -> final_review
  -> exported
```

A failure leaves the last valid checkpoint and exposes one actionable recovery. The workspace does not need a general-purpose workflow editor or a complete historical graph.

Mandatory gates:

| Gate | Exact target | Rule |
| --- | --- | --- |
| Script Review | Script Version | Approve/reject/revise; Hard Blocks prevent approve. |
| Budget Review | Production Request + budget facts | Required before any paid call. |
| Final Review | Video Version | Required before final export/completion. |

Storyboard review is optional for FAST-MVP; approve or skip is recorded.

## 6. Essential System Invariants

1. Source commit and factual teaching claim locators remain exact and inspectable.
2. Cross-stage consumption uses exact committed references.
3. Script and Final decisions bind the exact selected Version.
4. Budget approval binds the exact Production Request, price snapshot, amount and attempt limit.
5. The attempt is reserved before an external paid call; an uncertain result requires explicit recovery and cannot be blindly replayed.
6. Replacing one Scene preserves unaffected selected Scene media and invalidates only exact downstream delivery results.
7. Export uses the exact approved Video and produces a playable file plus required evidence.

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
- Require separate Product Owner approval for Provider selection, credentials, spend and deployment.

## 9. Verification by Risk

- Product flow: browser-driven offline end-to-end, then one authorized real/local-media end-to-end using the accepted F2A visual assets and F2B local TTS.
- Money/external effects: authorization, cap, attempt reservation and uncertain-retry tests.
- Data lineage: exact source/decision/media/export assertions.
- Scene recovery: one retry/replace integration test proving unaffected media is retained.
- F2A local visual import: six-image decode preflight, fixed playable conversion, visual-only replacement and restart/package replay evidence.
- Persistence: one process-restart continuation test.
- UI: primary-path and actionable-failure browser checks.

Issue #123 completed the fresh product-level run: exact Script v2 and Video v2 decisions, 12 zero-charge local attempts, playable 60-second H.264/AAC/mov_text output, visual-only Scene 2 replacement with preserved voice/audio/unaffected media, two restart replays and the exact four-file package. This closes the FAST-MVP verification target without changing the stable system contracts above.

Concurrency races, mutation campaigns, legacy-schema matrices and malformed-database suites are added only when a concrete change makes that risk part of the MVP path.

## 10. Deferred Architecture

Multi-user identity, distributed workers, multiple concurrent tasks, generic Artifact graph traversal, Provider routing/failover, plug-in marketplaces, cloud deployment and broad backward-compatibility frameworks are deferred until evidence shows the local MVP creates value.
