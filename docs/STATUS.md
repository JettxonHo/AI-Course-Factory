# AI Course Factory Current Status

## 1. Snapshot

Observed: 2026-08-14 (Asia/Shanghai)

| Fact | Current evidence |
| --- | --- |
| Product direction | Product Owner approved FAST-MVP v1.1 on 2026-08-13 |
| Current starting main | `main@65ce873f2dd5fccdcccf1ce5c5c1970071bb6261` |
| Historical F1 baseline | `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31`; bounded correction integrated through Issue #115 / PR #116 (historical, not the current starting main) |
| Active planning branch | `codex/121-warm-editorial-workspace` |
| Current implementation task | Issue #121 F2.5 Warm Editorial Production Desk; independently reviewed and APPROVED FOR MERGE |
| Historical merged regression evidence | 411 local tests passed after Issue #119 / PR #120; no hosted CI is claimed |
| Rebaseline validation | 411/411 local tests passed on `main@65ce873` with the explicit `PYTHONPATH=src` command below |
| Real product runtime | F2A Desktop ImageGen visual assets and local conversion independently accepted; F2B local GPT-SoVITS v2 is independently accepted COMPLETE; F2.5 local browser presentation is approved for merge, not F3 acceptance |
| Provider authorization | `PD-002` approved for local GPT-SoVITS v2; no cloud credentials, external charge or deployment authorized |

This file is a current snapshot, not authorization and not a historical PR transcript. Git and GitHub retain detailed history.

## 2. Implemented and Locally Verified on Main

- Exact-commit public GitHub acquisition and normalized Source Record.
- Grounded Knowledge, Course/Episode Plan and six-Scene Script planning.
- Script and Storyboard assessment/decision behavior.
- Character, Storyboard, Timeline, Production Request and Budget planning.
- Immutable Artifact model plus SQLite Artifact/decision/budget/task persistence.
- Script and Final Video workflow checkpoints and application coordination.
- Task-scoped filesystem workspace and Provider-attempt ledger.
- Provider-neutral Visual/TTS interfaces and deterministic Fake media.
- Claim-gated offline Production Orchestrator.
- Playable local FFmpeg Fixture generation/composition.
- Exact Scene Clip/Audio, Subtitle, logical Master Audio and Video Artifacts.
- Mandatory Final Video Review.
- Deterministic local Publish Package and Artifact Manifest.
- Durable current/stale Scene and delivery media projection merged through Issue #110 / PR #111.

These facts prove a substantial offline backend, accepted creator-supplied visuals and an accepted bounded local TTS path. They do not prove the final browser acceptance package, live pricing, paid execution, deployment or adoption.

## 3a. Issue #113 / PR #114 F1 Evidence (merged)

- Branch: `codex/113-offline-workspace`, based on the F1 starting baseline `main@1673b9c3fe350f0e7bcc3d7d22fb2a56c771bbbc`, merged into current `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31` through PR #114.
- Facade focused evidence: 16 tests passed, including durable create/open, exact source evidence, versioned Script revision/rejection, script/planning/budget gates, FFmpeg Fixture production, one local Scene replacement with unchanged Provider-attempt facts, final rejection/approval, package export and restart replay.
- Web focused evidence: 12 tests passed, including the three server-rendered view loop, versioned Script actions, Final rejection, bounded failure category/action, same-origin mutation boundaries, browser process reconstruction, playable video/SRT responses and package ZIP response.
- Final candidate regression: 386 local `unittest` tests passed; `compileall` and `git diff --check` are clean on this branch.
- Loopback command smoke: `PYTHONPATH=src uv run python -m ai_course_factory.web --data-dir <explicit-dir> --port 8765` bound `127.0.0.1` and returned the Start view with local security headers.
- These are local deterministic Fixture/code-path facts only; F2/F3 and real Provider/runtime acceptance remain incomplete.

## 3c. Issue #119 / PR #120 F2B Evidence (merged)

- Issue #119 / PR #120 is merged and closed at `main@65ce873`.
- Independent focused review and the opt-in local GPT-SoVITS v2 smoke accepted the explicit external Python 3.11/repository/model/reference configuration, zero-charge attempt records, no Fixture fallback and additive package attribution.
- The 411-test local regression baseline is evidence for the merged code path only; it is not cloud Provider, paid-spend or deployed-runtime evidence.

## 3. Missing for FAST-MVP

