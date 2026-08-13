# AI Course Factory System Spec v1.0

## 1. Status and Scope

| Field | Value |
| --- | --- |
| Status | Approved System Baseline |
| Product Input | `docs/product/PRD.md` |
| Current Code Baseline | `main@08085e4` |
| Approved | 2026-08-12 by Product Owner |
| Last Updated | 2026-08-13 |

本文件定义稳定的系统行为、领域语言、模块接口和不变量。它不规定 Python 目录、Web 框架、数据库产品、Provider SDK 或开发任务。

## 2. Canonical Language

| Term | Meaning |
| --- | --- |
| Artifact Candidate | Producer 提交给 Artifact Store 之前的提案；不是持久业务事实。 |
| Artifact Version | Commit 后不可变、可通过 exact Reference 读取的业务事实。 |
| Artifact Reference | `artifact_type + identity + version` 组成的 exact 地址。 |
| Decision Record | Creator 对 exact Artifact Version 的不可变决定。 |
| Workflow State | 当前任务的控制位置、pending gate、selected exact refs 和命令幂等信息。 |
| Provider Execution Record | 一次外部调用的 request representation、attempt、费用和结果；不是核心业务 Artifact。 |
| Scene | 局部审核、执行和重做的最小业务定位单位。 |
| Module | 通过一个 Interface 向调用方提供行为的实现单元。 |
| Interface | 调用者必须知道的完整契约，包括输入、结果、不变量、顺序和失败。 |
| Seam | 可以替换实现而不修改调用方的 Interface 所在位置。 |
| Adapter | 在一个 Seam 上满足 Interface 的具体实现。 |
| Task media projection | Application-owned task read model of selected media Artifact References and their `current\|stale` facts; it is not an Artifact Version or Workflow payload. |
| Scene media selection | Typed selection of one Scene's exact Clip or Audio Artifact Reference and its projection state. |
| Delivery media selection | Singleton selection for Subtitle, logical Master Audio, Video, Artifact Manifest or Publish Package. |

当前代码中的 `ArtifactCommitBoundary`、`ScriptDecisionBoundary` 等类名保留；本文用 “Artifact Store interface” 和 “Decision interface” 描述其系统角色，不要求为术语统一立即重命名代码。

## 3. System Context

```text
Creator
  <-> Local Workspace
        -> Application Module
             -> Workflow Module
             -> Knowledge / Content / Production Agents
             -> Artifact Store
             -> Production Orchestrator
                  -> Visual Provider Adapter
                  -> TTS Provider Adapter
                  -> Media Composer Adapter
             -> Packaging Module
```

只有 Application Module 面向本地工作台提供任务级用例。UI 不直接调用 Agent、Artifact Store、Workflow 或 Provider Adapter。

## 4. Module Responsibilities

### 4.1 Application Module

Interface 提供任务级命令和查询：创建任务、推进阶段、提交 Creator 决定、重做 Scene、查看状态、导出包。

负责：

- 解析命令并加载 exact References；
- 按顺序组合 Workflow、Agent、Artifact、Budget、Production 和 Packaging；
- 在外部副作用前检查 Gate 和 authorization；
- 返回稳定、可展示的结果投影。
- 维护由 Task media projection、scene media selection 和 delivery media selection 组成的任务级媒体读模型；该读模型不取代 Artifact repository 的 immutable Version ownership。

不负责内容生成、Artifact Commit 规则、Provider request 转换或媒体合成。

### 4.2 Workflow Module

Interface 接受 control command，返回 `success | pending | failure` 和 normalized snapshot。

负责：

- 业务阶段、pending gate、allowed actions 和 resume position；
- command identity 与幂等恢复；
- Script、Storyboard、Budget、Final Video gate 的控制顺序；
- 选择要使用的 exact Artifact References。

Workflow State 只保存控制值和 References，禁止保存 Artifact payload、Provider 原始响应或大媒体。

### 4.3 Agent Modules

Knowledge、Content、Production Agent 都是 staged planning modules：

