# AI Course Factory MVP Implementation Boundary Spec v0.1

## Document Status

| Field | Value |
| --- | --- |
| Document | AI Course Factory MVP Implementation Boundary Specification |
| Version | v0.1 |
| Phase | Phase 1.2 Step 6 — Implementation Boundary Design |
| Status | Review Draft |
| Coding | Not Started |
| Implementation Plan | Not Started |
| Last Updated | 2026-08-09 |
| Input Baseline | Technical Spec v0.1 Step 1–5 |
| Next Gate | Product Owner Review；只有收到明确“实施计划”指令后才可进入 Implementation Planning |

### Purpose

本文件定义从已冻结 Architecture Specification 进入未来 Implementation Phase 前必须保持的工程边界。它把 Step 1–5 的逻辑模块、接口与状态语义映射为可实现、可替换、可测试的工程接缝，但不决定代码、目录、框架细节或基础设施产品。

本文件回答：

> 如何把已冻结逻辑架构映射到真实工程环境，同时不让 Framework、Folder、Provider、Storage 或部署方式反向改变产品与架构契约？

### Source of Truth

本文件只使用以下已批准或已冻结输入：

1. [AI Course Factory MVP PRD v0.3 — Approved Baseline](../product/AI_Course_Factory_MVP_PRD_v0.3.md)
2. [Renderer Strategy Revision Addendum v1.0 — Accepted](../architecture/Renderer_Strategy_Revision_Addendum_v1.0.md)
3. [Phase 0.5 Step 1 Decision Record v1.0](../../Phase_0.5_Step_1_Decision_Record_v1.0.md)
4. [Phase 0.5 Step 2 Decision Record v1.0](../../Phase_0.5_Step_2_Decision_Record_v1.0.md)
5. [AI Product Studio Strategy V3](../strategy/AI_Product_Studio_Strategy_V3.md)
6. [AI Course Factory MVP Technical Spec v0.1 — Step 1–5](AI_Course_Factory_MVP_Technical_Spec_v0.1.md)

发生冲突时继续采用：Approved PRD → Accepted Addendum → Decision Records → Strategy → Technical Spec。Step 6 不具有修改 Step 1–5 产品或逻辑架构的权限。

### Frozen Implementation Principles

1. Architecture boundary 由责任、接口、依赖方向和不变量定义，不由文件夹名称定义。
2. MVP 优先采用同一应用运行环境中的逻辑模块，不把模块接口提前实现为 Microservice 或网络协议。
3. Framework、Provider、Storage 与环境配置只能通过 Adapter / Runtime seam 进入系统。
4. Runtime environment 可以变化；Artifact、Workflow、Agent、Skill、Command / Result 契约不得变化。
5. 一个模块应通过小而稳定的接口隐藏其内部复杂度；调用方和测试都只跨同一接口。
6. 物理实现可以重构，只要稳定接口、依赖方向和行为不变量保持不变。
7. 没有 Product Owner 的明确实施授权，不创建代码、Issue、Branch 或 PR。

## 1. Implementation Architecture Overview

### 1.1 Mapping Principle

Step 6 使用以下三层映射：

~~~text
Frozen Logical Module
    ↓ owns
Stable Implementation Interface / Seam
    ↓ realized by
Runtime Component and replaceable Adapter
~~~

- **Logical Module** 定义业务责任和不拥有的责任。
- **Implementation Interface / Seam** 定义调用方必须知道的最小契约、错误语义、顺序约束和依赖方向。
- **Runtime Component** 承载实现，可以与其他模块同进程，也可以在未来重新部署；部署位置不是当前架构契约。

### 1.2 MVP Runtime Shape Decision

MVP 的默认实现形态是：

> 一个模块化 Application Runtime，内部保持 Step 1–5 的逻辑接口与责任分离。

这意味着：

- Application、Workflow、Agent、Knowledge、Production、Artifact 与 Packaging 默认可以在同一运行环境内协作。
- LangGraph 是 Workflow 的运行时实现边界，不成为整个产品架构。
- Provider 与 Storage 通过可替换 Adapter 注入。
- 逻辑模块不等于独立进程、独立部署或远程服务。
- MVP 不引入 Microservice、Event Bus、Distributed Worker Platform 或 Dynamic Workflow Builder。

如果未来部署拓扑改变，只能替换实现或 Adapter；不得改变 Command、Artifact Reference、Production Request、Agent Task、Skill Result / Failure 或 Workflow Gate 语义。

### 1.3 Logical-to-Implementation Mapping

| Frozen Logical Module | Stable Implementation Interface / Seam | Runtime Component | May Vary Without Architecture Change |
| --- | --- | --- | --- |
| Application Layer | Application Command / Query interface；只提交 Workflow Command、读取受控 projection。 | Artifact-centric Single Task Workspace runtime。 | UI framework、rendering technology、local or hosted shell。 |
| Workflow Orchestration Layer | Workflow Command、Transition、Interrupt、Checkpoint / Resume interface。 | LangGraph Runtime Boundary、Workflow Nodes 与 state coordination。 | LangGraph内部 Node 粒度、checkpointer adapter、同步 / 异步执行形式。 |
| Agent Layer | Specialized Agent Task interface；输入 exact Artifact References 与 constraints，输出 Candidate / Review Candidate。 | Knowledge、Content、Production、Reviewer Agent runtimes + Model Runtime Adapter。 | LLM model、runtime provider、prompt implementation。 |
| Knowledge Layer | Source acquisition、normalization 与 provenance interface。 | GitHub Source Connector runtime + Source Normalization capability。 | Connector library、HTTP client、未来获批 source adapter。 |
| Production Layer | Production Execution interface；输入 approved Request + Budget Authorization，输出 standard outcome / refs。 | Production Orchestrator、Production Skills 与 Provider Adapters。 | Omni / TTS SDK、composition implementation、未来获批 renderer adapter。 |
| Artifact Layer | Artifact Commit、exact retrieval、dependency / stale query 与 Impact Preview interface。 | Artifact persistence、version、dependency 与 status projection runtime。 | Local / persistent storage implementation、metadata / blob 内部组织。 |
| Packaging Layer | Packaging interface；输入 approved Video 与 exact delivery refs，输出 Package Candidates / refs。 | Cover、Metadata、Manifest 与 Publish Package assembly runtime。 | Archive/export representation、internal builder implementation。 |

