# AI Course Factory Knowledge Video Editorial Implementation Spec v1.3

## 1. Status and authority

| Field | Value |
| --- | --- |
| Status | **AMENDED GOAL APPROVED / ACTIVE — S0 DOCS ONLY IN PROGRESS; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Creator-authored Script Package direction approved by Product Owner, 2026-08-24 |
| Exact amended Goal | Approved by Product Owner, 2026-08-24 |
| Product contract | docs/product/PRD.md |
| System contract | docs/spec/SYSTEM-SPEC.md |
| Planning baseline | main@47ac1e3333a2b1f4927baf6bf6de1c44950d9307 |
| Planning Issue | #148, docs-only |
| Runtime baseline | Python >=3.12,<3.13; existing external GPT-SoVITS Python 3.11 boundary |

No source, UI, test, dependency or runtime change is authorized by S0.

## 2. Current implementation audit

| Current implementation | Proposed treatment |
| --- | --- |
| GitHub Source connector and normalized Source Record | Reuse exact identity/commit/blob/unit/locator facts. |
| `_OfflineRuntime` Script author/reviser | Keep only as historical/test compatibility; do not use as the v1.3 primary authoring path. |
| Script Artifact/Decision repositories | Reuse immutable Version, prior reference and exact approve/reject semantics. |
| Protected H4 and rejected #145/#146/#147 candidates | Preserve untouched; do not copy/cherry-pick/merge as Script input. |
| Six per-Scene narration files | Keep readable for v1.2; do not relabel as Whole Narration. |
| Six fixed ten-second Timeline entries | Keep historical; Acoustic Alignment is the approved time authority. |
| Scene Generation Contract/Handoff Package | Keep reusable lineage/content evidence; no longer primary production plan/package. |
| Creator MP4 importer and committed composition | Keep compatibility/future special-shot seam; park as primary Goal. |
| Artifact/Decision/Task/Workspace repositories | Reuse and deepen only as exact vertical tasks require. |
| Final Decision/Publish Package | Reuse with new exact editorial lineage. |
| Three Simplified-Chinese Jinja views | Reuse as control surfaces with changed responsibilities, not new routes. |

The current merged code does not implement Creator-authored Script Package intake, Whole Narration, phrase-level alignment, Visual Edit Plan, Sample approval or deterministic editorial rendering. Dirty/rejected candidates do not change that fact.

E0 is complete through Issue #143 / PR #144. The Product Owner approved the Creator-authored Script Package amended exact Goal, eight defaults and S0 docs-only activation. Issue #148 owns the exact ten-doc authority integration; no S1/E1 code, Luna dispatch or dirty-candidate integration is authorized before S0 merge and a separately approved Task Contract.

## 3. Recommended physical direction

Prefer a small editorial spine over reinterpretation of Scene/Attempt-shaped contracts:

~~~text
web
  -> application facade
       -> current source/script services
       -> bounded creator-script-package intake
       -> whole-narration boundary
       -> acoustic-alignment boundary
       -> visual-edit-plan service
       -> deterministic-render boundary
       -> current final-review/package services
  -> current repositories + workspace
~~~

Later Task Contracts choose whether narration/alignment/plan/render live by deepening existing production/packaging modules or one cohesive editorial module. Issue #148 freezes product semantics, not private class names or public method signatures.

Dependency direction remains:

~~~text
web -> application -> domain/module interfaces
application -> repositories + local execution adapters
local adapters -> explicit external runtimes/tools
~~~

The UI does not see renderer component trees, alignment-library objects, Provider SDK types or repository mechanics.

### Creator Script Package intake boundary

Approved MVP default is one operator-configured directory and one fixed `creator-script.json`, triggered by an explicit same-origin Start-page POST. No browser path, multipart upload, textarea authoring, file manager or common-folder scan is required.

A later S1 Task Contract should add one adjacent bounded importer/service, not a Provider or generic registry. Before any Workspace, Artifact or state write it must:

