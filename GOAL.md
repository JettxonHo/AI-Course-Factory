# Goal: Deliver AI Course Factory FAST-MVP v1.1

## 1. Approval and State

| Field | Value |
| --- | --- |
| Status | **ACTIVE / APPROVED** |
| Approved by | Product Owner |
| Approval date | 2026-08-13 |
| Baseline | `main@b2642c18449e6d79b3b19fec39b7aeff564bf711` |
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

Observed on 2026-08-13:

- The F1 implementation was based on `main@1673b9c3fe350f0e7bcc3d7d22fb2a56c771bbbc` and integrated through PR #114.
- The merged baseline has 356 passing local regression tests and no claimed hosted CI evidence.
- Source-to-package offline modules, a durable facade and the local three-view workspace are integrated through Issue #113 / PR #114.
- Issue #110 was independently reviewed and merged through PR #111; the durable Scene media projection is part of this baseline.
- No cloud Provider credential, paid spend, deployment or public production runtime is authorized; PD-002 separately authorizes the bounded local GPT-SoVITS runtime for F2B.
- F1 passed independent review and local acceptance; this evidence is not real Provider or deployed-runtime evidence.
- F2A then merged through Issue #117 / PR #118 at `main@b2642c1` and was independently accepted COMPLETE after 397 local regression tests; its visuals are creator-supplied Desktop ImageGen assets generated outside the application.

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

Status: **IN PROGRESS / CANDIDATE** (Issue #119)

`PD-002` selects official GPT-SoVITS v2 through an explicitly configured external Python 3.11 runtime/repository/model cache and fixed synthetic Serena reference. Local inference is credential-free and zero external charge. F2B must pass independent focused/full review and the real opt-in smoke before it is marked complete. F2.5 is not implemented in this milestone.

The existing F2A visuals remain the accepted real visual asset path; no automatic cloud Visual Provider is started here. No F2.5 UI redesign or F3 acceptance is included.

Exit: the accepted F2A local-import Visual adapter and F2B local GPT-SoVITS TTS adapter work through the existing interfaces under recorded caps.

### F3 — Real end-to-end acceptance

Status: **BLOCKED ON F2B AND F2.5**

Run the fixed Demo from the browser with the accepted F2A visual assets and F2B local TTS adapter. Verify:

- exact source and visible claim evidence;
- Script, Budget and Final approvals;
- no paid call before approval or above the cap;
- creator-supplied F2A Scene visuals and real/local spoken narration;
- playable 9:16 MP4 and SRT;
- one bounded Scene retry/replace;
- restart continuation and local MP4/SRT/source/Manifest export.

Exit: evidence package is reviewed and the main controller returns `GOAL_APPROVED` or `GOAL_APPROVED_WITH_FOLLOW_UPS`.

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

The Goal is complete only when the fixed real browser Demo and export package satisfy PRD acceptance, focused and full tests pass, Provider/cost evidence is recorded, known limitations are honest, and the main controller independently approves the actual result.

Offline Fake success, code presence or a green regression suite alone cannot complete this Goal.
