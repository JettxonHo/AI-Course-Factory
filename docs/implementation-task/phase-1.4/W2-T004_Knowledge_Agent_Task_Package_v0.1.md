# W2-T004 Knowledge Agent — Task Package v0.1

## Task Package

| Field | Value |
| --- | --- |
| Package ID | `W2-T004-TP-v0.1` |
| Issue | [#11](https://github.com/JettxonHo/AI-Course-Factory/issues/11) |
| Branch | `agent/w2-t004-knowledge-agent` |
| Wave / Milestone | W2 / M2 |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Objective

Implement provider-neutral Model Runtime logical types/port and the grounded Knowledge Agent public seam. Use a controlled runtime only in tests; no real Provider call.

## Must Read

W2-T004 Contract/Issue; Technical Spec §7.3–§7.5, §7.9–§7.11; Implementation Boundary Model Runtime rules; accepted Source Record and Artifact seams/tests.

## Allowed Files

- `src/ai_course_factory/agents/__init__.py`
- `src/ai_course_factory/agents/runtime.py`
- `src/ai_course_factory/agents/knowledge_agent.py`
- `tests/agents/__init__.py`
- `tests/agents/test_knowledge_agent.py`

Do not modify any existing source/test, dependency or baseline file.

## Red → Green Sequence

1. Valid exact Source Record → grounded Candidate using a controlled runtime.
2. Candidate → external exact Commit integration.
3. Foreign/missing evidence and malformed claim output.
4. Reference/payload/context validation before invocation.
5. Runtime failure normalization and explicit-context audit.
6. Import boundary, full regression and compileall.

## Verification

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
```

Return standard readiness status with files, TDD evidence, exact Knowledge Reference proof, context/evidence audit and residual risks. Stop on Provider or contract expansion.
