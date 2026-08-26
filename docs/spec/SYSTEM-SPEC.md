# AI Course Factory Knowledge Video Business Loop System Spec v1.0

## 1. Status and authority

| Field | Value |
| --- | --- |
| Status | **MBL GOAL APPROVED / ACTIVE — B0 DOCS ONLY IN PROGRESS; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Three-video manual Douyin production/publication/feedback loop approved by Product Owner, 2026-08-27 |
| Exact Goal | Approved by Product Owner, 2026-08-27 |
| Product input | docs/product/PRD.md |
| Planning baseline | main@1a7692894bce6ebea3d88263da67713b426ba59e |
| Goal contract | docs/goals/KNOWLEDGE-VIDEO-BUSINESS-LOOP-MBL-v1.0.md |

This document records the approved MBL ownership and gate direction. Issue #152 changes documentation only; it does not change public interfaces, schemas, stages or dependencies.

Knowledge Video Editorial v1.3 E0/S0/S1 are accepted foundation; S1 is complete through Issue #150 / PR #151 at `main@1a769289` with 476/476 final regression evidence. The Product Owner approved the exact MBL Goal and B0 docs-only activation on 2026-08-27. B1–B6 feature implementation remains unauthorized until B0 merges and a separate milestone Task Contract is approved.

## 2. Architecture principle

Reuse accepted truth owners and extend the editorial spine through real delivery and feedback:

~~~text
Creator
  <-> three-view local SSR workspace
        -> Course Factory Application
             -> exact Source
             -> Creator-authored Script Package intake
             -> immutable Script + Script Decision
             -> authorized Doubao Whole Narration
             -> short-phrase clock -> canonical SRT
             -> Visual Edit Plan + Plan Decision
             -> creator-supplied static assets
             -> deterministic Sample Render + Sample Decision
             -> deterministic Full Render
             -> Final Video Decision
             -> publish-ready package
             -> manual Publication Record
             -> 72-hour / 7-day Performance Snapshots
             -> Content Hypothesis
        -> Artifact/Decision/Task repositories + local Workspace
~~~

The application remains the only business coordinator. The UI never reads repositories or controls renderer/provider SDKs directly. Codex-driven static-asset creation and manual Douyin publication are creator activities. Paid Doubao narration is application-controlled Provider work and must use exact Budget/Attempt ownership.

## 3. Canonical ownership

| Term | Meaning and owner |
| --- | --- |
| Artifact Version/Reference | Immutable business fact/exact address owned by the Artifact repository. No implicit latest. |
| Creator-authored Script Package | Explicit schema-v1 input with exact GitHub Source fields plus a package-owned ordered file projection and one stable `script_package_id`; it is preflight input, not a separate Artifact or Decision. |
| Script Package Claim | Top-level and sole evidence owner with exact `{claim_id, statement, evidence_locators}`; narration units refer to it only by `claim_ids`. |
| Script Version | Immutable Artifact that persistently owns the complete validated canonical package as exact `script_package` binding; narration/claims/source/provenance projections are read from it. |
| Decision | Human action bound to one exact Script, Visual Edit Plan, Sample Video or Final Video target. |
| Task Snapshot | Current product checkpoint, exact selected refs, pending action and recoverable safe failure. |
| Whole Narration | One continuous Doubao Liu Fei 2.0 audio Artifact for the exact approved Script and authorized Attempt. |
| Short-phrase Clock | Ordered short-phrase millisecond Artifact whose normalized text covers exact approved narration character-for-character and whose contiguous intervals span the Whole Narration from `0` to exact duration; sole audiovisual clock and canonical SRT authority. |
| Visual Edit Plan | Ordered editorial Artifact bound to Script/Narration/Alignment; every shot/range records A-roll or B-roll plus rationale, evidence, assets/gaps, overlay and motion facts. |
| Xiaotudou Asset Family | One Product Owner-selected rough monochrome adult-character model sheet and limited-animation pose pack, chosen from three explicit candidates. |
| Creator Static Asset | Explicit source/Codex/local-graphic character, illustration, diagram or screenshot fact with exact provenance; no application Provider Attempt/charge. |
| Deterministic Render Input | Exact committed narration/alignment/approved plan/assets supplied to the renderer. |
| Sample Video | Exact 15–20 second render Artifact requiring a human decision before full render. |
| Final Video | Full deterministic render from the approved lineage, subject to Final Video Decision. |
| Publish-ready Package | Post-approval MP4/SRT/cover/copy/lineage/feedback delivery. |
| Publication Record | Creator-declared Douyin URL/time bound to one exact approved Final Version; never presented as platform-authenticated. |
| Performance Snapshot | Immutable creator-entered 72-hour or 7-day metric fact bound to one Publication Record. |
| Content Hypothesis | Bounded human continue/change/stop decision based on the declared feedback, not automated analytics advice. |
| Knowledge Video Business Loop | Three distinct exact episode lineages through production, manual publication, 72-hour/7-day feedback and one next hypothesis. |

