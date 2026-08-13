# AI Course Factory FAST-MVP Implementation Spec v1.1

## 1. Status and Authority

| Field | Value |
| --- | --- |
| Status | Approved FAST-MVP Implementation Baseline |
| Approval | Product Owner, 2026-08-13 |
| Product Contract | `docs/product/PRD.md` |
| System Contract | `docs/spec/SYSTEM-SPEC.md` |
| Code Baseline | `main@5d4cae8bcb45e15cba036c45fc673f6245117a6b` |
| Runtime | Python `>=3.12,<3.13` |
| Supersedes | Implementation Spec v1.0 for daily development |

Prefer connecting the existing implementation into a usable product over refactoring it. A task may change architecture only after it proves the vertical path cannot be completed inside the approved boundaries.

## 2. Runtime Shape

One local process is the target:

```text
Loopback Web Workspace
  -> application facade
      -> current planning/review/task modules
      -> current production/budget/attempt modules
      -> current FFmpeg composer and packaging
      -> SQLite + task filesystem
```

Implementation choices:

- keep Python 3.12, LangGraph, SQLite, filesystem workspace and FFmpeg;
- use server-rendered HTML plus minimal JavaScript;
- prefer FastAPI/Uvicorn/Jinja2 if a small spike confirms clean integration; otherwise choose the smallest equivalent Python HTTP stack and record the decision in the feature PR;
- add only dependencies required by the current vertical Issue;
- keep one composition root that wires real/Fake Adapters explicitly.

No SPA, frontend build system, container platform or cloud deployment is required.

## 3. Current Reusable Implementation

At `main@5d4cae8`, the repository already contains:

- public GitHub acquisition, source normalization and grounded Knowledge/Script planning;
- Character, Storyboard, Timeline, Production Request and Budget planning;
- immutable Artifact Versions and SQLite repositories;
- persistent Script/Storyboard/Final decisions, Task projection and workflow checkpoints;
- task filesystem workspace and Provider-attempt ledger;
- provider-neutral Visual/TTS interfaces, deterministic Fake media and claim-gated offline production;
- local FFmpeg Fixture generation/composition and exact media Artifact commits;
- Final Video Review plus deterministic local Publish Package/Manifest.

The merged baseline has 340 passing local regression tests. This proves substantial offline modules, not a usable workspace, real Visual/TTS output or a real end-to-end product.

## 4. Missing Vertical Product Capabilities

1. One application facade that exposes the current pipeline as task-level commands and views.
2. A local web workspace for input, evidence, approvals, production status, video review, Scene action and export.
3. The smallest durable scene media selection/retry behavior required by that workspace.
4. One real Visual Adapter and one real TTS Adapter selected and separately authorized by the Product Owner.
5. One browser-driven real end-to-end acceptance run.

These gaps define the implementation order. New general repositories, compatibility frameworks or defensive utilities do not precede them.

## 5. Physical Direction

Use existing packages. Add only the following product-facing surface when its milestone begins:

```text
src/ai_course_factory/
├── application/     # deepen into one task-level facade/view model
├── web/             # local routes, templates and small static assets
├── production/      # selected real Visual/TTS adapters; existing orchestration/composition
└── config.py        # explicit local composition and credential validation if needed
```

Dependency direction:

```text
web -> application -> existing domain/workflow interfaces
application -> repositories + orchestrators + packaging
production adapters -> external SDK/HTTP/FFmpeg
```

The UI never reads SQLite directly, invokes an Agent directly or sees Provider SDK types. A new module must own meaningful policy or isolate a real side effect; pass-through wrappers are rejected.

## 6. Workspace Contract

Three views are enough:

1. **Start / Current Task** — fixed Demo source, create/open action and current stage.
2. **Review / Produce** — Script with sources, planning summary, budget/attempt facts, approvals, production progress and actionable failure.
3. **Final / Export** — playable video, six Scene rows, retry/replace action, Final Review and package download/path.

The browser may use normal form posts and server-rendered refreshes. Real-time sockets, drag-and-drop editing and a general dashboard are non-goals.

## 7. Delivery Sequence

### F0 — Close the current media-projection candidate

Issue #110 is allowed one bounded independent review and one full regression run. If the candidate satisfies the accepted Scene selection behavior without requiring an architectural rewrite, merge it. If it needs a second redesign/correction cycle, park it and let F1 implement only the smallest media state needed by the vertical workspace. Do not create a separate status-only PR.

### F1 — Offline usable workspace

One Issue/PR connects the existing Fake/local pipeline through the application facade and three-view web workspace. It must demonstrate: create/open -> Script approval -> planning -> Budget approval -> synthetic production -> playable video -> one Scene action -> Final approval -> export -> restart continuation.

The Scene action may initially use deterministic replacement media if needed; its state contract must remain compatible with the approved System Spec.

### F2 — Authorized real media Adapters

After `PD-001`–`PD-003` are approved, Visual and TTS Adapters may be separate parallel Issues with disjoint file ownership. Each has one Fake-free opt-in smoke test, normalized failure handling, credential preflight and a hard cost/attempt cap. These Issues do not redesign orchestration or UI.

### F3 — Real Demo acceptance

Wire both real Adapters through the same composition root and run the fixed Demo from the browser. Repair only defects that block the acceptance contract. Record the exported package, Provider attempt/cost evidence and known limitations.

## 8. Task Contract Minimum

Every implementation Issue states only:

- user-visible outcome and milestone;
- exact baseline and file/module ownership;
- required existing interfaces and prohibited scope;
- acceptance checks and focused commands;
- external effects/fees, if any;
- escalation conditions.

Avoid freezing private helper names, speculative schema details, line-count caps or exhaustive allowed-file lists unless they protect an observed conflict.

## 9. Test Strategy

During implementation, run the smallest focused behavior and integration tests. Before review/merge, run once:

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

Risk tiers:

| Tier | Applies to | Expected evidence |
| --- | --- | --- |
| A | credentials, paid attempts, workspace paths, destructive writes | happy path, key denial/failure, idempotency or recovery relevant to the risk |
| B | core planning, decisions, Scene selection, composition, export | behavior test plus one cross-module integration |
| C | local UI projection, copy and docs | primary flow/smoke evidence |

Do not require mutation audits, repeated two-instance races, arbitrary corruption injection or future-schema tests by default. Add them only when the task changes that exact risk boundary.

Fake success proves offline wiring only. Final acceptance requires a real Visual result, real spoken TTS, real FFmpeg output and a browser-visible playable video.

## 10. External Authorization

The approved FAST-MVP Goal authorizes F0/F1 offline development. It does not authorize:

- selecting or calling a real Provider;
- using credentials or incurring fees;
- increasing a cost/attempt cap;
- deployment, publication or sensitive data use.

Stop before F2 execution until the Product Owner records `PD-001`, `PD-002` and `PD-003`.
