# Native CLI interaction — replacement implementation plan

Binding inputs: [goal](goal.md), latest [scope amendment](scope-amendment.md), and [controller decisions](decisions.md). This replaces the conflicting design in `plan.md`; that file and its in-flight review remain historical. Plan only: implementation and independent review are pending.

## One slice and source basis

S1 delivers one thin CLI interaction: wait for the selected native CLI, return its actual exit and full final, retain logs, and leave business acceptance and further interactions to the caller.

- `scripts/agent-run-result.py:139–180,408–540,576` currently combines execution proof, three diagnostic classes, checks, acceptance states and a 12000-character final cap. Remove that coupling and redundant bookkeeping rather than rename its states.
- `scripts/codex-agent-run:488–557` obtains status from a prompt pipeline, promotes auxiliary-copy errors, then promotes collector errors. `scripts/claude-agent-run:443–458` promotes collector errors. These are the runner changes.
- `scripts/agent-tools.zsh:81–120,313–448` ends each launch path with the native command/helper. Setup can return before that command; `scripts/agent-endpoint.py:173–231,250–278` can fail before its Claude `execvpe`. A launcher setup return and a genuine CLI return can have the same number.
- Direct schema consumers: `tests/test_agent_run_results.py`, `tests/test_official_catalog_runtime.py:401–419,455–467`, `tests/test_agent_sandbox_runtimes.py:120–127`; operational consumers: both READMEs, `skills/sub-agents/SKILL.md` and `references/advanced.md`. Existing goal/amendment evidence establishes the missing-report bug and cap provenance; no paid reproduction is needed.

Change both runners, collector, these consumers and relevant existing regression suites together. Update `sub-agent-preflight` wording/tests only where they describe the changed checks. Inspect `agent-sandbox` and staged install/backup dependencies; preserve their setup/isolation boundaries and change code only for an actual direct dependency.

## Output contract: schema version 2

Collected mode emits one JSON object after native exit. Its complete top-level interface is:

| Fields | Meaning |
| --- | --- |
| `schema_version`, `source`, `runtime`, `provider` | `2`, `subagent_report`, and the selected runtime/provider; no inferred model identity. |
| `runtime_exit_code` | Exact observed native process code, including observed shell signal conventions. Never a parser/check/copy code. |
| `final_answer` | Full native final string, preserving whitespace and Unicode exactly; null when absent, nontext or ambiguous. An observed empty string remains empty with a diagnostic. |
| `session_id`, `terminal` | Observed native identity and terminal type/subtype; null if unavailable/ambiguous, with factual diagnostics. No synthetic `failed`/`conflicting` labels. |
| `wall_clock_seconds`, `usage`, `runtime_metrics` | Existing measured elapsed interval and attributable native totals; unavailable values null/empty object. No estimates or streaming-fragment summation. |
| `logs` | Existing `output`, `stderr`, `last_message` absolute paths or null; use the retained temporary final path when an auxiliary copy fails. |
| `diagnostics` | One list of concise `{message, path, line}` observations; unavailable location values null. Point to source evidence, without copying tool transcripts. |
| `checks` | `{artifacts: [...], canary: ...}`. Artifact entries retain `{path, exists, regular_file}`. Canary is null unless requested, otherwise `{proof_observed, proof_matches_expected, read_candidate_observed}`; matching is null when no comparable proof exists. These are observations only. |

Remove `agent_status`, `validation_status`, `result_status`, `runner_exit_code`, `final_answer_chars`, `final_answer_truncated`, diagnostic class arrays/counts/truncation metadata, and other redundant summary rollups. Add no wrapper status, completion flag, acceptance enum, compatibility flag or successor verdict. Do not relocate the final cap into another layer.

Source final text structurally: Codex's latest completed agent-message text; Claude's unique root result string. Nested/intermediate Claude assistant text is not a substitute final. Preserve an identifiable final despite unrelated malformed frames or native negative completion metadata; do not require a successful terminal to deliver its text. Missing/invalid/ambiguous final sources remain explicit observations, with readable partial material in retained logs and no replacement final prose.

Simplify parser bookkeeping to source attribution and useful observations. Remove success-proof/acceptance predicates and tool-text semantic suspicion heuristics. Keep damaged JSON/encoding, missing or conflicting terminal/identity, tool errors, recovered SSE/retry notices and native negative metadata visible with source locations. Extra nonessential event fields do not invalidate native text. A missing start/terminal frame is diagnostic information, not a second completion gate. Missing/conflicting totals are not invented.