Ownership separation:

- Source intake owns exact repository URL/identity, commit SHA, ordered file path/blob identities and normalized unit locators.
- Top-level package claims exclusively own evidence locators; narration units never duplicate them.
- Script-package intake owns structural validation, exact source membership and immutable Version creation; it does not author or semantically verify claims.
- Script Decision owns semantic, teaching-quality and content approval.
- Paid narration owns audio bytes plus exact Provider/voice/Budget/Attempt/cost facts, not timing decisions.
- Alignment owns all audiovisual timing and canonical subtitle intervals.
- Visual Edit Plan owns editorial intent, not media bytes.
- Asset intake/provenance owns selected creator inputs, not provider execution.
- Deterministic renderer owns media execution, not approval or lineage.
- Artifact repository commits immutable outputs.
- Decisions own human approvals/returns.
- Task state owns current selected refs/checkpoint.
- Publish builder consumes only exact approved Final lineage.
- Publication intake owns creator-declared URL/time and exact Final binding; it never owns Douyin credentials or API execution.
- Performance intake owns bounded creator-entered metric values and ages; it never claims platform authentication or causality.
- Product Owner owns the final content hypothesis.

## 4. Deep module boundaries

### Course Factory Application

Approved responsibilities:

- create/open/inspect the one local task;
- coordinate exact Source acquisition, explicit Script-package intake/re-import and Script decisions;
- request/replay Whole Narration;
- request/inspect Acoustic Alignment and canonical SRT;
- propose and submit exact Visual Edit Plan decisions;
- expose explicit creator asset readiness/provenance;
- request Sample Video only after plan approval;
- submit Sample decision and request full render only after approval;
- submit Final Video decision and export the package;
- record an explicitly confirmed manual Douyin Publication against the exact approved Final Version;
- accept creator-declared 72-hour and 7-day Performance Snapshots and one next hypothesis;
- restore exact current facts after restart.

It returns presentation values rather than repository/runtime/provider types. Later Task Contracts must choose the smallest additive view fields and operations; this specification does not freeze method names.

### Source and Creator-authored Script Package

The existing exact public GitHub connector, normalized Source Record, immutable Script repository and Script Decision semantics remain authoritative. The v1.3 primary path no longer treats private deterministic `_OfflineRuntime` output as a general Script author or natural-language revision engine.

The Creator-authored Script Package schema v1 has exactly eight top-level fields: `schema`, `version`, `script_package_id`, `source`, `claims`, `narration_units`, `creator_provenance`, `revision_note`.

