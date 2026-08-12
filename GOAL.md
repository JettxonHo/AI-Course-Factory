# Goal: Deliver AI Course Factory Core MVP v1.0

## 1. Goal Status

| Field | Value |
| --- | --- |
| Status | ACTIVE — M0, M1 and M2 complete; M3-001 through M3-009 complete; M3 remains active with Task projection media lifecycle integration and scene retry/replace pending; bounded local export/package is complete; real Provider, fees, UI and deployment remain pending/unauthorized |
| Approval | Product Owner, 2026-08-12 |
| Goal Owner | Product Owner |
| Orchestrator | ORCHESTRATOR_REVIEWER — `gpt-5.6-sol / xhigh` |
| Implementer | exact `luna-worker` — configured `gpt-5.6-luna / max` |
| Baseline | code parent `08085e4`; approved planning baseline `4c00eb2` |
| Coding Authorization | Granted for bounded M1–M4 tasks after milestone/task/runtime gates pass |
| External Provider Authorization | Not granted |
| Deployment Authorization | Not granted |
| Last Updated | 2026-08-13 |

## 2. Objective

交付一个可在本地启动和操作的 AI Course Factory Core MVP：Creator 输入 Microsoft `AI-For-Beginners` 公开仓库，完成来源可追溯的中文 Script、Production Planning、预算批准、真实媒体生成、Final Review，并导出可播放视频和可审计发布包。

Goal 的唯一完成结论必须由运行证据证明，而不是由文档、Fake Provider 或局部测试推断。

## 3. Required Reading

按顺序：

1. `AGENTS.md`
2. `docs/README.md`
3. `docs/product/PRD.md`
4. `docs/spec/SYSTEM-SPEC.md`
5. `docs/spec/IMPLEMENTATION-SPEC.md`
6. `docs/DEVELOPMENT-WORKFLOW.md`
7. `docs/STATUS.md`
8. 当前 GitHub Issue / 唯一 Task Contract

历史 Phase 文档只在上述文件明确引用时作为背景或证据使用。

## 4. Current Starting Point

当前 `main@682ecbd1633ff22f181cb5d5161bea6b0a05433e` 已完成并通过 340 local tests：

```text
Public GitHub
  -> exact Source Record
  -> grounded Knowledge
  -> Course / Episode Plan
  -> versioned six-scene Script
  -> mandatory Script Review
  -> exact approved Script
  -> provider-neutral Character Candidate
  -> exact Character Reference through the existing Artifact Store
  -> provider-neutral ordered Storyboard Candidate
  -> exact Storyboard Reference through the existing Artifact Store
  -> exact optional Storyboard approve/skip decision
  -> provider-neutral contiguous Timeline Candidate
  -> exact Timeline Reference through the existing Artifact Store
  -> provider-neutral Production Request Candidate
  -> exact Production Request Reference through the existing Artifact Store
  -> provider-neutral Production Budget Candidate from a Request-bound local Fixture price snapshot
  -> exact Production Budget Reference through the existing Artifact Store
  -> mandatory Creator Budget Review decision
  -> independent exact Budget Authorization after valid approval
  -> offline exact approved-Script-to-Authorization integration proof
  -> shared ArtifactRepository contract
  -> durable SQLite Artifact commit/get, restart and replay proof
  -> persistent exact Script Creator decision before Workflow resume
  -> persistent exact Storyboard approve/skip decision accepted by Timeline after restart
  -> atomic persistent Budget decision and Authorization after restart
  -> persistent LangGraph Script Review checkpoint with pending/terminal restart and replay proof
  -> persistent Task projection with exact selected References, stale impact, history and command replay
  -> task-scoped filesystem workspace with atomic immutable blob commit and restart/race proof
  -> persistent Provider-attempt ledger with pre-call Budget reservation and terminal-outcome recovery
  -> atomic Provider-attempt execution claim distinguishing new ownership from restart/replay
  -> provider-neutral visual/voice generation interfaces
  -> deterministic non-playable Fake visual/voice Fixture bytes committed only through the task Workspace
  -> playable local FFmpeg Fixture visual/voice media committed only through the task Workspace
  -> claim-gated offline Production Orchestrator for one exact visual/voice Scene operation
  -> zero-charge terminal Provider-attempt outcome with safe terminal restart replay
  -> exact ordered MediaComposition task with validated playable visual/voice Scene inputs and bounded subtitle text/timing
  -> local FFmpeg MediaComposer output with attached mov_text subtitles and deterministic task-binding metadata
  -> product-path ProductionOrchestrator composition for one exact committed Request and terminal visual/voice attempts
  -> exact Scene Clip/Scene Audio, Subtitle, logical Master Audio and Video Artifact lineage with staged replay/recovery
  -> durable mandatory Final Video Review assessment/decision seam for one exact Video Version
  -> durable namespaced Final Video Review Workflow + Application gate with exact decision persisted before Workflow state advance
  -> deterministic local Publish Package ZIP from exact approved Video, Subtitle and Source Record
  -> exact Artifact Manifest and Publish Package v1 facts with staged replay/recovery
```