- 接收已经解析并验证的 exact upstream Version；
- 通过 provider-neutral Model Runtime interface 进行受控推理；
- 验证 normalized result；
- 返回 Candidate 或 safe failure。

Agent 不 Commit Artifact、不推进 Workflow、不批准内容、不直接调用媒体 Provider。

Reviewer 是确定性检查与质量判断能力的组合，不拥有 Creator 最终决定。

### 4.4 Artifact Store

Interface 至少支持：

- `commit(candidate) -> exact reference`；
- `get(exact reference) -> immutable version`；
- 按 task/type 查询已存在 Versions；
- 查询 exact dependency 与直接/传递影响；
- 记录 stale/selected 等状态事实而不修改 Version payload。

当前实现只具备内存 `commit/get`。持久查询和影响传播属于 Core MVP 必需扩展。

### 4.5 Decision Module

Interface 对一个 exact Version 进行 assessment，并保存 Creator action。决定和质量判断分离：

- assessment 说明 Hard Block/Warning；
- decision 说明 Creator 的 approve/reject/revise/skip；
- Hard Block 存在时 approve 失败；
- equivalent command 可幂等重放，冲突 command identity 失败。

### 4.6 Budget Module

Interface 根据 Production Request、Provider price snapshot 和 retry policy 返回 Budget Candidate；批准后形成独立 Authorization。

Budget Authorization 必须绑定：

- exact Production Request Reference；
- price snapshot；
- maximum approved amount；
- maximum attempts；
- Creator、time 和 decision identity。

新的 Production Request Version 不继承旧 Authorization。

### 4.7 Production Orchestrator

Interface 接受：

- exact approved Production Request；
- matching valid Budget Authorization；
- explicit Scene scope；
- idempotency key。

返回 normalized production outcome，不返回 Provider SDK 类型。

负责 visual、voice、subtitle、audio 和 media composition 的执行顺序、attempt、预算检查和失败归一化。它不改变 Script/Storyboard/Timeline 意图，不批准预算或最终视频。

### 4.8 Provider and Composer Adapters

- Visual Adapter：内部 visual task -> provider request -> Scene Clip result。
- TTS Adapter：narration -> Scene Audio result。
- Media Composer Adapter：clips + audio + subtitle + timeline -> Video result。

每个 Interface 在 MVP 至少具有 Fake 和 Real/Local 两个 Adapter，因此 seam 是实际可替换点，不是为未来假设而创建的抽象。

### 4.9 Packaging Module

只消费 approved Final Video 和 exact delivery refs，生成可导出的目录/压缩包与 Manifest。它不重新生成内容或媒体，也不发布到外部平台。

## 5. Artifact Model

### 5.1 Required Core Artifacts

| Stage | Artifact |
| --- | --- |
| Source | Source Record |
| Knowledge | Knowledge |
| Content | Course Plan, Episode Plan, Script |
| Creative planning | Character, Storyboard |
| Execution planning | Timeline, Production Request, Production Budget |
| Media | Scene Clip, Scene Audio, Subtitle, Master Audio, Video |
| Quality/control | Review, Failure, Approval/Decision Record |
| Delivery | Artifact Manifest, Publish Package |

Provider prompt/request 和 SDK response 属于 Provider Execution Record，不注册为核心 Artifact。

### 5.2 Version Rules

1. `ArtifactReference` 必须 exact；不提供隐式 latest 读取接口。
2. Version payload 在 Commit 后不可变。
3. 首个 Version 不含 predecessor；修订必须引用当前 exact predecessor。
4. 相同 logical commit 与相同输入返回原 Reference；相同 identity 与不同输入冲突。
5. 上游修订不删除旧下游；旧下游状态变为 stale。
6. selected/current 是任务投影，不是 Artifact Version 可变字段。

### 5.3 Canonical Dependency Chain

```text
Source Record
  -> Knowledge
      -> Course Plan
      -> Episode Plan
          -> Script
              -> Character
                  -> Storyboard
                      -> Timeline
                          -> Production Request
                              -> Production Budget / Authorization
                              -> Scene Clip / Scene Audio / Subtitle
                                  -> Master Audio / Video
                                      -> Review / Approval
                                          -> Manifest / Publish Package
```

