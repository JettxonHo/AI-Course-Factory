# Goal: Deliver AI Course Factory Knowledge Video Business Loop MBL v1.0

## 1. Approval and State

| Field | Value |
| --- | --- |
| Status | **APPROVED / ACTIVE — B0 DOCS ONLY IN PROGRESS** |
| Approved by | Product Owner |
| Approval date | 2026-08-27 |
| Activation task | B0 Issue #152; docs PR pending |
| Planning baseline | `main@1a7692894bce6ebea3d88263da67713b426ba59e` |
| Goal type | Local single-user, Codex-assisted Knowledge Video Business Loop |
| Preserves | FAST-MVP v1.1 history; Creator Handoff v1.2 H0–H3.5 foundation; Knowledge Video Editorial v1.3 E0/S0/S1 accepted implementation |

Knowledge Video Editorial MVP v1.3 remains accepted foundation through S1 Creator Script Package intake. It did not complete E1–E4 or prove publication, audience response or business feedback. This Goal supersedes v1.3 only as the active delivery objective; it does not delete or relabel that history.

The protected H4 six-file candidate and the paused #145 Narrative Clock candidate remain untouched evidence. B0 neither resumes nor merges them.

## 2. Exact Goal

基于一个精确的公开 GitHub 课程来源和 Creator-authored Script Package，通过 Codex 辅助生产、豆包“刘飞 2.0”整篇旁白、短语级时间轴、人工批准的 A/B-roll 视觉编排、Codex 生图与 HyperFrames 确定性渲染，生成并人工批准 60–90 秒抖音知识视频；手工发布后回收 72 小时与 7 天数据，并连续完成三条“AI 如何看懂画面”系列视频，形成可复盘的最小业务闭环。

The first video proves the technical production, review, manual-publication and feedback path. Three comparable videos establish the first account baseline. MBL closure does not require strong performance: poor metrics can close the loop while rejecting the current content hypothesis.

## 3. Approved Primary Chain

```text
exact Computer Vision Source
  -> one Creator-authored Script Package per episode
  -> exact human-approved immutable Script Version
  -> one Doubao Liu Fei 2.0 Whole Narration
  -> short-phrase continuous clock + canonical SRT
  -> human-approved evidence-bound A/B-roll Visual Edit Plan
  -> explicit creator static assets
  -> approved 15–20 second HyperFrames Sample
  -> deterministic full render
  -> named-human 1.0x Final Review
  -> publish-ready package
  -> manual Douyin publication
  -> 72-hour feedback + 7-day archive
  -> next improvement hypothesis
```

AI Course Factory owns business truth, exact lineage, review gates, package facts and performance records. Codex is the current local production executor, not a permanent public product dependency. HyperFrames/FFmpeg remain bounded deterministic execution adapters. Future independent image/model APIs may replace Codex production only through separate approved adapters without rewriting the business chain.

## 4. Fixed First Business Experiment

### Source and audience

- Public source: `microsoft/AI-For-Beginners`.
- Exact supported file: `lessons/4-ComputerVision/06-IntroCV/README.md`.
- Each task acquires and binds the exact current commit, blob and locators; no implicit latest is stored downstream.
- Audience: adult Simplified-Chinese AI beginners.
- Platform: Product Owner's own Douyin account through manual publication; no Douyin publishing or analytics API.

### Three-episode series

1. **AI 看图片时，到底看见了什么？** — pixels, preprocessing, classification and detection.
2. **为什么一张清楚的照片，AI 可能还是看不懂？** — size, color, contrast and preprocessing.
3. **AI 怎么发现画面里有东西动了？** — frame difference, motion detection and optical flow.

Every episode is 60–90 seconds and uses a distinct Creator-authored Script Package under the existing S1 package/Decision contract. Episode 1 opens with: “你以为 AI 在看照片，其实它先看见的，只是一组像素数字。”

### Narration and timing

