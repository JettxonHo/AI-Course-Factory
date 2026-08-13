# AI Course Factory Implementation Spec v1.0

## 1. Status and Authority

| Field | Value |
| --- | --- |
| Status | Approved Implementation Baseline |
| Product Contract | `docs/product/PRD.md` |
| System Contract | `docs/spec/SYSTEM-SPEC.md` |
| Code Baseline | `main@08085e4` |
| Language Runtime | Python `>=3.12,<3.13` |
| Approved | 2026-08-12 by Product Owner |
| Last Updated | 2026-08-13 |

本文件把 System Spec 映射到当前仓库、运行时和测试。它不得修改产品范围或系统不变量。当前实现优先演进，不进行无证据的重写。

## 2. Runtime Shape

Core MVP 采用一个本地单进程应用，包含：

```text
Loopback Web Workspace
  -> Application layer
      -> LangGraph workflow
      -> Agent modules
      -> Artifact / Decision / Budget modules
      -> Production Orchestrator
      -> Packaging

Persistence
  -> SQLite metadata/checkpoints/decisions/attempts
  -> task-scoped filesystem media/export blobs
```

选择本地 Web Workspace 而不是 CLI-only：Mandatory Review、来源查看、预算批准、媒体预览和场景级恢复都需要可见交互。选择 server-rendered HTML + 少量 JavaScript，而不是独立 SPA，以减少 MVP 构建、状态同步和部署面。

建议实现栈：

- FastAPI + Uvicorn：本地 HTTP application interface；
- Jinja2 + minimal vanilla JavaScript：工作台；
- SQLite：结构化本地持久化；
- task-scoped filesystem：音视频与导出包；
- LangGraph 1.x：可恢复 Workflow；
- FFmpeg：本地媒体探测和合成；
- Provider SDK/HTTP client：只存在于对应 Adapter 内。

新增依赖必须在对应 Issue 中说明用途、替代方案和验证，不得一次性预装全部未来依赖。

## 3. Current Repository Reality

### 3.1 Implemented

| Package | Current behavior |
| --- | --- |
| `knowledge` | Public GitHub acquisition、exact commit/file identity、source normalization、Source Record Candidate |
| `agents.knowledge_agent` | source-closed Knowledge Candidate、claim/evidence validation |
| `agents.content_agent` | Course/Episode Plan 与 grounded Script Candidate、revision inputs |
| `artifacts.model` | Candidate、exact Reference、immutable Version |
| `artifacts.commit` | in-memory validation、idempotent Commit、exact get、explicit revision |
| `artifacts.script_decision` | Script assessment、Hard Block、Creator decision record |
| `workflow.script_review` | LangGraph mandatory Script Review、interrupt/resume、control-only checkpoint |
| `application.script_review` | exact Script lineage、decision-before-resume application coordination |

当前 66 tests 证明该离线纵向切片成立。它们不证明持久化、本地工作台、Production planning、Provider、媒体或导出存在。

### 3.2 Missing

- persistent Artifact/Decision/Checkpoint repositories；
- task aggregate 和 Application interface；
- Production Agent、Character、Storyboard、Timeline、Production Request；
- Budget 与授权；
- Production Orchestrator、Provider adapters、FFmpeg composer；
- Final Review、stale/impact、scene retry；
- local web workspace 与 packaging；
-真实 Model/Visual/TTS runtime evidence。

### 3.3 Accepted Media Projection Boundary

