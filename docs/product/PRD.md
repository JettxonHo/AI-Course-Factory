# AI Course Factory Creator Handoff PRD v1.2

## 1. Status

| Field | Value |
| --- | --- |
| Status | Approved Creator Handoff Product Baseline |
| Approval | Product Owner, 2026-08-14 |
| Product | AI Course Factory |
| Target | Creator Handoff Package plus imported generated Scene clips and local Final Video |
| Preserves | Completed FAST-MVP v1.1 history and accepted Source/Artifact/Decision/media contracts |

This PRD defines user value and product acceptance. System and implementation details belong in the two Specs; task authorization belongs in `GOAL.md`.

## 2. Product Job

For one independent AI Creator, the current product job is:

> Given one public technical-course GitHub repository, let me approve grounded teaching content, receive a complete per-Scene generation handoff with exact narration/SRT, manually create the Scene videos in my chosen subscription tools, import those exact clips, and locally review/export one traceable, product-quality Chinese education video.

The v1.2 product is successful only when this job works through the local workspace and passes a human content/listening/visual-rhythm review. More internal Artifacts, codec checks, ASR output or tests do not compensate for a missing product-quality result.

## 3. Fixed Demo Contract

| Field | Decision |
| --- | --- |
| Source | Microsoft `AI-For-Beginners`, Lesson 1 |
| Episode | 小土豆学 AI — Episode 01《AI不是魔法》 |
| Audience / language | Adult AI beginners / Simplified Chinese |
| Shape | Six ordered Scenes, about 60 seconds, 9:16 |
| Runtime | Local, single-user, one active Demo task |
| Preview media | Completed F2A still-image plus FFmpeg path, retained as Preview Video/technical evidence rather than v1.2 final-quality proof |
| Handoff | Ordered Scene Generation Contract, creator-readable prompts/continuity/camera instructions, exact narration audio, canonical SRT/Timeline and provenance |
| Final media | Creator-generated Scene videos imported from explicit files, plus application-owned narration/SRT and local FFmpeg composition |
| Delivery | Creator Handoff Package before generation; approved Final MP4, SRT, source attribution and Artifact Manifest after import/composition |

## 4. Core User Flow

1. Creator enters the public GitHub URL in the local workspace.
2. The system locks an exact source commit and generates grounded Knowledge and a six-Scene Script.
3. Creator approves, rejects or revises the Script with visible source evidence.
4. The system produces Character, Storyboard, Timeline, a provider-neutral Production Request and an ordered Scene Generation Contract.
5. The Creator explicitly approves the Storyboard. The system performs non-monetary local runtime/input readiness, then creates exact narration audio and canonical SRT/Timeline without using Budget Authorization for the manual handoff path.
6. The Creator downloads a deterministic Creator Handoff Package with per-Scene prompts, continuity/camera instructions, exact filenames, narration, SRT and provenance.
7. The Creator manually generates one video per Scene in a subscription interface such as Jimeng or Kling. This external activity is not an application Provider Attempt and creates no application charge.
8. At startup/configuration the operator declares one generated-clips directory. On Review, the Creator triggers atomic full-set import of exact `scene-1.mp4` through `scene-6.mp4`; the system validates/normalizes and binds each clip to its exact Scene/contract/Timeline before local composition with canonical narration/SRT.
9. Creator can re-import exact `scene-2-replacement.mp4` without deleting other usable Scene media.
10. Creator approves or rejects the exact Final Video Version and exports the existing delivery package.
11. Refresh or process restart restores the task sufficiently to continue.

### Workspace presentation contract (F2.5)

The local Creator workspace remains exactly three server-rendered views: Start / Current Task, Review / Produce and Final / Export. Each view makes the current stage and one next human action primary, with a semantic three-stage track (Ground, Produce, Deliver) whose active step is derived from the existing task stage and pending action. Start leads with script reading and compact source evidence; Review leads with one decision zone, production facts and a scan-friendly storyboard; Final presents the 9:16 playable video beside a desktop decision rail and collapses to one column on mobile. Prompt cards use native progressive disclosure. The presentation uses local warm-paper/ink/potato-gold styling, a self-hosted text favicon and CSS-only motion; it does not add JavaScript, external assets, a SPA, editor or upload manager.

For v1.2, frontend changes are limited to showing/reviewing the Scene Generation Contract, downloading the Handoff Package, triggering import from the operator-declared directory, reporting import readiness and completing the existing Final Review. No multipart upload, generic file manager or visual redesign is authorized merely because the product direction changed.

## 5. P0 Requirements

### Source and teaching accuracy

