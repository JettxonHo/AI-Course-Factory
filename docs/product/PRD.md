# AI Course Factory Knowledge Video Editorial PRD v1.3

## 1. Status

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE GOAL — E0 DOCS ONLY; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Approved by Product Owner, 2026-08-24 |
| Exact Goal | Approved by Product Owner on 2026-08-24 |
| Product | AI Course Factory |
| Candidate target | Local narration-led knowledge-video editorial MVP |
| Preserves | FAST-MVP v1.1 history; Creator Handoff v1.2 implementation/evidence; exact Source/Artifact/Decision truth |

This PRD defines the approved v1.3 user value and acceptance. Issue #143 integrates it with the exact Goal through an E0 docs-only PR whose merge remains pending. No feature implementation is authorized by E0.

## 2. Product job

For one independent knowledge-video Creator:

> Given one supported public technical-course GitHub source, help me approve a grounded Script, hear and inspect one continuous narration, review phrase-level timing, approve an evidence-backed visual edit plan, validate a short deterministic sample, and locally review/export one traceable finished Chinese knowledge video without depending on a video-generation API.

Success is an intelligible, visually supported and well-paced knowledge video. More Artifacts, codec checks or automated tests do not compensate for weak teaching fidelity, unnatural narration, missing visual evidence or poor rhythm.

## 3. Approved fixed-demo boundary

| Field | Approved decision |
| --- | --- |
| Source | Supported public Microsoft AI-For-Beginners lesson, locked to one exact commit/blob/locator set |
| Audience/language | Adult AI beginners / Simplified Chinese |
| Content | One grounded, human-approved Script |
| Audio | One continuous Whole Narration generated once |
| Time authority | Phrase-level millisecond Acoustic Alignment |
| Visual plan | Human-approved A/B-roll Visual Edit Plan tied to aligned phrases |
| Assets | Creator-supplied static character/environment/prop/illustration assets from Codex Desktop ImageGen, outside the application |
| Production | Deterministic local rendering; HyperFrames or a justified equivalent remains Task-gated |
| Sample gate | One exact 15–20 second Sample Video must be approved before full rendering |
| Final gate | Named-human normal-speed review of exact Final Video |
| UI | Exactly three lightweight local SSR/Jinja views |
| Delivery | Approved Final Video, canonical SRT and traceable Publish Package |

The existing approximately one-minute lesson remains the validation content, but final duration is derived from Whole Narration and Acoustic Alignment rather than six fixed ten-second slots.

## 4. Approved primary user flow

1. Creator submits the supported public GitHub URL.
2. The system locks one exact source commit and produces grounded Knowledge/Script facts with claim locators.
3. Creator revises and approves the exact Script Version.
4. The application renders one continuous Whole Narration for that Script and replays it durably.
5. A local alignment boundary maps the exact approved narration text into short ordered phrase intervals that continuously cover the Whole Narration from millisecond `0` to its exact duration.
6. Creator reviews narration, phrase alignment and canonical SRT in the Content & Audio view.
7. The application proposes a Visual Edit Plan covering every aligned phrase interval with A/B-roll role, teaching evidence, assets/gaps, overlays, motion/camera and transitions.
8. Creator reviews and approves the exact Visual Edit Plan.
9. Creator supplies any missing static assets through Codex Desktop ImageGen outside the application. The application records exact creator-supplied provenance and never calls an image/video Provider.
10. A deterministic renderer produces one representative 15–20 second Sample Video from exact committed inputs.
11. Creator approves or returns the exact sample. Full rendering is unavailable before sample approval.
12. The renderer creates the full Final Video from the same alignment, plan and selected assets.
13. A named human watches/listens at normal speed, records findings and approves or rejects the exact Final Video.
14. Only an approved Final Video can produce the Publish Package.
15. Refresh/process restart restores exact current facts without repeating narration, alignment or rendering.

## 5. Three-view product contract

### View 1 — 内容与音频 / Content & Audio

- Source repository, exact commit/blob/claim evidence;
- Script reading and exact approve/reject/revise actions;
- Whole Narration playback and durable identity;
- phrase alignment table with exact text and millisecond intervals;
- canonical SRT evidence and safe alignment failure/retry state.

### View 2 — 视觉编排与制作 / Visual Planning & Production

