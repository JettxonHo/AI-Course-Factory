# Documentation Map

## 1. Daily truth sources

Read in this order:

| Question | Authority |
| --- | --- |
| What is currently authorized? | `../GOAL.md`; use `STATUS.md` to distinguish approved Goal, current milestone and actual merge/runtime facts |
| What is verified now? | `STATUS.md` plus current Git/code/tests/GitHub |
| What product behavior is proposed or approved? | `product/PRD.md` |
| Which ownership and gates are stable/proposed? | `spec/SYSTEM-SPEC.md` |
| How would the repository implement them? | `spec/IMPLEMENTATION-SPEC.md` |
| How do Agents, Issues and reviews operate? | `DEVELOPMENT-WORKFLOW.md` and `../AGENTS.md` |
| Why did a hard direction change? | `decision-log.md` |

## 2. Product-family state

- **FAST-MVP v1.1** — completed historical family with accepted local Source-to-Publish evidence.
- **Creator Handoff MVP v1.2** — H0–H3.5 are implemented/accepted foundation capabilities; H4 never completed. The six-external-MP4 generation/import acceptance path is PARKED by D-010, while its exact lineage, handoff, import and restart behavior remain reusable evidence.
- **Knowledge Video Editorial MVP v1.3** — accepted foundation through E0/S0/S1. S1 Creator Script Package intake/review is complete at `main@1a7692894bce6ebea3d88263da67713b426ba59e` through Issue #150 / PR #151; E1–E4 were not completed.
- **Knowledge Video Business Loop MBL v1.0** — Product Owner approved the exact Goal on 2026-08-27. Issue #152 owns B0 docs-only authority integration; B1–B6 implementation remains unauthorized.

`GOAL.md` records MBL **APPROVED / ACTIVE** with B0 **IN PROGRESS / DOCS ONLY**. B0 changes no code and performs no Provider call, media production or publication. Creator Handoff H4 and Issue #145 remain parked/paused protected evidence, not implementation inputs.

## 3. Approved primary direction

The approved chain is exact Computer Vision Source → explicit Creator-authored Script Package → exact approved Script → Doubao Liu Fei 2.0 Whole Narration → short-phrase continuous clock/SRT → evidence-bound A/B-roll Visual Edit Plan → Codex creator assets → HyperFrames Sample/full render → named-human review → publish-ready package → manual Douyin publication → 72-hour/7-day feedback.

The current Goal contract is [KNOWLEDGE-VIDEO-BUSINESS-LOOP-MBL-v1.0.md](goals/KNOWLEDGE-VIDEO-BUSINESS-LOOP-MBL-v1.0.md). The v1.3 [Goal Contract](goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-PROPOSAL.md) and [Script-input Rebaseline](goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-SCRIPT-INPUT-REBASELINE.md) remain authoritative for the implemented S1 foundation unless the MBL contract explicitly changes a downstream outcome.

The Script Package contract still freezes one evidence owner, exact Source projection, canonical JSON-value rule and one `script_package_id` lineage. MBL adds real publication and feedback truth without weakening those invariants. Manual Douyin facts are creator-declared and bound to exact Final Versions; no platform API is implied.

## 4. Conflict rule

- Approved product behavior: PRD wins after Product Owner approval.
- Stable domain/ownership conflicts: System Spec wins.
- Stack/physical mapping conflicts: Implementation Spec wins.
- Goal may narrow current work but cannot silently rewrite Specs.
- STATUS reports facts and cannot authorize scope.
- Current code/Git/tests override stale implementation claims but do not create product permission.
- A later explicit Product Owner suspension can halt an older Goal without rewriting its historical text. When that suspension and the older Goal conflict, stop until the authority documents are reconciled through an approved Goal update.

An approved Goal does not bypass milestone entry gates. Label docs-PR merge state and implementation authorization separately.

## 5. Historical material

Older PRDs, phase plans, D-008/D-009, Creator Handoff contracts, closed Issues/PRs and H4 repo-external evidence remain audit history. D-010 changes the editorial path, D-011 changes Script ownership and D-012 changes the active completion target from local output evidence to a three-video publication/feedback loop without deleting prior facts.

## 6. Update rules

- Update PRD when approved product value/scope changes; proposed contracts must remain visibly proposed.
- Update System Spec only for stable ownership/gate changes.
- Update Implementation Spec only for physical direction/verification strategy.
- Update Goal only after exact objective/milestone authorization.
- Keep STATUS short and factual.
- Append hard decisions to the decision log; never rewrite prior decisions.
- Put implementation truth updates in their feature PRs; avoid ordinary status-only PRs.
