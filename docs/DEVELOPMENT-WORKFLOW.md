# AI Course Factory Development Workflow v1.0

## 1. Status

| Field | Value |
| --- | --- |
| Status | Approved Process Baseline |
| Owner | Product Owner + ORCHESTRATOR_REVIEWER |
| Approved Direction | Goal-driven development with exact `luna-worker` implementation routing |
| Last Updated | 2026-08-12 |

本文件说明项目怎样开发。它不定义产品功能、系统行为或当前实现状态。

## 2. Agent Operating Model

### ORCHESTRATOR_REVIEWER

项目主控使用项目级配置 `gpt-5.6-sol / xhigh`。它负责：

- 调查真实仓库、文档、Issue、PR、测试和运行状态；
- 产品、架构、接口和跨模块决策；
- 编写和维护权威文档、Goal 与 STATUS；
- 把里程碑拆成有界 Issue/Task Contract；
- 决定串并行、文件归属、分支与合并顺序；
- 精确调用 `luna-worker`；
- 独立检查代码、Diff、测试、构建和运行证据；
- 给出 PR 和 Goal 级验收结论。

### luna-worker

实现 Agent 的唯一标准身份为：

```text
custom agent: luna-worker
configured model: gpt-5.6-luna
configured reasoning effort: max
logical role: IMPLEMENTER
```

它只处理任务合同内的实现、测试、修复和必要文档同步。它不决定产品方向，不修改未授权公共接口，不引入重大依赖，不批准或合并自己的实现。

未经用户当前明确授权，不使用 Terra 或其他 Agent 作为实现回退。

## 3. Model Evidence

模型状态只允许：

- `CONFIG_VERIFIED`：Agent 文件和字段已验证，运行时模型未单独暴露。
- `RUNTIME_VERIFIED`：运行环境明确显示实际模型和推理强度。
- `UNVERIFIED_RUNTIME_MODEL`：配置或运行时无法确认。
- `MODEL_MISMATCH`：运行时证据与请求配置冲突。

Agent 自述、逻辑角色名称、成功创建线程或任务通过都不是运行时模型证明。

## 4. Goal Lifecycle

```text
PROPOSED
  -> APPROVED
  -> ACTIVE
  -> GOAL_REVIEW
  -> GOAL_APPROVED | GOAL_APPROVED_WITH_FOLLOW_UPS

ACTIVE -> BLOCKED | ESCALATE_TO_HUMAN
```

一个 Goal 必须大于单一任务、小于开放式 backlog，并包含：

- 一个可验证最终结果；
- 明确范围和非目标；
- 里程碑与依赖；
- 每个里程碑的行为完成条件；
- 测试、构建、运行和用户验收证据；
- 外部副作用和人工确认门；
- 停止、阻塞与恢复条件。

Goal 获批不自动授权付费 Provider、生产部署或其他高风险外部操作。

## 5. Issue and Task Contract

一个 Issue 只承载一个主要结果。实现开始前，Issue 正文或唯一 Task Contract 必须包含：

```text
Task ID / Issue
Goal and milestone
Objective and user value
Baseline commit
Required reading
Allowed modules/files
Out of scope / forbidden files
Interface and invariants
Acceptance criteria
Tests and runtime evidence
Dependencies and merge order
External side-effect posture
Autonomous decisions
Escalation and stop conditions
Expected handoff
```

不得同时为同一任务维护 Issue Spec、Bounded Contract、Task Package 和 Task Record 四套重复真源。GitHub Issue 是首选任务真源；只有 Issue 暂不可用时才创建一个本地任务合同，并在 Issue 建立后迁移。

## 6. Standard Loop

### 6.1 Prepare

主控：

1. 复核 Goal、STATUS、基准提交和工作区。
2. 选择最小、完整、可独立验证的下一项结果。
3. 建立或更新 Issue/Task Contract。
4. 明确接口、文件归属、依赖、分支和验证命令。
5. 验证 `luna-worker` 配置与可发现性。

### 6.2 Implement

主控使用准确的 `agent_type: luna-worker` 委派。Luna：

1. 读取合同、相关权威文档和现有代码。
2. 检查基准、分支、工作区和其他修改。
3. 输出简短实现计划。
4. 实现满足合同的最小完整变更。
5. 运行相关测试、全量回归和合同要求的运行证据。
6. 审查 Diff、范围漂移、临时代码和未跟踪文件。
7. 返回结构化结果包。

### 6.3 Handoff

结果包至少包含：

```text
Task / Issue
requested agent and model status
branch / worktree / baseline / latest commit
completion status
changed files and behavior
acceptance mapping
test/build/runtime commands and results
contract deviations and autonomous decisions
known limitations, risks and blockers
recommended review focus
```

### 6.4 Independent Review

主控重新读取实际 Diff 和运行证据，Review：

- Goal、Issue 和接口是否满足；
- 是否范围漂移、重复实现或过度设计；
- 错误、数据一致性、预算、隐私和安全边界；
- 测试是否能因错误实现而失败；
- Fake/Mock 是否被误当成真实能力；
- 文档和 STATUS 是否需要同步。

Review 状态：`APPROVED`、`CHANGES_REQUESTED`、`BLOCKED`、`ESCALATE_TO_HUMAN`。

`CHANGES_REQUESTED` 继续交给同一 Luna 修复。相同问题连续两轮未解决时，主控停止重试并重新分析任务或架构。

### 6.5 Merge and Advance

只有验收、测试、CI、文档、风险和独立 Review 都满足时才合并。合并后：

- 关闭或更新 Issue；
- 更新 GOAL 与 STATUS；
- 解除后续依赖；
- 决定下一任务，而不是自动扩大当前任务。

## 7. Parallelism

并行只用于真正独立的任务。默认最多三个子 Agent，同时满足：

- 不修改相同核心文件或未稳定接口；
- 没有未完成的共享依赖；
- 每个任务有明确文件所有权；
- 合并顺序和冲突责任人已指定；
- 并行收益高于协调和 Review 成本。

写入型核心任务默认串行；只读调查、测试和独立 Review 更适合并行。

## 8. External Side Effects

以下工作需要单独人工确认：

- 选择或切换真实视觉/TTS Provider；
- 使用付费凭据、提高预算或触发实际费用；
- 生产部署、不可逆迁移、敏感数据、认证授权或隐私变更；
- 大规模重写、主要技术栈切换或 Goal 方向变化。

Fake Adapter、离线 Fixture 和本地 dry-run 可以自主运行，但它们只能证明接口和控制流，不证明真实 Provider 可用。

## 9. Goal-level Acceptance

所有 Issue 完成后，主控执行一次跨模块 Review，至少验证：

- 用户主流程和 Mandatory Gates；
- Artifact lineage、恢复和持久化；
- 一个真实 Provider 路径和可播放输出；
- 本地工作台与导出包；
- 测试、运行、失败路径、已知限制和回滚；
- 文档与最终实现一致。

最终状态：`GOAL_APPROVED`、`GOAL_APPROVED_WITH_FOLLOW_UPS`、`GOAL_BLOCKED`、`GOAL_REJECTED`、`ESCALATE_TO_HUMAN`。
