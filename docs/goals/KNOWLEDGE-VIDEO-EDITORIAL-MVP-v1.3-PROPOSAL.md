# Knowledge Video Editorial MVP v1.3 — Approved Goal Contract

## 1. Contract state

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE — E0 DOCS ONLY; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Approved by Product Owner on 2026-08-24 |
| Exact Goal | Approved by Product Owner on 2026-08-24 |
| Activation Issue | #143, one nine-doc E0 PR; merge pending |
| Baseline | `main@d301efd8494029e8b8eae5001050974a67778937` |
| Preserves | FAST-MVP v1.1 completed history; Creator Handoff v1.2 implementation/evidence; protected H4/#142 candidate |

This contract records the approved near-term product direction and exact Goal. Current authorization is limited to E0 documentation integration. It does not authorize feature implementation, install HyperFrames, select an alignment engine, call a Provider, consume subscription credits, change dependencies or complete Creator Handoff H4.

Transition authority is explicit: `GOAL.md` now records v1.3 as APPROVED / ACTIVE with E0 docs-only IN PROGRESS. Creator Handoff H4 remains PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE. E0 merge is not yet a fact; after it merges, authorization advances only to E1 planning/Task Contract review.

## 2. Approved exact Goal

> Deliver one local Knowledge Video Editorial flow that turns the supported exact public GitHub source into an approved grounded Script, one continuous narration, phrase-level millisecond Acoustic Alignment, a human-approved Visual Edit Plan, deterministic A-roll/B-roll production, an approved 15–20 second Sample Video, a fully rendered Final Video, and a named-human-approved traceable Publish Package through exactly three lightweight server-rendered views.

The Product Owner explicitly approved this exact wording and E0 activation on 2026-08-24. Approval activates the Goal and E0 governance work; it does not authorize E1 feature code or Luna dispatch.

## 3. Why the rebaseline is needed

Creator Handoff v1.2 proved useful foundations: live grounded Source, exact Script/Storyboard decisions, deterministic narration and handoff files, creator-import lineage, restart/replay, a Chinese three-view workspace and a traceable Publish Package. H4 also produced an independently accepted Final-checklist correction and a source-grounded six-beat content correction, but no accepted final creator video.

The remaining product problem is editorial control, not another external generation handoff. Six separately generated MP4s make motion quality, teaching evidence and rhythm depend on an external video model before the application has established a coherent narration clock or edit plan. The new direction moves those decisions into an application-owned editorial spine and uses deterministic production for the MVP.

## 4. Current contract audit

### Reuse without reopening

| Existing fact or module | Reuse in v1.3 |
| --- | --- |
| Live GitHub Source Record, exact commit/blob/locators and grounded Knowledge | Remain the factual basis of Script and visual evidence. |
| Script Version plus approve/reject/revise Decisions | Remain the mandatory content gate. |
| Protected H4 exact-source content correction | Candidate input to the later Script/editorial slice after explicit disposition; never discard it. |
| Generic immutable Artifact repository and exact References | Own Whole Narration, Acoustic Alignment, Visual Edit Plan, Sample Video and Final Video facts. |
| Workspace and SQLite restart/replay discipline | Remain the local persistence boundary. |
| Local GPT-SoVITS runtime/reference | Candidate substrate for one continuous narration; it is not yet proof that the one-shot contract works. |
| Final Video Decision context/findings | Reuse for named-human final acceptance; preserve the protected nonempty checklist correction. |
| Publish Package | Continue as post-approval delivery, with expanded editorial lineage. |
| Exactly three zh-CN SSR/Jinja views | Remain the Human-in-the-loop control surface. |
| Creator-supplied static asset provenance | Codex Desktop ImageGen assets remain external creator inputs with no application Attempt/charge. |

### Contracts superseded on the primary path

1. Six independently rendered Scene narration files no longer define the primary narration. v1.3 requires one continuous Whole Narration generated once.
2. Six fixed ten-second Scene slots no longer own audiovisual timing. Phrase-level millisecond Acoustic Alignment is the only clock.
3. The Scene Generation Contract and Creator Handoff Package remain readable lineage assets, but a Visual Edit Plan bound to aligned phrases becomes the primary production plan.
4. Exact `scene-1.mp4` through `scene-6.mp4` import and Scene 2 replacement remain implemented compatibility/future enhancement seams, not the near-term production prerequisite or H4 completion route.
5. The creator-import Final gate cannot be reused as the v1.3 gate. v1.3 must bind one approved Visual Edit Plan, one approved Sample Video and a full deterministic render to the same alignment/assets.
6. The current per-Scene clip/audio composer cannot be fed invented Attempt/provider facts. A later task needs a small committed-input deterministic editorial renderer seam.
7. Review-page handoff/import actions cease to be the primary workflow. The same three views take the responsibilities defined below.

### Historical facts that remain true

- FAST-MVP v1.1 remains `COMPLETE / GOAL_APPROVED` local evidence.
- Creator Handoff v1.2 H0–H3.5 produced accepted reusable code and evidence. It is not relabelled complete because H4 never passed.
- D-008 and D-009 remain historical accepted decisions. D-010 changes the near-term primary path without deleting their rationale or evidence.
- Existing H3 creator-import Artifacts remain readable. No migration or deletion is implied.