- Current Source Record must have `source_kind=github`. Package `repository_url`, `repository_identity` and `commit_sha` respectively equal its fields. Package `files` is the ordered-unique `{path, blob_sha}` projection derived from `SourceRecord.units` in first-occurrence order; repeated identical pairs collapse and one path with different blobs fails closed. This is package-owned projection, not full SourceRecord payload equality, and adds no generic SourceRecord field/schema.
- `claims` is the only evidence owner. Each ordered claim has exact `{claim_id, statement, evidence_locators}`, a unique ID and at least one current-Source locator.
- Each ordered narration unit has exact `{unit_id, text, claim_ids}`, a unique ID and at least one ID resolving to an in-package claim. A narration unit cannot carry `evidence_locators`.
- `creator_provenance` is explicitly creator-declared, never authenticated identity: required `creator_declared_name`, `creator_role`, `tool_name`; optional `tool_version`, `session`, `project`.
- `revision_note` is required and nullable; when non-null it is bounded and nonempty. Raw prompts, runtime secrets, credentials, implicit latest and browser/local input paths are forbidden.

Intake validates the whole package before commit. Claim locators equal current `SourceRecord.units[].locator` byte-for-byte. Canonical logical equivalence is parsed JSON-value equality: whitespace and object-key order do not participate; array order and every accepted field/nested value do. Duplicate object keys are invalid and strings are not silently normalized.

Every accepted Script Version stores the full validated canonical `script_package` binding so restart can compare all fields without reconstructing lost provenance/source/claim facts. The first accepted package locks the Task/Source lineage to its `script_package_id`. Same ID/same canonical value replays the exact current Script ref and Decision with zero commit. Same ID/changed canonical value commits and selects the next Version with exact prior lineage; the old Decision stays historical, the new Version is unapproved and E1 stays closed until a new Decision. Only invalid, foreign Source/locator or different-ID conflict preserves the current Script selection and Decision unchanged.

Structural/source-membership validation is not automated claim interpretation: human approve/reject owns semantic and teaching quality. Reject requires bounded context, retains the current Version and awaits explicit external revision/re-import. Historical revise Decisions remain readable but cannot invoke `_OfflineRuntime` or qualify a v1.3 current Script; the legacy type is not deleted.

The package itself is not an Artifact or Decision. The committed Script Version is the downstream truth. Protected H4 and rejected #145/#146/#147 candidates remain preserved evidence and are not copied into this direction.

The first MBL series adds only the exact supported file `lessons/4-ComputerVision/06-IntroCV/README.md` within `microsoft/AI-For-Beginners`. The Source connector acquires its current commit/blob/unit locators at task start and then freezes those facts. B1 must not introduce arbitrary repository/path input, a GitHub browser or an implicit-latest downstream lookup. Each of the three episode tasks owns a distinct package/Script/Final/Publication lineage over that exact Source.

### Whole Narration

Whole Narration is one audio Artifact derived from the exact approved Script and explicit Doubao Speech Synthesis 2.0 voice “刘飞 2.0” configuration. It is generated in one Provider call per accepted attempt and replayed durably. Paid execution requires exact preflight, Budget Authorization, claimed Attempt, outcome and charge ownership before downstream acceptance.

Episode 1 may use at most two calls and CNY 2 total with no automatic retry. Episodes 2–3 have no paid authorization until later explicit caps. Credentials remain operator-local and never enter HTTP, logs, Artifact payloads or packages. B0 performs no call.

The existing GPT-SoVITS/per-Scene narration Artifacts remain readable history but cannot satisfy the MBL Whole Narration contract by concatenation or relabelling. The protected #145 candidate must not be resumed or merged wholesale; B2 starts from current main and explicitly classifies reusable phrase-clock concepts/lines.

### Short-phrase clock and canonical SRT

Alignment consumes exact approved Script text plus Whole Narration and returns ordered phrases with start/end milliseconds and exact text identity. It:

- after one declared punctuation/whitespace normalization, covers the approved narration character-for-character in order;
- defaults Chinese boundaries to 5–15 Han characters or an equivalent short phrase, subject to later engine-task validation, and cannot collapse to sentence/paragraph granularity;
- uses nonnegative, strictly ordered, non-overlapping intervals;
- is continuous: first start `0`, every prior end equals the next start, and final end equals exact audio duration;
- assigns engine-reported leading/trailing silence and gaps to adjacent phrases under a declared pause-allocation policy;
- owns canonical SRT timing;
- exposes confidence/quality evidence only as supporting facts;
- may use ASR for timestamp candidates but always uses approved Script narration as displayed text.

