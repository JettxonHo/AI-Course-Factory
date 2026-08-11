# AI Course Factory Current Status

## 1. Snapshot

| Field | Current Fact |
| --- | --- |
| Date | 2026-08-12 |
| Repository | `JettxonHo/AI-Course-Factory` |
| Branch | `codex/23-character-planning` |
| Reviewed M1-001 Commit | `d05e286b33dbb5e0c855a024b21648a4722861c7` |
| Code Parent | `08085e428db07e5a54a1a5a6a29517c84bba2d0d` |
| Planning Baseline | `4c00eb2139006b250574377a337c60a4a7758af3` |
| Remote | `origin/main@08085e428db07e5a54a1a5a6a29517c84bba2d0d`; M0/M1 branch published as `origin/codex/23-character-planning` |
| Worktrees | One main worktree |
| Open Issue | #23 — M1-001 Character Planning — sole Task Contract |
| Open PR | #24 — draft delivery PR for the approved M0 baseline and M1-001 |
| Current Code Gate | 73 tests passed |
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
- offline Source-to-approved-Script integration path；
- provider-neutral `ProductionAgent.plan_character` with exact Script/approval/lineage checks；
- bounded Character Candidate validation and safe runtime failures；
- external commit through the unchanged Artifact Store to an exact Character Reference；
- equivalent replay and changed-input Commit conflict evidence。

Verification on 2026-08-12:

```text
uv run python -m unittest discover -s tests -v
Ran 73 tests — OK

uv run python -m unittest tests.agents.test_production_agent -v
Ran 4 tests — OK

uv run python -m unittest tests.integration.test_character_planning -v
Ran 3 tests — OK

uv run python -m compileall -q src tests
OK

git diff --check
OK
```

This proves the current offline and no-Provider Character planning slice only. It does not prove Storyboard, Production Request, Budget, persistence, paid Provider, media or deployment behavior.

## 3. Not Implemented

- persistent database or file-backed Artifact/Decision/Checkpoint storage；
- task-level application and local Web Workspace；
- Storyboard/Timeline/Production Request planning；
- Storyboard decision and Budget gate；
- Production Orchestrator or Provider adapters；
- Visual/TTS/media generation；
- Final Video Review、stale/impact、scene retry；
- publish package/export；
- product Model Runtime and real media Provider evidence。

## 4. GitHub State

- Issue #23 is open, its body is the sole READY M1-001 Task Contract, and draft PR #24 is its delivery PR.
- PRs #2 through #22 for Phase 1.4 are merged.
- `main@08085e4` contains the accepted Source-to-approved-Script slice.
- Published commit `d05e286` contains the independently approved five-file Character planning implementation.
- The planning and implementation commits are published on `origin/codex/23-character-planning` but are not merged into `main`.
- GitHub reports no status checks for PR #24; the current evidence is the recorded local test/build run and main-controller independent Review, not remote CI.

Issue #23 remains open while draft PR #24 awaits the remote merge gate.

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
| Luna current discoverability | Visible in current collaboration tool | exact `luna-worker` dispatched for Issue #23 |
| Actual subagent runtime model | RUNTIME_VERIFIED | Luna task `019ff206-22f1-7282-97c4-fe1a324edf4d` `turn_context`: `gpt-5.6-luna / max` |
| Terra migration | Not applicable | No active/done Terra task found in this current run |

Official Codex configuration supports trusted project-scoped `.codex/config.toml` overrides. The current task is a fresh task in this trusted project, and its host-written `turn_context` independently exposes the effective `gpt-5.6-sol / xhigh` runtime values.

The runtime evidence above verifies Agent routing only; it does not prove product Model Runtime or Provider capability.

## 7. M0 Baseline and M1-001 Change

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

Issue #23 implementation is isolated in published commit `d05e286` and changes only:

- `src/ai_course_factory/agents/production_agent.py`；
- `src/ai_course_factory/agents/runtime.py`；
- `src/ai_course_factory/agents/__init__.py`；
- `tests/agents/test_production_agent.py`；
- `tests/integration/test_character_planning.py`。

The main orchestrator requested one review correction to remove redundant public aliases and arbitrary nested constraints. The same Luna narrowed the interface, all gates were rerun, and the final independent verdict is `APPROVED`.

## 8. Open Decisions and Blockers

### Current M1 state

- M0 activation is complete；
- M1 result 1 of 7 is independently approved and published in draft PR #24；
- M1 results 2–7 require new bounded Task Contracts and are not automatically authorized by Issue #23；
- Issue #23 remains open until PR #24 completes its review/merge workflow。

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

1. Complete the PR #24 review/merge gate before advancing the shared Production Agent interface.
2. Do not start Storyboard or another M1 result without its own bounded Task Contract.
3. Keep all real Provider, cost and deployment gates closed.
