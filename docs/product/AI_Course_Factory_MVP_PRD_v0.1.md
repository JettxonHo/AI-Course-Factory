# AI Course Factory MVP PRD v0.1

## Document Status

| 字段 | 内容 |
| --- | --- |
| Document | AI Course Factory MVP Product Requirements Document |
| Version | v0.1 |
| Phase | Phase 1.1 — PRD Formalization |
| Status | Review Draft |
| Owner | JettxonHo |
| Last Updated | 2026-08-09 |
| Next Phase | Phase 1.2 — Technical Spec（仅在本 PRD 获批后进入） |

## 0. 文档目的与边界

本文档正式定义 AI Course Factory MVP 的用户、问题、产品目标、范围、用户流程、功能需求、非功能需求和验收标准。

本文档回答：

- 为什么做？
- 为谁做？
- MVP 要解决什么问题？
- MVP 必须交付什么？
- 怎样判断 MVP 已完成？

本文档不定义：

- 代码仓库结构
- API 与数据 Schema
- LangGraph 节点和状态实现
- Agent、Skill、Renderer 的代码接口
- 开发任务、里程碑与 PR 顺序

这些内容分别属于 Phase 1.2 Technical Spec 和 Phase 1.3 Implementation Spec。

### 0.1 Baseline Inputs

本 PRD 受以下已确认文档约束：

1. [AI Product Studio Strategy V3](../strategy/AI_Product_Studio_Strategy_V3.md)
2. [Phase 0.5 Step 1 Decision Record v1.0](../../Phase_0.5_Step_1_Decision_Record_v1.0.md)
3. [Phase 0.5 Step 2 Decision Record v1.0](../../Phase_0.5_Step_2_Decision_Record_v1.0.md)

若本文档与上层战略或 Decision Record 冲突，应先显式修订对应决策，不在实现阶段静默改变产品方向。

## 1. Product Overview

AI Course Factory 是一个面向 AI 内容创作者的知识到教育内容生产应用。它把结构化或半结构化的知识源转化为可审核、可追踪、可继续生产的教学内容资产，并最终生成教育短视频。

MVP 使用 GitHub Repository 作为唯一知识源，以 Microsoft AI-For-Beginners 为首个 Demo 输入，验证以下端到端闭环：

```text
GitHub Repository
    ↓
Knowledge Understanding
    ↓
Course / Episode Planning
    ↓
Script
    ↓
Storyboard
    ↓
Timeline
    ↓
Stickman Video
```

AI Course Factory 不是：

- 通用 AI 视频生成器
- 完整在线课程平台
- 自动发布平台
- 多用户 SaaS
- ContentOS 平台本身

它是 AI Knowledge-to-Content Factory 的第一个垂直应用，也是未来抽象 ContentOS 能力的真实验证场景。

## 2. Product Vision

帮助 AI Creator 将现有知识资产快速转化为结构化、可审核、可复用的教育内容资产，减少从“理解资料”到“形成可发布内容”之间的重复劳动。

长期愿景不是只生成一条视频，而是建立：

```text
Knowledge Source → Structured Content Assets → Multi-format Content
```

的可扩展生产能力。

## 3. Problem Statement

### P-01：知识理解成本高

创作者需要手动浏览仓库结构、README、课程章节和其他材料，才能提炼适合受众的主题与关键信息。

### P-02：教学内容生产链路割裂

课程规划、脚本、分镜、配音、字幕和视频渲染通常由不同工具完成，信息需要反复复制，容易产生版本和上下文不一致。

### P-03：中间成果不可追踪、不可复用

许多生成流程只保留最终视频，无法追溯视频依据、复用脚本或分镜，也难以从中间步骤恢复。

### P-04：修改成本高

局部内容出现问题时，传统一键生成流程常常需要整体重做，缺少审核检查点和局部重生成能力。

### P-05：难以规模化形成稳定内容能力

