# AI Course Factory Core MVP PRD v1.0

## 1. Document Status

| Field | Value |
| --- | --- |
| Status | Approved Product Baseline |
| Owner | Product Owner |
| Product | AI Course Factory |
| Target | Core MVP |
| Approved | 2026-08-12 by Product Owner |
| Last Updated | 2026-08-12 |
| Supersedes | `AI_Course_Factory_MVP_PRD_v0.3.md` as daily implementation baseline |
| Coding Authorization | Defined by approved `GOAL.md`; this PRD alone does not authorize work |

## 2. Product Thesis

AI Course Factory 帮助 AI Creator 把一个可追溯的知识源，转换为一条可审核、可恢复、最终可播放的教育短视频生产链。

MVP 不是“生成一段看起来像视频的内容”，而是证明：

```text
source-grounded knowledge
  -> human-approved teaching script
  -> provider-neutral production plan
  -> budget-authorized media production
  -> human-approved playable video
  -> traceable export package
```

只有这条链在一个本地应用中真实闭合，MVP 才成立。单元测试、Fake Provider 或若干独立 Artifact 不能代替产品闭环。

## 3. Primary User and Job

Primary User 是独立 AI Creator：

- 能理解基本技术材料，但不希望手工完成研究、脚本、分镜和媒体装配；
- 重视内容准确性、来源可追溯、成本可控和人工最终决定；
- 需要一个可重复的生产过程，而不是一次性 Prompt。

核心 Job：

> 给定一个公开技术课程仓库，我要在本地审核关键内容和预算，最终得到一条可播放、可追溯、可导出的中文教育短视频。

## 4. MVP Demonstration Contract

| Field | MVP Decision |
| --- | --- |
| Knowledge source | 一个公开 GitHub Repository |
| Demo source | Microsoft `AI-For-Beginners`，聚焦 Lesson 1 |
| Series | 小土豆学 AI |
| Episode | Episode 01《AI不是魔法》 |
| Audience | 成年 AI 初学者 |
| Language | 简体中文 |
| Episode shape | 6 个有序 Scene，总时长约 60 秒 |
| Aspect ratio | 9:16 |
| Character | 小土豆 v1.0 |
| Runtime | 本地、单用户、单任务工作台 |
| Visual production | 一个经 Product Owner 明确选择并授权的真实 Visual Provider |
| Voice production | 一个经 Product Owner 明确选择并授权的真实 TTS Provider |
| Delivery | 可播放视频 + 字幕 + 来源与 Artifact Manifest 的本地导出包 |

“6 Scene”是当前内容模板，不是系统协议固定字段。系统以有序 Scene 集合表达内容，但 MVP UI 不提供动态场景模板编辑。

## 5. User Flow

1. Creator 在本地工作台创建单次任务并输入公开 GitHub URL。
2. 系统验证仓库，锁定 exact commit，并显示读取范围。
3. 系统生成 Source Record、Knowledge、Course Plan、Episode Plan 和 Script。
4. Creator 在 Mandatory Script Review 中查看来源、批准、拒绝或要求修改 exact Script Version。
5. 系统从 approved Script 生成 Character、Storyboard、Timeline 和 provider-neutral Production Request。
6. 若启用 Storyboard Review，Creator 必须先批准 Storyboard；未启用时系统记录显式 skip 决定。
7. 系统根据 Request 和价格快照生成 Production Budget；Creator 明确批准金额上限。
8. Production Orchestrator 通过已配置 Adapter 生成 Scene visual、旁白、字幕并合成视频。
9. 系统自动检查必需文件、lineage、时长和格式，显示 Hard Block 与 Warning。
10. Creator 在 Mandatory Final Video Review 中批准、拒绝或要求场景级重做。
11. 批准后系统导出视频、字幕、来源说明和 Artifact Manifest。

任何会使下游结果失效的修改，执行前必须显示受影响范围；旧 Version 保留，不得静默覆盖。

## 6. P0 Product Requirements

### 6.1 Source and Grounding

- `PR-001`：接受一个公开 GitHub Repository URL，拒绝不支持或不可访问的输入。
- `PR-002`：读取必须绑定 exact commit；后续处理不得隐式漂移到仓库 latest。
- `PR-003`：Knowledge 中的教学 claim 必须保留可定位的 source locator。
- `PR-004`：已批准 Script 中的事实性教学 claim 必须能追溯到 Knowledge；缺失来源为 Hard Block。

### 6.2 Content and Script Review

- `PR-005`：生成 Course Plan、Episode Plan 和符合 Demo Contract 的简体中文 Script。
- `PR-006`：Script 以六个有序 Scene 表达，并记录每个 Scene 的来源 claim。
- `PR-007`：Script Review 必须暂停、保存并恢复；决定必须绑定 exact Script Version。
- `PR-008`：Reject 或 Revise 产生新 Script Version；旧 Version 和决定记录保留。
- `PR-009`：存在 Hard Block 时 Creator 不能 Approve。

### 6.3 Production Planning

- `PR-010`：approved Script 依次形成 Character、Storyboard、Timeline 和 Production Request。
- `PR-011`：每个 planning Artifact 必须 Commit 后再被下游使用，依赖为 exact References。
- `PR-012`：Production Request 是 provider-neutral 核心 Artifact；Provider Prompt/Request 只属于执行记录。
- `PR-013`：Storyboard Review 默认可选，但 Approve 或 Skip 必须留下明确决定。

