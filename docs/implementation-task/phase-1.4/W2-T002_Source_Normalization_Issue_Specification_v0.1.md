# W2-T002 Source Normalization — Issue Specification v0.1

## Issue Identity

| Field | Value |
| --- | --- |
| Issue | [#7](https://github.com/JettxonHo/AI-Course-Factory/issues/7) |
| Title | Normalize acquired GitHub source material |
| Wave / Milestone | W2 / M2 |
| Category | Source Normalization |
| Owner | Knowledge Layer / Source Normalization Skill |
| Agent | exact `luna-worker` |
| Status | Issue Created — Package Ready |

## Background

W2-T001 now returns a complete exact-commit Source Acquisition Result. Knowledge Agent must not consume GitHub response formats or unstructured transport state, so this task creates the provider-neutral, provenance-preserving material seam first.

## Goal and User Value

Turn the selected Microsoft repository overview and Lesson 1 Markdown into stable content units that downstream reasoning can cite by exact file and lines without altering the source.

## Dependencies and Preconditions

- Issue #5 closed and PR #6 merged.
- W2-T001 live and offline evidence passed.
- Source Normalization Skill contract is frozen.

## Modification Scope

- `src/ai_course_factory/knowledge/normalization.py`
- `src/ai_course_factory/knowledge/__init__.py`
- `tests/knowledge/test_source_normalization.py`

## Non-modification Scope

- Existing Connector, Artifact and Workflow source/tests.
- Project dependencies and frozen Step 1–12 documents.
- Agent, Review, Approval, UI, database and Production modules.

## Artifact / Workflow Impact

None. Normalization returns a Skill Result or Failure. It does not create a Candidate, commit a Source Record or advance lifecycle.

## Acceptance and Test Requirements

All ten Bounded Task Contract criteria must pass through public normalization behavior. Tests must prove lossless reconstruction and exact line provenance without asserting private helper order.

## Risks / Blockers

- Content loss at section split: assert exact reconstruction.
- False headings in code: fence-aware minimal splitter.
- Prompt injection: preserve as inert text; no execution surface.
- Scope growth into semantic parsing: stop at structural source units.

## Completion Definition

Implementation, offline regression, architecture/security review and documentation evidence pass with no scope drift. This Issue does not complete the Source Record outcome or M2.