Script 直接依赖 Knowledge、Course Plan 和 Episode Plan；Production planning 的每个 Artifact 必须保留回到 approved Script 的可验证 lineage。

### 5.4 Task Media Projection

Task media projection is the application-owned read model for selected media references and their lifecycle facts. It is additive to the existing planning `TaskSnapshot` contract: the ten singleton planning selections and their persisted representation remain backward-readable. The media projection does not change Artifact Version immutability, and it does not copy media payloads into Workflow state.

The public value seam is a typed, frozen/slotted structure with explicit role and discriminator fields. A scene identity is a field in a scene media selection, never an encoded dynamic slot name such as `scene_clip:<scene_id>` or `scene_audio:<scene_id>`. The exact method signatures and physical record shape belong to a later implementation Task Contract.

The projection contains:

- one exact Scene Clip and one exact Scene Audio `ArtifactReference` selection per selected Scene, each marked `current` or `stale`;
- singleton delivery media selections for Subtitle, logical Master Audio, Video, Artifact Manifest and Publish Package;
- no selection when a media result does not yet exist; absence is not a mutable or pseudo-Artifact `missing` status.

The following invariants are stable:

1. Scene order is the exact ordered Scene sequence from the Timeline/Production Request, never lexical Scene ID order.
2. A role/Scene pair is unique within one projection, and each singleton delivery role has at most one selected exact Reference. Duplicate roles, duplicate Scene identities or order drift fail closed.
3. `current|stale` describes the selected-reference fact in the Task projection; it does not mutate the Artifact Version payload.
4. Replacing one Scene's media selection later replaces only that exact Scene role selection. Exact downstream Master Audio, Video, Artifact Manifest and Publish Package selections become stale according to dependency impact; unaffected Scene media remains current.
5. Artifact repository owns immutable Versions; the Task application projection owns selected/current/stale facts; the Provider Attempt Ledger owns execution history and budget enforcement; Decision and Workflow repositories own gates.
6. Final Video decisions remain Decision Records and Workflow checkpoint state, not Artifact selections.

The projection is a separate application/deep seam. A later implementation may use backward-compatible SQLite schema evolution or an additive table, but must choose the smallest verified physical form and preserve the planning snapshot compatibility boundary. This architecture record authorizes neither migration nor retry execution, Provider calls, cost, deployment or UI behavior.

## 6. Task State and Gates

### 6.1 Lifecycle

```text
created
  -> source_ready
  -> knowledge_ready
  -> script_review_pending
  -> script_revision_required | script_approved
  -> production_planning
  -> storyboard_review_pending (optional)
  -> budget_review_pending
  -> production_ready
  -> producing
  -> final_review_pending
  -> revision_required | approved
  -> packaged
  -> completed
```

Failure 不一定是独立 lifecycle state；Module 返回 failure 后，Workflow 保持最近有效 checkpoint 并暴露允许的恢复动作。

### 6.2 Mandatory Gates

| Gate | Target | Required | Allowed Decisions |
| --- | --- | --- | --- |
| Script Review | exact Script Version | Yes | approve, reject, revise |
| Storyboard Review | exact Storyboard Version | Configurable; decision always recorded | approve, reject, revise, skip when disabled |
| Budget Review | exact Production Request + Budget Version | Yes before paid calls | approve, reject |
| Final Video Review | exact Video Version | Yes | approve, reject, revise |

决定必须先持久化，再恢复 Workflow。相同 decision identity 等价重放成功；不同输入复用 identity 失败。

## 7. Commands and Results

Task-level command 最少包含：

- `task_id`；
- `command_id`；
- expected lifecycle/gate；
- target exact Artifact Reference；
- action 与安全的 bounded context；
- external side-effect authorization reference（如适用）。

Public result 统一为：

```text
status: success | pending | failure
snapshot: normalized task projection | none
output_refs: exact references
error_code: stable code | none
error_message: safe message | none
```

