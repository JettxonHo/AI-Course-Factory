# AI Course Factory Current Status

## 1. Snapshot

Observed: 2026-08-24 (Asia/Shanghai)

| Fact | Current evidence |
| --- | --- |
| Current merged baseline | main@d301efd8494029e8b8eae5001050974a67778937 |
| H3.5 | Issue #139 CLOSED; PR #140 MERGED; accepted focused 31/31 and full 462/462 evidence |
| Current approved Goal file | Knowledge Video Editorial MVP v1.3 is recorded in GOAL.md as **APPROVED / ACTIVE** |
| Prior Goal disposition | Creator Handoff H0–H3.5 remain foundation history; H4 is PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE |
| Active milestone | **E0 IN PROGRESS / DOCS ONLY** through Issue #143; merge pending |
| New direction | Product Owner approved Knowledge Video Editorial direction on 2026-08-24 |
| v1.3 state | **APPROVED / ACTIVE**; feature implementation unauthorized beyond E0 docs |
| Current task | Issue #143, one authoritative nine-doc E0 PR candidate |
| H4 Issues | #141 and #142 remain OPEN and PARKED; no open PR |
| External clips | Do not generate/import scene-1.mp4…scene-6.mp4 or scene-2-replacement.mp4; no Jimeng/Kling/Seedance credits authorized |
| Provider boundary | No video-generation LLM/API, credentials, fee/cap change or deployment authorized |

This file reports facts. Product Owner approval activates the exact v1.3 Goal and E0; it does not make the pending docs PR merged, complete E0 or authorize E1 implementation.

## 2. Protected in-flight H4 candidate

The original worktree remains on codex/141-creator-handoff-h4-acceptance@d301efd with exact six dirty files:

1. src/ai_course_factory/agents/scene_generation_contract.py
2. src/ai_course_factory/application/facade.py
3. src/ai_course_factory/web/templates/final.html
4. tests/application/test_creator_scene_import.py
5. tests/application/test_facade.py
6. tests/web/test_creator_scene_import.py

The protected Diff SHA-256 is f6b6d331a26f5a426566f04c978d1dd3684615cffb0a808f13fbaf145f803171; git diff --check passes. It contains independently reviewed Final checklist behavior plus exact-source Script/Storyboard content corrections. It must not be reset, cleaned, overwritten, silently merged or described as H4 completion.

Issue #143 runs in a separate clean worktree/branch so the protected candidate remains byte-for-byte unchanged. E0 performs no line-level salvage.

## 3. Implemented and reusable facts

- live public GitHub Source acquisition at one exact commit, normalized Source units and exact claim locators;
- grounded Knowledge/Script Versions and exact Script decisions;
- Character, Storyboard, Timeline and Scene Generation Contract history;
- generic immutable Artifact repository, SQLite Decisions/Task state and filesystem Workspace;
- local GPT-SoVITS boundary, deterministic narration/handoff files and restart replay;
- creator-import Scene Clip lineage, atomic explicit-directory import/re-import and committed local composition;
- exact Final Video decisions and deterministic Publish Package;
- exactly three fixed Simplified-Chinese SSR/Jinja views under D-009.

These are reusable implementation facts. They do not prove Whole Narration, Acoustic Alignment, Visual Edit Plan, a deterministic Sample Video or v1.3 Final acceptance.

## 4. Historical family truth

- FAST-MVP v1.1 remains **COMPLETE / GOAL_APPROVED** local evidence.
- Creator Handoff v1.2 H0–H3.5 remain accepted implementation/foundation facts.
- Creator Handoff H4 never passed a real final human-quality run and v1.2 must not be relabelled complete.
- D-008/D-009 and repo-external H4 evidence remain preserved. D-010 changes the approved primary path without rewriting history.

## 5. Approved editorial direction

The approved chain is:

~~~text
exact Source -> approved Script -> Whole Narration
-> phrase-level millisecond Acoustic Alignment
-> approved Visual Edit Plan -> deterministic A/B-roll
-> approved 15–20 second Sample Video -> full render
-> named-human Final Review -> Publish Package
~~~

Codex Desktop ImageGen supplies external creator-owned static assets. Narration, Alignment and SRT remain application-owned. HyperFrames or an equivalent deterministic renderer still requires an approved later Task Contract; nothing is installed or selected by Issue #143.

## 6. Current authorization

Authorized:

- Issue #143's exact nine-file authoritative documentation candidate, including GOAL.md;
- no-cost docs validation and independent review;
- docs commit/push, one ready PR, merge and truthful Issue closure after all gates pass;
- post-merge comments/closure for #141/#142 only as PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE.

Not authorized:

- feature implementation beyond E0 docs;
- Luna dispatch;
- HyperFrames/alignment dependency installation or runtime use;
- UI/source/test/dependency edits;
- external video generation/import, Provider/API/model/credentials/fees/cap;
- E1 coding/Luna dispatch before a post-E0 Task Contract is independently approved;
- deployment or publication.

There is no active feature-code milestone. Historical v1.2 implementation remains readable, but neither it nor the protected dirty candidate grants permission to resume H4.

## 7. Issue #143 evidence boundary

Issue #143 runs no product tests or full regression because it changes documentation only. Required evidence is:

- exact nine-file docs ownership;
- GOAL.md contains the exact approved v1.3 Goal and E0-only authorization;
- consistent APPROVED / ACTIVE Goal versus E0-only implementation wording;
- preserved D-008/D-009 and H4 history;
- stale/contradiction review;
- git diff --check.
