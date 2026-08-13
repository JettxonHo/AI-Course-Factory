# AI Course Factory Agent Rules

## 1. Scope and Reading Order

These rules apply to the repository. Before edits, read:

1. `docs/README.md`;
2. `GOAL.md`;
3. `docs/STATUS.md`;
4. relevant PRD/System/Implementation Spec sections;
5. the one current Issue or Task Contract;
6. `docs/DEVELOPMENT-WORKFLOW.md`.

Current code, Git and tests decide implementation facts. Historical plans and old conversations do not authorize work.

## 2. Authority

- PRD: user value, behavior, MVP scope and product acceptance.
- System Spec: stable domain ownership, gates and module boundaries.
- Implementation Spec: current stack, physical direction and verification strategy.
- `GOAL.md`: the approved current objective and milestone scope; it may narrow but not contradict the Specs.
- `docs/STATUS.md`: current verified facts only.
- Decision log: approved hard-to-reverse choices and their rationale.

Stop the affected work on a real conflict. Do not silently choose in code.

## 3. Agent Routing

### Main controller: ORCHESTRATOR_REVIEWER

- Configured `gpt-5.6-sol / xhigh`.
- Owns investigation, product/architecture decisions, Goal/Issue/Task Contracts, ownership, dispatch and independent review.
- Checks the real Diff, tests, runtime evidence and scope.

### Implementation: luna-worker

- Invoke exact custom Agent `luna-worker`, configured `gpt-5.6-luna / max`.
- Give it one approved, bounded Task Contract.
- It does not expand scope, change architecture/public interfaces or approve its own result.
- It does not spawn subagents unless explicitly instructed.
- It preserves user/concurrent changes.

Never fall back to Terra or a default worker. If Luna is unavailable, return:

```text
STATUS: BLOCKED_LUNA_WORKER_UNAVAILABLE
```

Configuration is not runtime identity proof.

## 4. Coding Gate

Feature coding requires an approved active Goal, Ready milestone, one Issue/Task Contract, known baseline/ownership, acceptance checks, exact Luna route and separate authorization for credentials/fees/external effects.

Missing gates allow investigation, planning, docs, no-cost validation and independent review only.

## 5. Implementation Rules

- Advance the next user-visible vertical outcome with the smallest complete change.
- Reuse/deepen existing modules; reject pass-through layers and speculative abstractions.
- Agents propose; Artifact repositories commit; Workflow/Task state stores control and exact references.
- Use exact cross-stage Artifact References; no implicit latest.
- Keep external Providers behind Adapters and paid calls behind explicit Budget Authorization.
- Preserve unaffected Scene media during one-Scene retry/replace.
- Do not introduce generic hashes, formal proofs, corruption frameworks, race loops or future-schema compatibility without a concrete MVP risk.
- Do not delete/reset/overwrite/clean unrelated or concurrent modifications.

## 6. Tests and Evidence

Run focused behavior/integration checks during work and the full regression once before merge:

```bash
PYTHONPATH=src uv run python -m unittest discover -s tests -v
```

Match evidence to risk. Credentials, money, paths and destructive effects require stronger failure/recovery checks; ordinary UI/docs do not. Fake/Fixture success cannot be described as real Provider or product acceptance evidence.

## 7. Git and Review

- One Issue normally maps to one outcome and one PR.
- Branches default to `codex/<issue>-<slug>`.
- Multiple writing agents need disjoint files and stable interfaces.
- The implementer hands off facts; the main controller independently reviews.
- Verdicts: `APPROVED`, `CHANGES_REQUESTED`, `BLOCKED`, `ESCALATE_TO_HUMAN`.
- One bounded correction is normal. If the same design needs another correction cycle, reconsider or park it.
- Update affected Goal/Status facts inside the feature PR; avoid status-only PRs.

## 8. Human Confirmation

Required for Provider/model/credential choice, any fee/cap change, deployment/publication, sensitive data/auth/privacy, irreversible migration, major stack rewrite, product/Goal expansion or weakening an essential PRD invariant.
