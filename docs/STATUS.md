# AI Course Factory Current Status

## 1. Snapshot

| Field | Current Fact |
| --- | --- |
| Date | 2026-08-12 |
| Repository | `JettxonHo/AI-Course-Factory` |
| Canonical Branch | `main` |
| Merged M1-001 Commit | `d05e286b33dbb5e0c855a024b21648a4722861c7` |
| Reviewed M1-002 Commit | `bb8e4974d3da96138ad466013bdee83cf8ee77f7` |
| Reviewed M1-003 Commit | `047ce29660e25c9d3e9407f1df3d1a53a2504272` |
| Reviewed M1-004 Commit | `77a360d8705209c8c70e9165de896c9bc7331359` |
| Reviewed M1-005 Commit | `1838819bcba7633fc057b77035d1e71f3da155eb` |
| Reviewed M1-006 Commit | `7ee3677a0640e5e454c2a81c354c4aff70191a54` |
| Reviewed M1-007 Commit | `6ccb19778e5620451cf4314a91ed738acedaa177` |
| Reviewed M2-001 Commit | `ce2db9a1d315dd250754e1427eacd6d9b058ddb7` |
| Latest Feature Baseline | M2-001 merged at `main@922d6c1fff14f536d836582b4d16f60375a01a3c` |
| Planning Baseline | `4c00eb2139006b250574377a337c60a4a7758af3` |
| Remote Canonical | `origin/main`; live HEAD is authoritative for transient docs-only merges |
| Worktrees | One main worktree |
| Current Task Contract | None; #43 is closed after M2-001 completion |
| Open PR | None |
| Current Code Gate | 131 tests passed on merged `main@922d6c1` |
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
- provider-neutral `ProductionAgent.plan_storyboard` with exact Script/approval/Character lineage checks；
- dynamic ordered Storyboard scene validation derived from the Script rather than a hardcoded system count；
- external commit through the unchanged Artifact Store to an exact Storyboard Reference；
- Character and Storyboard equivalent replay and changed-input Commit conflict evidence；
- exact in-memory Storyboard decision bound to the committed Storyboard/Script/Character lineage；
- enabled approve/reject/revise and disabled explicit-skip decision semantics with immutable replay/conflict behavior；
- provider-neutral `ProductionAgent.plan_timeline` with exact Script/Character/Storyboard and satisfying Storyboard-decision checks；
- Script-derived, zero-based, contiguous ordered Timeline timing with finite/duration/result normalization；
- external commit through the unchanged Artifact Store to an exact Timeline Reference；
- Timeline equivalent replay, changed-input Commit conflict and malformed-result non-Commit evidence；
- provider-neutral `ProductionAgent.plan_request` with exact Script/Character/Storyboard/Timeline and satisfying decision checks；
- exact language/aspect/timing/narration/visual/character/continuity aggregation with provider-specific fields rejected；
- external commit through the unchanged Artifact Store to an exact Production Request Reference；
- Production Request equivalent replay, changed-input Commit conflict and malformed-result non-Commit evidence；
- deterministic provider-neutral `BudgetModule.estimate` from one exact Production Request and Request-bound local Fixture price snapshot；
- integer-micros price arithmetic, complete visual/voice Scene coverage and bounded 1–3 attempt policy；
- external commit through the unchanged Artifact Store to an exact Production Budget Reference；
- mandatory in-memory Creator Budget Review approve/reject decision and independent Authorization after valid approval；
- Authorization bound to exact Request/Budget References, canonical snapshot, approved amount/attempt caps, Creator/time/decision identity；
- Budget Commit replay/conflict, underfunded/stale/mutated Budget rejection and new-Request-Version isolation evidence；
- offline cross-slice exact approved Script -> Character -> Storyboard decision -> Timeline -> Production Request -> Production Budget -> independent Authorization integration evidence；
- the integrated deterministic runtime invokes only Character/Storyboard/Timeline/Production Request planning once each; reject and underfunded approval create no Authorization；
- runtime-checkable `ArtifactRepository` contract shared by the existing in-memory boundary and the SQLite Adapter；
- durable exact Artifact Versions, immutable history and logical replay/conflict through standard-library SQLite；
- typed deterministic JSON for the complete accepted frozen value domain without pickle, integer coercion or mutable decode shapes；
- `BEGIN IMMEDIATE` atomic commit/revision behavior, close/reopen recovery, two-instance visibility and safe schema/storage failure normalization。

Verification on 2026-08-12:

