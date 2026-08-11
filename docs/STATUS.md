# AI Course Factory Current Status

## 1. Snapshot

| Field | Current Fact |
| --- | --- |
| Date | 2026-08-12 |
| Repository | `JettxonHo/AI-Course-Factory` |
| Branch | `main` during M0 planning-baseline finalization |
| Code Parent | `08085e428db07e5a54a1a5a6a29517c84bba2d0d` |
| Planning Baseline | Approved v1.0 truth sources in the M0 baseline commit containing this snapshot |
| Remote | `origin/main` at same commit when checked |
| Worktrees | One main worktree |
| Open Issue | #23 — W3-T001 Character Artifact Planning |
| Open PR | None |
| Current Code Gate | 66 tests passed |
| Product Goal | Approved and active as long-term Codex Goal `019ff1fc-4b0b-7e92-9fd1-c63a5679fe3b` |
| Real Provider | Not selected or authorized |
| Deployment | None |

STATUS is a verified snapshot, not a source of product requirements or coding authorization.

## 2. Implemented and Verified

- Public GitHub repository validation and bounded acquisition；
- exact source commit/blob identity and lossless normalization；
- Source Record Candidate and immutable Commit；
- source-closed Knowledge Candidate with evidence locators；
- Course/Episode Plan and six-scene grounded Script Candidate；
- explicit Script revision without overwrite；
- Script assessment, Hard Block and exact Creator decision；
- LangGraph mandatory Script Review interrupt/resume；
- decision persisted before resume；
- offline Source-to-approved-Script integration path。

Verification on 2026-08-12:

```text
uv run python -m unittest discover -s tests -v
Ran 66 tests — OK

uv run python -m compileall -q src tests
OK

git diff --check
OK
```

This proves the current offline slice only.

## 3. Not Implemented

- persistent database or file-backed Artifact/Decision/Checkpoint storage；
- task-level application and local Web Workspace；
- Production Agent and Character/Storyboard/Timeline/Request；
- Storyboard decision and Budget gate；
- Production Orchestrator or Provider adapters；
- Visual/TTS/media generation；
- Final Video Review、stale/impact、scene retry；
- publish package/export；
- real model/media provider runtime evidence。

## 4. GitHub State

- Issue #23 is open and has no matching PR.
- PRs #2 through #22 for Phase 1.4 are merged.
- `main@08085e4` contains the accepted Source-to-approved-Script slice.
- The Issue #23 Task Package link is not present on remote `main` because its source documents remain untracked locally.

Issue #23 must not be dispatched until the new Goal is approved and its contract is reconciled with the v1.0 truth sources.

## 5. Protected Untracked Materials

The following pre-existing/in-flight files are user-owned and must not be overwritten, moved, staged or deleted without a separate decision:

- `docs/planning/AI_Course_Factory_MVP_Phase_1.5_Production_Boundary_Validation_Plan_v0.1.md`
- `docs/implementation-plan/AI_Course_Factory_MVP_Phase_1.5_Implementation_Plan_Addendum_v0.1.md`
- `docs/implementation-task/AI_Course_Factory_MVP_W3_First_Bounded_Task_Instance_v0.1.md`
- `docs/implementation-task/AI_Course_Factory_MVP_W3_T001_Task_Package_v0.1.md`
- `docs/implementation-task/AI_Course_Factory_MVP_W3_T001_Dispatch_Preparation_Record_v0.1.md`

The Dispatch Preparation Record appeared during the 2026-08-12 planning run and was not created by this planning change. It is preserved as concurrent user work.

All five exact paths are locally excluded through `.git/info/exclude`. `git check-ignore -v` resolves each path to that file, and none is tracked. This is a local protection measure only; it does not archive, move, modify or authorize committing the materials.

## 6. Agent and Model State

| Item | State | Evidence |
| --- | --- | --- |
| Project orchestrator config | CONFIG_VERIFIED | `.codex/config.toml`: `gpt-5.6-sol / xhigh` |
| Codex config load | CONFIG_VERIFIED | `codex --strict-config doctor --json`: `config.load` is `ok`, effective model `gpt-5.6-sol`; overall doctor is non-zero only for the non-interactive `TERM=dumb` check |
| Current main task runtime | RUNTIME_VERIFIED | Current task `turn_context` records model `gpt-5.6-sol` and effort `xhigh` |
| `luna-worker` file | CONFIG_VERIFIED | `~/.codex/agents/luna-worker.toml` parsed with Python 3.12 |
| Luna configured model | CONFIG_VERIFIED | `gpt-5.6-luna / max` |
| Luna current discoverability | Visible in current collaboration tool | No worker spawned in this planning Goal |
| Actual subagent runtime model | UNVERIFIED_RUNTIME_MODEL | No implementation invocation performed |
| Terra migration | Not applicable | No active/done Terra task found in this current run |

Official Codex configuration supports trusted project-scoped `.codex/config.toml` overrides. The current task is a fresh task in this trusted project, and its host-written `turn_context` independently exposes the effective `gpt-5.6-sol / xhigh` runtime values.

No model configuration or task creation is evidence that W3-T001 implementation has started.

## 7. Current Planning Change

The M0 planning-baseline commit containing this snapshot establishes these approved v1.0 truth sources:

- `.codex/config.toml`
- `README.md`
- `AGENTS.md`
- `docs/README.md`
- `docs/product/PRD.md`
- `docs/spec/SYSTEM-SPEC.md`
- `docs/spec/IMPLEMENTATION-SPEC.md`
- `docs/DEVELOPMENT-WORKFLOW.md`
- `GOAL.md`
- this STATUS update
- decision D-002 in `docs/decision-log.md`

These are approved planning artifacts. They do not change product runtime behavior and do not include the five protected in-flight files.

## 8. Open Decisions and Blockers

### Blocks first M1 implementation dispatch

- reconcile Issue #23 with the approved Goal/Specs and establish it as the one authoritative Task Contract；
- create the assigned Issue branch from the approved planning baseline；
- validate exact `luna-worker` routing and runtime at dispatch time。

### Blocks only real Provider milestone

- PD-001 Visual Provider/model/credentials；
- PD-002 TTS Provider/voice/credentials；
- PD-003 smoke/full Demo budget and attempt limit。

### Does not currently block

- Product baseline and Goal approval；
- leaving the five protected untracked files untouched and explicitly excluded from implementation changes；
- No-Provider Production Planning after the dispatch gates pass；
- Fake Adapter and offline media composition；
- persistence and local workspace work within M1–M4。

## 9. Next Ordered Actions

1. Commit the approved v1.0 planning baseline without the five protected Phase 1.5 files.
2. Reconcile Issue #23 to the approved Goal and make its body the single bounded M1 Task Contract.
3. Create the assigned Issue branch and validate exact `luna-worker` routing/runtime.
4. Start the smallest approved M1 Task only; do not begin Provider calls.