### 1.4 Runtime Support Seams

以下是实现支持接缝，不是新的产品层或 Agent：

| Support Seam | Purpose | Does Not Become |
| --- | --- | --- |
| Runtime Composition Boundary | 在启动时装配 configuration、storage adapters、provider adapters 和 module implementations。 | 业务 Workflow 或 Service Locator。 |
| Configuration Boundary | 读取、验证并分发最小 Runtime Configuration。 | Task / Episode 产品配置或隐式业务状态。 |
| Storage Adapter Seams | 为 Artifact、Checkpoint、Execution Record 提供各自持久化实现。 | 一个混合所有语义的 Generic Store。 |
| Observability Boundary | 记录安全、必要的运行状态与 correlation。 | Artifact、Provider raw payload 或 Agent memory。 |

### 1.5 Implementation Architecture Diagram

~~~mermaid
flowchart TB
    User["AI Creator"]
    App["Application Runtime"]
    WorkflowInterface["Workflow Command / Query Interface"]
    WorkflowRuntime["LangGraph Runtime Boundary"]
    AgentInterface["Specialized Agent Task Interface"]
    AgentRuntime["Four Agent Runtimes"]
    ModelAdapter["Model Runtime Adapter"]
    KnowledgeInterface["Knowledge Source Interface"]
    KnowledgeRuntime["GitHub Connector + Normalization"]
    ProductionInterface["Production Execution Interface"]
    Orchestrator["Production Orchestrator Runtime"]
    Skills["Production Skills"]
    ProviderAdapters["Omni / TTS Adapters"]
    CommitBoundary["Candidate Validation / Commit Boundary"]
    ArtifactInterface["Artifact Commit / Query Interface"]
    ArtifactRuntime["Artifact Runtime"]
    PackagingInterface["Packaging Interface"]
    PackagingRuntime["Packaging Runtime"]
    External["LLM / GitHub / Omni / TTS"]
    ArtifactStorage["Artifact Storage Adapter"]
    CheckpointStorage["Workflow Checkpoint Adapter"]
    ExecutionStorage["Execution Record Adapter"]
    Composition["Runtime Composition Boundary"]

    User --> App --> WorkflowInterface --> WorkflowRuntime
    WorkflowRuntime --> AgentInterface --> AgentRuntime --> ModelAdapter --> External
    AgentRuntime -->|"Knowledge Agent only"| KnowledgeInterface --> KnowledgeRuntime --> External
    WorkflowRuntime --> ProductionInterface --> Orchestrator --> Skills --> ProviderAdapters --> External
    WorkflowRuntime --> PackagingInterface --> PackagingRuntime
    WorkflowRuntime --> ArtifactInterface
    AgentRuntime -->|"Artifact Candidate"| CommitBoundary
    Orchestrator -->|"Media / Failure Candidate"| CommitBoundary
    PackagingRuntime -->|"Package Candidate"| CommitBoundary
    CommitBoundary --> ArtifactInterface
    ArtifactInterface --> ArtifactRuntime --> ArtifactStorage
    WorkflowRuntime --> CheckpointStorage
    Orchestrator --> ExecutionStorage
    Composition -.-> App
    Composition -.-> WorkflowRuntime
    Composition -.-> AgentRuntime
    Composition -.-> Orchestrator
    Composition -.-> ArtifactStorage
    Composition -.-> CheckpointStorage
    Composition -.-> ExecutionStorage
~~~

图中 Runtime Composition Boundary 只负责启动装配。它不参与业务调用，也不能成为跨模块读取配置或定位依赖的全局入口。

## 2. Repository Boundary Design

### 2.1 Repository Design Principle

Repository 必须按逻辑责任与接口所有权组织，而不是按 Framework、Provider 或部署技术组织。物理 Folder 只是当前实现映射，不是 Architecture Contract。

正式规则：

> Repository structure may change without changing architecture boundary.

只要模块责任、stable interface、dependency direction 和不变量保持，重命名 Folder、移动实现或替换 Framework 不构成架构变更。反之，即使 Folder 名称保持不变，若责任或依赖方向改变，仍属于架构变更。

### 2.2 Logical Ownership

| Logical Ownership Area | Owns | Stable Surface Exposed to Other Areas | Internal Details Hidden |
| --- | --- | --- | --- |
| Application ownership | UI interaction、Command submission、read projection。 | Workflow Command / Query。 | UI state、view model、rendering framework。 |
| Workflow ownership | Lifecycle、Gate、Checkpoint、Resume、Continue From Here、selected refs。 | Workflow command handling and control result。 | Graph topology、Node decomposition、runtime callbacks。 |
| Agent ownership | 四个 Specialized Agent 的 task reasoning。 | Agent Task input / Candidate output。 | Prompt composition、model context、runtime conversation。 |
| Knowledge ownership | Source Connector、normalization、provenance acquisition。 | normalized source material / source failure。 | GitHub protocol、HTTP details、repository parsing mechanics。 |
| Production ownership | Orchestrator、Skills、retry / budget execution、failure normalization。 | Production execution outcome。 | Provider SDK、attempt mechanics、branch scheduling。 |
| Artifact ownership | Artifact commit / retrieval、version、dependency、status / stale。 | exact Artifact References and queries。 | persistence format、metadata / blob layout、storage SDK。 |
| Packaging ownership | Final Approval 后的 Cover、Metadata、Manifest、Publish Package assembly。 | Package result / refs。 | archive layout、builder sequence、export mechanics。 |