- open only the fixed regular non-symlink file under the configured root;
- enforce bounded bytes, UTF-8 JSON, no duplicate object keys, exact schema/version and the closed eight-field top-level set;
- require current `SourceRecord.source_kind=github`; compare package repository URL/identity/commit to the corresponding record fields; derive ordered-unique package `source.files[{path, blob_sha}]` from `SourceRecord.units` in first-occurrence order, rejecting one path with different blobs and without changing SourceRecord shape;
- require ordered top-level claims with exact `{claim_id, statement, evidence_locators}` as the sole evidence owner, with every locator byte-for-byte present in `SourceRecord.units[].locator`;
- require ordered narration units with exact `{unit_id, text, claim_ids}`, at least one resolvable claim per unit and no unit-level locators;
- require creator-declared provenance (`creator_declared_name`, `creator_role`, `tool_name`; optional `tool_version`, `session`, `project`) without authentication claims;
- reject raw prompts, secrets, runtime configuration and implicit/latest references;
- produce one complete immutable Script candidate or a safe failure with no partial Version/state visibility.

Canonical logical equivalence is parsed JSON-value equality: whitespace and object-key order do not participate; array order and every accepted field/nested value do. The accepted Script Artifact payload/provenance persistently contains the complete validated package under exact `script_package`; its public narration/claims/source/provenance projections read from that binding. The first accepted package locks the Task/Source lineage to its stable `script_package_id`. Same ID/same canonical value returns the exact current Script ref and Decision with zero commit. Same ID/changed value commits/selects the next Version with `prior_reference`; the old Decision remains historical, the new Version is unapproved and E1 remains closed. Only invalid, foreign Source/locator or different-ID conflict preserves prior Script selection and Decision unchanged. Restart comparison uses committed `script_package`, not a reconstructed subset; inspection requires no configured directory, while new intake/re-import does.

Validation proves shape, identity, locator membership and reference completeness. It does not infer whether a claim is true, whether a locator supports the narration, or whether teaching quality is good. v1.3 exposes only exact approve/reject; reject requires bounded context and external revision/re-import. Historical revise remains readable but cannot invoke `_OfflineRuntime` or qualify the current v1.3 Script.

## 4. Whole Narration implementation boundary

The existing LocalNarrationRenderer/GPT-SoVITS code proves explicit local runtime preflight and durable AAC output for six Scene tasks. It does not prove one continuous narration.

E1 must freeze a focused contract that:

- consumes the exact approved Script Version/text and explicit language/runtime/reference facts;
- renders one continuous audio output;
- validates decodeability, channel/sample-rate policy, duration and safe maximums;
- stores exact input binding before accepting bytes;
- replays accepted bytes without inference;
- fails before downstream Alignment/Plan side effects;
- keeps heavy GPT-SoVITS/PyTorch dependencies outside core Python 3.12;
- creates no Provider Attempt, Budget Authorization or external charge.

Do not implement Whole Narration by concatenating already accepted Scene files and renaming the result unless Product Owner explicitly accepts that product behavior.

## 5. Acoustic Alignment implementation boundary

E1 must evaluate a local no-credential phrase-alignment runtime against real approved narration. Selection evidence must include:

- a declared punctuation/whitespace normalization and proof that ordered phrase text covers exact approved narration character-for-character;
- Chinese phrase boundaries defaulting to 5–15 Han characters or an equivalent short phrase, with engine-task evidence and no sentence/paragraph fallback;
- millisecond intervals that are nonnegative, strictly ordered and non-overlapping;
- a continuous clock where first start is `0`, adjacent end/start values are equal and final end equals exact audio duration;
- a declared pause-allocation policy that assigns engine-reported leading/trailing silence and gaps to adjacent phrases;
- bounded runtime/resources for the fixed local Demo;
- safe failure and restart replay;
- human inspectability;
- no claim that confidence metrics equal product approval;
- ASR, when used, supplying timestamp candidates only while displayed text remains exact approved Script narration.

The chosen runtime remains outside the core dependency set when practical. If text, interval, continuity, exact-duration or derived-SRT validation fails, no accepted Alignment is committed and Visual Edit Plan stays closed. If a library/model must enter pyproject/uv.lock, that is an explicit Task ownership/architecture decision, not incidental installation.

Alignment output becomes the only source for SRT timing and renderer timing. Existing fixed Scene Timeline remains backward-readable but cannot drive v1.3 output.

## 6. Visual Edit Plan implementation boundary

