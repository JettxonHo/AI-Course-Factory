# W2-T002 Source Normalization — Task Record v0.1

## Status

| Field | Value |
| --- | --- |
| Task | `W2-T002` |
| Issue | [#7](https://github.com/JettxonHo/AI-Course-Factory/issues/7) |
| Package | `W2-T002-TP-v0.1` |
| Branch | `agent/w2-t002-source-normalization` |
| Ownership | Knowledge Layer / Source Normalization Skill |
| State | Integration Review Passed — Ready for PR Review |
| Coding | Complete within bounded task scope |

## Gate Evidence

| Gate | Result |
| --- | --- |
| W2-T001 merged and post-merge suite | Passed — PR #6 / 24 tests |
| Single ownership / verification target | Passed |
| Connector Result contract | Accepted |
| Issue and Package lineage | Passed |
| Exact luna-worker route | Ready; no fallback |
| Network / credential / Provider | Not required and not authorized |
| Full regression suite | Passed — 31 / 31 |
| Lossless provenance review | Passed |
| Architecture / security review | Passed — no Critical or Important findings remain |

## Expected Result

Exact acquired source text becomes lossless immutable source units with complete commit/blob/path/heading/line provenance. No Candidate, Artifact, Agent or Workflow behavior is included.

## Delivery Evidence

- Exact `luna-worker` changed only the three-file allowlist.
- ORCHESTRATOR_REVIEWER verified lossless reconstruction, provenance, boundaries and safe failures.
- Integration review: `W2-T002_Source_Normalization_Integration_Review_v0.1.md`.
- No Connector, Artifact, Workflow, Agent, dependency or frozen baseline contract changed.
