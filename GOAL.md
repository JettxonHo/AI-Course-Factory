# Goal: Deliver AI Course Factory Knowledge Video Editorial MVP v1.3

## 1. Approval and State

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE** |
| Approved by | Product Owner |
| Approval date | 2026-08-24 |
| Activation task | S0 Issue #148 / PR #149 merged; S1 Issue #150 on `codex/150-creator-script-package-intake` |
| Planning baseline | `main@597f3a03e582cbccc099ad0810e17b0262a80d51` |
| Goal type | Local single-user Knowledge Video Editorial MVP |
| Preserves | FAST-MVP v1.1 `COMPLETE / GOAL_APPROVED`; Creator Handoff v1.2 H0–H3.5 accepted foundation/history |

This Goal supersedes Creator Handoff v1.2 only as the active primary production path. It does not delete or relabel its accepted implementation, lineage, handoff, import, restart or UI evidence. Creator Handoff H4 remains **PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE**.

## 2. Exact Goal

Deliver one local Knowledge Video Editorial flow that acquires the supported exact public GitHub source; accepts a Creator-authored Script Package whose ordered narration units bind exact source locators and claim evidence; commits and human-approves one immutable Script Version; produces one continuous narration, phrase-level millisecond Acoustic Alignment, a human-approved Visual Edit Plan, deterministic A-roll/B-roll production, an approved 15–20 second Sample Video, a fully rendered Final Video, and a named-human-approved traceable Publish Package through exactly three lightweight server-rendered views.

Success is one intelligible, evidence-backed and well-paced local knowledge video. Codec, FFprobe, alignment metrics, screenshots and automated tests remain technical evidence; they cannot replace named-human review of teaching fidelity, narration completeness/naturalness, visual evidence/continuity and edit rhythm at normal playback speed.

## 3. Approved Primary Chain

```text
exact Source
  -> explicit Creator-authored Script Package intake
  -> exact human-approved immutable Script Version
  -> one continuous Whole Narration
  -> phrase-level millisecond Acoustic Alignment
  -> human-approved Visual Edit Plan
  -> deterministic A-roll / B-roll production
  -> approved 15–20 second Sample Video
  -> full local render
  -> named-human Final Review
  -> Publish Package
```

Acoustic Alignment is the sole continuous audiovisual clock. After one declared punctuation/whitespace normalization, ordered phrase text covers the approved narration character-for-character. Chinese defaults to 5–15 Han characters or an equivalent short phrase; intervals are nonnegative, strictly ordered, non-overlapping and continuous from millisecond `0` to exact audio duration under a declared pause-allocation policy. ASR may propose timestamp candidates but cannot replace approved Script text.

## 4. Canonical Product Boundary

- **Whole Narration** — one continuous application-owned narration audio Artifact for the exact approved Script, generated once and replayed durably.
- **Acoustic Alignment** — immutable ordered short-phrase millisecond intervals bound to exact approved narration text and Whole Narration; the sole audiovisual timing authority and canonical SRT timing source.
- **Visual Edit Plan** — one human-reviewable immutable plan bound to exact Script, Whole Narration and Alignment. Every shot/range records A-roll/B-roll plus rationale, evidence/claim intent, assets/gaps, overlays, motion/camera and transition intent.
- **A-roll Segment** — the Xiaotudou/IP presenter layer for hooks, transitions, emotion, physical action and low-information-density spoken delivery.
- **B-roll Segment** — the knowledge/evidence layer for concepts, steps, comparisons, processes, charts, source evidence, screenshots and demonstrations. Claim-bearing or information-dense content defaults to evidence-bound B-roll unless an exception reason is recorded; decorative B-roll cannot satisfy coverage.
- **Creator Static Asset** — an explicitly selected creator-supplied character, environment, prop, illustration, diagram or screenshot with exact provenance, no Provider Attempt and no application charge.
- **Sample Video** — an exact 15–20 second deterministic render containing at least one A-roll segment, one B-roll segment, their transition and representative overlay/motion behavior. Exact human approval is required before full rendering.
- **Final Video** — the complete deterministic render derived from the approved Alignment, Plan and selected assets, then bound to named-human Final Review.
- **Publish Package** — post-approval delivery containing the exact Final Video/SRT plus Source, Script, Narration, Alignment, Plan, Sample, asset and Final Decision provenance.

## 5. Stable Ownership and Compatibility

- Keep exact public GitHub Source commit/blob/locators, grounded Knowledge and Script Decision semantics.
- Make the Creator-authored Script Package the v1.3 primary Script input. The application validates its structure and exact Source membership, commits immutable Script Versions and records exact human approve/reject Decisions; it does not act as a general Script author or natural-language revision engine.
- Persist the complete validated canonical `script_package` binding on every accepted Script Version. Top-level claims exclusively own evidence locators; narration units bind claims by ID. Changed valid imports create an unapproved next Version with exact prior lineage, while canonical replay creates no Version or state mutation.
- Keep immutable Artifact Versions/References, exact Decisions, Task selection, local Workspace and restart/replay ownership.
- Keep Narration, Alignment and SRT application-owned. A renderer or external platform cannot replace these truths.
- Keep exactly three lightweight local SSR/Jinja control views: Content & Audio; Visual Planning & Production; Final Review & Delivery.
- Keep the existing Final Video Decision and Publish Package ownership, deepened only with exact editorial lineage through later bounded Tasks.
- Keep v1.2 per-Scene narration, Scene Generation Contract, Creator Handoff Package and creator-import media readable as foundation/compatibility history. They cannot satisfy the v1.3 primary Sample/Final gates.
- Preserve the protected H4 six-file dirty candidate and repo-external evidence for a later line-level reuse/compatibility/park disposition. Do not reset, clean, overwrite or cherry-pick it wholesale.

