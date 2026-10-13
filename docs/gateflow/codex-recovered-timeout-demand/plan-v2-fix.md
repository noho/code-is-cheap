# Plan v2 fix report — targeted corrections, re-review pending

Gate/work unit: plan fix / `codex-recovered-timeout-demand`. Branch: `fix/codex-recovered-timeout-demand`; source/base remains `62c3b26adeb994e81043d7b1afbcd4c6eb8974ae`. Binding inputs are [goal-confirmation-v2.md](goal-confirmation-v2.md) and [plan-v2-review-decision.md](plan-v2-review-decision.md). Only [plan-v2.md](plan-v2.md) and this report were authored by this agent. No production, test or product-document changes; no raw-log/business access, model calls, delegation, deployment, commit or push.

## Accepted items and changed sections

| Decision item | Targeted plan correction / sections |
| --- | --- |
| DS-F1 | Add `README.zh.md` to source evidence, affected/allowed files, goal alignment and Documentation decision. Require bilingual semantic parity and removal of obsolete unknown-error-fatal claims across both READMEs and the generic skill. |
| DS-F2 | In Valid diagnostics versus structural failure, assistant `error` and `system/api_retry` ancillary members accept absent/null/novel JSON payloads without an SDK 0.2.138 type/enum gate. Null assistant error is unavailable/nonfatal and retained; absent error alone remains ordinary handling. Core identity/content/tool/order and intact JSON remain mandatory. State Codex's native required string-message rule separately from Claude's non-proof top-level diagnostic payload policy. Add corresponding synthetic coverage. |
| Controller C1 | In protocol evidence and Claude native completion fields, support observed `stop_sequence` alongside `end_turn`. Add clean/recovered positives and negatives paired with both reasons in the validation matrix; every other negative/malformed result-field fence remains. Remove the obsolete unobserved-positive deferral for this reason. |
| DS-OQ1 / Mimo-OQ1 | Codex identity/order now explicitly rejects work/final/unknown/telemetry frames between the unique first thread start and turn start; only supported valid diagnostics are allowed there. Pin matrix coverage. |
| DS-OQ3 | Add existing `test_agent_sandbox_runtimes.py` as read/run integration evidence and its explicit `AGENT_SANDBOX_KERNEL_TESTS=1` / `SRT_TEST_BIN` command and prerequisites. Default skips are not passes. No integration-test source mutation or unrelated suite expansion. |
| Mimo-OQ3 | Shared states, docs and matrix distinguish observed `agent_status=completed` from parser/check rejection and nonzero call exit. Invalid identity/terminal/final proof or explicit native negative completion prevents completed; partial/final diagnostic display and not_assessed remain. |
| DS-OQ2 / Mimo-OQ2 context | Restate that root identity includes the authoritative result, without a new requirement. Preserve the authoritative result's optional/nullable table; permissive assistant/retry metadata does not weaken it. DS-OQ2 remains rejected-with-reason in the controller decision. |

Artifact identity/continuation and classified-risk wording were adjusted only to reflect these corrections. Goal/success signals, non-goals, the single S-1 behavioral slice, architecture/ownership, statistics, selected checks and controller delivery responsibilities are preserved. Corrections are applied to the plan, **not independently re-reviewed or implemented**; controller-owned decision/finding status is unchanged by this agent.

## Exact versions and evidence applicability

| Artifact | SHA-256 |
| --- | --- |
| Reviewed plan, preserved at `evidence/plan-v2-reviewed-a674f5ff.md` | `a674f5ff78efd35a4d71e68d6a32b5055ee553ec4fee1bf2cb097f339d6fbefd` |
| Corrected `plan-v2.md` | `13748c8ceb3e84dfd6ee3764ad7dfb534d3221d1401f15a11a09654412c039f4` |
| Binding v2 goal, unchanged | `a68fd2c4dbc3be7e7cefb943eceff4434f40b2352b25a4083948f2c2001b49b6` |
| Controller review decision, unchanged | `69dc5626d9d01694570d327ec0066f8a9e54ee4771436affd70e4588baf7fb7f` |
| `evidence/protocol/claude-local-completion-probe.json`, unchanged | `974302740b7af6f68eaf8677e5fd48dd798bcbdf5355e3acdb2a8f7384414509` |
| Probe script snapshot, unchanged | `ff787a5256a569e7be3400f8dfeb6d94d45d61857e0c2fa257aae677a469ad74` |

