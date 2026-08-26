# AI Course Factory Knowledge Video Business Loop PRD v1.0

## 1. Status

| Field | Value |
| --- | --- |
| Status | **MBL GOAL APPROVED / ACTIVE — B0 DOCS ONLY IN PROGRESS; FEATURE IMPLEMENTATION UNAUTHORIZED** |
| Product direction | Three-video manual Douyin production/publication/feedback loop approved by Product Owner, 2026-08-27 |
| Exact Goal | Approved by Product Owner, 2026-08-27 |
| Product | AI Course Factory |
| Candidate target | Local Codex-assisted Knowledge Video Business Loop |
| Preserves | FAST-MVP v1.1 history; Creator Handoff v1.2 implementation/evidence; exact Source/Artifact/Decision truth |

Knowledge Video Editorial v1.3 E0/S0/S1 are accepted foundation. S1 is complete at `main@1a7692894bce6ebea3d88263da67713b426ba59e` through Issue #150 / PR #151 with final 476/476 regression evidence. Product Owner approved the exact MBL Goal and B0 docs-only activation on 2026-08-27. This PRD is part of Issue #152's exact 11-doc authority integration and authorizes no B1–B6 feature implementation.

## 2. Product job

For one independent adult knowledge-video Creator:

> Given one exact public Computer Vision lesson and one explicitly supplied Creator-authored Script Package per episode, help me approve trustworthy content, produce and review a 60–90 second Douyin-ready knowledge video, manually publish it, return 72-hour/7-day watchability facts to the exact Final Version, and repeat that loop for three comparable episodes without depending on an application-controlled writing/video-generation API or platform publishing API.

Success is a repeatable production, human-review, manual-delivery and feedback path. Strong metrics are not required to close the loop; more Artifacts, codec checks or tests cannot replace teaching quality, human review, real publication or real feedback.

## 3. Approved fixed-demo boundary

| Field | Approved decision |
| --- | --- |
| Source | `microsoft/AI-For-Beginners/lessons/4-ComputerVision/06-IntroCV/README.md`, acquired at one exact commit/blob/locator set |
| Audience/language | Adult AI beginners / Simplified Chinese |
| Script input | One distinct schema-v1 `creator-script.json` per episode, authored by Codex outside the application and bound to exact Source facts |
| Content | Three immutable, human-approved Script lineages for the fixed Computer Vision series |
| Duration | 60–90 seconds per episode |
| Audio | Doubao Speech Synthesis 2.0 “刘飞 2.0”; one continuous Whole Narration call per attempt |
| Paid boundary | Episode 1: at most two calls and CNY 2 total; Episodes 2–3 require later explicit authorization |
| Time authority | Continuous short-phrase millisecond clock and canonical SRT; word-level alignment not required |
| Visual plan | Human-approved A/B-roll Visual Edit Plan tied to aligned phrases |
| Assets | Product Owner-approved Xiaotudou family plus exact source/Codex ImageGen/local-graphic assets |
| Production | Codex-assisted asset production; deterministic HyperFrames/FFmpeg adapters remain Task-gated |
| Sample gate | One exact 15–20 second Sample Video must be approved before full rendering |
| Final gate | Named-human normal-speed review of exact Final Video |
| UI | Exactly three lightweight local SSR/Jinja views |
| Delivery | Publish-ready MP4/SRT/cover/copy/lineage/feedback package |
| Business endpoint | Manual publication to Product Owner's Douyin account; no platform API |
| Feedback | Creator-declared 72-hour watchability snapshot and 7-day archive tied to exact Final Version |

The first episode proves the complete path. Three episodes published within seven days establish the first comparable baseline; they do not prove product-market fit.

## 4. Approved primary user flow