- `PR-001` Accept one supported public GitHub repository URL.
- `PR-002` Bind acquisition and downstream work to one exact commit.
- `PR-003` Preserve a source locator for each teaching claim.
- `PR-004` Block Script approval when a factual teaching claim lacks source support.

### Script and planning

- `PR-005` Generate Course Plan, Episode Plan and a Simplified-Chinese Script for the fixed Demo.
- `PR-006` Represent the Script as six ordered Scenes with claim references.
- `PR-007` Persist the mandatory Script approve/reject/revise decision.
- `PR-008` Revision creates a new Script Version and preserves the previous approved/rejected history.
- `PR-009` Hard Blocks prevent approval.
- `PR-010` Produce Character, Storyboard, Timeline and Production Request from the approved Script.
- `PR-011` Downstream stages consume committed exact Artifact References.
- `PR-012` Keep the Production Request provider-neutral; provider request bodies are execution details.
- `PR-013` Preserve the historical recorded skip state for v1.1, but require an explicit Storyboard `approve` before the v1.2 Handoff Package.

### Budget and media production

- `PR-014` Before a paid call, show a price snapshot, estimate, maximum attempts and maximum approved amount.
- `PR-015` Make no paid call without valid approval or when the next attempt would exceed the limit.
- `PR-015A` The manual v1.2 handoff/import path does not require or create Budget Authorization. Show that external subscription cost is not controlled by the application, and use non-monetary readiness/preflight for local TTS, handoff and import.
- `PR-016` Keep application-controlled paid Visual/TTS execution behind the Production Orchestrator and Budget/Attempt gates. H2 must provide bounded, durable local GPT-SoVITS narration through non-monetary readiness without turning it into a generic Provider path; manual external generation remains outside the Orchestrator.
- `PR-017` Associate each application-controlled paid generated Scene result with the exact Production Request and execution attempt; creator-import variants instead bind the exact Scene Generation Contract and contain no fabricated attempt/provider.
- `PR-018` Generate exact narration through TTS and keep application-owned narration/SRT/Timeline authoritative during final composition.
- `PR-019` F2A creator-supplied stills and Fixtures remain Preview/technical evidence for v1.2; the final-quality gate requires imported generated Scene videos.
- `PR-019A` Preserve the completed F2A exact-name/decode/replacement behavior for Preview Video and optional reference inputs without representing it as v1.2 Final Video quality.

### Creator handoff and generated Scene import

- `PR-027` Commit one ordered provider-neutral Scene Generation Contract bound to the exact approved Script, Storyboard, Timeline and Production Request.
- `PR-028` Export a deterministic Creator Handoff Package with exact references, creator-readable per-Scene prompts/continuity/camera instructions, narration audio, canonical SRT/Timeline and provenance.
- `PR-029` Treat manual Jimeng/Kling generation as creator-supplied external work: no Provider Attempt, application charge, credential or implicit Budget consumption.
- `PR-030` Accept one operator-declared generated-clips directory at startup/configuration. A Review-page POST atomically preflights/imports exact `scene-1.mp4` through `scene-6.mp4`; one re-import uses exact `scene-2-replacement.mp4`. Never accept multipart upload, scan Downloads/Desktop/latest or guess a file.
- `PR-031` Normalize selected imported clips for the existing composer while keeping native external audio/subtitle/effect tracks non-authoritative by default.
- `PR-032` Re-import one Scene as a new exact Scene Clip Version, preserve unaffected Scene media and invalidate only exact downstream delivery selections.
- `PR-033` Permit future Jimeng/Kling API adapters to consume the same Scene Generation Contract only after separate Provider/model/credential/price/cap approval and Budget/Attempt gating.
- `PR-034` Require a human full-watch/listen quality verdict bound to the exact Final Video Version; automated format/ASR checks cannot satisfy this requirement alone.
- `PR-035` Keep `artifact_type=scene_clip`, existing identities/Versions and Task selection, while adding a discriminated creator-import payload with no `attempt_id`/`provider` and an exact Scene Generation Contract dependency.
- `PR-036` Before v1.2 Final Review, resolve all six selected Scene Clip Versions and require creator-import variants for the same exact Scene Generation Contract. Legacy generated/Preview facts remain readable but cannot satisfy this gate.

### Recovery, review and delivery

- `PR-020` Distinguish provider, generation, quality and budget failures in user-facing status.
- `PR-021` Retry an application-controlled paid Provider only within approved attempt and budget limits; manual re-import follows its exact no-attempt Scene contract.
- `PR-022` Allow one Scene to be retried/replaced while preserving other usable Scene media.
- `PR-023` Require Final Video approval before final export/completion.
- `PR-024` Show current stage, pending human action, failures and available actions in the workspace.
- `PR-025` Export approved MP4, SRT, source attribution and Artifact Manifest.
- `PR-026` Export locally; do not auto-publish.

