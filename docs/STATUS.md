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
| Reviewed M2-002 Commit | `ca55c6347fdfed7d8e676f4ccf1131b5fd896003` |
| Reviewed M2-003 Commit | `2fb235e1e7e588a9dcad7aae1263b93fa27c391f` |
| Reviewed M2-004 Commit | `e18977d6783080d42db349f2ee33849aa08370f2` |
| Reviewed M2-005 Commit | `31df853567adbe65033ccb4cde463b05ccb8209c` |
| Reviewed M2-006 Commit | `71ca0dafab7615861c98d53bba6f7d6008f3530a` |
| Reviewed M2-007 Commit | `91dbdc38bae9a82c74960ac89779f7fc017c1d2e` |
| Reviewed M2-008 Commit | `0c63f3e0cc5f20cbc9cec0d8b76ecfeacdc6f45a` |
| Latest Feature Baseline | M2-008 merged at `main@437d8ca91b6ae990e5e7ae4f0d315b9979ec00aa` |
| Planning Baseline | `4c00eb2139006b250574377a337c60a4a7758af3` |
| Remote Canonical | `origin/main`; live HEAD is authoritative for transient docs-only merges |
| Worktrees | One main worktree |
| Current Task Contract | None; #67 is closed after M2-008 completion |
| Open PR | None |
| Current Code Gate | 230 tests passed on merged `main@437d8ca` |
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
- mandatory Creator Budget Review approve/reject decision and independent Authorization after valid approval；
- Authorization bound to exact Request/Budget References, canonical snapshot, approved amount/attempt caps, Creator/time/decision identity；
- Budget Commit replay/conflict, underfunded/stale/mutated Budget rejection and new-Request-Version isolation evidence；
- offline cross-slice exact approved Script -> Character -> Storyboard decision -> Timeline -> Production Request -> Production Budget -> independent Authorization integration evidence；
- the integrated deterministic runtime invokes only Character/Storyboard/Timeline/Production Request planning once each; reject and underfunded approval create no Authorization；
- runtime-checkable `ArtifactRepository` contract shared by the existing in-memory boundary and the SQLite Adapter；
- durable exact Artifact Versions, immutable history and logical replay/conflict through standard-library SQLite；
- typed deterministic JSON for the complete accepted frozen value domain without pickle, integer coercion or mutable decode shapes；
- `BEGIN IMMEDIATE` atomic commit/revision behavior, close/reopen recovery, two-instance visibility and safe schema/storage failure normalization；
- runtime-checkable `ScriptDecisionRepository` with the existing default in-memory behavior preserved；
- durable SQLite Script Creator decisions with exact lineage fields, immutable replay/conflict and close/reopen recovery；
- Script Review Application evidence that decision persistence succeeds before Workflow resume and storage failure leaves the gate pending；
- runtime-checkable `StoryboardDecisionRepository` with existing enabled-review/disabled-skip semantics preserved；
- durable SQLite Storyboard decisions with exact Script/Character lineage, mode/action and immutable replay/conflict；
- restored satisfying Storyboard decision reaches existing Timeline planning, while failed/corrupt storage produces no Timeline invocation。
- runtime-checkable `BudgetAuthorizationRepository` with the existing default in-memory behavior preserved；
- durable SQLite Budget decisions and independent Authorizations with exact Request/Budget/snapshot/Creator/time/cap binding；
- approve Decision+Authorization `BEGIN IMMEDIATE` atomicity, reject decision-only persistence, close/reopen replay, two-instance conflict and safe cross-table corruption normalization；
- runtime-checkable `CheckpointAdapter` with the existing in-memory default preserved；
- official synchronous LangGraph `SqliteSaver` behind a bounded `SQLiteCheckpointAdapter` with explicit lifecycle and safe storage errors；
- exact pending and terminal Script Review checkpoint recovery, command replay/conflict, two-instance visibility and control-only state after close/reopen；
- decision-before-resume recovery evidence: a durable Script decision survives a failed checkpoint write while the last valid checkpoint remains pending, then the same identity completes after reopen；
- malformed/cross-thread restored control projections and unsafe task/thread/command identities fail before state advance without raw storage detail；
- runtime-checkable `TaskRepository` with a fresh in-memory default and explicit `SQLiteTaskRepository` injection；
- durable Task revisions containing canonical exact Artifact selections, `current|stale` facts, caller command identity and derived lifecycle projection；
- dependency-edge direct/transitive impact preview, atomic upstream replacement, stale propagation and stale-slot regeneration with exact current dependencies；
- immutable current/history lookup and original command replay/impact after later revisions, with global command conflicts and revision/command-link integrity checks；
- SQLite Artifact + Task close/reopen composition, real two-instance competing-write serialization, atomic trigger rollback and safe open/closed/corrupt/future-schema failures。
- runtime-checkable `WorkspaceAdapter` with frozen task/file records and fixed `media|provider-records|exports` areas；
- task-scoped `FilesystemWorkspace` with safe bounded identities, adapter-derived paths and opaque exact bytes only；
- descriptor-relative `O_NOFOLLOW` traversal and canonical directory-chain revalidation prevent root/tasks/task/area and final-file symlink escape, including directory-swap mutations；
- temp-file write + file `fsync` + same-filesystem no-replace hardlink promotion provide immutable replay/conflict behavior and failure cleanup；
- workspace bytes survive adapter reconstruction, compose with a restarted SQLite Task projection, and serialize equal/different two-adapter races without orphan temporary files。
- runtime-checkable `ProviderAttemptRepository` and `ProviderAttemptLedger` load one exact durable Budget Authorization before repository mutation；
- each provider-neutral Scene/operation reservation derives exact Request/Budget/currency/amount/caps from the canonical Authorization snapshot and persists `started` before any future side effect；
- aggregate reserved micros, per-Scope attempt numbering, one unknown/nonterminal attempt, idempotency, exact replay/conflict and failed-attempt retry caps are enforced atomically in memory and SQLite；
- terminal success/failure outcomes retain safe charge/result and exact Workspace references; valid terminal replay succeeds while changed outcomes or static lineage fail closed；
- SQLite close/reopen, two-instance serialization, trigger rollback, full Authorization binding, impossible group/corrupt/future/open/closed state and JSON bounds have mutation-sensitive recovery evidence。