- Visual Edit Plan as an inspectable A/B-roll table, not a draggable timeline;
- aligned intervals, teaching evidence, asset references/gaps, overlays, camera/motion and transition intent;
- character/style references and creator-supplied provenance;
- one primary action for plan approval or sample production at the valid gate;
- Sample Video playback and approve/return action.

### View 3 — 终审与交付 / Final Review & Delivery

- exact Sample/Final lineage and full-video playback;
- required named-human content/listening/visual/rhythm findings;
- approve/reject of exact Final Video;
- Publish Package facts and download after approval.

No professional timeline editor, generic asset manager, dashboard, SPA, upload manager or fourth page is part of the MVP.

## 6. P0 requirements

### Source and Script

- PR-001 Accept only the supported public GitHub URL in the first local product slice.
- PR-002 Bind Source and downstream work to one exact commit/blob/locator set.
- PR-003 Preserve exact source locators for factual teaching claims.
- PR-004 Prevent Script approval when required claims lack exact support.
- PR-005 Preserve exact Script Version and Decision semantics for approve/reject/revise.

### Whole Narration and Acoustic Alignment

- PR-006 Render exactly one continuous Whole Narration for one exact approved Script.
- PR-007 Persist narration bytes and exact input binding so refresh/restart does not infer again.
- PR-008 Fail closed when the whole narration is missing, invalid, unintelligible at the product gate or not bound to the current Script.
- PR-009 After one declared punctuation/whitespace normalization, require ordered phrase text to cover the exact approved Script narration character-for-character. For Chinese, default phrase granularity is 5–15 Han characters or an equivalent short phrase; later engine validation may refine boundaries but cannot degrade to whole-sentence or whole-paragraph chunks.
- PR-010 Require nonnegative, strictly ordered and non-overlapping intervals that form one continuous clock: first start `0`, each prior end equals the next start, and final end equals exact Whole Narration duration. A declared pause-allocation policy assigns engine-reported leading/trailing silence and gaps to adjacent phrases.
- PR-011 Fail closed before committing accepted Alignment or opening Visual Edit Plan when exact-text, interval, continuity, duration or derived-SRT validation fails.
- PR-012 Derive canonical SRT timing from Acoustic Alignment while retaining approved Script narration as displayed text. ASR may supply timestamp candidates but cannot replace approved text with recognition output.
- PR-013 Keep the local alignment engine/runtime explicit, no-credential and Task-gated; Fake alignment is test evidence only.

### Visual Edit Plan and static assets

- PR-014 Commit one Visual Edit Plan bound to exact Script, Whole Narration and Acoustic Alignment.
- PR-015 For every shot/range, record A-roll/B-roll role and rationale, teaching evidence intent, asset selection/gap, overlay facts, camera/motion and transition intent. A-roll is the Xiaotudou/IP presenter layer for hooks, transitions, emotion/action and low-information-density delivery. B-roll is the content/evidence layer for concepts, steps, comparisons, processes, charts, source evidence, screenshots and demonstrations.
- PR-016 Default claim-bearing or information-dense ranges to B-roll unless the plan records an exception reason. Every B-roll range binds exact narration/alignment and teaching evidence/claim; decorative B-roll cannot satisfy coverage.
- PR-017 Require an exact human Visual Edit Plan decision before sample production.
- PR-018 Record Creator Static Assets—including character, environment, props, illustrations, diagrams and screenshots—with exact local identity/hash/provenance and no Provider Attempts, credentials or application charges.
- PR-019 Never scan Desktop/Downloads/latest or infer assets. Later Task Contracts must define one explicit bounded import/selection boundary.
- PR-020 Keep ImageGenerationTask/ImageGenerationResult API work deferred until a separate Provider/model/credential/price/cap decision.

### Deterministic production and sample

- PR-021 Supply only committed exact inputs to one bounded deterministic renderer seam.
- PR-022 Render A/B-roll, graphics, camera, transitions and overlays according to the approved plan and Acoustic Alignment.
- PR-023 Produce one exact 15–20 second Sample Video from a declared plan interval containing at least one A-roll segment, one B-roll segment and their transition, with representative overlay/motion behavior.
- PR-024 Require explicit Sample approval before full rendering; returned samples cannot silently trigger full output.
- PR-025 Keep renderer implementation details outside Artifact/Decision/UI types. HyperFrames is a candidate, not an approved dependency in this planning task.
- PR-026 Replaying accepted inputs must not create duplicate narration/alignment/sample/full versions.

