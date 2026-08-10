# W2-T006A Script Decision Context — Task Package v0.1

| Field | Value |
| --- | --- |
| Package ID | `W2-T006A-TP-v0.1` |
| Issue | [#17](https://github.com/JettxonHo/AI-Course-Factory/issues/17) |
| Branch | `agent/w2-t006a-decision-context` |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Allowed Files

- `src/ai_course_factory/artifacts/script_decision.py`
- `tests/artifacts/test_script_decision.py`

No other file may change.

## Red → Green

1. Persist bounded Revise context.
2. Missing / malformed / oversized Reject or Revise context fails closed.
3. Context is included in replay / conflict behavior.
4. Forged assessment, Hard Block and full regression remain green.

## Verification

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
git diff --check
```