- Primary TTS: Doubao Speech Synthesis 2.0, voice “刘飞 2.0”.
- Synthesize the complete accepted narration in one call per attempt; never assemble sentence calls.
- Episode 1: at most two paid calls and a total hard cap of CNY 2, with no automatic retry. Credentials remain operator-local and never enter the repository or package.
- Episodes 2–3 require a new explicit fee/cap authorization before any paid call.
- Use short-phrase alignment, normally 5–15 Chinese characters or an equivalent phrase. Local recognition may propose timestamps but approved Script text remains canonical.
- Accepted intervals form one continuous clock from zero through exact audio duration and own canonical SRT timing. Word-level alignment is not required for MBL.

### Editorial and visual system

- A-roll is the Xiaotudou presenter layer for hooks, transitions, emotion and low-density delivery.
- B-roll is the evidence/knowledge layer for concepts, comparisons, processes, source evidence and demonstrations; target approximately 65–75 percent of runtime.
- Every narration range owns a corresponding image, graphic or synchronized text purpose and exact claim/source binding. Decorative footage cannot satisfy coverage.
- Xiaotudou is an adult knowledge editor: asymmetric squat potato silhouette, dot eyes, no nose, one-stroke mouth, short limbs and black line scarf; rough monochrome hand drawing, never realistic human-faced, 3D plush or child-proportioned.
- Generate three silhouette candidates first. Product Owner selection freezes one model sheet and limited-animation pose pack. No lip sync or video-model character redraw.
- A-roll uses warm-white paper and black line art. B-roll uses charcoal with white graphics. Restrained cobalt blue is the only knowledge-emphasis color.
- Stable bottom subtitles show short-phrase narration; sparse in-frame labels show only the active knowledge relation.

### Sample, final and delivery

- The exact 15–20 second sample contains the 3-second hook, Xiaotudou A-roll, photo-to-pixel B-roll, real Liu Fei 2.0 narration, aligned subtitles and one A-to-B transition.
- Product Owner approval of the exact Sample Version is mandatory before full rendering.
- Product Owner watches the full Final Video at 1.0x and records content accuracy, narration naturalness/completeness, narration-picture correspondence, A/B/subtitle synchronization, rhythm and character consistency. Any failed dimension blocks publication.
- The publish-ready package contains Final MP4, SRT, Douyin cover, title/publish copy/topic suggestions, exact Script/source/asset/version manifest and 72-hour/7-day feedback template.

### Business feedback

- Publish three episodes within seven days, approximately every two days in a consistent time window.
- Round-one metrics are 5-second retention, average watch time and completion rate.
- The Final Review/Delivery view records exact published Final Version, Douyin URL/time, the 72-hour values, 7-day archive and next improvement hypothesis through manual entry.
- The first three videos establish a baseline. Learning value and commercial-opportunity metrics are later sequential rounds, not reasons to expand this Goal now.

## 5. Stable Ownership and Compatibility

- Preserve exact Source, immutable Artifact Versions/References, Script package/Decision, Task/Workspace and restart/replay ownership.
- Keep the complete validated `script_package` binding on each Script Version. The application validates structure/membership and never claims automatic semantic fact-checking.
- Keep exactly three lightweight SSR/Jinja control views: Content & Audio; Visual Planning & Production; Final Review & Delivery.
- Keep the frontend as a control and review surface, not a professional timeline editor, generic asset manager or dashboard.
- Keep Creator Handoff media, per-Scene narration and existing Publish Package facts readable as history/compatibility. They cannot satisfy the MBL gates by relabelling.
- Extract stable production contracts and methods from Codex Video Workflow; do not copy episode HTML, temporary media directories or a dirty worktree wholesale.
- Paid TTS remains behind exact Budget Authorization/Attempt semantics. Manual Douyin activity is creator activity, not an application Provider Attempt or charge.

## 6. Milestones

### B0 — Authority rebaseline

Status: **IN PROGRESS / DOCS ONLY** through Issue #152; docs PR pending.

