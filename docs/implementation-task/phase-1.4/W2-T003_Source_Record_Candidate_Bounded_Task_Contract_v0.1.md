# W2-T003 Source Record Candidate — Bounded Task Contract v0.1

## Identity

| Field | Value |
| --- | --- |
| Task | `W2-T003` |
| Issue | [#9](https://github.com/JettxonHo/AI-Course-Factory/issues/9) |
| Wave / Milestone | W2 / M2 |
| Category | Source Record Candidate boundary |
| Primary Ownership | Knowledge Layer / Source Record Candidate producer |
| Responsible Agent | exact `luna-worker`; no fallback |

## Objective

Build a validated `source_record` Artifact Candidate from accepted Normalized Source Material. Prove the unchanged Artifact Commit Boundary commits it as an immutable Version and returns an exact Reference. The builder does not execute Commit.

## Primary Verification Target

```text
accepted Normalized Source Material
    → validated Source Record Candidate
    → existing Artifact Commit Boundary
    → exact immutable Source Record Reference
```

## Input Contract

- `NormalizedSourceMaterial` with exact repository / commit and ordered units.
- Explicit stable Source Record identity for the current task/source scope.
- Explicit logical Commit identity for idempotent Commit.

No raw GitHub response, Workflow State, UI state, chat history, Provider context or implicit current Version is accepted.

## Output Contract

Success returns an `ArtifactCandidate` with:

- `artifact_type = source_record`;
- explicit stable identity and logical Commit ID;
- provider-neutral payload containing source kind, canonical repository, exact commit and lossless normalized units;
- explicit provenance derived from exact repository / commit and unit locators;
- explicit empty dependency tuple for the first Source Record;
- validation passed, but no committed Version or Workflow transition.

Failure returns safe `validation` or `execution` semantics without a partial Candidate.

## Validation Rules

1. Validate material type, canonical repository identity, exact commit and non-empty unit tuple.
2. Validate each unit's path/blob/heading/line/text and deterministic locator against material provenance.
3. Units for each file must be ordered, line-contiguous and keep one blob identity.
4. Source Record identity and Commit identity must be explicit non-empty strings.
5. Repository text remains inert payload; the builder never evaluates or interprets it.
6. No `latest`, mutable payload, implicit dependency or direct Artifact write is allowed.

## Acceptance Criteria

1. Accepted two-file normalized material produces one validated `source_record` Candidate.
2. Candidate payload preserves exact repository, commit, all ordered units and text.
3. Candidate provenance contains exact repository/commit root and unit locators.
4. Existing `ArtifactCommitBoundary.commit()` returns Version 1 exact Source Record Reference without modification.
5. Exact retrieval preserves immutable content; caller mutation cannot alter it.
6. Equivalent build and Commit replay returns the same exact Reference.
7. Conflicting reuse of logical Commit ID still fails through the existing Artifact contract.
8. Invalid material, inconsistent locator/line/blob, invalid identity or Commit ID returns no Candidate.
9. Builder source imports Artifact public types only and never calls Commit or Workflow.
10. Full regression and Python compilation pass.

## Non-goals

- Source acquisition or normalization behavior.
- Changing Artifact Candidate, Commit, Version or Reference contracts.
- Source Record revision, stale propagation or persistence.
- Knowledge Agent, Model Runtime, Script, Workflow, Review or Approval.

## Stop Conditions

Stop if completion needs Artifact source modification, direct Commit ownership, Workflow change, semantic knowledge inference, external Provider, new dependency or a new Artifact type.

## Completion Definition

Code/tests/review pass; exact Source Record Commit evidence exists; no scope drift and no Critical or Important finding remains.