Verification on 2026-08-12:

```text
uv run python -m unittest discover -s tests -v
Ran 230 tests — OK

uv run python -m unittest tests.production.test_provider_attempt_repository_contract -v
Ran 10 tests — OK

uv run python -m unittest tests.integration.test_sqlite_provider_attempt_ledger -v
Ran 6 tests — OK

uv run python -m unittest tests.persistence.test_workspace -v
Ran 13 tests — OK

uv run python -m unittest tests.integration.test_task_workspace -v
Ran 3 tests — OK

uv run python -m unittest tests.application.test_task_projection -v
Ran 10 tests — OK

uv run python -m unittest tests.integration.test_sqlite_task_projection -v
Ran 8 tests — OK

uv run python -m unittest tests.artifacts.test_repository_contract -v
Ran 6 tests — OK

uv run python -m unittest tests.integration.test_sqlite_artifact_repository -v
Ran 6 tests — OK

uv run python -m unittest tests.artifacts.test_script_decision_repository_contract -v
Ran 4 tests — OK

uv run python -m unittest tests.integration.test_sqlite_script_decision_repository -v
Ran 7 tests — OK

uv run python -m unittest tests.artifacts.test_storyboard_decision_repository_contract -v
Ran 4 tests — OK

uv run python -m unittest tests.integration.test_sqlite_storyboard_decision_repository -v
Ran 6 tests — OK

uv run python -m unittest tests.production.test_budget_repository_contract -v
Ran 6 tests — OK

uv run python -m unittest tests.integration.test_sqlite_budget_authorization -v
Ran 8 tests — OK

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

uv run python -m unittest tests.workflow.test_checkpoint_adapter_contract -v
Ran 4 tests — OK

uv run python -m unittest tests.integration.test_sqlite_script_review_checkpoint -v
Ran 10 tests — OK

uv run python -m compileall -q src tests
OK

git diff --check
OK
```

