# W2-T005 Content Agent — Bounded Task Contract v0.1

## Identity

| Field | Value |
| --- | --- |
| Task | `W2-T005` |
| Issue | [#13](https://github.com/JettxonHo/AI-Course-Factory/issues/13) |
| Wave / Milestone | W2 / M2 |
| Category | Content Agent Runtime |
| Primary Ownership | Agent Layer / Content Agent interface |
| Responsible Agent | exact `luna-worker`; no fallback |

## Objective and Verification Target

Implement the frozen Content Agent as two bounded invocations without adding an Agent:

```text
exact Knowledge Ref + matching Version + explicit content constraints
    → Course Plan Candidate + Episode Plan Candidate
    → external Commit returns exact Plan References
exact Knowledge + exact committed Plan Refs / Versions + constraints
    → grounded Script Candidate
    → external Commit returns exact Script Reference
```

This staged invocation is required because Script lineage must contain exact committed Plan References; a Candidate cannot predict a future Version. Both invocations remain one Content Agent responsibility and one Workflow business step.

## Input Contract

- exact committed `knowledge` Artifact Reference and matching immutable Version;
- explicit audience, series, Episode number/title, language and learning goal;
- explicit Episode Template Constraint: six Scenes, about 60 seconds and 9:16;
- scripting invocation additionally receives exact committed Course / Episode Plan References and matching Versions;
- optional revision context binds the exact prior Script Reference / Version, Creator decision identity and bounded revision instruction;
- provider-neutral Model Runtime port.

No Source Record payload, UI state, chat history, implicit memory, Provider SDK or moving `latest` Reference is accepted.

## Output Contract

Planning success returns a Candidate Set containing:

- one `content_plan` Candidate with role `course`;
- one `content_plan` Candidate with role `episode`;
- both depend exactly on the selected Knowledge Version.

Scripting success returns one validated `script` Candidate:

- dependencies are exactly the selected Knowledge, Course Plan and Episode Plan References;
- contains an ordered Scene collection that satisfies the supplied six-Scene template;
- every Scene references one or more claim IDs present in the selected Knowledge Version;
- a revision reuses Script identity, carries the exact prior Script Reference and never overwrites it.

Neither result is approved. Commit and Workflow progression remain external.

## Acceptance Criteria

1. Exact Knowledge + valid controlled planning result produces Course / Episode Plan Candidates.
2. Plans commit externally through the unchanged Artifact Boundary and return exact References.
3. Exact Knowledge + exact committed Plans + controlled script result produces a Script Candidate with exact three-reference lineage.
4. Six ordered Scenes and target duration are validated from the explicit Template Constraint; the constraint is not encoded in Workflow State shape.
5. Every Scene cites existing Knowledge claim IDs; missing or foreign grounding returns no Candidate.
6. Wrong Artifact type, mismatched Reference / Version, stale-style `latest`, malformed context, plan lineage mismatch or malformed runtime output fails closed.
7. Optional revision context produces a Script Candidate with an exact prior Script Reference; external Commit creates the next immutable Version and preserves history.
8. Runtime failures and raised exceptions are normalized without raw Provider detail.
9. Agent source never imports Commit, Workflow, Review, Provider SDK or network code.
10. Full regression, compileall, import boundary and diff checks pass.

## Non-goals / Stop Conditions

No real Provider, Prompt files, approval, Reviewer, Workflow transition, Source parsing, Storyboard, Timeline, Production, media, UI, API, database or Artifact implementation change. Stop if the exact Plan lineage cannot be represented without modifying a frozen contract, or if a new Agent / Provider / product capability is required.

## Completion Definition

Plan / Script Candidate and external Commit proof, revision proof, tests and independent review pass with no scope drift and no Critical or Important finding.
