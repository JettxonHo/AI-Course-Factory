# AI Product Studio Strategy V3

## Document Status

| 字段 | 内容 |
| --- | --- |
| Document | AI Product Studio Strategy |
| Version | V3.0 |
| Status | Strategic Baseline |
| Purpose | 指导 AI 产品生态建设 |
| Owner | JettxonHo |

## 1. Vision（长期愿景）

打造一个围绕 **Agent Workflow + Knowledge Transformation + Content Automation** 的 AI 产品生态。

核心定位：

- 英文：AI Product Builder focused on Agentic Workflow and Content Automation
- 中文：专注于 Agent 工作流与 AI 内容自动化方向的 AI 产品构建者

## 2. 核心战略原则

### 2.1 Application First

不优先构建完整平台，采用以下演进方式：

```text
真实应用验证
    ↓
能力沉淀
    ↓
平台抽象
```

即：Application First → Capability Extraction → Platformization。

### 2.2 Knowledge First

未来 AI 产品的核心不是单纯生成内容，而是将知识资产转换为可传播内容。

```text
Knowledge Source
    ↓
Knowledge Understanding
    ↓
Content Planning
    ↓
Production Pipeline
    ↓
Distribution
```

### 2.3 Build + Buy + Borrow

避免重复造轮子，优先：

1. 复用成熟方案
2. 二次开发优秀开源项目
3. 自研核心差异化能力

### 2.4 Artifact First

所有 AI 工作流必须支持：

- checkpoint
- artifact persistence
- partial execution

系统不应只是 Input → Output，而应是 Input → Artifact → Artifact → Artifact → Output。

## 3. 产品生态总架构

```text
AI Product Studio
        ↓
AI Knowledge-to-Content
        ↓
┌──────────────────────────────┐
│ AI Course Factory            │
│ 教育内容生产                  │
├──────────────────────────────┤
│ AI Ecommerce Agent           │
│ 商业内容生产                  │
└──────────────────────────────┘
        ↓
ContentOS Core
        ↓
Shared AI Infrastructure
```

## 4. 产品演进路线

### Phase 0：战略与调研阶段

目标：建立方向和技术判断。

产出：

- Strategy Document
- Decision Record
- Architecture Principle

状态：完成。

### Phase 1：AI Course Factory MVP

AI Course Factory 是第一个真实应用验证，不是单纯的 AI 视频工具，而是 AI Knowledge-to-Content Factory 的第一个垂直应用。

MVP 输入：GitHub Repository。

未来输入扩展：

- PDF
- Web
- YouTube
- Notion
- Local Document
- Knowledge Base

教育内容资产输出包括：

- Script
- Storyboard
- Timeline
- Video
- Blog
- Social Content

MVP Demo 选择 Microsoft AI-For-Beginners，原因是内容结构清晰、风险低，适合验证端到端流程。

### Phase 2：Knowledge Source 扩展

目标：验证从 GitHub 扩展到任意知识源的平台化能力，包括 AI 项目、技术文档、论文和产品文档。

### Phase 3：ContentOS 抽象

从 AI Course Factory 中提取 Core Infrastructure：

- Agent Runtime：Agent 执行、状态管理、Workflow
- Knowledge Layer：Source Connector、Knowledge Extraction、RAG、Memory
- Workflow Engine：状态流转、Checkpoint、Human Review
- Skill Layer：内容生产能力、外部工具调用

### Phase 4：多应用生态

```text
ContentOS
├── AI Course Factory
├── AI Ecommerce Agent
├── Marketing Agent
└── Creator Agent
```

### Phase 5：产品化

从个人开发系统升级为商业产品，增加：

- 用户系统
- Workspace
- Template Marketplace
- Skill Marketplace
- Agent Marketplace
- Cloud Deployment

## 5. AI Course Factory 架构定位

AI Course Factory 是 ContentOS 的第一个验证应用。

```text
Knowledge Source
    ↓
Knowledge Layer
    ↓
Agent Workflow
    ↓
Content Factory
    ↓
Production Skill Layer
    ↓
Output
```

## 6. Agent Architecture Principle

采用 Workflow + Specialized Agent，不采用超级 Agent，也不采用大量 Agent 自由协作。

MVP：

```text
Workflow
    ↓
Knowledge Agent
    ↓
Content Agent
    ↓
Production Agent
    ↓
Reviewer
```

## 7. Skill Architecture Principle

Skill 是可复用、可测试、可替换的能力模块。

- Creative Skills：Storyboard、Character Design、Teaching Visualization
- Production Skills：Image、Voice、Subtitle、Renderer
- Infrastructure Skills：Storage、Asset Management、Publishing

## 8. Production Pipeline Principle

采用 Programmatic + Template + AI Asset，不采用纯 AI 视频生成。

```text
Script
    ↓
Storyboard Artifact
    ↓
Timeline Artifact
    ↓
Renderer Interface
    ↓
Video Artifact
```

MVP 使用 Stickman Renderer；未来可扩展 Remotion Renderer、AI Video Renderer 和其他 Renderer。

## 9. Knowledge Source Strategy

MVP 使用 GitHub Connector。未来演进为：

```text
Knowledge Connector
├── GitHub
├── PDF
├── Web
├── YouTube
├── Notion
└── Local Files
```

## 10. GitHub Repository Strategy

```text
JettxonHo
├── AI-Course-Factory
├── ContentOS
├── ai-ecommerce-agent
├── hifly-hands-on-product-batch
├── trekking-potato
└── Other Projects
```

## 11. Existing Asset Strategy

- trekking-potato：IP Asset System，用于 Character、Brand、Visual Identity。
- hifly：Automation Layer，用于 Task Execution、Browser Automation、Batch Production。
- ai-ecommerce-agent：Agent Application Reference，复用 Agent Workflow、Human Review。
- ketchup Templates：不整体迁移；拆解为 Workflow Assets、Prompt Assets、QA Rules、Creative Skills。

## 12. MVP Success Criteria

MVP 成功不是完成平台，而是跑通以下闭环：

```text
Knowledge Source
    ↓
AI Understanding
    ↓
Content Planning
    ↓
Production
    ↓
Video Output
```

## 13. Non-goals（当前不做）

- SaaS 平台
- 用户体系
- 多租户
- Agent Marketplace
- Skill Marketplace
- 完整 ContentOS
- 自研视频模型
- 多 Renderer 管理系统

## 14. Final Strategic Statement

```text
Build Applications
    ↓
Discover Reusable Capabilities
    ↓
Extract ContentOS
    ↓
Create AI Product Ecosystem
```

最终目标：构建一个能够将知识资产自动转换为内容资产的 AI 产品基础设施。

下一步文档链路：

```text
AI Product Studio Strategy V3
    ↓
Phase 1.1 AI Course Factory MVP PRD
    ↓
Phase 1.2 Technical Spec
    ↓
Phase 1.3 Implementation Spec
    ↓
Coding
```

本文件作为后续所有 PRD 和 Spec 的上层约束。