未完成：本地工作台、Task projection media slots/lifecycle integration、真实 Provider、scene retry/replace、UI 和部署。Artifact Version、Script/Storyboard Creator decisions、Budget Authorization、现有 Script Review checkpoint、Task projection、task-scoped filesystem workspace、Provider-attempt ledger、visual/voice Fake Fixture 输出、playable local FFmpeg Fixture media、claim-gated offline Production Orchestrator、本地 FFmpeg MediaComposer、产品路径 composition、exact Scene Clip/Scene Audio、Subtitle、logical Master Audio 和 Video Artifact lineage/replay/recovery、durable mandatory Final Video Review decision seam，以及 namespaced Final Video Review Workflow + Application gate、deterministic local Publish Package and Artifact Manifest 已具备有界证据；后者在 state advance 前持久化 exact Final Video decision，并与同一 public thread 的 Script 默认 checkpoint namespace 共存。Publish Package exposes the public `PackagingFailure`, `PublishPackageResult` and `PublishPackageBuilder` seam; exact approved Video + Subtitle + reachable Source Record produce one deterministic ZIP in Workspace `exports`, followed by exact Artifact Manifest and Publish Package v1 facts. ZIP order is Video, canonical SRT, source attribution without source text, and Artifact Manifest, with deterministic metadata and byte/hash facts verified; exact Final Video decision and lineage validation precede Workspace/Artifact side effects, and replay/conflict/no-v2 plus Manifest/Package staged recovery are verified. Master Audio 是有序 Scene Audio References 的 logical assembly，不是 standalone blob。Budget price、Fake media、FFmpeg media、composition and Publish Package evidence remain deterministic local Fixtures; Fake Fixture bytes are non-playable, FFmpeg media and the composed MP4 are synthetic color/tone output rather than prompt-faithful visual or spoken TTS, and the offline production/package evidence does not prove Task projection media lifecycle, scene retry/replace, real Provider, live pricing, fees, paid execution, UI or deployment evidence。

## 5. In Scope

- 单个公开 GitHub source 和固定 Demo episode；
- exact source commit 与 claim grounding；
- Script mandatory review 和 revision；
- Character、Storyboard、Timeline、Production Request；
- optional Storyboard decision；
- Budget estimate、authorization 和 retry limit；
- 一个真实 Visual Provider Adapter；
- 一个真实 TTS Provider Adapter；
- FFmpeg 媒体探测与合成；
- Final Video mandatory review；
- exact Artifact version/dependency、stale/impact 和 scene-level retry；
- SQLite + task-scoped filesystem 持久化；
- 本地单用户 Web Workspace；
- approved video、subtitle、source attribution 和 Manifest 导出；
- offline E2E、provider smoke 和真实受预算约束的 E2E 验收。

## 6. Out of Scope

- 多用户、登录、权限、多租户、云 SaaS；
- 私有仓库产品化；
- 多知识源、多课程批量生产；
- 动态模板编辑、专业视频编辑；
- 多 Provider 路由或自动故障转移；
- 自研基础模型、Voice Clone；
- 自动发布；
- ContentOS/Marketplace 平台化；
- 生产云部署和商业计费。

## 7. Milestones

### M0 — Planning Baseline and Goal Gate

Status：**COMPLETE** — planning baseline `4c00eb2`; main-agent and Luna runtime gates verified; Issue #23 aligned as the sole M1 Task Contract.

Outcome：PRD、两个 Spec、开发协议、STATUS 和本 Goal 边界一致，并由 Product Owner 批准。

Exit：

- v1.0 文档交叉检查通过；
- 历史与在途材料已明确归档/保护规则；
- 项目级 `gpt-5.6-sol / xhigh` 与 `luna-worker` 配置可验证；
- Product Owner 明确批准本 Goal；
- Issue #23 与新 Goal/Spec 完成对齐，不扩大范围。

### M1 — Approved Script to Authorized Production Request

Status：**COMPLETE** — all 7 results are independently `APPROVED` and merged; result 7 was delivered by PR #41 at `main@13ccba4`.