Text, interval, continuity, duration or derived-SRT validation failure commits no accepted Alignment and does not open Visual Edit Plan.

The local timing runtime remains an implementation decision for B2. Word-level forced alignment is not required. Fake candidates are test evidence only and cloud alignment credentials/fees are not authorized.

### Visual Edit Plan

The plan consumes exact Script, Whole Narration and Acoustic Alignment. Every aligned shot/range is covered by ordered editorial instructions:

- A-roll or B-roll role plus the editorial reason;
- teaching evidence intent and claim links;
- creator static asset reference or explicit gap;
- overlay copy/fact and placement intent;
- camera, motion, graphics, transition and hold intent;
- continuity/style constraints.

A-roll is the Xiaotudou/IP presenter layer for hooks, transitions, emotion, physical action and low-information-density spoken delivery. B-roll is the content/evidence layer for concepts, steps, comparisons, processes, charts, source evidence, screenshots and demonstrations. Claim-bearing or information-dense content defaults to B-roll unless an exception reason is recorded. B-roll is never decorative filler: it binds exact narration/alignment and teaching evidence/claims.

A human Decision binds the exact plan before rendering. The plan is not a frontend timeline model and does not embed renderer component trees or Provider request bodies.

### Creator Static Assets

Codex ImageGen produces creator-owned assets outside the application for MBL. Xiaotudou uses a two-step gate: three explicit silhouettes first, then Product Owner selection of one model sheet and limited-animation pose pack. The accepted character is an asymmetric squat rough monochrome potato with dot eyes, no nose, one-stroke mouth, short limbs and black line scarf; no realistic human face, 3D/plush or child proportions. Fixed-asset motion is limited to blink, head tilt, point, hand raise, small bounce and position shift; no lip sync or video-model redraw.

An eventual bounded intake seam accepts only explicit files/manifest facts, validates them before commit and records provenance/hashes without scanning Desktop/Downloads/latest. Source assets take priority; missing illustrations/diagrams use Codex ImageGen or deterministic local graphics. It creates no application Provider Attempt, Budget Authorization, credential use or charge.

A future ImageGenerationTask → ImageGenerationResult Adapter requires separate Provider/model/credential/price/cap approval and must not become a generic registry.

### Deterministic renderer

The renderer consumes only committed exact Deterministic Render Input. It produces:

- one declared 15–20 second Sample Video from an exact plan range containing at least one A-roll segment, one B-roll segment, their transition and representative overlay/motion behavior;
- one full Final Video after exact Sample approval.

HyperFrames is the approved MBL renderer direction behind a bounded adapter, with FFmpeg for normalization/package checks. Renderer-specific composition trees, motion libraries and CLI details stay inside the adapter/module. B0 performs no installation, composition or render; B4 must prove the boundary against real Sample/Final inputs.

The renderer never owns Narration, Alignment, SRT or human decisions. Local FFmpeg remains the normalization/package delivery boundary where appropriate.

### Artifact, Decision and Task state

The generic Artifact repository remains unchanged by default. Later Tasks may add exact Artifact types/payload validators only for observed vertical needs.

At minimum, product truth must preserve exact references among:

~~~text
Source -> Creator-authored Script Package -> Script
       -> Whole Narration -> Short-phrase Clock
       -> Visual Edit Plan -> Sample Video -> Final Video -> Publish-ready Package
       -> Publication Record -> Performance Snapshots -> Content Hypothesis
~~~

with selected Creator Static Assets referenced by the Plan/Render input. Decisions bind Script, Plan, Sample and Final targets. Task state selects current refs and one next human action.

No generic graph engine, implicit latest lookup, parallel workflow or broad schema migration is implied.

### Three-view workspace

Exactly three local Jinja views remain:

1. Content & Audio;
2. Visual Planning & Production;
3. Final Review & Delivery, including manual publication and feedback facts.