### 6.4 Budget and Production

- `PR-014`：真实付费调用前必须存在价格快照、估算、重试上限和人工批准金额。
- `PR-015`：未批准预算或预计超限时不得调用付费 Provider。
- `PR-016`：Production Orchestrator 是唯一生产入口；顶层 Workflow 不直接调用 Visual、TTS 或媒体工具。
- `PR-017`：每个 Scene 产生可定位到 exact Production Request 和执行 attempt 的媒体结果。
- `PR-018`：旁白由独立 TTS 路径生成；最终视频由 visual、audio 和 subtitle 合成。
- `PR-019`：最终 MVP 证据必须包含至少一次经授权的真实 Visual Provider 和真实 TTS 执行。Fake 只用于开发与回归。

### 6.5 Review, Recovery and Delivery

- `PR-020`：系统区分 Provider Error、Generation Failure、Quality Failure 和 Budget Limit。
- `PR-021`：可重试技术失败只能在剩余预算和 Task Policy 内重试；默认总 attempt 不超过三次。
- `PR-022`：场景级失败不得删除其他有效 Artifact，Creator 可重试指定 Scene 或提供替代媒体。
- `PR-023`：Final Video Review 是 Mandatory Gate；未批准不得导出最终发布包或标记完成。
- `PR-024`：工作台显示任务阶段、核心 Artifact、exact Version、Gate、失败和可用动作。
- `PR-025`：导出包至少包含 approved video、subtitle、source attribution 和 Artifact Manifest。
- `PR-026`：系统只本地导出，不自动发布到外部平台。

## 7. Quality Rules

### Hard Block

- 缺少当前阶段必需 Artifact 或媒体文件；
- 事实性教学 claim 无来源；
- exact dependency 不匹配或 stale 结果被当作 current；
- 必选人工门禁未通过；
- 视频不可播放、格式不符或导出包缺少必需文件；
- 未经批准产生 Provider 费用。

### Warning

- 可识别但不稳定的角色外观；
- 节奏、镜头、视觉表达或主观教学质量可改善；
- 可选 BGM、Effect 或环境声缺失或表现不佳。

Creator 可以接受 Warning，但不能绕过 Hard Block。

## 8. Product Invariants

1. 所有跨阶段消费都绑定 exact Artifact Version。
2. 已批准 Version 不被覆盖；修订创建新 Version。
3. Agent 提议内容，Artifact 模块 Commit，Creator 批准；三种权限不合并。
4. Workflow 保存控制状态和 References，不复制 Artifact payload。
5. Provider-specific 表达不得进入核心 Production Request。
6. 真实费用始终位于显式预算授权之后。
7. Script 与 Final Video 两个人工门禁不可省略。

## 9. Non-goals

Core MVP 不包含：

- 多用户、账号、权限、多租户或云 SaaS；
- 私有仓库产品化鉴权；
- PDF、网页、YouTube、Notion 等多知识源；
- 多课程批处理或多任务看板；
- 动态 Scene 模板编辑器或专业时间线编辑器；
- 多 Provider 自动路由、自动故障转移或最低价选择；
- 自研视频、语音或语言模型；
- Voice Clone；
- 自动发布到社交或视频平台；
- Agent/Skill/Template Marketplace；
- 完整 ContentOS 抽象；
- 生产云部署或商业化计费。

## 10. MVP Acceptance

### Product Acceptance Scenario

**Given** 本地环境已配置经授权的 Visual 和 TTS Provider，Demo GitHub 仓库可访问，且 Creator 设定费用上限；

**When** Creator 从工作台创建 Episode 01，完成 Script、预算和 Final Video 必选审批；

**Then**：

1. 系统锁定 exact source commit；
2. approved Script 的教学 claims 全部可追溯；
3. Character、Storyboard、Timeline、Production Request 和 Budget lineage 完整；
4. 未经批准不发生付费调用；
5. 真实 Provider 生成结果被合成为可播放的 9:16 中文短视频；
6. Creator 可以查看 Warning、处理 Hard Block，并进行指定 Scene 重做；
7. Final approval 后导出包含视频、字幕、来源和 Manifest 的包；
8. 进程重启后任务、Artifact、Gate 和决定仍可恢复。

### Evidence Required

- 全量自动化测试通过；
- 本地应用启动和关键用户流程证据；
- 一次 offline Fake end-to-end 运行；
- 一次受预算约束的真实 Provider end-to-end 运行；
- 可播放 MP4 和导出 Manifest；
- 失败/恢复、重启恢复和无授权费用阻断证据。

## 11. Open Product Decisions

以下决定不阻塞无副作用的早期里程碑，但在真实媒体里程碑开始前必须由 Product Owner 明确：

- `PD-001`：MVP 真实 Visual Provider、可用模型和凭据来源；历史术语 “Omni” 不构成可执行供应商选择。
- `PD-002`：MVP TTS Provider、声音和凭据来源。
- `PD-003`：一次完整 Demo 的费用上限与自动重试预算。

本 PRD 获批不等于批准任何 Provider 调用或费用。