一次性的提示词和手工步骤无法沉淀为可重复执行、可测试、可替换的内容生产流程。

## 4. Target User

### 4.1 Primary User：AI Creator

典型特征：

- 需要持续输出 AI 或技术教育内容
- 能阅读 GitHub 项目或技术资料，但不希望手动完成全部内容整理和媒体制作
- 重视内容准确性、可控性和个人风格
- 能对脚本及最终视频做人工判断和修改
- 首期允许使用文件或开发者工具形态完成流程，不要求完整 SaaS 体验

### 4.2 Core Job to Be Done

当我找到一个值得传播的 AI 知识源时，我希望系统帮助我把它转化为可审核的短视频生产资产和最终视频，使我不必从零完成研究、脚本、分镜和视频制作，同时仍保留内容决策权。

### 4.3 非目标用户

MVP 不为以下用户优化：

- 需要多人协作和权限管理的企业团队
- 完全不参与内容审核的一键发布用户
- 需要专业非线性视频编辑器的影视制作人员
- 需要同时管理多个品牌、租户或发布渠道的运营团队

## 5. MVP Objective

MVP 的唯一主目标是证明：

> 系统能够把一个明确的 GitHub 知识源转化为结构化、可审核、可追踪的教育内容资产，并产出一条可观看的 60–90 秒火柴人教育短视频。

### 5.1 需要验证的产品假设

| ID | 假设 |
| --- | --- |
| H-01 | GitHub 仓库中的课程知识可以被提炼成适合短视频的教学主题与要点。 |
| H-02 | Script → Storyboard → Timeline 的中间资产能提高生产过程的可控性和可修改性。 |
| H-03 | 在脚本与最终视频阶段保留人工审核，能够避免错误内容直接进入下一阶段或发布。 |
| H-04 | Stickman 风格能以较低生产风险形成具有辨识度的 MVP 演示。 |
| H-05 | 保留中间资产、检查点与局部执行能力，比只交付最终视频更有长期产品价值。 |

### 5.2 MVP Demo

| 字段 | 决策 |
| --- | --- |
| Source | Microsoft AI-For-Beginners GitHub Repository |
| Demo Episode | Episode 01：AI 到底是什么？一个小土豆的 AI 启蒙之旅 |
| Target Duration | 60–90 秒 |
| Primary Output | Stickman 教育短视频 |
| Required Intermediate Outputs | Knowledge、Course/Episode Plan、Script、Storyboard、Timeline、Audio、Subtitle、Video |
| Human Checkpoints | Script Approval、Final Video Approval |

## 6. MVP Scope

### 6.1 P0 — 必须交付

#### Knowledge Intake

- 接收一个公开 GitHub Repository 作为输入
- 读取并识别与 Demo 主题相关的知识结构和内容
- 形成可保存、可追溯的 Knowledge Artifact

#### Content Planning

- 根据目标受众和时长生成课程或单集主题规划
- 为 Demo 选定一个明确的教学目标和核心信息
- 形成可保存的 Course / Episode Plan

#### Script Production

- 生成适合 60–90 秒教育短视频的脚本
- 脚本包含旁白、关键信息和段落或场景划分
- 在进入媒体生产前要求用户明确批准脚本

#### Storyboard and Timeline

- 将已批准脚本转化为 Storyboard
- Storyboard 至少表达 Scene、Shot、Character、Asset、Duration、Narration 和 Camera 意图
- 将 Storyboard 转化为可供渲染执行的 Timeline
- Timeline 至少覆盖视觉、旁白、字幕和时间关系

#### Media Production

- 生成或接入旁白音频
- 生成字幕
- 使用 Stickman 风格完成视频渲染
- 保持核心角色和主要视觉风格在同一视频内一致

#### Review and Export

- 对最终视频执行质量检查并输出问题清单或通过结果
- 最终视频必须经过人工批准
- 导出最终视频及全部中间资产

#### Artifact and Recovery