Outcome：现有 exact approved Script 形成 provider-neutral、预算受控的生产入口。

Ordered results：

1. Character Candidate -> exact Character Reference（复核并沿用 Issue #23）；
2. Storyboard Candidate -> exact Storyboard Reference；
3. optional Storyboard approve/skip decision；
4. Timeline Candidate -> exact Timeline Reference；
5. Production Request Candidate -> exact Request Reference；
6. Budget Candidate + mandatory Creator authorization；
7. no-Provider integration proof。

Exit：**PASSED** — the offline cross-slice proof traces every planning Artifact and exact decision through a separate valid Budget Authorization; Production Agent does not Commit or call a Provider; reject and underfunded approve produce no Authorization. This does not prove persistent authorization or a production-side call blocker, which belong to M2/M3.

### M2 — Durable Local Task Runtime

Status：**COMPLETE** — all 8 bounded implementation results are independently `APPROVED` and merged; result 8 was delivered by PR #68 at `main@437d8ca`.

Outcome：当前纵向切片和 M1 结果在进程重启后可恢复，并具有最小本地任务应用接口。

Results：

- Artifact repository interface contract 和 SQLite Adapter（**COMPLETE** — PR #44）；
- persistent Decision/Budget/Provider attempt records（**COMPLETE** — Script/Storyboard/Budget decisions and Budget Authorization by PR #47/#50/#54; pre-call Provider-attempt reservation/outcome ledger by PR #68）；
- persistent LangGraph checkpoint（**COMPLETE** — PR #57 for the existing Script Review control slice）；
- task aggregate、selected refs、status/stale/impact（**COMPLETE** — PR #60 for the durable Task projection）；
- task-scoped filesystem workspace（**COMPLETE** — PR #64 for fixed task areas, atomic immutable blobs and restart/race safety）；
- restart/replay/migration tests。

Exit：**PASSED** — exact Artifact/decision/authorization/checkpoint/Task/workspace/attempt state survives bounded restart/replay tests, invalid or unknown attempt state fails closed, and the current regression baseline remains green. This does not prove a Production Orchestrator, any Provider invocation, media generation, fees, live pricing, broader Workflow gates or deployment.

### M3 — Safe Offline Production Closure

Status：**ACTIVE** — M3-001 至 M3-009 已独立批准并合并；bounded local Publish Package/export complete；Task projection media lifecycle integration 和 scene retry/replace 仍待后续有界任务。

Outcome：无费用环境中用 Fake Visual/TTS + local FFmpeg Fixtures 生成可播放 per-operation 媒体和本地合成 MP4，已接入产品路径并形成可恢复媒体 Artifacts；durable mandatory Final Video Review decision seam、namespaced Final Video Review Workflow + Application gate（state advance 前持久化 exact decision）以及 deterministic local Publish Package/export 已完成，但 Task projection media lifecycle integration 和 scene retry/replace 仍待后续有界任务。

Results：

