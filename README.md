# AI Course Factory

AI Course Factory 是一个本地优先的知识视频制作应用。它把公开 GitHub 仓库中的可追溯知识，转成经过人工审核的脚本、音频、视觉编排、视频和可导出的发布包。

## 当前产品真相

- FAST-MVP v1.1 是已完成的本地历史基线。
- Creator Handoff MVP v1.2 已交付 H0–H3.5 的 Source、Script/Storyboard、Handoff、creator-import、确定性合成和三页中文工作台能力；H4 未完成。
- Issue #141/#142 的 H4 候选保留了已独立通过的 Final checklist 与 source-grounded content correction，但外部六段视频生成/导入主路径已被 Product Owner **PARK**。
- Knowledge Video Editorial MVP v1.3 exact Goal 已由 Product Owner 正式批准，状态为 **APPROVED / ACTIVE**。当前唯一 active milestone 是 Issue #143 的 E0 权威文档收口；feature implementation 与 E1 Luna/编码仍未授权。

推荐的新主链候选是：

```text
exact Source
  -> approved grounded Script
  -> one continuous Whole Narration
  -> phrase-level millisecond Acoustic Alignment
  -> human-approved Visual Edit Plan
  -> deterministic A-roll / B-roll production
  -> approved 15–20 second Sample Video
  -> full local render
  -> named-human Final Review
  -> Publish Package
```

MVP 不使用视频生成 LLM/API。Codex Desktop ImageGen 只在应用外提供 creator-supplied 静态角色、场景和道具；应用继续拥有 Narration、Alignment、SRT 和审核事实。HyperFrames 或等价确定性渲染 seam 仍需后续独立 Task Contract 论证，本规划任务不会安装或运行它。

正式合同见 [Knowledge Video Editorial MVP v1.3 Goal Contract](docs/goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-PROPOSAL.md) 与 [GOAL.md](GOAL.md)。Issue #143 正把已批准 Goal 与 D-010 转成一个九文件 E0 docs PR；在该 PR 合并前不得提前声明 E0 已完成。外部六 MP4 H4 路径继续 PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE。

## 当前可运行的已实现能力

合并后的应用仍是三个本地 server-rendered 页面，可从明确的数据目录启动：

```bash
PYTHONPATH=src uv run python -m ai_course_factory.web --data-dir ./var/ai-course-factory
```

默认只绑定 `127.0.0.1:8000`。已实现的 v1.2 兼容路径仍支持显式 GPT-SoVITS、本地图片输入及 creator-generated MP4 目录，但这些能力不构成 v1.3 已实现证据，也不应在当前 PARK 状态下驱动 H4 外部视频生成。

### 历史/兼容性本地输入

- F2A 图片输入只接受显式目录与固定 `scene-1.png` 至 `scene-6.png`。
- H3 creator clip 输入只接受显式目录与固定 `scene-1.mp4` 至 `scene-6.mp4`，没有浏览器路径/上传或 Downloads/Desktop/latest 扫描。
- F2B GPT-SoVITS 使用显式外部 Python 3.11、官方 repo/model/reference 配置；不读取云端凭据，外部调用费用为 0。

这些是保留的实现事实，不是继续外部 clip 生产的授权。

## 开始之前

Codex 和开发者按以下顺序阅读：

1. [docs/README.md](docs/README.md)
2. [GOAL.md](GOAL.md)
3. [docs/STATUS.md](docs/STATUS.md)
4. [AGENTS.md](AGENTS.md)

## 验证命令

代码任务的完整回归命令仍为：

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

Issue #143 是纯文档 E0 权威化任务，不运行 full regression。它只要求 exact nine-doc ownership、Goal/authority/stale wording review 与 `git diff --check`。

## 权威文档

- [PRD](docs/product/PRD.md)：产品价值、行为和验收候选。
- [System Spec](docs/spec/SYSTEM-SPEC.md)：系统 ownership、事实与 gate 候选。
- [Implementation Spec](docs/spec/IMPLEMENTATION-SPEC.md)：复用、物理方向和验证策略候选。
- [Decision Log](docs/decision-log.md)：D-010 及保留的历史决策。
- [Development Workflow](docs/DEVELOPMENT-WORKFLOW.md)：Goal、Luna、Issue、PR 和验收协作。

历史 Phase 与 Creator Handoff 文档继续保留为实现和决策证据，不作为 v1.3 实施授权。
