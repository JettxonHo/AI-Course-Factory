# AI Course Factory MVP PRD v0.3

## 1. Document Status

| 字段 | 内容 |
| --- | --- |
| Document | AI Course Factory MVP Product Requirements Document |
| Version | v0.3 |
| Phase | Phase 1.1 — PRD Formalization |
| Status | Approved Baseline |
| Owner | JettxonHo |
| Last Updated | 2026-08-09 |
| Intended Baseline | 进入 Phase 1.2 Technical Spec 前的产品基线 |
| Next Phase | Phase 1.2 — Technical Spec（仅在本 PRD 获批后进入） |

### 1.1 文档目的

本文档定义 AI Course Factory MVP 的产品契约、用户流程、功能边界、生产架构责任、Artifact 原则、审核规则、失败恢复和验收标准。

本文档回答“产品必须做什么”和“怎样判断 MVP 完成”，但不定义：

- 代码仓库结构
- API、类、函数或数据 Schema
- LangGraph 节点和状态实现
- 具体模型参数、供应商 SDK 或基础设施选型
- 开发任务、里程碑与提交顺序

上述内容分别属于 Phase 1.2 Technical Spec 和 Phase 1.3 Implementation Spec。

### 1.2 Baseline Inputs 与决策连续性

本 PRD 受以下已确认基线约束：

1. [AI Product Studio Strategy V3](../strategy/AI_Product_Studio_Strategy_V3.md)
2. [Phase 0.5 Step 1 Decision Record v1.0](../../Phase_0.5_Step_1_Decision_Record_v1.0.md)
3. [Phase 0.5 Step 2 Decision Record v1.0](../../Phase_0.5_Step_2_Decision_Record_v1.0.md)
4. [Renderer Strategy Revision Addendum v1.0](../architecture/Renderer_Strategy_Revision_Addendum_v1.0.md)
5. [AI Course Factory MVP PRD v0.2 — Archived Review Baseline](AI_Course_Factory_MVP_PRD_v0.2.md)

Renderer Strategy Revision Addendum 对旧文档中的以下 MVP 实现选择具有优先级：

- MVP 生产路线由确定性 Stickman Renderer 修订为 Prompt + Omni Hybrid Production。
- `stickman-video-director` 定位为 Director / Prompt Skill，而不是 Renderer。
- Timeline、Artifact First、Production Layer 可替换和未来确定性 Renderer 演进原则继续有效。

本 PRD 不删除或改写历史决策。自批准之日起，本 PRD 取代 PRD v0.2 成为当前产品基线；若与未被 Addendum 修订的上层决策冲突，应先修订对应 Decision Record，不得在实现阶段静默改变方向。

> 归档说明：PRD v0.2 与 Renderer Strategy Revision Addendum 已完成实体归档并建立交叉链接。v0.3 的归档退出条件已满足。

## 2. Product Overview

AI Course Factory 是面向 AI Creator 的知识到教育内容生产应用。它将可追溯的知识源转化为结构化、可审核、可恢复的内容与媒体资产，并最终生成可交付的教育短视频发布包。

MVP 使用一个公开 GitHub Repository 作为知识源，以 Microsoft AI-For-Beginners 为 Demo 输入，验证以下闭环：

```text
Knowledge Source
    ↓
Knowledge Understanding
    ↓
Content Planning
    ↓
Production Pipeline
    ↓
Video Output
```

首个内容系列为“小土豆学 AI”，首集为 Episode 01《AI不是魔法》。MVP 的核心价值不是单独生成一个视频文件，而是证明知识依据、内容决策、中间 Artifact、媒体生产和人工审核可以形成一条可追溯的完整链路。

AI Course Factory 不是通用 AI 视频生成器、完整课程平台、自动发布平台、多用户 SaaS 或 ContentOS 本身。它是 AI Knowledge-to-Content Factory 的第一个垂直应用和能力验证场景。

## 3. Product Contract

### 3.1 Primary User

Primary User 为 AI Creator，典型特征包括：

- 持续生产 AI 或技术教育内容
- 能阅读 GitHub 项目和技术资料，但不希望手工完成全部研究与媒体制作
- 重视内容准确性、可控性、品牌角色和过程可追溯性
- 愿意对脚本与最终视频承担人工决策责任

### 3.2 Input Contract

MVP 接收：

- 一个公开可访问的 GitHub Repository URL
- 一个单集生产任务
- 已确认的受众、语言、Episode Template 与角色规范

Demo 知识处理范围为：

1. 先理解 Microsoft AI-For-Beginners 的仓库索引与课程结构。
2. 再聚焦 Lesson 1 形成 Episode 01 的 Knowledge Artifact。

私有仓库鉴权、多知识源融合和批量课程生产不属于 MVP。

### 3.3 Knowledge Grounding Contract

MVP 采用 source-closed 规则：所有教学事实必须来自可追溯的 Knowledge Artifact。