## 5. Canonical terms

- **Whole Narration** — one continuous application-owned narration audio Artifact for the exact approved Script, generated once and replayed durably.
- **Acoustic Alignment** — immutable phrase intervals in milliseconds bound to exact approved narration text and Whole Narration; after one declared punctuation/whitespace normalization, ordered phrase text covers that narration character-for-character. Intervals form the sole continuous audiovisual clock: first start `0`, adjacent end/start equal, no overlap, and final end equals exact audio duration.
- **Visual Edit Plan** — human-reviewable immutable plan bound to the exact Script, Whole Narration and Acoustic Alignment. Every shot/range records A-roll or B-roll plus the reason, selected assets or gaps, camera/motion/graphics, overlays and evidence intent. Claim-bearing or information-dense content defaults to B-roll unless the plan records an exception reason.
- **A-roll Segment** — the Xiaotudou/IP presenter layer for hooks, transitions, emotion, physical action and low-information-density spoken delivery.
- **B-roll Segment** — the content/evidence layer for concepts, steps, comparisons, processes, charts, source evidence, screenshots or demonstrations. It binds exact narration/alignment plus teaching evidence/claims and cannot be decorative filler or replace narration/SRT truth.
- **Creator Static Asset** — a creator-supplied character, environment, prop, illustration, diagram or screenshot made outside the application and recorded with exact provenance, no Provider Attempt and no application charge.
- **Deterministic Render Input** — the exact committed Whole Narration, Acoustic Alignment, approved Visual Edit Plan and selected static assets consumed by one bounded renderer seam.
- **Sample Video** — an exact 15–20 second deterministic render of a declared plan interval; approval is required before full rendering.
- **Final Video** — the complete deterministic render derived from the approved alignment, plan and assets, then bound to named-human Final Review.
- **Publish Package** — post-approval delivery containing the Final Video/SRT plus exact Source, Script, narration, alignment, plan, sample, asset and review provenance.

## 6. Vertical options

### Adopted Option A — additive editorial spine

Add Whole Narration, Acoustic Alignment, Visual Edit Plan and Sample Video as exact immutable facts. Deepen the application facade and one small deterministic renderer boundary only through later Task-gated slices. Reuse Source/Script, Artifact/Decision, Workspace, SSR, Final Review and Publish Package. Keep v1.2 handoff/import facts readable but ineligible for the v1.3 primary gate.

This is the smallest option that gives one clock, honest lineage and a real sample-before-full-render decision without rewriting accepted truth owners.

### Option B — reinterpret the six-Scene contract

Store phrase alignment and editorial instructions inside the existing six Scene/audio/clip model.

Rejected: fixed Scene duration remains a competing clock, whole narration becomes six files in disguise, and external-MP4 assumptions stay coupled to the primary path.

### Option C — external editorial pipeline plus final-MP4 import

Create narration, alignment, visuals and edit outside the application, then import one final video for review/export.

Rejected: the application would no longer own narration, SRT, alignment, plan lineage or sample approval, contradicting the approved control-plane responsibility.

## 7. Approved three-view responsibility

1. **内容与音频 / Content & Audio** — exact Source, grounded Script decision, Whole Narration, phrase alignment and canonical SRT evidence.
2. **视觉编排与制作 / Visual Planning & Production** — Visual Edit Plan, A/B-roll table, asset references/gaps, character reference and Sample Video gate.
3. **终审与交付 / Final Review & Delivery** — sample/full playback, return/approve findings and Publish Package.

These are lightweight server-rendered control views, not a professional timeline editor, generic asset manager, dashboard, SPA or fourth page.

## 8. Frontend research contract

Frontend implementation cannot begin from a component library or style trend. The required sequence is:

1. collect 8–12 real workspace/flow references from Mobbin, Refero and A1 Gallery;
2. derive 2–3 structurally different information-architecture directions;
3. ask the Product Owner to choose 2–3 concrete references and one direction;
4. use mature editorial references from Minimal.gallery, Lapa Ninja and Fonts In Use to refine type, hierarchy and density;
5. write the approved direction into `DESIGN.md` (Agent’s Design may assist only after selection);
6. implement with the existing Jinja/vanilla-CSS stack unless a separately approved technical blocker exists;
7. perform a dedicated AI-Slop audit after implementation.

Lucide, React Bits, 21st.dev, Magic UI and shadcn may be implementation resources only. React/Tailwind/shadcn are not authorized stack decisions.

## 9. Approved milestone sequence

### E0 — Truth rebaseline

Status: **IN PROGRESS / DOCS ONLY** through Issue #143; PR/merge pending.

Record D-010, preserve v1.1/v1.2 history, park H4 external clips and integrate the approved exact v1.3 Goal in one nine-doc PR. No feature code.

### E1 — Narrative clock

