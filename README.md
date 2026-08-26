# AI Course Factory

AI Course Factory 是一个本地优先的知识视频制作应用。它把公开 GitHub 仓库中的可追溯知识，转成经过人工审核的脚本、音频、视觉编排、视频和可导出的发布包。

## 当前产品真相

- FAST-MVP v1.1 与 Creator Handoff v1.2 H0–H3.5 是保留的本地历史/基础能力；Creator Handoff H4 从未完成。
- Knowledge Video Editorial MVP v1.3 已完成 E0、S0 与 S1。Creator-authored Script Package intake/re-import、immutable Script Version、exact approve/reject Decision、restart/replay 已通过 Issue #150 / PR #151 合并到 `main@1a769289`，最终回归 476/476。
- v1.3 没有完成 Narrative Clock、Visual Edit Plan、Sample、full render 或发布；Issue #145 仍 OPEN/PAUSED，其未合并候选不得恢复或整包复用。
- Product Owner 于 2026-08-27 批准 **Knowledge Video Business Loop MBL v1.0** exact Goal。Issue #152 只执行 B0 docs-first authority rebaseline；B1–B6 代码、Provider 调用、媒体生产和抖音发布仍未授权。

批准的 MBL 主链是：

```text
exact Computer Vision Source
  -> explicit Creator-authored Script Package intake
  -> exact human-approved Script Version
  -> Doubao Liu Fei 2.0 Whole Narration
  -> short-phrase continuous clock + canonical SRT
  -> human-approved Visual Edit Plan
  -> Codex creator assets + deterministic A-roll / B-roll
  -> approved 15–20 second Sample Video
  -> full local render
  -> named-human Final Review
  -> publish-ready package
  -> manual Douyin publication
  -> 72-hour feedback + 7-day archive
```

首轮固定为三条“AI 如何看懂画面”系列，使用 `microsoft/AI-For-Beginners/lessons/4-ComputerVision/06-IntroCV/README.md` 的 exact commit/blob/locator 事实。每条 60–90 秒；第 1 条验证完整生产/发布/反馈路径，三条建立首个账号基线。数据不好可以否定内容假设，但不否定业务闭环已被真实执行。

AI Course Factory 是业务控制台，不是专业剪辑器。当前 MBL 允许 Codex 在应用外完成脚本与静态素材生产，豆包“刘飞 2.0”承担整篇旁白，HyperFrames/FFmpeg 通过后续 bounded adapter 负责确定性渲染。稳定生产合同必须允许将来替换为独立模型/API；B0 不调用任何 Provider、ImageGen、HyperFrames 或抖音能力。

现行权威见 [Knowledge Video Business Loop MBL v1.0](docs/goals/KNOWLEDGE-VIDEO-BUSINESS-LOOP-MBL-v1.0.md) 与 [GOAL.md](GOAL.md)。[v1.3 Goal Contract](docs/goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-PROPOSAL.md) 和 [Creator Script 重基线](docs/goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-SCRIPT-INPUT-REBASELINE.md) 保留为 S1 基础合同/历史。

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

这些是保留的实现事实，不是继续外部 clip 生产、恢复 #145 或跳过 B1–B6 gate 的授权。

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

B0 Issue #152 是 exact 11-doc change，只运行文档一致性、ownership 与 `git diff --check`；docs-only 不重跑 full regression。后续每个 feature milestone 仍须 focused checks、浏览器/真实边界证据及 merge 前一次 full regression。

## 权威文档

- [PRD](docs/product/PRD.md)：产品价值、行为和验收候选。
- [System Spec](docs/spec/SYSTEM-SPEC.md)：系统 ownership、事实与 gate 候选。
- [Implementation Spec](docs/spec/IMPLEMENTATION-SPEC.md)：复用、物理方向和验证策略候选。
- [Decision Log](docs/decision-log.md)：D-012 MBL 重基线及保留的历史决策。
- [Development Workflow](docs/DEVELOPMENT-WORKFLOW.md)：Goal、Luna、Issue、PR 和验收协作。

历史 Phase、Creator Handoff、v1.3 与受保护候选继续保留为实现和决策证据，不作为 MBL milestone 实施授权。