1. Creator explicitly selects the supported Computer Vision lesson; the application acquires and locks its exact current commit/blob/unit locators.
2. Codex authors one episode-specific `creator-script.json` outside the application from those exact Source units.
3. Creator explicitly triggers the existing configured-directory package intake from Content & Audio.
4. The application preflights the complete package before any Script/state write. Source identity and projected files equal the current GitHub Source Record; claim locators are exact members.
5. Top-level claims exclusively own `{claim_id, statement, evidence_locators}`. Narration units own `{unit_id, text, claim_ids}` and inherit evidence only through those IDs.
6. Accepted packages use the existing locked package-ID, canonical replay, immutable next-Version and exact prior-reference behavior.
7. Creator reads the Script and records an exact approve/reject Decision. Semantic accuracy and teaching quality remain human responsibilities; external revision returns as a new package Version.
8. After explicit paid-call authorization and dual preflight, the Doubao adapter renders the entire approved Script once using voice “刘飞 2.0”; durable replay performs no second call.
9. A local boundary maps approved Script text to ordered short phrases that continuously cover exact audio duration. Recognition text never replaces approved text.
10. Creator reviews Whole Narration, phrase clock and canonical SRT in Content & Audio.
11. The application proposes a Visual Edit Plan covering every phrase with A/B role, evidence, asset/gap, synchronized label, motion/camera and transition intent.
12. Creator reviews and approves the exact plan.
13. Codex creates three Xiaotudou candidates outside the application. Product Owner selects one; one model sheet and limited-animation pose pack become the only accepted A-roll character family.
14. Creator supplies remaining exact source/Codex/local-graphic assets through one later bounded intake boundary; the application records explicit provenance and never scans common folders.
15. HyperFrames produces the exact representative 15–20 second Sample from committed inputs.
16. Product Owner approves or returns the exact Sample. Full rendering remains unavailable before approval.
17. HyperFrames/FFmpeg create the 60–90 second Final Video from the same exact clock, plan and assets.
18. Product Owner watches/listens at 1.0x and records the six required quality findings against the exact Final Version.
19. Only an approved Final can produce the publish-ready MP4/SRT/cover/copy/lineage/feedback package.
20. Product Owner manually publishes the exact Final to their own Douyin account after an explicit execution confirmation.
21. The Final Review/Delivery view records creator-declared URL/time and binds it to the exact Final Version.
22. At 72 hours, Creator records 5-second retention, average watch time, completion rate and the next hypothesis; at seven days, Creator archives the final snapshot.
23. Repeat the same chain for the two remaining Computer Vision episodes under their own Script/Final/publication identities and fee gates.
24. Refresh/process restart restores exact accepted production/publication/feedback facts without repeated intake, TTS, alignment or rendering.

## 5. Three-view product contract

### View 1 — 内容与音频 / Content & Audio

- Source repository, exact commit/blob/normalized locator evidence;
- configured Script-package readiness, explicit intake/re-import and bounded validation findings;
- immutable Script reading and exact approve/reject actions;
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
- publish-ready package facts and download after approval;
- manual Douyin Publication Record and 72-hour/7-day Performance Snapshot entry tied to the exact Final Version;
- one explicit next content hypothesis after feedback.

No professional timeline editor, generic asset manager, analytics dashboard, SPA, upload manager or fourth page is part of the MBL.

## 6. P0 requirements

### Source and Script

