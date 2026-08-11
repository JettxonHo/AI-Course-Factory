# AI Course Factory Agent Rules

## 1. 适用范围

本文件适用于整个仓库。所有 Codex 主任务和子 Agent 在修改文件前必须读取本文件。

## 2. 必读顺序

1. `docs/README.md`：文档真源与冲突规则。
2. `GOAL.md`：当前获批 Goal；未获批时不得开始 Goal 功能编码。
3. `docs/STATUS.md`：当前实现、测试、分支和阻塞事实。
4. 与任务相关的 PRD、System Spec、Implementation Spec 章节。
5. 当前 GitHub Issue 或唯一 Task Contract。
6. `docs/DEVELOPMENT-WORKFLOW.md`：Agent、Git、PR、Review 和验收协议。

不要以旧对话、历史 Phase 状态字段或任务包自述替代当前代码、Git、测试和上述真源。

## 3. 权威边界

- `docs/product/PRD.md` 决定用户价值、产品行为、MVP 范围和产品验收。
- `docs/spec/SYSTEM-SPEC.md` 决定领域模型、Artifact、状态、门禁和模块接口。
- `docs/spec/IMPLEMENTATION-SPEC.md` 决定当前技术栈、物理模块、持久化、适配器和验证策略。
- `GOAL.md` 只能缩小本轮工作范围，不能修改 PRD 或 Spec。
- `docs/STATUS.md` 只陈述当前事实，不能授权新范围。
- `docs/decision-log.md` 记录已批准的例外、替代和难逆决策。

发生冲突时停止受影响工作，由主控 Agent给出证据、修正文档并记录决定。不得在代码中静默选择。

## 4. Agent 路由

### 主控：ORCHESTRATOR_REVIEWER

- 项目配置：`gpt-5.6-sol`，`xhigh`。
- 负责调查、产品与架构决策、Goal、里程碑、Issue/Task Contract、依赖和文件归属。
- 负责检查真实 Diff、测试、构建、运行证据和最终验收。
- 原则上不承担普通有界实现；若直接实现，最终批准必须由独立 Reviewer 或用户完成。

### 实现：luna-worker

- 必须以准确的自定义 Agent 名称 `luna-worker` 调用。
- 已配置模型：`gpt-5.6-luna`；推理强度：`max`。
- 只执行已批准、边界明确且可独立验证的 Task Contract。
- 不得扩展产品范围、修改公共接口、改变架构或批准自己的实现。
- 不得再派生子 Agent，除非主控明确要求。
- 必须保留用户和其他 Agent 的修改，不得回退无关变更。

禁止把实现任务自动回退给 Terra、默认 `worker` 或其他 Agent。若 `luna-worker` 不可发现，记录状态并返回：

```text
STATUS: BLOCKED_LUNA_WORKER_UNAVAILABLE
```

配置存在只代表 `CONFIG_VERIFIED`；只有运行环境明确暴露实际模型和推理强度时才能写 `RUNTIME_VERIFIED`。

## 5. 编码前置条件

功能编码开始前必须同时存在：

- Approved Goal；
- 对应里程碑处于 Ready；
- 单一 GitHub Issue 或唯一 Task Contract；
- 明确目标、允许文件、禁止范围、接口、验收和验证命令；
- 有效基准提交和干净或已解释的工作区；
- 有效 `luna-worker` 路由；
- 涉及付费 Provider 或外部副作用时，有单独授权和预算上限。

缺少任一项时，只允许调查、规划、文档、无副作用验证或独立 Review。

## 6. 实现规则

- 做满足任务合同的最小完整变更。
- 优先深化现有模块，不创建只做转发的浅模块。
- Agent 产生 Candidate；Artifact Store 验证并 Commit；Workflow 只保存控制状态和 exact Reference。
- 所有跨阶段消费必须使用 exact `ArtifactReference`，禁止隐式 latest。
- 外部 Provider 只能通过已定义接口的 Adapter 调用。
- 付费调用必须位于预算批准之后；测试默认使用 Fake Adapter。
- 不引入与真实产品风险无关的哈希、形式化证明或机械防御层。
- 不删除、重置、覆盖或整理不属于当前任务的修改。

## 7. 测试与证据

当前基础回归命令：

```bash
uv run python -m unittest discover -s tests -v
```

每个任务还必须运行 Task Contract 指定的最小相关测试。最终 MVP 不能用 Fake、Fixture 或 Mock 成功冒充真实 Provider 和可播放视频的运行证据。

## 8. Git 与 Review

- 一个 Issue 对应一个主要目标，原则上一个 PR 完成。
- 分支默认使用 `codex/<issue>-<slug>`；子 Agent 必须使用主控分配的分支或 worktree。
- 多个写入 Agent 不得并行修改相同核心文件、公共接口或未稳定契约。
- 实现者提交结构化交接；主控重新检查 Diff 和验证，不依赖自述批准。
- Review 结果仅使用 `APPROVED`、`CHANGES_REQUESTED`、`BLOCKED` 或 `ESCALATE_TO_HUMAN`。
- 同一问题连续两轮未解决时，返回主控重新分析，不继续机械尝试。

## 9. 必须人工确认

- 产品方向或 Goal 范围发生重大变化；
- 选择真实视觉/TTS Provider、产生额外费用或提高预算；
- 生产部署、敏感数据、认证授权、隐私或不可逆迁移；
- 更换主要技术栈或大规模重写；
- 多个合理方案无法仅凭工程证据裁决；
- 降低既定验收或测试标准。