## 6. Essential Invariants

Only these invariants are default MVP release blockers:

1. Approved teaching claims remain traceable to the locked source.
2. Script and Final Video approvals bind the exact Version being consumed/exported.
3. Paid calls occur only after an explicit valid Budget Authorization.
4. Replaying an uncertain paid attempt must not silently duplicate cost.
5. Scene retry preserves unaffected usable Scene media.
6. Final export contains a playable video and its required evidence files.
7. Manual external Scene generation creates no Provider Attempt or application charge; future application-controlled API calls require Budget/Attempt gates.
8. Final Video uses exact imported Scene Clip selections plus application-owned narration/SRT rather than a Preview Video being relabelled as final quality.
9. Imported Scene Clip provenance never invents a Provider Attempt, and v1.2 Final Review proves all six selected Clip Versions share one exact Scene Generation Contract.

Other corruption, concurrency, mutation and future-schema scenarios are tested only when the changed module creates a concrete corresponding risk.

## 7. Acceptance

Creator Handoff MVP v1.2 is accepted when one browser-driven Demo proves:

- GitHub URL -> grounded Script -> Script approval;
- explicitly approved Storyboard -> exact Scene Generation Contract;
- deterministic Creator Handoff Package with prompts, narration, SRT/Timeline and exact provenance;
- manual external generation creates no application attempt/charge or Budget Authorization, and the UI states external subscription cost is uncontrolled;
- an operator-declared directory plus Review POST atomically imports exact `scene-1.mp4` through `scene-6.mp4` as honest creator-import variants for one Scene Generation Contract;
- playable 9:16 Chinese Final MP4 composition and one bounded Scene re-import;
- Final Video approval;
- local MP4/SRT/source/Manifest export;
- one refresh or process restart recovery;
- no paid call before approval or above the cap;
- a named human reviewer watches/listens to the complete Final Video and accepts teaching fidelity, narration naturalness/completeness, visual continuity/action and edit rhythm.

Required evidence is the browser flow, both packages, imported Scene clip provenance, local GPT-SoVITS execution records, exact-reference assertions, technical media checks, restart/re-import evidence, focused/full tests and the human product-quality record.

Issue #117's accepted F2A evidence covers six local image inputs, exact preflight failure, local H.264 conversion, visual-only replacement, restart replay and honest external-source attribution. Issue #119 accepted the local GPT-SoVITS TTS path. Issue #123 / PR #124 supplied partial media/recovery evidence but did not prove live GitHub acquisition. Issue #125 / PR #126 corrected that boundary and repeated the complete same-task source-to-package browser acceptance; the planning controller accepted the merged combined evidence as `GOAL_APPROVED` on 2026-08-14.

## 8. Non-goals

- Multi-user, authentication, permissions, SaaS or production deployment.
- Private repositories or multiple knowledge-source types.
- Multi-course batch production or a general task dashboard.
- Professional timeline editing, dynamic templates or voice cloning.
- In-app Jimeng/Kling subscription automation, WebUI control or browser scripting.
- Assuming platform-native narration/subtitles replace canonical application-owned narration/SRT.
- Multi-Provider routing, failover or cost optimization.
- Automatic external publication, marketplace or ContentOS platform abstractions.
- General Artifact graph, distributed workers or exhaustive hostile-database recovery.

## 9. Approved and Deferred Decisions

- `PD-001` Automatic cloud Visual Provider remains deferred. Creator Handoff v1.2 adopts manual Jimeng/Kling subscription use plus explicit imported Scene clips; future API adapters require a separate decision.
- `PD-002` Approved: local GPT-SoVITS v2 through explicit external Python 3.11/repository/model configuration and the fixed synthetic Serena reference, with zero external charge.
- `PD-003` Smoke-test and full-Demo cost/attempt caps remain unchanged and local F2B inference does not incur external charge.

FAST-MVP acceptance does not authorize cloud credentials, paid calls, fees or deployment. F2A's external image generation remains outside the application, while F2B's local GPT-SoVITS inference uses no credentials or application Provider API call. F2.5 and F3 are complete for the fixed local single-user product; this is local-product evidence, not cloud or deployed-runtime evidence.

The Creator Handoff v1.2 Goal and eight fixed defaults are approved. H0 integrates this truth through Issue #129; H1-H4 implementation remains unauthorized until each milestone has its own bounded Issue/Task Contract and independent review.
