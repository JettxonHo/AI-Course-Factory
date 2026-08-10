# AI Course Factory MVP PRD v0.2

## 1. Document Status

| 字段 | 内容 |
| --- | --- |
| Document | AI Course Factory MVP Product Requirements Document |
| Version | v0.2 |
| Phase | Phase 1.1 — PRD Formalization |
| Status | Superseded by [PRD v0.3](AI_Course_Factory_MVP_PRD_v0.3.md) |
| Archive Type | Historical Review Baseline |
| Owner | JettxonHo |
| Baseline Date | 2026-08-09 |
| Archive Date | 2026-08-09 |

### 1.1 Archival Provenance

本文件补齐 AI Course Factory MVP PRD v0.2 的实体归档。它依据 v0.2 评审时已经确认的产品讨论、Renderer Strategy Revision Addendum 及 v0.3 Revision Pass 中明确列出的“当前状态”整理，目的是保存 v0.3 修订前的产品基线，而不是重新批准一份旧需求。

本文件是历史文档。所有当前需求、标准术语、范围分层和验收条件以 [AI Course Factory MVP PRD v0.3](AI_Course_Factory_MVP_PRD_v0.3.md) 为准。

### 1.2 Baseline Inputs

1. [AI Product Studio Strategy V3](../strategy/AI_Product_Studio_Strategy_V3.md)
2. [Phase 0.5 Step 1 Decision Record v1.0](../../Phase_0.5_Step_1_Decision_Record_v1.0.md)
3. [Phase 0.5 Step 2 Decision Record v1.0](../../Phase_0.5_Step_2_Decision_Record_v1.0.md)
4. [Renderer Strategy Revision Addendum v1.0](../architecture/Renderer_Strategy_Revision_Addendum_v1.0.md)

## 2. Product Overview

AI Course Factory 是面向 AI Creator 的知识到教育内容生产应用。MVP 使用公开 GitHub Repository 作为知识源，把知识理解、内容规划、脚本、分镜、媒体生产和最终审核连接成可追溯闭环。

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

MVP Demo 使用 Microsoft AI-For-Beginners，内容系列为“小土豆学 AI”，Episode 01 为《AI不是魔法》。

## 3. Product Contract

### 3.1 User and Source

- Primary User：AI Creator。
- MVP Source：一个公开 GitHub Repository。
- Demo Scope：先理解仓库课程结构，再聚焦 Lesson 1。
- Output Language：简体中文。
- Target Audience：成年 AI 初学者。

### 3.2 Knowledge Boundary

所有教学事实只允许来自可追溯 Knowledge Artifact。LLM 可以总结、改写、翻译、压缩、重组和进行教学化表达，但不得添加无法定位到 Knowledge Artifact 的事实性主张。

### 3.3 Episode and Character

| 字段 | v0.2 决策 |
| --- | --- |
| Episode | Episode 01《AI不是魔法》 |
| Learning Goal | AI 不是魔法：有些任务无法靠写死步骤解决，但可以让计算机从例子中学习。 |
| Scene Count | Fixed 6 Scenes |
| Duration | 约 60 秒 |
| Aspect Ratio | 9:16 |
| Style | 浅色教育风 |
| Character | 小土豆 v1.0 |
| Production Route | Prompt + Omni Hybrid Production |

小土豆 v1.0 包含不规则土豆轮廓头、两只黑点眼睛、简单嘴巴、极简线条身体、黑色线条四肢和无文字 AI 蓝小帽。

### 3.4 Human Review

- Script Review：Mandatory。
- Storyboard / Director Proposal Review：Optional by default；启用后必须批准才能进入 Omni 正式生成。
- Final Video Review：Mandatory。

## 4. User Flow

