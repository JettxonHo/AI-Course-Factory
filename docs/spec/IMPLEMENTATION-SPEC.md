# AI Course Factory Knowledge Video Editorial Implementation Spec v1.3

## 1. Status and authority

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE GOAL — E0 DOCS ONLY; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Approved by Product Owner, 2026-08-24 |
| Exact Goal | Approved by Product Owner on 2026-08-24 |
| Product contract | docs/product/PRD.md |
| System contract | docs/spec/SYSTEM-SPEC.md |
| Planning baseline | main@d301efd8494029e8b8eae5001050974a67778937 |
| Planning Issue | #143, docs-only |
| Runtime baseline | Python >=3.12,<3.13; existing external GPT-SoVITS Python 3.11 boundary |

No source, UI, test, dependency or runtime change is authorized by this candidate.

## 2. Current implementation audit

| Current implementation | Proposed treatment |
| --- | --- |
| GitHub Source connector, Knowledge claims and Script decisions | Reuse directly. |
| Protected H4 exact-source Script/Storyboard correction | Preserve untouched; later line-level disposition may reuse Source/Script content. |
| Six per-Scene narration files | Keep readable for v1.2; do not relabel as Whole Narration. |
| Six fixed ten-second Timeline entries | Keep historical; Acoustic Alignment becomes the proposed time authority. |
| Scene Generation Contract/Handoff Package | Keep reusable lineage/content evidence; no longer primary production plan/package. |
| Creator MP4 importer and committed composition | Keep compatibility/future special-shot seam; park as primary Goal. |
| Artifact/Decision/Task/Workspace repositories | Reuse and deepen only as exact vertical tasks require. |
| Final Decision/Publish Package | Reuse with new exact editorial lineage. |
| Three Simplified-Chinese Jinja views | Reuse as control surfaces with changed responsibilities, not new routes. |

The current code does not implement Whole Narration, phrase-level alignment, Visual Edit Plan, Sample approval or deterministic editorial rendering. Documentation must not imply otherwise.

`GOAL.md` now records v1.3 as APPROVED / ACTIVE and E0 as docs-only IN PROGRESS. Creator Handoff H4 stays PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE. No E1 code or Luna dispatch is authorized before E0 merge and a separately approved E1 Task Contract.

## 3. Recommended physical direction

Prefer a small editorial spine over reinterpretation of Scene/Attempt-shaped contracts:

~~~text
web
  -> application facade
       -> current source/script services
       -> whole-narration boundary
       -> acoustic-alignment boundary
       -> visual-edit-plan service
       -> deterministic-render boundary
       -> current final-review/package services
  -> current repositories + workspace
~~~

Later Task Contracts choose whether narration/alignment/plan/render live by deepening existing production/packaging modules or one cohesive editorial module. E0 does not freeze directories, class names or public method signatures.

Dependency direction remains:

~~~text
web -> application -> domain/module interfaces
application -> repositories + local execution adapters
local adapters -> explicit external runtimes/tools
~~~

The UI does not see renderer component trees, alignment-library objects, Provider SDK types or repository mechanics.

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

## 10. Proposed delivery sequence

### E0 — Truth rebaseline

Status: **IN PROGRESS / DOCS ONLY** through Issue #143; PR/merge pending.

Integrate the approved exact Goal across GOAL/STATUS/Specs/Decision Log in one nine-doc PR; park Issues #141/#142 with an explicit not-complete disposition after merge; preserve their Diff/evidence.

### E1 — Narrative clock

One Issue/PR for Whole Narration + Acoustic Alignment + canonical SRT through the existing control surface. Use exact Luna only after Task Contract approval. Run a real local narration/alignment smoke separate from fakes.

### E2 — Visual Edit Plan and asset readiness

One Issue/PR for plan proposal/review, creator static-asset manifest/gaps and exact Plan Decision. No renderer implementation or UI redesign beyond required controls.

### E3 — Deterministic sample gate

First a renderer evaluation/Task Contract; then one vertical sample path with exact 15–20 second playback and Sample Decision. HyperFrames remains preferred but evidence, not mention, selects it.

### E4 — Full render, Final Review and Publish

Full render from approved inputs, restart/replay, named-human product review and Publish Package. This milestone owns final browser/product acceptance.

## 11. Protected H4 branch

The dirty branch codex/141-creator-handoff-h4-acceptance remains at d301efd with six files and Diff SHA f6b6d331a26f5a426566f04c978d1dd3684615cffb0a808f13fbaf145f803171.

Issue #143 uses a clean separate worktree. No file from the dirty branch is copied into this candidate.

After Goal approval, the main controller performs a line-level disposition:

- source-grounded Script/Knowledge improvements: likely reusable;
- Final nonempty findings and replay behavior: likely reusable;
- Scene-specific camera/Handoff/import behavior and tests: compatibility or parked;
- external six-MP4 H4 execution: parked.

Do not cherry-pick or merge the candidate wholesale before that review.

## 12. Verification strategy

### Docs-only Issue #143

- exact nine-file ownership;
- GOAL.md exact approved v1.3 Goal plus E0-only authorization;
- status-language consistency;
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

- E0 not actually merged or the next milestone Task Contract not independently approved;
- alignment/renderer choice requiring unapproved cloud/model/dependency effects;
- generic Provider registry or frontend stack rewrite;
- professional editor/fourth view;
- broad Artifact/Workflow/schema rewrite;
- loss/overwrite of the protected H4 candidate;
- weakening Source/Script/Alignment/Sample/Final exact gates.

Issue #143 integrates E0 documentation only and does not dispatch Luna. After E0 merge, proceed only to E1 planning/startup review.