Outcome: make this exact Goal, D-012, the first three-video experiment, paid-call boundary, manual-publication truth and B1–B6 gates the repository authority without changing code or performing external actions.

### B1 — Series/source and Creator Package readiness

Status: **PENDING B0 MERGE**.

Outcome: add bounded support for the exact Computer Vision source, prove three episode package contracts can bind its exact locators, and freeze the Xiaotudou candidate/approval boundary. B1 planning requires a separate Issue/Task Contract; no code is authorized by B0.

### B2 — Whole Narration and phrase clock

Status: **PENDING B1**.

Outcome: integrate Doubao Liu Fei 2.0 behind explicit preflight/Budget/Attempt/cap controls, produce one durable Whole Narration, short-phrase continuous clock and canonical SRT. Do not merge or resume the #145 candidate wholesale.

### B3 — Visual Edit Plan and creator asset readiness

Status: **PENDING B2**.

Outcome: propose, inspect and approve one evidence-bound A/B-roll plan, one selected Xiaotudou asset family and all explicit creator static assets for Episode 1.

### B4 — HyperFrames sample and final renderer

Status: **PENDING B3**.

Outcome: freeze a bounded deterministic adapter, render and approve the exact 15–20 second Sample, then render the full Final Video from the same exact inputs.

### B5 — Final review, publish package and feedback intake

Status: **PENDING B4**.

Outcome: complete named-human review, build the publish-ready package, support a manual Douyin publication record and accept 72-hour/7-day performance facts. Publication itself requires an explicit execution confirmation at the gate.

### B6 — Real three-episode acceptance

Status: **PENDING B5**.

Outcome: produce, approve and manually publish the three fresh episodes, archive their 72-hour/7-day metrics and record the first content-format baseline plus the next experiment decision.

## 7. Current Authorization

Only B0 Issue #152 is currently authorized:

- edit the exact 11 documentation paths frozen in the Issue;
- append D-012 and update S1 merged truth;
- run docs consistency, ownership and diff checks;
- use the normal docs PR lifecycle.

B0 does **not** authorize B1–B6 code, Luna, tests/full regression, credentials, paid calls, model/runtime installation, ImageGen, HyperFrames render, media production, Douyin publication, deployment or performance claims.

## 8. Explicit Non-goals

- Douyin publishing/analytics API, automatic posting or authenticated platform integration;
- independent cloud image/video-generation API in the first MBL;
- video-generation LLM for the primary path;
- professional timeline editor, generic asset manager, SPA, fourth view or frontend rewrite;
- multi-user/cloud deployment, commercial distribution or production operations;
- pretending one high- or low-performing video proves the content business;
- using codec, ASR, screenshots, fixtures or agent opinion as named-human quality approval;
- resetting, cleaning, merging or silently copying protected H4/#145/#146/#147 worktrees.

## 9. Agent and Review Rules

- Main controller owns Goal/Task Contracts, actual Diff review, runtime evidence, fee/publication confirmations and final business verdict.
- Implementation milestones require exact `luna-worker` (`gpt-5.6-luna / max`) after an independently approved bounded Task Contract. Configuration is not runtime identity proof; no Terra/default fallback.
- One final full regression is required before each feature merge, but not for B0 docs-only.
- Fake/local technical evidence remains separate from real Provider, named-human, publication and performance evidence.
- Stop for unapproved Provider/model/credential/fee/cap, publication, dependency/stack expansion, broad schema rewrite or loss of protected work.

## 10. Completion Definition

The technical loop closes when Episode 1 completes exact Source/Script lineage, narration/timing, approved plan, approved sample, full render, named-human final review, publish-ready package, manual Douyin publication and both feedback checkpoints.

Knowledge Video Business Loop MBL v1.0 closes only when all three episodes complete the same chain, are published within the declared experiment window, have 72-hour and 7-day facts bound to their exact Final Versions, and end with an explicit continue/change/stop hypothesis. Closure is compatible with weak metrics; it proves a real feedback loop, not product-market fit, learning value, commercial demand, deployment or scalable economics.