```text
uv run python -m unittest discover -s tests -v
Ran 131 tests — OK

uv run python -m unittest tests.artifacts.test_repository_contract -v
Ran 6 tests — OK

uv run python -m unittest tests.integration.test_sqlite_artifact_repository -v
Ran 6 tests — OK

uv run python -m unittest tests.agents.test_production_agent -v
Ran 4 tests — OK

uv run python -m unittest tests.integration.test_character_planning -v
Ran 3 tests — OK

uv run python -m unittest tests.agents.test_storyboard_planning -v
Ran 5 tests — OK

uv run python -m unittest tests.integration.test_storyboard_planning -v
Ran 3 tests — OK

uv run python -m unittest tests.artifacts.test_storyboard_decision -v
Ran 7 tests — OK

uv run python -m unittest tests.integration.test_storyboard_decision -v
Ran 1 test — OK

uv run python -m unittest tests.agents.test_timeline_planning -v
Ran 5 tests — OK

uv run python -m unittest tests.integration.test_timeline_planning -v
Ran 4 tests — OK

uv run python -m unittest tests.agents.test_production_request_planning -v
Ran 4 tests — OK

uv run python -m unittest tests.integration.test_production_request_planning -v
Ran 2 tests — OK

uv run python -m unittest tests.production.test_budget -v
Ran 5 tests — OK

uv run python -m unittest tests.integration.test_budget_authorization -v
Ran 8 tests — OK

uv run python -m unittest tests.integration.test_authorized_production_request -v
Ran 2 tests — OK

uv run python -m compileall -q src tests
OK

git diff --check
OK
```

This proves the current offline and no-Provider planning/Budget slices plus durable Artifact commit/get/restart behavior. Creator decisions, Budget Authorization and Workflow checkpoint remain in-memory. Budget pricing is a deterministic local Fixture. It does not prove live pricing, production-side authorization enforcement, paid Provider, media or deployment behavior.

## 3. Not Implemented

- persistent Decision/Budget Authorization/Provider-attempt and Workflow-checkpoint storage；
- task-level application and local Web Workspace；
- production-side authorization enforcement；
- Production Orchestrator or Provider adapters；
- Visual/TTS/media generation；
- Final Video Review、stale/impact、scene retry；
- publish package/export；
- product Model Runtime and real media Provider evidence。

## 4. GitHub State

- Issue #23 is closed as completed; its sole M1-001 Task Contract was delivered by merged PR #24.
- `main@cd1a936` contains the approved M0 baseline and independently approved Character planning implementation.
- GitHub reported no status checks for PR #24; its merge evidence is the recorded local test/build run and main-controller independent Review, not remote CI.
- Issue #25 is closed as completed; its sole M1-002 Task Contract was delivered by merged PR #26.
- `main@c26e808` contains reviewed Storyboard implementation commit `bb8e497`.
- GitHub reported no status checks for PR #26; its merge evidence is the recorded local test/build run and main-controller independent Review, not remote CI.
- Issue #28 is closed as completed; its sole M1-003 Storyboard Decision Task Contract was delivered by merged PR #29.
- `main@a331c47` contains reviewed Storyboard decision implementation commit `047ce29`.
- GitHub reported no status checks for PR #29; its merge evidence is the recorded local test/build run and main-controller independent Review, not remote CI.
- Issue #31 is closed as completed; its sole M1-004 Timeline Planning Task Contract was delivered by merged PR #32.
- `main@4241554` contains reviewed Timeline implementation commit `77a360d`.
- GitHub reported no status checks for PR #32; its merge evidence is the recorded local test/build run and main-controller independent Review, not remote CI.
- Issue #34 is closed as completed; its sole M1-005 Production Request Planning Task Contract was delivered by merged PR #35.
- `main@1c01a34` contains reviewed Production Request implementation commit `1838819`.
- GitHub reported no status checks for PR #35; its merge evidence is the recorded local test/build run and main-controller independent Review, not remote CI.
- Issue #37 is closed as completed; its sole M1-006 Production Budget and Creator Authorization Task Contract was delivered by merged PR #38.
- `main@2379650` contains reviewed Budget/Authorization implementation commit `7ee3677`.
- GitHub reported no status checks for PR #38; its merge evidence is the recorded local test/build run, mutation audit and main-controller independent Review, not remote CI.
- Issue #40 is closed as completed; its sole M1-007 offline cross-slice integration Task Contract was delivered by merged PR #41.
- `main@13ccba4` contains reviewed single-file integration commit `6ccb197`.
- GitHub reported no status checks for PR #41; its merge evidence is the focused/full local runs, three killed lineage/authorization mutations and main-controller independent Review, not remote CI.
- Issue #43 is closed as completed; its sole M2-001 Artifact repository/SQLite Task Contract was delivered by merged PR #44.
- `main@922d6c1` contains reviewed SQLite repository commit `ce2db9a`.
- GitHub reported no status checks for PR #44; its merge evidence is the 131-test local run, six killed contract mutations, a 20-run two-instance concurrency audit and main-controller independent Review, not remote CI.

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
| Luna current discoverability | Visible in current collaboration tool | exact `luna-worker` dispatched for Issue #43 |
| Actual subagent runtime model | RUNTIME_VERIFIED | Luna task `019ff3c2-c80c-7323-b5d1-1b1afef95e67` `turn_context`: `gpt-5.6-luna / max` |
| Terra migration | Not applicable | No active/done Terra task found in this current run |

Official Codex configuration supports trusted project-scoped `.codex/config.toml` overrides. The current task is a fresh task in this trusted project, and its host-written `turn_context` independently exposes the effective `gpt-5.6-sol / xhigh` runtime values.

