# Knowledge Video Editorial MVP v1.3 — Historical Creator-authored Script Input Rebaseline

## 1. Status and authority

| Field | Value |
| --- | --- |
| Status | **HISTORICAL APPROVED FOUNDATION — S0 AND S1 COMPLETE; SUPERSEDED AS ACTIVE GOAL BY KNOWLEDGE VIDEO BUSINESS LOOP MBL v1.0** |
| Direction | Creator-authored Script Package amended Goal/defaults approved by Product Owner, 2026-08-24 |
| Exact amended Goal | Approved by Product Owner, 2026-08-24 |
| Governance Issue | #148 CLOSED; PR #149 MERGED |
| Intake implementation | Issue #150 CLOSED; PR #151 MERGED |
| Accepted foundation baseline | main@1a7692894bce6ebea3d88263da67713b426ba59e |
| Current authority | [Knowledge Video Business Loop MBL v1.0](KNOWLEDGE-VIDEO-BUSINESS-LOOP-MBL-v1.0.md) |

E0 completed through Issue #143 / PR #144, S0 through Issue #148 / PR #149, and the S1 intake implementation through Issue #150 / PR #151 with final regression `476/476`. This contract preserves the Product Owner-approved amended Goal and eight defaults as the accepted Script-input foundation. The active outcome is now the MBL v1.0 Goal, which reuses this intake contract and separately governs narration, visual production, manual Douyin publication and feedback. The old in-application Script-authoring/revision path remains retired from the primary flow.

## 2. Problem and current-contract audit

The application already owns useful exact seams:

- live supported GitHub Source acquisition with repository identity, exact commit/blob, normalized units and locators;
- immutable Script Artifact Versions, exact prior references and Script approve/reject Decision records;
- durable Task state, repository restart/replay and exactly three local SSR/Jinja views;
- downstream Whole Narration/Alignment planning that can consume one exact approved Script.

At the time of this rebaseline, the previous primary Script behavior conflicted with the approved direction:

- private deterministic `_OfflineRuntime` creates the initial Script during Source processing;
- natural-language `revision_context` is treated as if it were a general writing/revision engine;
- #145/#146/#147 showed that adding fixed selectors and special wording produces fragile fixture-shaped behavior rather than honest authoring intelligence;
- structure/source-locator checks and human semantic review are not clearly separated.

The protected H4 candidate and the dirty/rejected #145/#146/#147 candidates remain preserved evidence. This contract neither copies nor merges them.

## 3. Approved product contract

### Creator-authored Script Package

A creator prepares one structured Script Package outside the application using ChatGPT, Codex or an independent content workflow. Schema v1 has exactly eight top-level fields: `schema`, `version`, `script_package_id`, `source`, `claims`, `narration_units`, `creator_provenance`, `revision_note`.

The complete schema-shaped template is below. Angle-bracket placeholders must be replaced with exact current Source values before intake, so this template is not directly submittable:

```json
{
  "schema": "ai-course-factory.creator-script-package",
  "version": 1,
  "script_package_id": "ai-intro-creator-script",
  "source": {
    "repository_url": "https://github.com/microsoft/AI-For-Beginners",
    "repository_identity": "microsoft/AI-For-Beginners",
    "commit_sha": "<exact current Source commit SHA>",
    "files": [
      {
        "path": "lessons/1-Intro/README.md",
        "blob_sha": "<exact current Source blob SHA>"
      }
    ]
  },
  "claims": [
    {
      "claim_id": "claim-001",
      "statement": "An ordinary program follows an explicit algorithm.",
      "evidence_locators": [
        "<exact locator that is a member of the current Source Record>"
      ]
    }
  ],
  "narration_units": [
    {
      "unit_id": "unit-001",
      "text": "<approved-language narration>",
      "claim_ids": ["claim-001"]
    }
  ],
  "creator_provenance": {
    "creator_declared_name": "<creator-declared display name>",
    "creator_role": "course creator",
    "tool_name": "Codex",
    "tool_version": "<optional declared version>",
    "session": "<optional declared session>",
    "project": "<optional declared project>"
  },
  "revision_note": null
}
```

`claims` is the only evidence owner. Every claim has exact `{claim_id, statement, evidence_locators}`, a unique `claim_id` and at least one locator. Every narration unit has exact `{unit_id, text, claim_ids}`, a unique stable `unit_id` and at least one `claim_id`. Every referenced claim resolves inside the same package. A unit inherits locator binding only through its ordered `claim_ids`; `evidence_locators` on a narration unit is forbidden duplicate truth.