LLM 允许：

- 总结
- 改写
- 翻译
- 压缩
- 重组
- 教学化表达

LLM 禁止：

- 添加无法定位到 Knowledge Artifact 的事实性主张
- 使用模型记忆补齐来源中不存在的教学事实
- 在来源不足时把推测表达为事实

每一项进入脚本和最终视频的教学主张必须能追溯到源仓库中的文件、章节或等效来源定位。无法追溯的主张属于 Hard Block。

### 3.4 Episode Output Contract

| 字段 | MVP 决策 |
| --- | --- |
| Series | 小土豆学 AI |
| Episode | Episode 01《AI不是魔法》 |
| Audience | 成年 AI 初学者 |
| Language | 简体中文 |
| Learning Goal | AI 不是魔法：有些任务无法靠写死步骤解决，但可以让计算机从例子中学习。 |
| Episode Template | Fixed 6 Scene Template |
| Target Duration | 约 60 秒，每个 Scene 约 10 秒 |
| Aspect Ratio | 9:16 |
| Visual Style | 浅色教育风 |
| Character | 小土豆 v1.0 |
| Production Route | Prompt + Omni Hybrid Production |

Fixed 6 Scene 是 MVP Episode Template Constraint，不是 Workflow Schema 限制。Timeline 和 Production Request 必须能够表达有序场景集合；MVP 仅实例化六个 Scene，未来可在不推翻核心协议的前提下支持 Dynamic Scene Expansion。

### 3.5 Character Contract

小土豆 v1.0 的稳定视觉身份为：

- 不规则土豆轮廓头
- 两只黑点眼睛
- 简单嘴巴
- 极简线条身体与黑色线条四肢
- 固定身份标记：无文字的 AI 蓝小帽

角色一致性属于 Reviewer 的质量检查项；主观视觉波动默认记为 Warning，除非导致角色不可识别或违反必需格式。

### 3.6 Review and Completion Contract

MVP 使用 Critical Checkpoint 模型：

- Script Review：必选门禁。
- Storyboard / Director Proposal Review：MVP 默认可选；一旦用户启用，批准前不得调用 Omni 进行正式生成。
- Final Video Review：必选门禁。

Knowledge、Course / Episode Plan、Timeline 等 Artifact 必须可见和可追溯，但不增加额外强制人工门禁。

一次任务只有在最终 Video 通过人工批准并生成完整 Publish Package 后，才可标记为完成。

## 4. User Flow

```text
1. Creator 提交公开 GitHub Repository
    ↓
2. 系统验证来源并生成 Source Record
    ↓
3. Knowledge Agent 理解仓库结构并聚焦 Lesson 1
    ↓
4. 生成 Knowledge Artifact 与 Course / Episode Plan
    ↓
5. Content Agent 生成 Script Artifact
    ↓
6. Creator 执行 Mandatory Script Review
    ├── Reject / Revise → 形成新 Script Version → 再次审核
    └── Approve
          ↓
7. Production Agent 生成 Character 与 Storyboard Artifacts
    ↓
8. Optional Storyboard Review
    ├── 未启用 → 继续
    ├── Reject / Revise → 形成新版本 → 再次审核
    └── Approve
          ↓
9. Production Agent 生成 provider-neutral Timeline Artifact
    ↓
10. 系统从 Timeline 生成 provider-neutral Production Request Artifact
    ↓
11. 系统生成 Production Budget Artifact，并请求预算批准
    ├── Reject / Limit Exceeded → 暂停
    └── Approve
          ↓
12. Workflow 将 Production Request 交给 Production Orchestrator
    ├── Voice Skill → Scene Audio Artifacts
    ├── Audio Composer → Master Audio Artifact
    ├── Visual Generator Skill / Provider Adapter → Omni-specific Prompt / Request → Scene Clip Artifacts
    └── Media Composer → Video Artifact + Subtitle Artifact
          ↓
13. Reviewer 生成 Review Artifact
    ├── Hard Block → 修订或恢复后重新检查
    └── Warning / Pass → Creator 执行 Mandatory Final Video Review
          ├── Reject / Revise → Scene-level Revision / Continue From Here
          └── Approve
                ↓
14. Content Packaging 生成 Cover、Metadata 与 Artifact Manifest
    ↓
15. 导出 Publish Package
```

在任何会使已存在下游产物失效的修改或 `Continue From Here` 操作前，系统必须先展示 Artifact Impact Preview。

## 5. Functional Requirements

### 5.1 Knowledge Source and Understanding

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-001 | 系统必须允许 Creator 提交一个公开 GitHub Repository URL 作为单次任务输入。 | MVP Required |
| FR-002 | 系统必须验证仓库是否可访问；验证失败时给出明确错误且不得继续生成。 | MVP Required |
| FR-003 | 系统必须先识别仓库索引与课程结构，再聚焦 Lesson 1 提取 Episode 01 所需知识。 | MVP Required |
| FR-004 | 系统必须生成 Knowledge Artifact，并为教学要点保留可定位的来源引用。 | MVP Required |
| FR-005 | 系统必须阻止任何无法追溯到 Knowledge Artifact 的事实性教学主张进入已批准脚本或最终交付物。 | MVP Required |