The runtime evidence above verifies Agent routing only; it does not prove product Model Runtime or Provider capability.

## 7. M0/M1 Baseline and M2 Changes

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

Issue #25 implementation is isolated in merged commit `bb8e497` and changes only:

- `src/ai_course_factory/agents/production_agent.py`；
- `src/ai_course_factory/agents/runtime.py`；
- `src/ai_course_factory/agents/__init__.py`；
- `tests/agents/test_storyboard_planning.py`；
- `tests/integration/test_storyboard_planning.py`。

The exact Luna implementation preserved the existing Character result contract, added an independent Storyboard result envelope, derived Storyboard scene order from the exact Script, and left Commit ownership at the Artifact Store. The main orchestrator independently reviewed the actual diff, reran all gates, and returned `APPROVED`.

Issue #28 implementation is isolated in merged commit `047ce29` and changes only:

- `src/ai_course_factory/artifacts/storyboard_decision.py`；
- `src/ai_course_factory/artifacts/__init__.py`；
- `tests/artifacts/test_storyboard_decision.py`；
- `tests/integration/test_storyboard_decision.py`。

The exact Luna followed the confirmed public TDD seams: the first focused test was red because the boundary did not exist, then the public unit and committed-Storyboard integration slices turned green. The main orchestrator independently reviewed mode/action exclusivity, exact lineage, atomic failures, replay/conflict and safe exception behavior and returned `APPROVED`.

Issue #31 implementation is isolated in merged commit `77a360d` and changes only:

- `src/ai_course_factory/agents/production_agent.py`；
- `src/ai_course_factory/agents/runtime.py`；
- `src/ai_course_factory/agents/__init__.py`；
- `tests/agents/test_timeline_planning.py`；
- `tests/integration/test_timeline_planning.py`。

The exact Luna first observed a public import failure before implementing the Timeline seam. The main orchestrator requested one test-evidence correction for an actual upstream Storyboard scene-order mutation and a genuinely raised runtime exception. The same Luna corrected only the tests; the orchestrator reread the actual Diff, reran all gates, verified gate/timing mutations are caught, and returned `APPROVED`.

Issue #34 implementation is isolated in merged commit `1838819` and changes only:

- `src/ai_course_factory/agents/production_agent.py`；
- `src/ai_course_factory/agents/runtime.py`；
- `src/ai_course_factory/agents/__init__.py`；
- `tests/agents/test_production_request_planning.py`；
- `tests/integration/test_production_request_planning.py`。

The exact Luna first observed a public import failure before implementing the Production Request seam. The main orchestrator stopped an initial oversized implementation, required reuse of existing validators, and reduced the source addition to 291 lines. Independent Review then requested one test-only correction for upstream malformed narration and exact-shape runtime narration drift. The same Luna added those cases; the orchestrator reread the Diff, reran all gates, killed Timeline/result-validator bypass mutations, and returned `APPROVED`.

Issue #43 implementation is isolated in merged commit `ce2db9a` and changes only:

- `src/ai_course_factory/artifacts/commit.py`；
- `src/ai_course_factory/artifacts/sqlite.py`；
- `src/ai_course_factory/artifacts/__init__.py`；
- `tests/artifacts/test_repository_contract.py`；
- `tests/integration/test_sqlite_artifact_repository.py`。

The exact Luna recorded the required missing-interface RED, then implemented the shared repository contract and SQLite Adapter. Independent Review found one persisted logical-index integrity defect, returned `CHANGES_REQUESTED`, and the same Luna bound replay to the canonical persisted Version. The orchestrator reran all gates, killed replay/revision/type/restart mutations, exercised concurrent two-instance revisions and returned `APPROVED`.

## 8. Open Decisions and Blockers

### M1 milestone review

- M0 activation is complete；
- M1 result 1 of 7 is independently approved and merged by PR #24；
- M1 result 2 of 7 is independently approved and merged by PR #26 at `main@c26e808`；
- M1 result 3 of 7 is independently approved and merged by PR #29 at `main@a331c47`；
- M1 result 4 of 7 is independently approved and merged by PR #32 at `main@4241554`；
- M1 result 5 of 7 is independently approved and merged by PR #35 at `main@1c01a34`；
- M1 result 6 of 7 is independently approved and merged by PR #38 at `main@2379650`；
- M1 result 7 of 7 is independently approved and merged by PR #41 at `main@13ccba4`；
- M1 exit is `PASSED`: exact planning lineage, mandatory Budget Review and separate Authorization compose offline；
- M1 evidence remains deterministic/local/in-memory and does not establish persistence, live pricing, Provider execution, cost, media or deployment。

### M2 milestone review

- M2 result 1 is independently approved and merged by PR #44 at `main@922d6c1`；
- exact Artifact Versions and logical Commit replay now survive SQLite close/reopen；
- Decision, Budget Authorization, Workflow checkpoint, task aggregate and filesystem workspace persistence remain open；
- M2 exit is not yet passed。

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

1. Establish a separate bounded M2-002 Task Contract for the next persistent control-record seam; do not bundle the remaining M2 results.
2. Keep all real Provider, cost and deployment gates closed.