- PR-001 Accept only the supported `microsoft/AI-For-Beginners` repository and exact `lessons/4-ComputerVision/06-IntroCV/README.md` file for the first MBL series; do not add arbitrary path input or a repository browser.
- PR-002 Acquire the current source at task start, then bind all downstream work to its exact commit/blob/locator set rather than a floating `main`.
- PR-003 Accept Script input only through one explicit configured directory and fixed `creator-script.json`; never scan Desktop/Downloads/latest, accept a browser path or use implicit latest. Schema v1 requires current `SourceRecord.source_kind=github`, exact equality for package repository URL/identity/commit, and package-owned ordered-unique `{path, blob_sha}` projection from SourceRecord units; it does not add a `files` field to SourceRecord. Provenance is creator-declared and cannot imply authenticated identity.
- PR-004 Before any Script/state write, validate the complete closed package. Top-level claims are the sole evidence owners as exact `{claim_id, statement, evidence_locators}`; narration units contain exact `{unit_id, text, claim_ids}` with no duplicated locators. Every unit resolves at least one claim, every claim has at least one current-Source locator, and package Source identity equals the current Task Source Record. Validation proves identity, membership and reference completeness only; it does not claim semantic fact-checking.
- PR-005 Every accepted Script Version persistently contains the complete validated canonical package binding and derives its narration/claims/source/provenance views from it. The first accepted package locks one stable creator-declared `script_package_id`. Same ID/same canonical value replays the exact Script ref and Decision; same ID/changed value commits/selects the next Version with exact prior lineage, leaves the old Decision historical, requires a new Decision and keeps narration/production closed. Only invalid/foreign/different-ID conflict preserves current selection/Decision unchanged. MBL supports exact approve/reject only; reject requires bounded context and external revision/re-import, while legacy revise remains readable but cannot invoke `_OfflineRuntime` or qualify a current Script.

### Whole Narration and Acoustic Alignment

- PR-006 Render exactly one continuous Whole Narration for one exact approved Script through Doubao Speech Synthesis 2.0 voice “刘飞 2.0”, one provider call per accepted attempt.
- PR-007 Persist narration bytes and exact input binding so refresh/restart does not infer again.
- PR-008 Require exact Provider/voice/configuration preflight plus durable Budget Authorization and Attempt ownership before any paid call; Episode 1 permits at most two calls and CNY 2 total with no automatic retry, while Episodes 2–3 remain unauthorized until later caps. Missing, invalid, unintelligible or wrong-Script narration fails closed before downstream acceptance.
- PR-009 After one declared punctuation/whitespace normalization, require ordered phrase text to cover the exact approved Script narration character-for-character. For Chinese, default phrase granularity is 5–15 Han characters or an equivalent short phrase; later engine validation may refine boundaries but cannot degrade to whole-sentence or whole-paragraph chunks.
- PR-010 Require nonnegative, strictly ordered and non-overlapping intervals that form one continuous clock: first start `0`, each prior end equals the next start, and final end equals exact Whole Narration duration. A declared pause-allocation policy assigns engine-reported leading/trailing silence and gaps to adjacent phrases.
- PR-011 Fail closed before committing accepted Alignment or opening Visual Edit Plan when exact-text, interval, continuity, duration or derived-SRT validation fails.
- PR-012 Derive canonical SRT timing from Acoustic Alignment while retaining approved Script narration as displayed text. ASR may supply timestamp candidates but cannot replace approved text with recognition output.
- PR-013 Keep the local alignment engine/runtime explicit, no-credential and Task-gated; Fake alignment is test evidence only. Word-level forced alignment is not an MBL acceptance requirement.

### Visual Edit Plan and static assets

- PR-014 Commit one Visual Edit Plan bound to exact Script, Whole Narration and Acoustic Alignment.
- PR-015 For every shot/range, record A-roll/B-roll role and rationale, teaching evidence intent, asset selection/gap, overlay facts, camera/motion and transition intent. A-roll is the Xiaotudou/IP presenter layer for hooks, transitions, emotion/action and low-information-density delivery. B-roll is the content/evidence layer for concepts, steps, comparisons, processes, charts, source evidence, screenshots and demonstrations.
- PR-016 Default claim-bearing or information-dense ranges to B-roll unless the plan records an exception reason. Every B-roll range binds exact narration/alignment and teaching evidence/claim; decorative B-roll cannot satisfy coverage.
- PR-017 Require an exact human Visual Edit Plan decision before sample production.
- PR-018 Record Creator Static Assets—including the Product Owner-selected Xiaotudou model/pose family, source evidence, illustrations, diagrams and screenshots—with exact identity/hash/provenance. Codex/ImageGen creation is creator activity and creates no application Provider Attempt or charge.
- PR-019 Never scan Desktop/Downloads/latest or infer assets. Later Task Contracts must define one explicit bounded import/selection boundary.
- PR-020 Keep ImageGenerationTask/ImageGenerationResult API work deferred until a separate Provider/model/credential/price/cap decision.