### 5.2 Content Planning and Episode Template

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-006 | 系统必须基于 Knowledge Artifact 生成面向成年 AI 初学者的 Course / Episode Plan。 | MVP Required |
| FR-007 | 系统必须围绕 Episode 01 学习目标生成简体中文 Script Artifact。 | MVP Required |
| FR-008 | MVP 必须使用 Fixed 6 Scene Template，目标总时长约 60 秒，每个 Scene 约 10 秒。 | MVP Required |
| FR-009 | 系统必须支持 Creator 直接编辑、批准、拒绝或要求修改 Script Artifact。 | MVP Required |
| FR-010 | Script 未获批准时，系统不得进入正式 Storyboard 与媒体生产阶段。 | MVP Required |
| FR-011 | 系统必须从已批准脚本生成符合小土豆 v1.0 角色规范的 Character 与 Storyboard Artifacts。 | MVP Required |
| FR-012 | 系统必须支持可选的 Storyboard / Director Proposal Review；启用后必须批准才能进入 Omni 生成。 | MVP Required |
| FR-013 | 系统必须生成 provider-neutral Timeline Artifact；其场景集合不得在协议层被固定为六个。 | MVP Required |

### 5.3 Production Request and Orchestration

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-014 | 系统必须从 Timeline Artifact 生成独立、版本化、provider-neutral 的 Production Request Artifact。 | MVP Required |
| FR-015 | Production Request 必须描述场景、时长、视觉意图、角色约束、旁白与字幕引用、输出规格及其依赖，但不得包含仅对 Omni 有效的核心业务字段。 | MVP Required |
| FR-016 | Provider Adapter 必须把 Production Request 转换为 Omni-specific Prompt / Request；Prompt 属于供应商调用表示，不是系统核心 Artifact。 | MVP Required |
| FR-017 | 顶层 Workflow 必须只向 Production Orchestrator 提交已授权的 Production Request，不得直接调度 Omni、Voice Skill、Audio Composer 或 Media Composer。 | MVP Required |
| FR-018 | Production Orchestrator 必须协调视觉生成、语音生成、音频合成、媒体合成、重试、失败归一化和生产产物生成。 | MVP Required |
| FR-019 | MVP 的视觉生产必须采用 Prompt + Omni Hybrid Production，输出 9:16、浅色教育风、符合小土豆 v1.0 身份约束的 Scene Clip Artifacts。 | MVP Required |
| FR-020 | 系统必须保留供应商调用的必要追踪信息，使 Scene Clip 能定位到 Production Request Version 和具体生成尝试；供应商 Prompt 可作为执行记录保存，但不进入核心 Artifact 契约。 | MVP Required |

### 5.4 Audio, Subtitle, and Composition

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-021 | Voice Skill 必须将每个 Scene 的旁白文本转换为独立的 Scene Audio Artifact。 | MVP Required |
| FR-022 | Audio Composer 必须将 Scene Audio 按 Timeline 合成，并可接收可选 BGM 与 Effect，输出 Master Audio Artifact。 | MVP Required |
| FR-023 | BGM 或 Effect 缺失不得阻止 MVP 完成；清晰、完整且时序正确的旁白 Master Audio 为必需结果。 | MVP Required |
| FR-024 | 系统必须生成与已批准脚本和 Timeline 对应的 Subtitle Artifact。 | MVP Required |
| FR-025 | Media Composer 必须将 Scene Clip、Master Audio 与 Subtitle 合成为可播放的 Video Artifact。 | MVP Required |

