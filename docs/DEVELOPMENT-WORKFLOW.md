# AI Course Factory FAST-MVP Development Workflow v1.1

## 1. Purpose

This workflow turns the approved Goal into the shortest reviewable vertical product increments. Governance exists to protect user value, money, data and ownership—not to maximize documents or edge-case proofs.

## 2. Agent Routing

### ORCHESTRATOR_REVIEWER

- Project configuration: `gpt-5.6-sol`, reasoning `xhigh`.
- Owns investigation, product/architecture decisions, Goal and milestone sequencing, Task Contracts, file ownership, dispatch and independent review.
- Reads the real Diff and reruns relevant gates; it does not approve from worker self-report.
- Avoids ordinary implementation when an exact Luna can own a bounded task.

### luna-worker

- Invoke only the exact custom Agent name `luna-worker`.
- Configured model: `gpt-5.6-luna`; reasoning: `max`.
- Implements one approved Task Contract and does not expand product scope, redesign public interfaces or approve its own work.
- Must preserve user and concurrent changes and must not spawn subagents unless explicitly instructed.

No Terra/default-worker fallback. If the exact route is unavailable:

```text
STATUS: BLOCKED_LUNA_WORKER_UNAVAILABLE
```

Configuration proves routing setup only. Record `RUNTIME_VERIFIED` only when the runtime exposes model and reasoning identity.

## 3. Read Order

Before modifying files:

1. `docs/README.md`;
2. `GOAL.md`;
3. `docs/STATUS.md`;
4. relevant PRD/System/Implementation Spec sections;
5. the single GitHub Issue or Task Contract;
6. `AGENTS.md` and this workflow.

Use current code, Git and tests as implementation facts. Old planning documents and conversations are historical evidence only.

## 4. Ready Gate

Code implementation starts when all are true:

- the active Goal authorizes the milestone;
- one Issue/Task Contract defines a user-visible outcome;
- baseline, ownership and concurrent work are known;
- acceptance and focused verification are stated;
- exact `luna-worker` routing is available;
- any credentials, fees or external side effects have separate approval.

A Task Contract is intentionally short. It contains outcome, baseline, owned modules/files, required interfaces, prohibited scope, acceptance, commands, side effects and escalation conditions. Do not freeze private implementation details without a real compatibility need.

## 5. Delivery Loop

### Prepare

The main controller checks the current branch/worktree, overlapping edits, relevant public interfaces and the smallest end-to-end behavior that advances the Goal. One Issue normally maps to one primary PR.

### Implement

The Luna worker:

- makes the smallest complete vertical change;
- deepens existing modules before adding new layers;
- keeps Providers behind Adapters and paid calls behind Budget Authorization;
- runs focused checks while iterating;
- reports actual files, behavior, commands/results, limitations and deviations.

### Review

The main controller independently checks:

- Goal/acceptance fit and user-visible behavior;
- public contract and ownership boundaries;
- Diff scope, duplication and overdesign;
- tests that would fail for the key wrong behavior;
- external effects, fees, paths and data risks;
- honest Fake versus real-runtime claims.

Verdicts are `APPROVED`, `CHANGES_REQUESTED`, `BLOCKED` or `ESCALATE_TO_HUMAN`. Use the same Luna for one bounded correction. If the same design needs another correction cycle, stop and reconsider or park the task instead of mechanically hardening it.

### Merge and Advance

Before merge, run focused acceptance checks and the full regression once. Update related `GOAL.md`/`docs/STATUS.md` facts in the feature PR when needed; do not open a separate status-only PR. After merge, close/update the Issue and select the next milestone outcome.

## 6. Risk-Proportional Evidence

| Risk tier | Examples | Default evidence |
| --- | --- | --- |
| A | credentials, paid attempts, workspace traversal, destructive writes | main behavior, denial/failure, bounded replay/recovery |
| B | planning, decisions, Scene selection, composition, export | focused behavior test + one integration path |
| C | local UI view/projection, copy, docs | primary flow or smoke evidence |

The baseline full regression is:

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

Do not automatically require mutation audits, repeated race loops, arbitrary database corruption, exact-type policing, future-schema fixtures or line-count caps. Add such evidence only when the changed boundary carries that concrete risk.

## 7. Parallelism

Default to one writing implementation task. Parallel work is allowed when interfaces are already stable and file ownership is disjoint—for example, the F2 Visual and TTS Adapters. Read-only investigation and independent review may run in parallel.

Do not let multiple workers edit the same core module, public interface or dirty worktree.

## 8. External Side Effects

Separate Product Owner confirmation is mandatory before:

- selecting/changing a real Visual or TTS Provider;
- using credentials, making a paid call or changing the cap;
- production deployment, external publication or irreversible migration;
- sensitive data/auth/privacy work;
- major stack replacement or broad rewrite.

Fake/local runs are allowed for F1 but prove only offline wiring.

## 9. Goal Acceptance

The main controller performs one product-level review of the browser flow, exported media/evidence, cost authorization, Scene recovery, restart behavior, focused/full tests and known limitations. Final states are `GOAL_APPROVED`, `GOAL_APPROVED_WITH_FOLLOW_UPS`, `GOAL_BLOCKED`, `GOAL_REJECTED` or `ESCALATE_TO_HUMAN`.