Each state shows one primary human action and progressively discloses evidence. The UI does not become an editor, asset manager or dashboard. Current same-origin POST handling, autoescape, loopback default, security headers, accessible focus/targets and mobile one-column behavior remain essential.

### Packaging

Publish Package remains post-Final-approval delivery. It must add exact Whole Narration/Alignment/Edit Plan/Sample/asset provenance to existing Source/Script/Final facts. Creator Handoff Package remains a readable historical pre-generation package and is not overloaded as the v1.3 delivery package.

The MBL publish-ready package additionally owns cover, publishing copy/topic suggestions and the feedback template. It still contains no Douyin credential and does not publish. Publication Record and Performance Snapshots are adjacent durable business facts rather than ZIP entries reconstructed from latest state.

### Manual publication and performance feedback

The application never logs in to Douyin or calls a publishing/analytics API. After explicit human confirmation, the Product Owner manually publishes the exact approved Final and enters bounded URL/time facts. The application binds those creator-declared values to the exact Final Version.

At 72 hours it accepts 5-second retention, average watch time, completion rate and one next hypothesis. At seven days it accepts a final archive without overwriting the earlier snapshot. Same exact logical entry replays; changed values require an explicit correction rule in the later Task Contract and never silently rewrite history. GET/restart is read-only and offline.

Episode 1 Publication/Performance proves the technical loop. MBL completion resolves three distinct exact episode lineages and one final continue/change/stop hypothesis. Weak values can close the loop while rejecting the current content format.

## 5. Conceptual product checkpoints

These names describe product gates only; they are not approved public stage/schema values:

~~~text
source intake
  -> creator script package intake
  -> script review
  -> narration readiness
  -> alignment review
  -> visual edit review
  -> sample review
  -> full render
  -> final review
  -> exported
  -> manually published
  -> 72-hour feedback
  -> 7-day archive
  -> next hypothesis
~~~

Mandatory gates:

| Gate | Exact target | Rule |
| --- | --- | --- |
| Script Intake | Creator package + locked Source | Complete structural/identity/membership preflight before immutable Script commit. |
| Script Review | Script Version | Human semantic/teaching approve or reject bound to the exact Version. |
| Narration/Clock Readiness | Whole Narration + Short-phrase Clock | Exact Provider/Attempt/audio/text/time binding; no visual plan before accepted readiness. |
| Visual Edit Review | Visual Edit Plan Version | Human approval before sample rendering. |
| Sample Review | Sample Video Version + exact plan range | Human approval before full rendering. |
| Final Review | Final Video Version | Named-human normal-speed findings before export. |
| Publication | Final Video + Publication Record | Explicit human-confirmed manual publication; exact Final binding and no platform API. |
| Feedback | Publication + Performance Snapshot | Creator-declared 72-hour/7-day values and one next hypothesis. |

Paid Budget Review is mandatory for Doubao. Episode 1 permits at most two claimed calls and CNY 2 total; no other episode call is authorized by B0. Creator static assets, deterministic rendering and manual publication create no application Provider Attempt or charge.

## 6. Essential invariants

1. Package source identity and evidence locators match the exact locked Source; structural membership never masquerades as semantic fact-checking.
2. Cross-stage consumption uses committed exact References.
3. Script/Plan/Sample/Final decisions bind exact targets.
4. Whole Narration is one continuous Doubao audio fact for one exact approved Script and authorized Attempt.
5. Short-phrase Clock is the only audiovisual clock and canonical SRT timing source: normalized exact text coverage and contiguous non-overlapping intervals span `0` through exact audio duration.
6. Visual Edit Plan covers every aligned shot/range, records A/B-roll rationale, defaults claim-bearing/information-dense content to evidence-bound B-roll and keeps every selected asset explicit/provenanced.
7. Full render cannot start before Sample approval.
8. Final Video derives from the same approved plan/alignment/assets as the sample lineage.
9. Creator static assets and local deterministic rendering create no Provider Attempt or application charge; paid narration always preserves exact Budget/Attempt/charge truth.
10. Publication/Performance values bind an exact approved Final and stay labelled creator-declared rather than platform-authenticated.
11. One episode proves only the technical loop; three distinct complete episode lineages close MBL.
12. Historical v1.2/v1.3 media remains readable but cannot satisfy MBL gates by relabelling.

