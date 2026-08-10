# W2-T004 Knowledge Agent — Issue Specification v0.1

## Issue Identity

| Field | Value |
| --- | --- |
| Issue | [#11](https://github.com/JettxonHo/AI-Course-Factory/issues/11) |
| Title | Implement grounded Knowledge Agent contract |
| Wave / Milestone | W2 / M2 |
| Owner | Agent Layer / Knowledge Agent interface |
| Engineering Agent | exact `luna-worker` |
| Status | Issue Created — Package Ready |

## Background and Goal

An exact Source Record now exists. Implement only the Knowledge Agent reasoning boundary and the minimal provider-neutral runtime port it consumes, proving grounded Knowledge Candidate lineage without authorizing a real LLM Provider.

## Modification Scope

- `src/ai_course_factory/agents/__init__.py`
- `src/ai_course_factory/agents/runtime.py`
- `src/ai_course_factory/agents/knowledge_agent.py`
- `tests/agents/__init__.py`
- `tests/agents/test_knowledge_agent.py`

## Non-modification Scope

Artifact, Knowledge Source, Normalization and Workflow source/tests; dependencies; frozen baseline; Content/Production/Reviewer modules.

## Artifact / Workflow Impact

Agent returns a Knowledge Candidate with exact Source Record dependency. Tests call existing Commit externally. Agent never writes Artifact or lifecycle state.

## Risk and Completion

Risks are evidence forgery, source/payload mismatch, Provider leakage and responsibility drift. All Bounded Contract criteria, full regression and architecture/security review must pass. This Issue does not complete Script or M2.
