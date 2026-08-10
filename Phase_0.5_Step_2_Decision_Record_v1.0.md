# Phase 0.5 Step 2 Decision Record v1.0

## Document Status

Status: Approved Draft

Purpose: 记录 AI Course Factory MVP 在 Production Skill
Layer、Storyboard、Timeline、Artifact、Renderer Architecture
方面的调研结论与架构决策。

本文件作为后续： - PRD - Technical Spec - Architecture Decision Record -
Development Plan

的输入依据。

------------------------------------------------------------------------

# 1. 背景

AI Course Factory 的目标不是简单生成视频。

核心目标：

Knowledge Source → Knowledge Understanding → Content Planning →
Production Pipeline → Multi-format Output

长期目标：

通过 AI Course Factory 验证能力，并逐步抽象形成 ContentOS。

------------------------------------------------------------------------

# 2. Production Strategy 决策

## 最终选择

采用：

Programmatic + Template + AI Asset Hybrid Architecture

不采用：

-   纯AI视频生成
-   纯模板视频
-   自研视频模型

原因：

教学内容需要：

-   可控
-   可修改
-   可批量生产
-   保持角色一致性

------------------------------------------------------------------------

# 3. Production Skill Layer 架构

Production Skill Layer 分为三层：

------------------------------------------------------------------------

## 3.1 Creative Skills

负责：

"生产什么内容"。

包括：

-   Storyboard Skill
-   Character Design Skill
-   Teaching Visualization Skill

------------------------------------------------------------------------

## 3.2 Production Skills

负责：

"如何生成媒体"。

包括：

-   Image Generation Skill
-   Voice Generation Skill
-   Video Render Skill
-   Subtitle Skill

------------------------------------------------------------------------

## 3.3 Infrastructure Skills

负责：

"如何管理生产过程"。

包括：

-   Asset Management
-   Artifact Storage
-   Publishing

------------------------------------------------------------------------

# 4. Storyboard Architecture 决策

## Storyboard定位

Storyboard不是普通文本。

它是：

Narrative Intermediate Representation。

作用：

连接：

Script 与 Renderer。

架构：

Script Artifact

↓

Storyboard Artifact

↓

Timeline Artifact

↓

Renderer

↓

Video

------------------------------------------------------------------------

## Storyboard核心字段

MVP包含：

-   Scene
-   Shot
-   Character
-   Asset
-   Duration
-   Narration
-   Camera

------------------------------------------------------------------------

# 5. Timeline Layer 决策

## 是否需要Timeline？

结论：

需要。

原因：

Storyboard描述创意。

Timeline描述执行。

Timeline负责：

-   时间
-   动作
-   音频
-   字幕
-   动画事件

------------------------------------------------------------------------

## Timeline定位

作为Renderer统一输入。

Renderer不直接读取Storyboard。

------------------------------------------------------------------------

# 6. Renderer Architecture 决策

## Renderer Interface

统一：

    render(
     timeline,
     assets,
     config
    )

------------------------------------------------------------------------

## MVP Renderer

选择：

Stickman Renderer

原因：

-   差异化强
-   IP结合
-   快速产出展示效果

------------------------------------------------------------------------

## Future Renderer

候选：

Remotion Renderer

AI Video Renderer

Manim Renderer

------------------------------------------------------------------------

# 7. Artifact Architecture 决策

## 核心原则

视频不是单文件。

采用：

Artifact Graph。

结构：

    Knowledge Artifact

    ↓

    Script Artifact

    ↓

    Storyboard Artifact

    ↓

    Timeline Artifact

    ↓

    Asset Artifact

    ↓

    Video Artifact

------------------------------------------------------------------------

每个Artifact：

需要：

-   ID
-   Version
-   Status
-   Dependencies
-   Creator

------------------------------------------------------------------------

# 8. Partial Execution 决策

Workflow必须支持：

-   checkpoint
-   artifact persistence
-   partial execution

例如：

已有Storyboard：

直接：

Storyboard

↓

Timeline

↓

Render

不需要重新执行：

Knowledge → Script → Storyboard

------------------------------------------------------------------------

# 9. Asset Registry 决策

## 不采用：

简单文件夹。

## 不采用：

复杂资产管理系统。

## 采用：

Lightweight Asset Registry。

MVP：

registry.json + assets目录。

用于：

-   角色一致性
-   版本管理
-   资产复用

------------------------------------------------------------------------

# 10. Existing Assets Mapping

## ketchup-codex-doomsday-template

处理：

拆解复用。

迁移：

-   Workflow Assets
-   Prompt Assets
-   QA Rules

不整体复制。

------------------------------------------------------------------------

## ketchup-xuanhuan-template

复用：

-   Narrative Workflow
-   Story Design能力

不保留：

-   玄幻领域逻辑

------------------------------------------------------------------------

## stickman-video-director

定位：

Renderer Skill。

负责：

Timeline → Video。

------------------------------------------------------------------------

## Remotion

定位：

未来通用Renderer候选。

------------------------------------------------------------------------

# 11. Build / Buy / Borrow Decision

  能力                策略
  ------------------- ----------------
  Workflow Engine     Build
  Storyboard Logic    Build
  Timeline Schema     Build
  Character System    Build + Borrow
  TTS                 Buy/API
  Image Generation    Buy/API
  Stickman Renderer   Borrow + Adapt
  Remotion            Borrow Future
  Publishing          Later

------------------------------------------------------------------------

# 12. MVP Production Skill Scope

MVP实现：

## Creative

-   Storyboard Skill
-   Character Skill

## Production

-   TTS Skill
-   Subtitle Skill
-   Stickman Renderer

## Infrastructure

-   Lightweight Asset Registry
-   Artifact Storage

暂缓：

-   多Renderer系统
-   AI Video Model
-   自动发布
-   完整资产平台

------------------------------------------------------------------------

# 13. 最终 Production Architecture

    Production Agent

    ↓

    Storyboard Artifact

    ↓

    Timeline Artifact

    ↓

    Renderer Interface

    ↓

    Stickman Renderer

    ↓

    Video Artifact

    ↓

    Reviewer

    ↓

    Human Approval

------------------------------------------------------------------------

# 14. Final Principles

1.  视频生成不是核心竞争力。

核心：

Knowledge → Structured Content → Production Pipeline。

2.  Renderer必须可替换。

3.  Artifact必须可追踪。

4.  Workflow必须支持中断恢复。

5.  Skill必须接口化。

6.  MVP优先验证闭环，不追求完整平台。

------------------------------------------------------------------------

# Next Phase

进入：

Phase 1: AI Course Factory MVP PRD Design

目标：

定义：

-   用户
-   场景
-   MVP范围
-   功能列表
-   技术Spec
-   开发任务拆分
