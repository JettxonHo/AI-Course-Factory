# AI Course Factory Knowledge Video Business Loop Implementation Spec v1.0

## 1. Status and authority

| Field | Value |
| --- | --- |
| Status | **MBL GOAL APPROVED / ACTIVE — B0 COMPLETE; B1 IMPLEMENTATION IN PROGRESS** |
| Product direction | Three-video manual Douyin production/publication/feedback loop approved by Product Owner, 2026-08-27 |
| Exact Goal | Approved by Product Owner, 2026-08-27 |
| Product contract | docs/product/PRD.md |
| System contract | docs/spec/SYSTEM-SPEC.md |
| Planning baseline | main@bd4d44a2e9c710d26aea8c531328ae6ec7fefda4 |
| Planning Issue | #154, exact 15-path B1 readiness implementation |
| Runtime baseline | Python >=3.12,<3.13; no dependency or runtime change in B1 |

S1 Creator Script Package intake is merged through Issue #150 / PR #151 with final 476/476 regression evidence. B0 is merged through Issue #152 / PR #153. Issue #154 authorizes only its exact 15-path source/UI/test/truth-tail change; B2–B6, Provider execution, credentials, fees, media production, publication and broad repository/schema changes remain unauthorized.

## 2. Current implementation audit

| Current implementation | Proposed treatment |
| --- | --- |
| GitHub Source connector and normalized Source Record | Reuse exact identity/commit/blob/unit/locator facts. |
| `_OfflineRuntime` Script author/reviser | Keep only as historical/test compatibility; do not use as the MBL primary authoring path. |
| Script Artifact/Decision repositories | Reuse immutable Version, prior reference and exact approve/reject semantics. |
| Protected H4 and rejected #145/#146/#147 candidates | Preserve untouched; do not copy/cherry-pick/merge as Script input. |
| Creator Script Package intake/Decision | S1 implementation is merged and reusable without reopening its public contract. |
| Six per-Scene narration files | Keep readable for v1.2; do not relabel as Whole Narration. |
| Six fixed ten-second Timeline entries | Keep historical; Acoustic Alignment is the approved time authority. |
| Scene Generation Contract/Handoff Package | Keep reusable lineage/content evidence; no longer primary production plan/package. |
| Creator MP4 importer and committed composition | Keep compatibility/future special-shot seam; park as primary Goal. |
| Artifact/Decision/Task/Workspace repositories | Reuse and deepen only as exact vertical tasks require. |
| Final Decision/Publish Package | Reuse with new exact editorial lineage. |
| Three Simplified-Chinese Jinja views | Reuse as control surfaces; later add publication/feedback to Final without new routes. |

The current merged code implements Creator-authored Script Package intake/re-import and exact creator Decisions. It does not implement the exact Computer Vision source choice, Doubao Whole Narration, short-phrase clock, MBL Visual Edit Plan, approved Xiaotudou family, HyperFrames Sample/full rendering, manual Publication Record or Performance Snapshots. Dirty/rejected candidates do not change that fact.

Knowledge Video Editorial E0/S0/S1 remain accepted foundation. B1 adds only the fixed Computer Vision source seam, three package readiness proof and Xiaotudou future gate context; no B2–B6 code, Provider work or protected-candidate integration is authorized.

## 3. Recommended physical direction

Prefer a small business-loop spine over reinterpretation of Scene/Attempt-shaped contracts:

~~~text
web
  -> application facade
       -> current source/script services
       -> merged creator-script-package intake
       -> authorized Doubao whole-narration boundary
       -> short-phrase clock boundary
       -> visual-edit-plan service
       -> deterministic-render boundary
       -> current final-review/package services
       -> publication/performance intake
  -> current repositories + workspace
~~~

Later Task Contracts choose whether narration/clock/plan/render/publication facts live by deepening existing production/packaging/application modules or one cohesive business-loop module. Issue #152 freezes product semantics, not private class names or public method signatures.

Dependency direction remains:

~~~text
web -> application -> domain/module interfaces
application -> repositories + local execution adapters
local adapters -> explicit external runtimes/tools
~~~

The UI does not see renderer component trees, alignment-library objects, Provider SDK types or repository mechanics.

