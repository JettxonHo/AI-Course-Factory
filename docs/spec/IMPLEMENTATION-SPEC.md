# AI Course Factory Creator Handoff Implementation Spec v1.2

## 1. Status and Authority

| Field | Value |
| --- | --- |
| Status | Approved implementation direction; milestone coding remains Task-gated |
| Approval | Product Owner, 2026-08-14 |
| Product Contract | `docs/product/PRD.md` |
| System Contract | `docs/spec/SYSTEM-SPEC.md` |
| Planning baseline | `main@d96b091b5d6486129487f5b51b0bb1c43b64639b` (H0 merged through Issue #129 / PR #130); FAST-MVP v1.1 remains complete history |
| Current H1 correction baseline | `main@ce05e778a63f35a3ffd1ff88d0295c2220cab1f4`, branch `codex/133-storyboard-approve-replay` (Issue #133 pending independent review/merge) |
| Goal contract | `docs/goals/CREATOR-HANDOFF-MVP-v1.2-PROPOSAL.md` |
| Runtime | Python `>=3.12,<3.13` |
| Authorization | H0 complete; Issue #131 / PR #132 H1 implementation merged at `main@ce05e77`, with correction Issue #133 active; H2-H4 coding requires a bounded Task Contract per milestone |

Prefer connecting the existing implementation into a usable product over refactoring it. A task may change architecture only after it proves the vertical path cannot be completed inside the approved boundaries.

## 2. Runtime Shape

One local application remains the target; manual Scene generation is an explicit human/external step:

```text
Loopback Web Workspace
  -> application facade
      -> current Source/planning/review modules
      -> approved Scene Generation Contract + Handoff Package
      -> explicit creator Scene clip import
      -> current Task media projection + FFmpeg composer
      -> current Final Review + Publish Package
      -> SQLite + task filesystem

Creator Handoff Package -> manual Jimeng/Kling subscription UI -> generated Scene video files -> explicit import
```

Implementation choices:

- keep Python 3.12, LangGraph, SQLite, filesystem workspace and FFmpeg;
- use server-rendered HTML plus minimal JavaScript;
- prefer FastAPI/Uvicorn/Jinja2 if a small spike confirms clean integration; otherwise choose the smallest equivalent Python HTTP stack and record the decision in the feature PR;
- add only dependencies required by the current vertical Issue;
- keep one composition root; manual external generation is not wired as a Provider;
- preserve the existing external GPT-SoVITS/local FFmpeg boundaries and core dependency set unless an approved vertical Task proves a change is necessary.

No SPA, frontend build system, container platform or cloud deployment is required.

## 3. Current Reusable Implementation

At the current planning baseline `main@d96b091b5d6486129487f5b51b0bb1c43b64639b`, the repository already contains:

- public GitHub acquisition, source normalization and grounded Knowledge/Script planning;
- Character, Storyboard, Timeline, Production Request and Budget planning;
- immutable Artifact Versions and SQLite repositories;
- persistent Script/Storyboard/Final decisions, Task projection and workflow checkpoints;
- task filesystem workspace and Provider-attempt ledger;
- provider-neutral Visual/TTS interfaces, deterministic Fake media and claim-gated offline production;
- local FFmpeg Fixture generation/composition and exact media Artifact commits;
- accepted creator-supplied still-image import for the F2A Preview path and local GPT-SoVITS narration;
- Final Video Review plus deterministic local Publish Package/Manifest;
- the durable F1 application facade and three-view loopback workspace, including one local Scene replacement and package export.

F2.5 merged its presentation-only workspace through Issue #121 / PR #122 at `main@e155d193`. Issue #123 / PR #124 added a partial real local media/recovery record; Issue #125 corrected live GitHub acquisition and passed the 422-test regression. That historical F3 path proves the reusable local path, not creator-generated animated Scene quality, cloud Providers, deployment or adoption; H0 subsequently completed at `main@d96b091` through Issue #129 / PR #130.

## 4. Accepted Vertical Product Boundary

F2A local-import Visuals, F2B local GPT-SoVITS, the F2.5 Warm Editorial workspace and corrected F3 browser acceptance remain complete FAST-MVP v1.1 history. The approved v1.2 Goal reclassifies the F2A still-image composition as Preview Video and adds creator handoff/import boundaries without rewriting those accepted modules. Automatic API Providers, deployment, multiple tasks/users and general production operations remain outside this Goal.

## 5. Physical Direction

Use existing packages. Add only the following product-facing surface when its milestone begins:

```text
src/ai_course_factory/
├── application/     # deepen into one task-level facade/view model
├── web/             # local routes, templates and small static assets
├── production/      # existing TTS/composition plus imported-clip input and Final lineage compatibility
├── packaging/       # existing final Publish Package plus an adjacent Creator Handoff builder
└── artifacts/       # existing generic immutable commit/repository; additive types only if approved
```

Dependency direction:

```text
web -> application -> existing domain/workflow interfaces
application -> repositories + orchestrators + packaging
import boundary -> configured local files + FFmpeg/ffprobe
future API adapters -> external SDK/HTTP only after separate authorization
```

The UI never reads SQLite directly, invokes an Agent directly or sees Provider SDK types. The selected implementation direction adds no generic provider/plugin registry: one deep Handoff builder owns pre-generation package policy and one deep imported-clip module owns untrusted file validation/normalization. A future API adapter consumes the same Scene Generation Contract without changing its lineage or downstream Artifact ownership; it may re-enter the existing Budget/Attempt stage only after separate authorization.

## 6. Workspace Contract

Three views are enough:

1. **Start / Current Task** — fixed Source, grounded Script/Storyboard and current stage.
2. **Review / Produce** — Scene Generation Contract, handoff readiness/download, exact narration/SRT facts and one full-set/re-import action against the configured generated-clips directory.
3. **Final / Export** — composed Final Video, six imported Scene rows, one Scene re-import, human quality findings, Final Review and Publish Package.

The first slice uses one operator-declared generated-clips directory supplied at application startup/configuration. The Review page sends a normal POST with no path or multipart body: the application preflights exact `scene-1.mp4` through `scene-6.mp4` before full import, or exact `scene-2-replacement.mp4` for the bounded re-import. A generic upload/file manager, platform automation, real-time sockets, drag-and-drop editor and general dashboard are non-goals.

## 7. Approved Delivery Sequence

The Goal is active. H0 is complete at `main@d96b091`; Issue #131 / PR #132 is merged at `main@ce05e77`, and H1 remains in progress under correction Issue #133; H2-H4 start only after the preceding milestone and their own bounded Task Contract.

### H0 — Truth rebaseline

Integrate D-008, the exact Goal, canonical terms, eight approved defaults and quality gate. No feature code is part of H0.

### H1 — Scene Generation Contract

After explicit Storyboard approval, commit one immutable ordered contract from exact approved Script/Character/Storyboard/Timeline/Production Request references. Reuse current planning payloads; do not add Provider request bodies or a generic prompt framework.

### H2 — Creator Handoff Package

Add an adjacent deterministic builder rather than a mode on `PublishPackageBuilder`. After non-monetary local runtime/input preflight, it writes an earlier package containing a manifest, readable generation guide, exact narration, canonical SRT/Timeline and optional labelled reference assets. It commits handoff package facts through the existing Artifact repository and Workspace; the manual path creates no Budget Authorization. The H2 Task Contract must preserve idempotent local GPT-SoVITS output/restart without constructing a monetary authorization or weakening the paid-attempt ledger.

### H3 — Imported Scene clip composition

Add one local imported-clip boundary behind the existing composition direction. It atomically preflights exact `scene-1.mp4` through `scene-6.mp4` from the configured directory, binds each clip to one Scene Generation Contract entry, validates/normalizes video and records creator-supplied provenance without an Attempt. Exact `scene-2-replacement.mp4` is the bounded re-import.

H3 is a minimal public-contract expansion, not unchanged reuse: keep `artifact_type=scene_clip`, identity/version and Task selection, but add a discriminated creator-import payload with no attempt/provider and exact Production Request + Scene Generation Contract dependencies. Add an imported-clip composition input/reference variant rather than forging `MediaGenerationResult`. Task lineage accepts both exact legacy generated/Preview and creator-import variants. Before v1.2 Final Review, resolve all selected Clip Versions and require six creator-import variants bound to the same exact Scene Generation Contract. Scene Audio/Master Audio/Subtitle, one-Scene stale impact, the Final Video Decision record and Publish Package remain authoritative.

### H4 — Browser/product-quality acceptance

Exercise one fresh three-view Source-to-Handoff-to-import-to-Final flow with restart and one Scene re-import. Run technical gates plus a full human watch/listen record bound to the exact Final Video Version. Frontend work is limited to handoff/import/readiness and quality evidence; no unrelated redesign.

## 8. Reuse and Compatibility Rules

- Do not change generic Artifact Reference/Version semantics or create implicit latest lookups.
- Do not turn manual subscription work into Provider Attempts or Budget consumption.
- Do not overload `LocalImportedVisualGenerator`; it remains the F2A image-to-Preview implementation.
- Do not add a handoff mode to the existing Final Publish Package; the two packages have different stage eligibility and contents.
- Keep imported clips as existing `scene_clip` Artifact Versions, but use an exact discriminated payload rather than optional attempt/provider fields. The creator-import variant binds Production Request, Scene Generation Contract, Scene, declared filename, provenance, normalized output, media type and duration.
- Expand Task lineage, composition input and the v1.2 Final gate only where required. Legacy generated/Preview payloads remain readable and selectable for v1.1 maintenance but cannot pass the v1.2 final-quality gate.
- Preserve canonical narration/SRT selection even when imported video contains native audio/subtitle streams; v1.2 defaults to stripping/ignoring those tracks for the final mix.
- Keep v1.1 persisted facts readable. A later Task must identify any additive schema/state migration and prove restart compatibility before writing it.

## 9. Verification Strategy

During future implementation, focused tests should cover exact contract lineage, deterministic handoff contents, no-attempt manual provenance, fixed-directory full-set preflight with zero partial side effect, creator-import versus legacy payload compatibility, imported composition without fake attempt/provider, six-Clip same-contract Final gating, one-Scene re-import impact, restart and package replay. The normal full regression remains required once before merge.

Runtime acceptance must separate:

- **technical evidence:** exact references, decoded clips, duration/timeline compatibility, FFprobe, SRT, replay and files;
- **product-quality evidence:** a human watches/listens to the complete video at normal speed and records content correctness, narration naturalness/completeness, visual continuity/action and edit rhythm.

ASR, codec fields, screenshots and isolated frames cannot substitute for the human quality verdict.

## 10. External Authorization

Manual Jimeng/Kling subscription use is outside the application and creates no application Provider Attempt, credential use or charge. This approved Goal does not authorize application-controlled Jimeng/Kling APIs, model selection, credentials, price assumptions, Budget/cap changes, deployment or publication. Any future API adapter must consume the provider-neutral Scene Generation Contract and return to explicit Budget Authorization/Attempt semantics after a separate Product Owner decision.

## 11. Historical FAST-MVP v1.1 Delivery Evidence

The following sequence remains historical implementation evidence. It is not the v1.2 delivery plan.

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

Issue #123 / PR #124 ran the fixed Demo through the browser and recorded partial media evidence but did not prove browser-submitted live GitHub acquisition. Issue #125 / PR #126 completed the correction and repeated the full browser flow from source intake through exact live commit acquisition, Script v2, explicit Budget approval, six imported visuals, six real local GPT-SoVITS narrations, Video v2 after visual-only replacement, two restarts and an exact four-file package. The durable acceptance record is `docs/acceptance/FAST-MVP-v1.1-F3-ACCEPTANCE.md`.

## 12. Task Contract Minimum

Every implementation Issue states only:

- user-visible outcome and milestone;
- exact baseline and file/module ownership;
- required existing interfaces and prohibited scope;
- acceptance checks and focused commands;
- external effects/fees, if any;
- escalation conditions.

Avoid freezing private helper names, speculative schema details, line-count caps or exhaustive allowed-file lists unless they protect an observed conflict.

## 13. Historical Test Strategy

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

## 14. Historical External Authorization

The accepted FAST-MVP Goal and PD-002 authorize the completed no-cost local Demo. They do not authorize:

- cloud Provider credentials or calls;
- using credentials or incurring fees;
- increasing a cost/attempt cap;
- deployment, publication or sensitive data use.

F3 acceptance does not authorize Provider credentials, fees, deployment, publication or a broader product scope.

The approved v1.2 Goal does not authorize unbounded implementation. Issue #131 was the approved first H1 coding Task Contract and is merged; Issue #133 is the bounded H1 HTTP replay correction currently under review. H2-H4 remain separately gated, and all Provider/credential/fee/deployment boundaries remain unchanged.
