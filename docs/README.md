# Documentation Map

## 1. 当前权威真源

| 主题 | 权威文件 | 回答的问题 | 不负责 |
| --- | --- | --- | --- |
| 产品 | [product/PRD.md](product/PRD.md) | 为谁解决什么问题，MVP 做什么，怎样算产品完成 | 技术栈、类、表、开发任务 |
| 系统契约 | [spec/SYSTEM-SPEC.md](spec/SYSTEM-SPEC.md) | Artifact、状态、门禁、模块接口和失败语义 | Python 目录、框架配置、里程碑 |
| 实现 | [spec/IMPLEMENTATION-SPEC.md](spec/IMPLEMENTATION-SPEC.md) | 当前技术栈、代码映射、持久化、Adapter、测试 | 产品范围、Agent 调度 |
| 开发方式 | [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) | Goal、Agent、Issue、分支、PR、Review 和合并 | 产品与系统行为 |
| 当前目标 | [../GOAL.md](../GOAL.md) | 本轮做什么、不做什么、里程碑和停止条件 | 修改 PRD 或 Spec |
| 当前事实 | [STATUS.md](STATUS.md) | 代码、测试、Issue、PR、路由和阻塞的真实状态 | 未来授权 |
| 重要决定 | [decision-log.md](decision-log.md) | 为什么选择或替代一个难逆方向 | 任务流水账 |

## 2. 冲突处理

不同类型的信息不能简单用一条总优先级互相覆盖：

- 产品预期冲突：以 PRD 为准。
- 系统行为或领域术语冲突：以 System Spec 为准。
- 物理实现冲突：以 Implementation Spec 为准。
- 当前是否已经实现：以 Git、代码、测试和 STATUS 的实时复核为准。
- 当前是否允许执行：以已批准 GOAL、Issue/Task Contract 和外部副作用授权为准。
- 新决定改变旧决定：必须写入 decision-log，并明确受影响文件。

聊天消息、Issue、PR 或 Goal 都不能静默扩大 PRD；Implementation Spec 不能改变 System Spec；STATUS 不能授予编码权限。

## 3. 历史材料

以下目录和根文件保留为历史决策、旧基线与交付证据：

- `docs/product/AI_Course_Factory_MVP_PRD_v0.*.md`
- `docs/technical-spec/`
- `docs/implementation-plan/`
- `docs/execution-plan/`
- `docs/implementation-task/`
- `docs/implementation-goal/`
- `docs/governance/`
- `docs/planning/`
- `Phase_0.5_*_Decision_Record_v1.0.md`

它们不得被删除，但自决策 D-002 起不再作为 Codex 日常执行入口。只有当前权威文件明确引用的历史决定继续具有约束力。

工作区中尚未纳入 Git 的五份 Phase 1.5 / W3-T001 规划与派发准备材料属于受保护的在途资产；在 Product Owner 决定归档或提交之前不得覆盖、移动或删除。完整清单见 `STATUS.md`。

## 4. 更新规则

- 产品行为改变：先改 PRD并获得批准，再更新两个 Spec 和 Goal。
- 稳定系统接口改变：先改 System Spec，并在 decision-log 记录原因。
- 物理实现改变但产品行为不变：更新 Implementation Spec。
- 任务推进：更新 GOAL 和 STATUS，不为每一步新建重复治理文档。
- 合并后：同步 STATUS；只有难逆或容易被重新争论的决定才写 decision-log。
