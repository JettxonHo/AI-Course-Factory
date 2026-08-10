# W2-T001 GitHub Source Connector — Task Record v0.1

## Status

| Field | Value |
| --- | --- |
| Task | `W2-T001` |
| Issue | [#5](https://github.com/JettxonHo/AI-Course-Factory/issues/5) |
| Package | `W2-T001-TP-v0.1` |
| Branch | `agent/w2-t001-source-connector` |
| Ownership | Knowledge Layer / GitHub Source Connector adapter |
| State | Integration Review Passed — Ready for PR Review |
| Coding | Complete within bounded task scope |

## Gate Evidence

| Gate | Result |
| --- | --- |
| W1 Exit and post-merge tests | Passed |
| W2 Entry | Passed for bounded task preparation |
| Single ownership / verification target | Passed |
| Issue and Package lineage | Passed |
| Exact luna-worker route | Ready; no fallback |
| Public GitHub read | Authorized within Source Connector scope |
| Private credential / paid Provider | Not authorized and not required |
| Offline public behavior suite | Passed — 24 / 24 full suite |
| Live Microsoft source smoke | Passed — exact commit and two requested paths |
| Architecture / security review | Passed — no Critical or Important findings remain |

## Expected Result

One public GitHub locator plus explicit file paths produces a complete immutable Source Acquisition Result pinned to an exact commit, or a normalized safe Failure. No Artifact, Agent or Workflow behavior is included.

## Delivery Evidence

- Exact `luna-worker` modified only the five-file allowlist.
- ORCHESTRATOR_REVIEWER verified correctness, simplicity, architecture, security and bounded performance.
- Integration review: `W2-T001_GitHub_Source_Connector_Integration_Review_v0.1.md`.
- No dependency, Artifact, Workflow, Agent or frozen baseline contract changed.
