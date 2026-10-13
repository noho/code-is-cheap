# Aggregate fix: DS-A1

Gate/work unit: aggregate deepreview fix / `codex-recovered-timeout-demand`. Branch: `fix/codex-recovered-timeout-demand`; unchanged HEAD: `edd3d7bc937752d4ecab1e63cc6ba8599f17dac3`. This is the controller-authorized DS-A1 fix, governed by [goal-confirmation-v2.md](goal-confirmation-v2.md), [plan-v2.md](plan-v2.md), [aggregate-review-decision.md](aggregate-review-decision.md) and [DS aggregate review](../../reviews/code-review-20261013-164206.md). Their input hashes and the initial workspace status are saved in the new evidence directory's `before.json`.

**Finding status: DS-A1 已修复.** The display change and regression checks pass on the final source hashes below. Independent targeted re-review and aggregate gate adjudication remain controller-owned; this report does not declare aggregate pass or change the controller's finding/state records. No additional finding was implemented.

## Exact change and source identity

Only two production/test files changed:

- `scripts/agent-run-result.py:345`: replace the root/string-only display assignment guard with `if self.final_valid`. The immediately preceding, unchanged `final_valid` assignment means a root string with nonempty trimmed content. Empty/whitespace/missing/nonstring authoritative results preserve `self.final` and `self.final_line`, while `final_valid=False`, `terminal_valid=False`, failed/rejected/nonzero remain decisive. Earlier assistant text supplies display only.
- `tests/test_agent_run_results.py`: extend three existing adjacent methods, without a new test framework: `test_claude_result_owns_final_without_assistant_fallback`, `test_claude_native_negative_and_malformed_completion_overrides_success`, and `test_recovered_diagnostics_keep_selected_checks_for_both_runtimes`. The diff is 45 insertions / 8 deletions across the two files, including the single production guard replacement.

| Source | Before SHA-256 | Final SHA-256 |
| --- | --- | --- |
| `scripts/agent-run-result.py` | `9b44ac33099f49e8d4904e561e63f4e5dee43a6e177548cbb2edb5226f35ce5b` | `aa9b1a3eef7f048e6d8e8a06e06510da9178fcba9097270d422cf2eafc2dd7ff` |
| `tests/test_agent_run_results.py` | `6a237ba6338c9f3c04c5825606e3d75e03d2d053f6c6246665b1486d2beec8c4` | `6cda405c565c9ebc200885bd61c1d8fe7e480b3562330afacd63e9ac38be891b` |

Durable evidence: [aggregate-fix-ds-a1-20261013T084811Z-821b78d0](evidence/aggregate-fix-ds-a1-20261013T084811Z-821b78d0/). It contains byte-exact `before-`/`after-` source snapshots, `before.json`/`after.json`, `source-diff.patch`, validation scripts, exact argv/cwd/timestamps/exits/source hashes, and complete stdout/stderr logs. All six primary validation commands recorded unchanged before/after source hashes matching this table. `final-checks.json` records the delivery hash/snapshot checks and final whitespace/syntax checks; `evidence-sha256.json` inventories the new evidence.

The only documentation written by this fix is this report and the new evidence directory. No goal/plan/state, earlier artifacts/evidence, runner source, README or skill was edited. Existing controller changes were retained. No original business files or other-agent logs were read; no native runtime/model request, delegation, commit, push, PR or deployment was performed.

## Newly run validation

The exact commands and exits, including the full targeted `-k` selection and Python syntax program, are in [validation.json](evidence/aggregate-fix-ds-a1-20261013T084811Z-821b78d0/validation.json). Each label has separate `.stdout` and `.stderr` files. Orchestrator command:

```bash
python3 -B docs/gateflow/codex-recovered-timeout-demand/evidence/aggregate-fix-ds-a1-20261013T084811Z-821b78d0/validate_fix.py
```

| Check / log label | Actual result |
| --- | --- |
| `affected-tests` | exit 0; 7 selected methods passed, 6.709s, no skip |
| `synthetic` / `probe_display.py` | exit 0; 14 cases / 168 assertions passed; every input, collector argv, report, internal final/terminal validity and final source line saved |
| `full-affected-suite` | exit 0; mandatory final full affected suite: **56 passed**, 28.548s, no skip |
| `python-syntax` | exit 0; compile both changed Python files without writing bytecode |
| `runner-syntax` | exit 0; approved plan-form `zsh -n scripts/codex-agent-run scripts/claude-agent-run`; final checks additionally parse each runner separately |
| `diff-check` | exit 0; `git diff --check` |

Mandatory full-suite command, executed after all production/test edits:

```bash
python3 -B -m unittest discover -s tests -p test_agent_run_results.py -v
```

Python: 3.11.15. No validation attempt failed; the expected rejected synthetic calls have actual collector exit 1 and are preserved in their individual records, rather than counted as successful calls. Primary harness exit was 0. No production/test edits followed this full-suite run; final checks verify equality with its hashes and saved snapshots.

## Coverage and interaction reasoning