The saved **actual native CLI 2.1.296** localhost probe, captured 2026-10-13 13:54:45 +08:00, records managed exit 0 and, for each positive reason, native exit 0, one request and one success result with `is_error=false`, `terminal_reason=completed`, nonempty synthetic result and null `api_error_status`. The script checksum matches the artifact. Both minimal equivalents match those terminal fields but remain synthetic inputs. API stop-reason docs corroborate custom stop completion; SDK 0.2.138 is not asserted equivalent to CLI 2.1.296. This evidence proves the supported protocol reasons, not changed-collector behavior, real transient recovery or installed delivery. Raw paths/hashes were read only as artifact metadata; raw files were not opened.

Unchanged earlier review evidence remains applicable only to unchanged assertions. Strict retry/null-error payload and unsupported stop_sequence judgments are superseded; corrected diagnostics/status/startup/native-integration/docs assertions require targeted independent re-review.

## Validation actually performed

- Compared the corrected plan with the saved reviewed snapshot. Programmatic checks passed: unchanged goal/non-goals/statistics/selected-check sections, exactly one S-1, unchanged terminal_reason/api_error_status/errors/deferred_tool_use table rows, obsolete rejected policies absent and explicit native opt-in present. Goal/decision/reviewed snapshot/protocol hashes remain unchanged.
- Verified saved probe JSON, script checksum and terminal fields against both minimal equivalents, without rerunning the probe or accessing raw logs. Confirmed Darwin and installed `srt`, `codex`, `claude`; kernel opt-in is unset. No native integration run or default skip is claimed as a pass.
- Snapshot `git diff --no-index --check` produced no whitespace diagnostics (exit 1 reflects differing files); tracked `git diff --check` and production/test/product-doc equality against HEAD passed. Plan Markdown/command syntax checks are local artifact checks, not runtime validation.
- A preservation assertion initially detected concurrent controller-owned `state.json` drift. This agent did not edit state; subsequent checks excluded controller state while verifying immutable inputs. No production drift was found. Old artifacts and reviewer reports were not rewritten.

Behavioral tests, original replay, native integration under a kernel-capable environment, independent review and installed/live probes remain required at their approved gates. No prior baseline or stored protocol observation is presented as their pass.

## Classified risks and uncovered scope

| Risk / uncovered scope | Classification, owner / destination |
| --- | --- |
| Current false rejection, native negative masking and stale docs; changed behavior and native integration not yet exercised | **fixed in current slice** (planned S-1, not yet implemented/validated); implementation agent/controller, approved implementation and code review. Kernel initialization failure, if encountered, must be recorded and resolved rather than counted as a skip/pass. |
| Codex lacks independent refusal/finish metadata; future Claude final schema and historical identity visibility | **assigned to later work unit**, maintainer/caller; evidence-backed protocol work if needed. Existing explicit final/identity fences remain. |
| Business correctness and artifact content beyond selected checks | **assigned to later work unit**, caller's existing verification workflow; no business evidence accessed or acceptance added. |
| Real transient-fault reproduction | **assigned to later work unit if requested**, user/controller; local/native and later ordinary live probes do not inject faults. |

No new blocking question, material user tradeoff or plan-fix blocker. Documentation decision here is plan/report only; product-document edits belong to approved S-1. **Next entry point: controller dispatches independent dual targeted plan re-review of this corrected plan against the v2 goal and accepted decision; implementation remains gated on re-review and accepted-plan commit.**
