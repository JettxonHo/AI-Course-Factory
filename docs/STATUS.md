# AI Course Factory Current Status

## 1. Snapshot

| Field | Current Fact |
| --- | --- |
| Date | 2026-08-13 |
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
| Reviewed M3-001 Commit | `6d14524c2f6852d86a0721e6c7930b70ef81bbcd` |
| Reviewed M3-002 Commit | `c48177a7ba2ff2e0f92381fa35ab6c08cdbe52b4` |
| Reviewed M3-003 Commit | `367047ab5a1e0d745f5862159acc4cb11476d107` |
| Reviewed M3-004 Commit | `b8e2d706edeec210532d724cfc21360253965058` |
| Reviewed M3-005 Commit | `fb9ef21d2264ac6773f2ff3c589684c8003146b8` |
| Reviewed M3-006 Commit | `26bffd61b4f5f04039c2d33c1e881ac99e007f8d` |
| Reviewed M3-007 Commit | `6fc259eb2f9836f517785dbc41b2206e82ca2a7e` |
| Reviewed M3-008 Commit | `e99e75c76e0852343ac4495b4e900bb17a19e734` |
| Reviewed M3-009 Commit | `5b8d9f7ea3624a7ac88389f76898eeec3b7f732f` |
| Latest Feature Baseline | M3-009 merged by PR #104 at `main@682ecbd1633ff22f181cb5d5161bea6b0a05433e` |
| Planning Baseline | `4c00eb2139006b250574377a337c60a4a7758af3` |
| Remote Canonical | `origin/main`; live HEAD is authoritative for transient docs-only merges |
| Worktrees | One main worktree |
| Current Task Contract | None; M3-009/Issue #103 is closed through PR #104; Issue #105 is docs-only and authorizes no next implementation; any follow-up requires a separate Task Contract for Task projection media lifecycle integration or scene retry/replace |
| Open PR | None |
| Current Code Gate | 340 full local tests passed and compileall passed on merged `main@682ecbd1633ff22f181cb5d5161bea6b0a05433e`; GitHub reported no hosted checks |
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
- frozen, slotted provider-neutral visual/voice generation tasks, normalized media results/failures and runtime-checkable interfaces；
- explicit-injection deterministic Fake visual/voice adapters that validate exact Production Request and task-scoped Workspace references before writing；
- canonical bounded UTF-8 Fixture envelopes with explicit Fake provider identity and non-playable media types, written only through `WorkspaceAdapter.commit`；
- visual and voice close/reopen replay, changed-content conflict/no-overwrite, malformed Workspace-success, huge-duration and exact-type mutation evidence without Provider, SDK, subprocess or fees。
- separate exported `FFmpegFixtureVisualGenerator` and `FFmpegFixtureVoiceGenerator` behind the existing `VisualGenerator` / `VoiceGenerator` protocols；
- playable synthetic local FFmpeg Fixture media with exact profiles: visual H.264 `540x960`, `24 fps`, `yuv420p`, no audio; voice AAC `48 kHz`, mono, no video; both use MP4-family containers；
- exact normalized task-binding metadata, real bounded ffprobe JSON validation before commit, Workspace-only immutable byte commit, byte-exact equivalent replay/conflict behavior and zero-charge terminal Orchestrator restart replay；
- frozen exact `ProviderAttemptClaim(record, created)` and runtime Repository/Ledger claim methods preserve existing reserve behavior while exposing atomic execution ownership；
- in-memory locking and SQLite `BEGIN IMMEDIATE` distinguish first reservation (`created=True`) from started/terminal replay (`created=False`) without get-then-reserve inference；
- close/reopen and real two-instance exact-race evidence yields one execution owner and one replay observer, while cross-Authorization idempotency conflict and corrupted claim results fail safely。
- frozen `ProductionExecutionResult` and explicit-injection `ProductionOrchestrator` validate one exact Production Request/media task before one atomic claim；
- only a newly created claim invokes the matching deterministic Fake visual/voice adapter once, then persists a zero-charge terminal outcome；started/failed/succeeded claims return safe status or terminal replay without Adapter invocation；
- terminal replay reconstructs the exact result without duplicate Adapter calls, while forged task/claim/result/complete records, noncanonical references and nonzero terminal charges fail closed in the independent mutation audit。
- frozen, slotted `MediaCompositionScene`, `MediaCompositionTask` and `MediaCompositionResult` records plus runtime-checkable `MediaComposer` interface；
- explicit-injection `FFmpegMediaComposer` validates exact ordered composition tasks and bounded subtitle text/timing before Workspace reads or process execution；
- local composer re-probes every exact Workspace visual/voice input, generates canonical UTF-8 subtitle cues, concatenates at least two ordered Scene inputs, and emits MP4-family H.264 `540x960` `24 fps` `yuv420p` + AAC `48 kHz` mono + one attached `mov_text` subtitle stream；
- composed output carries deterministic task-binding metadata and is committed only through the task Workspace with exact replay, changed-input conflict/no-overwrite, malformed-output and safe failure evidence；
- frozen `ProductionCompositionResult` and the sole public `ProductionOrchestrator.compose` path validate one exact committed Production Request/Timeline plus terminal zero-charge Scene attempts before mutation；
- staged product-path commits create exact Scene Clip, Scene Audio, Subtitle, logical Master Audio and Video Artifact Versions with canonical lineage, provenance and dependencies；
- exact replay after durable-store/workspace reconstruction and staged Video-commit recovery preserve immutable upstream Artifacts and output bytes without duplicate generation；
- frozen/slotted Final Video assessment, finding, failure and decision records plus a runtime-checkable repository seam preserve the exact mandatory Final Video Review contract；
- the Final Video decision boundary structurally assesses one exact PR #92 Video Version, including canonical Scene Clip/Subtitle/Master Audio binding, deterministic hard blocks and mandatory `approve|reject|revise` actions；
- the in-memory default and SQLite v1 Final Video decision repositories preserve exact replay/conflict, close/reopen, two-instance visibility and safe corruption/storage failure behavior without storing media payloads or Workflow state；
- the durable namespaced Final Video Review Workflow + Application gate persists one exact Final Video decision before Workflow state advance, while the Script default checkpoint namespace and `final_video_review` coexist for the same public thread in one SQLite database；
- six read-only Workflow result projections are restored, and exact-type/AlwaysEqual Video plus decision-binding mutations fail closed in the independently reviewed gate；
- public `PackagingFailure`, `PublishPackageResult` and `PublishPackageBuilder` provide the deterministic Publish Package seam；
- exact approved Video + Subtitle + reachable Source Record produce one deterministic local ZIP in Workspace `exports`, then exact Artifact Manifest and Publish Package v1 facts；
- ZIP order is Video, canonical SRT, source attribution without source text, Artifact Manifest; deterministic metadata and byte/hash facts are verified；
- exact Final Video decision and lineage validation precede Workspace/Artifact side effects, and replay/conflict/no-v2 plus Manifest/Package staged recovery are verified；

