# Goal: Deliver AI Course Factory FAST-MVP v1.1

## 1. Approval and State

| Field | Value |
| --- | --- |
| Status | **ACTIVE / F3 CORRECTION APPROVED FOR MERGE / FINAL GOAL VERDICT PENDING** |
| Approved by | Product Owner |
| Approval date | 2026-08-13 |
| Acceptance baseline | Issue #125 candidate based on `main@af61d31e949e20947517ba4d8ab6db867b6a5017` |
| Goal type | Local end-to-end FAST-MVP |
| Supersedes | Remaining sequencing and scope of Core MVP Goal v1.0 |

Completed M0–M2 and accepted M3-001–M3-009 remain reusable implementation evidence. They are not reopened. This Goal redirects remaining work from horizontal hardening to the shortest usable vertical product path.

## 2. Objective

Deliver one local browser flow in which a Creator can take the fixed GitHub course source through grounded Script review, planning, explicit Budget approval, accepted creator-supplied F2A visuals plus real/local TTS production, FFmpeg composition, one Scene retry/replace, Final Video review and local export of a playable, traceable package.

Goal success is a working product Demo with real media and bounded spend, not a count of modules, PRs, documents or tests.

## 3. Authorized Scope

- Review/close or park the current Issue #110 media-projection candidate under the F0 rule below.
- Build the minimal application facade and local three-view web workspace.
- Connect the already merged offline planning, approval, production, composition and packaging capabilities.
- Implement only the Scene selection/retry behavior needed by the product flow.
- Provide the bounded F2A Desktop ImageGen local-import bridge: an explicit operator directory, exact six-image preflight, local conversion and visual-only Scene 2 replacement. This bridge is external-source evidence, not a real Visual Provider implementation.
- After the approved `PD-002`, implement the bounded local GPT-SoVITS v2 TTS Adapter; F2A creator-supplied visuals already satisfy the FAST-MVP real-visual asset boundary. Automatic cloud Visual Provider work remains deferred.
- Deliver the separately approved F2.5 Warm Editorial Production Desk in the existing three-view web surface without changing application behavior or public view contracts.
- Run and document one fixed-source real end-to-end acceptance Demo.
- Update affected current truth docs inside the same feature PR when facts change.

## 4. Explicit Non-goals

- Multi-user/SaaS/authentication/production deployment.
- Multiple sources, courses, tasks, templates or Provider routing.
- General workflow UI, professional media editor or automatic publication.
- Large refactor of accepted modules before the vertical flow works.
- General Artifact graph, distributed execution, universal corruption recovery or speculative schema compatibility.
- Standalone governance/status PRs unless a hard-to-reverse decision changes.

## 5. Starting Fact Boundary

Observed on 2026-08-14:

- The F1 implementation was based on `main@1673b9c3fe350f0e7bcc3d7d22fb2a56c771bbbc` and integrated through PR #114.
- The merged F2.5 baseline has 414 passing local regression tests and no claimed hosted CI evidence.
- Source-to-package offline modules, a durable facade and the local three-view workspace are integrated through Issue #113 / PR #114.
- Issue #110 was independently reviewed and merged through PR #111; the durable Scene media projection is part of this baseline.
- No cloud Provider credential, paid spend, deployment or public production runtime is authorized; PD-002 separately authorizes the bounded local GPT-SoVITS runtime for F2B.
- F1 passed independent review and local acceptance; this evidence is not real Provider or deployed-runtime evidence.
- F2A then merged through Issue #117 / PR #118 at `main@b2642c1` and was independently accepted COMPLETE after 397 local regression tests; its visuals are creator-supplied Desktop ImageGen assets generated outside the application.
- F2B then merged through Issue #119 / PR #120 at `main@65ce873`; the bounded local GPT-SoVITS v2 adapter was independently accepted COMPLETE with the 411-test regression baseline.
- F2.5 merged through Issue #121 / PR #122 at `main@e155d193`; its Warm Editorial three-view presentation passed independent 1440px/375px browser review and the 414-test regression.
- F3 Issue #123 / PR #124 supplied partial media, approval, restart, Scene replacement and export evidence from a fresh browser run, but did not prove live GitHub acquisition. Issue #125 corrected that boundary and passed a new same-task live-source-to-package acceptance; the final planning Goal verdict follows merge.

`docs/STATUS.md` owns the current factual snapshot if these facts change.

## 6. Milestones

### F0 — Rebaseline and resolve Issue #110

Status: **COMPLETE**

1. Issue #110 received one bounded independent review and one full regression run.
2. The compatible candidate was merged through PR #111 without architectural rework.
3. This FAST-MVP planning rebaseline is integrated after that merge.

Exit: daily truth sources point to FAST-MVP, and #110 is either merged/closed or explicitly parked with preserved work.

### F1 — Offline usable workspace

Status: **COMPLETE**

One Issue and one main PR deliver:

- one application facade over the current pipeline;
- Start/Current Task, Review/Produce and Final/Export views;
- visible source evidence, pending gates, budget facts, failures and available actions;
- deterministic Fake/local media through FFmpeg to a browser-playable video;
- one Scene retry/replace while preserving unaffected Scene media;
- Final approval, package export and one restart continuation;
- browser evidence plus focused tests and one full regression run.

Exit: a person can complete the fixed Demo offline without calling internal modules manually.

### F2A — Creator-supplied Desktop ImageGen visual bridge

