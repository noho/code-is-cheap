# Final closeout: Codex recovery startup diagnostics

**Final closeout pass.** Work unit complete within its confirmed scope. Draft PR: https://github.com/noho/code-is-cheap/pull/54. User retains merge and live-deployment decisions.

## What changed / why

The old supported-recovery predicate required thread/turn starts at parsed ordinals1/2. The original native stream instead has one exact skip_host_skill_discovery startup diagnostic at ordinal2, a valid turn start at3, later recovered reconnect and valid final/turn.completed/native0. The fixed collector accounts for zero or one strictly recognized diagnostic in that gap and requires exact ordinal equality. It retains the original startup anomaly and every other recovery, lifecycle, final/terminal, exit, parser and selected-check fence. Unknown/additional frames cannot bridge the starts.

Product files: scripts/agent-run-result.py and tests/test_agent_run_results.py. No runner argument/schema/routing/provider/auth/sandbox/config change. No warning suppression. No original caller file/task/acceptance was modified or rerun.

## Verified evidence and limits

- Actual full56 deterministic runner/collector tests passed; independent reviewers reran them, including exact-head PR tests. Initial macOS path-alias assertion failure was corrected in the test before focused/full pass. Actual output preserved in evidence/implementation-tests.txt.
- Supported startup gap, ordinary failed tool plus recovery, adjacent/no-retry controls, lookalike/extra-field/path boundaries, unknown/execution gap frames, multiplicity/order/0–1–2–25 counts, parser corruption, failed/missing/invalid terminals/finals, native/postprocessing nonzero and explicit synthetic check failure remain covered. Raw detail/Claude/statistics/report behavior stays unchanged.
- Root's actual original-only structural replay now returns completed/turn.completed/needs_review and runtime/runner0, counts0/16/1, with startup line2 and recovered line322 retained. All four original file hashes, 364 events/177 tools, raw usage and wall2698.161843 are unchanged. The equivalent structural baseline's anomaly count is preserved; original optional checks were deliberately not replayed.
- Original business/canary/artifact/professional correctness is **not assessed** by this work unit. External agents received source and sanitized controls, never original business history. Real forced network interruption was not rerun; the parser defect was proved by actual recorded structure and adversarial offline controls.
- Immutable PR review used base0b2b6a4bc41430e5398c227b026fa98af640f1c0/head93e5cf325e3f39b8ee129d243e9bb4fa6992c67a, full28-file diff, hashf39c501bb889c7f74f18bb64f79b48436f8a1eb612caec0a6eb48c90120112d2. Head/base stable through reviewer/root close queries. Root verified actual full2335-line MiMo snapshot reads with no truncation. Source/test bytes remain equal to this reviewed head after derivative review/closeout records; the reports do not claim to review a later metadata OID.
- Repository has no configured CI/checks; actual offline tests and independent reviews satisfy this confirmed goal. All13 assigned runner subprocesses closed with actual exit0; real wall/token/diagnostic logs retained in evidence/dispatch-statistics.json and its referenced private logs.

## Reviews, adjudication and commits

| Gate | Artifact / disposition | Accepted checkpoint |
| --- | --- | --- |
| Plan/fix/re-review | plan-review-decision.md, plan-fix.md; accepted missing tool-failure interaction case fixed and verified by both routes | 3ea43c9 |
| S1 implementation/code review | implementation.md, code-review-decision.md; no outstanding accepted finding | 1225754 |
| Aggregate deepreview | aggregate-review-decision.md; both pass, no fix required | 86ee51d |
| Draft readiness | ready.md, work branch pushed and new draft PR created | 93e5cf3 |
| Exact-OID PR review | pr-review-decision.md and both pr-54-review artifacts; no outstanding accepted finding, no code fix/re-review required; accepted evidence pushed | 636d1dc |

Dynamic config paths/nonblank IDs remain payload under an exact warning-envelope/message identity; the fixed-path-family suggestion was rejected with direct original match evidence. Low fixture-location suggestions were rejected with stable canonical test-resource ownership recorded: test maintainers retain/move the three tracked inputs and test references together. No deferred accepted finding or unclassified risk remains. Expected or corrected tool failures retain diagnostics; they did not mechanically invalidate otherwise evidenced reviews.

## Docs and compatibility

Existing README/skill recovery/needs_review/statistics/check wording remains accurate, so no product doc edit is needed. Binding plan, decisions, actual tests/replay and closeout evidence are versioned in this work unit. Existing invocation and report fields unchanged; no migration/config action required for callers. Only the evidenced exact envelope/text/ASCII lexical path grammar and single-warning start gap are supported.

## Remaining owners / actual entrypoint status

| Remaining area | Owner / destination |
| --- | --- |
| Future extra fields/text, Unicode or space paths, multiple startup warnings | Collector maintenance: later evidence-backed work unit; current conservative rejection preserved |
| Original optional/business acceptance and task restoration | Caller/business controller: its own authorized validation/restoration, not this PR |
| Manual merge, installed-live update and any live reconnect validation | User/deployment controller: separate merge/sync authorization |
| Stable regression-input availability | Test maintainers: keep versioned inputs with test references, update atomically if reorganizing |
| Optional future CI automation | Repository maintainers: separate work only if requested; current existing CI policy unchanged |

Source collector hash ea836b684381420045b064c7ba865ac2b1cf6fa5501b308d0379661253df7301. Installed /Users/leo/.local/bin/agent-run-result.py remains old hash0301f6dd9f589b7b705aa5e2f5033b573a2bfce23f0ae2ca23b40c374dab06e4 (actual read-only status: evidence/deployment-status.json). **Fix not deployed.** Repository/source entry validated by deterministic public runner tests and original structure replay; no claim of a new live provider run. Standard codex-agent-run --provider mimo, including agent-sandbox wrapping, gains this classification correction after installed collector synchronization; arguments stay the same. --detail keeps its existing raw-output semantics.

## Issue status / next entry

No GitHub issue number was designated, so no closing keyword, issue creation or external closeout comment applies. Draft PR stays open/draft; no merge/approve/mark-ready/reviewer request/live sync/caller dispatch was performed.

Next entry: user manual merge of PR54, separately authorize sync to live, then caller verifies its actual standard entry and independently handles original selected/business checks and task restoration. Controller scope is complete; current gate is final closeout pass.