Verification evidence through 2026-08-13:

M3-003 historical pre-PR #84 baseline: 264 full regression tests passed on `main@42cf6c2`; this historical count is retained only as M3-003 evidence.

M3-004 historical merge gates at `main@88309e0` (271 tests; retained as the prior feature evidence):

```text
uv run python -m unittest discover -s tests -v
Ran 271 tests — OK

uv run python -m unittest tests.production.test_ffmpeg_fixture_adapters -v
Ran 5 tests — OK

uv run python -m unittest tests.integration.test_ffmpeg_fixture_orchestrator -v
Ran 2 tests — OK

uv run python -m unittest tests.production.test_orchestrator -v
Ran 15 tests — OK

uv run python -m unittest tests.integration.test_offline_production_orchestrator -v
Ran 2 tests — OK

uv run python -m unittest tests.production.test_provider_attempt_repository_contract -v
Ran 14 tests — OK

uv run python -m unittest tests.integration.test_sqlite_provider_attempt_ledger -v
Ran 8 tests — OK

uv run python -m unittest tests.production.test_media_interfaces -v
Ran 4 tests — OK

uv run python -m unittest tests.integration.test_fake_media_adapters -v
Ran 7 tests — OK

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

M3-005 historical merge gates at `main@2741200` (PR #88 evidence):

```text
uv run python -m unittest tests.production.test_ffmpeg_composer -v
Ran 3 tests — OK

uv run python -m unittest tests.integration.test_ffmpeg_composer -v
Ran 6 tests — OK

uv run python -m unittest discover -s tests -v
Ran 280 tests — OK

uv run python -m compileall -q src tests
OK