### 5.5 Budget, Review, Versioning, and Recovery

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-026 | 正式调用 Omni 前，系统必须生成 Production Budget Artifact，至少包含场景数、预计生成秒数、价格快照、基础估算、最大重试预算和批准状态。 | MVP Required |
| FR-027 | 未获预算批准、预计超限或重试将突破已批准预算时，Workflow 必须暂停，不得继续产生供应商费用。 | MVP Required |
| FR-028 | Reviewer 必须生成 Review Artifact，并把问题划分为 Hard Block 或 Warning。 | MVP Required |
| FR-029 | 缺少必需 Artifact、存在无来源教学主张或输出格式错误必须标记为 Hard Block。 | MVP Required |
| FR-030 | 角色一致性、节奏和其他主观质量问题默认标记为 Warning；Creator 可以接受 Warning 或发起修改。 | MVP Required |
| FR-031 | 每个核心 Artifact 必须具有稳定标识、版本、状态、创建来源和上游版本依赖。 | MVP Required |
| FR-032 | 上游修改必须创建新版本，不得覆盖旧的已批准版本；受影响的现有下游版本必须标记为 `stale`。 | MVP Required |
| FR-033 | 在执行会影响下游产物的修改、Regenerate 或 Continue From Here 前，系统必须展示基本 Artifact Impact Preview。 | MVP Required |
| FR-034 | 系统必须支持从最近有效 Artifact 继续执行，并支持以 Scene 为最小业务定位单位重新生成受影响的下游结果。 | MVP Required |
| FR-035 | 生产失败必须归类为 Provider Error、Generation Failure、Quality Failure 或 Budget Limit，并生成 Failure Artifact。 | MVP Required |
| FR-036 | 对可重试失败，MVP 默认允许首次调用后最多两次自动重试；超过尝试或预算限制后必须暂停并展示可用恢复路径。 | MVP Required |
| FR-037 | 失败、重试或人工替换不得删除此前有效 Artifact，也不得静默覆盖已批准结果。 | MVP Required |

### 5.6 Workspace and Packaging

| ID | Requirement | Priority |
| --- | --- | --- |
| FR-038 | MVP 必须提供轻量本地 Artifact-centric Single Task Workspace，显示输入、流程状态、Knowledge、Script、Storyboard、Timeline、Video 与相关审核操作。 | MVP Required |
| FR-039 | Workspace 必须支持 Script 编辑、Artifact 查看、Approve、Reject、Regenerate、Continue From Here、Impact Preview 和 Export。 | MVP Required |
| FR-040 | Final Video 未获人工批准时，任务不得进入 Content Packaging。 | MVP Required |
| FR-041 | Final Video 获批后，系统必须生成由 Media Package、Metadata Package 和 Artifact Manifest 组成的 Publish Package。 | MVP Required |
| FR-042 | MVP 只负责生成和导出 Publish Package，不得自动发布到外部平台。 | MVP Required |

## 6. Agent Responsibilities

MVP 继续采用 Workflow + Specialized Agent，不采用单一超级 Agent，也不采用大量 Agent 自由协作。

| Component | Responsibilities | Explicitly Does Not Own |
| --- | --- | --- |
| Knowledge Agent | 理解仓库结构；聚焦 Lesson 1；提取教学要点；建立来源引用；生成 Knowledge Artifact 候选内容。 | 不决定视频视觉生产方式；不添加源外事实。 |
| Content Agent | 生成 Course / Episode Plan 与 Script；把来源知识转化为适合成年初学者的简体中文教学表达。 | 不调用媒体供应商；不绕过 Script Review。 |
| Production Agent | 基于已批准脚本进行角色、分镜和执行规划；生成 Character、Storyboard、Timeline 与 Production Request 候选内容。 | 不直接调用 Omni、TTS 或 Composer；不拥有重试和供应商错误处理。 |
| Reviewer | 检查来源一致性、Artifact 完整性、格式、角色一致性、节奏与主观质量；生成 Hard Block / Warning。 | 不是最终发布判断者；不得替代 Creator 的强制批准。 |

Production Orchestrator 不是新的 Agent。它是生产域内的执行协调组件，责任见第 8 节。

## 7. Skill Layer

Skill 是可复用、可测试、可替换的执行能力。Skill 执行明确任务并返回标准结果，不拥有跨阶段 Workflow、人工门禁或最终产品决策。

### 7.1 Knowledge and Creative Skills

- GitHub Connector：读取公开仓库与必要文件，返回带来源定位的内容。
- Knowledge Extraction Skill：提取仓库结构、课程索引和 Lesson 1 知识。
- Storyboard Skill：把已批准脚本转化为场景化叙事方案。
- Character Skill：应用小土豆 v1.0 视觉身份约束。
- Teaching Visualization Skill：将教学概念转化为可执行的视觉意图。
- Director / Prompt Skill：可辅助形成 Director Proposal 或供应商提示策略；`stickman-video-director` 属于此层，不是 Renderer。

### 7.2 Production Skills

- `Visual Generator Skill`：接收标准视觉生成任务并返回 Scene Clip 或标准化失败结果；MVP 由 Omni Provider Adapter 实现。
- `Voice Skill`：执行 `text → Scene Audio Artifact`，使用外部统一 TTS 路线，不依赖 Omni 生成主旁白。
- `Subtitle Skill`：根据脚本、音频与 Timeline 形成 Subtitle Artifact。
- `Audio Composer`：执行 `Scene Audio + optional BGM + optional Effect → Master Audio Artifact`。
- `Media Composer`：执行 `Scene Clips + Master Audio + Subtitle → Video Artifact`。

### 7.3 Infrastructure Capabilities

- Artifact Storage：持久化 Artifact 版本、状态和依赖。
- Lightweight Asset Registry：管理角色、视觉与媒体资产引用。
- Provider Adapter：把内部 Production Request 映射为外部供应商请求，并把供应商结果归一化。
- Packaging Capability：在最终批准后组装 Publish Package。

