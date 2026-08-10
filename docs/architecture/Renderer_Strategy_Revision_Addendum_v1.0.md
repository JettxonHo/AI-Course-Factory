# Renderer Strategy Revision Addendum v1.0

## Document Status

| 字段 | 内容 |
| --- | --- |
| Document | Renderer Strategy Revision Addendum |
| Version | v1.0 |
| Status | Accepted |
| Decision Date | 2026-08-09 |
| Owner | JettxonHo |
| Scope | AI Course Factory MVP Production Strategy |
| Current Product Baseline | [AI Course Factory MVP PRD v0.3](../product/AI_Course_Factory_MVP_PRD_v0.3.md) |

## 1. Purpose

本 Addendum 修订 AI Course Factory MVP 的视频生产路线，并保持 Strategy V3、Phase 0.5 Step 1 与 Phase 0.5 Step 2 的历史记录完整。

旧文档不直接改写。凡本 Addendum 明确列出的旧 Renderer 条款，其状态均为 `Superseded`；未被列出的战略原则继续有效。

## 2. Context

Phase 0.5 Step 2 将 `stickman-video-director` 理解为可以执行 `Timeline → Video` 的 Renderer Skill，并据此选择确定性 Stickman Renderer 作为 MVP Renderer。

后续核查确认：

- `stickman-video-director` 的实际能力是把内容转化为 Director Proposal 和供应商视频提示词。
- 它不负责调用视频模型，也不负责生成、剪辑或合成最终视频。
- MVP 需要在保留结构化 Artifact、外部语音和可控合成的同时，使用 Omni 生成场景视觉片段。

因此，原有 MVP Renderer 选择与实际可复用资产能力不一致，需要通过本 Addendum 修订。

## 3. Decision

AI Course Factory MVP 采用：

> **Prompt + Omni Hybrid Production**

MVP 生产链路遵循：

```text
Approved Script
    ↓
Storyboard Artifact
    ↓
Timeline Artifact
    ↓
Provider-neutral Production Request
    ↓
Production Layer
    ├── External Voice / Audio Composition
    ├── Omni Visual Generation
    └── Media Composition
          ↓
Video Artifact
```

具体责任如下：

- Omni 负责场景视觉片段、动画和可选环境声。
- 外部统一 Voice Skill 负责主旁白。
- Audio Composition 负责场景旁白、可选 BGM 与 Effect 的 Master Audio。
- Media Composition 负责视觉片段、Master Audio 和字幕的最终合成。
- Production Layer 必须保持供应商可替换边界。

## 4. Superseded Clauses

以下旧条款由本 Addendum 明确替代：

| Source | Previous Clause or Decision | New Status | Replacement |
| --- | --- | --- | --- |
| [AI Product Studio Strategy V3 §8](../strategy/AI_Product_Studio_Strategy_V3.md) | “MVP 使用 Stickman Renderer。” | Superseded | MVP 使用 Prompt + Omni Hybrid Production。 |
| [Phase 0.5 Step 2 §6](../../Phase_0.5_Step_2_Decision_Record_v1.0.md) | MVP Renderer 选择 Stickman Renderer。 | Superseded | MVP 使用 Omni 视觉生成与外部语音、媒体合成的混合路线。 |
| [Phase 0.5 Step 2 §10](../../Phase_0.5_Step_2_Decision_Record_v1.0.md) | `stickman-video-director` 定位为 Renderer Skill，负责 `Timeline → Video`。 | Superseded | `stickman-video-director` 定位为 Director / Prompt Skill，不直接渲染视频。 |
| [Phase 0.5 Step 2 §11](../../Phase_0.5_Step_2_Decision_Record_v1.0.md) | Stickman Renderer 采用 Borrow + Adapt。 | Superseded | 借用并适配其导演与 Prompt 能力；视频生成通过 Omni Provider 能力完成。 |
| [Phase 0.5 Step 2 §12](../../Phase_0.5_Step_2_Decision_Record_v1.0.md) | MVP Production Skill 包含 Stickman Renderer，AI Video Model 暂缓。 | Superseded | MVP Production Skill 包含 Omni Visual Generation、Voice、Subtitle、Audio / Media Composition。 |
| [Phase 0.5 Step 2 §13](../../Phase_0.5_Step_2_Decision_Record_v1.0.md) | `Timeline → Renderer Interface → Stickman Renderer → Video`。 | Superseded | `Timeline → provider-neutral Production Request → Production Layer → Provider Adapter / Skills → Video`。 |
| [AI Course Factory MVP PRD v0.1](../product/AI_Course_Factory_MVP_PRD_v0.1.md) | Stickman Renderer、60–90 秒与相应旧生产依赖。 | Superseded for current MVP | 当前产品需求以 PRD v0.3 为准。 |

