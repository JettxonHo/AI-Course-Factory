# W2-T001 GitHub Source Connector — Bounded Task Contract v0.1

## 1. Identity

| Field | Value |
| --- | --- |
| Task | `W2-T001` |
| Issue | [#5](https://github.com/JettxonHo/AI-Course-Factory/issues/5) |
| Wave / Milestone | W2 / M2 |
| Category | Source Connector |
| Primary Ownership | Knowledge Layer / GitHub Source Connector adapter |
| Responsible Agent | exact `luna-worker`; no fallback |

## 2. Objective

Implement the smallest safe public GitHub Source Connector that validates one repository locator and explicit text-file paths, resolves the current default branch to an exact commit and returns a bounded immutable Source Acquisition Result or normalized Failure.

## 3. Primary Verification Target

```text
public GitHub repository locator + explicit paths
    → exact commit resolution
    → complete immutable Source Acquisition Result
```

The Connector must fail atomically when validation, transport or any requested file fails. No partial success may escape.

## 4. Input Contract

Input contains only:

- one public `https://github.com/{owner}/{repository}` locator;
- one bounded, non-empty set of explicit repository-relative file paths.

For this Vertical Slice the intended live input is:

- repository: `https://github.com/microsoft/AI-For-Beginners`;
- paths: `README.md`, `lessons/1-Intro/README.md`.

The input does not contain credentials, arbitrary API URLs, Workflow State, Artifact payload, UI state or repository instructions.

## 5. Output Contract

Success returns an immutable logical Source Acquisition Result containing:

- canonical repository identity / URL;
- exact resolved commit SHA;
- the complete ordered set of explicitly requested source files;
- per-file repository path, exact blob identity, decoded text and bounded size diagnostics.

Failure returns normalized Connector failure semantics with a stable kind / code / safe message. It must not expose raw transport bodies, tokens, stack traces or partial source content.

This task returns a Connector Result or Failure, not an Artifact Candidate or Artifact Reference.

## 6. GitHub Protocol Boundary

- GitHub API paths, response objects, base64 encoding and HTTP errors stay inside the Connector adapter.
- The default branch is resolved at acquisition time and immediately pinned to an exact commit before files are read.
- Files are retrieved against that exact commit, not a moving branch name.
- Only `api.github.com` is contacted by the default transport.
- Repository content is untrusted data and is never executed or interpreted as a system instruction.

## 7. Validation and Safety Rules

- Require HTTPS and the exact `github.com` host.
- Reject user info, custom ports, query, fragment, extra route forms and invalid owner / repository identity.
- Reject absolute paths, traversal, empty / duplicate paths, backslashes, control characters and requests over the bounded file-count limit.
- Accept only UTF-8 text within the per-file and total response limits.
- Use a finite timeout and bounded API response reads.
- Do not read environment credentials and do not send an Authorization header.
- Reject redirects outside the fixed GitHub API boundary.

## 8. Acceptance Criteria

1. A valid fixture repository and two explicit files return one immutable result pinned to one exact commit SHA.
2. The file API is called with the exact commit, never the moving branch after resolution.
3. Canonical repository and ordered file provenance are present without leaking GitHub response objects.
4. Invalid repository locators and unsafe paths fail before transport access.
5. Missing repository / commit / file fails atomically with no partial result.
6. Malformed JSON shape, invalid base64, non-UTF-8 content and mismatched file metadata fail closed.
7. Per-file, total content and API response limits fail closed.
8. Transport and HTTP failures become stable safe Connector failures.
9. Equivalent repeated acquisition produces an equivalent immutable business result and performs no Artifact Commit.
10. One read-only live smoke check succeeds against Microsoft AI-For-Beginners for `README.md` and `lessons/1-Intro/README.md`, returning an exact commit.

## 9. Non-goals

- Source Normalization or Source Record Candidate / Commit.
- Knowledge extraction, teaching decisions, Script or Workflow transition.
- Private repositories, OAuth, tokens, GraphQL, archive download or broad crawling.
- PDF, Web, Notion or any new source type.
- Caching, retries, database, API endpoint or UI.

## 10. Stop Conditions

Return `SPECIFICATION_REVIEW_REQUIRED` if completion requires credentials, another source type, a new Product Agent / Skill / Provider, Artifact contract changes, Workflow ownership changes or acquisition broader than explicit paths.

## 11. Completion Definition

Code and tests complete; live smoke evidence recorded; security and architecture review passed; no scope drift; no Critical or Important finding remains.