Decision D-003 (Issue #107, accepted Option A on 2026-08-13) establishes the architecture for the next M3 slice without claiming an implementation. The current planning `TaskSnapshot` remains a ten-singleton contract and must stay backward-readable. The future Task media projection is an additive, application-owned read model with typed **scene media selection** and singleton **delivery media selection** values; it is not a new media blob table by implication and it does not transfer ownership from the existing Artifact, Attempt, Decision or Workflow seams.

This boundary is stable, but no method signatures, filename, schema migration or retry command is frozen here. A later implementation Task Contract must choose the smallest verified physical form behind a separate application module/deep seam and preserve backward-compatible SQLite reads. Until that Issue is separately frozen, the projection and scene retry/replace behavior are not authorized or implemented.

## 4. Package Plan

保留现有包，按真正变化 seam 增量扩展：

```text
src/ai_course_factory/
├── application/
│   ├── task.py                 # task-level commands and queries
│   └── script_review.py        # existing specialized use case
├── artifacts/
│   ├── model.py                # existing immutable values
│   ├── commit.py               # existing in-memory adapter; interface evolves carefully
│   ├── repository.py           # persistent Artifact interface and SQLite adapter seam
│   ├── decisions.py            # generalized exact-version decisions when required
│   └── impact.py               # fixed-DAG stale/impact behavior
├── agents/
│   ├── runtime.py              # provider-neutral model runtime interface
│   ├── knowledge_agent.py
│   ├── content_agent.py
│   └── production_agent.py     # staged planning only
├── workflow/
│   ├── task_workflow.py        # end-to-end control graph
│   ├── script_review.py
│   └── checkpoint.py           # persistent adapter added behind current seam
├── production/
│   ├── model.py                # requests, tasks, outcomes, failures
│   ├── budget.py
│   ├── orchestrator.py
│   ├── interfaces.py           # visual, voice, composer interfaces
│   └── adapters/
│       ├── fake.py
│       ├── visual_<selected>.py
│       ├── tts_<selected>.py
│       └── ffmpeg.py
├── packaging/
│   └── builder.py
├── persistence/
│   ├── sqlite.py
│   └── workspace.py
├── web/
│   ├── app.py
│   ├── routes.py
│   ├── templates/
│   └── static/
└── config.py
```

这是目标责任图，不授权一次性创建全部文件。每个 Issue 只创建支持其行为所需的最小模块。

## 5. Dependency Direction

```text
web -> application -> workflow / agent interfaces / domain modules
workflow -> exact references + application-facing interfaces
agents -> artifact value objects + model runtime interface
production orchestrator -> production interfaces + artifact values
adapters -> external SDK / FFmpeg / SQLite
packaging -> artifact query interface + workspace interface
```

禁止：

- domain/Artifact values 导入 Web、FastAPI、SQLite 或 Provider SDK；
- Agent 导入 Workflow、Artifact Commit implementation 或媒体 Provider；
- Workflow 导入 Provider SDK 或保存 Artifact payload；
- Provider Adapter 决定 budget、retry policy、Artifact status 或 Creator gate；
- UI 直接访问 persistence 或调用 Agent/Provider；
- Application 依赖具体 Fake Adapter。

## 6. Interface Shapes

下面是行为形状，不要求逐字采用类名。

### 6.1 Artifact Repository

```python
class ArtifactRepository(Protocol):
    def commit(self, candidate: ArtifactCandidate) -> ArtifactReference: ...
    def get(self, reference: ArtifactReference) -> ArtifactVersion: ...
    def list_versions(self, artifact_type: str, identity: str) -> tuple[ArtifactReference, ...]: ...
    def dependents(self, reference: ArtifactReference) -> tuple[ArtifactReference, ...]: ...
```

当前 `ArtifactCommitBoundary` 是内存 Adapter。扩展时先提取/确认 Interface contract tests，再增加 SQLite Adapter；不得用 repository wrapper 复制现有规则。

### 6.2 Production Agent

Production Agent 提供 staged methods：

```text
plan_character(approved_script, constraints) -> Candidate | Failure
plan_storyboard(approved_script, character, constraints) -> Candidate | Failure
plan_timeline(approved_script, character, storyboard, gate_decision) -> Candidate | Failure
plan_request(timeline, storyboard, character, approved_script) -> Candidate | Failure
```

每一步只返回 validated Candidate，外部 Application 调用 Artifact Repository Commit 后才能进入下一步。Issue #23 只允许第一步，不应预建其余实现。

### 6.3 Production Interfaces

```python
class VisualGenerator(Protocol):
    def generate(self, task: VisualTask) -> MediaOutcome: ...

class VoiceGenerator(Protocol):
    def synthesize(self, task: VoiceTask) -> MediaOutcome: ...

class MediaComposer(Protocol):
    def compose(self, task: CompositionTask) -> MediaOutcome: ...
```

Interface 只使用内部 immutable values、受控文件 references 和 normalized outcomes，不泄漏 SDK response。

### 6.4 Application Use Cases

工作台通过 task-level commands 操作：

- create task / inspect source；
- generate or revise content；
- decide pending gate；
- start authorized production；
- retry or replace one Scene；
- inspect impact；
- export approved package。

The application boundary also owns the combined Task media projection read model. It exposes typed scene media selections (Clip and Audio) and singleton delivery media selections (Subtitle, logical Master Audio, Video, Artifact Manifest and Publish Package) as exact References plus `current|stale` facts. The projection is a separate application/deep seam from the existing planning `TaskSnapshot`; this document does not freeze its public method signatures. Scene order must come from exact Timeline/Production Request order, not lexical Scene IDs, and a missing selection is represented by absence rather than a mutable `missing` value.

HTTP route 只解析/展示，不承载业务规则。错误通过稳定 code 映射为用户消息。

## 7. Persistence Design

### 7.1 SQLite Owns

- task identity、lifecycle projection 和 selected refs；
- Artifact Version metadata、serialized payload、dependencies、provenance；
- status facts、decisions、budget authorizations；
- Workflow checkpoints；
- Provider execution attempts、cost and output refs；
- export records。

### 7.2 Filesystem Owns

- Scene clip/audio、master audio、subtitle、video；
- provider raw response only when explicitly needed for audit and safely bounded；
- package staging and final export。

默认目录：

```text
.ai-course-factory/
  tasks/<task_id>/
    media/
    provider-records/
    exports/
  course-factory.sqlite3
```

该目录加入 `.gitignore`。所有路径由 Workspace Adapter 根据 task id 生成；调用者不能传入任意输出路径。

### 7.3 Transactions

- Artifact Version、dependencies 和 logical commit index 在一个 transaction 内写入。
- Creator decision/authorization 必须持久化后才恢复 Workflow。
- Provider attempt reservation 和 budget consumption 必须在外部调用前持久化。
- 媒体文件先写临时文件，验证成功后原子移动到 task workspace，再提交 output record。

### 7.4 Task Media Projection Storage Boundary

The existing ten planning selections and their persisted rows remain backward-readable. The additive Task media projection may be represented by backward-compatible SQLite schema evolution or an additive table, chosen by the later implementation Task Contract after verification; this docs task performs no migration. Its persisted values must be frozen/slotted typed records with explicit role/discriminator fields, never dynamic `scene_clip:<scene_id>` or `scene_audio:<scene_id>` strings.

The storage boundary must preserve exact Timeline/Production Request Scene ordering, role/Scene uniqueness, singleton delivery-role uniqueness, absence-as-not-selected, and `current|stale` projection facts. A later Scene retry/replace update may replace only one exact Scene Clip or Scene Audio selection and must mark only exact downstream Master Audio, Video, Artifact Manifest and Publish Package selections stale while leaving unaffected Scene media current. Artifact repository, Attempt Ledger, and Decision/Workflow repositories retain their existing ownerships. No Provider call, cost, deployment, UI, or retry execution is part of this architecture baseline.

## 8. Configuration and Secrets

配置分三类：

- Product config：Demo audience、series、episode、scene template、review enablement。
- Runtime config：database/workspace path、host/port、timeout、FFmpeg path、log level。
- Secret config：Provider keys/tokens；只来自环境或本地未跟踪 secret file。

项目提供 `.env.example` 时只能列变量名和非敏感示例。不得记录真实 key、Provider raw auth error 或 secret-bearing request。

本地服务器默认：

```text
host = 127.0.0.1
remote access = disabled
one active operator
```

## 9. Provider Integration Rules

Provider 选择未批准前只实现 Fake 和 contract tests，不创建猜测性的 SDK Adapter。

每个真实 Adapter Task 必须冻结：

- provider/model/version and official contract；
- credentials and environment variable names；
- supported duration/aspect/media constraints；
- request idempotency/query semantics；
- timeout/retryable error mapping；
- price snapshot source and unit；
- smoke test budget and stop condition。

真实 smoke test 默认关闭，通过显式环境开关运行；CI 不产生费用。

## 10. Media Composition

FFmpeg Adapter 负责：

- probe 输入媒体并验证可读性；
- normalise scene visual/audio duration within approved tolerance；
- concatenate ordered Scenes；
- mix narration and optional audio；
- burn or attach subtitle according to fixed MVP profile；
- produce 9:16 H.264/AAC MP4 and normalized metadata。

调用以参数数组执行，不拼接 shell string。失败返回 safe normalized result并保留诊断引用，不返回无限日志到 Workflow/UI。

## 11. Local Web Workspace

MVP 页面最少包含：

1. Create Task：source URL 和固定 Demo config；
2. Task Overview：lifecycle、pending gate、error、budget 和 available actions；
3. Artifact Viewer：type、exact Version、dependencies、source locators；
4. Script Review：Script、evidence、approve/reject/revise；
5. Production Planning：Character/Storyboard/Timeline/Request/Budget；
6. Production Monitor：Scene attempts、cost、failure、retry/replace；
7. Final Review and Export：video preview、warnings、approve/export。

不实现账号、导航型多任务看板、复杂编辑器或设计系统。优先可验证的主流程、清晰状态和错误恢复。

## 12. Testing Strategy

### 12.1 Required Layers

| Layer | Purpose | External cost |
| --- | --- | --- |
| Unit | Module invariants and failures | None |
| Interface contract | Same semantics across in-memory/SQLite and Fake/Real adapters | None by default |
| Integration | Application + Workflow + Artifact/persistence | None |
| Offline E2E | Local workspace + Fake providers + FFmpeg fixture media | None |
| Provider smoke | One minimal approved call per real Adapter | Explicit opt-in |
| Real acceptance E2E | Full Demo through authorized providers | Explicit budget approval |

### 12.2 Baseline Commands

```bash
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q src tests
git diff --check
```

随着 Web/FFmpeg 引入，Task Contract 必须增加相关启动、HTTP/UI 和 media probe 测试；不得用简单 import 或 HTTP 200 代替行为验收。

### 12.3 Test Quality

- 关键 interface 通过 public behavior 测试，不测试私有实现细节。
- Fake 服从与 Real Adapter 相同的 normalized outcome contract。
- 至少有一次 mutation-sensitive 断言：错误 lineage、未授权预算或错误 gate 必须使测试失败。
- Provider smoke 失败必须区分代码、凭据、配额、模型可用性和外部服务故障。

When the separate media projection implementation Issue is authorized, its focused contract evidence must cover backward-readable planning snapshots, typed role/discriminator validation, exact Timeline/Production Request ordering, role/Scene and singleton uniqueness, absence semantics, current/stale transitions, exact downstream impact and preservation of unaffected Scene selections. This docs-only alignment supplies no such code or test evidence.

## 13. Observability

结构化日志字段最少包括：`task_id`、`command_id`、`stage`、`artifact_ref`、`provider`、`attempt_id`、`result_code` 和 safe duration/cost。

禁止记录：secret、完整 Provider auth response、无边界模型输入、用户本地敏感绝对路径。

STATUS/PR 中的 “passed” 必须说明是 unit、offline、provider smoke 还是真实 E2E。

## 14. Migration from Current Code

1. 不重写已经通过的 Source-to-Approved-Script slice。
2. Issue #23 继续作为 Character planning 的候选首个有界实现，但只有新 Goal 获批、Task Contract 对齐并解除并发文档冲突后才能派发。
3. 在持久化 Task 中用 contract tests 保持当前 Commit/Review 行为，再增加 SQLite Adapter。
4. 先用 Fake providers + FFmpeg 闭合无费用 production，再选择真实 Provider。
5. Web Workspace 只调用 Application layer，不复制既有 Script Review 规则。
6. 每个里程碑以可运行纵向行为结束，不以创建文件或接口数量结束。
7. D-003 is an accepted architecture baseline only. Before implementation, freeze one unique Task Contract for the additive Task media projection, then a separate bounded contract for offline Scene retry/replace; keep Provider, fees, deployment and UI closed.

## 15. Explicitly Deferred

- Cloud database、object storage、queue、distributed workers；
- REST public product interface、multi-client support；
- background job platform；
- provider auto-routing and failover；
- general Artifact graph database；
- plugin/skill platform；
- production deployment topology。

如果某个实现 Task 声称必须先引入上述能力，主控必须要求可验证证据或返回架构审查，不得把未来平台提前塞进 MVP。
