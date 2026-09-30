setup_status: ok
agent_status: completed
tool_evidence: yes
canary_status: match
warnings:
  - MiMo: recovered function argument parsing failures, instruction scan/process-query failures, and timestamp command failure.
  - MiMo: a temporary sync did not stub launchctl; its output has neither restart success nor unloaded-service notice. This smoke is excluded from deployment evidence. Controller smoke explicitly stubbed launchctl.
  - Kimi: expected negative probe exit, recovered report patch formatting and timestamp/path validation errors.
retry_class: none

# Catalog template review adjudication

## Scope and authority

- Branch: codex/gpt-6-1-sol-defaults; base: main.
- User requested robust template selection across recent Codex versions, with GPT-6.0 as donor if compatible.
- User retains merge ownership. No live configuration synchronization was performed.
- Both external agents used independent complete task prompts, unique preflights, temporary outputs and no-persist runs. No nested agent dispatch was authorized.
- Reviewed source diff SHA256: d9ba5d86658c606ff0a395a0a84d235d5dd9252f36df95f0e1c34c9b491aab38; independently checked unchanged after both reviews.
- Reviews: docs/reviews/code-review-20260930-183334.md (MiMo); docs/reviews/code-review-20260930-182836.md (Kimi).

## Dispatch acceptance

- Both runner exits: 0; each has one turn.completed, no outer error/turn.failed, successful canary read event and exact final CANARY match. No final contains literal fabricated tool-call markup.
- MiMo: 131 events, 55 successful command events. Final report completed with two findings.
- Kimi: 110 events, 34 successful command events. Final report completed without material findings.
- Individual command/tool errors were assessed for purpose, recovery and result impact. Expected negative probes and recovered report-production errors do not invalidate complete review evidence.
- MiMo emitted interim literal tool-call syntax during a failed interruption attempt, then resumed real tool execution and completed the review; this was not an unexecuted final masquerading as a completed task.
- Method deviations: MiMo used a forbidden process-list probe (failed), scanned runtime paths outside the requested scope, and ran temporary sync without a launchctl stub. Its full-sync smoke is not accepted as deployment evidence. No restart success marker appears. Controller verification used an explicit launchctl stub, existing HOME, and only temporary shared/agent roots. These deviations are retained here even though the reviewer understated them.
- Kimi artifact's Validation section predates its recovered report-writing errors; final message and stderr record those additional errors. Review findings are accepted based on the full event stream, not that abbreviated section alone.
- Raw event streams remain private runner artifacts and are not committed; review artifacts and this adjudication preserve outcomes without publishing environment traces.

## Findings adjudication

### MiMo 1: direct metadata with code-mode prompt

**Decision: rejected-with-reason as a current defect; retain future upstream drift as residual risk.**

The counterexample changes an official catalog entry to claim direct tools while its instructions claim functions.exec. No such inconsistency was found in installed Codex 0.159.2 or cached 0.157.0, 0.157.1 and 0.158.0 catalogs. All select gpt-5.5, whose direct instructions do not require functions.exec. Current code-mode entries are excluded by authoritative tool capability metadata. Keyword matching cannot establish arbitrary prompt semantics and can reject harmless references; generator-owned instructions would replace the user's requested Codex-derived instructions. This change does not claim compatibility with arbitrary future contradictory catalogs.

### MiMo 2: unknown donor fields and GPT identity inheritance

**Decision: rejected-with-reason as a new actionable defect; retain schema evolution as residual risk.**

Deep-copy plus explicit third-party overrides is the existing generator design. The newly added test verifies schema preservation and copy isolation; it does not establish that any hypothetical unknown behavioral field is safe. Current donor fields were inspected and the generated catalogs were parsed by four real Codex binaries. Retaining current Codex schema and base instructions is intentional; current gpt-5.5's GPT-5 persona wording was also present in the old GPT-5 donor family, so it is not introduced by dynamic selection. An invented unknown field does not identify a current incorrect runtime path. A complete static allowlist would require updates for newly required schema fields and undermine the user's version-resilience goal. Known incompatible behavior is excluded/overridden; protocol/schema changes still require fresh investigation.

### Kimi

No material findings. Accept evidence of current-catalog selection, guardian exclusion, preserved built-in metadata, staged failure preservation and documentation alignment. Its future-drift notes are retained below.

## Controller validation

- Focused tests: test_model_catalog_generation.py (6 tests) and test_codex_model_defaults.py (5 tests), all pass. Includes real current bundled catalog, donor removal/renaming fixtures, incompatible candidates, guardian exclusion, deep-copy isolation and preservation on failed generation.
- Full temporary sync using Codex 0.159.2 succeeds: nine third-party catalogs, three GPT cards and business gpt-6.1-sol/high; unrelated business project trust retained. launchctl is replaced with a temporary stub, so real services cannot restart.
- Current Codex 0.159.2 parses generated Kimi catalog: direct tools, context_window/max_context_window 1,048,576. No provider request was issued.
- Actual cached binaries at ~/.codex/packages/app-server-daemon/releases/<version>-aarch64-apple-darwin/codex: 0.157.0, 0.157.1, 0.158.0. For each, debug models ran under fresh CODEX_HOME, generator used that binary's catalog, and that same binary parsed all nine generated profile catalogs with correct direct mode and card window. All pass; all dynamically select gpt-5.5.
- Donor-name unit fixtures are synthetic; older-version coverage above uses real binaries, not those fixtures.

## Residual risk

- No live gateway round trip was performed. CLI catalog generation/loading and tooling metadata are verified.
- A future catalog with no compatible direct session model is deliberately rejected and installed cards/catalogs are preserved.
- Future tool/schema semantic changes can still require adaptation; compatible model removal or renaming no longer requires a fixed donor ID edit.
- Selection follows catalog order, not parsed model version names. Reordering chooses another compatible donor rather than promising newest-first semantics.
