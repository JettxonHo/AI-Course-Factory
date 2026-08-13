# AI Course Factory Current Status

## 1. Snapshot

Observed: 2026-08-13 (Asia/Shanghai)

| Fact | Current evidence |
| --- | --- |
| Product direction | Product Owner approved FAST-MVP v1.1 on 2026-08-13 |
| Merged baseline | `origin/main@ec36d5e818315695e5462a95f8e48af33d8a5f98` |
| Active planning branch | `codex/fast-mvp-rebaseline-integration` |
| Current implementation task | None; F1 is Ready and needs one unique Task Contract |
| Merged regression evidence | 356 local tests passed after M3-010; no hosted CI is claimed |
| Rebaseline validation | 356/356 local tests passed on the integration branch with the explicit `PYTHONPATH=src` command below |
| Real product runtime | Not yet verified: no local web workspace and no real Visual/TTS end-to-end evidence |
| Provider authorization | Not granted; `PD-001`–`PD-003` remain required |

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

These facts prove a substantial offline backend. They do not prove a usable UI, prompt-faithful visuals, spoken TTS, live pricing, paid execution, deployment or adoption.

## 3. Missing for FAST-MVP

1. One application facade joining the existing modules into task-level use cases.
2. A browser workspace for source input, evidence, approvals, status, video review, Scene action and export.
3. One authorized real Visual Adapter.
4. One authorized real TTS Adapter.
5. One capped browser-driven real end-to-end Demo and exported evidence package.

## 4. Current Concurrent Work

F0 is complete. Issue #110 passed independent review and merged through PR #111 at `main@ec36d5e`; focused tests were 10 application + 6 SQLite integration, and the post-merge full regression was 356/356.

There is no current implementation Task Contract. F1 must remain one vertical workspace Issue and one main PR.

## 5. Current Direction and Next Actions

1. Merge the FAST-MVP rebaseline.
2. Open one F1 vertical workspace Issue/PR and dispatch exact `luna-worker`.
3. Demonstrate the complete offline browser path with local/Fake media and FFmpeg.
4. Ask the Product Owner for `PD-001`, `PD-002` and `PD-003` only when F1 can consume real Adapters.
5. Implement the real Visual and TTS Adapters, then run F3 acceptance.

Do not open new horizontal hardening, status-only or future-architecture tasks before F1 unless an observed blocker requires them.

## 6. Authorization and Evidence Boundary

Authorized now:

- FAST-MVP planning/docs;
- Issue #110 review/merge-or-park;
- F1 offline application/UI implementation and no-cost local validation.

Not authorized now:

- Provider selection, credentials or real calls;
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
