# AI Course Factory Current Status

## 1. Snapshot

Observed: 2026-08-15 (Asia/Shanghai)

| Fact | Current evidence |
| --- | --- |
| Product direction | FAST-MVP v1.1 remains accepted history; Product Owner approved the exact Creator Handoff MVP v1.2 Goal and eight defaults on 2026-08-14 |
| Current repository baseline | `main@c4f2f5e07839f9dee87e0c13cdfaf84500c3b629` (Issue #135 / PR #136 merged; H2 complete) |
| Accepted FAST-MVP v1.1 baseline | `main@f388e4ac666e0302bef67796f88a9c32fdc9d1d1` |
| Historical F1 baseline | `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31`; bounded correction integrated through Issue #115 / PR #116 (historical, not the current starting main) |
| Active milestone | H3 Generated Scene Clip import and exact composition, IN PROGRESS |
| Current task | Issue #137 on `codex/137-generated-scene-import`; candidate implementation pending independent review and merge |
| H1 merged implementation and correction evidence | Issue #131 / PR #132 plus Issue #133 / PR #134 are merged at `main@91b4512`; 433-test regression, compileall and Diff checks are recorded as merged H1 evidence |
| H2 accepted implementation evidence | Issue #135 / PR #136 is merged at `main@c4f2f5e`; H2 package/narration replay and 444-test regression evidence are accepted |
| Historical merged regression evidence | 414 local tests passed after Issue #121 / PR #122; no hosted CI is claimed |
| F3 repository gates | Issue #125: 52 focused tests and 422 full tests passed; compileall and Diff/ownership checks passed; no hosted CI is claimed |
| F3 runtime evidence | Fresh browser task acquired live GitHub commit `33e781bf...` and then completed Script v2, real local media, two restarts, Scene 2 replacement, Final approval and byte-identical four-file export replay |
| Product state | FAST-MVP v1.1 remains `COMPLETE / GOAL_APPROVED`; Creator Handoff MVP v1.2 is `APPROVED / ACTIVE`; H0-H2 are complete, H3 Issue #137 is in progress, and H3.5/H4 remain pending |
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

These facts plus Issue #125 prove the corrected fixed live-source browser flow. They do not prove live pricing, paid execution, cloud Provider behavior, deployment or adoption.

## 3a. Issue #113 / PR #114 F1 Evidence (merged)

- Branch: `codex/113-offline-workspace`, based on the F1 starting baseline `main@1673b9c3fe350f0e7bcc3d7d22fb2a56c771bbbc`, merged through PR #114 at the historical `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31` snapshot.
- Facade focused evidence: 16 tests passed, including durable create/open, exact source evidence, versioned Script revision/rejection, script/planning/budget gates, FFmpeg Fixture production, one local Scene replacement with unchanged Provider-attempt facts, final rejection/approval, package export and restart replay.
- Web focused evidence: 12 tests passed, including the three server-rendered view loop, versioned Script actions, Final rejection, bounded failure category/action, same-origin mutation boundaries, browser process reconstruction, playable video/SRT responses and package ZIP response.
- Final candidate regression: 386 local `unittest` tests passed; `compileall` and `git diff --check` are clean on this branch.
- Loopback command smoke: `PYTHONPATH=src uv run python -m ai_course_factory.web --data-dir <explicit-dir> --port 8765` bound `127.0.0.1` and returned the Start view with local security headers.
- These were local deterministic Fixture/code-path facts only; later F2A/F2B/F3 evidence is recorded separately below.

## 3c. Issue #119 / PR #120 F2B Evidence (merged)

- Issue #119 / PR #120 is merged and closed at `main@65ce873`.
- Independent focused review and the opt-in local GPT-SoVITS v2 smoke accepted the explicit external Python 3.11/repository/model/reference configuration, zero-charge attempt records, no Fixture fallback and additive package attribution.
- The 411-test local regression baseline is evidence for the merged code path only; it is not cloud Provider, paid-spend or deployed-runtime evidence.

## 3. FAST-MVP Acceptance

F1, F2A, F2B and F2.5 remain complete for the fixed local Demo. Issue #123 / PR #124 supplied partial media, approval, restart, Scene replacement and export evidence but did not prove live source acquisition. Issue #125 / PR #126 corrected that boundary, repeated the complete same-task browser run and merged at `main@f388e4a`. The planning controller accepted the combined evidence as `GOAL_APPROVED` on 2026-08-14; the durable record is `docs/acceptance/FAST-MVP-v1.1-F3-ACCEPTANCE.md`.

## 3b. Issue #115 / PR #116 F1 Correction Evidence

- Explicit caller-provided Budget amount and attempt caps are preserved; only `None` selects the current offline defaults.
- Explicit zero amount or attempts fails closed at `budget_review`, with no Budget decision, authorization, production attempt or Provider side effect.
- Focused facade verification passed 18 tests; the post-correction full regression passed 388 tests, with `compileall` and `git diff --check` clean.

## 3d. Issue #121 / PR #122 F2.5 Evidence (merged)

- The Warm Editorial Production Desk changes only the frozen templates, stylesheet, text SVG favicon, web presentation test and approved truth-doc updates.
- Independent focused verification passes 15 core web tests and 19 affected web tests; the final full regression passes 414 tests, with `compileall` and `git diff --check` clean.
- Independent browser review completed the Fixture flow and read-only durable F2A/F2B restart view at 1440x900 and 375x812. It confirms no horizontal overflow, active/completed/upcoming navigation, visible focus, 44px targets, playable video, replace/approve/export reachability, compact source/attempt/charge attribution and no raw machine paths.
- The CSS/static contract has no external imports/assets or JavaScript and includes reduced-motion, visible-focus, mobile-breakpoint and long-content wrapping rules. A first review correction raised normal-text contrast above 4.5:1; a compatibility correction restored existing attempt/charge facts in Final.
- PR #122 merged at `main@e155d193`; F2.5 is COMPLETE. Its presentation evidence is separate from the later F3 runtime acceptance.

## 3e. Issue #123 / #124 Partial F3 Media Evidence

- Historical candidate run: placeholder Fixture source plus exact Script v2 decision binding, unchanged 18,000-micros/two-attempt Budget approval, and no media side effect before authorization; source acquisition remains unproven.
- Real local media: six imported visual plus six GPT-SoVITS voice attempts, all succeeded at zero charge; H.264 540x960 24fps, AAC 48k mono, mov_text and six nonempty SRT cues.
- Scene recovery: Scene 2 Clip and Video advanced to v2 while its voice, Scene Audio, Master Audio and every unaffected Scene selection stayed exact; no new voice attempt was created.
- Recovery/export: two process restarts performed no regeneration; Video/SRT/ZIP endpoints replayed HTTP 200 and byte-identical outputs; the ZIP contains exactly video, subtitle, GitHub/visual/TTS attribution and Artifact Manifest.
- UX: the Warm Editorial UI completed the full flow at 1440x900 and 375x812 without horizontal overflow, with visible keyboard focus and no raw machine paths.
- These bullets remain historical media/recovery evidence only; they do not prove live GitHub acquisition or final Goal approval.
- Repository gates: 37 focused tests and the complete 414-test local regression passed on the historical candidate; Issue #125 / PR #126 later supplied the separate accepted source-correction gates recorded below.

## 3f. Issue #125 Corrected F3 Live-Source Evidence

- Fresh GET displayed source intake with zero task, Artifact, Budget or media records. An unsupported URL made zero connector calls and left durable state empty.
- The browser submitted the exact supported URL. The default connector acquired upstream commit `33e781bf7bfb9b39fd27c4e4a3e592669b52cb4b`, path `lessons/1-Intro/README.md` and blob `6b29b141e0f0f81477e16bee4e4d1e6222d0579c`; an independent same-run connector read matched all three facts.
- The same task revised and approved Script v2, approved the unchanged 18,000-micros/two-attempt Budget, generated six imported visuals and six GPT-SoVITS voices, restarted twice, replaced only Scene 2 visual, approved Video v2 and exported the exact four-file package.
- After the second restart, Video, SRT and ZIP endpoints returned HTTP 200 with byte-identical hashes. Attempts remained exactly six visual plus six voice, all succeeded and charged zero; Scene 2 voice, Scene Audio, Master Audio and every unaffected Scene reference remained exact.
- Independent FFprobe reported H.264 540x960 `yuv420p` 24fps, AAC 48kHz mono, `mov_text` and 60 seconds. Local CPU transcription confirmed six non-silent, intelligible Chinese narrations.
- Main-controller verification passed 52 focused tests and the final 422-test regression; compileall, `git diff --check` and exact ownership review passed. No hosted checks are claimed.

## 4. Current Concurrent Work

F0 is complete. Issue #110 passed independent review and merged through PR #111. F1 then merged through PR #114; the historical F1 correction snapshot was `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31`. Issue #117 / PR #118 subsequently merged and closed at `main@b2642c1` after independent 397-test regression evidence; F2A is COMPLETE, and its creator-supplied local bridge does not call a Visual Provider or claim F3 completion.

Issue #113 / PR #114 completed the single vertical F1 workspace contract.

Issue #115 / PR #116 corrected explicit Budget cap binding without changing the F1 flow, Budget domain, Provider interfaces or F1 completion state.

Issue #117 / PR #118 is merged and closed at `main@b2642c1`; F2A is independently accepted COMPLETE. Its historical candidate-time document phrases were corrected with the next feature PR rather than a status-only PR.

Issue #119 / PR #120 is merged and independently accepted COMPLETE. It adds local GPT-SoVITS v2 through explicit external Python 3.11/repository/model/reference configuration, with six zero-charge voice attempts, no Fixture fallback, and additive package attribution.

Issue #121 / PR #122 merged the independently accepted Warm Editorial presentation at `main@e155d193`. Issue #123 / PR #124 then supplied partial F3 media evidence without proving live source acquisition; Issue #125 / PR #126 supplied and merged the accepted bounded correction at `main@f388e4a`.

Issue #129 closed and its exact docs Diff merged through PR #130; H0 is COMPLETE. Issue #131 / PR #132 implemented the bounded H1 contract and Issue #133 / PR #134 corrected repeated HTTP approval replay; both are merged at `main@91b4512`, so H1 is COMPLETE. Issue #135 / PR #136 is merged at `main@c4f2f5e` with accepted 444-test regression evidence, so H2 is COMPLETE. Issue #137 is the active H3 candidate and remains in progress pending independent review.

## 5. Current Direction

FAST-MVP v1.1 remains complete for the fixed local single-user product. The active Creator Handoff v1.2 Goal sends exact generation instructions and narration/SRT to the Creator, who generates Scene videos manually in a subscription UI; exact clips then return for local composition and Final Review. `GOAL.md` is the execution truth and `docs/goals/CREATOR-HANDOFF-MVP-v1.2-PROPOSAL.md` records the approved underlying contract.

The selected vertical design adds a Scene Generation Contract, an adjacent pre-generation Creator Handoff Package and an explicit Imported Generated Scene Clip boundary. It preserves the generic Artifact repository, `scene_clip` identity/version chain, Task selection/stale impact, GPT-SoVITS narration, FFmpeg composition behavior, Final Video decision and post-approval Publish Package. H3 Issue #137 is implementing the bounded public-contract expansion: an honest no-attempt creator-import Clip payload, matching Task/composition input support and a Final gate that proves all six selected Clips bind the same exact contract. F2A still-image output remains readable Preview/technical evidence and cannot satisfy that gate. H3.5 Simplified-Chinese workspace redesign and H4 human watch/listen acceptance remain pending.

The approved first import interaction is fixed: one operator-declared generated-clips directory at startup/configuration, exact `scene-1.mp4` through `scene-6.mp4`, a Review-page POST that preflights the whole set before import, and exact `scene-2-replacement.mp4` for re-import. The manual path bypasses Budget Authorization and instead uses non-monetary local readiness; external subscription cost is explicitly outside application control.

## 6. Authorization and Evidence Boundary

Authorized now:

- H2 Issue #135 / PR #136 is complete at `main@c4f2f5e` with accepted 444-test evidence;
- H3 Issue #137 implementation and independent review under the exact approved Task Contract;
- H3.5 and H4 planning only until their own bounded Task Contracts are approved;
- bounded maintenance of the merged F1 flow;
- maintenance of the accepted fixed local Demo;
- no-cost local validation and evidence replay.

Not authorized now:

- H3.5/H4 implementation or a Luna dispatch before each exact milestone Task Contract passes review;
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