Status: **COMPLETE** (Issue #117 / PR #118 merged at `b2642c1`)

Issue #117 adds an explicit `--visual-import-dir` path for six creator-supplied PNG/JPEG stills. The application preflights every exact filename and decodes each image before any production attempt, workspace media write or Artifact commit; local FFmpeg produces the playable H.264 clips after Budget approval at zero external charge. Scene 2 replacement accepts only `scene-2-replacement.png`, reuses the predecessor voice/Scene Audio/Master Audio selections, rebuilds stale video, and preserves all unaffected Scene references. Restart replays the committed result without reconversion, and package attribution states that the images were supplied through ChatGPT Desktop ImageGen, generated outside the application, with model version unverified.

F2A does not call a cloud Visual Provider or use credentials. Independent browser, media, restart and ZIP evidence accepted the external-source visual bridge; automatic cloud Visual Provider work is deferred and does not block F3.

### F2B — Local real GPT-SoVITS TTS

Status: **COMPLETE** (Issue #119 / PR #120 merged at `65ce873`)

`PD-002` selects official GPT-SoVITS v2 through an explicitly configured external Python 3.11 runtime/repository/model cache and fixed synthetic Serena reference. Local inference is credential-free and zero external charge. Independent focused/full review and the opt-in local smoke accepted the bounded adapter; F2B does not claim cloud Provider or deployment evidence.

The existing F2A visuals remain the accepted real visual asset path; no automatic cloud Visual Provider is started here. F2.5 and F3 acceptance remain separate milestones.

Exit: the accepted F2A local-import Visual adapter and F2B local GPT-SoVITS TTS adapter work through the existing interfaces under recorded caps.

### F2.5 — Warm Editorial Production Desk

Status: **COMPLETE** (Issue #121 / PR #122 merged at `e155d193`)

Issue #121 upgrades the existing exactly-three server-rendered views into the approved Warm Editorial Production Desk. It keeps the existing routes, view model, POST actions, media endpoints, security boundaries and provenance facts while adding a semantic three-stage track, task/stage/next-action hierarchy, progressive disclosure for visual prompt cards, storyboard scanning, a 9:16 final review with a sticky desktop decision rail, local favicon and responsive CSS-only polish. No JavaScript, SPA, editor, upload manager, provider behavior or public contract is added.

Independent review accepted the real Diff after focused rendered-HTML/static checks, 1440px/375px browser review and the 414-test full regression. PR #122 merged without changing application behavior or claiming F3 evidence.

### F3 — Real end-to-end acceptance

Status: **CANDIDATE COMPLETE / APPROVED FOR MERGE** (Issue #125; final planning Goal verdict pending)

Issue #125 repeated the full browser flow from a previously nonexistent data directory. The Creator submitted the one supported public URL, the default connector locked real upstream commit `33e781bf7bfb9b39fd27c4e4a3e592669b52cb4b` and acquired `lessons/1-Intro/README.md` with blob `6b29b141e0f0f81477e16bee4e4d1e6222d0579c`; the same task then completed:

- live GitHub source acquisition and exact Source/Script decision facts;
- Script, Budget and Final approvals;
- no paid call before approval or above the cap;
- creator-supplied F2A Scene visuals and real/local spoken narration;
- playable 9:16 MP4 and SRT;
- one bounded Scene retry/replace;
- restart continuation and local MP4/SRT/source/Manifest export.

Exit: the Issue #125 correction, fresh same-run acceptance and independent main-controller review passed, including 52 focused tests, the 422-test full regression, compileall and Diff/ownership review. The candidate is approved for merge; no final `GOAL_APPROVED` claim is made until the planning controller reviews the merged result. The local MVP remains bounded to the fixed Demo and is not deployment, adoption, paid Provider or cloud-runtime evidence.

## 7. Agent Operating Model

- Main controller: configured `gpt-5.6-sol / xhigh`; owns investigation, product/architecture decisions, Task Contracts, dispatch and independent review.
- Implementation: exact custom `luna-worker`, configured `gpt-5.6-luna / max`; owns only bounded code changes.
- No Terra/default-worker fallback. If exact Luna is unavailable, return `STATUS: BLOCKED_LUNA_WORKER_UNAVAILABLE`.
- Configuration does not prove runtime identity; record `RUNTIME_VERIFIED` only when exposed by the runtime.
- An implementation worker does not approve its own result.

## 8. Development Rules

1. Optimize for the next user-visible vertical outcome.
2. Reuse and deepen existing modules; do not add pass-through layers.
3. One primary outcome per Issue/PR. Update related truth docs in that PR instead of opening a status-only PR.
4. Use exact Artifact references, keep approval and budget boundaries, and isolate external Providers behind Adapters.
5. Apply tests in proportion to real risk; no automatic mutation, corruption, concurrency or future-schema campaign.
6. Run focused checks during work, the full regression once before merge, and inspect the real Diff independently.
7. Preserve concurrent/user work and stop on overlapping ownership.

## 9. Stop Conditions

Escalate before:

- Provider selection, credential use, fee or cap change;
- production deployment, external publication or sensitive data use;
- major stack replacement or broad rewrite;
- weakening one of the six PRD essential invariants;
- expanding beyond the fixed single-task Demo;
- resolving two reasonable product options without Product Owner input.

Do not stop merely because a hypothetical future edge case lacks a generalized defense.

## 10. Completion Definition

The completion candidate now satisfies the corrected fixed real browser Demo: it starts from the submitted supported URL, acquires and displays a non-placeholder upstream commit/locator, and completes the media/recovery/export acceptance with focused and full tests, local processing/cost evidence, known limitations and independent main-controller approval.

The prior #123/#124 media result remains partial historical evidence; Issue #125 supplies the corrected fresh live-source F3 run. Final Goal approval remains a post-merge planning verdict and is not inferred from Offline Fake success, code presence or a green regression suite alone.
