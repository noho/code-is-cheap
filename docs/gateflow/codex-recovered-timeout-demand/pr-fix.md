# PR59 accepted DS-PR1 fix

DS-PR1 is **fixed in the current worktree and synthetically validated**. This delegate makes no PR-review-pass or live-pass claim. The only accepted finding is the controller's DS-PR1 in [pr-review-decision.md](pr-review-decision.md), originating from [the actual DS PR59 review](../../reviews/pr-59-review-20261013-173833.md). No additional finding was provided or implemented.

Work unit: `codex-recovered-timeout-demand`. Existing branch: `fix/codex-recovered-timeout-demand`; unchanged HEAD: `2f0db8fb5fdfca02d90a69503b943aee348a81a0`; existing draft PR59. The authoritative goal and plan remain unchanged:

| Input | SHA-256 |
| --- | --- |
| goal-confirmation-v2.md | `a68fd2c4dbc3be7e7cefb943eceff4434f40b2352b25a4083948f2c2001b49b6` |
| plan-v2.md | `13748c8ceb3e84dfd6ee3764ad7dfb534d3221d1401f15a11a09654412c039f4` |
| pr-review-decision.md | `f68bf2e2d4e817976a60a0b59c39436aebceb98bbd209a0f9c1ba762dfeed8d2` |
| DS actual PR artifact | `7d4ccce0e0298339f2ffe679cca52dadaddedab761e0f2098123fd04edc90b14` |

## Exact change and source identity

`Collection.claude()` now computes `joined = "".join(text)` and permits root assistant display assignment only when `joined` is nonempty. An empty joined string retains the earlier `final`, `final_line` and displayed character count. Root ownership stays required; whitespace-only joined text still updates the display without trimming or prose interpretation. Authoritative root result validation, completion proof, terminal handling and selected checks are unchanged. Retained assistant display never supplies acceptable-final proof.

| File | Before SHA-256 | Final SHA-256 | Delta |
| --- | --- | --- | --- |
| scripts/agent-run-result.py | `aa9b1a3eef7f048e6d8e8a06e06510da9178fcba9097270d422cf2eafc2dd7ff` | `406ec8697cd516f335d3334b8a554353c9cc587d5e60428c4b9ba21e5817891d` | +3 / -2, one local joined-text guard |
| tests/test_agent_run_results.py | `6cda405c565c9ebc200885bd61c1d8fe7e480b3562330afacd63e9ac38be891b` | `a65efef0fa30fb631420fc8e786a825b1c31cfd67c555df66bd7af0c9b6678ea` | +53 / -0, one regression method |

The exact two-file patch is [source-delta.patch](evidence/pr-ds-pr1-synthetic-20261013T100056Z-ed64579b/source-delta.patch), SHA-256 `184bba5919d4949db51803a8426c053c4ea4b4cbb257901aa2ac8ed8afa07c24`. Original 56 test methods remain; the suite now contains 57. All final validation runs record these exact final source hashes before and after execution. The pre-fix red test uses the final test file against the unmodified `aa9b1a3e…` collector; it does not claim to test the original test-file hash.

## Actual validation

All commands ran in `/Users/leo/workspace/code-is-cheap`. [EVIDENCE.md](evidence/pr-ds-pr1-synthetic-20261013T100056Z-ed64579b/EVIDENCE.md) lists exact command arguments, source snapshots, exits and raw stdout/stderr. Each CLI probe retains its complete synthetic input JSONL, exact argv, process exit, raw report, stderr and internal `final_line` observation in the phase snapshot. These are synthetic streams, not native transcripts.

| Validation | Actual result |
| --- | --- |
| Pre-fix new regression method | Exit 1; 1 method, 57 expected failing subtests: 56 empty-text invalid-result cases plus whitespace followed by an empty frame. Raw failure output retained. |
| Pre-fix synthetic probe | Exit 0 for successful bug reproduction; 62 cases, 57 contract mismatches. No acceptance/exit/proof mismatch. |
| Final synthetic probe and saved-report comparison | Both exit 0; same 62 input streams, zero contract mismatches. All 62 preserve terminal, completion proof booleans, execution/validation status, exits, tool counts and `not_assessed` across versions. |
| Final affected current-source suite | Exit 0; 11 methods, all passed, 10.358 seconds reported by unittest. Includes Claude ownership/core/native metadata, duplicate/postterminal, selected checks and native/postprocessing exit paths. |
| Final mandatory full current-source suite | `python3 -B -m unittest discover -s tests -p test_agent_run_results.py -v`; exit 0; **57/57 passed**, no skips, 29.885 seconds reported by unittest. |
| Python syntax | Exit 0; both changed files compiled with `compile()`; no bytecode writes. Exact command in syntax-final/result.json. |
| Diff check | `git diff --check`; exit 0. |

