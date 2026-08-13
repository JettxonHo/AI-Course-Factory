# Goal: Deliver AI Course Factory FAST-MVP v1.1

## 1. Approval and State

| Field | Value |
| --- | --- |
| Status | **ACTIVE / APPROVED** |
| Approved by | Product Owner |
| Approval date | 2026-08-13 |
| Baseline | `main@5d4cae8bcb45e15cba036c45fc673f6245117a6b` |
| Goal type | Local end-to-end FAST-MVP |
| Supersedes | Remaining sequencing and scope of Core MVP Goal v1.0 |

Completed M0–M2 and accepted M3-001–M3-009 remain reusable implementation evidence. They are not reopened. This Goal redirects remaining work from horizontal hardening to the shortest usable vertical product path.

## 2. Objective

Deliver one local browser flow in which a Creator can take the fixed GitHub course source through grounded Script review, planning, explicit Budget approval, real Visual/TTS production, FFmpeg composition, one Scene retry/replace, Final Video review and local export of a playable, traceable package.

Goal success is a working product Demo with real media and bounded spend, not a count of modules, PRs, documents or tests.

## 3. Authorized Scope

- Review/close or park the current Issue #110 media-projection candidate under the F0 rule below.
- Build the minimal application facade and local three-view web workspace.
- Connect the already merged offline planning, approval, production, composition and packaging capabilities.
- Implement only the Scene selection/retry behavior needed by the product flow.
- After separate Product Owner Provider/budget decisions, implement one real Visual Adapter and one real TTS Adapter.
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

- `origin/main` is `5d4cae8bcb45e15cba036c45fc673f6245117a6b`.
- The merged baseline has 340 passing local regression tests and no claimed hosted CI evidence.
- Source-to-package offline modules exist; the web workspace and real Visual/TTS path do not.
- Issue #110 is open. Its unmerged candidate exists in a separate primary worktree, with 13 focused tests reported green; it has not yet passed independent review or full regression and is not part of this baseline.
- No real Provider, credential, spend, deployment or production runtime is authorized by this Goal approval.

`docs/STATUS.md` owns the current factual snapshot if these facts change.

## 6. Milestones

### F0 — Rebaseline and resolve Issue #110

Status: **READY**

1. Merge this FAST-MVP planning rebaseline.
2. Give Issue #110 one bounded independent review and one full regression run.
3. If it is compatible with the vertical workspace and needs no architecture rewrite, merge it.
4. If review requires a second redesign/correction cycle, park it without deleting the candidate; F1 implements only the smallest Scene media state it actually needs.

Exit: daily truth sources point to FAST-MVP, and #110 is either merged/closed or explicitly parked with preserved work.

### F1 — Offline usable workspace

Status: **READY AFTER F0**

One Issue and one main PR deliver:

- one application facade over the current pipeline;
- Start/Current Task, Review/Produce and Final/Export views;
- visible source evidence, pending gates, budget facts, failures and available actions;
- deterministic Fake/local media through FFmpeg to a browser-playable video;
- one Scene retry/replace while preserving unaffected Scene media;
- Final approval, package export and one restart continuation;
- browser evidence plus focused tests and one full regression run.

Exit: a person can complete the fixed Demo offline without calling internal modules manually.

### F2 — Real Visual and TTS

Status: **BLOCKED ON PRODUCT DECISIONS**

Required first:

- `PD-001`: Visual Provider/model/credential source;
- `PD-002`: TTS Provider/voice/credential source;
- `PD-003`: smoke and full-Demo amount/attempt caps.

After approval, use two bounded Issues if file ownership is independent: one Visual Adapter and one TTS Adapter. Each must fail closed on missing credentials, normalize Provider failure and prove one capped opt-in real smoke. No Provider routing framework or UI redesign.

Exit: both real Adapters work through the existing interface under recorded caps.

### F3 — Real end-to-end acceptance

Status: **BLOCKED ON F1 + F2**

Run the fixed Demo from the browser with both real Adapters. Verify:

- exact source and visible claim evidence;
- Script, Budget and Final approvals;
- no paid call before approval or above the cap;
- real Scene visuals and spoken narration;
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
