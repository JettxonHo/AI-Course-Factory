# AI Course Factory FAST-MVP Implementation Spec v1.1

## 1. Status and Authority

| Field | Value |
| --- | --- |
| Status | Approved FAST-MVP Implementation Baseline |
| Approval | Product Owner, 2026-08-13 |
| Product Contract | `docs/product/PRD.md` |
| System Contract | `docs/spec/SYSTEM-SPEC.md` |
| Accepted local baseline | `main@e155d193032aad6a9c98e1e8cbebd4e10febdbc6` plus Issue #123 acceptance evidence |
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

At `main@72ef53805aa33aa847d35f70d4a36303681ecec1`, the repository already contains:

- public GitHub acquisition, source normalization and grounded Knowledge/Script planning;
- Character, Storyboard, Timeline, Production Request and Budget planning;
- immutable Artifact Versions and SQLite repositories;
- persistent Script/Storyboard/Final decisions, Task projection and workflow checkpoints;
- task filesystem workspace and Provider-attempt ledger;
- provider-neutral Visual/TTS interfaces, deterministic Fake media and claim-gated offline production;
- local FFmpeg Fixture generation/composition and exact media Artifact commits;
- Final Video Review plus deterministic local Publish Package/Manifest;
- the durable F1 application facade and three-view loopback workspace, including one local Scene replacement and package export.

That historical baseline had the reusable provider-neutral interfaces and local Fixture path only. F2A and F2B later added the independently accepted local-import Visual and local GPT-SoVITS adapters. F2.5 merged its presentation-only workspace through Issue #121 / PR #122 at `main@e155d193`.

The merged F2.5 baseline has 414 passing local regression tests. Issue #123 adds a fresh real local end-to-end acceptance record; neither result proves a cloud Visual/TTS Provider path, deployment or adoption.

## 4. Accepted Vertical Product Boundary

F2A local-import Visuals, F2B local GPT-SoVITS, the F2.5 Warm Editorial workspace and the F3 browser acceptance are independently accepted for the fixed local Demo. Automatic cloud Providers, deployment, multiple tasks/users and general production operations remain outside this implementation baseline.

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

### F2A — Explicit Desktop ImageGen local visual bridge

Issue #117 keeps image generation outside the application. The operator passes `--visual-import-dir`; the adapter accepts only the six exact initial PNG/JPEG names, decodes all six before any attempt/workspace/Artifact side effect, and uses fixed shell-disabled FFmpeg/ffprobe conversion to H.264 `yuv420p` 540x960 24fps MP4. Budget approval still gates conversion, while the ledger provider token is a safe local-import marker and the charge remains zero. Scene 2 replacement requires only `scene-2-replacement.png`, reuses the predecessor voice and audio/master references, rebuilds stale video, and leaves other Scene selections unchanged. Restart and package replay must avoid reconversion and include additive honest source attribution. F2A was independently reviewed and merged through PR #118 at `b2642c1`; the candidate-time wording above is historical.

### F2B — Local GPT-SoVITS v2 TTS Adapter

Issue #119 added one explicit local GPT-SoVITS v2 adapter behind the existing VoiceGenerator seam. It uses an external Python 3.11/repository/model cache and fixed synthetic Serena reference, invokes the official CLI with shell disabled, normalizes AAC/m4a locally, records six zero-charge attempts and adds TTS attribution without changing Budget/Workflow/Artifact contracts. PR #120 merged at `main@65ce873` after independent review; F2B is COMPLETE and F2.5 is the separate presentation milestone below.

### F2.5 — Warm Editorial Production Desk

Issue #121 upgrades only the existing three Jinja views and local stylesheet. It adds a semantic three-stage progress track, task/stage/next-action hierarchy, compact provenance, native details prompt cards, a Review decision zone/storyboard grid, and a Final 9:16 player with a sticky desktop decision rail and mobile one-column layout. A local text SVG favicon and CSS-only 150–250ms polish are included. Existing routes, view kinds, POST actions/field names, media endpoints, autoescape, same-origin checks, security headers and provider/fee/provenance facts remain unchanged. No application/domain/repository/production/packaging changes, JavaScript, SPA, external assets, editor or upload manager are authorized.

F2.5 passed focused rendered-HTML/static checks, 1440px/375px browser review, independent Diff review and the 414-test full regression before PR #122 merged. Its evidence remains presentation-only; Issue #123 separately owns F3 runtime acceptance.

### F3 — Real Demo acceptance

Issue #123 ran the fixed Demo through the browser without a product-code correction. The accepted evidence includes Script v2, explicit Budget approval, six imported visuals, six real local GPT-SoVITS narrations, Video v2 after visual-only replacement, two restarts and an exact four-file package. The durable record is `docs/acceptance/FAST-MVP-v1.1-F3-ACCEPTANCE.md`.

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

F2A local-import success proves the accepted creator-supplied visual bridge and local conversion. Fake success proves offline wiring only. Final acceptance requires the F2A visual result, real/local spoken TTS, real FFmpeg output and a browser-visible playable video.

## 10. External Authorization

The accepted FAST-MVP Goal and PD-002 authorize the completed no-cost local Demo. They do not authorize:

- cloud Provider credentials or calls;
- using credentials or incurring fees;
- increasing a cost/attempt cap;
- deployment, publication or sensitive data use.

F3 acceptance does not authorize Provider credentials, fees, deployment, publication or a broader product scope.