From the exact approved Script, commit one durable Whole Narration and phrase-level millisecond Acoustic Alignment; derive canonical SRT; prove safe failure, restart/replay and human inspectability. After a declared punctuation/whitespace normalization, phrase text must cover the approved narration character-for-character in order. Chinese phrases default to 5–15 Han characters or an equivalent short phrase, subject to later engine-task validation, and cannot collapse to sentence/paragraph granularity. The accepted clock must be nonnegative, strictly ordered, non-overlapping and continuous from `0` through exact audio duration by allocating engine-reported leading/trailing silence or gaps to adjacent phrases. A Task Contract must validate a local alignment runtime and whole-narration TTS behavior without changing the core dependency set by default.

### E2 — Visual Edit Plan and asset readiness

Create and review the aligned A/B-roll plan, explicit static-asset manifest/gaps, overlay facts and one exact approval. Codex Desktop ImageGen remains outside the application with honest creator-supplied provenance.

### E3 — Deterministic sample gate

Evaluate and freeze HyperFrames or one justified equivalent behind the same small renderer seam. Render one representative 15–20 second sample from exact committed inputs and require human approval before full rendering.

### E4 — Full render, Final Review and Publish

Render the complete video from the approved inputs, complete named-human normal-speed review, export the exact package and prove restart/replay.

## 10. Goal acceptance gates

1. Source/claim/Script lineage and Script approval are exact.
2. Whole Narration is one continuous audio fact with byte-stable replay; per-Scene inference cannot masquerade as it.
3. After declared punctuation/whitespace normalization, Acoustic Alignment phrase text covers the exact approved narration character-for-character in order. Chinese phrases default to 5–15 Han characters or equivalent short phrases and cannot degrade to whole sentences/paragraphs. Intervals are nonnegative, strictly ordered, non-overlapping and continuous: first start `0`, every prior end equals the next start, and final end equals exact audio duration. Leading/trailing silence and gaps are assigned to adjacent phrases under the declared pause-allocation policy; SRT is derived only after validation. ASR may propose timestamps but cannot replace approved display text.
4. Visual Edit Plan covers every aligned shot/range and states A-roll/B-roll role plus rationale, evidence intent, assets/gaps, overlays and motion without implicit latest inputs. Claim-bearing or information-dense ranges default to B-roll unless an explicit exception is recorded; every B-roll range binds exact narration/alignment and teaching evidence/claim.
5. A named human approves the exact Visual Edit Plan.
6. Sample Video is 15–20 seconds, includes at least one A-roll segment, one B-roll segment and the transition between them, exercises overlay/motion behavior, and is approved before full rendering.
7. Full Video is derived from the same exact alignment/plan/assets and passes playable media, SRT and restart checks.
8. A named human watches/listens at normal speed and records content fidelity, narration naturalness/completeness, visual evidence/continuity and rhythm findings against the exact Final Video.
9. Publish Package preserves exact editorial lineage and creator-asset provenance.
10. No video-generation LLM/API, credentials, paid call/cap, subscription-credit use or fabricated Attempt/charge appears in the MVP path.

## 11. Protected H4 candidate treatment

The current dirty branch `codex/141-creator-handoff-h4-acceptance` remains untouched at `d301efd` with exact six-file Diff SHA-256 `f6b6d331a26f5a426566f04c978d1dd3684615cffb0a808f13fbaf145f803171`.

After exact v1.3 Goal approval, a separate disposition review must classify lines rather than cherry-pick the branch wholesale:

- **Reuse candidate:** source-grounded Script/Knowledge improvements and exact Final findings/replay behavior.
- **Compatibility evidence:** creator-import Final tests and prior handoff/import lineage.
- **Parked path:** external six-MP4 generation/import acceptance and Scene-2 replacement as the primary Goal.

No reset, cleanup, overwrite, implicit merge or H4 completion claim is permitted. Issue #141/#142 remain open until the Product Owner approves an explicit close/park/disposition action.

## 12. Authorization and stop conditions

This approved Goal contract does not authorize feature implementation. E0 is docs only. Stop before E1 coding/Luna dispatch until E0 has actually merged and one bounded E1 Task Contract startup gate is independently approved.

Later Task Contracts must independently validate:

- the local phrase-alignment engine/runtime and its quality/latency evidence;
- whether HyperFrames satisfies the deterministic renderer boundary or one equivalent is better;
- how approved local GPT-SoVITS produces one continuous narration without pulling its heavy dependencies into core Python 3.12;
- the exact Sample Video interval and approval binding;
- additive Artifact/Decision/state/view contracts and backward-readable v1.2 facts.

Return to Product Owner review for a general Provider registry, cloud image/video API, model/credentials/fees/cap, new frontend stack, professional editor, fourth view, broad Artifact/Workflow rewrite, deployment, publication or weakening of exact Source/Script/Final invariants.

## 13. Docs-first candidate boundary

Issue #143 owns exactly nine documentation files: the independently reviewed planning candidate plus `GOAL.md`. No tests or full regression are required for this E0 docs-only candidate; `git diff --check`, Goal/authority/stale-wording checks and exact docs ownership are sufficient. The branch must not prewrite PR merge, Issue closure or E0 completion.
