# Controller review closeout — agent-sandbox E2BIG

Implementation review identities: base f818dde2d361dea5313aefb7d7383399f947e0c9;
initial implementation 690ec69116f95b79bcb1d1d60c9044ac36eff6d1;
second snapshot 6672741e6a58939aba3a65c57c03843d2c92aa10;
final implementation ac5b244637e926b8658f5b336e4247b106fd96b8.

## DS Flash R1

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: [exploratory_rg_no_match, recovered_fixture_parse_errors, recovered_fixture_argv_error]
evidence_gaps: []
retry_class: none
```

codex/ds-flash, e2big-ds-flash-20261009-r1. Managed session 17020 exited 0,
valid JSONL with turn.completed, empty stderr, final/report token and original
cat output matched expected. 110 command completion records. item_51 rg had no
match; direct full source was read. item_81/84/85/86 had JSON extraction offsets
wrong in an ad-hoc fixture, recovered by corrected fixture; item_90 passed a
missing argv value to a fixture, then real installed package validation was
checked correctly. None was a product test failure or unrecovered necessary
source read. An exploratory printenv returned no credential-like variable names;
no environment values are copied into this artifact.

Finding 1 (low) accepted: --check falsely accepted standalone srt0.0.79.
Fixed with shared validateRuntime/--validate package/module check plus fixtures.
No permission or compaction change in this follow-up commit.

## MiMo Codex R1 — rejected, user-authorized stop

```yaml
setup_status: ok
agent_status: blocked
tool_evidence: yes
tool_trace: partial
required_evidence: partial
canary_status: unknown
result_status: rejected
warnings: []
evidence_gaps: [corrupt_structured_output, missing_final_review_artifact, no_turn_completed_before_user_stop]
retry_class: provider
```

codex/mimo, e2big-mimo-20261009-r1. Managed session 52531 exited 130 after
explicit user authorization to stop and use MiMo Claude for the single same
provider corrective retry. The event file remains rejected: 18 malformed
physical JSONL lines at 173-181, 184-189, 191-193, involving escaped quoting and
raw line splitting in tool completion output. SHA256:
57aa61c3811424f473e7ccf7c348433d0b7e21c50a4b4b76f44c96660a0c6121.
The specific emitter/transport defect was not investigated in this E2BIG PR;
this is an output integrity failure, not a mechanical refusal of a nonzero
exploratory command. Initial canary file read existed, but no final report token
was delivered, so final canary acceptance is unknown. No conclusion from this
attempt is used as independent review evidence.

## DS Flash R2 — finding closure

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: []
evidence_gaps: []
retry_class: none
```

codex/ds-flash, e2big-ds-flash-20261009-r2. Managed session 41917 exited 0;
valid JSONL with turn.completed, all command completion exits 0, empty stderr,
report token matched. Independent real-install and rejected-standalone preflight
fixtures, non-spawn/non-import markers, version/name/bin/missing-module matrix
and focused tests prove Finding 1 resolved. No new findings. The ordinary-only
CI gate note, unchanged srt --version execution, duplicated explicit pin and
module-integrity limits are residual risks, not unresolved defects.

## MiMo Claude R2 — user-authorized stop, no result

```yaml
setup_status: ok
agent_status: blocked
tool_evidence: no
tool_trace: unavailable
required_evidence: missing
canary_status: unknown
result_status: rejected
warnings: [claude_unrecognized_model]
evidence_gaps: [no_structured_output, missing_final_review_artifact]
retry_class: user_authorized_restart
```

claude/mimo, e2big-mimo-claude-20261009-r2. Managed session 85470 exited 130
following the user's explicit “杀掉重来” instruction. The default JSON output
remained empty and no report existed at stop. The only stderr diagnostic was
`[claude-code:unrecognized_model]` for mimo-v2.6-pro[1m], a recognized nonfatal
metadata warning. No provider failure or completed review is inferred from
elapsed time or the empty in-flight output. No conclusions from this attempt
are accepted. The user explicitly authorized an additional same-provider
restart, which uses stream-json for observable tool evidence.

## MiMo Claude R3 — accepted, two findings adjudicated

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: [claude_unrecognized_model, recovered_scratch_write_restriction, recovered_probe_harness_errors]
evidence_gaps: []
retry_class: none
```

claude/mimo/mimo-v2.6-pro[1m], e2big-mimo-claude-20261009-r3.
Managed session 52603 exited 0; 21278 valid stream-json records, result subtype
success/is_error=false, 44 turns. All 43 tool calls have matching tool results.
The actual read and report token matched (final summary did not repeat the token;
the report satisfies this run's report protocol). The event init model matches
self-report. SHA256 of the stream:
58c17071c4114257634e531818024236b5384f94e1a1935ad992eefde2e1cf2f.

Two failed Bash calls were recovered: first, profile creation in bare /private/tmp
was refused by Claude's inner sandbox; scratch moved to /private/tmp/claude.
Second, the reviewer's harness omitted the deny action prefix and supplied empty
original coverage lists. Minimal debugging and corrected harness produced
ALL PROBES PASSED. The repository's ordinary launch (6, skip 1) and sandbox
(17, skip 6) suites also returned OK in actual tool output. These failures do
not invalidate the recovered findings or source review. The full source review
did not show an AGENTS.md file read; controller checked the actual repository
instructions, and the focused follow-up explicitly requires that tool read.

Finding 1 (low), validator ordering: accepted and fixed. Structural validation
now precedes version execution. The standalone marker scenario is in ordinary
SetupTests and proves the unsupported candidate never executes.

Finding 2 (low), hard-link policy-evidence mutation: initially uncertain in
review, independently CONFIRMED by controller's synthetic native envelope.
Both source/effective files were linked, chmodded and written through aliases.
This affects retained evidence, not the loaded kernel policy. Accepted with the
reviewer's minimal provenance remedy: SHA-256 of exact bytes before spawn goes
to envelope stderr; caller collects via a trusted parent pipe and checks retained
files before auditing. README/skill explicitly disclaim inode immutability and
trust in Agent-writable logs. The native regression proves alias mutation/hash
mismatch while the loaded deny remains enforced. Local synthetic probe evidence:
/private/tmp/e2big-hardlink-probe-result.json (no business input).

## DS Flash Codex R3 — final focused closure accepted

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: [self_reported_model_unverified, recovered_output_truncation]
evidence_gaps: []
retry_class: none
```