### Deterministic production and sample

- PR-021 Supply only committed exact inputs to one bounded deterministic renderer seam.
- PR-022 Render A/B-roll, graphics, camera, transitions and overlays according to the approved plan and Acoustic Alignment.
- PR-023 Produce one exact 15–20 second Sample Video from a declared plan interval containing at least one A-roll segment, one B-roll segment and their transition, with representative overlay/motion behavior.
- PR-024 Require explicit Sample approval before full rendering; returned samples cannot silently trigger full output.
- PR-025 Keep renderer implementation details outside Artifact/Decision/UI types. HyperFrames is the approved MBL direction behind a later bounded adapter; B0 selects no dependency and performs no render.
- PR-026 Replaying accepted inputs must not create duplicate narration/alignment/sample/full versions.

### Final review and delivery

- PR-027 Build Final Video only from the exact approved plan/alignment/assets/sample lineage.
- PR-028 Bind Final approval to the exact Final Video Version and required named-human findings.
- PR-029 Require content fidelity, narration completeness/naturalness, visual evidence/continuity and edit rhythm findings after normal-speed full viewing/listening.
- PR-030 Export only an approved Final Video with canonical SRT, cover, publishing copy, feedback template and traceable Source/Script/Narration/Clock/Edit Plan/Sample/asset lineage.
- PR-031 Restore playback/package facts after restart without rerender.

### External effects and compatibility

- PR-032 MBL makes no video-generation LLM/API call and consumes no Jimeng/Kling/Seedance credits.
- PR-033 Manual or Codex-generated static assets are creator-supplied facts, never fabricated application Provider Attempts or charges.
- PR-034 Future application-controlled ImageGenerationTask adapters require separate Product Owner approval and paid-call Budget/Attempt gates when applicable.
- PR-035 Preserve v1.2 handoff/import facts as readable compatibility/history; they cannot satisfy the MBL Final/publication/feedback gates.

### Publication and business feedback

- PR-036 Bind one creator-declared Publication Record to one exact approved Final Video Version; require Douyin URL and publication timestamp and label them as manually entered, not platform-authenticated.
- PR-037 Perform publication manually only after an explicit Product Owner execution confirmation. Store no Douyin credential and call no publishing/analytics API.
- PR-038 Accept a 72-hour Performance Snapshot containing exact metric age, 5-second retention, average watch time and completion rate; bind it to the Publication Record and validate bounded values before state mutation.
- PR-039 Accept one seven-day final snapshot/archive without overwriting the 72-hour fact or relabelling creator-declared metrics as authenticated data.
- PR-040 Require one bounded next improvement hypothesis for each 72-hour review and one explicit continue/change/stop series decision after the third seven-day archive.
- PR-041 Keep GET/refresh/restart read-only and replay Publication/Performance facts without network access, production calls or duplicate records.
- PR-042 Treat one published episode as technical-loop proof only. Require three distinct episode Script/Final/Publication lineages before MBL completion.
- PR-043 Target three publications within seven days, approximately every two days in a consistent window, without representing that cadence as an algorithm guarantee.
- PR-044 Permit weak performance to close the business loop while rejecting the current content hypothesis. Do not equate MBL closure with product-market fit, learning value, commercial demand or scalable economics.
- PR-045 Preserve exactly three SSR views; add publication/feedback controls to Final Review/Delivery rather than creating a dashboard, fourth view or SPA.

## 7. Essential invariants