This proves the current offline and no-Provider planning/Budget slices plus durable Artifact, Script/Storyboard decision, Budget Authorization, existing Script Review Workflow-checkpoint, exact Task-projection restart behavior, task-scoped filesystem persistence and pre-call Provider-attempt reservation/outcome recovery. Budget pricing is a deterministic local Fixture. It does not prove broader Workflow gates, a Production Orchestrator, any Provider invocation, live pricing, paid media, UI or deployment behavior.

## 3. Not Implemented

- Production Orchestrator, broader Workflow gates and production-side authorization enforcement；
- task-level production application use cases and local Web Workspace；
- Visual/TTS/Composer adapters and media generation；
- Final Video Review and scene retry/replace；
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
- Issue #46 is closed as completed; its sole M2-002 persistent Script decision Task Contract was delivered by merged PR #47.
- `main@6593ed1` contains reviewed Script decision persistence commit `ca55c63`.
- GitHub reported no status checks for PR #47; its merge evidence is the 142-test local run, conflict/reference/restart and mismatched-success mutation checks, a 20-run two-instance conflict audit and main-controller independent Review, not remote CI.
- Issue #49 is closed as completed; its sole M2-003 persistent Storyboard decision Task Contract was delivered by merged PR #50.
- `main@5ec30a0` contains reviewed Storyboard decision persistence commit `2fb235e` and the bounded test hardening from PR #52.
- GitHub reported no status checks for PR #50; its merge evidence is the 152-test local run, conflict/reference/mode/restart mutations, downstream Timeline failure checks, a 20-run two-instance conflict audit and main-controller independent Review, not remote CI.
- Issue #53 is closed as completed; its sole M2-004 persistent Budget decision/Authorization Task Contract was delivered by merged PR #54.
- `main@fdd755c` contains reviewed Budget persistence commit `e18977d`.
- GitHub reported no status checks for PR #54; its merge evidence is the 166-test local run, atomic second-insert rollback, exact direct-save mutations, cross-table corruption checks, a 10-run two-instance conflict audit and main-controller independent Review, not remote CI.
- Issue #56 is closed as completed; its sole M2-005 persistent Script Review checkpoint Task Contract was delivered by merged PR #57.
- `main@6a7217e` contains reviewed checkpoint persistence commit `31df853`.
- GitHub reported no status checks for PR #57; its merge evidence is the 180-test local run, pending/terminal close-reopen proof, decision-before-resume recovery, raw-error suppression, malformed restored-state mutations and main-controller independent Review, not remote CI.
- Issue #59 is closed as completed; its sole M2-006 persistent Task projection Task Contract was delivered by merged PR #60.
- `main@eca9fb5` contains reviewed Task projection commit `71ca0da`.
- GitHub reported no status checks for PR #60; its merge evidence is the 198-test local run, exact selection/impact/lifecycle mutations, revision/command corruption checks, atomic write rollback, real two-instance race and main-controller independent Review, not remote CI.
- Issue #63 is closed as completed; its sole M2-007 task-scoped filesystem workspace Task Contract was delivered by merged PR #64.
- `main@1ae961b` contains reviewed workspace commit `91dbdc3`.
- GitHub reported no status checks for PR #64; its merge evidence is the 214-test local run, descriptor-chain and directory-swap mutations, atomic write/link cleanup, exact restart/race behavior and main-controller independent Review, not remote CI.
- Issue #67 is closed as completed; its sole M2-008 persistent Provider-attempt ledger Task Contract was delivered by merged PR #68.
- `main@437d8ca` contains reviewed Provider-attempt commit `0c63f3e`.
- GitHub reported no status checks for PR #68; its merge evidence is the 230-test local run, exact Authorization/pre-call reservation, restart/retry/terminal replay, atomic race/rollback, record-fingerprint/group corruption mutations and main-controller independent Review, not remote CI.

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
| Luna current discoverability | Completed and closed after handoff | exact `luna-worker` for Issue #67 was interrupted immediately after each completed handoff to release the execution slot |
| Actual subagent runtime model | RUNTIME_VERIFIED | Luna task `019ff47e-6876-7ee3-926c-bae3d89a64b8` `turn_context`: `gpt-5.6-luna / max` |
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

