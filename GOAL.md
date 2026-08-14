# Goal: Deliver AI Course Factory Creator Handoff MVP v1.2

## 1. Approval and State

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE** |
| Approved by | Product Owner |
| Approval date | 2026-08-14 |
| H0 merged baseline | `main@d96b091b5d6486129487f5b51b0bb1c43b64639b` (Issue #129 / PR #130) |
| Current task | Issue #135 H2 Creator Handoff Package on `codex/135-creator-handoff-package`; H1 Issue #133 / PR #134 is merged at `main@91b451225c40fd7fa884355ac7da6fa1e373238b` |
| Goal type | Local single-user Creator Handoff MVP |
| Preserves | FAST-MVP v1.1 `COMPLETE / GOAL_APPROVED` history |

FAST-MVP v1.1 and its accepted F1/F2A/F2B/F2.5/F3 evidence remain complete historical facts. v1.2 repositions the next product result; it does not reopen or relabel that acceptance.

## 2. Exact Goal

Deliver one local Creator Handoff flow that turns the supported public GitHub source into an exact, human-reviewable Scene Generation Contract and Creator Handoff Package; accepts creator-generated Scene videos from one operator-declared directory through an explicit browser import action; composes those clips with AI Course Factory's exact narration, SRT and Timeline; and produces a human-approved Final Video and traceable Publish Package.

Success requires a full human watch/listen judgment. Codec, FFprobe, ASR, screenshots and automated tests remain technical evidence; they cannot replace review of teaching fidelity, narration completeness/naturalness, visual continuity/action and edit rhythm at normal playback speed.

## 3. Approved Defaults

1. Require explicit Storyboard `approve` before the Creator Handoff Package; historical `skip` remains readable but is not v1.2-ready.
2. Accept MP4 only in the first import slice.
3. Freeze `scene-1.mp4` through `scene-6.mp4` and `scene-2-replacement.mp4`.
4. Include labelled optional F2A reference stills in the Creator Handoff Package.
5. Record external native audio/subtitle/effects as metadata/provenance only; they are not canonical selected tracks.
6. Reuse Final Video Decision context/findings with a required human content/listening/continuity/rhythm checklist.
7. Bypass Budget Authorization for the manual handoff/import path. External subscription cost is outside application control; Budget/Attempt remains for legacy Preview maintenance and future application-controlled paid APIs.
8. Use one operator-declared generated-clips directory plus a Review-page POST trigger. No multipart/browser upload, generic file manager or Downloads/Desktop/latest scan is authorized.

## 4. Canonical Product Boundary

- **Scene Generation Contract** — one immutable provider-neutral Artifact bound to exact approved Script, Storyboard, Timeline and Production Request references, with ordered per-Scene prompt/continuity/camera/action/duration/import identity.
- **Preview Video** — the historical F2A still-image composition and other technical/progress output; it cannot satisfy the v1.2 Final quality gate.
- **Creator Handoff Package** — a deterministic pre-generation package containing exact references, per-Scene guide, exact narration, canonical SRT/Timeline, provenance and labelled optional reference stills. It is not the final Publish Package.
- **Imported Generated Scene Clip** — one creator-supplied MP4 committed as an honest creator-import `scene_clip` variant, with no fabricated attempt/provider.
- **Final Video** — local composition of six exact creator-import Scene Clips plus application-owned narration/SRT/Timeline, bound by the existing Final Video Decision.

Manual Jimeng/Kling subscription work occurs outside the application. It creates no Provider Attempt, application credential use or application charge. Future application-controlled `JimengVideoAdapter`/`KlingVideoAdapter` work requires a separate Product Owner decision for Provider/model/credentials/price/cap and re-enters Budget/Attempt gates.

## 5. Stable Compatibility Contract

- Keep `artifact_type=scene_clip`, existing per-Scene identity/version chains and Task selection/stale impact.
- Add a discriminated creator-import payload containing at least `source_kind="creator_import"`, exact Production Request and Scene Generation Contract References, `scene_id`, declared filename, creator provenance, normalized output, media type and duration.
- The creator-import payload has no `attempt_id` or `provider`; its exact dependencies include the Production Request and Scene Generation Contract.
- Task lineage reads both legacy generated/Preview and creator-import payloads. Legacy facts remain readable but cannot satisfy v1.2 Final Review.
- H3 adds an honest imported-clip composition input/reference variant instead of forging `MediaGenerationResult` fields.
- Before v1.2 Final Review, resolve all six selected Scene Clip Versions and require creator-import variants for the exact ordered Scenes, all bound to the same exact Scene Generation Contract.
- Exact narration audio, Scene/Master Audio, canonical SRT/Timeline, Final Video Decision and final Publish Package remain application-owned truth.

## 6. Milestones

### H0 — Truth rebaseline

Status: **COMPLETE** (Issue #129 closed; PR #130 merged)

Outcome: integrate D-008, this active Goal, canonical terms, approved defaults, stable ownership and verification boundaries without product code.

Exit: Issue #129's exact docs Diff merged through PR #130 at `main@d96b091`; H0 is complete and H1 was ready from that real baseline.

### H1 — Grounded Storyboard and Scene Generation Contract

Status: **COMPLETE** (Issue #131 / PR #132 plus bounded correction Issue #133 / PR #134 merged at `main@91b4512`)

Outcome: from exact approved Source/Script/Storyboard/Timeline/Production Request references, commit one human-reviewable ordered Scene Generation Contract and expose it through the existing three-view workspace.

Exit: explicit Storyboard approval and exact lineage are durable; every Scene exposes its narration identity, visual intent/action, generation prompt, continuity, camera/motion, duration and fixed MP4 filename; restart reads the same contract without regeneration.

H1 implementation is bounded by the approved Issue #131 Task Contract and its Issue #133 HTTP replay correction, exact ownership, migration/restart evidence and focused/full verification. Issue #133 / PR #134 is independently reviewed and merged at `main@91b4512` with 433-test regression evidence.

### H2 — Creator Handoff Package

Status: **IN PROGRESS** (Issue #135 candidate; not merged)

Outcome: export a deterministic handoff ZIP with exact references, generation guide, narration, SRT/Timeline, provenance and labelled optional reference stills, after non-monetary local readiness.

Exit: package replay is byte-stable; local narration is durable/idempotent without fabricated monetary authorization; manual generation creates no Attempt or charge. The current candidate remains unmerged until independent review and the full regression.

### H3 — Generated Scene Clip import and exact composition

Status: **PENDING H2**

Outcome: atomically import exact `scene-1.mp4` through `scene-6.mp4` from one configured directory, compose with canonical narration/SRT, and support exact `scene-2-replacement.mp4` while preserving unaffected media.

Exit: creator-import payload/input/Final-gate compatibility is proven; no partial side effect occurs on failed preflight; restart and stale/recompose behavior remain exact.

### H4 — Browser and product-quality acceptance

Status: **PENDING H3**

Outcome: one fresh three-view Source-to-Handoff-to-import-to-Final-to-Publish flow completes with restart/replay and a named human full-watch/listen verdict bound to the exact Final Video Version.

Exit: technical and product-quality gates pass; no Preview Video is accepted as v1.2 Final quality.

## 7. Authorized Scope

- H0 is complete at `main@d96b091` through Issue #129 / PR #130.
- Implement and independently review the bounded H2 Issue #135 Task Contract after H1 is complete at `main@91b4512`.
- Reuse the current live Source, Artifact repository, Script/Storyboard/Final decisions, Task media projection, local GPT-SoVITS narration, FFmpeg composition and Publish Package.
- Change frontend only where a milestone needs contract review, handoff download, import readiness/action or final quality evidence; retain exactly three server-rendered views.
- Update related Goal/Status facts inside the corresponding feature PR using actual, not anticipated, merge/runtime evidence.

## 8. Explicit Non-goals

- Jimeng/Kling API integration, Provider/model/credential selection, paid calls or cap changes.
- Deployment, publication, multi-user/auth, multiple sources/tasks or sensitive data handling.
- Fourth page, SPA, generic upload/file manager, professional editor or unrelated visual redesign.
- Replacing exact narration/SRT with external native tracks.
- Generic Provider/plugin framework, parallel workflow, Artifact graph rewrite or broad migration.
- Treating manual subscription work as an application Provider Attempt or Budget-controlled spend.

## 9. Agent and Review Rules

- Main controller: configured `gpt-5.6-sol / xhigh`; owns investigation, contracts, dispatch and independent review.
- Implementation: exact `luna-worker`, configured `gpt-5.6-luna / max`; no Terra/default fallback.
- Each H1-H4 coding milestone requires its own bounded Issue/Task Contract and ownership. No parallel milestone coding is implied by Goal approval.
- Run focused checks during implementation and the full regression once before each merge; Fake/technical evidence is not human product-quality acceptance.
- Preserve unaffected work and stop on a real public-contract, Provider/fee, migration or scope conflict.

## 10. Completion Definition

Creator Handoff MVP v1.2 is complete only when H0-H4 are complete and one human-approved Final Video is built from six exact creator-import Scene Clips, application-owned narration/SRT/Timeline and exact source/planning lineage, then exported through the traceable Publish Package.

This Goal is local MVP evidence only. It does not establish cloud Provider execution, paid economics, deployment, publication, adoption or production operations.