`Production Request Artifact` 是系统内部、供应商无关的生产协议。Omni Prompt 是 Provider Adapter 生成的供应商调用表示。两者不得合并为同一个核心 Artifact。

## 8. Production Architecture

### 8.1 Canonical Name

生产域执行协调组件正式命名为 **Production Orchestrator**。

不采用 `ProductionPipelineFacade`，因为其职责不只是隐藏接口，还包括多能力调度、重试、失败分类、预算约束执行和生产产物生成。不采用泛化的 `Production Service` 作为产品架构术语，因为它不能清晰表达协调职责。

`Production Orchestrator` 是生产域内的子编排器，不取代顶层 Workflow。

### 8.2 Workflow 与 Production Layer 边界

| Boundary | Owns | Does Not Own |
| --- | --- | --- |
| Top-level Workflow | 端到端阶段流转；Human Review；预算授权；跨阶段状态；Continue From Here；何时进入或退出生产域。 | 不直接构造 Omni Prompt；不直接调用单个媒体 Skill；不处理供应商原始响应。 |
| Production Agent | 创意与生产规划；Character、Storyboard、Timeline、Production Request 候选内容。 | 不执行供应商调用；不决定重试；不管理人工门禁。 |
| Production Orchestrator | 执行一个已授权的 Production Request；调度 Visual Generator、Voice、Audio Composer、Subtitle、Media Composer；执行固定重试与失败归一化；产出生产 Artifact 或 Failure Artifact。 | 不改变教学事实；不批准预算；不决定 Script 或 Final Video 是否通过；不拥有完整端到端 Workflow。 |
| Provider Adapter | 把 provider-neutral 请求转换为 Omni-specific Prompt / API Request；调用供应商；标准化返回、错误和调用记录。 | 不改变上游业务意图；不管理 Artifact Graph；不决定人工恢复。 |
| Artifact Layer | 保存版本、依赖、状态、`stale`、Review、Failure 与追踪关系。 | 不进行内容推理或供应商调用。 |

### 8.3 Internal Protocol vs Provider Request

```text
Timeline Artifact
    ↓
Production Request Artifact
    │  provider-neutral internal protocol
    ↓
Production Orchestrator
    ↓
Omni Provider Adapter
    ↓
Omni-specific Prompt / Request
    │  provider-specific execution representation
    ↓
Scene Clip Result / Normalized Failure
```

核心系统依赖 Production Request，不依赖 Omni Prompt。更换视觉供应商时，应替换 Provider Adapter，而不要求改写 Timeline、Production Request 或顶层 Workflow 的产品语义。

### 8.4 Production Branches

```text
Production Request Artifact
    ├── Narration Branch
    │     Voice Skill
    │         ↓
    │     Scene Audio Artifacts
    │         ↓
    │     Audio Composer + optional BGM / Effect
    │         ↓
    │     Master Audio Artifact
    │
    ├── Visual Branch
    │     Omni Provider Adapter
    │         ↓
    │     Omni Prompt / Request
    │         ↓
    │     Scene Clip Artifacts
    │
    └── Timing / Text Branch
          Subtitle Artifact

Scene Clips + Master Audio + Subtitle
    ↓
Media Composer
    ↓
Video Artifact
```

Omni 负责视觉片段、动画和可选环境声，不负责主旁白。主旁白始终来自统一 Voice Skill，以保证声音策略可替换、可重生和可独立合成。

## 9. Artifact Model

### 9.1 Artifact Categories

| Category | Artifacts | Purpose |
| --- | --- | --- |
| Source and Knowledge | Source Record、Knowledge Artifact | 保存输入与事实依据。 |
| Content | Course / Episode Plan、Script Artifact | 保存教学目标、结构与表达。 |
| Creative Planning | Character Artifact、Storyboard Artifact | 保存角色规范与视觉叙事。 |
| Execution Planning | Timeline Artifact、Production Request Artifact、Production Budget Artifact | 保存供应商无关的执行意图、授权范围与成本边界。 |
| Production Media | Scene Audio、Master Audio、Subtitle、Scene Clip、Video | 保存可独立复用和组合的媒体产物。 |
| Control and Quality | Review Artifact、Failure Artifact | 保存质量判断、失败分类与恢复状态。 |
| Packaging | Cover Artifact、Metadata Package、Artifact Manifest、Publish Package | 保存最终交付结构。 |

Omni Prompt / Request 属于 Provider Execution Record，可用于审计和复现，但不是核心业务 Artifact，也不得成为 Timeline 的替代品。

### 9.2 Minimum Artifact Contract

每个核心 Artifact 至少具有：

- `id`
- `version`
- `type`
- `status`
- `created_by`
- `dependencies`，且指向上游的确切版本
- `source_refs`（适用于知识与教学内容）
- `created_at`