Optional checks preserve current explicit opt-in and evidence limitations: canary proof/read candidates do not prove task correctness; artifact existence does not prove provenance/content. Missing files, hard links/log aliases, mismatched proofs and read errors become factual diagnostics/check observations, never exit decisions. Diagnostic entries summarize distinct issues with source references; no three severity classes, duplicate rollups or transcript-sized payloads.

## Exit and delivery ownership

- Before CLI entry, invalid arguments/inputs, unavailable dependencies, unsafe output destinations or actual launch failure remain runner setup errors (existing outer code 2), without an ordinary report inventing a native exit. Show original cause and any allocated log paths on stderr. Preflight keeps its own existing setup/usage codes.
- Capture the native command's wait status immediately. For Codex, snapshot the CLI pipeline component rather than aggregate `pipefail`, or feed prepared stdin without a producer pipeline; preserve prompt bytes. An early-exiting CLI must not inherit the producer's SIGPIPE status.
- Drop the initial plan's general launch/outcome channel and execution-proof protocol. The demonstrated ambiguity above needs only an invocation-local, error-only pre-exec pipe: launcher/helper setup errors report their cause; the descriptor closes on successful native exec and is not exposed to Agent tools. Narrow changes to `agent-tools.zsh` / `agent-endpoint.py` are limited to this error boundary and terminal exec, preserving ordinary interactive behavior. No launch-success messages, post-exit handshake, stored lifecycle state or duplicate provider setup. Failure to establish the handoff is setup failure; unobservable launch/wait outcome is reported as unknown, never guessed from logs or a reserved exit number.
- A collector that reads/parses/checks sources and successfully serializes its observations exits 0, even for missing/unreadable/malformed logs or absent final. Such data problems are not collector-process failures. Remove its acceptance-derived return and `--runner-exit-code` input.
- After primary delivery succeeds, return the exact native code. Auxiliary `--last-message` creation/copy/mismatch/cleanup failures cannot change it in collected or detail mode; retain available temporary text and expose the cause/path. Keep no-clobber and prelaunch destination checks.
- If the wrapper cannot execute collection, serialize or write the primary result, return a genuine delivery failure (outer 1 for native 0); preserve an observed native nonzero exactly. Stderr states the actual failure, known native code and retained paths. Do not demand JSON from a broken serializer or manufacture a native final/status. An interrupted wrapper or unavailable wait result reports what is known without inventing native completion.
- `--detail` remains raw stdout/stderr/redirection, skips automatic collection and optional post-run checks, and retains native exit semantics. No automatic retries, resumption or provider switching.

## Behavior matrix and required offline regressions

Unless stated otherwise, exercise both runtimes through public runners and the collector directly; assert actual exit separately from report content.

| Input / event | Expected behavior and evidence |
| --- | --- |
| Native 0, final explains Python import failure, requested report absent | Outer 0, exact native final, artifact absent observation; no task/provider failure classification. |
| Native 0, final describes missing input, inability or an incomplete skeleton | Outer 0, exact text; caller decides business completion and follow-up. |
| Native 0, tool error/recovered SSE/stderr notice/check mismatch/negative native metadata | Outer 0; concise source-linked observations and raw logs, no acceptance verdict. |
| Native 0, final longer than 12000 characters | Assert decoded final equality to the entire fixture, including Unicode/newlines/leading and trailing whitespace, through collector and both runners; removed fields absent. |
| Native 7 (also genuine native 1, 2, 126, 127) | Preserve exact native/outer code with or without final, check observations or damaged source data. Collector itself exits 0 on successful delivery. |
| Missing/empty/nontext final; malformed/truncated/invalid-UTF-8 or missing/unreadable source; duplicate/conflicting terminals | Preserve observed native exit; precise absence/shape/location facts, no fabricated final or blame. Unrelated damage must not erase an attributable final. Test nested-only Claude text cannot become final. |
| Codex auxiliary final missing/stale, destination raced/unwritable, copy/cleanup failure after native 0 or 7 | Outer/native stay 0 or 7 in collected and detail modes; primary final unchanged, retained temp path when available, precise diagnostic, destination never clobbered. |
| Collector process crashes/cannot launch, serialization fails, or primary stdout write fails after native 0 or 7 | Outer 1 or original 7; stderr distinguishes delivery failure and records known native/log facts. Separately prove malformed input can be serialized with collector exit 0. |
| Invalid setup or failed native exec versus actual CLI returning identical numeric code | Fake native-entry marker absent for setup, no invented native report; marker present for actual native returns. Exercise real repository launcher/helper paths using synthetic private configuration. |
| Large piped prompt and native early exit 0 or 7 | Actual CLI component code wins over producer SIGPIPE; complete prompt reaches a consuming fake CLI. |
| Existing/symlink/aliased output, artifact or final destination; optional isolation/preflight/detail/install paths | Preserve prelaunch safety checks, distinct/new files and private permissions; retain raw streams, arguments/session behavior and isolation boundaries. Post-run optional observations do not change native exit. |