- 每个阶段的产物独立保存并可追溯到其上游输入
- 流程中断后可以从最近有效检查点继续
- 已有有效上游产物时，不要求从知识提取阶段全部重跑
- 支持以 Scene 为最小业务定位单位重新生成受影响内容

### 6.2 P1 — MVP 验证后再评估

- 第二个 GitHub 项目 Demo
- 更多教学模板或视觉风格
- 更细粒度的 Storyboard 人工审核
- 更丰富的质量评价与运营指标
- Blog 或 Social Content 等多格式输出

P1 不属于 MVP 完成条件。

### 6.3 Out of Scope / Non-goals

- PDF、Web、YouTube、Notion、Local Files 等多知识源
- 私有 GitHub Repository 的完整鉴权产品化
- 多用户、用户账号、Workspace、权限与多租户
- SaaS 控制台和云端商业部署
- Agent、Skill 或 Template Marketplace
- 完整 ContentOS 抽象
- 多 Renderer 管理系统
- Remotion、Manim 或 AI Video Renderer 的正式接入
- 自研 TTS、图像或视频基础模型
- 自动发布到社交媒体或视频平台
- 专业时间线编辑器
- 24 集完整课程批量生产

## 7. End-to-End User Flow

```text
1. Creator 提交 GitHub Repository
    ↓
2. 系统读取并生成 Knowledge Artifact
    ↓
3. 系统生成 Course / Episode Plan
    ↓
4. 系统生成 Script Artifact
    ↓
5. Creator 审核脚本
    ├── Reject / Revise → 修改脚本后再次审核
    └── Approve
          ↓
6. 系统生成 Storyboard Artifact
    ↓
7. 系统生成 Timeline、Audio 与 Subtitle Artifacts
    ↓
8. 系统生成 Stickman Video Artifact
    ↓
9. 系统执行质量检查
    ↓
10. Creator 审核最终视频
    ├── Reject / Revise → 定位问题并局部重新生成
    └── Approve → 导出
```

## 8. Functional Requirements

### 8.1 Knowledge Source and Understanding

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-001 | 系统必须允许用户提交一个 GitHub Repository 作为任务输入。 | P0 |
| FR-002 | 系统必须验证输入是否可访问；不可访问时给出明确错误且不得继续生成。 | P0 |
| FR-003 | 系统必须提取与课程内容相关的仓库结构、主题和关键知识。 | P0 |
| FR-004 | 系统必须生成并保存 Knowledge Artifact，并保留来源标识。 | P0 |

### 8.2 Content Planning and Script

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-005 | 系统必须基于 Knowledge Artifact 生成 Course / Episode Plan。 | P0 |
| FR-006 | 单集规划必须包含目标受众、教学目标、核心信息和目标时长。 | P0 |
| FR-007 | 系统必须从已选单集规划生成 Script Artifact。 | P0 |
| FR-008 | 脚本必须适配 60–90 秒目标时长，并包含可映射到场景的结构。 | P0 |
| FR-009 | 系统必须支持用户批准、拒绝或要求修改脚本。 | P0 |
| FR-010 | 脚本未获批准时，系统不得开始后续媒体生产。 | P0 |

### 8.3 Storyboard and Timeline

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-011 | 系统必须从已批准脚本生成 Storyboard Artifact。 | P0 |
| FR-012 | Storyboard 必须使用稳定的 Scene / Shot 标识，以支持定位和局部修改。 | P0 |
| FR-013 | 系统必须从 Storyboard 生成独立 Timeline Artifact。 | P0 |
| FR-014 | Timeline 必须表达视频中视觉、旁白、字幕及时间关系。 | P0 |

### 8.4 Media Production

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-015 | 系统必须为已批准内容生成或接入旁白音频。 | P0 |
| FR-016 | 系统必须生成与旁白内容和时间关系对应的字幕。 | P0 |
| FR-017 | 系统必须使用 Stickman 风格生成可播放的视频。 | P0 |
| FR-018 | 系统必须在单个视频内维持核心角色和视觉风格的一致性。 | P0 |

