# W2-T001 GitHub Source Connector — Issue Specification v0.1

## Issue Identity

| Field | Value |
| --- | --- |
| Issue | [#5](https://github.com/JettxonHo/AI-Course-Factory/issues/5) |
| Title | Implement safe public GitHub Source Connector |
| Wave / Milestone | W2 / M2 |
| Category | Source Connector |
| Owner | Knowledge Layer / GitHub Source Connector adapter |
| Agent | exact `luna-worker` |
| Status | Issue Created — Package Ready |

## Background

W1 established immutable Artifact and resumable Workflow seams. W2 must begin from a real public Knowledge Source without exposing GitHub protocol to Knowledge Agent or allowing repository content to act as instructions.

## Goal and User Value

Resolve the Microsoft AI-For-Beginners source to an exact upstream commit and retrieve only the explicitly selected overview and Lesson 1 files. This gives every later Knowledge claim a stable provenance root.

## Dependencies and Preconditions

- W1 Exit Gate passed.
- Technical Spec Source Connector boundary is frozen.
- Public GitHub read is authorized; private credentials and paid Provider calls are not.
- Branch `agent/w2-t001-source-connector` is based on the accepted W1 `main`.

## Input Documents

- Approved PRD v0.3 Knowledge Boundary and Demo contract.
- Technical Spec §3 Knowledge Layer, §7 Knowledge Agent boundary, §8.4 Source Connector.
- Implementation Boundary Spec Knowledge Runtime boundary.
- Implementation / Execution Plans M2 / W2.
- W2 Entry Record and W2-T001 Bounded Task Contract.

## Modification Scope

- `src/ai_course_factory/knowledge/__init__.py`
- `src/ai_course_factory/knowledge/source.py`
- `src/ai_course_factory/knowledge/github_connector.py`
- `tests/knowledge/__init__.py`
- `tests/knowledge/test_github_connector.py`

## Non-modification Scope

- Existing Artifact and Workflow source/tests.
- Frozen Step 1–12 documents.
- Agent, Review, Approval, UI, database, Production and Provider modules.
- Project dependencies unless specification review explicitly authorizes one; standard library is sufficient.

## Artifact / Workflow Impact

None in this task. The Connector returns a Source Acquisition Result or Failure and neither commits an Artifact nor advances Workflow.

## Acceptance and Tests

All ten Bounded Task Contract acceptance criteria must be covered by offline public-behavior tests except the separate read-only live smoke check. Tests must not assert private helper call order and must prove that invalid input does not reach transport.

## Risks and Blockers

- SSRF or arbitrary redirect: fixed GitHub hosts and fail-closed redirects.
- Memory amplification: bounded response, file and aggregate sizes.
- Moving upstream branch: resolve exact commit before retrieving files.
- Prompt injection: repository text remains inert data.
- Rate limits / upstream outage: return safe execution failure; do not add credentials or automatic retry.

## Completion Definition

Implementation, offline tests, live smoke, contract review, security review and documentation evidence pass with no scope drift. This Issue does not by itself complete M2.
