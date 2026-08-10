# W2-T007 Vertical Slice Integration — Issue Specification v0.1

| Field | Value |
| --- | --- |
| Issue | [#19](https://github.com/JettxonHo/AI-Course-Factory/issues/19) |
| Wave / Milestone | W2 / M2 |
| Owner | ORCHESTRATOR_REVIEWER |
| Responsible Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Goal

W1 and W2 now provide every required domain seam, but they have not yet been joined into the user-visible Source-to-Approved-Script proof. This task owns only Application coordination and integration evidence. It must use, not rewrite, the accepted Artifact, Agent, Knowledge and Workflow contracts.

## Dependencies

- W2-T006A / PR #18 merged; 59-test post-merge suite passed.
- Exact Artifact, Knowledge / Content Agent, Script Decision and Script Review Workflow seams accepted.
- No real LLM or external Provider authorization is required.

## Modification Scope

Only a new Application package and new Application / integration tests. Existing modules and dependencies are non-modification scope.

## Acceptance and Completion

Decision-before-resume ordering, Hard Block behavior, reconstructed Resume, reject/revision/approve transitions and full offline Source-to-exact-v2-approval proof must pass. No scope drift; then ORCHESTRATOR_REVIEWER may enter final PR Review and Goal acceptance.