### Creator Script Package intake boundary

Approved MVP default is one operator-configured directory and one fixed `creator-script.json`, triggered by an explicit same-origin Start-page POST. No browser path, multipart upload, textarea authoring, file manager or common-folder scan is required.

Merged S1 adds one adjacent bounded importer/service, not a Provider or generic registry. Its accepted behavior remains:

- open only the fixed regular non-symlink file under the configured root;
- enforce bounded bytes, UTF-8 JSON, no duplicate object keys, exact schema/version and the closed eight-field top-level set;
- require current `SourceRecord.source_kind=github`; compare package repository URL/identity/commit to the corresponding record fields; derive ordered-unique package `source.files[{path, blob_sha}]` from `SourceRecord.units` in first-occurrence order, rejecting one path with different blobs and without changing SourceRecord shape;
- require ordered top-level claims with exact `{claim_id, statement, evidence_locators}` as the sole evidence owner, with every locator byte-for-byte present in `SourceRecord.units[].locator`;
- require ordered narration units with exact `{unit_id, text, claim_ids}`, at least one resolvable claim per unit and no unit-level locators;
- require creator-declared provenance (`creator_declared_name`, `creator_role`, `tool_name`; optional `tool_version`, `session`, `project`) without authentication claims;
- reject raw prompts, secrets, runtime configuration and implicit/latest references;
- produce one complete immutable Script candidate or a safe failure with no partial Version/state visibility.

Canonical logical equivalence is parsed JSON-value equality: whitespace and object-key order do not participate; array order and every accepted field/nested value do. The accepted Script Artifact payload/provenance persistently contains the complete validated package under exact `script_package`; its public narration/claims/source/provenance projections read from that binding. The first accepted package locks the Task/Source lineage to its stable `script_package_id`. Same ID/same canonical value returns the exact current Script ref and Decision with zero commit. Same ID/changed value commits/selects the next Version with `prior_reference`; the old Decision remains historical, the new Version is unapproved and E1 remains closed. Only invalid, foreign Source/locator or different-ID conflict preserves prior Script selection and Decision unchanged. Restart comparison uses committed `script_package`, not a reconstructed subset; inspection requires no configured directory, while new intake/re-import does.

Validation proves shape, identity, locator membership and reference completeness. It does not infer whether a claim is true, whether a locator supports the narration, or whether teaching quality is good. MBL exposes only exact approve/reject; reject requires bounded context and external revision/re-import. Historical revise remains readable but cannot invoke `_OfflineRuntime` or qualify the current Script.

### Exact first-series source boundary

B1 must add the smallest explicit selection/configuration for `microsoft/AI-For-Beginners/lessons/4-ComputerVision/06-IntroCV/README.md`. The Source connector resolves the current commit/blob/unit locators once and downstream package values bind them exactly. Do not add arbitrary repository/path fields, a GitHub browser, common-folder scan or implicit latest. The three episode packages use distinct stable package IDs and exact lineages over the same acquired Source.

## 4. Whole Narration implementation boundary

The existing LocalNarrationRenderer/GPT-SoVITS code proves historical local runtime preflight and durable AAC output for six Scene tasks. It does not prove the approved Doubao Whole Narration and is not the MBL primary Provider.

B2 must freeze a focused Doubao Speech Synthesis 2.0 / “刘飞 2.0” contract that:

- consumes the exact approved Script Version/text and explicit Provider/voice/language configuration;
- requires Provider/credential preflight plus durable Budget Authorization and claimed Attempt before the first paid call;
- renders the complete narration through one call per accepted attempt;
- validates decodeability, channel/sample-rate policy, duration and safe maximums;
- stores exact input binding before accepting bytes;
- replays accepted bytes without inference;
- fails before downstream Alignment/Plan side effects;
- records exact success/failure/unknown Attempt and charge facts without exposing credentials;
- enforces Episode 1 at most two calls/CNY 2 total with no automatic retry;
- rejects Episodes 2–3 until a later explicit cap authorization.

Do not implement Whole Narration by concatenating per-Scene files or repeated sentence calls. Do not resume/merge the #145 candidate wholesale; start from current main and explicitly reimplement/salvage only reviewed provider-neutral clock concepts.