- Production Orchestrator（**COMPLETE** — PR #80 at `main@42cf6c2`, implementation commit `367047a`; one exact Production Request/media task acquires one atomic claim, invokes only the matching deterministic Fake adapter for `created=True`, persists a zero-charge terminal outcome, and safely replays terminal state without a duplicate adapter call）；
- visual/voice/composer interfaces（**PARTIAL** — provider-neutral visual/voice interfaces completed by PR #72, playable local FFmpeg Fixture adapters by PR #84, the MediaComposer seam/local implementation by PR #88, and product-path wiring by PR #92; the durable Final Video Review decision seam is complete through PR #96 and the namespaced Final Video Review Workflow + Application gate through PR #100, while Task projection media lifecycle integration remains pending）；
- Fake Adapters（**PARTIAL** — deterministic visual/voice non-playable Fixture adapters completed by PR #72; separate playable per-operation FFmpeg Fixture adapters completed by PR #84; local composition and product-path Orchestrator wiring are complete through PR #92; the durable Final Video Review decision seam is complete through PR #96 and the namespaced Final Video Review Workflow + Application gate through PR #100; bounded local Publish Package/export is complete, while Task projection media lifecycle integration and scene retry/replace remain pending）;
- playable local FFmpeg Fixture media（**COMPLETE** — PR #84; visual H.264 540x960 24 fps `yuv420p` with no audio, voice AAC 48 kHz mono with no video, MP4-family bytes; exact task-binding metadata, real ffprobe validation before Workspace commit, byte-exact replay/conflict and zero-charge terminal restart replay）；
- MediaComposer seam and local FFmpeg composition（**COMPLETE** — PR #88 at `main@2741200`, reviewed implementation commit `fb9ef21`; frozen `MediaCompositionScene` / `MediaCompositionTask` / `MediaCompositionResult` records, runtime `MediaComposer`, and `FFmpegMediaComposer` compose at least two ordered playable Scene inputs after real input probes, generate canonical attached subtitle cues, produce MP4-family H.264 540x960 24 fps `yuv420p` + AAC 48 kHz mono + one `mov_text` stream, bind deterministic task metadata, and commit only through Workspace with exact replay/conflict/no-overwrite evidence）；
- product-path composition and exact media Artifacts（**COMPLETE** — PR #92 at `main@8f48681`, implementation commit `26bffd61b4f5f04039c2d33c1e881ac99e007f8d`; exact committed Request/Timeline and zero-charge terminal Scene attempts validate before staged Scene Clip/Scene Audio, Subtitle, logical Master Audio and Video Artifact commits; exact lineage, replay and staged recovery preserve immutable upstream facts and Workspace output. Master Audio is a logical ordered assembly, not standalone-file evidence; output remains local FFmpeg synthetic Fixture evidence）；
- durable mandatory Final Video Review decision seam（**COMPLETE** — PR #96 at `main@b3f2999`, implementation commit `6fc259e`; Issue #95 closed. Frozen/slotted assessment, finding, failure and decision records, runtime repository seam, in-memory default and SQLite v1 adapter assess one exact PR #92 Video structure and canonical Scene Clip/Subtitle/Master Audio binding, enforce deterministic hard blocks and mandatory `approve|reject|revise`, and preserve exact replay/conflict plus restart/two-instance/corruption behavior. This is decision/persistence evidence only; Task projection media lifecycle integration and scene retry/replace remain pending）；
- durable namespaced Final Video Review Workflow + Application gate（**COMPLETE** — PR #100 at `main@f3e536d`, implementation commit `e99e75c`; Issue #99 closed. Exact Final Video decision persistence occurs before Workflow state advance; fixed `final_video_review` checkpoint namespace coexists with the Script default namespace for the same public thread in one SQLite database. Evidence is 10 workflow tests, 12 application tests, 2 durable integration tests and 329 full local regression tests; no hosted checks, real Provider, fees, deployment, Task projection media lifecycle, scene retry/replace or UI evidence）；
- deterministic local Publish Package and Artifact Manifest（**COMPLETE** — M3-009, Issue #103, PR #104 at `main@682ecbd`, reviewed implementation commit `5b8d9f7ea3624a7ac88389f76898eeec3b7f732f`. Public `PackagingFailure`, `PublishPackageResult` and `PublishPackageBuilder` seam; exact approved Video + Subtitle + reachable Source Record produce one deterministic local ZIP in Workspace `exports`, then exact Artifact Manifest and Publish Package v1 facts. ZIP order is Video, canonical SRT, source attribution without source text, Artifact Manifest; deterministic metadata and byte/hash facts are verified. Exact Final Video decision and lineage validation precede Workspace/Artifact side effects; replay/conflict/no-v2 and Manifest/Package staged recovery are verified. Evidence uses SQLite Artifact + Final Video decision repositories, FilesystemWorkspace restart, independent ZIP parse, byte-equal playable MP4 and optional ffprobe. Focused public contract 10, durable integration 1, full local regression 340, compileall and diff/allowlist/protected gates passed; GitHub reported no hosted checks and evidence is local only. Initial `tests/packaging` namespace shadowed third-party `packaging.version` under full discovery and was corrected to `tests/test_packaging_builder.py`; main returned two bounded `CHANGES_REQUESTED` rounds for exact type/lineage/media/public evidence/private coupling, the same Luna corrected them, and `builder.py` is 647 lines below the 650 hard cap）；
- Provider Execution Record、attempt 和 bounded retry（**PARTIAL** — persistent attempts and atomic new-vs-existing execution claims completed by PR #68/#76; bounded offline Orchestrator execution completed by PR #80; automatic retry remains pending）；
- Task projection media lifecycle integration、scene retry/replace；

Exit：offline E2E 从 approved Script 到 approved playable MP4 和 export package；Fake 身份在证据中清楚标记。

### M4 — Local Creator Workspace

Outcome：Creator 可以通过 loopback Web UI 完成核心主流程，而不需要调用 Python 内部接口。

Results：

