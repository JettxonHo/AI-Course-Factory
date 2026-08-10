# W1-T002 Workflow Control — Task Package v0.1

## Task Package

| Field | Value |
| --- | --- |
| Package ID | `W1-T002-TP-v0.1` |
| Issue | [#3](https://github.com/JettxonHo/AI-Course-Factory/issues/3) |
| Branch | `agent/w1-t002-workflow-control` |
| Wave / Milestone | W1 / M1 |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Objective

Implement and test the W1-T002 Contract: a real LangGraph control runtime that binds an exact Script Reference, checkpoints control-only state, pauses at Mandatory Script Review and resumes idempotently for Approve, Reject or Revise.

## Must Read

1. `docs/implementation-task/phase-1.4/W1-T002_Workflow_Control_Bounded_Task_Contract_v0.1.md`
2. `docs/implementation-task/phase-1.4/W1-T002_Workflow_Control_Issue_Specification_v0.1.md`
3. Technical Spec §6.2, §6.3, §6.5, §6.8–§6.11, §9.11–§9.13.
4. Implementation Boundary Spec §1, §4 and §6.
5. Existing Artifact public API and tests.
6. Official LangGraph [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) and [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).

## Current Implementation

- `main` contains merged W1-T001 exact Artifact Commit seam with 10 passing tests.
- Branch contains only W1-T002 planning records before implementation.
- Python 3.12.13 and `uv` are available.
- No Python project manifest or LangGraph dependency exists.

## Confirmed Public Test Seam

Test only a public `ScriptReviewWorkflow`-style runtime API that:

- starts or enters review using thread/task identity and exact Script Reference;
- returns a normalized snapshot at pending interrupt;
- resumes with an exact-version Creator decision command;
- returns a normalized completed/revision-required snapshot;
- reconstructs from the same checkpoint adapter.

Do not test private LangGraph node call order or checkpointer internals.

## Allowed Files

- `pyproject.toml`
- `uv.lock`
- `src/ai_course_factory/workflow/__init__.py`
- `src/ai_course_factory/workflow/model.py`
- `src/ai_course_factory/workflow/checkpoint.py`
- `src/ai_course_factory/workflow/script_review.py`
- `tests/workflow/__init__.py`
- `tests/workflow/test_script_review_workflow.py`

Do not modify Artifact source/tests or governance files.

## Runtime Dependency Rule

- Add only official `langgraph` in the current major line (`>=1,<2`) as a project runtime dependency.
- Resolve and commit `uv.lock` using Python 3.12.
- No LangChain model/provider package, database driver or test framework may be added.

## Red → Green Sequence

1. Project/runtime setup and one failing test that starts with a committed Script exact Reference and expects a pending Mandatory Review interrupt.
2. Minimal graph + in-memory checkpoint adapter to pass.
3. Failing reconstruction/resume Approve test using a second runtime with the same adapter; minimal pass.
4. Failing Reject and Revise routing tests; minimal pass.
5. Failing wrong-version / unknown-reference / invalid-action tests; minimal fail-closed pass.
6. Failing equivalent replay and conflicting command-ID tests; minimal idempotency pass.
7. Explicit assertion that checkpointed state contains no Script payload.
8. Full Artifact + Workflow test suite.

## Input / Output Contract

Input is exact Script Reference plus task/thread and Creator command identity/action/target. Output is normalized Workflow snapshot/result only. Script payload remains in Artifact Layer; Creator decision does not become an Approval Artifact in this task.

## Verification Commands

```text
uv lock --python /opt/homebrew/bin/python3.12
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
```

## Stop Conditions

Stop if implementation needs to modify the Artifact seam, add a Provider/model/database, store Script payload in graph state, perform a pre-interrupt side effect, expose raw LangGraph state as the domain API or create a general workflow builder.

## Handoff

Return `READY_FOR_INTEGRATION_REVIEW`, `BLOCKED_WITH_EVIDENCE` or `SPECIFICATION_REVIEW_REQUIRED` with files, red/green evidence, dependency version, full test results, checkpoint payload audit and remaining risk.

