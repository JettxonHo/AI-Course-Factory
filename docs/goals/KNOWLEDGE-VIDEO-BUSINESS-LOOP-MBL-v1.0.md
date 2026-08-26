# Knowledge Video Business Loop MBL v1.0 — Approved Goal Contract

## 1. Contract state

| Field | Value |
| --- | --- |
| Status | **GOAL APPROVED / ACTIVE — B0 DOCS ONLY IN PROGRESS** |
| Product Owner approval | 2026-08-27 |
| Recording task | Issue #152 |
| Baseline | `main@1a7692894bce6ebea3d88263da67713b426ba59e` |
| Implementation | **UNAUTHORIZED** until a later milestone Task Contract passes its startup gate |

Knowledge Video Editorial MVP v1.3 remains accepted foundation through S1 Creator Script Package intake. It did not complete its Narrative Clock, Visual Edit Plan, Sample, full-render or named-human acceptance milestones, and it explicitly excluded publication. This contract keeps the trustworthy foundation and changes the active objective from “one local finished-video proof” to a small real production-and-feedback loop.

## 2. Exact Product Owner-approved Goal

基于一个精确的公开 GitHub 课程来源和 Creator-authored Script Package，通过 Codex 辅助生产、豆包“刘飞 2.0”整篇旁白、短语级时间轴、人工批准的 A/B-roll 视觉编排、Codex 生图与 HyperFrames 确定性渲染，生成并人工批准 60–90 秒抖音知识视频；手工发布后回收 72 小时与 7 天数据，并连续完成三条“AI 如何看懂画面”系列视频，形成可复盘的最小业务闭环。

This exact wording is also recorded in `GOAL.md` and Issue #152. The Goal is deliberately a business-loop contract, not a claim of product-market fit or a promise to automate publication.

## 3. First-principles boundary

A minimum business loop must connect five real facts:

1. **valuable input** — exact public teaching evidence and one approved Creator-authored Script;
2. **repeatable production** — exact narration, timing, visual plan, assets and deterministic render;
3. **human quality** — a representative sample gate and named-human complete-viewing verdict;
4. **real delivery** — one publish-ready package and an actual manual Douyin publication;
5. **feedback** — metrics tied to the exact published Final Version and one next hypothesis.

Generating an MP4 without publication is a production loop, not a business loop. Publishing one video proves the path but not a baseline. Three comparable videos are the smallest approved experiment; they are not statistical proof of a business.

## 4. Canonical terms

- **Knowledge Video Business Loop** — exact Source-to-Script-to-production-to-publication-to-feedback lineage ending in an explicit next decision.
- **Creator-authored Script Package** — the already implemented S1 schema-v1 package. One distinct package owns each episode; Codex authors it outside the application and the application validates/imports it without pretending to be a general writer.
- **Whole Narration** — one continuous accepted narration audio for the exact approved Script, produced in one TTS call per attempt and replayed durably.
- **Short-phrase Clock** — ordered, continuous millisecond ranges, normally 5–15 Chinese characters or one equivalent short phrase. Recognition output proposes timestamps only; approved Script text remains canonical.
- **A-roll Segment** — Xiaotudou presenter layer for hooks, transitions, emotion, physical action and low-information-density delivery.
- **B-roll Segment** — evidence and knowledge layer for pixels, comparisons, processes, diagrams, source evidence and demonstrations. It is never decorative filler.
- **Visual Edit Plan** — immutable, human-reviewable instructions binding each narration range to A/B role, rationale, evidence/claim, asset, overlay and deterministic motion intent.
- **Xiaotudou Asset Family** — one Product Owner-approved model sheet and limited-animation pose pack derived from three explicit candidate silhouettes.
- **Sample Video** — exact 15–20 second representative render that must pass human review before full rendering.
- **Publish-ready Package** — approved Final MP4/SRT plus cover, posting copy, exact lineage/asset manifest and feedback template.
- **Publication Record** — creator-declared Douyin URL and publication time bound to one exact approved Final Version. It is not an authenticated platform API fact.
- **Performance Snapshot** — manually entered metric values at a declared age, bound to the Publication Record and labelled as creator-declared data.
- **Content Hypothesis** — the continue/change/stop decision recorded after the three-video baseline; it is not automated analytics advice.

## 5. Approved experiment

### 5.1 User, platform and source

- Operator and named reviewer: Product Owner.
- Audience: adult Simplified-Chinese AI beginners.
- Platform: Product Owner's own Douyin account.
- Delivery: manual publication only; no Douyin API, browser automation or credential intake.
- Repository: `https://github.com/microsoft/AI-For-Beginners`.
- File: `lessons/4-ComputerVision/06-IntroCV/README.md`.
- Runtime intake locks an exact commit, blob and source locators. No contract hard-codes a floating `main` as downstream truth.