Migrate existing assertion helpers away from `validation_status`-derived exits; independently assert schema keys, exact process code, exact final and diagnostic source. Reuse existing copy-race controls and fake runtime fixtures; add native-entry boundary cases in `test_install_endpoints.py` / existing mocked sandbox tests, not a new framework. Collector failure injection uses a private staged directory and must not accidentally break canary prevalidation. Stage installation only into temporary targets, never installed tools.

After implementation, run focused runner-result, preflight, endpoint and sandbox suites, syntax checks, then mandatory repository checks:

```bash
python3 -m unittest discover -s tests -p 'test_agent_run_results.py'
python3 -m unittest discover -s tests -p 'test_sub_agent_preflight.py'
python3 -m unittest discover -s tests -p 'test_install_endpoints.py'
python3 -m unittest discover -s tests -p 'test_agent_sandbox.py'
zsh -n scripts/codex-agent-run
zsh -n scripts/claude-agent-run
zsh -n scripts/agent-tools.zsh
bash -n scripts/sub-agent-preflight
./scripts/validate-skills.sh
OFFICIAL_CATALOG_RUNTIME_TESTS=0 AGENT_SANDBOX_KERNEL_TESTS=0 python3 -m unittest discover -s tests
git diff --check
```

Use Python 3.11+ and the existing PyYAML validator environment. Report prerequisite/environment failures honestly; do not silently waive checks. Native/provider and kernel opt-in suites remain unexecuted coverage; migrate their directly affected assertions without enabling paid probes. No tests are required in this plan-only turn.

## Documentation, policy and delivery

Update `README.md`, `README.zh.md`, the repository sub-agents skill and advanced reference with the complete schema-v2 migration: removed fields, full final, native exit ownership, information-only checks, genuine setup/delivery exceptions, and collector-process exit semantics. Migrate repository consumers directly; external callers must stop treating missing artifacts or diagnostic findings as runner acceptance. Preserve historical investigations, measurements and old review results as authored, including the two requested host-handle-loss investigation files.

Remove the skill's fixed same-provider retry ceiling and fallback sequence. Whether to accept, request input, continue or make another interaction is the caller's choice under existing user/project permissions and routes. Normal explanatory finals are normal replies. Preserve original attempts/logs, measurement batch membership and prescribed concurrency; retries cannot replace failed measured samples. Keep explicit persistence/resume capabilities without automatic context reconstruction or replay.

The controller adjudicates this plan and dispatches separate independent parallel reviewers under the confirmed routes, then implementation/accepted fixes and code review. This author does not claim review approval or implementation. Deliver the eventual tested/reviewed slice as a draft PR; user merges manually. No provider/model/routing/permission/config changes, portfolio replay, supervisor/storage/recovery system or live deployment is authorized.

Controller closeout records applicable `./scripts/sync-agent-tools.sh` and `./scripts/sync-skills.sh` commands and reminds the user to sync from the approved checkout only with deployment authorization. Reload interactive launcher functions with `source ~/.zshrc` or a new shell; reopen Agent sessions for changed skills. Installed runner callers already using PATH need no shell reload. `sync-codex-agent.sh` is not applicable to this slice.

## Classified risks and uncovered areas

| Risk / uncovered area | Classification, owner and destination |
| --- | --- |
| Exit/check coupling, final loss/cap, auxiliary override, native/setup ambiguity and repository consumers | **Fixed in current slice** (required, not yet done); implementer owns code/tests/docs, controller verifies evidence. |
| External callers depending on schema v1 or rejection exits | **Assigned to later work unit**; caller maintainers/user own adoption after merge, documented migration supplied here; nonblocking for authorized contract change. |
| Installed runner/skill skew | **Assigned to later work unit**; user/maintainer owns authorized sync and session reload from approved checkout. |
| Unrepresented native protocol variants and unrun real-runtime/kernel coverage | **Assigned to later work unit** if needed; runtime maintainers/controller own integration follow-up; this slice preserves native facts and source visibility without claiming that coverage. |
| Wrapper death/host-handle loss prevents observing native exit or delivering any result | **Requiring new issue or explicit user decision**; maintainer owns separate lifecycle/recovery work. Historical proposals remain evidence, not implementation scope. |

Readiness: ready for controller adjudication and independent revised-plan review. Unresolved scope blockers: none; review and implementation remain pending.
