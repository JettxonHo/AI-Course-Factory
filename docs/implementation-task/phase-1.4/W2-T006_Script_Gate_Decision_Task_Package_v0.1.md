# W2-T006 Script Gate Decision — Task Package v0.1

## Task Package

| Field | Value |
| --- | --- |
| Package ID | `W2-T006-TP-v0.1` |
| Issue | [#15](https://github.com/JettxonHo/AI-Course-Factory/issues/15) |
| Branch | `agent/w2-t006-script-decision` |
| Wave / Milestone | W2 / M2 |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Objective

Implement a deterministic Script Gate assessment and local immutable Creator Approval Record seam. It must reject Approve under Hard Block and must not call Workflow.

## Must Read

W2-T006 Contract/Issue; Technical Spec §7.8, §9.7–§9.8; Implementation Boundary §6.2 and §6.4; accepted Artifact, Content Agent and Script Workflow public contracts/tests.

## Allowed Files

- `src/ai_course_factory/artifacts/__init__.py`
- `src/ai_course_factory/artifacts/script_decision.py`
- `tests/artifacts/test_script_decision.py`

Do not modify any other source/test, dependency or baseline file. Preserve existing and concurrent changes.

## Red → Green Sequence

1. Valid exact Script / Knowledge / Plans → Pass assessment.
2. Foreign claim and exact lineage / required format mutation → Hard Block.
3. Pass → immutable exact Approve record.
4. Hard Block → Approve refused with no record; Reject / Revise accepted.
5. Equivalent replay and conflicting decision identity.
6. Existing Script immutability, import boundary, full regression and compileall.

## Verification

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
git diff --check
```

Return files, TDD evidence, Pass / Hard Block examples, exact Approval Record proof, idempotency result, boundary audit and residual risks. Stop on Workflow, Reviewer, Provider or product expansion.