| Behavior / interaction | Current-source coverage and interpretation |
| --- | --- |
| `''` and `'  '` after readable root partial | Direct regression asserts preserved text/chars, terminal failed, failed/rejected and outer/runner 1. Selected-canary regression asserts the proof's original output line 2 / proof line 2. Synthetic checks independently assert `self.final_line=2`, `final_valid=False`, `terminal_valid=False`. |
| Missing/null/number/list result | Existing direct matrix now asserts preserved partial/chars and rejection; synthetic evidence confirms source line and invalid proof flags. A missing terminal remains rejected with partial text retained. |
| No prior root text; readable nested text | Direct matrix covers both no-text and valid parent/nested/tool-result streams for empty/whitespace/nonstring results. Display remains empty with chars 0 and rejection. Synthetic empty/whitespace cases confirm `final_line=None`; nested text cannot supply root display or completion proof. |
| Native negative metadata with readable authoritative result | Existing exhaustive negative/malformed completion matrix now includes earlier root partial and asserts authoritative nonempty text/chars remain displayed. Refusal/max_tokens/content_filter synthetic controls confirm terminal invalid/rejection while readable result owns display and `final_valid=True`. This preserves the separation of readable-final shape from native terminal validity. |
| Selected canary/artifact checks | Empty/whitespace results with a wrong partial canary still report mismatch at the retained source line; matching partial canary still cannot rescue invalid final. Missing selected artifacts remain hard errors in both cases. Existing valid-final selected-check matrix verifies independent completed+rejected behavior for canary/artifact/last-message failures in both runtimes. |
| Duplicate terminal, root/nested ownership and Codex behavior | The duplicate-result early return, parent/root validation, assistant display scope and Codex adapter are unchanged. Targeted methods cover first-final retention, trailing fences, nested tool scoping and latest-message Codex rejection; the full suite checks broader identity/exit/parse/statistics/detail behavior. |
| Public report and exit contract | Existing report-contract assertions keep the schema/key set and `result_status=not_assessed`. The proof/check/exit logic is unchanged. Retained partial proof scanning may improve rejection attribution or show canary match, but cannot alter invalid final/terminal acceptance. |

This is display fidelity under the approved Claude ownership/partial-retention rule, with no success fallback, metadata policy change or new architecture. Native negative nonempty result text still replaces partial display because `final_valid` checks readable root text independently of `terminal_valid`.

## Evidence applicability and controller handoff

- **Pre-fix evidence:** DS aggregate review and its reported prior 56-test/native/replay results refer to collector `9b44ac33…` and tests `6a237ba6…`. They remain historical evidence for unaffected paths and motivation; they do not establish current-source DS-A1 display behavior or a current-version native/replay pass. The existing DS probe expected blank display and is not a post-fix acceptance oracle.
- **New evidence:** this fix's targeted checks, 14 synthetic cases, final 56-test suite and syntax/diff checks apply to `aa9b1a3e…` / `6cda405c…`. Raw synthetic records use only new generated protocol data. The full suite's sync-install test targets temporary fixtures; it establishes no live installation or deployment.
- **Remaining required work in this same work unit:** controller runs the current-source outer native suite and current-version original replays, assesses unchanged-path evidence applicability, and obtains independent dual-route targeted re-review. The child nested native sandbox was previously blocked; per this handoff it was not rerun and no skip/block is represented as a pass. No original input or preexisting evidence was modified by this delegate.
- **Installed/live:** no installed equality, installed replay, live probe or sync pass is claimed here. Controller owns those approved later gates and delivery actions.

## Classified residual risks / owners / destinations

| Risk / uncovered area | Classification | Owner / destination |
| --- | --- | --- |
| DS-A1 blank authoritative text erasing readable partial display; partial line/chars losing fidelity | **fixed in current slice** | Fix implementer; current aggregate targeted re-review by controller and both independent reviewers |
| Display-only fallback accidentally rescuing invalid final, accepting nested text or masking native negatives/check failures | **fixed in current slice** (guard preserves existing proof flags; current regression/synthetic/full-suite coverage above) | Controller / current aggregate re-review |
| Codex protocol lacks independent refusal/completeness evidence when only completed prose is emitted | **assigned to later work unit** if richer native evidence is available; unchanged approved-plan limitation | Maintainer/caller / evidence-backed protocol work; preserve text and `not_assessed` |
| Future SDK/CLI completion-field/schema variants and historical missing metadata | **assigned to later work unit**; unchanged approved-plan limitation | Maintainer / protocol evidence and compatibility work |
| Business correctness and artifact meaning beyond explicitly selected mechanical checks | **assigned to later work unit**, unchanged caller-owned responsibility | Caller / existing business verification workflow; originals remain controller-only |
| Reproduction of actual transient provider/network faults | **assigned to later work unit if requested**, unchanged approved-plan limitation | User/controller / fault-specific evidence workflow; ordinary synthetic/live completion is not fault reproduction |

No new scope tradeoff or unclassified residual risk was identified. Remaining current-source outer-native/replay verification is an explicit current-gate controller handoff, not a deferred accepted finding or a request to change the goal. Delegate implementation checks have no blocker. **Next entry point: controller current-source verification and independent dual-route targeted aggregate re-review of DS-A1; no commit or gate transition by this delegate.**