```text
Creator submits public GitHub repository
    ↓
Knowledge Artifact
    ↓
Course / Episode Plan
    ↓
Script Artifact
    ↓
Mandatory Script Review
    ↓
Character + Storyboard Artifacts
    ↓
Optional Storyboard Review
    ↓
Scene Audio Artifacts
    ↓
Master Audio
    ↓
Timeline Artifact
    ↓
Production Budget Artifact
    ↓
Mandatory Budget Approval
    ↓
Prompt Package
    ↓
ProductionPipelineFacade
    ↓
Scene Clip Artifacts
    ↓
Composition
    ↓
Video Artifact
    ↓
Review Artifact
    ↓
Mandatory Final Review
    ↓
Cover + Publish Package
```

## 5. Functional Requirements

### 5.1 Knowledge and Content

| ID | Requirement |
| --- | --- |
| FR-001 | 接收并验证一个公开 GitHub Repository。 |
| FR-002 | 读取仓库索引与课程结构，并聚焦 Lesson 1。 |
| FR-003 | 生成保留来源定位的 Knowledge Artifact。 |
| FR-004 | 基于 Knowledge Artifact 生成 Course / Episode Plan。 |
| FR-005 | 生成围绕 Episode 01 学习目标的简体中文 Script Artifact。 |
| FR-006 | 阻止无来源教学主张进入批准结果。 |
| FR-007 | 支持 Script 编辑、拒绝、修改和批准。 |
| FR-008 | Script 未批准时不得进入正式媒体生产。 |

### 5.2 Storyboard, Timeline, and Production

| ID | Requirement |
| --- | --- |
| FR-009 | 从批准脚本生成 Character 与 Storyboard Artifacts。 |
| FR-010 | Storyboard 必须使用稳定 Scene 标识，并应用小土豆 v1.0。 |
| FR-011 | 生成包含视觉、旁白、字幕和时间关系的 Timeline Artifact。 |
| FR-012 | 使用 Fixed 6 Scene 结构形成约 60 秒视频。 |
| FR-013 | 从 Timeline 生成用于媒体供应商调用的 Prompt Package。 |
| FR-014 | 通过 `ProductionPipelineFacade` 调度 Visual Generator、Voice Skill 和 Composer。 |
| FR-015 | 使用 Omni 生成 9:16 浅色教育风的 Scene Clip。 |
| FR-016 | Voice Skill 为每个 Scene 生成独立 Scene Audio。 |
| FR-017 | 将 Scene Audio 形成 Master Audio。 |
| FR-018 | 生成与 Timeline 对应的 Subtitle Artifact。 |
| FR-019 | 将 Scene Clip、Master Audio 和 Subtitle 合成为 Video Artifact。 |

### 5.3 Review, Artifact, and Recovery

| ID | Requirement |
| --- | --- |
| FR-020 | 生成 Production Budget Artifact，并在 Omni 调用前请求批准。 |
| FR-021 | Reviewer 将确定性问题标记为 Hard Block，将主观质量问题标记为 Warning。 |
| FR-022 | Final Video 必须经过 Creator 批准。 |
| FR-023 | 核心 Artifact 保留 ID、Version、Status 和 Dependencies。 |
| FR-024 | 上游修改创建新版本，旧下游保留并标记 `stale`。 |
| FR-025 | 变更前显示 Artifact Impact Preview。 |
| FR-026 | 支持 Continue From Here 与 Scene-level Regeneration。 |
| FR-027 | Omni 失败时执行受限重试；失败后生成 Failure Artifact。 |
| FR-028 | 预算超限或异常重试时暂停 Workflow。 |
| FR-029 | 失败不得删除此前有效 Artifact。 |

### 5.4 Workspace and Export

| ID | Requirement |
| --- | --- |
| FR-030 | 提供轻量本地 Artifact-centric Single Task Workspace。 |
| FR-031 | 展示 Knowledge、Script、Storyboard、Timeline、Video 与 Workflow 状态。 |
| FR-032 | 提供 Approve、Reject、Regenerate、Continue From Here 和 Export。 |
| FR-033 | Final Video 批准后生成包含 Video、Audio、Subtitle、Title、Description、Cover、Tags 和 Artifact Manifest 的 Publish Package。 |
| FR-034 | MVP 不自动发布到外部平台。 |

## 6. Agent Responsibilities