### 2.3 Physical Structure Rules

未来设计物理 Repository 时必须遵守：

1. 每个逻辑 ownership area 有一个清晰的外部接口；内部实现不通过旁路暴露。
2. Interface 由拥有业务语义的模块定义，不由外部 Adapter 或 Framework 定义。
3. Provider-specific、Storage-specific 与 Framework-specific 内容必须集中在匹配 Adapter / Runtime implementation 内。
4. Runtime Composition 是唯一选择具体 Adapter implementation 的位置；业务模块不自行创建外部依赖。
5. Shared 区域只能保存真正稳定、跨模块且无业务所有权争议的最小概念；不得成为通用杂物区。
6. Artifact logical types、Workflow control types 与 Provider SDK types 不得放入同一个公共模型集合。
7. 测试以模块 interface 为观察面；不得因为测试方便而把内部 seam 扩大成公共 interface。
8. 一处变更若需要多个无关模块同时了解 Provider / Storage 细节，说明 seam 已被破坏。
9. 本文件不规定 Folder 名称、package 名称、Python module、Framework layout 或最终目录树。

### 2.4 Architecture Change Test

| Proposed Change | Architecture Change? | Reason |
| --- | --- | --- |
| 重命名或移动一个内部 Folder，外部 interface 不变。 | No | 物理映射变化。 |
| 替换 local Artifact Storage Adapter，Artifact interface 不变。 | No | Adapter replacement。 |
| 把 Omni response type 暴露给 Workflow。 | Yes，禁止 | Provider detail 穿透稳定 seam。 |
| 让 Agent 直接 Commit Artifact。 | Yes，禁止 | 违反 Agent / Artifact boundary。 |
| 把一个逻辑模块拆成多个 Microservices。 | Yes，需要新决策 | 改变运行与失败边界，非 MVP 默认。 |
| 调整 LangGraph 内部 Node 粒度，Lifecycle / Checkpoint 语义不变。 | No | Workflow implementation detail。 |

### 2.5 Deferred Physical Decisions

以下内容必须等待 Implementation Spec / Implementation Plan：

- 目录树和文件路径
- package / module naming
- language-level import layout
- dependency injection mechanism
- build system、package manager 与 Framework bootstrap
- test file placement

## 3. Dependency Direction Rules

### 3.1 Two Dependency Views

Step 6 区分：

- **Runtime call direction**：一个模块在业务执行时调用哪个 interface。
- **Implementation dependency direction**：哪个 implementation 可以了解哪个 contract 或外部 SDK。

外部 Adapter 实现 core-owned interface，因此 Adapter 可以依赖该 interface 和外部 SDK；core module 不能依赖 Adapter implementation 或 SDK。

### 3.2 Allowed Runtime Call Direction

~~~mermaid
flowchart TB
    Application["Application"]
    Workflow["Top-level Workflow"]
    Agents["Agent Layer"]
    Knowledge["Knowledge Layer"]
    ModelRuntime["Model Runtime Adapter"]
    Production["Production Orchestrator"]
    Skills["Production Skills"]
    Adapters["Provider Adapters"]
    Packaging["Packaging Layer"]
    Artifact["Artifact Interface"]
    External["External Providers"]

    Application --> Workflow
    Application -.->|"read-only projection"| Artifact
    Workflow --> Agents
    Workflow --> Production
    Workflow --> Packaging
    Workflow --> Artifact
    Agents --> Knowledge
    Agents --> ModelRuntime
    Agents -->|"Candidate return path"| Workflow
    Production --> Skills
    Skills --> Adapters
    Adapters --> External
    Production -->|"Candidate / outcome"| Workflow
    Packaging --> Artifact
    Knowledge -->|"Source Connector Adapter"| External
~~~

Artifact Commit 的实际调用可以由 Workflow-owned Commit Node 或其他已批准 Commit boundary 执行；Agent 与 Skill 始终只返回 Candidate / Result。

### 3.3 Allowed Dependencies

| Caller / Implementation | May Depend On | Purpose |
| --- | --- | --- |
| Application | Workflow Command / Query；Artifact read-only projection。 | 提交用户意图与展示权威状态。 |
| Workflow | Agent Task interfaces、Production Execution interface、Packaging interface、Artifact interface、Checkpoint interface。 | 控制阶段、门禁、提交、恢复与选择。 |
| Agent Runtime | Agent Contract、Model Runtime interface；Knowledge Agent 可依赖 Knowledge interface。 | 推理并返回 Candidate。 |
| Knowledge Runtime | Source Connector interface、normalization / provenance rules。 | 获取并规范化 source。 |
| Production Orchestrator | Production Skill interfaces、Artifact Candidate boundary、Execution Record interface。 | 调度生产、重试与结果聚合。 |
| Production Skill | 自身 capability contract；必要时依赖匹配 Provider Adapter interface。 | 单一能力执行。 |
| Packaging Runtime | Artifact query / commit interfaces。 | 读取 approved refs 并提交 package candidates。 |
| Artifact Runtime | Artifact contracts 与 storage adapter interface。 | 持久化、版本、dependency 与 stale。 |
| Provider / Storage Adapter | Core-owned interface + specific external SDK / protocol。 | 隔离外部实现。 |
| Runtime Composition | 所有待装配 interfaces 与 selected implementations。 | 只在启动时连接依赖。 |

