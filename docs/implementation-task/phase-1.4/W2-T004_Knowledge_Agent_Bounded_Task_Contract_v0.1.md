# W2-T004 Knowledge Agent — Bounded Task Contract v0.1

## Identity

| Field | Value |
| --- | --- |
| Task | `W2-T004` |
| Issue | [#11](https://github.com/JettxonHo/AI-Course-Factory/issues/11) |
| Wave / Milestone | W2 / M2 |
| Category | Knowledge Agent Runtime |
| Primary Ownership | Agent Layer / Knowledge Agent interface |
| Responsible Agent | exact `luna-worker`; no fallback |

## Objective and Verification Target

Implement the frozen Knowledge Agent contract over a provider-neutral Model Runtime port:

```text
exact Source Record Ref + matching resolved payload + explicit task constraints
    → normalized model result
    → grounded validated Knowledge Artifact Candidate
```

The Agent returns a Candidate or safe failure. It does not Commit, select a Version, call GitHub protocol, advance Workflow or approve content.

## Input Contract

- exact committed `source_record` Artifact Reference;
- resolved immutable Source Record payload matching that Reference;
- explicit Task Context: course, Lesson 1 scope, language and audience intent;
- frozen Knowledge Boundary: summary / rewrite / teaching expression allowed, untraceable fact addition forbidden;
- explicit Knowledge Artifact identity and logical Commit identity;
- provider-neutral Model Runtime port.

No UI state, chat history, implicit memory, Provider SDK or moving `latest` Reference is accepted.

## Model Runtime Port

Define only the smallest shared logical request/result/failure objects and invocation protocol needed by the Agent. The port isolates provider response shape. This task implements no Provider, SDK, credential, Prompt file, model choice, retry or hidden memory.

## Output Contract

Success returns a validated `knowledge` Artifact Candidate with:

- exact Source Record dependency;
- repository/course structure summary and Lesson 1 focus;
- ordered knowledge claims with stable IDs, statements, confidence and one or more exact evidence locators;
- gaps/ambiguities and bounded model diagnostics;
- provenance linking the invocation purpose and cited evidence.

Failure returns `validation` or `execution` semantics with no partial Candidate.

## Acceptance Criteria

1. Exact Source Record ref + matching payload + controlled valid runtime output produces a Knowledge Candidate.
2. Candidate dependency is exactly the supplied Source Record Version.
3. Every claim cites at least one locator present in that Source Record; foreign/missing evidence returns no Candidate.
4. Candidate commits through the unchanged Artifact Boundary and exact retrieval preserves lineage.
5. Wrong Artifact type, malformed Reference/payload, payload/reference mismatch, missing context or `latest` identity fails before runtime where applicable.
6. Runtime receives only explicit source/task/knowledge constraints; repository instruction text remains data.
7. Runtime technical failure and malformed output are normalized without raw Provider detail.
8. Duplicate claim IDs, empty statements, invalid confidence or unbounded structures fail closed.
9. Agent source never imports Commit, Workflow, GitHub transport or Provider SDK.
10. Full regression and compileall pass.

## Non-goals / Stop Conditions

No real Provider, Prompt engineering, Knowledge approval, Script, Reviewer, Workflow, retry, memory, RAG, Source mutation or Artifact modification. Stop if any is required, or if the frozen Agent/Runtime contracts are insufficient.

## Completion Definition

Knowledge Candidate/Commit proof, tests and review pass with no scope drift and no Critical or Important finding.