原始 exception、credential、Provider body 和本地敏感路径不通过 Application interface 返回。

## 8. Failure Semantics

| Category | Examples | Default Behavior |
| --- | --- | --- |
| validation | invalid reference, lineage mismatch, malformed model result | no commit, no state advance, no external call |
| provider_error | timeout, rate limit, provider 5xx | bounded retry if authorized and budget remains |
| generation_failure | empty/unusable media, refused generation | record attempt; retry or revise provider representation |
| quality_failure | character drift, pacing, subjective weakness | Warning unless required format/identity is broken |
| budget_limit | no approval or next attempt exceeds limit | immediate pause; no call |
| persistence_failure | commit/checkpoint/decision write failed | do not advance; surface recoverable failure |

失败处理必须保留此前有效 Versions 和 attempts。Quality Failure 不触发无限自动重试。

## 9. Idempotency and Side-effect Order

### 9.1 Artifact and Command

- Artifact Commit 使用 caller-provided logical commit identity。
- Workflow/Decision 使用 command identity。
- 重放相同输入返回相同结果；identity 冲突 fail closed。

### 9.2 Provider Attempt

每个外部 attempt 在调用前持久化 planned/started record，调用后更新 terminal outcome。恢复时：

- terminal success 复用结果；
- terminal failure 按 policy 决定是否新建 attempt；
- started 但未知结果不得盲目重复付费调用，必须查询 Provider 或人工确认。

### 9.3 Required Order

```text
validate exact inputs
  -> persist command/authorization check
  -> reserve attempt and budget
  -> external call
  -> persist execution outcome
  -> validate Candidate
  -> commit Artifact Version
  -> advance Workflow
```

任何前置步骤失败都不得执行后续外部副作用。

## 10. Persistence and Recovery Contract

进程重启后必须恢复：

- task projection 和 selected refs；
- Artifact Versions、dependencies 和 status facts；
- Workflow checkpoint；
- Creator decisions 和 Budget Authorization；
- Provider attempts、费用和 output refs；
- export record。

The existing planning `TaskSnapshot` rows remain backward-readable when the additive Task media projection is introduced. The later implementation Task Contract must choose a backward-compatible SQLite schema evolution or additive table and persist typed scene/delivery selections, ordering, uniqueness, `current|stale` facts and dependency impact without changing the ten planning slots. This System Spec records the boundary only; it does not prescribe a migration or method signature.

媒体 blob 不进入 Workflow state 或数据库大字段；只保存受控文件引用、元数据和校验所需信息。

`Continue From Here` 必须先计算并展示 impact，再创建新下游 Versions。MVP 只要求固定 Artifact DAG 的直接与传递影响，不要求通用图数据库。

## 11. Security and Trust

- Source URL、Provider output、模型 output 和上传媒体均是不可信输入。
- GitHub Connector 只允许支持的 public GitHub locator 和安全 path。
- 本地工作台默认只监听 loopback，不提供远程多用户访问。
- Secret 只从运行时环境/本地 secret 配置读取，不写 Artifact、日志、Manifest 或 Git。
- 文件输出被限制在 task workspace；禁止任意路径写入和路径穿越。
- Provider request 只包含完成任务所需的最小内容。

## 12. Verification Contract

每个 Module 必须可以通过自己的 public Interface 测试：

- Unit：输入验证、状态转换、failure 和 invariants。
- Contract：Fake 与 Real Adapter 对同一 Interface 的标准结果语义。
- Integration：Artifact + Workflow + Application 的真实组合。
- End-to-end offline：Fake Provider + 本地 composer 的完整闭环。
- End-to-end real：经授权 Provider、预算、可播放输出和导出包。

最终 real end-to-end 证据不能使用 Fake、Fixture 或手工伪造 output refs。

## 13. Deferred Product Decisions

System contracts 已隔离但不替 Product Owner 选择：

- 真实 Visual Provider 和模型；
- 真实 TTS Provider 和声音；
- Demo 费用与 retry 上限。

这些决定只影响 Adapter、配置和预算，不得改变核心 Artifact、Workflow 或 Application interfaces。