- create task、status 和 Artifact viewer；
- Script review；
- planning/budget views；
- production monitor、scene failure/retry；
- video preview、Final Review 和 export；
- UI behavior tests 与浏览器证据。

Exit：在 offline providers 下完整用户流程可从 UI 操作，刷新和重启不丢状态。

### M5 — Authorized Real Provider Path

Entry human gates：

- `PD-001` Visual Provider/model/credentials approved；
- `PD-002` TTS Provider/voice/credentials approved；
- `PD-003` smoke 和 full Demo 预算/attempt 上限 approved。

Outcome：真实 Adapter 在预算门内完成场景媒体生产。

Results：

- official provider contract verification；
- visual and TTS adapters；
- opt-in contract/smoke tests；
- cost, timeout, failure and unknown-attempt handling；
- minimal authorized smoke evidence。

Exit：每个真实 Adapter 至少一次受控成功和一个失败映射证据；CI 默认不产生费用。

### M6 — Real End-to-End MVP Acceptance

Outcome：固定 Demo 通过真实 Provider 形成可交付视频包。

Exit：

- 从 source URL 到 export 的真实用户流程完成；
- 9:16 简体中文视频可播放；
- Script、Budget、Final Video gates 有 exact decisions；
- claims、planning、attempt、media 和 Manifest lineage 完整；
- 未授权/超预算调用被真实阻断；
- 进程重启、一个失败恢复和一个 scene-level redo 已验证；
- 全量 test/build/CI 通过；
- Goal-level independent Review 通过。

## 8. Issue Strategy

- 每个 Issue 只有一个主要行为结果和一个主要 ownership。
- 每个 Agent/Artifact/Adapter seam 先通过自己的 Interface tests，再进入 integration Issue。
- 不为同一任务维护多套重复任务文件；Issue 正文或一个本地 Task Contract 二选一。
- Issue #23 保留，但在实际 dispatch 前必须根据本 Goal 的 authority、状态和允许文件重新对齐。
- 不预先创建 M4/M5 的 Provider-specific Issues，直到上游 Interface 稳定且 Product Owner 完成 PD-001 至 PD-003。

## 9. Agent and Review Rules

- 主控负责任务拆解、架构/产品裁决、分支/文件归属、独立 Review 和 Goal 验收。
- 有界实现交给 exact `luna-worker`；禁止自动 Terra fallback。
- Luna 不修改任务合同之外的文件，不批准自己的 PR，不自行扩展 Agent/Artifact/Workflow。
- 写入型核心任务默认串行；只有稳定接口后的独立 Adapter/UI 工作可并行。
- 同一 Review 问题连续两轮未解决时返回主控重构任务，不机械重试。

## 10. Verification Gates

每个 Issue 必须声明并通过：

- focused behavior tests；
- full regression；
- compile/static/build checks；
- changed-file and dependency audit；
- applicable integration/runtime evidence；
- `git diff --check`；
- independent Review。

里程碑完成是行为状态，不以文件数量、Mock 结果或 PR merge 本身判定。

## 11. Stop and Escalation Conditions

立即暂停受影响任务并升级主控/用户：

- PRD 与 Spec 无法同时满足；
- 必须改变公共 Artifact、Workflow 或 Application interface；
- 需要重大依赖、技术栈切换、数据迁移或大规模重写；
- 工作范围跨越当前 Issue；
- 需要真实 Provider/费用但授权不完整；
- 凭据、隐私、认证、生产部署或不可逆外部操作；
- 关键测试需被削弱才能通过；
- `luna-worker` 不可发现或出现明确 model mismatch；
- 相同缺陷连续两轮修复仍失败。

不受阻塞影响的调查、文档、Fake/Offline work 和独立 Review 可以继续。

## 12. Goal Completion Definition

Goal 只有在 M0 至 M6 全部通过、Product Acceptance Scenario 有真实运行证据、所有计划内 Issues/PRs 已关闭或有明确接受的 follow-up，并且主控给出 `GOAL_APPROVED` 或 `GOAL_APPROVED_WITH_FOLLOW_UPS` 时完成。

以下不能单独构成完成：

- 66 tests 或更多 unit tests 通过；
- Fake Provider E2E；
- 仅生成 Production Request；
- 一个媒体文件存在但不可追溯；
- 文档声称 Ready；
- PR 已合并但未进行 Goal-level Review。

## 13. Approval Record

| Role | Decision | Date | Notes |
| --- | --- | --- | --- |
| Product Owner | Approved | 2026-08-12 | Authorizes bounded M1–M4 coding after activation gates; does not authorize Provider cost, credentials, external calls or deployment. |