## 7. Failure and recovery

- Validation/runtime failures preserve the last accepted checkpoint and exact refs.
- Failed Script-package intake creates no Script Version/state change and preserves the prior selected Script.
- Failed narration creates no accepted narration or alignment.
- Failed alignment or derived-SRT validation creates no accepted Alignment, plan or SRT timing.
- Failed asset/preflight/sample/full render does not replace accepted upstream selections.
- A returned Sample leaves full rendering unavailable.
- GET/refresh remains read-only and does not invoke narration/alignment/rendering.
- Restart replays accepted bytes/facts without repeating costly local work.
- Failed/invalid Publication or Performance intake preserves the exact approved Final and all prior snapshots.
- GET/restart never publishes, accesses Douyin, calls Doubao or rewrites feedback.

User-facing failures remain safe and actionable. This specification does not authorize a generic recovery, corruption or concurrency framework.

## 8. Security and external effects

- Bind UI to loopback by default.
- Keep runtimes/assets under explicit operator configuration and task workspace boundaries.
- Do not scan common folders or infer latest Script/assets.
- Use argv/shell-disabled subprocess execution for local tools.
- Keep model/runtime caches, generated assets/media and evidence outside the repository.
- Make no video-generation API call or subscription-credit action.
- Keep Doubao credentials operator-local; never expose them in forms, logs, Artifact payloads or packages.
- Require exact Budget Authorization and Attempt ownership for paid narration.
- Store no Douyin credential and make no publishing/analytics API call.
- Require separate Product Owner approval for Provider/model/credentials/fees/cap/deployment and each manual publication execution.

## 9. Compatibility and parked paths

- D-008 Scene Generation Contract, Creator Handoff Package and H3 creator-import facts remain readable.
- The six-MP4 plus Scene-2 replacement flow is PARKED as a primary Goal, not deleted.
- v1.2 per-Scene narration and fixed Timeline remain historical/compatibility facts.
- The protected H4 dirty candidate remains intact. The paused #145 and rejected #146/#147 candidates remain evidence and are not wholesale implementation sources.
- Knowledge Video Editorial v1.3 E0/S0/S1 remains accepted foundation; S1 is complete at `main@1a769289`, while E1–E4 never completed.
- No migration, cleanup or protected-candidate Issue completion is implied by B0.

## 10. Verification by risk

- Source/lineage: exact reference/locator tests.
- Whole Narration: audio validity, exact binding, failure and restart replay.
- Paid narration: exact Provider/voice/cap authorization, at-most-once claim/recovery, charge facts and no automatic retry.
- Short-phrase clock: exact text coverage, monotonic millisecond bounds, duration/SRT derivation and human inspection.
- Plan: exact interval coverage, evidence/assets, human decision and replay.
- Renderer: exact committed input, sample-before-full denial, deterministic replay and playable media.
- UI: three-view route/form/security/accessibility and one-primary-action browser checks.
- Product quality: named-human full normal-speed watch/listen; automation cannot substitute.
- Publication/feedback: exact Final binding, invalid/replay behavior, no API/credential, creator-declared labels and three-episode cardinality.

## 11. Deferred architecture

Cloud image/video generation, generic Provider registry/routing, arbitrary sources, multi-user, professional editor, generic asset manager, distributed rendering, new frontend stack, automated publication/analytics API, deployment and broad graph/schema rewrites remain deferred.

Issue #152 authorizes exactly the B0 11-doc integration and its normal docs PR lifecycle. No B1–B6 code, Luna, credential, paid call, ImageGen, HyperFrames/media, Douyin publication or performance entry is authorized. Actual B0 merge permits B1 planning only.
