# AI Course Factory

AI Course Factory 是一个本地优先的 AI 教育短视频生产应用。它把公开 GitHub 仓库中的可追溯知识，转换为经过人工审核的脚本、生产计划、视频和可导出的发布包。

当前代码已完成第一条离线纵向切片：

```text
Public GitHub source
  -> Source Record
  -> grounded Knowledge
  -> Course / Episode Plan
  -> versioned Script
  -> mandatory Script Review
  -> exact approved Script Version
```

Production Planning、媒体生成、本地工作台和发布包仍未实现。当前真实状态见 [docs/STATUS.md](docs/STATUS.md)，当前已批准开发目标见 [GOAL.md](GOAL.md)。

## 开始之前

Codex 和开发者必须先阅读：

1. [AGENTS.md](AGENTS.md)
2. [docs/README.md](docs/README.md)
3. [GOAL.md](GOAL.md)
4. [docs/STATUS.md](docs/STATUS.md)

## 当前验证命令

```bash
uv run python -m unittest discover -s tests -v
```

运行要求：Python 3.12。项目当前只依赖 LangGraph；未来依赖必须通过批准的有界任务加入。

## 权威文档

- [PRD](docs/product/PRD.md)：产品必须做什么。
- [System Spec](docs/spec/SYSTEM-SPEC.md)：系统必须保持什么行为和契约。
- [Implementation Spec](docs/spec/IMPLEMENTATION-SPEC.md)：代码和运行时怎样实现这些契约。
- [Development Workflow](docs/DEVELOPMENT-WORKFLOW.md)：Codex、Goal、Luna、Issue、PR 和验收怎样协作。

历史 Phase 文档保留为决策与交付证据，但不再作为日常开发入口。