With F1, F2A and F2B accepted, remaining FAST-MVP work is:

1. Independent acceptance of the F2.5 Warm Editorial Production Desk presentation.
2. One capped browser-driven real end-to-end Demo and exported evidence package.

## 3b. Issue #115 / PR #116 F1 Correction Evidence

- Explicit caller-provided Budget amount and attempt caps are preserved; only `None` selects the current offline defaults.
- Explicit zero amount or attempts fails closed at `budget_review`, with no Budget decision, authorization, production attempt or Provider side effect.
- Focused facade verification passed 18 tests; the post-correction full regression passed 388 tests, with `compileall` and `git diff --check` clean.

## 3d. Issue #121 F2.5 Approved-for-merge Evidence

- The Warm Editorial Production Desk changes only the frozen templates, stylesheet, text SVG favicon, web presentation test and approved truth-doc updates.
- Independent focused verification passes 15 core web tests and 19 affected web tests; the final full regression passes 414 tests, with `compileall` and `git diff --check` clean.
- Independent browser review completed the Fixture flow and read-only durable F2A/F2B restart view at 1440x900 and 375x812. It confirms no horizontal overflow, active/completed/upcoming navigation, visible focus, 44px targets, playable video, replace/approve/export reachability, compact source/attempt/charge attribution and no raw machine paths.
- The CSS/static contract has no external imports/assets or JavaScript and includes reduced-motion, visible-focus, mobile-breakpoint and long-content wrapping rules. A first review correction raised normal-text contrast above 4.5:1; a compatibility correction restored existing attempt/charge facts in Final.
- Main-controller verdict is APPROVED FOR MERGE. This is not F3 acceptance or FAST-MVP completion.

## 4. Current Concurrent Work

F0 is complete. Issue #110 passed independent review and merged through PR #111. F1 then merged through PR #114; the historical F1 correction snapshot was `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31`. Issue #117 / PR #118 subsequently merged and closed at `main@b2642c1` after independent 397-test regression evidence; F2A is COMPLETE, and its creator-supplied local bridge does not call a Visual Provider or claim F3 completion.

Issue #113 / PR #114 completed the single vertical F1 workspace contract.

Issue #115 / PR #116 corrected explicit Budget cap binding without changing the F1 flow, Budget domain, Provider interfaces or F1 completion state.

Issue #117 / PR #118 is merged and closed at `main@b2642c1`; F2A is independently accepted COMPLETE. Its two historical candidate-time document phrases are corrected in this feature PR rather than a status-only PR.

Issue #119 / PR #120 is merged and independently accepted COMPLETE. It adds local GPT-SoVITS v2 through explicit external Python 3.11/repository/model/reference configuration, with six zero-charge voice attempts, no Fixture fallback, and additive package attribution.

Issue #121 is independently reviewed and APPROVED FOR MERGE. It upgrades only the three existing server-rendered views and local stylesheet with the approved Warm Editorial Production Desk direction; no route, view-model, form, media or Provider behavior changes are in scope. F3 remains blocked until this PR is merged.

## 5. Current Direction and Next Actions

1. Merge the independently accepted Issue #121 F2.5 presentation.
2. Run F3 acceptance through the same browser flow after the F2.5 merge.

Do not open new horizontal hardening, status-only or future-architecture tasks while F2 remains blocked unless an observed blocker requires them.

## 6. Authorization and Evidence Boundary

Authorized now:

- FAST-MVP planning/docs;
- bounded maintenance of the merged F1 flow;
- bounded F2.5 presentation implementation and no-cost local validation;
- no-cost local validation.

Not authorized now:

- cloud Provider selection, credentials or real calls;
- any fee or budget increase;
- deployment or external publication;
- destructive migration or broad rewrite.

Agent configuration is `gpt-5.6-sol / xhigh` for the main controller and exact `luna-worker` configured as `gpt-5.6-luna / max` for implementation. Configuration presence is `CONFIG_VERIFIED`; runtime identity is claimed only when the active runtime exposes it.

## 7. Verification Commands

Base regression:

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

Each Issue adds only focused commands that prove its acceptance behavior. Fake/Fixture results remain offline evidence and must not be described as real Provider success.

## 8. Historical Evidence

Detailed milestone, Issue, commit, correction-round and test-count history remains available in Git, closed GitHub Issues/PRs and repository history. It is intentionally not duplicated here; daily development starts from the current facts above.