`creator_provenance` is creator-declared provenance, not authentication. The application may display these values only as declared facts. `creator_declared_name`, `creator_role` and `tool_name` are required; `tool_version`, `session` and `project` may be omitted. `revision_note` is always present and is either `null` or one bounded nonempty string. Raw prompts, runtime secrets, credentials, implicit latest and machine-specific input paths are forbidden.

### Intake and validation

The approved MVP boundary is one operator-configured directory containing fixed `creator-script.json`, plus an explicit same-origin Start-page POST. The POST carries no path and no multipart bytes. The application never scans Desktop, Downloads or `latest`.

Before any Workspace, Artifact or state write, intake validates the complete file:

1. regular non-symlink fixed file, bounded size, UTF-8 JSON, no duplicate object keys, exact supported schema/version and closed field sets;
2. current Source Record `source_kind` is `github`, and package `source.repository_url`, `source.repository_identity` and `source.commit_sha` respectively equal the current record fields;
3. package `source.files` equals the ordered-unique `{path, blob_sha}` projection derived from current `SourceRecord.units` in first-occurrence order. Repeated identical pairs collapse; the same `path` paired with different `blob_sha` values fails closed;
4. ordered unique claims and narration units with bounded nonempty statements/text;
5. every narration unit resolves at least one in-package claim and every claim owns at least one locator;
6. every claim locator is byte-for-byte equal to a locator present in current `SourceRecord.units`, with no locator duplicated onto narration units;
7. no forbidden prompt/secret/runtime/path fields.

`source.files` is a package-owned exact projection derived from the existing Source Record; it is not a claim that `files` exists in the Source Record payload or that the package `source` object equals that full payload. Intake does not change the generic Source Record shape/schema.

These checks prove structure, identity, locator membership and reference completeness. They do not prove that narration is true, that a locator semantically supports a claim, or that the teaching is good. The creator reads the committed Script Version and a human Script Decision owns those judgments.

### Canonical value, package identity, failure and replay

- The first accepted package locks the Task/current Source lineage to its safe creator-declared `script_package_id`.
- Canonical logical equivalence is JSON-value equivalence after parsing: insignificant JSON whitespace and object-key order do not participate; array order does participate. Every accepted field and nested value under all eight top-level fields participates. String values are not silently normalized.
- Every accepted Script Version persistently owns the complete validated canonical value as exact `script_package` payload/provenance. Public Script narration, claims, Source projection and creator provenance are read from that binding; intake cannot discard fields and reconstruct them later.
- The same `script_package_id` plus the same canonical value returns the existing exact Script reference, preserves its exact Decision and creates zero new Version/state mutation.
- The same `script_package_id` plus any changed accepted logical field commits and selects the next Script Version with exact `prior_reference` lineage. Any Decision for the prior Version remains historical only; the new Version begins unapproved, requires a new approve/reject Decision and keeps E1 closed.
- After the lineage is locked, a different `script_package_id` is a conflict and cannot create a parallel Script lineage.
- Re-import never overwrites an old Version or Decision. Only invalid, foreign-Source/locator or different-ID conflict preserves the current selected Script and Decision unchanged.
- v1.3 primary Script actions are only approve/reject. Reject requires nonempty bounded context, preserves the exact current Script Version and never invokes `_OfflineRuntime`; the Creator revises externally and explicitly re-imports the same package ID to create the next Version. Historical revise Decisions remain readable but cannot invoke `_OfflineRuntime` or qualify a v1.3 current Script. Intake itself is not a Decision, and the legacy Decision type is not deleted.
- Restart/GET/inspect uses durable Artifact/state only and does not require the configured directory; only a new intake/re-import does.
- E1 consumes only the exact approved Script and never authors or revises it.

### Contract examples

The JSON above is a complete schema-shaped template, not a valid intake instance while angle-bracket placeholders remain. After replacing those placeholders with exact current Source commit/blob/locator values, it represents the minimum cardinality: one projected Source file, one evidence-owning claim and one narration unit that references it.

Three invalid mutations define the failure edge:

1. **Unknown claim:** change the unit to `"claim_ids": ["claim-missing"]` without adding that top-level claim. Result: structural/reference failure; zero Script/state write.
2. **Foreign source or locator:** change `source.commit_sha`, a `{path, blob_sha}` pair, or a claim locator so it is not equal to/member of the current Task Source Record. Result: source conflict; zero Script/state write.
3. **Different package ID after first acceptance:** re-import the otherwise valid canonical value with `"script_package_id": "parallel-script"`. Result: lineage conflict; preserve the current Script/Decision and create no parallel Version.

