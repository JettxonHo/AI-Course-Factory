# W2-T003 Source Record Candidate — Issue Specification v0.1

## Issue Identity

| Field | Value |
| --- | --- |
| Issue | [#9](https://github.com/JettxonHo/AI-Course-Factory/issues/9) |
| Title | Build validated Source Record Candidate |
| Wave / Milestone | W2 / M2 |
| Owner | Knowledge Layer / Source Record Candidate producer |
| Agent | exact `luna-worker` |
| Status | Issue Created — Package Ready |

## Background

W2-T001 and W2-T002 now provide exact acquired and lossless normalized source material. This task establishes the first Artifact Graph business record without letting the normalization Skill or Candidate producer own Commit.

## Modification Scope

- `src/ai_course_factory/knowledge/source_record.py`
- `src/ai_course_factory/knowledge/__init__.py`
- `tests/knowledge/test_source_record_builder.py`

## Non-modification Scope

- Artifact, Connector, Normalization and Workflow source/tests.
- Dependencies and frozen Step 1–12 documents.
- Agent, Reviewer, Approval, UI, database and Production modules.

## Artifact / Workflow Impact

The new producer returns a Source Record Candidate. Tests invoke the existing public Artifact Commit seam to verify integration. The producer itself does not Commit, select the Reference or advance Workflow.

## Acceptance and Risk

All ten Bounded Contract criteria must pass through public APIs. Main risks are provenance drift, mutable payload, implicit Version selection and accidental Commit ownership; each must fail closed or be excluded by construction.

## Completion Definition

Implementation, full tests, architecture/security review and documentation pass. This Issue completes the Source Record outcome but not Knowledge generation or M2.
