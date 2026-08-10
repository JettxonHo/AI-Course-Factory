# W2-T002 Source Normalization — Task Package v0.1

## Task Package

| Field | Value |
| --- | --- |
| Package ID | `W2-T002-TP-v0.1` |
| Issue | [#7](https://github.com/JettxonHo/AI-Course-Factory/issues/7) |
| Branch | `agent/w2-t002-source-normalization` |
| Wave / Milestone | W2 / M2 |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Objective

Implement the deterministic, lossless Source Normalization public seam defined by W2-T002. Use the existing accepted acquisition result; perform no network, Artifact or Agent operation.

## Must Read

1. W2 Grounded Script Entry Record.
2. W2-T002 Bounded Contract and Issue Specification.
3. W2-T001 Connector public types/tests and Integration Review.
4. Technical Spec §8.4.1–§8.4.3, §7.5 Input Boundary and Artifact/Workflow separation.

## Allowed Files

- `src/ai_course_factory/knowledge/normalization.py`
- `src/ai_course_factory/knowledge/__init__.py`
- `tests/knowledge/test_source_normalization.py`

Do not modify Connector, Artifact, Workflow, dependencies or governance baseline files.

## Public Test Seam

Expose a small `SourceNormalizer`-style API that accepts `SourceAcquisitionResult` and returns Normalized Source Material or Normalization Failure. Public value objects must be immutable and contain only provider-neutral source/provenance semantics.

## Red → Green Sequence

1. Failing two-file lossless normalization test; add minimum unit/result objects and normalizer.
2. Failing exact line and nested-heading provenance assertions; implement hierarchy.
3. Failing fenced-code heading test; add bounded fence awareness.
4. Failing malformed provenance / size / duplicate / empty tests; fail atomically.
5. Prompt-like text inertness and result immutability.
6. Equivalent repeat behavior, full regression and compile check.

## Verification Commands

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
```

## Stop Conditions

Stop if a network fetch, Artifact Candidate / Commit, semantic knowledge extraction, Agent, new dependency, full Markdown engine or contract modification becomes necessary.

## Handoff

Return `READY_FOR_INTEGRATION_REVIEW`, `BLOCKED_WITH_EVIDENCE` or `SPECIFICATION_REVIEW_REQUIRED` with changed files, red/green evidence, reconstruction/provenance results, full tests and residual risks.