real FFmpeg/ffprobe 9.0 capability: libx264, native AAC, mov_text, fps/tpad/apad/concat
independent output evidence: H.264 540x960 24 fps yuv420p + AAC 48 kHz mono + one mov_text stream; ordered SRT timing/text; MP4-family ftyp and deterministic binding metadata
git diff --check plus tracked/untracked diff checks
OK
```

M3-005 Review history: the main-controller first paused at the 580-line soft cap; semantic reuse reduced the composer implementation to 511 lines. Review returned `CHANGES_REQUESTED` for a fake timeout and insufficient exact/reorder/timing evidence; the same Luna corrected both. Main then independently reran the 3 focused unit tests, 6 integration tests and 280-test full regression, compileall, FFmpeg/ffprobe capability and output/subtitle probes, plus a forged 44.1 kHz final-audio mutation that failed generically before Workspace commit. GitHub has no hosted checks, so this is local evidence only.

M3-006 merge gates at `main@8f4868157b532af73f21c37743b7b6c67fa5b55e` (PR #92 evidence):

```text
focused composition unit: 12 passed
durable FFmpeg/SQLite integration: 1 passed
full regression: 293 passed
compileall: passed

real FFmpeg/ffprobe 9.0 capability: libx264, native AAC, mov_text; independent probes covered H.264 540x960 24 fps yuv420p, AAC 48 kHz mono and mov_text output
main-controller mutation audit: mutable repository snapshot and exact committed Request scalar-family mutation failed closed before Composer
GitHub reported no hosted checks
```

M3-006 Review history: the main-controller returned `CHANGES_REQUESTED` in two rounds for a mutable repository snapshot and the exact committed Request scalar family; the same Luna corrected both. Independent evidence covered exact Scene Clip/Scene Audio, Subtitle, logical Master Audio and Video Artifact lineage, replay and staged Video-commit recovery. The evidence boundary is local FFmpeg synthetic color/tone/subtitle Fixture output only; no remote checks were reported.

This proves the current offline planning/Budget/durable-runtime slices, provider-neutral visual/voice interfaces, deterministic non-playable Fake Fixture output, playable per-operation local FFmpeg Fixture media through the task Workspace, claim-gated offline Production Orchestrator behavior, local FFmpeg composition and the product-path media Artifact composition described above. Budget pricing, Fake media, FFmpeg media and the composed MP4 remain deterministic local Fixture evidence; Fake Fixture bytes are non-playable, while FFmpeg media and the composed MP4 are synthetic color/tone output with attached subtitles rather than prompt-faithful visual or spoken TTS. This M3-006 evidence does not prove the later Final Video decision seam, Task/gate integration, scene retry, export, any real Provider invocation, live pricing, fees, paid media, UI or deployment behavior.

M3-007 merge gates at `main@b3f2999e509a5467b590679177ec62f1c938ba41` (PR #96 evidence; implementation commit `6fc259eb2f9836f517785dbc41b2206e82ca2a7e`):

```text
focused Final Video decision contract: 6 passed
SQLite Final Video decision integration: 6 passed
full regression: 305 passed
compileall: passed
git diff --check, exact changed-file allowlist and protected-five audit: passed
GitHub reported no hosted checks
```

M3-007 Review history: the main-controller first returned `CHANGES_REQUESTED` for a concrete foreign Scene Clip canonical-binding defect and missing single-mutation evidence; the same Luna corrected both. The public surface was then narrowed by removing a private helper from the module `__all__`, and the final independent verdict was `APPROVED`. The merged seam contains frozen/slotted assessment, finding, failure and decision records, a runtime-checkable repository seam with in-memory default and SQLite v1 adapter, exact PR #92 Video structural assessment, canonical ordered Scene Clip/Subtitle/Master Audio binding, deterministic hard blocks, mandatory `approve|reject|revise` rules, exact replay/conflict, restart/two-instance and corruption evidence.

M3-007 evidence is decision/persistence only: no media probe, Workspace write, Provider call, fee, Task/Workflow advance, scene retry/replace, export, UI or deployment evidence was added. M3-008 now wires this exact decision through the namespaced Application/Workflow gate and persists it before state advance; Task projection media lifecycle, scene retry/replace, export, real Provider, cost and deployment gates remain closed.

M3-008 merge gates at `main@f3e536dce655d16d188b8924066c978254e83c6d` (PR #100 evidence; implementation commit `e99e75c76e0852343ac4495b4e900bb17a19e734`):

```text
workflow tests: 10 passed
application tests: 12 passed
durable integration tests: 2 passed
full local regression: 329 passed
compileall: passed
git diff --check: passed
GitHub reported no hosted checks
```

M3-008 Review history: independent Review corrected exact-type/AlwaysEqual Video and decision-binding defects and restored six read-only Workflow result projections; the final result was `APPROVED`. The durable gate uses the fixed `final_video_review` checkpoint namespace, persists the exact Final Video decision before Workflow state advance, and keeps the Script default namespace separately readable for the same public thread in one SQLite database.

M3-008 evidence is limited to the namespaced durable Final Video Review Workflow + Application gate. No hosted checks, real Provider, fees, deployment, Task projection media lifecycle, scene retry/replace or UI evidence exists; the next bounded Task Contract was not authorized by Issue #101.

M3-009 merge gates at `main@682ecbd1633ff22f181cb5d5161bea6b0a05433e` (Issue #103 / PR #104 evidence; reviewed implementation commit `5b8d9f7ea3624a7ac88389f76898eeec3b7f732f`):

```text
focused public contract: 10 passed
durable integration: 1 passed
full local regression: 340 passed
compileall: passed
git diff --check: passed
exact four-file allowlist and protected-five audit: passed
GitHub reported no hosted checks
```

M3-009 Review history: the initial `tests/packaging` namespace shadowed third-party `packaging.version` during full unittest discovery and was corrected to `tests/test_packaging_builder.py`. Main returned two bounded `CHANGES_REQUESTED` rounds for exact type/lineage/media/public evidence/private coupling; the same Luna corrected them, and `builder.py` is 647 lines below the 650 hard cap.

M3-009 evidence: public `PackagingFailure`, `PublishPackageResult` and `PublishPackageBuilder` consume exact approved Video, Subtitle and reachable Source Record facts, validate the exact Final Video approval and lineage before Workspace/Artifact side effects, write one deterministic ZIP to Workspace `exports`, then commit exact Artifact Manifest and Publish Package v1 facts. ZIP order is Video, canonical SRT, source attribution without source text, Artifact Manifest; deterministic metadata and byte/hash facts are verified. Replay/conflict/no-v2 and Manifest/Package staged recovery are verified. Durable evidence uses SQLite Artifact + Final Video decision repositories, FilesystemWorkspace restart, independent ZIP parse, byte-equal playable MP4 and optional ffprobe. No real Provider, network service, fees, deployment, external publication, Task media projection, scene retry or UI evidence exists; GitHub reported no hosted checks, evidence is local only, and Issue #105 is docs-only with no open implementation Task Contract authorized.

## 3. Not Implemented

Playable per-operation local FFmpeg Fixture media, local FFmpeg composition, bounded product-path media Artifact composition and deterministic local Publish Package/Artifact Manifest are implemented; the following remain not implemented:

- broader Task projection/media-lifecycle integration and production orchestration beyond the bounded composition and Final Video gate slices；
- task-level production application use cases and local Web Workspace；
- real Visual/TTS Provider adapters and non-Fixture product media generation beyond the local composer output；
- Task projection media lifecycle integration, scene retry/replace；
- product Model Runtime, UI and deployment evidence。

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
- Issue #71 is closed as completed; its sole M3-001 provider-neutral visual/voice interface and deterministic Fake Adapter Task Contract was delivered by merged PR #72.
- `main@60af4d2` contains reviewed Fake media interface commit `6d14524`.
- GitHub reported no status checks for PR #72; its merge evidence is the 241-test local run, exact-result/canonical-envelope/replay/conflict/type-mutation checks and main-controller independent Review, not remote CI or real Provider/playable-media evidence.
- Issue #75 is closed as completed; its sole M3-002 atomic Provider-attempt execution-claim Task Contract was delivered by merged PR #76.
- `main@39efaa4` contains reviewed execution-claim commit `c48177a`.
- GitHub reported no status checks for PR #76; its historical M3-002 merge evidence is the 247-test local run, close/reopen claim replay, repeated two-instance one-owner races, forged-claim and cross-Authorization idempotency mutations and main-controller independent Review, not remote CI or Provider execution evidence. The historical M3-003 pre-PR #84 baseline was 264 tests at `main@42cf6c2`.
- Issue #79 is closed as completed; its sole M3-003 claim-gated offline Production Orchestrator Task Contract was independently approved and delivered by merged PR #80.
- PR #80 implementation commit is `367047a`; merge commit is `42cf6c2` (`main@42cf6c2`).
- Its evidence is 15 focused unit tests, 2 focused integration tests, 264 full regression tests (the M3-003 pre-PR #84 historical count), compile/diff checks, and an independent mutation audit. The audit covered forged task/claim/result/complete records, noncanonical references and nonzero terminal charges; each failed closed. GitHub reported no status checks for PR #80, so this is local review evidence, not remote CI, Provider, playable-media or product-runtime evidence.
- Issue #83 is closed as completed; its sole M3-004 playable local FFmpeg Fixture media Task Contract was independently approved and delivered by merged PR #84.
- PR #84 implementation commit is `b8e2d706edeec210532d724cfc21360253965058`; merge commit is `88309e0b79722243ac264d29be36ceb7e1e1dda4` (`main@88309e0`).
- PR #84 exports separate `FFmpegFixtureVisualGenerator` and `FFmpegFixtureVoiceGenerator` behind the existing media protocols. Visual output is synthetic H.264 `540x960`, `24 fps`, `yuv420p`, no audio; voice output is synthetic AAC `48 kHz`, mono, no video; both are playable MP4-family Fixture bytes with exact task-binding metadata, real ffprobe validation before Workspace commit, immutable byte-exact replay/conflict and zero-charge terminal restart replay.
- Main-controller review first returned `CHANGES_REQUESTED` for missing frame-rate/container validators and missing failed-terminal replay evidence; the same Luna corrected both. Main then independently ran 5 focused adapter tests, 2 focused integration tests, 271 full regression tests, compileall, real FFmpeg/ffprobe capability and probe checks, and avg-frame-rate/voice-container mutation audits. GitHub reported no status checks for PR #84, so this is local review/runtime evidence, not remote CI, real Provider/TTS, prompt-faithful media or full product-runtime evidence.
- The verification host exposes FFmpeg/ffprobe 9.0; FFmpeg runs with `-nostdin`, while ffprobe 9.0 rejects that option and is run with stdin=`DEVNULL` as the bounded compatibility path.
- Issue #87 is closed as completed; its sole M3-005 local FFmpeg MediaComposer Task Contract was independently approved and delivered by merged PR #88.
- PR #88 implementation commit is `fb9ef21d2264ac6773f2ff3c589684c8003146b8`; merge commit is `27412008a6e14bbc101362d3fd5f72087bdee644` (`main@2741200`).
- PR #88 adds frozen `MediaCompositionScene`, `MediaCompositionTask` and `MediaCompositionResult` records, the runtime-checkable `MediaComposer` interface and explicit-injection `FFmpegMediaComposer`. It composes at least two ordered playable visual/voice Scene inputs only after real Workspace re-probes, writes canonical attached subtitle cues, and emits MP4-family H.264 `540x960` 24 fps `yuv420p` + AAC 48 kHz mono + one `mov_text` stream with deterministic task-binding metadata.
- PR #88 commits only through the task Workspace and proves exact result/byte replay, changed ordered inputs/timing/subtitle/lineage conflict without overwrite, safe generic failures and independent final-output/subtitle probes. Main review recorded the 580-line soft-cap pause, semantic reuse to 511 lines, `CHANGES_REQUESTED` for fake timeout and insufficient exact/reorder/timing evidence, same-Luna correction, 3 focused tests, 6 integration tests, 280 full tests, compileall/tool/probe checks and a forged 44.1 kHz final-audio mutation. GitHub reported no status checks for PR #88, so this is local synthetic Fixture evidence only.
- The #88 evidence boundary is playable composed synthetic output (color clips, artificial tones and attached subtitles), not product-path ProductionOrchestrator composition, Subtitle/Master Audio/Video Artifact Commit, Task/gate integration, Final Review, export, prompt-faithful visual, spoken TTS, real Provider, paid media, UI or deployment evidence.
- Issue #91 is closed as completed; its sole M3-006 product-path composition and media Artifact recovery Task Contract was independently approved and delivered by merged PR #92.
- PR #92 implementation commit is `26bffd61b4f5f04039c2d33c1e881ac99e007f8d`; merge commit is `8f4868157b532af73f21c37743b7b6c67fa5b55e` (`main@8f48681`).
- PR #92 adds the sole public `ProductionOrchestrator.compose` path and exact `ProductionCompositionResult`; it validates one committed Request/Timeline plus terminal zero-charge Scene attempts, stages Scene Clip/Scene Audio, Subtitle, logical Master Audio and Video Artifact commits, and preserves exact lineage, replay and staged Video-commit recovery.
- PR #92 merge evidence is 12 focused composition unit tests, 1 durable local FFmpeg/SQLite integration test, 293 full regression tests, compileall, real local FFmpeg/ffprobe probes and a mutation audit for a mutable repository snapshot plus the exact committed Request scalar family. Main-controller review returned `CHANGES_REQUESTED` in two rounds and then independently approved the corrected result. GitHub reported no hosted checks.
- The #92 evidence boundary is local FFmpeg synthetic color/tone/subtitle Fixture output only; Master Audio is a logical ordered assembly rather than standalone-file evidence. This does not prove Task/gate integration, Final Review/scene retry, export, real Provider, fees, UI, deployment or full E2E evidence.
- Issue #95 is closed as completed; its sole M3-007 durable mandatory Final Video Review decision Task Contract was independently approved and delivered by merged PR #96.
- PR #96 implementation commit is `6fc259eb2f9836f517785dbc41b2206e82ca2a7e`; merge commit is `b3f2999e509a5467b590679177ec62f1c938ba41` (`main@b3f2999`).
- PR #96 adds frozen/slotted assessment, finding, failure and decision records, a runtime-checkable Final Video decision repository seam, the in-memory default and SQLite v1 adapter. It assesses the exact PR #92 Video structure and canonical Scene Clip/Subtitle/Master Audio binding, issues deterministic hard blocks, enforces mandatory `approve|reject|revise`, and preserves exact replay/conflict plus restart/two-instance/corruption behavior.
- PR #96 merge evidence is 6 focused contract tests, 6 SQLite integration tests, 305 full regression tests, compileall, diff/allowlist/protected audits and main-controller independent review. The first review returned `CHANGES_REQUESTED` for the foreign Scene Clip canonical-binding defect and missing single-mutation evidence; the same Luna corrected both, removed a private helper from module `__all__`, and the final verdict was `APPROVED`. GitHub reported no hosted checks.
- The #96 evidence boundary is decision/persistence only. It does not prove Task/Workflow gate advance, scene retry/replace, export, media probes, Workspace writes, real Provider calls, fees, UI, deployment or full E2E evidence.
- Issue #99 is closed as completed; its sole M3-008 durable namespaced Final Video Review Workflow + Application gate Task Contract was independently approved and delivered by merged PR #100.
- PR #100 implementation commit is `e99e75c76e0852343ac4495b4e900bb17a19e734`; merge commit is `f3e536dce655d16d188b8924066c978254e83c6d` (`main@f3e536d`).
- PR #100 persists the exact Final Video decision before Workflow state advance through the fixed `final_video_review` namespace; the Script default namespace and Final Video namespace coexist for the same public thread in one SQLite checkpoint database. Review corrections covered exact-type/AlwaysEqual Video and decision binding, and restored six read-only Workflow result projections.
- PR #100 merge evidence is 10 workflow tests, 12 application tests, 2 durable integration tests, 329 full local regression tests, compileall and diff checks. GitHub reported no hosted checks.
- The #100 evidence boundary excludes real Provider, fees, deployment, Task projection media lifecycle, scene retry/replace, export/package and UI evidence. Issue #101 is the docs-only alignment and authorizes no next Task Contract or public API.
- Issue #103 is closed as completed; its sole M3-009 deterministic approved-video Publish Package and Artifact Manifest Task Contract was independently approved and delivered by merged PR #104.
- PR #104 implementation commit is `5b8d9f7ea3624a7ac88389f76898eeec3b7f732f`; merge commit is `682ecbd1633ff22f181cb5d5161bea6b0a05433e` (`main@682ecbd`).
- PR #104 adds the public `PackagingFailure`, `PublishPackageResult` and `PublishPackageBuilder` seam. Exact approved Video + Subtitle + reachable Source Record facts produce one deterministic local ZIP in Workspace `exports`, then exact Artifact Manifest and Publish Package v1 facts; ZIP order is Video, canonical SRT, source attribution without source text, Artifact Manifest, with deterministic metadata and byte/hash facts verified.
- PR #104 validates the exact Final Video decision and lineage before Workspace/Artifact side effects, and verifies replay/conflict/no-v2 plus Manifest/Package staged recovery. Durable evidence uses SQLite Artifact + Final Video decision repositories, FilesystemWorkspace restart, independent ZIP parse, byte-equal playable MP4 and optional ffprobe.
- PR #104 merge evidence is focused public contract 10, durable integration 1, full local regression 340, compileall and diff/allowlist/protected gates passed. The initial `tests/packaging` namespace shadowed third-party `packaging.version` under full discovery and was corrected to `tests/test_packaging_builder.py`; main returned two bounded `CHANGES_REQUESTED` rounds for exact type/lineage/media/public evidence/private coupling, the same Luna corrected them, and `builder.py` is 647 lines below the 650 hard cap. GitHub reported no hosted checks; evidence is local only.
- The #104 evidence boundary excludes real Provider, network service, fees, deployment, external publication, Task media projection, scene retry and UI evidence. Issue #105 is the docs-only alignment and authorizes no open implementation Task Contract or public API.

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
| Luna current discoverability | Completed and closed after handoff | exact `luna-worker` for Issue #103 was closed after the completed handoff; no active worker remains; this is route/closure evidence, not independent Issue #103 runtime identity |
| Last independently exposed Luna runtime | RUNTIME_VERIFIED | Issue #79 Luna task `019ff4d3-628a-7eb0-a7cb-c4d6c390a205` host `turn_context`: `gpt-5.6-luna / max`; this remains the last independently exposed Luna runtime evidence and does not claim the Issue #103 or Issue #105 runtime |
| Issue #95 Luna route | UNVERIFIED_RUNTIME_MODEL | Exact `luna-worker` route is required by the Task Contract; this snapshot exposes no independent Issue #95 task UUID or host `turn_context`, so its runtime model is not separately claimed |
| Issue #99 Luna route | UNVERIFIED_RUNTIME_MODEL | Exact `luna-worker` route is required by the Task Contract; this snapshot exposes no independent Issue #99 task UUID or host `turn_context`, so its runtime model is not separately claimed |
| Issue #103 Luna route | UNVERIFIED_RUNTIME_MODEL | Exact `luna-worker` route is required by the Task Contract; this snapshot exposes no independent Issue #103 task UUID or host `turn_context`, so its runtime model is not separately claimed |
| Issue #93 docs runtime | UNVERIFIED_RUNTIME_MODEL | This docs-only alignment exposes no independent Issue #93 task UUID or host `turn_context`; no runtime identity/model claim is made |
| Issue #97 docs runtime | UNVERIFIED_RUNTIME_MODEL | This docs-only alignment exposes no independent Issue #97 task UUID or host `turn_context`; no runtime identity/model claim is made |
| Issue #101 docs runtime | UNVERIFIED_RUNTIME_MODEL | This docs-only alignment exposes no independent Issue #101 task UUID or host `turn_context`; no runtime identity/model claim is made |
| Issue #105 docs runtime | UNVERIFIED_RUNTIME_MODEL | This docs-only alignment exposes no independent Issue #105 task UUID or host `turn_context`; no runtime identity/model claim is made |
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

Issue #71 implementation is isolated in reviewed commit `6d14524` and changes only:

- `src/ai_course_factory/production/model.py`；
- `src/ai_course_factory/production/interfaces.py`；
- `src/ai_course_factory/production/adapters/__init__.py`；
- `src/ai_course_factory/production/adapters/fake.py`；
- `src/ai_course_factory/production/__init__.py`；
- `tests/production/test_media_interfaces.py`；
- `tests/integration/test_fake_media_adapters.py`。

The exact Luna recorded the missing public-interface RED and implemented only provider-neutral visual/voice values, interfaces and deterministic Fake Fixture adapters. Independent Review reproduced huge-integer misclassification and exact-type bypasses, then required exact result/envelope and visual+voice replay/conflict evidence. The same Luna corrected the bounded defects without adding a Provider or playable media path; the orchestrator reran all gates, returned `APPROVED`, and closed the worker immediately after each completed handoff.

Issue #75 implementation is isolated in reviewed commit `c48177a` and changes only:

- `src/ai_course_factory/production/attempt.py`；
- `src/ai_course_factory/production/sqlite_attempt.py`；
- `src/ai_course_factory/production/__init__.py`；
- `tests/production/test_provider_attempt_repository_contract.py`；
- `tests/integration/test_sqlite_provider_attempt_ledger.py`。

The exact Luna added one atomic execution-claim signal while preserving the prior Provider-attempt methods. Independent Review reproduced a cross-Authorization idempotency regression in the in-memory group validator and an incorrect storage-failure category. The same Luna corrected the group-owner binding and safe failure normalization; the orchestrator reran focused/full gates and repeated the two-instance claim race, returned `APPROVED`, and closed the worker immediately after handoff.

Issue #79 implementation is isolated in reviewed commit `367047a` and changes only:

- `src/ai_course_factory/production/__init__.py`；
- `src/ai_course_factory/production/model.py`；
- `src/ai_course_factory/production/orchestrator.py`；
- `tests/production/test_orchestrator.py`；
- `tests/integration/test_offline_production_orchestrator.py`。

The exact Luna implemented one explicit-injection, claim-gated offline Orchestrator for one exact Production Request/media task. It invokes only the matching deterministic Fake adapter for `created=True`, persists a zero-charge terminal outcome, and safely reconstructs terminal replay without a duplicate Adapter call. Independent Review killed forged task/claim/result/complete records, noncanonical references and nonzero terminal-charge mutations; the final verdict was `APPROVED`. Fake Fixture bytes remain non-playable, and no Composer/FFmpeg, subtitle/video Artifact, Final Review/export, real Provider, network, live pricing, fees, UI or deployment behavior was added.

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

### M3 milestone review

- M3-001 is independently approved and merged by PR #72 at `main@60af4d2`；
- M3-002 is independently approved and merged by PR #76 at `main@39efaa4`；
- M3-003 is independently approved and merged by PR #80 at `main@42cf6c2` (implementation commit `367047a`)；
- M3-004 is independently approved and merged by PR #84 at `main@88309e0` (implementation commit `b8e2d70`)；
- M3-005 is independently approved and merged by PR #88 at `main@2741200` (implementation commit `fb9ef21`)；
- M3-006 is independently approved and merged by PR #92 at `main@8f48681` (implementation commit `26bffd6`)；
- M3-007 is independently approved and merged by PR #96 at `main@b3f2999` (implementation commit `6fc259e`)；
- M3-008 is independently approved and merged by PR #100 at `main@f3e536d` (implementation commit `e99e75c`)；
- M3-009 is independently approved and merged by PR #104 at `main@682ecbd` (implementation commit `5b8d9f7`)；
- provider-neutral visual/voice interfaces and deterministic non-playable Fake Fixture adapters now write only through the task Workspace with exact replay/conflict evidence；
- atomic Provider-attempt claims now distinguish the one new execution owner from restart/concurrent replay before a future Adapter call；
- the offline Production Orchestrator now validates one exact Request/media task, invokes only the matching Fake adapter after a new claim, persists zero-charge terminal outcomes and safely replays terminal state；
- separate playable local FFmpeg Fixture visual/voice adapters now validate real ffprobe output before Workspace commit, preserve exact task-bound bytes on replay/conflict, and support zero-charge terminal restart replay；
- the local `FFmpegMediaComposer` now validates and re-probes at least two ordered playable Scene inputs, emits a deterministic MP4-family H.264/AAC output with one attached `mov_text` subtitle stream, and preserves Workspace-only replay/conflict/no-overwrite behavior；
- product-path `ProductionOrchestrator.compose` now validates the exact committed Request/Timeline and terminal Scene attempts, stages Scene Clip/Scene Audio, Subtitle, logical Master Audio and Video Artifact commits, and preserves exact lineage, replay and staged recovery；
- the durable Final Video Review decision seam now assesses exact Video structural lineage, enforces hard-block and Creator action rules, and persists exact decisions through in-memory and SQLite repositories with replay/conflict/restart/corruption evidence；
- the namespaced Final Video Review Workflow + Application gate now persists the exact Final Video decision before state advance; Script default and `final_video_review` checkpoint namespaces coexist for one public thread in one SQLite database, with 10 workflow, 12 application, 2 durable integration and 329 full local tests recorded；
- the deterministic local Publish Package seam now validates exact approved Video/Subtitle/Source lineage, writes the ordered ZIP and exact Manifest/Package v1 facts through Workspace/Artifact boundaries, and preserves replay/conflict/no-v2 and staged recovery evidence；
- M3 remains active: Task projection media lifecycle integration and scene retry/replace remain not implemented or authorized; bounded local export/package is complete, while real Provider, fees, UI and deployment remain closed；
- no real Provider, credential, fee, SDK, network or deployment evidence exists。

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

1. Issue #105 is docs-only and authorizes no next implementation Task Contract. If work resumes, establish a separate bounded Task Contract and architecture review for Task projection media lifecycle integration or scene retry/replace; do not invent a public API, select or call a real Provider, incur fees, or add UI/deployment.
2. Keep all real Provider, cost and deployment gates closed.
