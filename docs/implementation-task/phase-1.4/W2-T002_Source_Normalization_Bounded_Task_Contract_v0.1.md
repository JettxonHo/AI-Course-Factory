# W2-T002 Source Normalization — Bounded Task Contract v0.1

## Identity

| Field | Value |
| --- | --- |
| Task | `W2-T002` |
| Issue | [#7](https://github.com/JettxonHo/AI-Course-Factory/issues/7) |
| Wave / Milestone | W2 / M2 |
| Category | Source Normalization |
| Primary Ownership | Knowledge Layer / Source Normalization Skill |
| Responsible Agent | exact `luna-worker`; no fallback |

## Objective

Transform one complete `SourceAcquisitionResult` into immutable provider-neutral Normalized Source Material whose ordered content units preserve exact repository, commit, blob, path, heading and line-range provenance without adding, deleting, summarizing or executing source text.

## Primary Verification Target

```text
complete exact-commit Source Acquisition Result
    → ordered immutable normalized units
    → lossless text + exact line provenance
```

## Input Contract

- A successful `SourceAcquisitionResult` from the accepted W2-T001 public seam.
- Exact repository identity and 40-hex commit SHA.
- A non-empty ordered tuple of exact-path UTF-8 Source Files with 40-hex blob identity and declared byte sizes.

No GitHub response object, URL to fetch, Workflow State, Artifact payload, chat memory or provider context is accepted.

## Output Contract

Success returns immutable Normalized Source Material containing:

- canonical repository URL / identity and exact commit;
- ordered normalized source units;
- for each unit: deterministic locator, file path, blob SHA, heading path, exact start/end lines and unchanged source text;
- bounded material diagnostics.

Failure returns a stable `validation` or `execution` kind, detailed code and safe message. There is no partial success.

The output is a Skill Result, not an Artifact Candidate or Artifact Reference.

## Normalization Rules

1. Preserve file order from the Connector result.
2. Split Markdown-oriented text only at ATX headings outside fenced code blocks.
3. Preserve every original character exactly inside the ordered unit texts, including line endings.
4. Maintain heading hierarchy as a tuple of source titles; do not interpret its business meaning.
5. Associate every unit with exact commit, blob, path and one-based inclusive line range.
6. Repository instructions, links, HTML, code and prompt-like language remain inert text.
7. Reject missing or inconsistent provenance, duplicate paths, invalid SHA, size mismatch and empty non-consumable material.

## Acceptance Criteria

1. The accepted two-file acquisition fixture normalizes into ordered immutable units.
2. Concatenating a file's unit texts reconstructs its input text exactly.
3. Unit line ranges are one-based, inclusive, contiguous and match the original text.
4. Heading hierarchy is correct for nested ATX headings.
5. Heading-like text inside backtick or tilde fenced code is not treated as a section boundary.
6. Prompt-like repository text remains unchanged and produces no side effect.
7. Invalid type, repository identity, commit/blob SHA, duplicate path, byte-size mismatch or empty file fails before returning material.
8. Failure exposes no raw exception and no partial units.
9. Equivalent repeated normalization produces an equivalent immutable result.
10. Full Artifact + Workflow + Connector regression suite remains green with no network access required by normalization tests.

## Non-goals

- GitHub acquisition, retry, cache or network.
- Source Record Candidate / Artifact Commit.
- Knowledge extraction, summarization, claims, confidence or teaching selection.
- Agent, Model Runtime, Workflow, Review, Approval, database or UI.
- Full CommonMark compliance, HTML rendering, link fetching or generic document framework.

## Stop Conditions

Stop if completion needs to modify Connector, Artifact or Workflow contracts; fetch any external content; add a parser dependency; infer teaching knowledge; add a Skill / Agent / source type; or persist an Artifact.

## Completion Definition

Code and tests complete; lossless provenance verified; architecture/security review passed; no scope drift and no Critical or Important finding remains.