| Component | Responsibility |
| --- | --- |
| Knowledge Agent | 理解仓库、提取知识并建立来源关联。 |
| Content Agent | 生成 Course / Episode Plan 与 Script。 |
| Production Agent | 生成 Character、Storyboard、Timeline，并协调媒体生产意图。 |
| Reviewer | 检查来源、格式、角色一致性、节奏和主观质量。 |

MVP 采用 Workflow + Specialized Agent，不采用超级 Agent 或大量 Agent 自由协作。

## 7. Skill Layer

### 7.1 Knowledge and Creative Skills

- GitHub Connector
- Knowledge Extraction
- Storyboard Skill
- Character Skill
- Teaching Visualization Skill
- Director / Prompt Skill

### 7.2 Production Skills

- Visual Generator Skill，MVP 使用 Gemini Omni Flash 路线
- Voice Skill，使用外部统一 TTS
- Subtitle Skill
- Composer

### 7.3 Infrastructure Skills

- Artifact Storage
- Lightweight Asset Registry
- Provider Adapter
- Packaging

`stickman-video-director` 在 v0.2 中已修订为 Director / Prompt Skill，不承担最终 Renderer 职责。

## 8. Production Architecture

v0.2 使用 `ProductionPipelineFacade` 表达 Workflow 与媒体生产能力之间的统一入口：

```text
Timeline Artifact
    ↓
Prompt Package
    ↓
ProductionPipelineFacade
    ├── Visual Generator Skill / Omni
    ├── Voice Skill
    └── Composer
          ↓
Video Artifact
```

Facade 负责隐藏 Visual Generator、Voice 和 Composer 的具体调用，使顶层 Workflow 不直接依赖媒体供应商。

Provider-specific Prompt 被组织为 Prompt Package 并保留生成记录。Production Layer 必须保持可替换，以便未来接入确定性 Stickman Renderer、Remotion 或其他视觉供应商。

## 9. Artifact Model

### 9.1 Core Artifacts

- Source Record
- Knowledge Artifact
- Course / Episode Plan
- Script Artifact
- Character Artifact
- Storyboard Artifact
- Scene Audio Artifacts
- Master Audio
- Timeline Artifact
- Production Budget Artifact
- Prompt Package
- Scene Clip Artifacts
- Subtitle Artifact
- Video Artifact
- Review Artifact
- Failure Artifact
- Cover Artifact
- Publish Package

### 9.2 Versioning Rules

- 核心 Artifact 具有 ID、Version、Status 和 Dependencies。
- 上游修改创建新版本，不覆盖旧的已批准版本。
- 受影响的旧下游版本标记为 `stale`。
- `Continue From Here` 复用仍然有效的上游产物。
- 重新生成前展示 Artifact Impact Preview。

## 10. Review System

### 10.1 Hard Block

- 缺少必需 Artifact
- 教学主张无法追溯到 Knowledge Artifact
- 必需格式错误
- 强制人工门禁未通过

### 10.2 Warning

- 小土豆视觉一致性不足
- 节奏问题
- 视觉、镜头或其他主观质量问题

Reviewer 生成 Review Artifact，但 Creator 对 Warning 和最终视频拥有最终决定权。Hard Block 未解决前不得继续。

## 11. Failure Recovery

MVP 对 Omni Scene 生成失败采用：

```text
Provider Call
    ↓ failure
Automatic Retry
    ↓ failure
Automatic Retry
    ↓ failure or budget limit
Failure Artifact + Workflow Pause
```

默认最多三次尝试。重试或预算超限后，Creator 可以人工重试、修改指定 Scene 或上传替代 Scene Clip，再从该位置继续。

Failure Artifact 记录失败阶段、Scene、尝试次数、错误原因、预算状态和恢复选项。失败不得删除此前有效 Artifact。

## 12. Publish Package

Final Video 获批后，系统生成单一 Publish Package，包含：

- Final Video
- Subtitle
- Scene Audio
- Master Audio
- Title
- Description
- Cover
- Tags
- Artifact Manifest