## 5. Preserved Decisions

本 Addendum 不推翻以下已确认原则：

1. AI Course Factory 的核心竞争力是 Knowledge → Structured Content → Production Pipeline，而不是基础视频模型本身。
2. Workflow + Specialized Agent 继续有效。
3. Human Review 必须保留。
4. Storyboard 是连接 Script 与执行层的 Narrative Intermediate Representation。
5. Timeline 是供应商无关的执行计划 Artifact。
6. Artifact First、checkpoint、artifact persistence 和 partial execution 继续有效。
7. Production Skill 必须可测试、可替换。
8. MVP 继续遵循 Build + Buy + Borrow，不自研视频基础模型。
9. 未来确定性 Stickman Renderer、Remotion Renderer 或其他视觉生产方式仍可通过稳定边界接入。

## 6. `stickman-video-director` Revised Position

`stickman-video-director` 的 MVP 定位为 Director / Prompt Skill：

- 根据已批准内容形成 Director Proposal。
- 将分镜意图转化为适合目标视频供应商的提示策略。
- 支持场景级提示词组织和视觉一致性约束。

它不负责：

- 调用 Omni 或其他视频模型
- 生成最终 Scene Clip
- 合并场景视频
- 生成主旁白
- 合成字幕、音频或最终 Video Artifact

## 7. Production Boundary Consequences

本决策带来以下产品与架构约束：

- Prompt 是 provider-specific execution representation，不是系统核心 Artifact。
- Timeline 与生产供应商之间需要 provider-neutral 的内部生产协议。
- 供应商调用必须通过 Adapter 隔离。
- 生产流程必须处理 Provider Error、Generation Failure、Quality Failure 与 Budget Limit。
- 付费生成前必须存在预算估算与人工授权。
- 单个 Scene 失败不得使有效的知识、脚本、分镜或其他场景产物失效。
- Provider Preview 能力变化时，系统必须允许暂停、重试或人工提供替代 Scene Clip。

内部协议、Production Orchestrator、Audio Composer、Artifact Schema 和具体 Adapter Contract 由获批的 PRD v0.3 与后续 Technical Spec 进一步定义。

## 8. Alternatives Considered

### Deterministic Stickman Renderer for MVP

- 优点：输出更确定、可编程控制较强。
- 问题：现有 `stickman-video-director` 并不是 Renderer；MVP 需要额外建设完整渲染能力，会扩大首期工程范围。
- 结论：不作为 MVP 路线，保留为后续候选。

### Pure One-shot AI Video Generation

- 优点：链路短。
- 问题：弱化 Script、Storyboard、Timeline、外部语音、Artifact 追踪和局部恢复。
- 结论：拒绝。MVP 采用结构化 Hybrid Production，而不是无中间资产的一键生成。

### Remotion-first Production

- 优点：程序化合成和模板能力成熟。
- 问题：不属于当前 Demo 的最短闭环，且会把 MVP 重点转向 Renderer 工程。
- 结论：MVP 不接入，保留为后续确定性 Renderer 候选。

## 9. Consequences and Risks

### Positive Consequences

- 与现有 `stickman-video-director` 的真实能力一致。
- 更快验证 Knowledge-to-Content-to-Video 闭环。
- 保留 Timeline、Artifact 和局部重生成价值。
- 将供应商特性限制在 Adapter 内，避免产品契约直接依赖 Prompt 格式。

### Risks

- Omni 输出可能存在角色一致性和质量波动。
- Preview 供应商能力、限制和价格可能变化。
- 场景生成与重试可能带来不可预测成本。

### Required Mitigations

- Character Artifact 与视觉一致性 Review。
- Scene-level generation、Failure Artifact 和局部恢复。
- Production Budget Gate。
- 外部 Voice Skill 与独立 Audio Composition。
- Provider Adapter 与人工替代 Scene Clip 路径。

## 10. Decision Chain

```text
AI Product Studio Strategy V3
    ↓
Phase 0.5 Step 1 Decision Record v1.0
    ↓
Phase 0.5 Step 2 Decision Record v1.0
    ↓
Renderer Strategy Revision Addendum v1.0
    ↓
AI Course Factory MVP PRD v0.2 — Archived Review Baseline
    ↓
AI Course Factory MVP PRD v0.3 — Approved Baseline
```

## 11. Approval Record

| Role | Name | Decision | Date | Notes |
| --- | --- | --- | --- | --- |
| Product Owner | JettxonHo | Accepted | 2026-08-09 | Renderer strategy revision approved as baseline input. |
