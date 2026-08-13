# AI Course Factory

AI Course Factory 是一个本地优先的 AI 教育短视频生产应用。它把公开 GitHub 仓库中的可追溯知识，转换为经过人工审核的脚本、生产计划、视频和可导出的发布包。

当前代码已具备从 Source 到本地 Publish Package 的大部分离线后端能力；获批的 FAST-MVP 方向是把这些能力尽快接成可操作的本地产品：

```text
Public GitHub source
  -> grounded Script + human review
  -> production plan + budget approval
  -> Visual/TTS + FFmpeg
  -> final review + local export
```

本地 Web 工作台、真实 Visual/TTS Adapter 和真实端到端 Demo 尚未完成。当前真实状态见 [docs/STATUS.md](docs/STATUS.md)，当前获批 FAST-MVP 目标见 [GOAL.md](GOAL.md)。

## 开始之前

Codex 和开发者按以下顺序阅读：

1. [docs/README.md](docs/README.md)
2. [GOAL.md](GOAL.md)
3. [docs/STATUS.md](docs/STATUS.md)
4. [AGENTS.md](AGENTS.md)

## 当前验证命令

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

运行要求：Python 3.12。新增依赖只在当前纵向任务确有需要时加入。

## 权威文档

- [PRD](docs/product/PRD.md)：产品必须做什么。
- [System Spec](docs/spec/SYSTEM-SPEC.md)：系统必须保持什么行为和契约。
- [Implementation Spec](docs/spec/IMPLEMENTATION-SPEC.md)：代码和运行时怎样实现这些契约。
- [Development Workflow](docs/DEVELOPMENT-WORKFLOW.md)：Codex、Goal、Luna、Issue、PR 和验收怎样协作。

历史 Phase 文档保留为决策与交付证据，但不再作为日常开发入口。