Cover 从已批准 Video Artifact 选择关键帧并应用品牌模板，不引入独立 AI 图片生成模型。MVP 只导出，不自动发布。

## 13. MVP Scope

v0.2 将以下能力统一纳入 MVP 产品范围：

- GitHub Connector
- Knowledge Artifact 与来源追踪
- Course / Episode Plan 与 Script
- Fixed 6 Scene Storyboard 与 Timeline
- Mandatory Script Review 与 Final Video Review
- Optional Storyboard Review
- Prompt + Omni Hybrid Production
- Scene Audio、Master Audio、Subtitle 与 Video Composition
- Production Budget Artifact 与 Budget Gate
- Artifact Versioning、`stale`、Impact Preview 和 Partial Regeneration
- Failure Artifact、受限重试与人工 Scene Clip 替换
- Cover 与 Publish Package
- Artifact-centric Single Task Workspace

## 14. Non Goals

- SaaS 账号、多用户、Workspace、权限与多租户
- 私有 GitHub 完整鉴权
- PDF、Web、YouTube、Notion 和 Local Files 等多知识源
- Dynamic Scene Expansion
- 多 Renderer 管理系统
- 确定性 Stickman Renderer 或 Remotion 的 MVP 接入
- 自研视频、图像或语音基础模型
- 专业时间线编辑器
- 自动发布
- 完整 ContentOS
- Marketplace

## 15. Acceptance Criteria

1. Microsoft AI-For-Beginners 能形成 Knowledge、Plan、Script、Storyboard、Timeline、Audio、Subtitle、Video 与 Publish Package。
2. 教学事实能追溯到 Lesson 1 的 Knowledge Artifact；无来源主张被 Hard Block。
3. 视频为简体中文、9:16、浅色教育风、Fixed 6 Scene、约 60 秒，并使用小土豆 v1.0。
4. Script 和 Final Video 未批准时，Workflow 不能越过相应门禁。
5. Omni 生成前存在已批准 Budget Artifact。
6. Scene Audio 能形成 Master Audio，并与 Scene Clip、Subtitle 合成 Video。
7. Reviewer 能区分 Hard Block 与 Warning。
8. 上游修改形成新版本，受影响下游标记 `stale`，并支持 Scene-level Regeneration。
9. Omni 失败后保留有效 Artifact，执行受限重试并提供人工恢复路径。
10. Final Video 批准后生成完整 Publish Package，且不执行自动发布。

## 16. Revision Findings Leading to v0.3

v0.3 Revision Pass 识别并解决了以下 v0.2 边界问题：

| Revision | v0.2 State | v0.3 Resolution |
| --- | --- | --- |
| Production naming | `ProductionPipelineFacade` 未完整表达协调职责。 | 采用 `Production Orchestrator`，并与顶层 Workflow 分权。 |
| Prompt boundary | Prompt Package 位于核心 Artifact 链。 | 引入 provider-neutral Production Request Artifact；Prompt 下沉至 Provider Adapter。 |
| Audio architecture | Voice Skill 后直接形成 Master Audio，Composer 责任不清。 | 增加 Audio Composer，区分 Scene Audio 与 Master Audio。 |
| Scene constraint | Fixed 6 Scene 的产品约束与 Schema 边界未充分区分。 | 明确为 Episode Template Constraint，协议支持可变有序场景。 |
| Publish structure | Publish Package 为扁平清单。 | 分为 Media Package、Metadata Package 与 Artifact Manifest。 |
| Failure model | 只有通用 Retry 与 Failure Artifact。 | 建立 Provider、Generation、Quality、Budget 四类 Failure 与恢复矩阵。 |
| Scope | 高级架构能力与 MVP 必需交付混在同一范围。 | 分离 MVP Required Features 与 Architecture Foundation。 |

## 17. Archive Record

| Role | Name | Decision | Date | Notes |
| --- | --- | --- | --- | --- |
| Product Owner | JettxonHo | Archived and Superseded | 2026-08-09 | v0.2 实体归档作为 v0.3 决策历史；不再是当前实施基线。 |
