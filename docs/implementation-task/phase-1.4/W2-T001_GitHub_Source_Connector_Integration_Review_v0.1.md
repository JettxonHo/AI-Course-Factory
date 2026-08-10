# W2-T001 GitHub Source Connector — Integration Review v0.1

## Review Status

| Field | Value |
| --- | --- |
| Issue | [#5](https://github.com/JettxonHo/AI-Course-Factory/issues/5) |
| Task Package | `W2-T001-TP-v0.1` |
| Branch | `agent/w2-t001-source-connector` |
| Reviewer | ORCHESTRATOR_REVIEWER |
| Result | Approved for PR Review |
| Date | 2026-08-10 |

## Context

The change implements only the GitHub Source Connector boundary. It validates a public GitHub repository locator and explicit source paths, resolves the upstream default branch to an exact commit, and retrieves all requested UTF-8 text files against that commit. It returns an immutable Source Acquisition Result or normalized Failure; it does not normalize content, commit a Source Record, invoke an Agent or advance Workflow.

## Test Review

Offline public-behavior tests cover:

- exact-commit resolution before ordered file acquisition;
- repository and path validation before transport;
- missing repository, commit or file without partial success;
- malformed response, base64, UTF-8 and file metadata;
- exact 40-hex commit / blob identity validation;
- API response, file and aggregate size limits;
- safe transport failure normalization;
- immutable result and equivalent repeat behavior.

The tests would fail if file reads used the moving branch, unsafe inputs reached transport, malformed provenance was accepted, one successful file escaped beside a failed file, source text was mutable or raw transport details leaked.

## Five-axis Review

### Correctness — Passed

- Acquisition orders repository metadata → exact commit → exact-commit file reads.
- Success contains one canonical repository identity, exact commit and ordered complete file set.
- Commit and blob identifiers must be canonical 40-character hexadecimal Git SHAs.
- Every requested file must match path, type, declared byte length, base64 encoding and UTF-8 decoding.
- Failure is atomic; no partial Source Acquisition Result is returned.

### Readability and Simplicity — Passed

- The public API contains only `GitHubSourceConnector`, `SourceAcquisitionResult`, `SourceConnectorFailure` and `SourceFile`.
- The implementation uses only the standard library and the accepted Knowledge Layer boundary.
- Speculative aliases and coercive result behavior were removed during review.

### Architecture — Passed

- GitHub protocol, response shape, encoding and transport errors stay inside the Connector adapter.
- Repository text remains inert untrusted data and is not treated as an instruction.
- No Artifact Commit, Agent, Workflow, Review, Approval, UI, database or Production responsibility crosses the task boundary.
- Failure kinds remain within the frozen `validation`, `execution` and `source_access` Connector semantics.

### Security — Passed

- Only HTTPS `github.com/{owner}/{repository}` input and Connector-built `api.github.com` requests are allowed.
- User info, ports, query, fragment, traversal, control characters, duplicate paths and unsafe redirect targets fail closed.
- Response, file-count, per-file and aggregate size limits bound untrusted input.
- No credentials, environment secrets, Authorization header, shell, dynamic execution or raw error/body leakage exists.

### Performance — Passed for W2-T001 scope

- Only explicitly requested files are fetched; there is no recursive crawl or archive download.
- File count and total bytes are bounded.
- Sequential acquisition is appropriate for the two-file Vertical Slice and avoids premature concurrency infrastructure.

## Verification

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
Ran 24 tests
OK

PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
Passed
```

Read-only live smoke through the public Connector API:

| Evidence | Value |
| --- | --- |
| Repository | `https://github.com/microsoft/AI-For-Beginners` |
| Exact commit | `33e781bf7bfb9b39fd27c4e4a3e592669b52cb4b` |
| `README.md` | 28,827 bytes; blob `229d738c43730add39f7e964e61c71b155e7453d` |
| `lessons/1-Intro/README.md` | 16,022 bytes; blob `6b29b141e0f0f81477e16bee4e4d1e6222d0579c` |
| Total | 44,849 bytes |

Additional evidence:

- `git diff --check` passed.
- Changed source/tests remain within the five-file Task Package allowlist.
- No dependency or frozen baseline document changed.

## Findings

No Critical or Important findings remain. Review required exact Git SHA validation, frozen Failure kind normalization and removal of speculative public aliases; all were resolved with red-to-green evidence and live revalidation.

## Verdict

```text
READY_FOR_PR_REVIEW
```