### 3.4 Forbidden Dependencies

| Forbidden Dependency | Why Forbidden |
| --- | --- |
| Agent → Workflow | Agent 不拥有 Lifecycle、Gate、Retry、Resume 或下一阶段。 |
| Agent → Production Skill / Provider Adapter | Production Agent 是规划者，不是生产执行入口。 |
| Agent → Artifact Storage implementation | Agent 只能返回 Candidate，不能 Commit 或查询隐式 latest。 |
| Skill → Workflow | Skill 不返回 Transition，也不读取 Workflow State。 |
| Skill → Artifact Storage | Skill 只返回 Result / Failure，不拥有 Artifact Commit。 |
| Adapter → business planning / Workflow logic | Adapter 只翻译协议、验证响应并归一化错误。 |
| Workflow → Provider SDK / provider-specific Prompt | 供应商细节必须停留在 Adapter。 |
| Application → Agent / Skill / Provider | 所有业务动作必须经过 Workflow Command。 |
| Artifact Runtime → Agent / Workflow / Production implementation | Artifact Layer 是底层业务记录模块，不反向编排 producer。 |
| Core module → concrete Storage / Provider implementation | 具体 implementation 只能由 Runtime Composition 注入。 |
| 任意模块 → global mutable Service Locator / config dictionary | 会形成隐式依赖和无法审计的运行时行为。 |

### 3.5 Dependency Invariants

1. Dependency graph 必须保持无环；上层 orchestration 可以调用下层 interface，下层不能反向控制上层。
2. Workflow 是 Agent、Production、Packaging 之间唯一跨阶段协调者。
3. Production Orchestrator 是 Production Skills 的唯一生产域调用入口。
4. Agent、Skill、Adapter 不能推进 Task Lifecycle。
5. Artifact Runtime 不知道 producer 的内部实现。
6. Provider / Storage implementation 只能在 Runtime Composition 被选择。
7. External SDK type、exception 与 response shape 不得跨 Adapter seam。
8. 同一 interface 同时服务 production adapter 与 local test / mock adapter；测试不创建第二套业务契约。
9. 逻辑 module interface 变化必须回到 Technical Spec 审查，不能以“Folder refactor”名义绕过。
10. 不因未来拆分可能性提前加入 network boundary、message contract 或 Event Bus。

## 4. Runtime Environment Boundary

### 4.1 Environment Equivalence Contract

Local Runtime 与 Production Runtime 必须执行同一套：

- Workflow lifecycle 与 Human / Budget Gate 规则
- Agent、Skill、Adapter interfaces
- Artifact identity、version、dependency、status 与 exact-reference rules
- Command / Result、Failure 与 idempotency semantics
- Provider response validation 与 credential isolation requirements

环境之间只替换 Adapter implementation 与 Runtime Configuration。禁止用 local-only shortcut 改写业务流程。

### 4.2 Local and Production Mapping

| Runtime Concern | Local Runtime | Production Runtime | Contract That Must Remain Identical |
| --- | --- | --- | --- |
| Application | Local single-task workspace。 | Deployed single-task workspace。 | Workflow Command / Query。 |
| Workflow | Same LangGraph business graph with development runtime configuration。 | Same approved graph with persistent runtime configuration。 | Lifecycle、Interrupt、Resume、Checkpoint semantics。 |
| Artifact persistence | Local Artifact Storage Adapter。 | Persistent Artifact Storage Adapter。 | Commit、exact retrieval、version、dependency、stale。 |
| Workflow checkpoint | Local Checkpoint Adapter。 | Persistent Checkpoint Adapter。 | Checkpoint / Resume control state。 |
| Execution records | Local Execution Record Adapter。 | Persistent Execution Record Adapter。 | Attempt identity、terminal outcome、replay guard。 |
| LLM / Omni / TTS | Mock / test adapters by default；explicit developer opt-in for paid sandbox use。 | Real approved Provider Adapters。 | Normalized Result / Failure and validation。 |
| GitHub | Public source adapter or controlled fixture adapter。 | Public GitHub Source Connector。 | Source Record、normalization、provenance。 |
| Configuration | Local non-secret defaults + developer secret source。 | Deployment configuration + managed secret source。 | Validated Runtime Configuration categories。 |

### 4.3 Mock and Real Adapter Rule

Mock / fixture adapters make the external seam testable, but they must:

- satisfy the same core-owned interface
- return the same normalized Result / Failure categories
- obey the same attempt, budget and idempotency semantics
- avoid bypassing Artifact Commit、Review 或 Human Gate
- never silently call a real paid Provider

Local Runtime 可以使用可替代 persistence implementation，但不能用 process memory 作为 Artifact、Checkpoint 或 Attempt 的概念定义。

### 4.4 Runtime Consistency Invariants

1. Environment name 不进入 Artifact、Agent、Skill 或 Workflow business contract。
2. 同一个 exact Artifact Reference 在相同 task scope 内具有相同语义。
3. Local-only bypass 不得跳过 Script Review、Budget Approval、Final Review 或 Packaging。
4. Production-only Provider detail 不得进入 core state。
5. 缺少必要 Runtime Configuration 时 fail closed，不自动使用另一个 Provider、Storage 或不受控默认值。
6. 本 Step 不选择 deployment topology、container、cloud、database 或 process manager。

## 5. Configuration Boundary

### 5.1 Configuration Flow

