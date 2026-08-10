# W2-T003 Source Record Candidate — Task Package v0.1

## Task Package

| Field | Value |
| --- | --- |
| Package ID | `W2-T003-TP-v0.1` |
| Issue | [#9](https://github.com/JettxonHo/AI-Course-Factory/issues/9) |
| Branch | `agent/w2-t003-source-record` |
| Wave / Milestone | W2 / M2 |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Objective

Implement the validated Source Record Candidate producer and prove it integrates with the unchanged W1 Artifact Commit seam.

## Must Read

1. W2-T003 Bounded Contract and Issue Specification.
2. Accepted Source Normalization public types/tests/review.
3. Existing Artifact public types, Commit behavior and tests.
4. Technical Spec Source Record, Candidate/Commit and Artifact First sections.

## Allowed Files

- `src/ai_course_factory/knowledge/source_record.py`
- `src/ai_course_factory/knowledge/__init__.py`
- `tests/knowledge/test_source_record_builder.py`

Do not modify Artifact, Connector, Normalization, Workflow, dependencies or governance baseline files.

## Public Test Seam

A small `SourceRecordBuilder`-style API receives accepted normalized material plus explicit Artifact identity / Commit identity and returns `ArtifactCandidate` or safe failure. Integration tests call existing `ArtifactCommitBoundary` separately.

## Red → Green Sequence

1. Failing accepted material → validated Candidate test.
2. Failing Candidate → exact Commit / immutable retrieval test.
3. Failing replay and conflict integration tests.
4. Failing malformed locator/line/blob/order/identity tests.
5. Import/boundary audit, full regression and compileall.

## Verification Commands

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
```

## Stop Conditions

Stop if Artifact implementation changes, direct Commit ownership, external I/O, semantic knowledge extraction, Workflow change or dependency addition is required.

## Handoff

Return the standard readiness status with changed files, red/green evidence, exact committed Reference evidence, full tests, boundary audit and residual risks.