具体字段类型和 Schema 由 Technical Spec 定义。

### 9.3 Versioned Artifact Graph

MVP 遵循以下产品规则：

1. 已批准 Artifact 不得被静默覆盖。
2. 修改上游 Artifact 必须创建新版本。
3. 旧下游版本保留，但在依赖不再匹配时标记为 `stale`。
4. 新执行必须明确选择所依赖的上游版本。
5. `Continue From Here` 复用未受影响且仍有效的上游 Artifact。
6. Artifact Impact Preview 必须在操作前列出将被标记为 `stale` 或需要重新生成的下游结果。

MVP 可以用固定 Artifact 关系和简化状态传播实现这些规则；不要求构建通用图数据库或完整 Artifact 平台。

### 9.4 Scene Model Boundary

Scene 是局部审核和重新生成的最小业务定位单位。MVP 模板生成六个 Scene，但 Artifact Graph、Timeline 和 Production Request 的模型必须以有序集合表达 Scene，不能把“恰好六个”编码为不可扩展的 Workflow 状态形状。

## 10. Review System

### 10.1 Review Levels

| Level | Meaning | Workflow Effect | Final Authority |
| --- | --- | --- | --- |
| Hard Block | 确定性不合格，当前产物不可继续。 | 阻止进入下一阶段或完成状态。 | 修复并重新检查后才能继续。 |
| Warning | 存在主观或可接受的质量风险。 | 不自动阻止；必须向 Creator 可见。 | Creator 可接受或要求修改。 |

### 10.2 Hard Block Rules

至少包括：

- 缺少当前阶段必需 Artifact
- 教学主张无法追溯到 Knowledge Artifact
- 必需输出格式错误或无法读取
- 依赖版本不匹配却被当作有效结果使用
- 必选人工门禁未通过

### 10.3 Warning Rules

至少包括：

- 小土豆角色视觉一致性不足但仍可识别
- 场景节奏偏快或偏慢
- 视觉表达、镜头或主观教学质量可改善
- BGM、Effect 或环境声表现不理想

### 10.4 Checkpoints

- Script Review：Mandatory。
- Storyboard / Director Proposal Review：Optional by default；启用后为 Mandatory Gate。
- Final Video Review：Mandatory。

Reviewer 是质量门禁，不是最终裁判。Creator 对 Warning 和最终视频拥有最终决定权，但不得绕过 Hard Block。

Review Artifact 至少记录检查对象及版本、问题级别、类型、Scene 定位、原因、建议动作、检查结果和人工决定。

## 11. Failure Recovery

### 11.1 Failure Classification

| Failure Type | Typical Examples | Default Handling | Allowed Recovery Paths |
| --- | --- | --- | --- |
| Provider Error | timeout、网络错误、限流、供应商服务错误 | 若预算允许，执行受限自动重试；记录每次尝试。 | 自动重试；人工重试；暂停后恢复；上传替代 Scene Clip。 |
| Generation Failure | 模型拒绝、空结果、不可解析结果、无可用媒体输出 | 可在不改变教学事实和 Production Request 语义的前提下重建 provider-specific 请求并重试。 | 场景级重试；修订供应商表达；人工上传 Scene Clip；返回上游修订。 |
| Quality Failure | 角色不一致、视觉与场景意图偏离、节奏或主观质量不达标 | 形成 Review Warning；若同时违反必需格式或角色不可识别，则升级为 Hard Block。 | Creator 接受 Warning；提交 Scene-level Revision Request；重新生成指定 Scene；上传替代 Scene Clip。 |
| Budget Limit | 未批准预算、预计超限、自动重试将突破上限 | 立即暂停，不自动重试，不继续产生费用。 | 提高或重新批准预算；减少重试范围；缩小重新生成范围；上传替代 Scene Clip。 |

### 11.2 Retry Policy

- 对标记为 retryable 的 Provider Error 或 Generation Failure，默认执行首次调用加最多两次自动重试，即最多三次尝试。
- 每次尝试前必须检查剩余预算。
- Quality Failure 不触发无限自动重试；由 Creator 决定是否接受或发起定向修改。
- Budget Limit 不得自动恢复，必须获得新的人工授权或使用不产生该供应商费用的替代路径。
- 重试只生成新尝试记录或新 Artifact Version，不得覆盖此前有效结果。

### 11.3 Failure Artifact

Failure Artifact 至少记录：

- failure category
- stage 与 `scene_id`
- provider 与 attempt number（如适用）
- normalized error code / reason
- retryable 状态
- 已消耗和剩余预算信息
- 受影响的输出
- 可选恢复路径
- 当前恢复状态

MVP 必须实现上述四类失败的基础识别和恢复；跨供应商自动故障转移、智能策略引擎和复杂恢复编排属于 Architecture Foundation，不是 MVP 完成条件。