The full suite includes the existing temporary-directory installation fixture; no live sync or installation was performed. The native kernel suite was not rerun. No original replay, original replay helper, original business source or raw other-agent log was read/executed. Earlier/archive evidence is referenced only for the accepted finding and binding contract; no old validation pass is substituted for current-source checks.

## Coverage and proof boundary

The new method has 56 invalid-result subtests: matching and mismatched partial canary, one/three empty text blocks, with/without a root tool call plus paired tool result, and missing terminal / absent result member / null / number / list / empty / whitespace result. They retain the earlier display and exact character count, remain failed/rejected/nonzero/not_assessed, retain canary match or mismatch, omit the false missing-canary error and retain mismatched proof attribution at output event line 2 / proof line 2 / raw output path. The persistent probe also checks internal `final_line=2` for matching and mismatching cases.

Six controls cover valid result ownership, a normal nonempty authoritative `content_filter` negative displayed and rejected, tool-only frames, mixed empty/nonempty root updates, paired nested empty/nonempty frames and whitespace-only root text followed by empty text. The first five complete reports are unchanged in the before/after comparison after replacing only the distinct probe fixture-directory segment in path fields; all unnormalized raw reports remain saved. The whitespace control confirms whitespace updates are preserved, then survive a later empty joined-text frame. Existing full-suite tests retain Codex, root/nested identity, duplicate/postterminal fencing, artifact/canary checks, native/postprocessing exits, diagnostic bounds, report schema and not_assessed coverage.

## Failed evidence-capture attempt and concurrent bookkeeping

The first final-manifest capture exited 1 on an equality assertion because only controller-owned `state.json` changed concurrently. Its exact heredoc/script, raw failure output and hashes are saved under [failed-final-capture-attempt/](evidence/pr-ds-pr1-synthetic-20261013T100056Z-ed64579b/failed-final-capture-attempt/result.json). That attempt copied final source snapshots but stopped before writing the manifest. No source/test check failed after the fix.

Observed state SHA-256: `a74b1f281a3419aa01f8de3413845faa4fc7976527e6cdc142898d7a24048f35` initially, then `2c23f385e836041a673f57d9833cd4efee149b62601445360b18095780edb7f3`. This delegate did not write, restore or adjudicate state. The corrected capture separately verifies binding-input equality and records controller-owned drift; exit 0. Goal, plan, decision and DS review remain byte-identical. HEAD and branch are unchanged. No earlier artifact/evidence was edited by this delegate.

## Classified residuals and controller continuation

| Residual or remaining task | Classification / owner / destination |
| --- | --- |
| DS-PR1 | Fixed locally with current-source synthetic proof; controller verifies delivery and routes updated-source dual actual-PR re-review. No accepted DS-PR1 fix remains for this delegate. |
| Empty-block native trigger has no direct native observation here | Evidence limitation; controller/maintainer retain the accepted synthetic finding. No native reproduction claimed. |
| Outer current-source native suite and both original replay versions | Required controller validation; not run by this nested delegate, not claimed passed. Controller owns original inputs/helpers. |
| Commit/push/update existing draft59 and versioned dual PR re-review | Required controller gate work; this delegate performs no Git/GitHub mutation or review dispatch. PR review remains pending. |
| Concurrent state drift | Controller-owned bookkeeping; reconcile in controller state/closeout. Not a production/test failure or binding-goal change. |
| Installed equality/replay, approved sync and live probes | Controller delivery after full review; pending, no live-pass claim or sync by this delegate. |
| Existing absence of remote CI checks; post-terminal diagnostic payload observability | Existing CI gap / maintainer observability follow-up; no fresh GitHub check or change by this delegate. Raw log retention and source-line fences remain unchanged. |
| Business correctness, Codex absent native refusal field, future native schema and real transient-fault reproduction | Existing caller/maintainer/user-controller follow-up boundaries; unchanged, no additional fix or prose heuristic. `result_status=not_assessed`. |

Delegate blockers: **none**. Only the two allowed production/test files, this `pr-fix.md`, and the uniquely named new synthetic evidence directory were written. No goal, delegation, confirmation, commit, push, PR/GitHub write, sync, merge, runner/README/skill edit or original-data read was performed. Next entry point is controller validation and adjudication of this exact source version, then the controller-owned existing-PR update and versioned re-review.