### 8.5 Review, Revision, and Export

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-019 | 系统必须对最终视频执行内容、教学表达和媒体质量检查。 | P0 |
| FR-020 | 质量检查结果必须指出是否通过，并在失败时标识问题类型、位置和原因。 | P0 |
| FR-021 | 系统必须支持用户批准、拒绝或要求修改最终视频。 | P0 |
| FR-022 | 最终视频未获批准时不得标记为完成。 | P0 |
| FR-023 | 系统必须允许针对指定 Scene 重新执行受影响的下游步骤。 | P0 |
| FR-024 | 系统必须导出最终视频和全部必需中间资产。 | P0 |

### 8.6 Artifact and Workflow Control

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-025 | 每个产物必须具有唯一标识、版本、状态、创建来源和上游依赖信息。 | P0 |
| FR-026 | 用户必须能够识别当前执行阶段及各必需产物的状态。 | P0 |
| FR-027 | 流程必须在脚本批准和最终视频批准处保存检查点。 | P0 |
| FR-028 | 流程中断后必须能够从最近有效产物或检查点继续。 | P0 |
| FR-029 | 上游产物未发生变化时，用户必须能够只执行选定的下游阶段。 | P0 |
| FR-030 | 任一步骤失败时，系统必须保留此前已成功生成的有效产物。 | P0 |

## 9. Required Deliverables

一次成功的 MVP 运行至少产生：

| Deliverable | 用户价值 | 完成条件 |
| --- | --- | --- |
| Source Record | 知道内容来自哪里 | 可定位输入仓库和本次运行 |
| Knowledge Artifact | 查看系统提炼出的知识依据 | 有主题、要点和来源关联 |
| Course / Episode Plan | 确认本集教什么 | 有受众、目标、核心信息、时长 |
| Script Artifact | 审核教学表达 | 有版本和批准状态 |
| Storyboard Artifact | 查看视觉叙事方案 | 每个 Scene / Shot 可定位 |
| Timeline Artifact | 形成可执行生产计划 | 视觉、旁白、字幕与时间关系完整 |
| Audio Artifact | 提供旁白 | 可播放并关联脚本版本 |
| Subtitle Artifact | 提供字幕 | 内容与时间关系可用 |
| Video Artifact | 交付最终内容 | 可播放、60–90 秒、Stickman 风格 |
| Review Result | 说明是否达到交付条件 | 有通过状态或可定位问题清单 |
| Run Manifest | 保留完整追踪关系 | 能追溯本次运行的全部产物版本 |

## 10. Non-functional Requirements

| ID | Requirement |
| --- | --- |
| NFR-001 — Recoverability | 执行中断不得导致已成功生成的有效产物丢失；恢复后无需默认全量重跑。 |
| NFR-002 — Traceability | 最终视频必须可追溯到 Timeline、Storyboard、Script、Knowledge 和 Source。 |
| NFR-003 — Controllability | 用户可以在明确审核点阻止流程继续，并能定位需要修改的 Scene。 |
| NFR-004 — Replaceability | 产品需求不得依赖某个不可替换的模型或供应商；具体适配方案在 Technical Spec 定义。 |
| NFR-005 — Observability | 用户能够看到当前阶段、成功/失败状态、错误原因和产物位置。 |
| NFR-006 — Data Integrity | 失败或重试不得静默覆盖已批准产物；新结果必须形成可识别版本。 |
| NFR-007 — Consistency | 同一视频中的核心角色命名、视觉身份和关键知识表达必须保持一致。 |
| NFR-008 — Failure Isolation | 单个下游步骤失败不应使此前有效的上游产物失效。 |
| NFR-009 — Source Attribution | Knowledge Artifact 必须保留源仓库信息，最终内容应能识别其知识来源。 |
| NFR-010 — Testability | 所有 P0 Requirement 都必须能够通过自动检查、产物检查或明确人工验收进行验证。 |

