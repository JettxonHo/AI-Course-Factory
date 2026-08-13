# AI Course Factory FAST-MVP PRD v1.1

## 1. Status

| Field | Value |
| --- | --- |
| Status | Approved FAST-MVP Product Baseline |
| Approval | Product Owner, 2026-08-13 |
| Product | AI Course Factory |
| Target | Smallest usable local end-to-end MVP |
| Supersedes | PRD v1.0 as the daily implementation baseline |

This PRD defines user value and product acceptance. System and implementation details belong in the two Specs; task authorization belongs in `GOAL.md`.

## 2. Product Job

For one independent AI Creator:

> Given one public technical-course GitHub repository, let me review the teaching content and maximum cost locally, then produce, review and export one playable, traceable Chinese education video without assembling the pipeline by hand.

The MVP is successful only when this job works through the local workspace. More internal Artifacts, repository abstractions or tests do not compensate for a missing user flow.

## 3. Fixed Demo Contract

| Field | Decision |
| --- | --- |
| Source | Microsoft `AI-For-Beginners`, Lesson 1 |
| Episode | 小土豆学 AI — Episode 01《AI不是魔法》 |
| Audience / language | Adult AI beginners / Simplified Chinese |
| Shape | Six ordered Scenes, about 60 seconds, 9:16 |
| Runtime | Local, single-user, one active Demo task |
| Media | Creator-supplied Desktop ImageGen stills from an explicit directory (F2A; generated outside the application at zero external charge) plus one authorized/local TTS path and local FFmpeg; automatic cloud Visual Provider work is deferred |
| Delivery | Playable MP4, SRT, source attribution and Artifact Manifest |

## 4. Core User Flow

1. Creator enters the public GitHub URL in the local workspace.
2. The system locks an exact source commit and generates grounded Knowledge and a six-Scene Script.
3. Creator approves, rejects or revises the Script with visible source evidence.
4. The system produces Character, Storyboard, Timeline and a provider-neutral Production Request.
5. The system estimates cost; Creator explicitly approves a maximum amount and attempt count.
6. The Production Orchestrator generates Scene visuals and narration, then FFmpeg composes a playable video and subtitles. In the bounded F2A local-import mode, the Creator supplies six exact Desktop ImageGen stills and the application only performs local conversion after Budget approval; no Visual Provider API is called.
7. Creator can retry or replace one failed/unsatisfactory Scene without deleting other usable Scene media.
8. Creator approves or rejects the final video and exports the delivery package.
9. Refresh or process restart restores the task sufficiently to continue the Demo.

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
- `PR-013` Storyboard review may be skipped, but the choice is recorded.

### Budget and media production

- `PR-014` Before a paid call, show a price snapshot, estimate, maximum attempts and maximum approved amount.
- `PR-015` Make no paid call without valid approval or when the next attempt would exceed the limit.
- `PR-016` Route Visual, TTS and composition through one Production Orchestrator entry point.
- `PR-017` Associate each Scene result with the exact Production Request and execution attempt.
- `PR-018` Generate narration through TTS and compose visual, audio and subtitles into the video.
- `PR-019` Final MVP evidence includes the accepted F2A creator-supplied visual assets and an authorized real/local TTS path; Fake/local Fixtures remain development evidence only.
- `PR-019A` The F2A local-import mode accepts only `scene-1.png` through `scene-6.png` (and exact `scene-2-replacement.png` for replacement), decodes all inputs atomically before attempts/media/Artifacts, charges zero external amount, and preserves the predecessor voice/Scene Audio/Master Audio during a visual-only replacement.

### Recovery, review and delivery

- `PR-020` Distinguish provider, generation, quality and budget failures in user-facing status.
- `PR-021` Retry only within the approved attempt and budget limits.
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

Other corruption, concurrency, mutation and future-schema scenarios are tested only when the changed module creates a concrete corresponding risk.

## 7. Acceptance

The MVP is accepted when one browser-driven Demo proves:

- GitHub URL -> grounded Script -> Script approval;
- planning -> Budget approval;
- accepted F2A visual assets and real/local TTS generation within the approved cap;
- playable 9:16 Chinese MP4 composition;
- one bounded Scene retry/replace;
- Final Video approval;
- local MP4/SRT/source/Manifest export;
- one refresh or process restart recovery;
- no paid call before approval or above the cap.

Required evidence is the browser flow, the exported package, F2A visual-asset evidence plus the local GPT-SoVITS execution records, focused tests for changed behavior and the full regression run before merge/acceptance.

Issue #117's now-accepted F2A evidence covers six local image inputs, exact preflight failure, local H.264 conversion, visual-only replacement, restart replay and honest external-source attribution. It satisfies the visual side of `PR-019`; F2B TTS and the F3 browser acceptance remain outstanding.

## 8. Non-goals

- Multi-user, authentication, permissions, SaaS or production deployment.
- Private repositories or multiple knowledge-source types.
- Multi-course batch production or a general task dashboard.
- Professional timeline editing, dynamic templates or voice cloning.
- Multi-Provider routing, failover or cost optimization.
- Automatic external publication, marketplace or ContentOS platform abstractions.
- General Artifact graph, distributed workers or exhaustive hostile-database recovery.

## 9. Human Decisions Still Required

- `PD-001` Automatic cloud Visual Provider remains deferred; F2A creator-supplied Desktop ImageGen visuals satisfy the FAST-MVP visual asset boundary.
- `PD-002` Approved: local GPT-SoVITS v2 through explicit external Python 3.11/repository/model configuration and the fixed synthetic Serena reference, with zero external charge.
- `PD-003` Smoke-test and full-Demo cost/attempt caps remain unchanged and local F2B inference does not incur external charge.

FAST-MVP approval does not authorize cloud credentials, paid calls, fees or deployment. F2A's external image generation remains outside the application, while F2B's local GPT-SoVITS inference uses no credentials or application Provider API call. F2.5 and F3 remain separate milestones.
