# W2-T007 Vertical Slice Integration — Task Package v0.1

| Field | Value |
| --- | --- |
| Package ID | `W2-T007-TP-v0.1` |
| Issue | [#19](https://github.com/JettxonHo/AI-Course-Factory/issues/19) |
| Branch | `agent/w2-t007-vertical-slice` |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Allowed Files

- `src/ai_course_factory/application/__init__.py`
- `src/ai_course_factory/application/script_review.py`
- `tests/application/__init__.py`
- `tests/application/test_script_review_service.py`
- `tests/integration/__init__.py`
- `tests/integration/test_vertical_slice.py`

Do not modify any existing source/test, dependency or baseline file. Preserve existing and concurrent work.

## Required Implementation

- Minimal Application service/value objects for start and decision handling.
- Resolve exact Script dependencies through the public Artifact interface.
- Validate pending checkpoint before decision persistence.
- Issue assessment and persist exact Creator decision before calling Workflow Resume.
- Return normalized application success/pending/failure without leaking raw exceptions or Artifact payload into control state.
- Offline integration test using fixture GitHub transport and controlled model runtimes.

## Red → Green Sequence

1. Valid Script → assessment + pending mandatory gate.
2. Hard Block Approve rejected; Workflow remains pending.
3. Decision persistence is observable before real Workflow Resume.
4. Exact pending-checkpoint mismatch and retry behavior.
5. Complete fixture Source → Knowledge → Plan → Script v1 Reject → Script v2 Approve flow with reconstructed Resume.
6. Full regression, compileall, diff and import/scope audit.

## Verification

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
git diff --check
```

Return TDD evidence, exact Reference chain, checkpoint / decision ordering proof, final v2 approval state, scope audit and residual risks. Stop on any frozen module change or external Provider need.
