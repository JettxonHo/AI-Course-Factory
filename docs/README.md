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
- **Knowledge Video Editorial MVP v1.3** — E0 is complete at `main@47ac1e3` through Issue #143 / PR #144. The Product Owner approved the Creator-authored Script Package amended exact Goal, eight defaults and S0 docs-only activation. Issue #148 is integrating that authority; no feature implementation milestone is active.

`GOAL.md` now records the approved amended v1.3 execution truth with S0 **IN PROGRESS / DOCS ONLY**. It does not authorize S1/E1 implementation or the older `_OfflineRuntime` Script-authoring path. Creator Handoff H4 stays PARKED / SUPERSEDED AS PRIMARY PATH / NOT COMPLETE.

## 3. Approved primary direction

The approved amended chain is Source → explicit Creator-authored Script Package intake → exact human-approved Script Version → Whole Narration → phrase-level millisecond Acoustic Alignment → human-approved Visual Edit Plan → deterministic A/B-roll → 15–20 second Sample Video gate → full render → named-human Final Review → Publish Package.

The current Goal contract remains in [KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-PROPOSAL.md](goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-PROPOSAL.md). The approved Script-input amendment, alternatives and defaults are in [KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-SCRIPT-INPUT-REBASELINE.md](goals/KNOWLEDGE-VIDEO-EDITORIAL-MVP-v1.3-SCRIPT-INPUT-REBASELINE.md).

The approved contract freezes one evidence owner (top-level claims), a package-owned ordered file projection derived from GitHub SourceRecord units without changing SourceRecord, one canonical JSON-value rule and one `script_package_id` lineage. Every Script Version persistently owns the complete canonical package; changed imports require a new Decision. The #148 S0 contract owns exactly ten docs including `GOAL.md`; only the merged authoritative docs PR permits S1 planning.

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

Older PRDs, phase plans, D-008/D-009, Creator Handoff contracts, closed Issues/PRs and H4 repo-external evidence remain audit history. D-010 changes the approved editorial path; D-011 changes Script ownership without deleting or relabelling that history.

## 6. Update rules

- Update PRD when approved product value/scope changes; proposed contracts must remain visibly proposed.
- Update System Spec only for stable ownership/gate changes.
- Update Implementation Spec only for physical direction/verification strategy.
- Update Goal only after exact objective/milestone authorization.
- Keep STATUS short and factual.
- Append hard decisions to the decision log; never rewrite prior decisions.
- Put implementation truth updates in their feature PRs; avoid ordinary status-only PRs.