~~~mermaid
flowchart LR
    Environment["Environment Variables / Secret Source"]
    Loader["Configuration Loading Boundary"]
    Validate{"Validate at startup"}
    RuntimeConfig["Validated Runtime Configuration"]
    Composition["Runtime Composition Boundary"]
    ModelRuntime["Model Runtime Adapter"]
    ProviderAdapters["Omni / TTS / GitHub Adapters"]
    StorageAdapters["Artifact / Checkpoint / Execution Storage Adapters"]
    Core["Workflow / Agent / Skill core modules"]

    Environment --> Loader --> Validate
    Validate -->|"Valid"| RuntimeConfig --> Composition
    Validate -->|"Invalid"| Stop["Fail closed before business execution"]
    Composition --> ModelRuntime
    Composition --> ProviderAdapters
    Composition --> StorageAdapters
    Composition --> Core
~~~

Environment Variables 是输入源之一，不是业务模块可随时读取的全局状态。所有配置必须在 Runtime Composition 前完成 validation。

### 5.2 Configuration Categories

| Configuration Boundary | Owns | Consumer | Must Not Change |
| --- | --- | --- | --- |
| Model Configuration | Model provider selection、approved model runtime settings、runtime limits。 | Model Runtime Adapter。 | Agent responsibility、Agent Task contract、Artifact semantics。 |
| Production Provider Configuration | Omni / TTS endpoint、credential association、provider runtime limits。 | Matching Provider Adapter。 | Production Request、Skill contract、Failure categories。 |
| Knowledge Provider Configuration | GitHub access / transport settings for public source retrieval。 | Source Connector Adapter。 | Source Record 与 Knowledge grounding contract。 |
| Storage Configuration | Selected Artifact、Checkpoint、Execution Record adapter settings。 | Matching Storage Adapter。 | Stored concept ownership与 exact-reference semantics。 |
| Application Runtime Configuration | Development mode、safe runtime options、non-business observability settings。 | Runtime Composition / Application runtime。 | Task Lifecycle、Gate、Episode content contract。 |

### 5.3 Access Rules

| Module | May Read Raw Environment / Secret Source? | Receives |
| --- | --- | --- |
| Runtime Composition / Configuration Loader | Yes，作为唯一入口。 | Raw values，随后必须验证。 |
| Model Runtime Adapter | No direct read。 | 最小、已验证的 model runtime configuration。 |
| Provider Adapter | No direct read。 | 匹配 Provider 的最小 configuration / credential handle。 |
| Storage Adapter | No direct read。 | 匹配 Storage 的最小 configuration。 |
| Agent | No。 | Task constraints 与 exact Artifact References。 |
| Skill | No。 | Explicit inputs、Execution Context 与 Constraints。 |
| Workflow | No。 | 已装配 interfaces 与 task control metadata。 |
| Artifact / Packaging | No。 | 已装配 storage / export interfaces。 |

### 5.4 Business Configuration vs Runtime Configuration

以下属于业务事实，不能藏在 Environment Variables：

- Audience、Language、Episode Goal
- Fixed 6 Scene Template selection
- Character v1.0 constraints
- Optional Storyboard Review 是否启用
- selected Artifact Versions
- Budget Approval
- Continue From Here entry / Scene scope

这些信息必须通过 Task Context、Artifact、Approval Record 或 Workflow State 表达。Runtime Configuration 只能决定“用哪个实现运行已批准契约”，不能决定“产品应该做什么”。

### 5.5 Credential and Secret Rules

1. Agent 不读取 environment 或 secret。
2. Skill 不保存或返回 API Key。
3. Provider Adapter 只获得完成调用所需的最小 credential handle。
4. Credential 不进入 Prompt、Artifact、Produced Output Reference、Provider Execution Record、Workflow State、Command Result 或日志。
5. Provider response 与 repository content 均视为 untrusted input，必须在 Adapter boundary 验证。
6. Configuration validation error 必须清理 secret value；不得把 raw value 写入 diagnostics。
7. Local secret file 只能作为未提交的开发输入；本文件不规定具体文件名或 secret product。
8. Provider 配置缺失时不得回退到未经批准的 Provider。

## 6. Storage Boundary Decision

### 6.1 Decision

MVP 冻结三个不同的逻辑 Storage interfaces：

1. Artifact Storage
2. Workflow Checkpoint Storage
3. Execution Record Storage

三者可以在未来的物理实现中共享一个 persistence engine，也可以分开部署，但不得合并为一个无语义的 Generic Store。共享基础设施不等于共享 ownership、contract 或 lifecycle。

### 6.2 Storage Responsibility Matrix

| Storage Interface | Owns | Required Logical Operations | Explicitly Does Not Own |
| --- | --- | --- | --- |
| Artifact Storage | Artifact Versions、payload / metadata association、exact dependencies、provenance、status facts；以及 Artifact Layer 内的 Approval / decision records。 | Immutable commit、exact version retrieval、identity history、dependency query、stale / impact query、record lookup。 | Workflow cursor、LangGraph checkpoint、Provider attempt lifecycle、latest-based business selection。 |
| Workflow Checkpoint Storage | LangGraph control snapshots、pending gate、selected refs、resume cursor、command processing association。 | Save checkpoint、load exact thread checkpoint、resume history、command dedup association。 | Artifact payload、Provider raw response、Agent memory、business version history。 |
| Execution Record Storage | Provider attempt intent、Request Version、Scene scope、Attempt Number、terminal result / failure association。 | Reserve attempt、lookup attempt、record terminal outcome、support replay / reconciliation guard。 | Artifact Version、Human Approval、Workflow Lifecycle、Provider credential。 |

Command Processing Record 属于 Workflow control persistence；Provider Execution Record 属于 Execution Record Storage；Approval Record 属于 Artifact Layer 的 decision-record seam。它们各自保留 Step 5 定义的不同语义，即使底层使用同一持久化产品也不能互相替代。

### 6.3 Artifact Storage Abstraction

Artifact Storage interface 必须隐藏：

- metadata 与大型 media payload 是否使用不同物理介质
- storage key、path、bucket、table 或 collection
- serialization、compression 与 transport
- local 与 production implementation 差异

