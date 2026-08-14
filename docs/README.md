# Documentation Map

## 1. Daily Truth Sources

Read in this order:

| Question | Authority |
| --- | --- |
| What is the current authorized outcome? | `../GOAL.md` |
| What is true now? | `STATUS.md` plus current Git/code/tests |
| What user value and MVP behavior are required? | `product/PRD.md` |
| Which system ownership and invariants are stable? | `spec/SYSTEM-SPEC.md` |
| How is this repository implementing them? | `spec/IMPLEMENTATION-SPEC.md` |
| How do Agents, Issues, tests and reviews operate? | `DEVELOPMENT-WORKFLOW.md` and `../AGENTS.md` |
| Why was a hard-to-reverse choice made? | `decision-log.md` |

FAST-MVP v1.1 is the completed historical family. Creator Handoff MVP v1.2 is the current `APPROVED / ACTIVE` family; H0 is complete through Issue #129 / PR #130 at `main@d96b091`, Issue #131 / PR #132 is merged at `main@ce05e77`, and H1 remains in progress under bounded correction Issue #133 on `codex/133-storyboard-approve-replay`. H2-H4 implementation still requires a bounded Task Contract per milestone.

## 2. Conflict Rule

- Product behavior conflicts: PRD wins after Product Owner approval.
- Stable domain/ownership conflicts: System Spec wins.
- Stack/physical mapping conflicts: Implementation Spec wins.
- Goal may narrow current work but cannot rewrite PRD/Specs.
- STATUS reports facts and cannot authorize scope.
- Current code/Git/tests override stale implementation claims, but do not silently change approved product contracts.

On a real conflict, stop only the affected work, show evidence and update the proper truth source/decision log.

## 3. Historical Material

Older PRDs, phase plans, architecture reviews, task packages and execution records remain historical evidence. They are not daily authority unless a current truth source explicitly cites them.

Detailed PR/test/correction history belongs in Git and GitHub, not in `STATUS.md`. Do not add a new planning document when the change fits an existing truth source.

## 4. Update Rules

- Update PRD only when approved product value/scope/acceptance changes.
- Update System Spec only when a stable domain, ownership, gate or interface boundary changes.
- Update Implementation Spec only when stack, physical direction or verification strategy changes.
- Update Goal when objective, milestone authorization or stop conditions change.
- Keep STATUS short and current; replace stale facts rather than appending a project diary.
- Record only hard-to-reverse decisions in the decision log.
- Update related Goal/Status facts in the feature PR. Do not create a status-only PR by default.

## 5. Archived Planning

Historical files under `docs/archive/`, earlier phase directories and prior task packages are preserved for audit. Codex should not scan them routinely or infer current permission from them.