## 5. Short-phrase clock implementation boundary

B2 must evaluate a local no-credential short-phrase timing runtime against real approved Doubao narration. Selection evidence must include:

- a declared punctuation/whitespace normalization and proof that ordered phrase text covers exact approved narration character-for-character;
- Chinese phrase boundaries defaulting to 5–15 Han characters or an equivalent short phrase, with engine-task evidence and no sentence/paragraph fallback;
- millisecond intervals that are nonnegative, strictly ordered and non-overlapping;
- a continuous clock where first start is `0`, adjacent end/start values are equal and final end equals exact audio duration;
- a declared pause-allocation policy that assigns engine-reported leading/trailing silence and gaps to adjacent phrases;
- bounded runtime/resources for the fixed local Demo;
- safe failure and restart replay;
- human inspectability;
- no claim that confidence metrics equal product approval;
- ASR, when used, supplying timestamp candidates only while displayed text remains exact approved Script narration;
- no requirement for word-level forced alignment.

The chosen runtime remains outside the core dependency set when practical. If text, interval, continuity, exact-duration or derived-SRT validation fails, no accepted Alignment is committed and Visual Edit Plan stays closed. If a library/model must enter pyproject/uv.lock, that is an explicit Task ownership/architecture decision, not incidental installation.

Alignment output becomes the only source for SRT timing and renderer timing. Existing fixed Scene Timeline remains backward-readable but cannot drive v1.3 output.

## 6. Visual Edit Plan implementation boundary

B3 should reuse grounded Script/Knowledge facts and exact Artifact/Decision ownership. The proposed plan payload is provider-neutral and renderer-neutral. It must represent, for each aligned interval:

- exact phrase/alignment identity;
- A-roll/B-roll role and editorial rationale;
- teaching evidence/claim refs;
- explicit selected Creator Static Asset refs or a missing-asset fact;
- overlay copy/placement intent;
- camera, motion, graphics, transition and hold intent;
- continuity/style constraints.

A-roll is limited to the Xiaotudou presenter layer for hooks, transitions, emotion/action and low-information-density delivery. B-roll carries concepts, steps, comparisons, processes, charts, source evidence, screenshots and demonstrations and targets approximately 65–75 percent without becoming a hard renderer quota. Claim-bearing or information-dense ranges default to B-roll unless an exception reason is recorded, and every B-roll range binds exact narration/clock plus teaching evidence/claim rather than decorative filler.

The plan should be one deep immutable Artifact, not a collection of mutable UI rows and not a renderer JSON tree. One exact human Decision gates sample rendering. A later Task must define the smallest additive ApplicationView projection; no professional editing interactions are authorized.

## 7. Static asset boundary

For MBL, Codex ImageGen creates character/illustration/diagram assets outside the application. B3 may add a bounded explicit manifest/import seam only after its Task Contract defines:

- operator-declared directory or exact manifest;
- allowed formats/size limits and decode preflight;
- exact identity/hash/provenance;
- no symlink/path traversal/latest-folder inference;
- atomic acceptance before Artifact/selection mutation;
- no Provider Attempt, credential or application charge.

Reference images and generated media remain outside Git.

Character readiness is two-stage: generate three rough monochrome adult Xiaotudou silhouettes, then commit only the Product Owner-selected model sheet and limited-animation pose family. A-roll may animate blink, head tilt, point, hand raise, small bounce and position shift from fixed assets; no lip sync or video-model redraw. Warm-white/black-line A-roll and charcoal/white/cobalt B-roll remain presentation contracts, not renderer-private guesses.

Future ImageGenerationTask → ImageGenerationResult work requires separate Provider/model/credential/price/cap approval. It must be one small Adapter, not a registry/framework.

## 8. Deterministic renderer boundary

B4 implements HyperFrames behind the same conceptual seam:

**Input:** exact task, Whole Narration, Short-phrase Clock, approved Visual Edit Plan, selected Creator Static Assets, render range and output reference.

**Output:** playable local Sample or Final Video plus exact technical/provenance facts, or one safe failure.

Required behavior:

- argv/shell-disabled local invocation or an equivalently bounded library call;
- no network/provider credentials;
- plan/alignment remain authoritative;
- exact 15–20 second Episode 1 sample containing the 3-second hook, Xiaotudou A-roll, photo-to-pixel B-roll, real narration, canonical subtitles, their transition and representative overlay/motion behavior;
- no full render before exact Sample approval;
- deterministic/idempotent replay for unchanged exact inputs;
- changed alignment/plan/assets conflict or create a new exact version rather than overwrite;
- local FFmpeg normalization/package compatibility;
- native renderer captions/audio cannot replace application-owned Narration/SRT.

Renderer implementation stays behind the boundary. HyperFrames installation, composition code and dependencies are prohibited in B0 and require an approved B4 Task Contract.

## 9. Three-view implementation direction

Keep existing routes and Jinja/vanilla CSS:

1. Start becomes Content & Audio.
2. Review becomes Visual Planning & Production.
3. Final remains Final Review & Delivery and later owns manual Publication/Performance intake.

Route names may remain for compatibility; presentation labels and permitted actions derive from additive exact product facts. Publication and Performance entry must use bounded same-origin POSTs on Final, not a fourth view, frontend framework, client state store, WebSocket, drag-and-drop timeline, dashboard or generic file manager.

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

### Accepted foundation

- E0 complete through Issue #143 / PR #144 at `main@47ac1e3`.
- S0 complete through Issue #148 / PR #149 at `main@597f3a0`.
- S1 Creator Script Package intake complete through Issue #150 / PR #151 at `main@1a769289`, with final full regression 476/476.

These facts remain implemented foundation. The old E1–E4 milestones did not complete and do not authorize resuming their candidates.

### B0 — Business-loop authority rebaseline

Issue #152 owned exactly 11 docs, appended D-012 and recorded the approved MBL Goal; it is complete through merged PR #153. No code/test/runtime/media/external action belonged to B0.

### B1 — Series/source and Creator Package readiness

Issue #154 is the approved bounded implementation candidate. It adds only the exact Computer Vision file selection/acquisition needed for the first series, proves three package contracts can bind its locators and freezes the three-candidate Xiaotudou approval boundary. No generic source browser or character generation is included.

### B2 — Doubao Whole Narration and short-phrase clock

One bounded Issue/PR consumes only exact approved imported Script. It owns Doubao Liu Fei 2.0 adapter/preflight/Budget/Attempt/cap behavior, one-call Whole Narration, continuous short-phrase clock and canonical SRT. Real paid smoke is separately authorized and reported; #145 is not merged wholesale.

### B3 — Visual Edit Plan and creator assets

One bounded Issue/PR owns plan proposal/review, explicit A/B/evidence coverage, Xiaotudou selection/asset family, remaining creator asset readiness and exact Plan Decision. Codex asset creation remains an external creator action with explicit provenance.

### B4 — HyperFrames Sample and full render

One or more bounded Issues may separate adapter evaluation from production only if ownership evidence requires it. The vertical outcome remains an approved exact 15–20 second Sample followed by full deterministic render from unchanged exact inputs.

### B5 — Final, publish-ready package and feedback intake

One bounded Issue/PR owns Product Owner six-dimension Final findings, MP4/SRT/cover/copy/lineage/feedback package, manual Publication Record and 72-hour/7-day Performance Snapshot UI/state. It does not automate Douyin.

### B6 — Real three-episode acceptance

Controller-owned product acceptance produces and manually publishes all three fresh episodes under explicit per-episode paid/publication gates, archives 72-hour/7-day facts and records one continue/change/stop hypothesis. Repository changes, if any, require their own Task Contract; publication/performance evidence stays honest and external-media artifacts remain outside Git.

## 11. Protected H4 branch

The dirty branch codex/141-creator-handoff-h4-acceptance remains at d301efd with six files and Diff SHA f6b6d331a26f5a426566f04c978d1dd3684615cffb0a808f13fbaf145f803171.

B0 Issue #152 used a clean separate worktree at the then-current `origin/main`. B1 Issue #154 uses its own clean worktree at `main@bd4d44a2e9c710d26aea8c531328ae6ec7fefda4`; no file from protected/rejected dirty branches is copied into this candidate. The paused #145 worktree also remains protected with Diff SHA `df724e19daedae3038ed25b1c94e5fa05149cc3cbb88dc0f0f32197d91662e0d`.