E2 should reuse grounded Script/Knowledge facts and exact Artifact/Decision ownership. The proposed plan payload is provider-neutral and renderer-neutral. It must represent, for each aligned interval:

- exact phrase/alignment identity;
- A-roll/B-roll role and editorial rationale;
- teaching evidence/claim refs;
- explicit selected Creator Static Asset refs or a missing-asset fact;
- overlay copy/placement intent;
- camera, motion, graphics, transition and hold intent;
- continuity/style constraints.

A-roll is limited to the Xiaotudou/IP presenter layer for hooks, transitions, emotion/action and low-information-density delivery. B-roll carries concepts, steps, comparisons, processes, charts, source evidence, screenshots and demonstrations. Claim-bearing or information-dense ranges default to B-roll unless an exception reason is recorded, and every B-roll range binds exact narration/alignment plus teaching evidence/claim rather than decorative filler.

The plan should be one deep immutable Artifact, not a collection of mutable UI rows and not a renderer JSON tree. One exact human Decision gates sample rendering. A later Task must define the smallest additive ApplicationView projection; no professional editing interactions are authorized.

## 7. Static asset boundary

For the MVP, Codex Desktop ImageGen creates character/environment/prop/illustration/diagram/screenshot assets outside the application. E2 may add a bounded explicit manifest/import seam only after its Task Contract defines:

- operator-declared directory or exact manifest;
- allowed formats/size limits and decode preflight;
- exact identity/hash/provenance;
- no symlink/path traversal/latest-folder inference;
- atomic acceptance before Artifact/selection mutation;
- no Provider Attempt, credential or application charge.

Reference images and generated media remain outside Git.

Future ImageGenerationTask → ImageGenerationResult work requires separate Provider/model/credential/price/cap approval. It must be one small Adapter, not a registry/framework.

## 8. Deterministic renderer boundary

E3 evaluates HyperFrames first against the same conceptual seam:

**Input:** exact task, Whole Narration, Acoustic Alignment, approved Visual Edit Plan, selected Creator Static Assets, render range and output reference.

**Output:** playable local Sample or Final Video plus exact technical/provenance facts, or one safe failure.

Required behavior:

- argv/shell-disabled local invocation or an equivalently bounded library call;
- no network/provider credentials;
- plan/alignment remain authoritative;
- exact 15–20 second sample range containing A-roll, B-roll, their transition and representative overlay/motion behavior;
- no full render before exact Sample approval;
- deterministic/idempotent replay for unchanged exact inputs;
- changed alignment/plan/assets conflict or create a new exact version rather than overwrite;
- local FFmpeg normalization/package compatibility;
- native renderer captions/audio cannot replace application-owned Narration/SRT.

Renderer implementation stays behind the boundary. HyperFrames installation, composition code and dependencies are prohibited in Issue #143 and require their own approved Task.

## 9. Three-view implementation direction

Keep existing routes and Jinja/vanilla CSS:

1. Start becomes Content & Audio.
2. Review becomes Visual Planning & Production.
3. Final remains Final Review & Delivery.

Route names may remain for compatibility; presentation labels and permitted actions derive from additive exact product facts. Do not add a fourth route/view kind, frontend framework, client state store, WebSocket, drag-and-drop timeline or generic file manager.

### Required design process

1. collect 8–12 real references from Mobbin/Refero/A1 Gallery;
2. produce 2–3 IA directions;
3. Product Owner chooses 2–3 references and one direction;
4. refine with Minimal.gallery/Lapa Ninja/Fonts In Use;
5. create DESIGN.md from the selected direction;
6. implement only milestone-required behavior;
7. perform an AI-Slop audit.

Component libraries do not replace this design gate. Agent’s Design is for handoff after selection.

## 10. Approved delivery sequence

### E0 — Truth rebaseline

Status: **COMPLETE** at `main@47ac1e3`; Issue #143 CLOSED, PR #144 MERGED.

Integrated the narration-led editorial Goal and honestly parked Issues #141/#142 without marking H4 complete.

### S0 — Script-input truth rebaseline

Status: **IN PROGRESS / DOCS ONLY** through Issue #148; amended exact Goal and defaults approved.