1. Every imported Script unit binds the exact locked Source identity and member locators; the human Script Decision owns semantic and teaching approval.
2. Script, Visual Edit Plan, Sample and Final decisions bind the exact Version consumed downstream.
3. Whole Narration is one continuous application-owned audio fact for the exact Script.
4. Acoustic Alignment is the only audiovisual clock: normalized exact text coverage and continuous non-overlapping intervals span `0` through exact audio duration; SRT, plan and render cannot introduce competing timing.
5. Every planned shot/range states A-roll/B-roll plus rationale. Information-dense/claim-bearing content defaults to evidence-bound B-roll, while A-roll remains the presenter layer.
6. Full rendering is impossible before exact Sample approval.
7. Static creator assets and deterministic local rendering create no cloud Provider Attempt or charge; paid Doubao narration must create exact authorized Attempt/cost facts.
8. Final export uses the exact approved Final Video and preserves complete editorial lineage.
9. v1.2 imported-clip/Preview facts remain readable but cannot be relabelled as MBL acceptance.
10. Publication and Performance facts bind the exact approved Final Version and remain explicitly creator-declared rather than platform-authenticated.
11. GET/refresh/restart never publish, call Doubao, render media or fetch Douyin analytics.
12. Episode 1 proves the technical loop; only three complete Publication/Performance lineages close MBL.
13. Weak performance may reject the content hypothesis without erasing or falsifying the completed business loop.

## 8. Product acceptance

The technical loop is accepted only when Episode 1 proves:

- live exact Computer Vision Source acquisition, explicit episode Script Package intake and exact Script approval;
- authorized one-call Whole Narration behavior, short-phrase continuous clock and canonical SRT;
- one complete Visual Edit Plan with exact A/B-roll/evidence/asset coverage and approval;
- one Product Owner-selected Xiaotudou family and explicit remaining creator assets;
- an exact 15–20 second sample containing hook, A-roll, B-roll, transition, real narration and subtitles, approved before full render;
- full deterministic 60–90 second render and playable output;
- Product Owner 1.0x six-dimension Final findings;
- publish-ready MP4/SRT/cover/copy/lineage/feedback package;
- explicit manual Douyin publication and creator-declared URL/time bound to the exact Final Version;
- 72-hour watchability values and 7-day archive;
- restart/replay without repeated intake, TTS, alignment, rendering or duplicate business records;
- exact Budget/Attempt/charge facts within the Episode 1 cap and no video-generation API/credits.

The MBL Goal is accepted only after the two remaining Computer Vision episodes complete the same exact chain under their own fee/publication gates, all three have 72-hour and 7-day facts, and the Product Owner records one continue/change/stop content hypothesis.

Technical decode, FFprobe, alignment metrics, screenshots and tests support acceptance but cannot replace named-human review, real manual publication or creator-entered platform feedback.

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

- video-generation LLM/API in the MBL;
- automated Jimeng/Kling/Seedance operation or subscription-credit use;
- generic Provider registry, multi-provider routing or cost optimization;
- professional timeline editor, generic asset manager, dashboard, SPA, fourth page or frontend framework migration;
- voice cloning UI, arbitrary courses/sources, multi-user/auth, deployment or automated publication;
- Douyin credential storage, publishing/analytics API or an analytics dashboard;
- promising retention thresholds, product-market fit, learning value, commercial demand or scalable economics from the first three videos;
- rewriting generic Artifact/Decision/Workflow ownership;
- treating ASR/alignment scores or media metadata as named-human product approval.

## 11. Historical boundary

FAST-MVP v1.1 remains complete. Creator Handoff v1.2 H0–H3.5 remains foundation/history; H4 is PARKED / NOT COMPLETE. Knowledge Video Editorial v1.3 E0/S0/S1 remains accepted foundation, with S1 complete through Issue #150 / PR #151 at `main@1a769289`; E1–E4 never completed. D-008 through D-011 and all protected evidence remain preserved. D-012 records the approved MBL direction. Issue #152 is docs-only; no B1–B6 implementation or external action is active.
