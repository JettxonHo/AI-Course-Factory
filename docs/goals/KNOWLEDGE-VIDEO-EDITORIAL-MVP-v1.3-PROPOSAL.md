# Knowledge Video Editorial MVP v1.3 — Approved Goal Contract

## 1. Contract state

| Field | Value |
| --- | --- |
| Status | **AMENDED GOAL APPROVED / ACTIVE — S0 DOCS ONLY IN PROGRESS; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Approved by Product Owner on 2026-08-24 |
| Exact Goal | Approved by Product Owner on 2026-08-24 |
| E0 evidence | Issue #143 CLOSED; PR #144 MERGED; main@47ac1e3 |
| Script-input authority integration | Issue #148; exact amended Goal/defaults approved; S0 docs PR/merge pending |
| Baseline | `main@47ac1e3333a2b1f4927baf6bf6de1c44950d9307` |
| Preserves | FAST-MVP v1.1 completed history; Creator Handoff v1.2 implementation/evidence; protected H4/#142 candidate |

This contract records the approved amended exact v1.3 Goal, the completed E0 baseline and the S0 docs-only authority integration now in progress. The Creator-authored Script Package contract and eight approved defaults are in [KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-SCRIPT-INPUT-REBASELINE.md](KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-SCRIPT-INPUT-REBASELINE.md).

Transition authority is explicit: `GOAL.md` now records the approved Creator-authored Script Package amendment and S0 **IN PROGRESS / DOCS ONLY**. There is no active feature implementation milestone. The former in-application Script-authoring path and paused E1 candidate remain unauthorized; Creator Handoff H4 remains PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE.

## 2. Approved amended exact Goal

> Deliver one local Knowledge Video Editorial flow that acquires the supported exact public GitHub source; accepts a Creator-authored Script Package whose ordered narration units bind exact source locators and claim evidence; commits and human-approves one immutable Script Version; produces one continuous narration, phrase-level millisecond Acoustic Alignment, a human-approved Visual Edit Plan, deterministic A-roll/B-roll production, an approved 15–20 second Sample Video, a fully rendered Final Video, and a named-human-approved traceable Publish Package through exactly three lightweight server-rendered views.

The Product Owner explicitly approved this exact amended wording, all eight Script-input defaults and S0 docs-only activation on 2026-08-24. Approval activates the amended Goal and S0 governance work; it does not authorize S1/E1 feature code or Luna dispatch.

## 3. Why the rebaseline is needed

Creator Handoff v1.2 proved useful foundations: live exact Source, immutable Script/Storyboard decisions, deterministic narration and handoff files, creator-import lineage, restart/replay, a Chinese three-view workspace and a traceable Publish Package. H4 also produced preserved checklist/content candidates, but no accepted final creator video. The #145/#146/#147 Script experiments demonstrated that private deterministic authoring/revision is not a credible general product boundary; those candidates remain rejected or paused evidence.

The remaining product problem is editorial control, not another external generation handoff. Six separately generated MP4s make motion quality, teaching evidence and rhythm depend on an external video model before the application has established a coherent narration clock or edit plan. The new direction moves those decisions into an application-owned editorial spine and uses deterministic production for the MVP.

## 4. Current contract audit

### Reuse without reopening

| Existing fact or module | Reuse in v1.3 |
| --- | --- |
| Live GitHub Source Record, exact commit/blob/units/locators | Remains the membership and identity basis for imported Script evidence. |
| Script Version plus approve/reject Decisions | Remain the mandatory immutable content gate. |
| Protected H4 and rejected #145/#146/#147 candidates | Preserve as evidence; do not use/copy as the primary Script authoring implementation. |
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
- D-008 and D-009 remain historical accepted decisions. D-010 changes the editorial path; D-011 changes Script input ownership without deleting their rationale or evidence.
- Existing H3 creator-import Artifacts remain readable. No migration or deletion is implied.

## 5. Canonical terms

- **Creator-authored Script Package** — explicit schema-v1 external input locked by one `script_package_id`; repository URL/identity/commit equal the GitHub Source Record and ordered `{path, blob_sha}` files are a package-owned unique projection from its units, not a new SourceRecord field.
- **Script Package Claim** — the sole evidence owner, exact `{claim_id, statement, evidence_locators}`. Narration units contain only `{unit_id, text, claim_ids}` and inherit locators through resolved claim IDs.
- **Creator-declared Provenance** — declared `creator_declared_name`, `creator_role`, `tool_name` and optional tool/session/project facts; never authenticated identity.
- **Script Version** — immutable application-owned Artifact that persistently owns the complete validated canonical `script_package` binding and is subject to exact human approve/reject Decision.
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