codex/ds-flash, e2big-ds-flash-20261009-r3. Managed session 59109 exited 0,
107 valid JSONL records with turn.completed; 94 completed commands, all exit 0,
no errors and empty stderr. Report and actual canary read matched. SHA256:
803ce8834912d05afd3bea3a7023d41b7588506fd159bec44d705736fd7f2d5a.
Frozen ac5b244, base 6672741 verified before/after. All 8 changed files recovered
from truncated diff output through smaller reads. Independent ordinary marker,
validator and large-profile/hash tests passed. Both findings closed within the
precise provenance/structural-validation claims; no new findings.

The report's self-declared model `gpt-5` is NOT accepted as model identity.
The actual controller command selected --provider ds-flash; the deployed card
records model deepseek-flash / model_provider deepseek. This Codex stream has no
model-identity event, so no independently observed upstream model is claimed.
This self-report error does not replace the real routing/tool evidence or negate
the demonstrated source tests. The report is preserved verbatim; the controller
corrects its model claim here.

Remaining provenance limits are explicit: the trusted parent must retain the
pre-spawn adapter record, not accept a later child echo as a replacement. Hashes
only compare final bytes; transient mutation/restoration is not disproved. No
supply-chain authenticity or filesystem evidence immutability is claimed.

## MiMo Claude R4 — focused closure accepted; final doc/parser finding fixed

```yaml
setup_status: ok
agent_status: completed
tool_evidence: yes
tool_trace: complete
required_evidence: complete
canary_status: match
result_status: accepted
warnings: [claude_unrecognized_model, summary_test_count_corrected]
evidence_gaps: []
retry_class: none
```

claude/mimo/mimo-v2.6-pro[1m] (observed init model), e2big-mimo-claude-20261009-r4.
Managed session 77054 exited 0; 9738 valid stream-json records, result subtype
success/is_error=false, 24 turns, all 23 tools paired with successful results.
Report and actual canary read matched. SHA256:
199eda74b591db546fba3391f642df9618c66fec4f0be195f8d7b3e352d2482b.
AGENTS.md was actually read, closing the prior full-review coverage omission.
Frozen ac5b244/base 6672741 remained unchanged through review. Its independent
hash-of-exact-written-bytes compaction scratch passed. Actual ordinary tool
output was 6 tests (skip 1) plus 18 (skip 6), i.e. 24 total/17 executed passes;
the final summary's “23” was a count error, not a failed test. The detailed
report gives the correct individual suite counts.

Both prior findings closed. New low finding accepted: descendants share stderr
and can emit later forged hash records, so last-wins parsing is unsafe. The
controller applied the recommended first-occurrence contract in both READMEs
and SKILL: retain the first adapter seatbelt_profile record before runner start,
never overwrite it with later duplicates. Tests now parse only that record.
The native hard-link regression now has its synthetic runner append forged
matching digests after mutating both files; the genuine first record still
mismatches and detects the altered evidence. An ordinary duplicate-record test
also passes. No production code changed in this last closure. The test fixture
pins AGENT_TOOLS_FILE to source to resolve the noted clean-machine dependency.
No additional independent review is claimed for this docs/tests-only closure;
the controller verified the exact prescribed remedy and adversarial regression.

## Final controller verdict

- All accepted findings are fixed; no outstanding merge-blocking finding.
- Production implementation identity ac5b244 was examined by both final focused
  reviewers, in addition to the earlier full E2BIG reviews and fix closure.
- Final docs/tests closure explicitly narrows evidence claims and parsing; it
  changes no production code, filesystem permissions, provider routing or
  lifecycle behavior.
- Final ordinary suite: 94 tests, OK, 9 explicit opt-in skips, 33.354 seconds.
- Final native Seatbelt plus Codex/Claude local-mock suite: 27 tests, all passed,
  12.423 seconds. Synthetic-only credentials/input; no business Agent launched.
- Current reported full policy retained all 4108 denies with 4108 kernel denials
  and 4108 actual read-only open denials; historical missing paths are qualified
  in the validation artifact and not claimed as verified actual reads.
- Remaining limits: macOS/srt0.0.79 only; extreme insufficiently groupable
  policies can hit native compiler limits and fail closed. Hashes are provenance,
  not immutable files or proof against transient mutation/restoration; trusted
  parent capture of the first record is required. Package checks are structural,
  not content-integrity authentication.
- No live deployment, business workflow operation, finance input read, business
  output modification or deny-list reduction was performed.