## 12. Publish Package

### 12.1 Production Output 与 Content Packaging 边界

Production Pipeline 的完成结果是通过技术合成与质量检查的媒体 Artifact，核心为 Video Artifact，并关联 Scene Clips、Scene Audio、Master Audio 和 Subtitle。

Content Packaging 仅在 Final Video 获人工批准后执行。它不重新生成教学内容或视频，而是把已批准生产结果、发布元数据和追踪信息组织为可交付结构。

### 12.2 Package Structure

```text
Publish Package
├── Media Package
│   ├── Approved Final Video
│   ├── Cover Artifact
│   ├── Subtitle
│   ├── Master Audio
│   └── Scene Audio Segments
├── Metadata Package
│   ├── Title
│   ├── Description
│   ├── Tags
│   └── Source Attribution
└── Artifact Manifest
    ├── Artifact IDs and Versions
    ├── Dependency Trace
    ├── Approval Status
    ├── Source References
    └── Provider Execution References
```

Cover Artifact 必须从已批准 Video Artifact 中选择关键帧，并套用品牌模板生成；MVP 不引入独立 AI 封面图生成模型。

Publish Package 是单次任务的内容交付物，不代表已经发布到任何平台。多平台规格适配、渠道模板和自动发布均不属于 MVP。

## 13. MVP Scope

### 13.1 MVP Required Features

以下能力必须实现并通过第 15 节验收：

1. 公开 GitHub Connector 与输入验证。
2. 仓库结构理解、Lesson 1 聚焦、Knowledge Artifact 与来源追踪。
3. Course / Episode Plan、简体中文 Script 生成与 Mandatory Script Review。
4. Fixed 6 Scene Episode Template、小土豆 v1.0、Storyboard 与 Timeline。
5. Provider-neutral Production Request 与 Omni Provider Adapter。
6. Prompt + Omni Hybrid Visual Generation。
7. Voice Skill、Scene Audio、Audio Composer、Master Audio、Subtitle 与 Media Composition。
8. 生产预算估算、Budget Artifact 和强制预算批准。
9. Hard Block + Warning Review 与 Mandatory Final Video Review。
10. 核心 Artifact 的版本、依赖、`stale`、基本 Impact Preview 和 Continue From Here。
11. 四类 Failure、受限重试、暂停、Scene-level Revision 和人工 Scene Clip 替换路径。
12. 轻量本地 Artifact-centric Single Task Workspace。
13. 分层 Publish Package 与本地导出。

### 13.2 Architecture Foundation

以下项目必须在 Technical Spec 中保留清晰扩展边界，但 MVP 可采用简化实现，且不作为完整平台能力交付：

| Foundation | MVP Simplification | Future Direction |
| --- | --- | --- |
| Artifact Graph | 固定核心 Artifact 关系、版本依赖和基本 `stale` 传播。 | 通用 DAG、复杂查询、跨任务复用和完整可视化。 |
| Failure Recovery | 固定四类 Failure、最多三次尝试、人工恢复路径。 | 策略引擎、自动根因判断、跨供应商故障转移。 |
| Scene Model | Schema 使用可变有序集合，但产品模板固定六个 Scene。 | Dynamic Scene Expansion 与多 Episode Template。 |
| Production Provider Boundary | 只接入 Omni，但通过 Production Request 与 Adapter 隔离。 | 多 Visual Provider、确定性 Stickman Renderer、Remotion Renderer。 |
| Artifact Impact Preview | 操作前列出直接与传递受影响的核心 Artifact。 | 交互式依赖图、复杂变更模拟和批量修复。 |
| Budget Control | 单次任务估算、价格快照、批准上限和重试检查。 | 多供应商报价、动态路由、账户级预算和成本分析。 |
| Publish Package | 一个固定通用结构，本地导出。 | 多渠道 Packaging Profile 与自动分发。 |

Architecture Foundation 的含义是“现在定义稳定边界并避免封死未来”，不是“现在实现完整平台”。

## 14. Non Goals

MVP 明确不包含：

- SaaS 账号、用户体系、Workspace、权限和多租户
- 私有 GitHub Repository 的完整鉴权产品化
- PDF、Web、YouTube、Notion、Local Files 等多知识源
- 多知识源融合与 RAG 平台
- Dynamic Scene Expansion 的用户功能
- 多 Renderer / 多 Visual Provider 管理系统
- 确定性 Stickman Renderer、Remotion Renderer 或 Manim Renderer 的正式接入
- 供应商自动故障转移和智能成本路由
- 自研 LLM、TTS、图像或视频基础模型
- Voice Clone 和高级声音市场
- 专业时间线编辑器或非线性视频编辑器
- 多人协作、任务列表和批量课程生产
- 多平台专属 Packaging Profile
- 自动发布到社交媒体或视频平台
- Agent、Skill、Template Marketplace
- 完整 ContentOS 抽象或独立 Skill 平台