Any future salvage requires a separate line-level disposition:

- source-grounded Script/Knowledge experiments: preserved evidence, not the v1.3 primary author/reviser;
- Final nonempty findings and replay behavior: likely reusable;
- Scene-specific camera/Handoff/import behavior and tests: compatibility or parked;
- external six-MP4 H4 execution: parked.

Do not cherry-pick or merge the candidate wholesale before that review.

## 12. Verification strategy

### B0 Issue #152 docs-only integration (historical)

- exact 11-doc ownership and no runtime/test/dependency path;
- exact Chinese Goal equality across Issue #152, `GOAL.md` and the new MBL contract;
- D-012 append-only after D-011, preserving D-008–D-011;
- S1 COMPLETE truth: Issue #150 CLOSED, PR #151 MERGED, `main@1a769289`, 476/476;
- current B0 COMPLETE and B1 IN PROGRESS wording, with B2–B6 implementation unauthorized;
- Episode 1 exact Provider/voice/two-call/CNY 2 cap without any Provider call/credential;
- Episodes 2–3 explicit later fee gates and manual-publication execution gates;
- protected H4/#145 Diff identities unchanged;
- stale-current-authority, publication-completion and performance-claim scans;
- `git diff --check`; no full regression was run for the docs-only B0 milestone (the worker did not run one).

### B1 Issue #154 implementation evidence

- exact 15-path ownership and no application/script-package, connector, schema, Workflow, dependency, CSS, Provider or media edits;
- public RED chronology for the historical source path, fresh Start copy and absent three-root proof;
- fixed Computer Vision source acquisition, exact package source projection/locators and three distinct package IDs;
- restart/replay from each fresh root with zero duplicate Script Version, Decision, Budget Authorization or Provider Attempt writes;
- source-only `script_review / approve_script` gate with no fabricated Product Owner Decision;
- fixed three-candidate Xiaotudou boundary visible as future context only, with no asset creation/import/approval;
- focused compatibility, compileall, `git diff --check` and exact ownership/prohibited scans; final full regression, live GitHub smoke, browser acceptance and merge remain controller-owned.

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
| Paid Whole Narration | exact Script/Provider/voice/Budget/Attempt/cap binding, real audio, no automatic retry, failure before downstream state, restart no call |
| Short-phrase clock | normalized character-for-character text coverage, 5–15-character default phrase granularity, contiguous non-overlapping `0`-to-duration clock, SRT binding, human inspection |
| Visual Edit Plan | shot/range A/B rationale, information-dense B-roll default, evidence/assets, exact Decision, replay |
| Xiaotudou assets | three candidates, exact Product Owner selection, one fixed model/pose family, decode/provenance/replay |
| Renderer | required hook/A-roll/photo-to-pixel B-roll/real narration/subtitle transition sample, sample-before-full denial, exact inputs, playable output, idempotent replay |
| Final | named-human 1.0x six-dimension findings, exact Version, publish-ready package lineage |
| Publication/feedback | explicit manual execution, exact Final binding, creator-declared labels, 72-hour/7-day snapshots, no API/credential and three-episode cardinality |

## 13. External authorization and stop conditions

No B2–B6 implementation, credential, paid call, ImageGen/HyperFrames media action, deployment or publication is authorized by B1. Stop for:

- B0 not merged or the approved B1 Task Contract scope changing;
- any Doubao call without exact Provider/voice/preflight/Budget/Attempt/cap/credential confirmation;
- any Episode 2–3 paid call without its later cap;
- clock/renderer choice requiring unapproved cloud/model/dependency effects;
- generic Provider registry or frontend stack rewrite;
- professional editor/fourth view;
- broad Artifact/Workflow/schema rewrite;
- Douyin credential/API/automation, publication without explicit confirmation or fabricated performance;
- loss/overwrite of protected H4/#145/#146/#147 candidates;
- weakening Source/Script/Clock/Sample/Final/Publication exact gates.

Issue #152 used no worker. Issue #154 uses the exact `luna-worker` route after startup approval; final full regression, real boundary evidence, browser review and merge remain owned by the main controller.
