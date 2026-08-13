# AI Course Factory Current Status

## 1. Snapshot

Observed: 2026-08-13 (Asia/Shanghai)

| Fact | Current evidence |
| --- | --- |
| Product direction | Product Owner approved FAST-MVP v1.1 on 2026-08-13 |
| Current starting main | `main@b2642c18449e6d79b3b19fec39b7aeff564bf711` |
| Historical F1 baseline | `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31`; bounded correction integrated through Issue #115 / PR #116 (historical, not the current starting main) |
| Active planning branch | `codex/119-local-gpt-sovits-tts` |
| Current implementation task | Issue #119 F2B local GPT-SoVITS v2 TTS; candidate implementation pending independent review |
| Historical merged regression evidence | 388 local tests passed after the F1 correction; no hosted CI is claimed |
| Rebaseline validation | 356/356 local tests passed on the integration branch with the explicit `PYTHONPATH=src` command below |
| Real product runtime | F2A Desktop ImageGen visual assets and local conversion independently accepted; F2B GPT-SoVITS runtime smoke remains opt-in candidate evidence |
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

These facts prove a substantial offline backend, accepted creator-supplied visuals and a bounded local TTS candidate. They do not prove the final browser acceptance package, live pricing, paid execution, deployment or adoption.

## 3a. Issue #113 / PR #114 F1 Evidence (merged)

- Branch: `codex/113-offline-workspace`, based on the F1 starting baseline `main@1673b9c3fe350f0e7bcc3d7d22fb2a56c771bbbc`, merged into current `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31` through PR #114.
- Facade focused evidence: 16 tests passed, including durable create/open, exact source evidence, versioned Script revision/rejection, script/planning/budget gates, FFmpeg Fixture production, one local Scene replacement with unchanged Provider-attempt facts, final rejection/approval, package export and restart replay.
- Web focused evidence: 12 tests passed, including the three server-rendered view loop, versioned Script actions, Final rejection, bounded failure category/action, same-origin mutation boundaries, browser process reconstruction, playable video/SRT responses and package ZIP response.
- Final candidate regression: 386 local `unittest` tests passed; `compileall` and `git diff --check` are clean on this branch.
- Loopback command smoke: `PYTHONPATH=src uv run python -m ai_course_factory.web --data-dir <explicit-dir> --port 8765` bound `127.0.0.1` and returned the Start view with local security headers.
- These are local deterministic Fixture/code-path facts only; F2/F3 and real Provider/runtime acceptance remain incomplete.

## 3. Missing for FAST-MVP

With F1 and the F2A visual bridge accepted, remaining FAST-MVP work is:

1. Independent acceptance of the authorized local GPT-SoVITS TTS Adapter.
2. The separately authorized F2.5 product outcome.
3. One capped browser-driven real end-to-end Demo and exported evidence package.

## 3b. Issue #115 / PR #116 F1 Correction Evidence

- Explicit caller-provided Budget amount and attempt caps are preserved; only `None` selects the current offline defaults.
- Explicit zero amount or attempts fails closed at `budget_review`, with no Budget decision, authorization, production attempt or Provider side effect.
- Focused facade verification passed 18 tests; the post-correction full regression passed 388 tests, with `compileall` and `git diff --check` clean.

## 4. Current Concurrent Work

F0 is complete. Issue #110 passed independent review and merged through PR #111. F1 then merged through PR #114; the historical F1 correction snapshot was `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31`. Issue #117 / PR #118 subsequently merged and closed at `main@b2642c1` after independent 397-test regression evidence; F2A is COMPLETE, and its creator-supplied local bridge does not call a Visual Provider or claim F3 completion.

Issue #113 / PR #114 completed the single vertical F1 workspace contract.

Issue #115 / PR #116 corrected explicit Budget cap binding without changing the F1 flow, Budget domain, Provider interfaces or F1 completion state.

Issue #117 / PR #118 is merged and closed at `main@b2642c1`; F2A is independently accepted COMPLETE. Its two historical candidate-time document phrases are corrected in this feature PR rather than a status-only PR.

Issue #119 is the active F2B candidate. It adds local GPT-SoVITS v2 through explicit external Python 3.11/repository/model/reference configuration, with six zero-charge voice attempts, no Fixture fallback, and additive package attribution. F2.5 and F3 remain incomplete.

## 5. Current Direction and Next Actions

1. Complete independent review and opt-in local GPT-SoVITS smoke for Issue #119.
2. Implement the separately authorized F2.5 decision/outcome.
3. Run F3 acceptance through the same browser flow.

Do not open new horizontal hardening, status-only or future-architecture tasks while F2 remains blocked unless an observed blocker requires them.

## 6. Authorization and Evidence Boundary

Authorized now:

- FAST-MVP planning/docs;
- bounded maintenance of the merged F1 flow;
- bounded no-cost local GPT-SoVITS F2B implementation and validation;
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
