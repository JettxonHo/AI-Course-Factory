# Goal: Deliver AI Course Factory Knowledge Video Editorial MVP v1.3

## 1. Approval and State

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE** |
| Approved by | Product Owner |
| Approval date | 2026-08-24 |
| Activation task | E0 Issue #143 on `codex/143-knowledge-video-editorial-rebaseline`; docs PR/merge pending |
| Planning baseline | `main@d301efd8494029e8b8eae5001050974a67778937` |
| Goal type | Local single-user Knowledge Video Editorial MVP |
| Preserves | FAST-MVP v1.1 `COMPLETE / GOAL_APPROVED`; Creator Handoff v1.2 H0–H3.5 accepted foundation/history |

This Goal supersedes Creator Handoff v1.2 only as the active primary production path. It does not delete or relabel its accepted implementation, lineage, handoff, import, restart or UI evidence. Creator Handoff H4 remains **PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE**.

## 2. Exact Goal

Deliver one local Knowledge Video Editorial flow that turns the supported exact public GitHub source into an approved grounded Script, one continuous narration, phrase-level millisecond Acoustic Alignment, a human-approved Visual Edit Plan, deterministic A-roll/B-roll production, an approved 15–20 second Sample Video, a fully rendered Final Video, and a named-human-approved traceable Publish Package through exactly three lightweight server-rendered views.

Success is one intelligible, evidence-backed and well-paced local knowledge video. Codec, FFprobe, alignment metrics, screenshots and automated tests remain technical evidence; they cannot replace named-human review of teaching fidelity, narration completeness/naturalness, visual evidence/continuity and edit rhythm at normal playback speed.

## 3. Approved Primary Chain

```text
exact Source
  -> approved grounded Script
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
- Keep immutable Artifact Versions/References, exact Decisions, Task selection, local Workspace and restart/replay ownership.
- Keep Narration, Alignment and SRT application-owned. A renderer or external platform cannot replace these truths.
- Keep exactly three lightweight local SSR/Jinja control views: Content & Audio; Visual Planning & Production; Final Review & Delivery.
- Keep the existing Final Video Decision and Publish Package ownership, deepened only with exact editorial lineage through later bounded Tasks.
- Keep v1.2 per-Scene narration, Scene Generation Contract, Creator Handoff Package and creator-import media readable as foundation/compatibility history. They cannot satisfy the v1.3 primary Sample/Final gates.
- Preserve the protected H4 six-file dirty candidate and repo-external evidence for a later line-level reuse/compatibility/park disposition. Do not reset, clean, overwrite or cherry-pick it wholesale.

## 6. Milestones

### E0 — Truth rebaseline

Status: **IN PROGRESS / DOCS ONLY** (Issue #143; merge pending)

Outcome: make this exact Goal the repository execution truth; record D-010, the narration-led editorial chain, A/B-roll semantics, continuous Alignment clock, v1.2/H4 disposition and implementation stop conditions in one nine-file authoritative docs PR.

Exit: the exact nine-doc Diff is independently reviewed and merged; Issue #143 closes with actual Git/GitHub facts. No feature code, dependency or runtime action belongs to E0.

### E1 — Narrative clock

Status: **BLOCKED ON E0 MERGE; PLANNING ONLY AFTER E0**

Outcome: from the exact approved Script, produce one durable Whole Narration, one validated Acoustic Alignment and canonical SRT through the existing control surface.

Entry: after E0 merges, create one bounded E1 Issue/Task Contract with exact ownership, runtime/dependency evaluation, RED/focused/full gates, restart compatibility and exact Luna route. E1 coding/Luna dispatch remains unauthorized until that startup gate is independently approved.

### E2 — Visual Edit Plan and asset readiness

Status: **PENDING E1**

Outcome: propose, inspect and approve one exact Visual Edit Plan with shot/range A/B rationale, evidence/claim coverage, creator static-asset manifest/gaps and overlay/motion intent.

### E3 — Deterministic Sample gate

Status: **PENDING E2**

Outcome: evaluate HyperFrames or one justified equivalent against a small deterministic renderer seam, then render and approve one exact 15–20 second A-roll/B-roll Sample before full rendering.

### E4 — Full render, Final Review and Publish

Status: **PENDING E3**

Outcome: render the complete video from approved exact inputs, complete named-human normal-speed review, export the traceable package and prove restart/replay.

## 7. Authorized Scope

Current authorization is E0 only:

- update the exact nine documentation files owned by Issue #143;
- independently review the docs Diff and run ownership/authority/stale-wording/`git diff --check` gates;
- commit, push, create one ready docs PR, merge after review and close Issue #143;
- truthfully comment/close Issues #141/#142 as PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE while preserving their dirty branch and evidence.

After E0 merge, authorization advances only to E1 planning and one Task Contract startup review. It does not directly authorize E1 code or Luna dispatch.

## 8. Explicit Non-goals

- video-generation LLM/API in the MVP primary path;
- automated Jimeng/Kling/Seedance operation, external six-MP4 generation/import or subscription-credit use;
- generic Provider registry, ImageGeneration Provider/model/credential/fee/cap choice or paid call;
- HyperFrames/alignment runtime installation during E0;
- professional timeline editor, generic asset manager, dashboard, SPA, fourth view or frontend framework migration;
- multiple users/sources/tasks, auth, deployment or publication;
- broad Artifact/Decision/Workflow/schema rewrite;
- treating ASR/alignment scores, codec checks or fixtures as named-human acceptance.

## 9. Agent and Review Rules

- Main controller: configured `gpt-5.6-sol / xhigh`; owns investigation, Task Contracts, dispatch, actual Diff review and runtime/product evidence.
- Implementation: exact `luna-worker`, configured `gpt-5.6-luna / max`; no Terra/default fallback and no self-approval.
- Every E1–E4 implementation milestone requires one bounded Issue/Task Contract and independent startup approval before dispatch.
- Use RED/focused iteration during implementation and one final full regression before merge. Fake/runtime/technical evidence remains separate from named-human product acceptance.
- Stop for any Provider/model/credential/fee/cap, dependency/stack expansion, deployment/publication, broad public-contract rewrite or loss of protected H4 work.

## 10. Completion Definition

Knowledge Video Editorial MVP v1.3 is complete only when E0–E4 are complete and one fresh browser-driven local run proves exact Source and approved Script lineage, one continuous Narration, validated continuous Acoustic Alignment/canonical SRT, an approved evidence-backed Visual Edit Plan, an approved A-roll/B-roll Sample, full deterministic rendering, restart/replay, named-human normal-speed findings bound to the exact Final Video and one traceable Publish Package.

This Goal is local single-user MVP evidence only. It does not establish cloud Provider execution, paid economics, deployment, publication, adoption or production operations.