The primary lesson currently requires a bounded source-path expansion because merged S1 code supports the historical Lesson 1 path. B0 records that need; B1 must freeze its smallest public seam and cannot introduce a generic repository browser, arbitrary path field or file manager.

### 5.2 Series and cadence

| Episode | Teaching promise | Primary visual proof |
| --- | --- | --- |
| 1 | AI 看图片时，到底看见了什么？ | photo → pixels → preprocessing → classification versus detection |
| 2 | 为什么一张清楚的照片，AI 可能还是看不懂？ | size/color/contrast and before/after preprocessing |
| 3 | AI 怎么发现画面里有东西动了？ | frame difference, motion detection and optical flow |

Each episode is 60–90 seconds. Publish all three within seven days, approximately every two days in a consistent time window. This is an experiment-control choice, not a claim about the Douyin algorithm.

Episode 1 begins with: “你以为 AI 在看照片，其实它先看见的，只是一组像素数字。” Its teaching line is photo → pixels → preprocessing → classification/detection; it does not expand into model architecture, training implementation or code.

### 5.3 Script and evidence

- One distinct Creator-authored Script Package per episode.
- Codex authors the package outside the application from the exact acquired Source units.
- Top-level claims keep sole evidence-locator ownership under the implemented S1 contract.
- The application validates structure, exact Source identity and locator membership; the Product Owner owns semantic and teaching approval.
- Revisions happen outside the application and return under the same episode package ID as a new immutable Version requiring a new Decision.
- The old `_OfflineRuntime` natural-language author/reviser remains out of the primary path.

### 5.4 Narration, cap and clock

- Provider/product: Doubao Speech Synthesis 2.0.
- Voice: “刘飞 2.0”.
- One accepted attempt synthesizes the entire narration once. Sentence-level multiple calls and stitched speech are prohibited.
- Episode 1 has Product Owner authorization for at most two paid calls and a total CNY 2 hard cap. Only a concrete pronunciation, rhythm or text defect may justify the second call; no automatic retry.
- Episodes 2–3 have no paid-call authorization yet. Each needs an explicit cap/credential gate before execution.
- Provider credentials remain outside Git, HTTP forms, logs, Artifacts and packages.
- Paid application-controlled work must use existing Budget Authorization and Attempt ownership rather than creator-declared zero-charge facts.
- Alignment uses local timestamps as untrusted candidates, continuous short-phrase intervals and exact approved Script display text. MBL does not require word-level forced alignment.

### 5.5 A/B-roll and asset system

- B-roll target: approximately 65–75 percent, subject to the approved plan rather than a hard renderer quota.
- Every narration range has a visual purpose and an exact evidence/claim binding. Information-dense facts default to B-roll.
- Xiaotudou candidate contract: asymmetrical squat potato, dot eyes, no nose, one-stroke mouth, short limbs, black line scarf, rough monochrome hand drawing and adult-editor temperament.
- Reject realistic human features, 3D/plush rendering, child proportions and character redraw by a video model.
- Generate three silhouette candidates. Only Product Owner selection permits one model sheet and limited-animation pose pack.
- Allowed fixed-asset animation: blink, head tilt, point, hand raise, small bounce and position shift. No lip sync requirement.
- A-roll: warm-white paper, black rough line art. B-roll: charcoal, white diagrams/text. Cobalt blue: knowledge emphasis only.
- Subtitles remain in a stable bottom safe zone; in-frame copy is limited to the current concept/relation.
- Asset priority: source-repository evidence first, then Codex ImageGen or deterministic local graphics. Unknown web assets are prohibited.

### 5.6 Rendering and review

AI Course Factory remains the control plane. Codex is the current operator/executor for content and static-asset production. HyperFrames/FFmpeg execute behind a bounded deterministic renderer boundary. The product must persist stable inputs/outputs and allow future independent image/model adapters; it must not persist Codex-private runtime behavior as business truth.

The representative Sample must include:

- the first 3-second hook;
- Xiaotudou A-roll;
- photo-to-pixel B-roll;
- real Liu Fei 2.0 narration;
- the canonical short-phrase subtitles;
- one A-roll-to-B-roll transition and representative motion/overlay behavior.

Product Owner approval of the exact Sample Version gates full rendering. Product Owner then watches the complete Final Video at 1.0x and records PASS/FAIL findings for:

1. content accuracy and teaching clarity;
2. narration naturalness and completeness;
3. narration-to-picture correspondence;
4. A/B-roll and subtitle synchronization;
5. edit rhythm/watchability;
6. Xiaotudou consistency and adult visual tone.

Any FAIL blocks the publish-ready package and publication.

### 5.7 Delivery and feedback

The package contains:

- approved vertical Final MP4;
- canonical SRT;
- Douyin cover;
- title, publishing copy and a small set of relevant topic suggestions;
- exact Source/Script/Narration/Clock/Plan/Sample/asset/Final lineage manifest;
- 72-hour and 7-day feedback template.

