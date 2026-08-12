# Goal: Deliver AI Course Factory Core MVP v1.0

## 1. Goal Status

| Field | Value |
| --- | --- |
| Status | ACTIVE — M0 complete; M1 results 1–4 merged; result 5 active under Issue #34 |
| Approval | Product Owner, 2026-08-12 |
| Goal Owner | Product Owner |
| Orchestrator | ORCHESTRATOR_REVIEWER — `gpt-5.6-sol / xhigh` |
| Implementer | exact `luna-worker` — configured `gpt-5.6-luna / max` |
| Baseline | code parent `08085e4`; approved planning baseline `4c00eb2` |
| Coding Authorization | Granted for bounded M1–M4 tasks after milestone/task/runtime gates pass |
| External Provider Authorization | Not granted |
| Deployment Authorization | Not granted |
| Last Updated | 2026-08-12 |

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

当前 `main` 已完成并通过 98 tests：

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
```

未完成：Production Request、Budget、持久化、本地工作台、Provider、媒体合成、Final Review、恢复和导出。当前 Character/Storyboard/decision/Timeline 证据只覆盖 no-Provider、in-memory planning boundary。

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

Status：**ACTIVE** — results 1–4 of 7 are independently `APPROVED` and merged; result 5 is the sole active bounded task under Issue #34 on `codex/34-production-request-planning`; results 6–7 remain pending and unauthorized without their own Task Contracts.

Outcome：现有 exact approved Script 形成 provider-neutral、预算受控的生产入口。

Ordered results：

1. Character Candidate -> exact Character Reference（复核并沿用 Issue #23）；
2. Storyboard Candidate -> exact Storyboard Reference；
3. optional Storyboard approve/skip decision；
4. Timeline Candidate -> exact Timeline Reference；
5. Production Request Candidate -> exact Request Reference；
6. Budget Candidate + mandatory Creator authorization；
7. no-Provider integration proof。

Exit：所有 planning Artifacts lineage 可追溯；Production Agent 不 Commit、不调用 Provider；未授权 Request 不能进入生产。

### M2 — Durable Local Task Runtime

Outcome：当前纵向切片和 M1 结果在进程重启后可恢复，并具有最小本地任务应用接口。

Results：

- Artifact repository interface contract 和 SQLite Adapter；
- persistent Decision/Budget/Provider attempt records；
- persistent LangGraph checkpoint；
- task aggregate、selected refs、status/stale/impact；
- task-scoped filesystem workspace；
- restart/replay/migration tests。

Exit：创建、review、revision、planning 和 budget checkpoint 在重启后 exact 恢复；现有 66 tests 保持通过。

### M3 — Safe Offline Production Closure

Outcome：无费用环境中用 Fake Visual/TTS + FFmpeg 生成可播放视频并完成 Final Review 和导出。

Results：

- Production Orchestrator；
- visual/voice/composer interfaces；
- Fake Adapters；
- Provider Execution Record、attempt 和 bounded retry；
- subtitle/audio/video Artifact；
- Final Review、scene retry/replace；
- Manifest/Publish Package。

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