## 11. MVP Acceptance Criteria

### AC-01：完整闭环

**Given** Microsoft AI-For-Beginners GitHub Repository 可访问，  
**When** 用户创建 Demo 任务并完成两个必要批准，  
**Then** 系统生成 Knowledge、Course / Episode Plan、Script、Storyboard、Timeline、Audio、Subtitle、Video、Review Result 和 Run Manifest，且最终视频可播放。

### AC-02：Demo 内容与时长

最终视频围绕“AI 到底是什么？一个小土豆的 AI 启蒙之旅”形成一个可理解的单集教学表达，目标时长为 60–90 秒，使用 Stickman 视觉风格。

### AC-03：脚本审核门禁

脚本处于未批准或已拒绝状态时，系统不生成正式 Storyboard、Timeline 或 Video；脚本批准后才可继续。

### AC-04：最终审核门禁

最终视频未获人工批准时，任务不得标记为完成或发布就绪。

### AC-05：可追溯性

从最终 Video Artifact 可以定位其 Timeline、Storyboard、Script、Knowledge Artifact 和源仓库；每个必需产物均有版本和状态。

### AC-06：中断恢复

在 Script 批准后中断流程，再次启动时可以复用已批准 Script，从后续有效阶段继续，而不是重新执行全部前置步骤。

### AC-07：局部重新生成

当 Reviewer 或用户指出某个 Scene 存在问题时，系统可以保留未受影响的已批准上游资产，并重新生成该 Scene 及受影响的下游结果。

### AC-08：失败保留

当 TTS、字幕或渲染步骤失败时，Knowledge、Plan、Script、Storyboard 等此前成功产物仍然存在，且用户能够看到失败步骤和原因。

### AC-09：导出完整性

一次已批准运行可导出最终视频、全部必需中间资产和追踪清单；缺少任何 P0 交付物时不得判定 MVP 完成。

### AC-10：范围约束

MVP 不以用户系统、SaaS 控制台、多知识源、多 Renderer、自动发布或完整 ContentOS 为完成条件。

## 12. Success Criteria

### 12.1 MVP Release Gate

只有同时满足以下条件，Phase 1 MVP 才可判定为端到端闭环完成：

1. AC-01 至 AC-10 全部通过。
2. 所有 P0 Functional Requirements 有对应验证证据。
3. Demo 视频通过最终人工审核。
4. 全部必需中间资产已保存并可追溯。
5. 至少完成一次中断恢复验证和一次 Scene 级局部重新生成验证。

### 12.2 本阶段不采用的虚假成功指标

以下结果不能单独证明 MVP 成功：

- 只生成一个 MP4 文件
- 只展示 Agent 对话
- 只生成脚本但未进入生产链路
- 只完成架构或代码骨架
- 依靠手工补齐缺失的核心产物却宣称自动闭环完成

## 13. Assumptions, Dependencies, and Risks

### 13.1 Assumptions

- MVP Demo 使用公开可访问的 Microsoft AI-For-Beginners Repository。
- 首期为单用户、单任务主流程，不要求并发和团队协作能力。
- 用户愿意在脚本和最终视频阶段进行人工审核。
- 首期目标是验证产品闭环，不承诺商业级 SLA。

### 13.2 Dependencies

- 可用的 GitHub 内容访问能力
- 可用的 LLM 能力
- 可用的 TTS 与必要的图像生成能力
- 可适配的 Stickman Renderer 或现有 `stickman-video-director` 资产
- trekking-potato 或等效角色视觉资产的可用版本

具体供应商、模型、库和部署方式由 Technical Spec 决定。

### 13.3 Key Risks