调用方只依赖 Artifact Identity、exact Version、Artifact Reference、dependency、status 与 commit outcome。Artifact Storage 不负责选择 Workflow 当前版本。

### 6.4 Persistence Ordering

~~~mermaid
flowchart TB
    Candidate["Validated Artifact Candidate"]
    ArtifactCommit["Artifact Storage<br/>idempotent Commit"]
    ArtifactRef["Exact Artifact Reference"]
    WorkflowCheckpoint["Workflow Checkpoint Storage<br/>bind ref and cursor"]
    AttemptIntent["Execution Record Storage<br/>reserve attempt"]
    Provider["External Provider Call"]
    AttemptOutcome["Execution Record Storage<br/>terminal outcome"]
    OutputCandidate["Media / Failure Candidate"]

    Candidate --> ArtifactCommit --> ArtifactRef --> WorkflowCheckpoint
    AttemptIntent --> Provider --> AttemptOutcome --> OutputCandidate --> ArtifactCommit
~~~

逻辑顺序：

1. Candidate Commit 成功并获得 exact Artifact Reference 后，Workflow 才能绑定 Reference 并推进 checkpoint。
2. 外部 Provider 调用前必须先在 Execution Record Storage 建立 attempt identity。
3. 外部调用后必须先保存 terminal execution evidence，再形成 Media / Failure Candidate。
4. Approval Record 成功持久化后，Workflow 才能推进 Human Gate。
5. 具体 transaction、outbox、lock、reconciliation 或跨存储一致性算法留给 Implementation Spec。

### 6.5 Storage Invariants

1. Artifact payload 永不进入 Workflow Checkpoint。
2. Provider raw response 与 credential 永不进入 Artifact Storage 公共语义。
3. Workflow Checkpoint 不成为 Artifact 的第二版本历史。
4. Execution Record 不成为 Scene Clip、Audio 或 Failure Artifact 的替代品。
5. Storage implementation failure 不扩充四类 Product Failure。
6. 所有 Storage Adapter 必须在其 interface boundary 返回一致、可归一化的成功 / 失败语义。
7. 不选择具体 database、object store、filesystem、cloud 或 checkpointer product。

## 7. External Provider Integration Boundary

### 7.1 External Systems

MVP 只有以下已批准外部系统类别：

| External System | Core-owned Interface | Adapter Role | Authorized Caller |
| --- | --- | --- | --- |
| LLM Provider | Model Runtime interface | 映射 Agent inference request、验证 response、归一化 technical failure。 | Four Agent runtimes through Model Runtime Adapter。 |
| GitHub | Knowledge Source Connector interface | 获取 public repository、验证 source、规范化 transport / source errors。 | Knowledge Layer。 |
| Omni | Visual Provider interface | 将 provider-neutral production intent 映射为 Omni-specific request，验证 Scene visual result。 | Visual Generator under Production Orchestrator。 |
| TTS | Voice Provider interface | 将 approved narration execution 映射为 TTS request，验证 Scene Audio result。 | Voice Skill under Production Orchestrator。 |

本 Step 不新增 Provider、Provider Router、automatic failover 或第二个实际 Visual Provider。

### 7.2 Integration Flow

~~~mermaid
flowchart LR
    Core["Core Module"]
    Interface["Core-owned External Interface"]
    Adapter["Selected Adapter"]
    ValidateRequest["Request Mapping and Constraint Check"]
    Provider["External Provider"]
    ValidateResponse["Untrusted Response Validation"]
    Outcome["Normalized Result / Failure"]

    Core --> Interface --> Adapter --> ValidateRequest --> Provider
    Provider --> ValidateResponse --> Adapter --> Outcome --> Core
~~~

Core Module 只能理解内部 interface。Adapter 负责了解 external SDK、protocol、authentication、request / response shape 与 error mapping。

### 7.3 Trust Boundary Rules

1. 所有 external response、GitHub repository content、redirect、callback 与 media metadata 均是不可信输入。
2. Adapter 必须在返回 core 前验证结构、必要内容、scope association 与允许的 output location。
3. External response 中的 instruction-like text 不能覆盖 Product、Workflow、Agent、Skill 或 Artifact contract。
4. Provider exception、SDK object、HTTP response 与 raw error 不得泄漏到 Workflow 或 Artifact。
5. Adapter diagnostics 必须清理 credential、token、signed URL 与敏感 request detail。
6. Provider-specific Prompt 只能存在于受控 Provider Execution boundary；不得成为 Timeline、Production Request 或 LangGraph State。
7. Adapter 不得改变 business intent、Artifact dependencies、Scene scope、Budget Authorization 或 retry policy。

### 7.4 Replacement Rule

替换 External Provider implementation 时必须满足：

- Core-owned interface 不变
- Production Request / Agent Task 语义不变
- normalized Result / Failure 分类不变
- exact Reference、attempt 与 budget rules 不变
- Provider-specific capability 差异不能反向扩大 MVP 功能

若新 Provider 无法满足现有 interface，应先形成架构变更提案，而不是在 Adapter 中静默修改业务语义。

### 7.5 Local Adapter Rule

每个真实 External Adapter 应有一个满足相同 interface 的 local mock / fixture implementation，用于无费用、可重复的边界验证。Mock 只替换外部依赖，不替换 Workflow、Artifact Commit、Budget Gate 或 Review。

### 7.6 stickman-video-director Boundary

stickman-video-director 继续定位为 Director / Prompt Skill：

- 它不是 External Provider。
- 它不是 Renderer。
- 它不能调用 Omni。
- 它不能绕过 Production Orchestrator。
- 它产生的 provider-neutral planning result 必须遵守 Step 3 / Step 4 Candidate 与 Skill Result boundary。

