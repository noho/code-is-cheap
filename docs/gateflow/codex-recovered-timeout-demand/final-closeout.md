# Final closeout — codex-recovered-timeout-demand

**Final closeout pass.** Terminal-driven collector repair, full Gateflow review, authorized live sync and both ordinary three-step live probes are complete. Draft PR [#59](https://github.com/noho/code-is-cheap/pull/59) remains OPEN/draft; no merge/approval/mark-ready/reviewer-request/Issue comment performed. Developer and Judge business candidates remain caller-unaccepted.

## Delivered behavior and docs

`scripts/agent-run-result.py` removes connection/startup text recognizers and deferred recovery queues. Call acceptance uses zero native/necessary postprocessing exits, one valid same-execution native successful terminal, complete nonempty authoritative final, intact log and successful selected checks. Codex uses ordered unique starts/final/turn.completed; Claude uses its root result and native completion fields. Structurally valid intermediate diagnostics are retained as bounded anomalies/needs_review irrespective of unfamiliar wording. Failed/absent/conflicting terminals, explicit negative completion fields, damaged logs, missing final or selected-check/process failure still reject; native completion never clears these errors. result_status stays not_assessed.

Two accepted review findings were also fixed in scope: DS-A1 preserves readable root partial when Claude result is blank; DS-PR1 restores the preexisting nonempty-joined assistant display guard so empty text blocks do not erase partial/canary attribution. Neither change rescues missing/invalid final or changes call acceptance. Tests and README.md/README.zh.md/shared sub-agents skill describe the final contract. Runners/profiles/catalog/routes/shim are unchanged.

## Review, commits and actual validation

| Checkpoint | Actual version / outcome |
| --- | --- |
| User-confirmed goal v2 / plan | goal SHAa68fd2c4… and plan13748c8c…; old whitelist-only artifacts explicitly superseded |
| Accepted plan | b5a8095a2f2c8f72596f4a393ad5c70e85ca48ca; independent mimo/ds plan review and targeted re-review |
| Accepted S-1 | edd3d7bc937752d4ecab1e63cc6ba8599f17dac3; dual slice review pass |
| Accepted aggregate | 1bd8246a0135958816be3cd4441b59e458af7af6; DS-A1 dual re-review 已修复 |
| Current source fix | aa7bcb747f41bba1ee1504005df5f938e8571aba; collector406ec869… / testsa65efef0… |
| Accepted actual PR review | 0feb4498aaa624c9984c1e705f04e75d808bd2c3; both required routes independently reviewed exact aa7bcb7/base62c3b26 with full173-file compare snapshot SHA c19f9e4b… and stable close OIDs; DS-PR1 已修复 |
| Latest mandatory local tests | 57/57 full suite,11 affected methods,62 before/after synthetic streams (57 mismatches→0; proof/exit/not_assessed unchanged); current-source native kernel suite2/2 actual pass |
| Rejection regressions | Both runtimes native/postprocess nonzero, negative/missing/conflicting terminal/final, parse damage/invalid identity and selected check failures remain nonzero; novel diagnostic recovery retains raw/source evidence |
| Hosted checks | GitHub reports zero checks/statuses/suites; no remote CI pass claimed. Required local checks actually passed |

Review details: code-review-decision.md, aggregate-review-decision.md, pr-review-decision.md; actual PR re-review artifacts `docs/reviews/pr-59-review-20261013-182754.md` (ds) and `…184446.md` (mimo). Final source matches both reviews; accepted-review metadata-only bridge is in evidence/pr-review-artifact-delta.json. Byte-faithful evidence archives/indexes retain every named raw snapshot/log; initial failed unit assertion, expected red regressions, nested sandbox initialization failure, state-drift capture failure and controller raw-evidence whitespace packaging correction are honestly preserved. Current source/native checks passed; no failure waived. Original root Mimo scratch remains locally and is copied unchanged in its versioned archive with provenance map.

## Actual installed entry and original replays

Actual authorized deployment: 2026-10-13 18:52:54 +08:00 from accepted review commit0feb449, source unchanged from independently reviewed aa7bcb7. Both `./scripts/sync-agent-tools.sh` and `./scripts/sync-skills.sh` exited0. Installed collector `/Users/leo/.local/bin/agent-run-result.py` SHA256 **406ec8697cd516f335d3334b8a554353c9cc587d5e60428c4b9ba21e5817891d**; byte-equal to approved checkout, verified again after both probes. Actual PATH runner entries `/Users/leo/.local/bin/codex-agent-run` and `/Users/leo/.local/bin/claude-agent-run`; native CLI `/opt/homebrew/bin/codex` =0.162.1, `/Users/leo/.local/bin/claude` =2.1.296. Both installed skill copies also match. No sync-codex-agent needed because profile/catalog/routes/shim unchanged. Exact command/stdout/hash records: evidence/live-sync/summary.json and live-verification.md.

| Original case | Installed replay | Preserved proof / business disposition |
| --- | --- | --- |
| Developer timeout/high-demand | actual0, completed/needs_review/not_assessed, errors0/anomalies8/warnings0 | 5 notices+3 previous anomalies, final/session/usage/tools/canarymatch/2 artifacts unchanged, source hashes before==after; business acceptance pending |
| Judge unknown TLS close_notify/handshake EOF | actual0, completed/needs_review/not_assessed, errors0/anomalies10/warnings0 |4 notices+6 previous anomalies, final/session/usage/tools/canarymatch/4 artifacts unchanged, source hashes before==after; business acceptance pending |

New records are evidence/original-replay-installed.json and judge-replay-installed.json. Frozen original summaries/logs/business files remain unchanged; no business Agent rerun, no G1 release or business judgment acceptance inferred.

## mimo-flash live probes after sync

| Runtime | Actual execution | Tool evidence / independent result |
| --- | --- | --- |
| Codex | managed/native/runner0/0/0, passed, turn.completed | exactly3 successful command results: full input read → actual Python input read/math/exclusive new-file write → full result read; count5,sum6,squares374; nonce/inputSHA/regular-fresh artifact verified |
| Claude Code | managed/native/runner0/0/0, passed, root success | exactly3 successful tools Read/Bash actual isolated Python+open x/Read; count5,sum−41,squares415; nonce/inputSHA/regular-fresh artifact verified; only1 known benign model-name stderr warning |

Both inputs byte-unchanged, canarymatch and readcandidate true. Controller inspected actual commands/results in order and compared file data to independently prepared oracle, not final prose alone. Records/native synthetic logs/input/result/program transcripts: evidence/live-probes/{codex,claude}/, live-{codex,claude}-run.json, live-probe-prelaunch.json. These ordinary real-provider probes verify tool I/O/computation/runtime completion; they do not inject or claim actual network fault reproduction. Classification repair is proved by real original-log deterministic replay and synthetic/negative native protocol regression.

## Findings, residuals, association and next entry

DS-F1/DS-F2/C1 planning items addressed and re-reviewed; DS-A1 and DS-PR1 both accepted→**已修复**, independent dual verification. No unresolved accepted finding, needs-more-evidence, blocker or unclassified risk. Optional extra edge-test consolidation assigned maintainer later regression-maintenance work unit (existing immutable probes cover current contract). Native empty-frame scenario currently synthetic-only, future native schema/nested variants/Codex refusal metadata limitations assigned maintainer later evidence-backed work units. Business correctness belongs to caller; both originals remain pending. Actual injected transport faults later only if requested. CI absence is recorded, not a claimed pass. Existing postterminal payload observability stays raw-log based, maintainer follow-up if needed.

External Issue association/comment: **N/A** (bug-fix work unit, no external Issue specified/created). Merge remains user-owned; PR stays draft. This task has already synced the two applicable components. Use a new shell or `source ~/.zshrc` when interactive launcher functions change; direct installed runner callers on PATH need no sourcing. Reopen Agent sessions to load updated skill. Applicable actual sync commands are recorded above; no extra approval/duplicate sync needed for this unchanged installed source.

**Work unit completed. Next entry: user manual merge of draft59 and caller's separate technical/business acceptance workflow for the preserved Developer/Judge candidates.** Remaining publication is delivery evidence only; source/native/probe results do not change with its metadata commit.
