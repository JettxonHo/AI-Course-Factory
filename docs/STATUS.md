# AI Course Factory Current Status

## 1. Snapshot

Observed: 2026-08-14 (Asia/Shanghai)

| Fact | Current evidence |
| --- | --- |
| Product direction | Product Owner approved FAST-MVP v1.1 on 2026-08-13 |
| F3 acceptance baseline | Historical media baseline `main@e155d193032aad6a9c98e1e8cbebd4e10febdbc6`; correction baseline `af61d31e949e20947517ba4d8ab6db867b6a5017` |
| Historical F1 baseline | `main@cf458341f4e6bdd324e51ebfc835f19c4a2b0e31`; bounded correction integrated through Issue #115 / PR #116 (historical, not the current starting main) |
| Acceptance branch | `codex/125-live-source-f3-correction` |
| Current task | Issue #125 live-source correction is `APPROVED FOR MERGE`; #123/#124 remains partial historical media evidence |
| Historical merged regression evidence | 414 local tests passed after Issue #121 / PR #122; no hosted CI is claimed |
| F3 repository gates | Issue #125: 52 focused tests and 422 full tests passed; compileall and Diff/ownership checks passed; no hosted CI is claimed |
| F3 runtime evidence | Fresh browser task acquired live GitHub commit `33e781bf...` and then completed Script v2, real local media, two restarts, Scene 2 replacement, Final approval and byte-identical four-file export replay |
| Product state | F1, F2A, F2B and F2.5 are COMPLETE; F3 correction is `APPROVED FOR MERGE`, with final planning Goal verdict pending after merge |
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

F1, F2A, F2B and F2.5 remain complete for the fixed local Demo. Issue #123 / PR #124 supplied partial media, approval, restart, Scene replacement and export evidence but did not prove live source acquisition. Issue #125 corrected that boundary and repeated the complete same-task browser run. The durable candidate record is `docs/acceptance/FAST-MVP-v1.1-F3-ACCEPTANCE.md`; final Goal approval remains a post-merge planning verdict.

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
- Repository gates: 37 focused tests and the complete 414-test local regression passed on the historical candidate; Issue #125 adds a separate source-correction gate and does not claim the final full regression yet.

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

Issue #121 / PR #122 merged the independently accepted Warm Editorial presentation at `main@e155d193`. Issue #123 / PR #124 then supplied partial F3 media evidence without proving live source acquisition; Issue #125 owns and has passed the bounded correction candidate.

## 5. Current Direction

Merge the independently approved Issue #125 correction, then request the planning controller's final Goal verdict on the merged result. Any cloud Provider, paid use, deployment, publication, multiple-task/user expansion or new Goal requires separate Product Owner authorization.

## 6. Authorization and Evidence Boundary

Authorized now:

- FAST-MVP planning/docs;
- bounded maintenance of the merged F1 flow;
- maintenance of the accepted fixed local Demo;
- no-cost local validation and evidence replay.

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