## 6. Milestones

### E0 — Truth rebaseline

Status: **COMPLETE** at `main@47ac1e3333a2b1f4927baf6bf6de1c44950d9307`; Issue #143 CLOSED, PR #144 MERGED.

Outcome: established the narration-led editorial chain, A/B-roll semantics, continuous Alignment clock, v1.2/H4 disposition and implementation stop conditions through D-010.

### S0 — Creator Script input rebaseline

Status: **COMPLETE** at `main@597f3a03e582cbccc099ad0810e17b0262a80d51`; Issue #148 CLOSED, PR #149 MERGED.

Outcome: make this amended exact Goal, D-011, Creator-authored Script Package schema/lineage/intake semantics and the approved defaults below the repository execution truth in one exact ten-file docs change.

Exit: the exact ten-doc Diff was independently reviewed and merged; Issue #148 is closed with actual Git/GitHub facts. S1 owns the next bounded feature slice.

### S1 — Creator Script Package intake

Status: **IN PROGRESS** through Issue #150; bounded implementation candidate on `codex/150-creator-script-package-intake`.

Outcome: explicitly intake/re-import one fixed `creator-script.json`, validate exact Source membership, commit/select immutable Script Versions and record exact human approve/reject Decisions with restart/idempotency evidence.

Entry: S0 merged through PR #149; Issue #150 is the independently approved bounded S1 Task Contract with exact ownership, RED/focused/full gates, compatibility and exact Luna route. Final merge/closure evidence remains pending.

### E1 — Narrative clock

Status: **PENDING S1**

Outcome: from the exact approved Script, produce one durable Whole Narration, one validated Acoustic Alignment and canonical SRT through the existing control surface.

Entry: only an exact human-approved Creator-authored Script Version from S1 can enter E1. E1 owns narration/alignment/SRT and does not author or revise Script.

### E2 — Visual Edit Plan and asset readiness

Status: **PENDING E1**

Outcome: propose, inspect and approve one exact Visual Edit Plan with shot/range A/B rationale, evidence/claim coverage, creator static-asset manifest/gaps and overlay/motion intent.

### E3 — Deterministic Sample gate

Status: **PENDING E2**

Outcome: evaluate HyperFrames or one justified equivalent against a small deterministic renderer seam, then render and approve one exact 15–20 second A-roll/B-roll Sample before full rendering.

### E4 — Full render, Final Review and Publish

Status: **PENDING E3**

Outcome: render the complete video from approved exact inputs, complete named-human normal-speed review, export the traceable package and prove restart/replay.

## 7. Approved Script-input defaults

1. Use one operator-configured directory plus fixed `creator-script.json`.
2. Use JSON schema version 1.
3. Trigger intake/re-import through one explicit same-origin Start-page POST with no path or upload field.
4. Require creator-declared provenance; require the `revision_note` field while allowing its bounded note value to be `null`.
5. Automatically validate exact Source identity, the ordered file projection and locator membership.
6. Leave semantic support and teaching quality exclusively to an exact human Script Decision.
7. Use canonical JSON-value equivalence and one locked `script_package_id` lifecycle.
8. Expose approve/reject only for v1.3; keep legacy revise readable but unable to invoke authoring or qualify a current v1.3 Script.

## 8. Authorized Scope

Current authorization is S1 Issue #150 only:

- implement the exact 34 paths owned by Issue #150;
- run RED/focused/compatibility checks, compileall, diff-check and exact ownership review;
- keep Provider/model/credential/fee/deploy, E1/E2, generic repository/schema changes and protected candidates out of scope.

S1 implementation does not authorize E1/E2, Provider/model/credential/fee/deploy, or protected-candidate reuse; the main controller owns final full regression and merge gates.

## 9. Explicit Non-goals

- video-generation LLM/API in the MVP primary path;
- automated Jimeng/Kling/Seedance operation, external six-MP4 generation/import or subscription-credit use;
- generic Provider registry, ImageGeneration Provider/model/credential/fee/cap choice or paid call;
- HyperFrames/alignment runtime installation during S0;
- professional timeline editor, generic asset manager, dashboard, SPA, fourth view or frontend framework migration;
- multiple users/sources/tasks, auth, deployment or publication;
- broad Artifact/Decision/Workflow/schema rewrite;
- treating ASR/alignment scores, codec checks or fixtures as named-human acceptance.

## 10. Agent and Review Rules

- Main controller: configured `gpt-5.6-sol / xhigh`; owns investigation, Task Contracts, dispatch, actual Diff review and runtime/product evidence.
- Implementation: exact `luna-worker`, configured `gpt-5.6-luna / max`; no Terra/default fallback and no self-approval.
- Every S1/E1–E4 implementation milestone requires one bounded Issue/Task Contract and independent startup approval before dispatch.
- Use RED/focused iteration during implementation and one final full regression before merge. Fake/runtime/technical evidence remains separate from named-human product acceptance.
- Stop for any Provider/model/credential/fee/cap, dependency/stack expansion, deployment/publication, broad public-contract rewrite or loss of protected H4 work.

## 11. Completion Definition

Knowledge Video Editorial MVP v1.3 is complete only when S0, S1 and E1–E4 are complete and one fresh browser-driven local run proves exact Source and approved Creator-authored Script Package lineage, one continuous Narration, validated continuous Acoustic Alignment/canonical SRT, an approved evidence-backed Visual Edit Plan, an approved A-roll/B-roll Sample, full deterministic rendering, restart/replay, named-human normal-speed findings bound to the exact Final Video and one traceable Publish Package.

This Goal is local single-user MVP evidence only. It does not establish cloud Provider execution, paid economics, deployment, publication, adoption or production operations.