## 8. Development Workflow Boundary

### 8.1 Decision-to-Code Lifecycle

~~~mermaid
flowchart LR
    Decision["Approved Decision Record / PRD"]
    Technical["Approved Technical Specification"]
    Boundary["Approved Implementation Boundary"]
    Plan["Explicitly Authorized Implementation Plan"]
    Task["Bounded Implementation Task"]
    Issue["GitHub Issue"]
    Branch["Task Branch"]
    PR["Pull Request"]
    Review["Contract + Quality Review"]
    Merge["Merge"]

    Decision --> Technical --> Boundary --> Plan --> Task --> Issue --> Branch --> PR --> Review --> Merge
~~~

本图定义未来开发治理顺序，不表示本 Step 已创建任何 Implementation Plan、Issue、Branch、PR 或代码。

### 8.2 Coding Agent Preconditions

任何 Coding Agent 开始修改代码前，必须同时存在：

1. **Approved specification**：明确引用 PRD、Technical Spec 与本 Implementation Boundary 的批准版本。
2. **Explicit coding authorization**：Product Owner 已明确允许进入对应 Implementation task。
3. **Bounded task**：只拥有一个清晰模块或跨模块接缝，不能泛化为“实现整个系统”。
4. **Acceptance criteria**：可观察、可验证，且直接映射 PRD / Technical Spec。
5. **Inputs and dependencies**：明确 exact upstream decisions、required contracts 与外部前置条件。
6. **Non-goals**：明确本任务不得顺带增加的 Agent、Skill、Provider、Feature 或 infrastructure。
7. **Verification requirement**：规定需要提交的测试 / validation evidence，但不在 Step 6 设计具体测试代码。

缺少任一项时，Coding Agent 必须停在 planning / clarification，不得自行补全产品方向。

### 8.3 Bounded Implementation Task Contract

未来每个 Implementation Task 至少说明：

| Task Element | Required Meaning |
| --- | --- |
| Objective | 一个可完成、可验收的工程结果。 |
| Ownership | 明确负责的 logical module / seam；避免多个任务同时修改同一 ownership area。 |
| Baseline References | 对应 PRD AC、Technical Spec section 与 Step 6 invariant。 |
| Allowed Changes | 可修改的责任范围与允许的 implementation decisions。 |
| Forbidden Changes | 不得修改的 contracts、providers、artifact types、gates 与 scope。 |
| Acceptance Criteria | 外部可观察行为与失败语义。 |
| Verification Evidence | Review 时必须提供的检查、测试或运行证据类别。 |
| Handoff | 已完成、未完成、外部依赖与后续任务输入。 |

### 8.4 GitHub Workflow Rules

1. Issue 从 approved bounded task 创建，不从模糊聊天直接创建。
2. 一个 Branch 对应一个 bounded task 或一个明确批准的紧密任务组。
3. PR 必须引用 Issue、specification sections 与 acceptance criteria。
4. PR Review 必须检查 dependency direction、Artifact / State boundary、credentials 与 Provider leakage。
5. Review 不只检查“能否运行”，还检查是否改变 frozen contract。
6. Merge 只发生在 acceptance evidence 完整且无未解决 boundary violation 后。
7. 未批准的 scope expansion 必须回到 planning，不得藏在同一 PR。

### 8.5 AI Agent Development Rules

- AI Agent 只能在任务 ownership 内修改实现。
- Agent 不得为了测试方便暴露内部 seam 或创建 global mutable dependencies。
- Agent 不得自行增加 dependency、Provider、Skill、Agent 或 infrastructure。
- Agent 必须保留用户已有和其他任务的改动，不回滚无关工作。
- Agent handoff 必须以文件、验证结果和剩余风险为证据，不以“看起来完成”作为结论。
- Architecture contract 变更必须先更新并批准 specification；不能先写代码再回填文档。

### 8.6 Current Authorization

当前只授权 Step 6 Review Draft 文档工作：

- Implementation Plan：Not Started
- GitHub Issue：Not Created
- Branch：Not Created
- PR：Not Created
- Coding：Not Started
- Coding Authorization：Not Granted

Product Owner 明确发出“实施计划”指令前，不进入 Implementation Planning。Implementation Plan 获批也不自动等于 Coding Authorization。

## 9. Coding Readiness Checklist

### 9.1 Readiness Status

| Item | Status | Evidence / Blocking Condition |
| --- | --- | --- |
| PRD v0.3 Approved Baseline | Passed | Product baseline 已批准。 |
| Renderer Strategy Revision Addendum | Passed | Prompt + Omni Hybrid Production 已接受。 |
| Step 1 Architecture Boundary | Passed | 七层逻辑架构与模块责任已冻结。 |
| Step 2 Workflow Design | Passed | Lifecycle、Gate、Checkpoint、Resume 与 Production mapping 已冻结。 |
| Step 3 Agent Contract | Passed | 四个 Agent 与 Candidate boundary 已冻结。 |
| Step 4 Skill / Adapter Contract | Passed | Skill、Adapter、Result / Failure 边界已冻结。 |
| Step 5 Artifact / State Model | Passed as Step 6 input | Artifact、Reference、State、Command / Result 逻辑语义已冻结供本 Step 使用。 |
| Step 6 Repository Boundary Design | Review Draft Complete | 等待 Product Owner Review。 |
| Step 6 Dependency Direction Rules | Review Draft Complete | 等待 Product Owner Review。 |
| Step 6 Runtime / Configuration / Storage Boundary | Review Draft Complete | 等待 Product Owner Review。 |
| Step 6 External Provider Boundary | Review Draft Complete | 等待 Product Owner Review。 |
| Step 6 Baseline Conflict Assessment | Passed | 见本文件末尾。 |
| Step 6 Approved Baseline | Pending | Product Owner 尚未批准本 Review Draft。 |
| Implementation Plan | Not Started | 等待明确“实施计划”指令。 |
| Bounded Implementation Tasks | Not Created | 必须由获批 Implementation Plan 产生。 |
| Acceptance Criteria per Task | Not Created | 必须在具体 Implementation Task 中建立。 |
| Coding Authorization | Not Granted | 当前不得开始 Coding。 |