### Final review and delivery

- PR-027 Build Final Video only from the exact approved plan/alignment/assets/sample lineage.
- PR-028 Bind Final approval to the exact Final Video Version and required named-human findings.
- PR-029 Require content fidelity, narration completeness/naturalness, visual evidence/continuity and edit rhythm findings after normal-speed full viewing/listening.
- PR-030 Export only an approved Final Video with canonical SRT and traceable Source/Script/Narration/Alignment/Edit Plan/Sample/asset lineage.
- PR-031 Restore playback/package facts after restart without rerender.

### External effects and compatibility

- PR-032 MVP makes no video-generation LLM/API call and consumes no Jimeng/Kling/Seedance credits.
- PR-033 Manual or Codex-generated static assets are creator-supplied facts, never fabricated application Provider Attempts or charges.
- PR-034 Future application-controlled ImageGenerationTask adapters require separate Product Owner approval and paid-call Budget/Attempt gates when applicable.
- PR-035 Preserve v1.2 handoff/import facts as readable compatibility/history; they cannot satisfy the v1.3 primary Final gate.

## 7. Essential invariants

1. Approved factual claims remain traceable to the exact locked source.
2. Script, Visual Edit Plan, Sample and Final decisions bind the exact Version consumed downstream.
3. Whole Narration is one continuous application-owned audio fact for the exact Script.
4. Acoustic Alignment is the only audiovisual clock: normalized exact text coverage and continuous non-overlapping intervals span `0` through exact audio duration; SRT, plan and render cannot introduce competing timing.
5. Every planned shot/range states A-roll/B-roll plus rationale. Information-dense/claim-bearing content defaults to evidence-bound B-roll, while A-roll remains the presenter layer.
6. Full rendering is impossible before exact Sample approval.
7. Static creator assets and deterministic local rendering create no cloud Provider Attempt or charge.
8. Final export uses the exact approved Final Video and preserves complete editorial lineage.
9. v1.2 imported-clip/Preview facts remain readable but cannot be relabelled as v1.3 acceptance.

## 8. Product acceptance

The MVP is accepted only when one fresh browser-driven Demo proves:

- live Source acquisition and exact grounded Script approval;
- one continuous narration and phrase-level alignment with human-readable text/time evidence;
- canonical SRT derived from that alignment;
- one complete Visual Edit Plan with exact A/B-roll and asset provenance/gaps;
- explicit plan approval;
- an exact 15–20 second sample containing A-roll, B-roll, their transition and representative overlay/motion behavior, approved before full render;
- full deterministic render and playable output;
- restart/replay without repeated narration/alignment/rendering;
- named-human normal-speed full watch/listen and four-dimension findings;
- exact approved Publish Package;
- zero video-generation API/credential/fee/subscription-credit use.

Technical decode, FFprobe, alignment metrics, screenshots and tests support acceptance but cannot replace the named-human review.

## 9. Frontend research gate

Before visual implementation:

1. gather 8–12 real references from Mobbin, Refero and A1 Gallery;
2. derive 2–3 information-architecture directions;
3. Product Owner selects 2–3 specific references and one direction;
4. refine editorial typography/hierarchy with Minimal.gallery, Lapa Ninja and Fonts In Use;
5. record the selected direction in DESIGN.md;
6. implement only required control-plane behavior;
7. perform an AI-Slop audit.

Agent’s Design may help write the chosen direction. Lucide, React Bits, 21st.dev, Magic UI and shadcn are implementation resources only, not product evidence or stack authorization.

## 10. Non-goals

- video-generation LLM/API in the MVP;
- automated Jimeng/Kling/Seedance operation or subscription-credit use;
- generic Provider registry, multi-provider routing or cost optimization;
- professional timeline editor, generic asset manager, dashboard, SPA, fourth page or frontend framework migration;
- voice cloning UI, multiple courses/tasks/users, auth, deployment or publication;
- rewriting generic Artifact/Decision/Workflow ownership;
- treating ASR/alignment scores or media metadata as named-human product approval.

## 11. Historical boundary

FAST-MVP v1.1 remains complete. Creator Handoff v1.2 H0–H3.5 remains implemented foundation/history; H4 is PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE. D-008/D-009 and all existing evidence remain preserved. The exact v1.3 Goal is approved and active; E0 docs integration remains in progress, and E1 feature work requires its own post-E0 Task gate.