Status: **COMPLETE** at `main@47ac1e3`; Issue #143 CLOSED, PR #144 MERGED.

Recorded D-010, preserved v1.1/v1.2 history and parked H4 external clips without claiming H4 complete.

### S0 — Creator Script input rebaseline

Status: **IN PROGRESS / DOCS ONLY** through Issue #148; amended exact Goal and defaults approved.

Define the Creator-authored Script Package, single evidence ownership, exact Source shape, canonical logical equivalence, locked package ID, explicit intake/re-import, immutable Script Version and human semantic Decision ownership. This exact ten-doc candidate writes `GOAL.md` as **APPROVED / ACTIVE** while S0 remains **IN PROGRESS** until merge.

Issue #148 owns exactly ten docs including `GOAL.md`. One docs PR integrates the approved amended Goal/defaults with S0 **IN PROGRESS**. Only the actual merge makes S0 **COMPLETE** and permits S1 planning; no status-only PR.

### S1 — Creator Script Package intake

After S0 merge and one independently approved Task Contract, implement the smallest explicit intake/re-import vertical. E1 remains paused until S1 produces one exact approved Script.

### E1 — Narrative clock

From the exact human-approved imported Script, commit one durable Whole Narration and phrase-level millisecond Acoustic Alignment; derive canonical SRT; prove safe failure, restart/replay and human inspectability. E1 consumes Script and does not author/revise it. After a declared punctuation/whitespace normalization, phrase text must cover the approved narration character-for-character in order. Chinese phrases default to 5–15 Han characters or an equivalent short phrase, subject to later engine-task validation, and cannot collapse to sentence/paragraph granularity. The accepted clock must be nonnegative, strictly ordered, non-overlapping and continuous from `0` through exact audio duration by allocating engine-reported leading/trailing silence or gaps to adjacent phrases.

### E2 — Visual Edit Plan and asset readiness

Create and review the aligned A/B-roll plan, explicit static-asset manifest/gaps, overlay facts and one exact approval. Codex Desktop ImageGen remains outside the application with honest creator-supplied provenance.

### E3 — Deterministic sample gate

Evaluate and freeze HyperFrames or one justified equivalent behind the same small renderer seam. Render one representative 15–20 second sample from exact committed inputs and require human approval before full rendering.

### E4 — Full render, Final Review and Publish

Render the complete video from the approved inputs, complete named-human normal-speed review, export the exact package and prove restart/replay.

## 10. Goal acceptance gates

1. Creator package GitHub identity equals the Source Record, its files project ordered-unique unit path/blob pairs, and claim locators exactly match unit locators; the immutable Script Version retains the full canonical package binding and receives the human semantic/teaching Decision.
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

- **Preserved evidence:** source-grounded Script/Knowledge experiments and exact Final findings/replay behavior; none is automatically reused.
- **Compatibility evidence:** creator-import Final tests and prior handoff/import lineage.
- **Parked path:** external six-MP4 generation/import acceptance and Scene-2 replacement as the primary Goal.

No reset, cleanup, overwrite, implicit merge or H4 completion claim is permitted. Issue #141/#142 remain open until the Product Owner approves an explicit close/park/disposition action.

## 12. Authorization and stop conditions

This approved amended Goal does not authorize feature implementation. Stop before S1/E1 coding or Luna dispatch until S0 is actually merged and one bounded S1 Task Contract startup gate is independently approved.

Later Task Contracts must independently validate:

- the local phrase-alignment engine/runtime and its quality/latency evidence;
- whether HyperFrames satisfies the deterministic renderer boundary or one equivalent is better;
- how approved local GPT-SoVITS produces one continuous narration without pulling its heavy dependencies into core Python 3.12;
- the exact Sample Video interval and approval binding;
- additive Artifact/Decision/state/view contracts and backward-readable v1.2 facts.

Return to Product Owner review for a general Provider registry, cloud image/video API, model/credentials/fees/cap, new frontend stack, professional editor, fourth view, broad Artifact/Workflow rewrite, deployment, publication or weakening of exact Source/Script/Final invariants.

## 13. Docs-first candidate boundary

The current Issue #148 candidate owns exactly ten documentation files including `GOAL.md`. No tests or full regression are required; `git diff --check`, authority/schema/default wording checks and exact ownership are sufficient. It records the approved amended Goal and S0 **IN PROGRESS**, but must not prewrite S0 completion, PR merge or Issue closure.