| ID | Risk | Product Mitigation |
| --- | --- | --- |
| R-01 | 源仓库内容过多，短视频主题失焦 | 单集规划必须明确教学目标、核心信息和时长。 |
| R-02 | 内容提炼不准确 | 保留来源追踪，并在最终质量检查中评价知识准确性。 |
| R-03 | 视频风格不一致 | 使用角色与资产记录，要求单视频内核心视觉身份一致。 |
| R-04 | 媒体生成失败拖垮全流程 | 保存中间产物，允许从失败阶段重试。 |
| R-05 | 过早平台化导致 MVP 延期 | 严格执行 Non-goals，禁止把 ContentOS 平台能力加入 P0。 |
| R-06 | 过度追求自动化削弱内容控制 | 保留 Script 和 Final Video 两个人工门禁。 |
| R-07 | 具体供应商形成锁定 | 产品需求以能力和产物定义，不把单一模型作为产品契约。 |

## 14. Open Product Decisions for Approval

以下问题不阻止 v0.1 进入评审，但必须在 PRD 批准或 Technical Spec 开始前明确：

| ID | Decision | v0.1 Working Assumption |
| --- | --- | --- |
| OQ-01 | Demo 输出语言 | 简体中文 |
| OQ-02 | 核心角色/IP | 使用“小土豆”/trekking-potato 作为 Demo 主角 |
| OQ-03 | 首期用户操作形态 | 允许本地或开发者工作流，不要求完整 Web UI |
| OQ-04 | 最终视频发布规格 | PRD 只要求可播放和可导出；分辨率、画幅、编码在 Technical Spec 决定 |
| OQ-05 | Knowledge Accuracy 的人工验收责任 | MVP 由 Creator 在最终审核中承担发布前确认责任 |

## 15. Requirements Traceability

| Upstream Decision | PRD 落点 |
| --- | --- |
| Application First | MVP 只验证 AI Course Factory，不建设完整 ContentOS。 |
| Knowledge First | FR-003 至 FR-008 将知识理解和内容规划置于视频生产之前。 |
| Artifact First | FR-025 至 FR-030、NFR-001 至 NFR-003、AC-05 至 AC-09。 |
| Workflow + Specialized Agent | 作为 Phase 1.2 的架构约束；PRD 只定义用户可见流程与门禁。 |
| Human Review 必须保留 | FR-009、FR-010、FR-021、FR-022、AC-03、AC-04。 |
| Programmatic + Template + AI Asset | P0 Media Production 与 Stickman Demo 范围。 |
| Storyboard 作为中间表示 | FR-011、FR-012 和 Required Deliverables。 |
| Timeline 作为 Renderer 输入 | FR-013、FR-014 和 Required Deliverables。 |
| Artifact Graph | FR-025、NFR-002、AC-05。 |
| Partial Execution | FR-023、FR-028、FR-029、AC-06、AC-07。 |
| Lightweight Asset Registry | FR-018、NFR-007；实现形式留给 Technical Spec。 |
| Stickman Renderer 为 MVP Renderer | FR-017、AC-02。 |
| MCP Ready, not MCP First | 不作为用户功能；留作 Technical Spec 的接口兼容约束。 |
| Build / Buy / Borrow | 作为 Technical Spec 的选型约束，不写成用户功能。 |

## 16. Phase 1.1 Exit Criteria

进入 Phase 1.2 Technical Spec 前必须满足：

1. Product Owner 已评审本文档。
2. OQ-01 至 OQ-05 已确认或被明确延期并记录责任人。
3. P0、P1 和 Non-goals 已获确认。
4. MVP Acceptance Criteria 已获确认。
5. 文档状态由 `Review Draft` 更新为 `Approved Baseline`。

在这些条件满足前，不开始 Repository Architecture、API、State Schema、Agent Contract 或 Skill Contract 的正式设计。

## 17. Approval Record

| Role | Name | Decision | Date | Notes |
| --- | --- | --- | --- | --- |
| Product Owner | JettxonHo | Pending | — | — |

