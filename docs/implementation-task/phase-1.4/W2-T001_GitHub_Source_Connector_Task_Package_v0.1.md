# W2-T001 GitHub Source Connector — Task Package v0.1

## Task Package

| Field | Value |
| --- | --- |
| Package ID | `W2-T001-TP-v0.1` |
| Issue | [#5](https://github.com/JettxonHo/AI-Course-Factory/issues/5) |
| Branch | `agent/w2-t001-source-connector` |
| Wave / Milestone | W2 / M2 |
| Agent | exact `luna-worker` |
| Status | Ready for Assignment |

## Objective

Implement and test the W2-T001 Contract as a standard-library-only GitHub adapter. The public seam accepts a repository locator and explicit paths, resolves the default branch to an exact commit and returns immutable acquisition data or a normalized safe failure.

## Must Read

1. `W2_Grounded_Script_Wave_Entry_Record_v0.1.md`.
2. `W2-T001_GitHub_Source_Connector_Bounded_Task_Contract_v0.1.md`.
3. `W2-T001_GitHub_Source_Connector_Issue_Specification_v0.1.md`.
4. Technical Spec §3.7, §7.5, §8.4.1–§8.4.3 and §8.12.
5. Existing Artifact / Workflow public seams only to confirm non-interference.

## Current Implementation

- W1 is merged and 17 / 17 tests pass on `main`.
- No Knowledge Layer runtime exists.
- Python 3.12, standard library and the existing project environment are available.
- Upstream discovery currently finds `README.md` and `lessons/1-Intro/README.md`; do not hard-code the discovered commit as runtime truth.

## Allowed Files

- `src/ai_course_factory/knowledge/__init__.py`
- `src/ai_course_factory/knowledge/source.py`
- `src/ai_course_factory/knowledge/github_connector.py`
- `tests/knowledge/__init__.py`
- `tests/knowledge/test_github_connector.py`

Do not modify Artifact, Workflow, governance baseline, dependency or unrelated files.

## Implementation Constraints

- Use the Python standard library; add no dependency.
- Keep transport injectable for offline public behavior tests, while the default transport performs the real read-only GitHub API call.
- Transport accepts Connector-built GitHub API paths, not arbitrary caller URLs.
- Use GitHub repository metadata → commit resolution → exact-commit file reads.
- Decode only bounded UTF-8 text and validate returned path / size / encoding metadata.
- Do not read environment secrets or send credentials.

## Red → Green Sequence

1. Failing valid fixture test for exact commit plus two files; implement the minimal result path.
2. Failing assertion that file reads use the commit SHA; pin before file retrieval.
3. Failing invalid locator / unsafe path tests; validate before transport.
4. Failing missing / malformed / encoding tests; normalize safe atomic Failure.
5. Failing per-file / aggregate / API response limit tests; add bounded reads.
6. Failing transport error test; normalize without raw body / exception leakage.
7. Immutability and equivalent repeat behavior.
8. Full regression suite, compile check and separate live smoke.

## Verification Commands

```text
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m unittest discover -s tests -p 'test_*.py' -v
PYTHONPATH=src uv run --python /opt/homebrew/bin/python3.12 python -m compileall -q src tests
```

Run the live Microsoft smoke through the public Connector API after offline tests. Report exact commit, returned paths and sizes, but do not persist source payload in governance documents.

## Stop Conditions

Stop if implementation needs a credential, a non-GitHub source, broad crawl, Artifact Commit, Agent reasoning, Workflow change, new dependency or execution of repository content.

## Handoff

Return `READY_FOR_INTEGRATION_REVIEW`, `BLOCKED_WITH_EVIDENCE` or `SPECIFICATION_REVIEW_REQUIRED` with changed files, red / green evidence, full tests, live smoke result, security boundary audit and residual risks.