### 9.2 Overall Readiness Decision

**Coding Readiness：Not Ready / Not Authorized。**

Architecture inputs 已足以完成 Implementation Boundary Review Draft，但以下 Gate 尚未满足：

1. Step 6 尚未被 Product Owner 标记为 Approved Baseline。
2. Product Owner 尚未发出“实施计划”指令。
3. 尚无获批 Implementation Plan。
4. 尚无 bounded Implementation Tasks 与 task-level acceptance criteria。
5. 尚无 Coding Authorization。

### 9.3 Step 6 Exit Gate

Step 6 只有在以下条件全部满足后才能退出 Review Draft：

- Product Owner 完成本文件评审。
- Baseline Conflict Assessment 保持 Passed。
- Repository、Dependency、Runtime、Configuration、Storage 与 Provider boundaries 被确认。
- Coding Readiness Checklist 中 Step 6 Approved Baseline 更新为 Passed。
- 文档状态更新为 Approved Baseline。

即使 Step 6 Approved，也只允许等待 Product Owner 的“实施计划”指令；不得自动进入 Coding。

## 10. Explicit Non-goals

Step 6 明确不包含：

- API Design 或 Endpoint
- JSON / Pydantic / TypeScript Schema
- Database Schema、table、index 或 migration
- Code Implementation 或伪实现
- 最终 Repository directory / file structure
- Python module、package 或 Framework folder naming
- LangGraph Node code、reducer 或 checkpointer implementation
- Provider SDK Integration
- Prompt Engineering、system prompt 或 model parameter
- Deployment Script、container、cloud topology 或 infrastructure provisioning
- CI/CD Pipeline
- Testing Implementation 或 test framework selection
- GitHub Issue、Milestone、Branch、PR 或 commit 创建
- Implementation Plan 或任务拆分
- 新 Agent、新 Skill、新 Provider、新 Renderer 或新 Knowledge Source
- Microservice、Event Bus、Distributed Task System、Dynamic Workflow Builder
- Multi Provider Router、automatic failover 或自动发布
- Coding

## Baseline Conflict Assessment

### Assessment Result

**Passed。**

### Cross-check

| Baseline | Assessment |
| --- | --- |
| PRD v0.3 | 未修改产品定位、用户、Demo、MVP scope、Human Gates、Failure types、Packaging 或 acceptance criteria。 |
| Renderer Strategy Revision Addendum | 保留 Prompt + Omni Hybrid Production、provider-neutral Production Request、external Voice / composition 与 replaceable Adapter boundary。 |
| Technical Spec Step 1 | 保留七个逻辑层；Runtime Composition、Configuration 与 Storage Adapters 只是 implementation support seams，不是新增产品层。 |
| Technical Spec Step 2 | 保留 Top-level Workflow 唯一 lifecycle owner；LangGraph 只实现 control flow；Production Orchestrator 仍是 production execution 唯一入口。 |
| Technical Spec Step 3 | 保留 Knowledge、Content、Production、Reviewer 四个 Agent；未增加 Agent，未授予 Provider、Artifact Commit 或 Workflow ownership。 |
| Technical Spec Step 4 | 保留 Skill 单一能力、Result / Failure、Adapter isolation 与 external response validation；未增加 Provider 或 Skill scope。 |
| Technical Spec Step 5 | 保留 immutable Artifact Version、exact Reference、dependency、stale、separate records 与 control-only LangGraph State；未引入 payload duplication。 |

### Historical Decision Handling

旧 Decision Record 中的 deterministic Stickman MVP Renderer 条款继续由 Renderer Strategy Revision Addendum 标记为 Superseded。本文件没有恢复该旧路线。stickman-video-director 仍是 Director / Prompt Skill，不是 Renderer 或 Provider。

### Scope Check

- No product scope expansion
- No new Agent
- No new Skill
- No new Provider
- No Microservice
- No Event Bus
- No Dynamic Workflow Builder
- No code or implementation plan

## Step 6 Completion Check

| Completion Criterion | Result |
| --- | --- |
| Logical Module → Interface / Seam → Runtime Component mapping 已定义。 | Passed |
| Repository logical ownership 与 physical structure 分离。 | Passed |
| Allowed / forbidden dependency direction 与 invariants 已定义。 | Passed |
| Local / Production Runtime contract parity 已定义。 | Passed |
| Model、Provider、Storage configuration boundaries 已冻结。 | Passed |
| Agent / Skill 不读取 environment，credential 不泄漏。 | Passed |
| Artifact、Checkpoint、Execution Record Storage 未混为一个概念。 | Passed |
| LLM、GitHub、Omni、TTS 只通过 Adapter 进入。 | Passed |
| Decision-to-Code workflow 与 Coding Agent preconditions 已定义。 | Passed |
| Coding Readiness Checklist 已完成。 | Passed |
| Explicit Non-goals 已声明。 | Passed |
| Baseline Conflict Assessment。 | Passed |
| 未修改 Step 1–5，未进入 API、Database、Code、Issue 或 Implementation Plan。 | Passed |

## Current Status

~~~text
Phase 1.2 Step 6 — Review Draft Complete
Implementation Plan — Not Started
Coding — Not Started
Coding Authorization — Not Granted
~~~
