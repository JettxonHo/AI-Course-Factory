# Phase 0.5 Step 1 Decision Record v1.0

## Status

Approved Draft

## Purpose

记录 AI Course Factory MVP 在 Agent Framework、Skill
Architecture、Workflow Design 方面的调研结论与架构决策，为后续
PRD、Technical Spec、ADR 提供依据。

------------------------------------------------------------------------

# 1. 核心背景

AI Course Factory 不是简单的视频生成工具，而是验证：

Knowledge Source → AI理解 → 内容规划 → 内容生产 → 多渠道输出

的端到端能力。

长期目标：

通过 AI Course Factory 验证能力，再逐步抽象形成 ContentOS。

架构目标：

-   MVP快速落地
-   可展示真实产品能力
-   避免未来大规模重构
-   支持平台化演进

------------------------------------------------------------------------

# 2. Agent Framework 决策

调研对象：

-   LangGraph
-   CrewAI
-   OpenAI Agents SDK
-   Dify Workflow
-   n8n AI Workflow

## 结论

采用：

LangGraph + 自定义 Skill Interface

原因：

AI Course Factory 本质是 Workflow Orchestration
问题，而不是聊天机器人问题。

------------------------------------------------------------------------

# 3. Skill Architecture 决策

Skill定义：

可复用、可测试、可替换的执行能力模块。

Skill负责：

-   执行能力
-   外部工具调用

Skill不负责：

-   目标判断
-   任务规划

------------------------------------------------------------------------

## Skill分类

### Creative Skills

负责内容创造：

-   Storyboard
-   Character Design
-   Teaching Visualization

### Production Skills

负责媒体生产：

-   Image Generation
-   TTS
-   Video Render
-   Subtitle

### Infrastructure Skills

负责基础能力：

-   Asset Management
-   Storage
-   Publishing

------------------------------------------------------------------------

## Skill迁移原则

已有 ketchup templates：

不整体复制。

拆解为：

-   Workflow Assets
-   Agent Instructions
-   Execution Skills

------------------------------------------------------------------------

# 4. Workflow边界

Workflow负责：

-   流程控制
-   状态管理
-   条件分支
-   Human Review

Agent负责：

-   推理
-   判断
-   规划
-   决策

Skill负责：

-   执行
-   调用能力
-   返回结果

------------------------------------------------------------------------

# 5. MVP Agent设计

不采用：

大量Multi-Agent自由协作。

原因：

增加Token成本、调试成本和系统复杂度。

采用：

Workflow + Specialized Agent。

MVP：

Workflow： 1个

Agent：

-   Knowledge Agent
-   Content Agent
-   Production Agent

Reviewer：

质量控制。

------------------------------------------------------------------------

# 6. MCP决策

采用：

MCP Ready，而不是 MCP First。

原因：

MCP适合：

-   外部工具连接
-   数据源连接
-   能力发现

但不负责：

-   Workflow
-   Planning
-   Memory

策略：

MVP使用内部Tool Interface。

未来Skill可包装为MCP Server。

------------------------------------------------------------------------

# 7. MVP架构原则

    Input

    ↓

    Knowledge Source

    ↓

    LangGraph Workflow

    ↓

    Agents

    ↓

    Skill Layer

    ↓

    Human Review

    ↓

    Output

------------------------------------------------------------------------

# 8. 放弃方案

## 单超级Agent

原因：

长期维护困难，Prompt膨胀。

## 大量Multi-Agent

原因：

过度设计，增加复杂度。

## 先开发完整ContentOS

原因：

平台优先会导致周期过长，缺少真实反馈。

## MVP阶段独立Skill平台

原因：

增加管理成本。

------------------------------------------------------------------------

# 9. 最终决策

  领域              决策
  ----------------- ------------------------------
  Agent Framework   LangGraph
  Workflow模式      Workflow + Specialized Agent
  Agent数量         3+1
  Skill模式         Tool-like Interface
  Skill管理         MVP项目内，未来Registry
  MCP               未来兼容
  Human Review      必须保留
  核心竞争力        Knowledge → Content转换能力

------------------------------------------------------------------------

# 下一阶段

Phase 0.5 Step 2：

Video Production Pipeline Research

目标：

确定：

-   Production Skill Layer
-   Video Rendering方案
-   Animation方案
-   TTS方案
-   视频生产Workflow