The exact ten-doc candidate records Creator-authored Script Package ownership, intake semantics, options and stop conditions and writes the amended `GOAL.md` **APPROVED / ACTIVE** with S0 **IN PROGRESS**. Only its actual merge permits S0 **COMPLETE** and S1 planning; no status-only PR.

### S1 — Creator Script Package intake

Only after S0 merge and an independently approved S1 Task Contract: implement explicit intake/re-import, exact Source membership preflight, immutable Script Versioning, exact human approve/reject Decision and restart/idempotency evidence.

### E1 — Narrative clock

Consume only the exact human-approved imported Script. One Issue/PR owns Whole Narration + Acoustic Alignment + canonical SRT through the existing control surface. E1 does not write or revise Script. Use exact Luna only after Task Contract approval and run real local narration/alignment smoke separate from fakes.

### E2 — Visual Edit Plan and asset readiness

One Issue/PR for plan proposal/review, creator static-asset manifest/gaps and exact Plan Decision. No renderer implementation or UI redesign beyond required controls.

### E3 — Deterministic sample gate

First a renderer evaluation/Task Contract; then one vertical sample path with exact 15–20 second playback and Sample Decision. HyperFrames remains preferred but evidence, not mention, selects it.

### E4 — Full render, Final Review and Publish

Full render from approved inputs, restart/replay, named-human product review and Publish Package. This milestone owns final browser/product acceptance.

## 11. Protected H4 branch

The dirty branch codex/141-creator-handoff-h4-acceptance remains at d301efd with six files and Diff SHA f6b6d331a26f5a426566f04c978d1dd3684615cffb0a808f13fbaf145f803171.

Issue #148 uses a clean separate worktree. No file from protected/rejected dirty branches is copied into this candidate.

Any future salvage requires a separate line-level disposition:

- source-grounded Script/Knowledge experiments: preserved evidence, not the v1.3 primary author/reviser;
- Final nonempty findings and replay behavior: likely reusable;
- Scene-specific camera/Handoff/import behavior and tests: compatibility or parked;
- external six-MP4 H4 execution: parked.

Do not cherry-pick or merge the candidate wholesale before that review.

## 12. Verification strategy

### Docs-only Issue #148

- exact ten-file ownership including `GOAL.md`;
- exact amended Goal/eight-default/S0-in-progress truth;
- E0-complete and S1/E1-implementation-unauthorized status consistency;
- Creator-package/source-membership/human-semantic-Decision wording consistency;
- stale H3.5/H4 wording scan;
- git diff --check;
- no tests/full regression.

### Later code tasks

- focused behavior tests first;
- integration tests for exact lineage/persistence/local media;
- real local runtime evidence separate from fakes;
- browser evidence for the exact three views;
- full regression once before merge;
- compileall, diff and ownership review;
- named-human product verdict separate from technical checks.

Risk-specific evidence:

| Boundary | Required evidence |
| --- | --- |
| Whole Narration | exact binding, real audio, failure before downstream state, restart no inference |
| Alignment | normalized character-for-character text coverage, 5–15-Han-character default phrase granularity, contiguous non-overlapping `0`-to-duration clock, SRT binding, human inspection |
| Visual Edit Plan | shot/range A/B rationale, information-dense B-roll default, evidence/assets, exact Decision, replay |
| Renderer | A-roll+B-roll+transition sample, sample-before-full denial, exact inputs, playable output, idempotent replay |
| Final | named-human normal-speed watch/listen, exact Version, package lineage |

## 13. External authorization and stop conditions

No video-generation LLM/API, credential, fee/cap, subscription-credit use, deployment or publication is authorized. Stop for:

- S0 not merged or the next milestone Task Contract not independently approved;
- alignment/renderer choice requiring unapproved cloud/model/dependency effects;
- generic Provider registry or frontend stack rewrite;
- professional editor/fourth view;
- broad Artifact/Workflow/schema rewrite;
- loss/overwrite of the protected H4 candidate;
- weakening Source/Script/Alignment/Sample/Final exact gates.

Issue #148 plans the Script-input amendment only and does not dispatch Luna. After approval/merge of a future authoritative Goal amendment, proceed first to one S1 Task Contract; E1 remains paused until an exact approved Script exists through that path.
