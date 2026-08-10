# W2-T006A Script Decision Context — Issue Specification v0.1

| Field | Value |
| --- | --- |
| Issue | [#17](https://github.com/JettxonHo/AI-Course-Factory/issues/17) |
| Wave / Milestone | W2 / M2 |
| Owner | ORCHESTRATOR_REVIEWER |
| Responsible Agent | exact `luna-worker` |
| Status | Ready for Assignment |

W2-T006 correctly persists exact Creator decisions, but the frozen Approval Record contract also requires decision context. This correction keeps revision intent durable and prevents later Content regeneration from using uncommitted UI state.

Modification scope is limited to the existing Script decision module, public export only if needed, and its tests. The single verification target is durable exact-version revision context. Completion requires public behavior tests, full regression and no scope drift.