## 4. Alternatives

### Option A — configured directory + fixed `creator-script.json` (approved)

Matches the existing local explicit-input pattern, keeps paths out of HTTP, permits atomic complete-package preflight and avoids adding a file manager or authoring UI.

### Option B — bounded structured Start form/textarea

Possible but not recommended for the first slice. It increases parsing, escaping, partial-edit and long-form UX risk and blurs review control with content authoring. It may be reconsidered only through a later product/UI decision.

### Option C — application-controlled LLM authoring

Deferred and not authorized. It would require a separate Provider/model/credential/fee/cap decision, honest Attempt/Budget behavior and a much larger reliability/product contract. No generic Provider registry is implied.

## 5. Three-view responsibility

1. **内容与音频** — Source identity/locators, configured package readiness, explicit intake/re-import, validation findings, immutable Script review/Decision, then Whole Narration/Alignment/SRT.
2. **视觉编排与制作** — approved Visual Edit Plan, asset readiness and Sample gate after E1.
3. **终审与交付** — unchanged Sample/Final playback, named-human findings and Publish Package.

No fourth view, SPA, generic file manager, browser path field, upload manager or application writing editor is introduced.

## 6. Historical approved amended exact Goal

> Deliver one local Knowledge Video Editorial flow that acquires the supported exact public GitHub source; accepts a Creator-authored Script Package whose ordered narration units bind exact source locators and claim evidence; commits and human-approves one immutable Script Version; produces one continuous narration, phrase-level millisecond Acoustic Alignment, a human-approved Visual Edit Plan, deterministic A-roll/B-roll production, an approved 15–20 second Sample Video, a fully rendered Final Video, and a named-human-approved traceable Publish Package through exactly three lightweight server-rendered views.

This wording was the Product Owner-approved exact v1.3 Goal and remains historical authority for the accepted Script-input foundation. It is superseded as the active completion target by the exact MBL v1.0 Goal.

## 7. Approved milestone sequence

- **S0 — Script-input truth rebaseline:** authoritative docs/Goal amendment only.
- **S1 — Creator Script Package intake:** explicit directory/file preflight, exact Source membership, immutable Version/re-import, human Decision, SSR evidence and restart/idempotency.
- **E1 — Narrative clock:** consume exact approved Script; Whole Narration, continuous phrase Alignment and canonical SRT. E1 does not author Script.
- **E2–E4:** retain Visual Edit Plan/static assets, deterministic Sample gate, full render, named-human Final Review and Publish Package.

Historical completion truth: S0 and S1 are complete. The former E1-E4 sequence is not active implementation authority; the MBL contract reclassifies the remaining work as B2-B6 around the frozen three-video Douyin loop.

## 8. Approved defaults and Product Owner decisions

Approved defaults:

1. configured directory plus fixed `creator-script.json`;
2. JSON schema version 1;
3. explicit Start-page intake/re-import POST with no path/upload field;
4. creator-declared provenance required; `revision_note` field required but its bounded note content optional through `null`;
5. exact Source identity and locator membership validated automatically;
6. semantic support and teaching quality decided only by a human Script Decision;
7. canonical logical equivalence and the locked `script_package_id` lifecycle described above;
8. v1.3 exposes approve/reject only; legacy revise remains readable and cannot invoke authoring.

The Product Owner approved the exact v1.3 Goal and all eight defaults on 2026-08-24. Issue #148 / PR #149 merged the ten-doc authority set, and Issue #150 / PR #151 completed the S1 intake implementation. These defaults remain binding for the MBL Script-input foundation. Any request for browser authoring, application-controlled LLM, automatic semantic verification or a different intake boundary remains a separate decision; narration Provider/model/credential/fee/cap authority now follows the exact MBL contract.

## 9. Historical boundary and current stop conditions

The S0 and S1 gates described above are complete. Do not reopen or weaken their exact Source, package identity, canonical-value, immutable Version, Decision or replay invariants.

Current work must stop unless authorized by the MBL v1.0 milestone contract. In particular, this historical document does not authorize B1-B6 code, Provider execution, semantic fact-checking, a fourth view, SPA/file manager, credentials/fees beyond the explicitly approved MBL cap, deployment, automated publication or reuse of protected dirty candidates.