Issue #46 implementation is isolated in merged commit `ca55c63` and changes only:

- `src/ai_course_factory/artifacts/script_decision.py`；
- `src/ai_course_factory/artifacts/sqlite_script_decision.py`；
- `src/ai_course_factory/artifacts/__init__.py`；
- `tests/artifacts/test_script_decision_repository_contract.py`；
- `tests/integration/test_sqlite_script_decision_repository.py`。

The exact Luna recorded the required missing-interface RED and preserved the existing Script assessment and Application APIs behind an injected repository seam. Independent Review found that a mismatched successful repository result could resume Workflow, returned `CHANGES_REQUESTED`, and the same Luna required equality with the requested immutable record. The orchestrator reran all gates, killed conflict/reference/restart mutations, exercised concurrent decision identities and returned `APPROVED`.

Issue #49 implementation is isolated in merged commit `2fb235e` and changes only:

- `src/ai_course_factory/artifacts/storyboard_decision.py`；
- `src/ai_course_factory/artifacts/sqlite_storyboard_decision.py`；
- `src/ai_course_factory/artifacts/__init__.py`；
- `tests/artifacts/test_storyboard_decision_repository_contract.py`；
- `tests/integration/test_sqlite_storyboard_decision_repository.py`。

The exact Luna recorded the required missing-interface RED, added the standalone repository seam and proved restored decisions at the existing Timeline consumer. The orchestrator independently reviewed the real Diff, killed conflict/reference/mode/restart mutations, exercised simultaneous conflicting identities and returned `APPROVED` without a correction round.

Issue #53 implementation is isolated in merged commit `e18977d` and changes only:

- `src/ai_course_factory/production/budget.py`；
- `src/ai_course_factory/production/sqlite_budget.py`；
- `src/ai_course_factory/production/__init__.py`；
- `tests/production/test_budget_repository_contract.py`；
- `tests/integration/test_sqlite_budget_authorization.py`。

The exact Luna recorded the missing repository-interface RED and preserved the existing Budget public records and in-memory behavior behind an injected repository seam. Independent Review returned `CHANGES_REQUESTED` for direct-save bounds/canonicality and cross-table integrity, then corrected request-order semantics, encoded JSON bounds, replay-before-conflict corruption handling and mutation-test construction. The orchestrator reran all gates and returned `APPROVED`.

Issue #56 implementation is isolated in merged commit `31df853` and changes only:

- `pyproject.toml`；
- `uv.lock`；
- `src/ai_course_factory/workflow/checkpoint.py`；
- `src/ai_course_factory/workflow/script_review.py`；
- `src/ai_course_factory/workflow/__init__.py`；
- `tests/workflow/test_checkpoint_adapter_contract.py`；
- `tests/integration/test_sqlite_script_review_checkpoint.py`。

The exact Luna recorded the missing public checkpoint-interface RED and used the official `langgraph-checkpoint-sqlite==3.1.1` synchronous saver without recreating its schema. Independent Review first suppressed raw storage causes and required a full decision/checkpoint close-reopen recovery, then rejected malformed or cross-thread restored projections and unsafe identities before state advance. The orchestrator reran all gates, killed command/no-advance and forged-state mutations and returned `APPROVED`.

Issue #59 implementation is isolated in merged commit `71ca0da` and changes only:

- `src/ai_course_factory/application/task.py`；
- `src/ai_course_factory/application/sqlite_task.py`；
- `src/ai_course_factory/application/__init__.py`；
- `tests/application/test_task_projection.py`；
- `tests/integration/test_sqlite_task_projection.py`。