## 15. Acceptance Criteria

### AC-01：End-to-End Closure

**Given** Microsoft AI-For-Beginners 公开仓库可访问，  
**When** Creator 创建 Episode 01 任务并完成所有强制批准，  
**Then** 系统生成从 Source Record 到 Publish Package 的必需 Artifact，最终视频可播放，完整发布包可导出。

### AC-02：Knowledge Grounding

系统先记录仓库课程结构，再从 Lesson 1 形成 Knowledge Artifact；已批准脚本与视频中的每项事实性教学主张均可定位到 Knowledge Artifact 和源文件。任一无来源主张会产生 Hard Block。

### AC-03：Episode and Character Contract

最终视频为简体中文、9:16、浅色教育风，使用 Fixed 6 Scene Template，总时长约 60 秒，并保持小土豆 v1.0 的可识别身份和 Episode 01《AI不是魔法》的学习目标。

### AC-04：Human Review Gates

Script 未获批准时不得进入正式生产；Storyboard Review 启用后，未获批准时不得调用 Omni；Final Video 未获批准时不得进入 Content Packaging 或完成状态。

### AC-05：Production Boundary

Timeline 先形成 provider-neutral Production Request Artifact，再由 Omni Provider Adapter 生成 provider-specific Prompt / Request。顶层 Workflow 不直接调度 Omni、Voice Skill、Audio Composer 或 Media Composer。

### AC-06：Audio Architecture

每个 Scene 具有可播放的 Scene Audio Artifact；Audio Composer 能按 Timeline 生成完整 Master Audio；BGM 或 Effect 缺失不阻止完成；主旁白不依赖 Omni 音频。

### AC-07：Media Composition

Production Orchestrator 能协调 Scene Clip、Master Audio、Subtitle 与 Media Composer 生成可播放 Video Artifact，并保留各生产产物的版本依赖。

### AC-08：Review Classification

Reviewer 能把缺少 Artifact、无来源主张和格式错误标记为 Hard Block，把角色一致性、节奏和主观质量问题标记为 Warning；Creator 可接受 Warning，但不能绕过 Hard Block。

### AC-09：Versioning and Partial Regeneration

修改一个已批准 Script 或指定 Scene 时，系统创建新版本，保留旧版本，展示 Artifact Impact Preview，将受影响的旧下游标记为 `stale`，并只重新执行受影响的下游步骤。

### AC-10：Failure Recovery

至少分别验证一次 Provider Error、Generation Failure、Quality Failure 和 Budget Limit：系统生成 Failure Artifact，保留此前有效产物，遵守对应重试规则，并向 Creator 提供该类型允许的恢复路径。

### AC-11：Budget Gate

Omni 首次调用前存在已批准的 Production Budget Artifact；任何会突破批准上限的调用或重试均被暂停，且未产生未经授权的供应商费用。

### AC-12：Publish Package Layering

Final Video 获批后，系统导出包含 Media Package、Metadata Package 和 Artifact Manifest 的 Publish Package；Cover 来自批准视频关键帧与品牌模板；系统不执行外部平台自动发布。

### AC-13：Replaceability and Template Boundary

在不改动 Timeline 和 Production Request 产品语义的前提下，可以在 Technical Spec 中定义另一个 Visual Provider Adapter；Scene 在协议中为有序集合，而非固定六字段结构。MVP 不要求实际接入第二个 Provider 或动态场景 UI。

### AC-14：Scope Control

MVP 不以多知识源、多用户、动态场景、多 Renderer、供应商自动切换、专业编辑器、自动发布或完整 ContentOS 为完成条件。

### 15.1 Phase 1.1 Exit Gate

| Exit Condition | Status |
| --- | --- |
| Product Owner 完成 v0.3 评审。 | Complete |
| PRD v0.2 已补齐实体归档。 | Complete |
| Renderer Strategy Revision Addendum 已补齐实体归档。 | Complete |
| v0.3 Baseline Inputs 已建立交叉链接。 | Complete |
| `Production Orchestrator`、`Production Request Artifact`、`Audio Composer`、四类 Failure 和 Publish Package 分层被确认为标准术语。 | Complete |
| MVP Required Features、Architecture Foundation、Non Goals 与 AC-01 至 AC-14 获得确认。 | Complete |
| 文档状态更新为 `Approved Baseline`。 | Complete |

Phase 1.1 退出条件已经满足。本次归档不自动启动 Phase 1.2；Technical Spec 仅在 Product Owner 发出下一阶段明确指令后开始。

### 15.2 Approval Record

| Role | Name | Decision | Date | Notes |
| --- | --- | --- | --- | --- |
| Product Owner | JettxonHo | Approved with archive conditions — conditions satisfied | 2026-08-09 | PRD v0.2、Renderer Addendum 与 v0.3 交叉链接已归档完成。 |
