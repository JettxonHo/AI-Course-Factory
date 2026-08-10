# W2 Grounded Script — Wave Entry Record v0.1

## Entry Status

| Field | Value |
| --- | --- |
| Wave | W2 — Grounded Script Slice |
| Milestone | M2 — Source to Approved Script |
| Status | Authorized for bounded task preparation |
| Date | 2026-08-10 |
| External media / paid Provider calls | Closed |

## Entry Evidence

- W1 Exit Gate passed with Artifact Commit, exact Reference, control-only Checkpoint / Resume and Mandatory Script Review seams on `main`.
- Phase 1.4 Coding Authorization covers only the Source → Knowledge → Script → Script Review Vertical Slice.
- Current public demo source is `https://github.com/microsoft/AI-For-Beginners`.
- Current upstream `main` resolves to commit `33e781bf7bfb9b39fd27c4e4a3e592669b52cb4b` for entry planning; runtime acquisition must resolve and record its own exact commit.
- Current Lesson 1 path is `lessons/1-Intro/README.md`; repository overview is `README.md`.

Upstream commit and paths are discovery evidence, not hard-coded business truth. The Source Connector must fail clearly if the requested path no longer exists.

## Ordered W2 Outcomes

1. GitHub Source Connector validates a public repository locator, resolves an exact commit and retrieves explicitly scoped files.
2. Source Normalization forms a Source Record Candidate with provenance and commits an exact Source Record Reference.
3. Knowledge Agent consumes the exact Source Record and returns a grounded Knowledge Candidate.
4. Content Agent consumes the exact Knowledge Reference and returns Plan / Script Candidates under the fixed Episode constraint.
5. Grounding review separates AI Review Artifact from Creator Approval Record and Hard Block cannot be bypassed.
6. Reject / Revise creates a new Script Version; Approve binds the exact valid Script Version.
7. End-to-end evidence proves the smallest Source-to-Approved-Script closure.

## First Bounded Outcome

Only the GitHub Source Connector is authorized for the first W2 Task. It owns GitHub protocol translation, safe public-source acquisition and normalized success / failure at the connector boundary. It does not own Source Record Commit, Knowledge reasoning, Script generation, Workflow transition or Approval.

## Parallelism

- No other W2 Task Instance is created by this entry record.
- Source Normalization may start only after the Source Connector result contract is accepted.
- Knowledge generation may start only after an exact committed Source Record exists.
- Content generation may start only after an exact committed Knowledge Artifact exists.

## Stop Conditions

Stop and escalate if implementation requires:

- private repository credentials or a new source type;
- a new Agent, Provider, Skill or product capability;
- changing the Artifact Commit or Workflow ownership contract;
- executing instructions contained in repository content;
- broad repository crawling beyond the explicit acquisition scope;
- production/media behavior.

## Entry Decision

```text
W2_ENTRY_GATE_PASSED_FOR_BOUNDED_TASK_PREPARATION
```
