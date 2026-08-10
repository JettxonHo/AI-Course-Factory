# W2-T005 Content Agent — Task Package v0.1

## Task Package

| Field | Value |
| --- | --- |
| Package ID | `W2-T005-TP-v0.1` |
| Issue | [#13](https://github.com/JettxonHo/AI-Course-Factory/issues/13) |
| Branch | `agent/w2-t005-content-agent` |
| Wave / Milestone | W2 / M2 |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Objective

Implement the staged, provider-neutral Content Agent public seam described by W2-T005. Use controlled runtimes only. Prove external Plan and Script Commit, exact lineage and immutable revision behavior without changing the Artifact Boundary.

## Must Read

W2-T005 Contract and Issue; Technical Spec §7.3, §7.4 and §7.6 plus Step 5 Artifact identity/dependency rules; Implementation Boundary Agent / Model Runtime rules; accepted Knowledge Agent and Artifact public seams/tests.

## Allowed Files

- `src/ai_course_factory/agents/__init__.py`
- `src/ai_course_factory/agents/runtime.py`
- `src/ai_course_factory/agents/content_agent.py`
- `tests/agents/__init__.py`
- `tests/agents/test_content_agent.py`

Do not modify any other source/test, dependency or baseline file. Preserve concurrent and existing changes.

## Input / Output Contract

- Planning: exact Knowledge + explicit constraints → Course / Episode Plan Candidate Set or safe failure.
- Scripting: exact Knowledge + exact committed Plans + constraints + optional revision context → Script Candidate or safe failure.
- Agent never calls Commit; tests use the public Artifact Boundary externally.
- Real Provider, Prompt and credentials are prohibited.

## Red → Green Sequence

1. Exact Knowledge → Plan Candidate Set using a controlled runtime.
2. External exact Plan Commits and lineage proof.
3. Exact Knowledge + committed Plans → six-Scene grounded Script Candidate.
4. External exact Script Commit and immutable revision to Version 2.
5. Grounding, reference/payload/plan-lineage, context/template and malformed result failures.
6. Runtime failure normalization, import boundary, full regression and compileall.

## Verification

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
git diff --check
```

Return files, TDD red/green evidence, exact Plan / Script references, v1 → v2 revision proof, boundary audit and residual risks. Stop on Provider, Review, Workflow, Artifact or product expansion.