The exact Luna recorded the missing public Task-projection RED and kept the SQLite adapter behind explicit injection. Independent Review rejected valid-shape revision/command corruption, incorrect lifecycle regression with unrelated current branches, forged direct repository transitions and stale-impact misreporting. The same Luna corrected each bounded defect, the orchestrator independently reran focused and full gates, and the final verdict was `APPROVED`.

Issue #63 implementation is isolated in reviewed commit `91dbdc3` and changes only:

- `.gitignore`；
- `src/ai_course_factory/persistence/__init__.py`；
- `src/ai_course_factory/persistence/workspace.py`；
- `tests/persistence/__init__.py`；
- `tests/persistence/test_workspace.py`；
- `tests/integration/test_task_workspace.py`。

The exact Luna recorded the missing public persistence module RED and implemented only the task-scoped filesystem seam. Independent Review reproduced a real directory-swap/symlink escape between validation and commit, returned `CHANGES_REQUESTED`, and required descriptor-relative no-follow operations plus identity revalidation. The same Luna corrected the bounded defect, added mutation-sensitive cleanup and partial-write evidence, and was closed immediately after handoff. The orchestrator independently killed the original escape mutation, reran focused/full gates and returned `APPROVED`.

Issue #67 implementation is isolated in reviewed commit `0c63f3e` and changes only:

- `src/ai_course_factory/production/attempt.py`；
- `src/ai_course_factory/production/sqlite_attempt.py`；
- `src/ai_course_factory/production/__init__.py`；
- `tests/production/test_provider_attempt_repository_contract.py`；
- `tests/integration/test_sqlite_provider_attempt_ledger.py`。

The exact Luna recorded the missing repository-interface RED and stopped at the no-Provider pre-call/outcome persistence seam. Independent Review rejected an over-cap first draft, then reproduced Authorization-return, row/fingerprint binding, terminal-lineage, changed-Authorization retry and attempt-sequence corruption defects. The same Luna corrected each bounded issue, the orchestrator independently reran all focused/full gates and the original mutations, returned `APPROVED`, and closed the worker immediately after each completed handoff.

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
- M2 result 2 is independently approved and merged by PR #47 at `main@6593ed1`；
- M2 result 3 is independently approved and merged by PR #50, with test hardening in PR #52, at `main@5ec30a0`；
- M2 result 4 is independently approved and merged by PR #54 at `main@fdd755c`；
- M2 result 5 is independently approved and merged by PR #57 at `main@6a7217e`；
- M2 result 6 is independently approved and merged by PR #60 at `main@eca9fb5`；
- M2 result 7 is independently approved and merged by PR #64 at `main@1ae961b`；
- M2 result 8 is independently approved and merged by PR #68 at `main@437d8ca`；
- exact Artifact Versions and logical Commit replay now survive SQLite close/reopen；
- exact Script Creator decisions now survive SQLite close/reopen and are persisted before Workflow resume；
- exact Storyboard decisions now survive SQLite close/reopen and reach Timeline by exact record；
- exact Budget decisions and Authorizations now survive SQLite close/reopen with atomic approval persistence；
- the existing Script Review Workflow checkpoint now survives SQLite close/reopen with exact pending/terminal replay and safe corruption handling；
- the Task projection now survives SQLite close/reopen with exact selected References, immutable history, command replay, dependency-edge stale impact and safe two-instance writes；
- the task-scoped filesystem workspace now survives adapter reconstruction with exact immutable bytes, fixed areas, safe no-follow traversal and two-adapter race behavior；
- Provider-attempt reservations and terminal outcomes now survive SQLite close/reopen with exact Authorization binding, aggregate budget/attempt caps, unknown-started recovery and safe corruption handling；
- M2 exit is `PASSED`: all approved durable-runtime results have independent Review and restart/replay evidence while all external Provider and cost gates remain closed。

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

1. Establish a separate bounded M3-001 Task Contract for the provider-neutral production orchestration interface and deterministic Fake boundary; do not select or call a real Provider, incur fees or bundle media composition beyond the approved contract.
2. Keep all real Provider, cost and deployment gates closed.
