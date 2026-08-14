# Creator Handoff MVP v1.2 Approved Goal Contract

## 1. Contract State

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE** |
| Product direction | Accepted by Product Owner on 2026-08-14 |
| Exact Goal approval | Product Owner, 2026-08-14 |
| Planning baseline | `main@d96b091b5d6486129487f5b51b0bb1c43b64639b` (H0 merged through Issue #129 / PR #130) |
| Planning Issue | #129 (closed); H1 implementation #131 / PR #132 plus correction #133 / PR #134 merged at `main@91b4512`; H2 Issue #135 / PR #136 is complete at `main@c4f2f5e` |
| Current H3 candidate | Issue #137 on `codex/137-generated-scene-import`, based on `main@c4f2f5e07839f9dee87e0c13cdfaf84500c3b629` |
| Preserves | FAST-MVP v1.1 `COMPLETE / GOAL_APPROVED` history |

This file records the approved contract behind the active `GOAL.md`. H2 is complete through Issue #135 / PR #136 with accepted 444-test regression evidence; H3 is in progress only under Issue #137. H3.5 and H4 remain separately gated, and this file does not reopen FAST-MVP v1.1.

## 2. Approved Exact Goal

Deliver one local Creator Handoff flow that turns the supported public GitHub source into an exact, human-reviewable Scene Generation Contract and Creator Handoff Package; accepts creator-generated Scene videos from one operator-declared directory through an explicit browser import action; composes those clips with AI Course Factory's exact narration, SRT and Timeline; and produces a human-approved Final Video and traceable Publish Package.

Success is not merely a playable file. A human must confirm that the teaching content is correct, the narration is natural and fully heard, the visual actions and continuity fit each Scene, and the edit has credible rhythm at normal playback speed.

## 3. Current Contract Audit

### Reuse without reopening

| Existing contract | Reuse in v1.2 |
| --- | --- |
| Live GitHub Source Record and Knowledge grounding | Preserve exact repository, commit, blob and claim locators. |
| Script/Storyboard/Timeline/Production Request Artifacts | Inputs to one provider-neutral Scene Generation Contract. |
| Script, Storyboard and Final Video Decisions | Preserve exact-Version human bindings; do not invent package/import decisions. |
| Generic immutable Artifact repository | Commit additive Scene Generation Contract/Handoff Package facts and imported Scene Clip Versions. |
| GPT-SoVITS narration, Scene Audio, Master Audio and canonical SRT | Keep as application-owned audio/text truth. |
| Task media projection | Retain the existing Scene Clip identity/version slots and stale impact; add acceptance of a discriminated creator-import payload. |
| FFmpeg composer | Reuse normalization/composition behavior after adding an honest imported-clip input variant that does not require attempt/provider fields. |
| Final Review and Publish Package | Preserve the exact approved-Video/export decision, while expanding the v1.2 gate to resolve and validate all selected imported Clip Versions. |
| Warm Editorial three-view workspace | Extend only the steps needed to prepare/download handoff, import clips and review the final result. |

### Real conflicts to resolve

1. **Visual outcome semantics:** F2A still-image clips currently enter the same Video/Final path. In v1.2 they must be labelled Preview Video and cannot satisfy the product-quality acceptance gate.
2. **Package eligibility:** `PublishPackageBuilder` consumes an exact approved Final Video. A pre-generation Creator Handoff Package has different inputs and cannot be a mode flag on the same package without weakening stage meaning.
3. **Attempt semantics:** manual Jimeng/Kling work is creator activity outside the application, not a Provider Attempt, retry or application charge.
4. **Import binding:** the accepted still-image adapter owns image decode/conversion. Generated video import needs a separate explicit Scene-clip boundary; overloading the image adapter would blur input and output contracts.
5. **Acceptance evidence:** v1.1 automated media/ASR/FFprobe checks are technical gates. v1.2 needs a recorded human content, listening and visual-rhythm verdict.
6. **Budget-stage meaning:** the current Demo gates local media work behind Budget review, while the manual subscription path creates no application Attempt or charge. v1.2 must remove Budget Authorization from the manual handoff path and use non-monetary runtime/input readiness instead; otherwise the UI would imply control over external subscription spend that the application does not have. H2 must also preserve durable/idempotent local narration without forging a monetary authorization or weakening the paid-attempt invariant.
7. **Scene Clip truth:** the existing generated `scene_clip` payload and composition input require `attempt_id` and `provider`, and Final Review currently validates only referenced Clip identity. Manual imports need a discriminated no-attempt payload plus a Final gate that proves all six selected Clip Versions are creator imports for one exact Scene Generation Contract.

## 4. Vertical Options

### Selected Option A — Additive Handoff Package plus Imported Scene Clip boundary

Add one immutable Scene Generation Contract, one adjacent Creator Handoff Package builder and one explicit local Imported Scene Clip boundary. Keep `artifact_type=scene_clip`, existing identities/Versions and Task selection, but add a discriminated creator-import payload, an honest imported-clip composition input and a v1.2 Final lineage gate. The existing Final Video decision and Publish Package remain downstream owners.

**Advantages:** deepest reuse, clear pre-generation versus post-approval package semantics, no parallel workflow, future API adapters can consume the same Scene Generation Contract.

**Cost:** adds two meaningful product seams and two application stages, plus a bounded public-contract expansion in Scene Clip payload validation, composition input and Final Review. Focused compatibility tests must keep v1.1 generated/Preview facts readable while excluding them from the v1.2 final-quality gate.

### Option B — Add handoff/import modes to Production Request, current Visual adapter and Publish Package

Use mode flags on current media and packaging interfaces so the existing Visual path either converts stills, imports generated clips or emits a handoff ZIP.

**Advantages:** fewer new module names initially.

**Rejected:** makes one adapter accept unrelated input types, makes one package mean both pre-generation instructions and post-approval delivery, and increases observable mode combinations across already accepted interfaces.

### Option C — Separate Creator Handoff workflow and artifact graph

Create a new end-to-end workflow from Storyboard approval through external generation/import, with its own persistence and package lifecycle.

**Advantages:** explicit isolation and room for future multi-provider orchestration.

**Rejected:** duplicates current Task stage, Artifact, Scene selection, recovery and Final Review behavior before evidence justifies a second workflow.

## 5. Approved Contract-First Shape

### Scene Generation Contract

One immutable ordered Artifact derived from exact:

- approved Script Version and its source/claim lineage;
- Character and Storyboard Version plus recorded Storyboard decision;
- Timeline and provider-neutral Production Request Version;
- per-Scene `scene_id`, duration, narration identity, visual intent/action, generation prompt, character/style continuity, camera/motion instruction, negative constraints and expected import filename.

It contains no Jimeng/Kling request body and no credential/price facts. Manual and future API generation consume the same contract.

### Creator Handoff Package

One deterministic package Artifact plus workspace ZIP. Approved contents:

1. `generation-guide.md` — global continuity plus readable per-Scene prompt/camera/action instructions;
2. `scene-generation-contract.json` and `timeline.json` — exact planning facts;
3. `subtitles.srt` and `narration/scene-1.m4a` through `scene-6.m4a` — canonical application-owned narration/text;
4. `provenance.json`, `reference-stills/README.md` and optional labelled `reference-stills/scene-1.png` through `scene-6.png`;
5. `handoff-manifest.json` — deterministic file facts and hashes.

The Handoff Package does not contain or imply an approved Final Video and cannot satisfy the final Publish Package gate.

### Imported Generated Scene Clip

- The operator supplies one generated-clips directory through explicit application startup/configuration. The Review page exposes one POST action that first preflights the complete exact set `scene-1.mp4` through `scene-6.mp4`, then imports it atomically. It does not accept multipart upload, a per-request path, Downloads/Desktop/latest scanning or filename guessing.
- One Scene re-import uses exact `scene-2-replacement.mp4` from the same configured directory and preflights it before changing Artifact/Task state.
- Keep `artifact_type=scene_clip` and the existing per-Scene identity/version chain. Add an exact creator-import variant with at least `source_kind="creator_import"`, `production_request_reference`, `scene_generation_contract_reference`, `scene_id`, `declared_filename`, creator-supplied provenance, normalized `output_reference`, `media_type` and `duration_milliseconds`.
- The creator-import variant contains no `attempt_id` or `provider`. Its exact Artifact dependencies include the Production Request and Scene Generation Contract References. Manual import creates no Provider Attempt or application charge.
- Local normalization strips/ignores native audio for the canonical mix. Composition consumes an additive imported-clip input/reference variant rather than constructing `MediaGenerationResult` with invented attempt/provider values.
- Re-import creates a new same-identity Scene Clip Version, preserves unaffected Scene selections and makes only exact downstream Video/Manifest/Publish Package selections stale.
- Task selection/lineage accepts both the legacy generated/Preview shape and the new creator-import shape. Compatibility is for reading/selection only: legacy Preview facts cannot satisfy the v1.2 final-quality gate.

### Final Video

The composition path consumes the ordered selected Imported Generated Scene Clips, exact Scene Audio/Master Audio, canonical Subtitle and Timeline. Before a v1.2 Final candidate can enter Final Review, the gate resolves all six selected Scene Clip Versions and requires each to be the creator-import variant, bound to its exact Scene and the same exact Scene Generation Contract. The existing Final Video decision then binds the resulting Video Version; only that approved Version may enter the existing Publish Package.

## 6. Approved Milestones

### H0 — Truth rebaseline

**Outcome:** integrate the approved D-008, v1.2 Goal and contract/acceptance boundaries while preserving v1.1 history.

**Exit:** Issue #129's exact docs Diff merged through PR #130 at `main@d96b091`; H0 is `COMPLETE` and H1 was `READY` from that real merged baseline.

### H1 — Grounded Script, Storyboard and Scene Generation Contract

**Outcome:** the browser exposes the exact grounded Script/Storyboard and a human-reviewable ordered generation contract with prompt, continuity, camera/action, duration and filename for every Scene.

**Exit:** exact lineage is committed after an explicit Storyboard `approve`; prompts contain no platform SDK payload. Issue #131 / PR #132 plus Issue #133 / PR #134 are merged at `main@91b4512`; H1 is complete.

### H2 — Creator Handoff Package

**Outcome:** after non-monetary local runtime/input readiness, the Creator downloads the deterministic handoff ZIP with instructions, exact narration, SRT, manifest and provenance, then can work manually in Jimeng/Kling. No Budget Authorization represents that subscription activity. The H2 Task Contract must make local narration durable/idempotent without routing it through a fabricated monetary authorization.

**Exit:** package replay is byte-stable; manual generation creates no Provider Attempt or charge; package facts do not masquerade as Final delivery.

H2 status: **COMPLETE** (Issue #135 / PR #136; `main@c4f2f5e`; accepted 444-test regression).

### H3 — Imported Scene clips and exact local composition

**Outcome:** with one operator-declared directory, the Creator triggers full-set import of exact `scene-1.mp4` through `scene-6.mp4`; the system validates exact Scene/contract/timeline binding and composes them with canonical narration/SRT into a Final Video candidate. Exact `scene-2-replacement.mp4` supports one Scene re-import while preserving all unaffected media.

**Exit:** imported clip provenance is visible; no implicit directory scan occurs; exact references drive composition and stale impact.

H3 status: **IN PROGRESS** (Issue #137 candidate; independent review and merge remain pending).

### H3.5 — Simplified-Chinese Creator workspace

**Outcome:** separately redesign the three-view Creator workspace for the approved Simplified-Chinese product experience while preserving H3 lineage, Final gate and three-route boundaries.

**Exit:** the separately approved workspace design and browser evidence pass; H3.5 does not authorize Provider/API, upload or H4 human-quality scope.

### H4 — Browser acceptance and product-quality gate

**Outcome:** one fresh browser flow completes Source -> Handoff -> manual external generation -> import -> Final Review -> Publish Package, including restart/replay.

**Exit:** technical gates pass and a named human reviewer watches/listens to the full result at normal speed, records content/listening/visual-rhythm findings, and approves the exact Final Video Version.

Frontend work is limited to the controls and evidence needed for handoff download, clip import/status and final review. H0-H4 do not authorize a general redesign, fourth page, SPA, timeline editor or upload manager.

## 7. Product-Quality Acceptance

Technical checks remain required: exact references, safe explicit paths, decodeability, duration/timeline compatibility, playable output, SRT structure, restart and package evidence. They are not sufficient.

The H4 reviewer must additionally confirm:

- **Content:** each Scene visibly supports its exact grounded teaching intent; no unsupported factual claim or misleading visual metaphor is introduced.
- **Listening:** every approved narration line is intelligible, natural enough for the intended audience, complete and neither clipped nor masked; ASR text is supporting evidence only.
- **Visual continuity:** the main character/style is recognizably continuous, actions and camera behavior match the Scene contract, and generation defects/text/watermarks do not distract.
- **Rhythm:** visual events, cuts and shot duration support the narration at normal speed; the result is not accepted merely because total duration and codec fields match.
- **Whole-product judgment:** the reviewer watches and listens to the complete Final Video, not isolated frames/clips only, and binds the verdict to the exact Video Version.

## 8. Approved Defaults

The Product Owner approved these defaults on 2026-08-14:

1. require explicit Storyboard `approve` before H2 rather than accepting historical `skip`;
2. accept MP4 only in the first vertical slice;
3. freeze `scene-1.mp4` through `scene-6.mp4` and `scene-2-replacement.mp4`;
4. include existing F2A stills as labelled optional reference frames in the Handoff ZIP;
5. record platform-native audio/subtitle/effects as provenance metadata only, not selected canonical tracks;
6. reuse the existing Final Video Decision context/findings with a required human checklist;
7. bypass Budget Authorization for the manual handoff/import path, show that external subscription cost is not controlled by the application, and retain Budget/Attempt only for legacy Preview maintenance and future application-controlled paid APIs;
8. use one operator-declared generated-clips directory plus a Review-page POST trigger, with no browser upload/file chooser or generic file manager.

## 9. Authorization and Stop Conditions

The Goal is approved and active. H0 and H1 are complete; H2 is `COMPLETE` through Issue #135 / PR #136 at `main@c4f2f5e` with 444-test evidence. H3 is `IN PROGRESS` under Issue #137; H3.5 and H4 remain pending and each requires its own bounded Issue/Task Contract. No API call, credential, charge or deployment is authorized by this contract alone.

Stop and return to Product Owner review before selecting a Jimeng/Kling API/model, using credentials, changing Budget/caps, replacing the canonical narration/SRT contract, adding a new Decision type, expanding beyond the fixed one-task Demo or weakening exact Artifact/Final approval invariants.
