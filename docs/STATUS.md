# AI Course Factory Current Status

## 1. Snapshot

Observed: 2026-08-13 (Asia/Shanghai)

| Fact | Current evidence |
| --- | --- |
| Product direction | Product Owner approved FAST-MVP v1.1 on 2026-08-13 |
| Merged baseline | `origin/main@5d4cae8bcb45e15cba036c45fc673f6245117a6b` |
| Active planning branch | `codex/fast-mvp-rebaseline` in an isolated worktree |
| Current implementation task | GitHub Issue #110 is open in the primary worktree |
| Merged regression evidence | 340 local tests passed for the M3-009 package baseline; no hosted CI is claimed |
| Rebaseline validation | 340/340 local tests passed in the isolated worktree with the explicit `PYTHONPATH=src` command below |
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

These facts prove a substantial offline backend. They do not prove a usable UI, prompt-faithful visuals, spoken TTS, live pricing, paid execution, deployment or adoption.

## 3. Missing for FAST-MVP

1. One application facade joining the existing modules into task-level use cases.
2. A browser workspace for source input, evidence, approvals, status, video review, Scene action and export.
3. Merged minimal Scene media selection/retry behavior.
4. One authorized real Visual Adapter.
5. One authorized real TTS Adapter.
6. One capped browser-driven real end-to-end Demo and exported evidence package.

## 4. Current Concurrent Work

Issue #110 — **M3-010: durable scene-scoped Task media projection contract** — is open. At the time of this snapshot, the primary worktree contains an unmerged candidate touching:

- `src/ai_course_factory/application/__init__.py`;
- `src/ai_course_factory/application/media_task.py`;
- `src/ai_course_factory/application/sqlite_media_task.py`;
- `tests/application/test_task_media_projection.py`;
- `tests/integration/test_sqlite_task_media_projection.py`.

Reported focused evidence is 13 passing tests. The candidate is not merged evidence until the main controller independently reviews the actual Diff and runs the full regression.

F0 disposition:

- merge after one bounded review if it fits the vertical workspace without architectural rework; or
- park it intact if another redesign/correction cycle is required.

No other task may overwrite or clean these files.

## 5. Current Direction and Next Actions

1. Merge the FAST-MVP rebaseline.
2. Resolve Issue #110 using the F0 rule.
3. Open one F1 vertical workspace Issue/PR and dispatch exact `luna-worker`.
4. Demonstrate the complete offline browser path with local/Fake media and FFmpeg.
5. Ask the Product Owner for `PD-001`, `PD-002` and `PD-003` only when F1 can consume real Adapters.
6. Implement the real Visual and TTS Adapters, then run F3 acceptance.

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