After manual publication, the existing Final Review/Delivery surface records creator-declared Publication and Performance facts without a platform API. Round-one values are:

- 5-second retention;
- average watch time;
- completion rate.

The first readout occurs at 72 hours and the final archive at seven days. Do not delete/repost automatically because early values are weak. Learning-value measures and commercial-opportunity measures are later sequential rounds.

## 6. Architecture choices

### Adopted — control plane plus replaceable production adapters

Keep Source/Script/Artifact/Decision/Task/Workspace/three-view truth in AI Course Factory. Extract stable production contracts from the proven Codex Video Workflow methods, then add small adapters for TTS, alignment and HyperFrames. Do not copy episode-specific HTML, temporary asset trees or a dirty worktree wholesale.

### Rejected — build an independent image/video Provider stack first

Rejected for the first MBL because it delays the real publication/feedback test. Future standalone operation remains an explicit adapter replacement after the loop proves value.

### Rejected — keep the workflow entirely manual and outside the product

Rejected because Script/Plan/Sample/Final/Publication/Performance lineage would fragment across chat, folders and screenshots instead of producing a repeatable product path.

### Rejected — turn the frontend into a professional editor

Rejected because the product needs three strong decision/control surfaces, not a timeline editor, generic asset manager, dashboard or SPA.

### Rejected — declare business success from one video

Rejected because the first video proves only the path. The first three establish a baseline; even those do not prove product-market fit.

## 7. Milestones and entry gates

| Milestone | Outcome | Entry rule |
| --- | --- | --- |
| B0 | exact authority/Goal/decision/docs rebaseline | Product Owner approval; docs only |
| B1 | exact Computer Vision source, three package contracts and Xiaotudou candidate gate | B0 merged; separate Task Contract |
| B2 | Doubao Whole Narration, explicit paid-call boundary, short-phrase clock and SRT | B1 complete; provider credentials/cap confirmed at execution |
| B3 | approved evidence-bound A/B plan and complete creator asset readiness | B2 complete; explicit asset boundary |
| B4 | approved representative Sample and deterministic full render | B3 complete; HyperFrames Task Contract |
| B5 | named-human final gate, publish package and manual feedback intake | B4 complete; publication confirmation |
| B6 | three fresh published episodes and 72-hour/7-day business record | B5 complete; per-episode fee/publication gates |

Each implementation milestone normally maps to one Issue/outcome/PR and exact Luna dispatch. Later evidence can justify splitting a milestone, but no docs wording authorizes code by itself.

## 8. Acceptance

The technical loop is complete after Episode 1 proves the entire Source-to-feedback chain. The MBL Goal is complete only when:

1. three distinct exact Creator Script Packages bind the declared Computer Vision Source;
2. every episode has exact approved Script, Whole Narration, continuous phrase clock and canonical SRT;
3. every episode has one approved evidence-bound A/B Visual Edit Plan and selected explicit assets;
4. every episode passes an exact Sample decision before full render;
5. Product Owner completes every six-dimension Final review at 1.0x;
6. every approved Final has a publish-ready package and manual Douyin Publication Record;
7. every Publication has a 72-hour Performance Snapshot and 7-day archive tied to the exact Final Version;
8. the three-video result records one explicit continue/change/stop hypothesis;
9. all paid calls stay within their explicit per-episode authorization and durable Attempt facts;
10. restart/replay preserves accepted bytes, references, Decisions, Publication and Performance facts without rerunning production.

Metrics may be poor. That closes the business loop while rejecting the current content hypothesis. No automated metric, codec check or agent opinion replaces named-human review or Product Owner interpretation.

## 9. Preserved and parked work

- S1 is complete through Issue #150 / PR #151 at `main@1a7692894bce6ebea3d88263da67713b426ba59e`; its 476-test regression is accepted foundation evidence.
- Issue #145 remains OPEN/PAUSED during B0. Its protected 35-path working candidate is not merged, copied or resumed; B2 must start from current main and conduct an explicit line-level salvage/reimplementation review.
- #146/#147 remain CLOSED/NOT_PLANNED with preserved rejected candidates.
- H4 remains PARKED/NOT COMPLETE with its protected six-file candidate intact.
- Creator Handoff media/history remains readable but cannot satisfy MBL acceptance by relabelling.

## 10. B0 authorization boundary

Issue #152 owns exactly 11 documentation files. B0 may create one docs PR and, after independent review, merge it. It may not:

- change code, tests, UI, dependencies or runtime configuration;
- dispatch Luna;
- access provider credentials or make paid calls;
- invoke ImageGen/HyperFrames/media rendering;
- publish to Douyin or record fabricated performance;
- close B1–B6 as complete;
- reset, clean, overwrite, cherry-pick or merge protected candidates.

Actual B0 merge makes this Goal the active repository authority and permits only B1 planning. It does not authorize B1 implementation.
