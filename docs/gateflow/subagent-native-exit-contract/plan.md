# Sub-agent native exit contract — implementation plan

Status: ready for independent Planreview; not an implementation approval or a controller gate decision.

Binding scope: [goal.md](goal.md), the current user handoff, and repository [AGENTS.md](../../../AGENTS.md). Branch: `fix/subagent-native-exit-contract`; approved base: `32a244d1e286086be86dba837976d3d72fdd6c1f`. The clarified interaction contract overrides the older acceptance and retry rules in the sub-agents skill. This authoring task changes only this file. No implementation, tests, model calls, delegation, commits, branch changes, PR actions, sync or deployment were performed.

## Code evidence and root cause

The inspected checkout has the following concrete ownership problems:

| Source | Observed behavior and implication |
| --- | --- |
| `scripts/agent-run-result.py:407–455,469–495` | One collection path records malformed/missing native events, last-message discrepancies, missing declared artifacts and canary mismatches in `errors`. These observations have different owners; an absent requested report is not a native CLI exit. |
| `scripts/agent-run-result.py:514–528,574–576` | Any `errors` produces `validation_status=rejected`, synthesizes `runner_exit_code=1` when the input was zero, and makes the collector process exit 1. `agent_status` also combines native exit, wrapper postprocessing, execution proof, identity, successful terminal and final validity. The ostensibly informational `result_status=not_assessed` does not undo these failure verdicts. |
| `scripts/codex-agent-run:498–505,510–552` | `print ... \| "$runner" ...` runs under `pipe_fail`; `$?` is an aggregate pipeline outcome, not necessarily the CLI's status. `run_exit` then mixes that value with last-message handling and collector exit. Missing optional last-message output, a destination race and a real copy failure currently all promote zero to one. |
| `scripts/claude-agent-run:443–458` | The launcher function's status is passed as both native and runner exit; any collector nonzero promotes native zero to outer failure. |
| `scripts/agent-tools.zsh:81–120,205–236,313–448`; `scripts/agent-endpoint.py:173–231,250–278` | Both launchers can fail before starting the CLI: credential/helper/local-service checks, Codex home/model-card/connection/shim checks, and Claude connection/settings validation. Claude's helper eventually `execvpe`s the CLI; Codex invokes it as its last command. A returned launcher status cannot blindly be described as a native process exit. These are launch plumbing facts, not permission to change providers or routes. |
| `scripts/sub-agent-preflight:95–159,210–229,244–312` | Preflight checks setup and emits a command without executing it; it appends final-answer, optional canary and declared-artifact instructions. It has no result acceptance or retry loop. Its setup failures must stay setup failures. |
| `scripts/agent-sandbox:233–255,650–654,730–748` | The optional envelope checks collector readability and artifact/input permissions before dispatch, then execs the fixed runner. It does not consume result statuses. Existing read/write restrictions are unrelated to task acceptance and remain intact. |
| `tests/test_agent_run_results.py:86–114,466–579,974–980,1038–1057` | Direct collector tests and runner tests share an assertion helper that derives process exit from `validation_status`. Existing tests encode the very rejection policy being replaced, including report/canary rejection and postprocessing promotion. They cannot merely be left as the acceptance oracle. |
| `README.md:373–436,752–778`; `README.zh.md:349–401,698–722`; `skills/sub-agents/SKILL.md:61–108,123–132`; `skills/sub-agents/references/advanced.md:18–36` | These consumers teach mechanical rejection as nonzero exit, successful native terminal metadata as acceptance, and a fixed one-same-provider retry ceiling. Both languages and the advanced reference need the same new contract. |

Other current field consumers found outside historical gate/review artifacts are `tests/test_official_catalog_runtime.py:401–419,455–467` and `tests/test_agent_sandbox_runtimes.py:120–127`. Their clean/tool-error success assertions remain applicable; the official host-disabled case must assert the observed native outcome rather than assume absent business output means nonzero. `tests/test_install_endpoints.py:431–474` already proves some Claude launcher failures never enter the CLI, and `tests/test_agent_sandbox.py:1623–1668` exercises real launch plumbing with fake executables. These provide a basis for offline launch-boundary coverage.

Root fix: separate **native process outcome**, **runner setup/delivery failure**, **protocol/check observations**, and **caller task acceptance**. Moving just the artifact error to another list, or changing only the shell exit while retaining a misleading `failed`/`rejected` report, is insufficient.

## One implementation slice

**S1: make one runner invocation faithfully expose one CLI interaction, with diagnostics and caller acceptance independent.** Code, regressions and consumer documentation ship together. No prerequisite experiment or staged migration requires a second slice.

Necessary implementation scope:

- Both runner scripts and `scripts/agent-run-result.py`.
- The narrow launch/error boundary in `scripts/agent-tools.zsh` and, where needed for Claude's pre-exec errors, `scripts/agent-endpoint.py`. Do not duplicate provider setup in the runners or change connection resolution, models, credentials policy, sandbox permissions or shim behavior.
- `scripts/sub-agent-preflight` only for directly affected help/result wording and integration with the unchanged generated command contract; retain its setup validation and optional prompt instructions.
- `tests/test_agent_run_results.py`, relevant launch/setup cases in `tests/test_install_endpoints.py`, `tests/test_sub_agent_preflight.py`, and directly affected consumer assertions identified above. Extend existing test files rather than build a new verification framework.
- `README.md`, `README.zh.md`, `skills/sub-agents/SKILL.md`, and `skills/sub-agents/references/advanced.md`.

Inspect `agent-sandbox` compatibility, installation/backup tests and staged installation behavior; change those production helpers only if an actual dependency of this contract requires it. No new service, durable result store, supervisor, automatic recovery, schema framework or provider configuration belongs in S1. Explicit persistence/resume options remain caller-selected CLI capabilities; they do not authorize automatic continuation. Each invocation launches at most one chosen CLI and waits for its actual exit.

## Process and failure ownership

### Native versus setup and delivery

1. Capture the launched CLI's wait status separately and immediately. Native nonzero is returned exactly, including the shell's conventional signal-derived status when actually observed from that process. Never replace it with collector/check status, a prompt-producer status, or a guessed zero.
2. Remove the Codex pipeline ambiguity: feed the same prompt bytes through a prepared stdin source, or independently snapshot the CLI component's status before any later command overwrites it. An early-exiting CLI must not acquire `print`'s SIGPIPE as its native exit. Input preparation failure before launch is setup failure. A producer-side broken pipe after a CLI has itself completed is diagnostic information, not a substitute native status.
3. Known pre-CLI failures, including failures inside the managed launcher/helper, are runner setup failures. Preserve the existing runner setup convention: outer exit 2, clear original cause, and no native-result report pretending a CLI ran. If private logs were already opened, print their paths on runner stderr. Preserve preflight's existing exit 1 for failed setup and exit 2 for usage errors; it is a command generator, not a native invocation.
4. Add only the minimal invocation-local launch-outcome communication needed between the existing runner and launcher/helper to distinguish pre-exec failure from an executed CLI's return. This must be an explicit internal control channel, not parsing model output or human stderr. Do not identify “not started” from missing native events, reserve a native exit number as a setup sentinel, or infer native zero from absent metadata. A real CLI returning 1, 2, 126 or 127 is still a native return. Preserve ordinary interactive launcher use when the runner-specific channel is absent. Keep the channel private to launch plumbing and close it before agent tools could inherit it; it is neither persistent execution storage nor a new public CLI feature. Local mechanics are the implementer's choice, but these distinction tests are required.
5. Real runner-owned delivery errors remain errors of the wrapper: failure to copy a requested last-message file to its new destination, a destination race that prevents that copy, failure to invoke/complete the collector, or failure to deliver its serialized report. Record them separately from native outcome. A missing, malformed, mismatching or unreadable native output discovered by a completed collector is a diagnostic observation, not evidence that the wrapper failed to execute collection.
6. If the native status was never obtained, do not emit a normal native report with an invented status. Report the wrapper interruption/wait failure and retained paths on stderr, preserving an observed runner signal exit where available. This scope does not recover lost host handles or promise a summary after termination.

Let `N` be an actually observed native status and `W` the independent wrapper delivery outcome (`0` or `1` after launch). The outer runner exit is:

```text
before CLI launch: setup/usage failure -> 2, no fabricated native report
after CLI exit:    N != 0 -> N
                  N == 0 and W != 0 -> 1, explicitly a wrapper delivery failure
                  N == 0 and W == 0 -> 0, regardless of diagnostics or task acceptance
```

Native nonzero takes precedence if both the CLI and wrapper fail, while the separate wrapper observation remains visible. Checks cannot set `W`. Retained-but-corrupt log data, missing/invalid final events and failed selected artifact/canary checks cannot set `W`.

### Collector process exit

`agent-run-result.py` is a serializer/observer. Once it successfully produces its report, its own process exit is 0 even when the report records native nonzero, invalid protocol, missing final, tool errors or failed checks. Remove the `validation_status -> collector exit` mapping at line 576. Collector usage/setup errors and unexpected collection/serialization/output failures remain collector-process failures; runners identify them as wrapper delivery failures, never as native failures.

Keep caught output/stderr read errors and event-decoding failures in a serializable report. Do not convert them into unhandled exceptions. If the collector process itself fails or produces no usable report, the runner must surface its actual code/cause, known native exit and log paths on the caller's stderr, independently of the retained runtime stderr. Do not fabricate a final answer or print an apparently complete success report. A best-effort diagnostic is sufficient when stdout itself is broken; no durable fallback-result mechanism is introduced.

### Codex explicit last-message handling

Preserve private temporary capture, no-clobber checks and the exit trap's retained-file pointer. The event stream continues to own final-answer extraction.

- No regular native last-message file: record the missing/invalid optional output and its requested destination; `W=0`. If the stream contains a valid final, the interaction is still completed.
- A saved last-message file disagrees with the event final, or a collector cannot read that auxiliary file: retain both sources and the discrepancy; `W=0`.
- A real copy/destination failure after a regular temporary file exists: `W=1`; preserve the temporary file and report its actual path. Do not overwrite an occupied destination. Native `N` stays unchanged.
- Native nonzero plus any of these cases: return the exact native code and retain both native and wrapper observations. A failed optional-file check must not be relabeled as a copy failure.
- Apply these ownership rules in `--detail` too. Detail still returns raw output, bypasses collector/canary/artifact checks and does not gain a result-acceptance policy.

## Result fields and status compatibility

Keep the existing report object, field names, truncation limits, diagnostic entries and `schema_version=1`. This is an explicitly documented behavioral migration, not a claim of unchanged status semantics. One additive field is necessary to preserve independent failure ownership; avoid unrelated schema changes.

| Field | New precise meaning |
| --- | --- |
| `runtime_exit_code` | Exact observed native CLI status. No check, parser or postprocessing override. Prelaunch/unknown-status failures do not emit the ordinary report rather than invent this value. |
| `wrapper_exit_code` (additive) | Independent postlaunch runner delivery outcome, 0 or 1. Remains 0 for protocol/check findings. Allows a native nonzero and a wrapper failure to be represented simultaneously. Underlying I/O/collector codes and causes remain in diagnostics. |
| `runner_exit_code` | Actual outer status according to `N/W` precedence above, never synthesized from `validation_status`. |
| `agent_status` | `completed`: native 0 and an attributable complete nonempty native final is available. `incomplete` (new value): native 0 but collection cannot establish complete final delivery/ownership. `failed`: an observed native nonzero only; it describes the process, not blame assigned to a provider/model or a business verdict. Wrapper copy failure alone does not turn an otherwise completed interaction into `failed`. |
| `validation_status` | Diagnostic rollup only: `passed` if there are no errors/anomalies; `needs_review` if either exists. Existing warning-only behavior remains `passed`. Stop emitting the old acceptance value `rejected`; retain detailed errors, counts and source locations instead. No caller/provider retry is implied. |
| `result_status` | Always `not_assessed`. The caller alone decides task/artifact acceptance. |
| `terminal` | Retain the observed terminal identity: Codex `turn.completed`/`turn.failed`; Claude its root result's string `subtype` (`success` remains `success`). Keep `conflicting` for multiple terminals and null when unavailable. Do not manufacture Claude `terminal=failed` merely because a success-labeled result reports a limit/refusal or has invalid completion metadata; preserve the reported subtype and diagnostic. |
| `final_answer` and existing length/truncation fields | Preserve native text verbatim within the existing display cap. Preserve readable partial/candidate text when final proof is incomplete, with `agent_status=incomplete` and explicit diagnostics; it is not a manufactured complete final. No fallback from nested Claude text to a root final. |
| `session_id`, `usage`, `runtime_metrics`, `wall_clock_seconds`, `logs`, check and diagnostic fields | Preserve current sourcing and limits: null identity on invalid/conflicting identity; no invented usage, no aggregation of streaming fragments, no trusted usage from conflicting terminals; actual timings and raw log paths. Optional check outcomes are observations. |

Final ownership remains structural, not semantic. Keep the existing Codex start/order/identity/latest-completed-message checks and Claude root-result/parent-scope checks as visibility diagnostics. Missing/invalid/ambiguous execution proof makes the summary `incomplete`, never native failure. A malformed non-proof frame need not erase an otherwise unambiguous observed final. A valid explicit native end event is different from a “successful task” end event: valid negative terminal metadata or a valid failure terminal with nonempty final text is reported, but native 0 still represents a completed interaction. For Claude, valid `is_error=true`, a non-success subtype, `stop_reason=refusal`/`max_tokens`, or a structured limit/error with an attributable final must not alone produce `agent_status=failed` or a task rejection. Preserve malformed metadata diagnostics and genuinely invalid final/provenance visibility. Preserve the existing supported historical absence/null stop metadata and absent Claude identity behavior.

Neither final prose nor words such as “blocked”, “unable”, “import failed”, “skeleton” or “complete” influence these fields. Do not add success/failure keyword lists, semantic answer classifiers, final-content task checks or path extraction. Existing explicit canary proof parsing and tool-syntax diagnostics may remain informational; they must never become a task-success classifier.

Compatibility changes to call out in both READMEs and skill/reference: native 0 with parser/check findings now returns 0; `rejected` is no longer emitted; native-zero insufficient final/protocol proof uses `incomplete`, not `failed`; Claude terminal labels reflect the reported subtype; collector's own successful-report exit is always 0; `wrapper_exit_code` is additive. Update the internal collector argument handoff to carry independent wrapper status instead of the overloaded precollection `--runner-exit-code` input (the collector command is internal, and direct-fixture tests must migrate with it). Callers that previously used nonzero/`rejected` to demand a report or canary must explicitly inspect `artifacts`, `canary_status`, diagnostics and their own evidence requirements. Clean success, ordinary tool-error success, exact native nonzero, raw detail output, log paths and field types otherwise remain stable.

## Required behavior matrix

Unless stated otherwise, these are collected runs for **both** runtimes, `N=0`, `W=0`; the collector successfully emits its report and exits 0. “Final” means structurally attributable native final, not a claim that the requested task succeeded.

| Case | Outer exit; report status | Required evidence retained |
| --- | --- | --- |
| Valid native final, no checks selected | `0`; `completed / passed` | Exact final, native terminal, raw stdout/stderr, real metrics where supplied. |
| Final explains Python import failure; declared optional report absent | `0`; `completed / needs_review` | Final unchanged; artifact `exists=false` and missing-artifact diagnostic. `runtime_exit_code=runner_exit_code=wrapper_exit_code=0`. |
| Final reports missing input/environment obstacle/inability/normal blocked answer, no checks fail | `0`; `completed / passed` (or `needs_review` only for actual recorded diagnostics) | No provider/business failure invented from prose. |
| Incomplete skeleton artifact exists and is a new regular file; native final delivered | `0`; `completed / passed` absent other diagnostics | Mechanical file facts only. Do not inspect skeleton completeness or accept its business content. |
| Canary mismatch, missing standalone proof, conflicting proof, or expected token becomes unreadable after valid setup | `0`; `completed / needs_review` | Existing `mismatch`/`unknown`, candidate read, mismatch source/line/path and counts. No silent pass. |
| Artifact absent/nonregular/hard-linked/log alias after valid setup, or its check read fails | `0`; `completed / needs_review` | Existing file facts and specific failed-check diagnostic; no native override. |
| Ordinary tool command failure (e.g. `rg` exit 1, import/permission error, Claude `is_error` tool result), or unfinished tool call, then valid final | `0`; `completed / needs_review` | Tool traces/anomalies and final; caller judges unresolved impact. |
| Recovered SSE disconnect/server retry/unknown intermediate diagnostic, then valid final | `0`; `completed / needs_review` | Every bounded diagnostic and full raw log; no wording inventory, new retry or provider switch. |
| Structurally valid native negative completion/limit/refusal/error terminal with final and native 0 | `0`; `completed / needs_review` | Actual terminal/subtype and negative fields in raw log/diagnostics, no synthetic process/provider failure. |
| Malformed non-proof JSON/event or damaged diagnostic frame, with unambiguous valid final proof still available | `0`; `completed / needs_review` | Parser error and its location; retain observed final. |
| Missing/invalid/duplicated/conflicting starts, identity or terminal prevents final ownership proof | `0`; `incomplete / needs_review` | Honest terminal/null/conflicting identity and proof diagnostics; readable candidate text kept as incomplete. |
| Empty/absent/whitespace/non-string/invalidly encoded final, or Claude root result lacks final despite assistant partial text | `0`; `incomplete / needs_review` | Missing/invalid-final diagnostic, raw logs and any readable partial text. No assistant/nested fallback manufactured as final. |
| Truncated, invalid UTF-8, absent or unreadable retained output prevents complete final extraction; collector catches it | `0`; `incomplete / needs_review` | Actual read/decode/protocol causes and paths. Successfully reporting damaged source data is not a collector-process failure. |
| Retained stderr cannot be read, but final proof is available | `0`; `completed / needs_review` | Read diagnostic and actual path, without asserting logs were intact. |
| Native `N != 0`, with full/partial/empty final or any diagnostic/check result | Exact `N`; `failed / needs_review`; `runtime_exit_code=runner_exit_code=N`, `wrapper_exit_code=0` | Native code, text and source logs remain available. Collector process itself exits 0. |
| Codex requested last-message file missing/nonregular, or saved file differs from final | `0`; `completed / needs_review` if event final proof exists, otherwise `incomplete / needs_review`; `W=0` | Specific auxiliary-output diagnostic, event-owned text, actual saved/temp path only when present. |
| Codex regular last-message exists but destination is raced/unwritable or copy fails | `1`; native 0, `W=1`; `completed / needs_review` if event final proof exists | Copy cause, destination and retained private final-message path. This is explicitly runner delivery failure. |
| Same real last-message copy error with native `N != 0` | Exact `N`; `failed / needs_review`; `wrapper_exit_code=1` | Both failures independently visible; wrapper code must not disappear behind native code. |
| Collector process invocation/crash/serialization/summary-write failure after native 0 | `1`; native status remains known 0; no trustworthy report/status promised | Caller stderr explicitly identifies collector/wrapper failure, underlying code/cause and retained logs. Do not replace a missing summary with a fictitious successful final. |
| Same collector-process failure with native `N != 0` | Exact `N`; no trustworthy report/status promised | Independently identify collector failure and exact known native code on stderr; retain logs. |
| Invalid prompt/cwd/output/canary input, missing launcher/helper/model card/required connection, or native exec cannot start | Runner setup `2`; no native report. Preflight retains its own setup/usage codes. | Fake native entry marker absent; original setup cause and any allocated log paths visible. No provider measurement sample claimed. |
| CLI really executes and returns 126/127; or Codex ignores a large stdin prompt and exits 0 with final | Exact native 126/127 with failed status; or `0` with completed status respectively | Never confuse native codes with setup sentinels or substitute upstream SIGPIPE. |
| Native status never obtained because wrapper interrupted/wait failed | Observed runner signal status, or wrapper failure `1`; no invented native report | Explicit unknown status and retained paths; no automatic recovery/relaunch. |

Combine recovered SSE/tool diagnostics with missing artifact/canary failure and with real postprocessing/native failure in tests so the independent axes cannot accidentally be recoupled. Detail-mode tests verify the same native/setup/delivery ownership while preserving raw stdout/stderr and bypassing optional checks.

## Offline validation and repository checks

Implementation verification must use deterministic independent fixtures and fake CLI executables; no paid model probe, portfolio replay, installed-runner modification, live endpoint request or deployment.

1. Decouple `assert_completion` from `validation_status`. Direct collector tests assert serializer exit separately from report native/runner/wrapper fields; public runner tests assert actual subprocess exit against the observed fake CLI status. Preserve malformed-event/final/identity, Unicode/finite JSON, diagnostic cap/source, usage and log-retention assertions while migrating their intended statuses. Do not globally replace every old 1 with 0 without checking the owner.
2. Add the specific import-failure-final plus missing report regression for both runtimes, and a mechanically valid skeleton fixture. Check exact final bytes, artifact facts, all three exit fields and no business verdict. An all-clear prose fixture and blocked/unable prose fixture with otherwise identical protocol must have identical process/status treatment.
3. Exercise every matrix family through collector fixtures and both public runners where applicable. Use independently authored malformed/truncated streams, not only the collector's own event builders. Include empty root result after assistant text, duplicate/conflicting terminals, invalid identity, native negative metadata, late expected-token disappearance, hard-linked artifacts and ordinary/recovered diagnostic combinations.
4. Exercise actual repository launch functions/helpers against fake `codex`/`claude` executables with a native-entry marker and controlled returns. Demonstrate setup errors never enter native, genuine CLI nonzero remains exact, native 126/127 is distinguished from exec failure, and prompt pipe behavior cannot replace native status. Use private temporary homes and synthetic connection data; never inspect or alter live keys/settings.
5. Reuse the existing missing/raced/unwritable last-message fixture controls, separately testing missing-file observations (`W=0`) and copy delivery failures (`W=1`) with native 0 and 7. Verify no-clobber and retained temporary-final paths. Add collector-process failure injection in a private staged script directory, including native 0 and 7, and summary-output failure; check caller stderr rather than requiring a JSON report from a failed serializer. Injection must not affect prelaunch canary setup validation accidentally.
6. Verify `--detail` raw stream bytes/redirection, explicit/new private log destinations, session arguments/identity, optional preflight prompts and command generation, envelope setup permissions, and the existing self-contained staged-install test. The install test directs both `AGENT_RUN_BIN_DIR` and `AGENT_TOOLS_TARGET` to a temporary directory; it is not live sync.

Run focused suites after implementation, then the documented full repository checks once the focused cases pass:

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

Use an available Python 3.11+ environment and the repository validator's existing PyYAML environment; report a missing prerequisite rather than silently installing or skipping a required check. No `.github` workflow directory exists in the inspected checkout; README specifies skill validation and full unittest discovery. Native-runtime/kernel opt-in suites are not required to establish this wrapper/collector contract: retain their directly affected assertions, record them as unexecuted coverage, and do not enable them or paid routes for this work unit. If launch-channel changes affect envelope operation, prove that plumbing offline using the existing mocked envelope tests rather than widening policy or adding a model probe.

Record tested revision/working diff, commands, exits and relevant fixture assertions in the controller's implementation evidence. This plan author has only inspected source; it does not claim these future checks passed.

## Documentation, caller policy and controller handoff

Documentation decision: **update user-facing operational documentation**, because exit/status semantics intentionally change. Revise the Runner results and Sub Agents sections in both READMEs, the skill's result/retry sections, and advanced optional-check wording. Explain native versus wrapper code precedence, `incomplete`, diagnostic-only checks, removal of `rejected`, collector process ownership and the required caller migration. Remove claims that missing artifacts/check failure or normal negative completion imply provider failure. Keep historical investigations/reviews as historical evidence rather than rewriting them.

Replace the skill's fixed “at most one same-provider retry, then fallback” rule with caller ownership: a caller may accept, ask for missing input, continue with a fresh context, or choose another interaction/retry count under its existing task authorization and project routing. A normal blocked/incomplete-work final is not automatically a failed provider attempt. Neither the runner nor this skill automatically retries, resumes, switches provider, escalates permission or grants authorization. Preserve original attempts and logs. Preserve the measurement rule: once a measured execution starts, retain it in its original batch; do not replace it with a retry result or retry until success, and retain prescribed concurrency. Prelaunch setup failures are not executed provider samples. `needs_review` alone requires neither user approval nor a new call.

The controller's next step is required independent Planreview for this public contract. The approved goal's explicit routes take precedence over AGENTS defaults: `gpt-6-sol` via Codex runner for implementation/accepted fixes; `mimo` and `ds-flash` via Claude runner for two independent parallel Planreviews and later complete Deepreviews. No built-in agents or recursive delegation. Controller adjudicates findings, dispatches accepted fixes and obtains affected independent re-review; a plan author does not perform these controller decisions. No review dispatch is authorized within this plan-only turn.

After the implementation/review gates, the controller owns draft-PR checks, inclusion of the two unchanged historical files, and closeout evidence. Record applicable post-merge/user-authorized deployment commands in closeout:

```bash
./scripts/sync-skills.sh
./scripts/sync-agent-tools.sh
```

Run them only from the checkout containing approved changes after user authorization. `sync-codex-agent.sh` is not applicable because this slice changes no profiles/catalogs/routes/shim. After deploying changed launchers, reload interactive functions with `source ~/.zshrc` or a new shell; reopen Agent sessions for changed skills. Installed runners already on `PATH` do not require callers to source shell configuration. This work unit does not merge or deploy automatically.

## Residual risks and uncovered areas

Classifications below use the repository's allowed residual-risk categories. “Fixed in current slice” denotes required S1 coverage, not work already completed by this plan.

| Risk / uncovered area | Owner and destination | Allowed classification / disposition |
| --- | --- | --- |
| Existing exit/status/check coupling, synthetic failure labels and unobserved launcher setup attribution | S1 implementer; runner/helper/collector code, fixture tests and consumer docs; controller verifies adjudicated evidence | **fixed in current slice**; required before implementation/review closeout, not deferred. |
| Repository consumers or external callers rely on legacy `rejected`, binary completed/failed enums, Claude normalized `failed`, or collector rejection exit | Repository consumers: S1 implementer/tests/docs. External callers: user/caller maintainers; caller integration after merge using the documented migration | Repository portion **fixed in current slice**; external integration **assigned to later work unit**, nonblocking for this authorized public-contract change. No compatibility flag preserves the bad acceptance rule. |
| Installed skill/launcher/runner skew until authorized sync | User/maintainer; post-merge sync from approved checkout and session reload recorded in closeout | **assigned to later work unit** (authorized deployment/integration), no live changes in S1. Staged installation is covered offline. |
| Native protocol/version variation may reduce final/identity/metrics visibility even when native exits 0 | Caller/runtime integration maintainer; explicit diagnostics and retained raw logs now, a separately scoped protocol-compatibility work unit if encountered | **assigned to later work unit** for variants not represented in fixtures. S1 must still return observed native exit and honest incomplete visibility. No paid probes required. |
| Wrapper death, stdout consumer failure or host-handle loss can prevent summary delivery and native status recovery | Maintainer; separate explicitly authorized lifecycle/recovery work unit, linked to the two existing host-handle-loss investigation files | **requiring new issue or explicit user decision**, nonblocking. This slice only reports known state/cause where execution is still observable; it does not implement historical durability/supervisor proposals. |
| Opt-in real native CLI/kernel suites and portfolio task are not rerun | Controller; implementation validation/closeout uncovered-coverage record; user/runtime maintainer owns any later explicitly selected integration validation | **assigned to later work unit** if needed; offline wrapper, source-log and launch-boundary evidence is S1's required verification. No claim of live/provider coverage. |

The user's two historical files remain unchanged and are to be included by the controller as requested. Inspection-time SHA-256 values, for preservation checks only:

```text
db4b8fac945c4d17da89c576870852b959808edd06ec0b3de03b5fd2ce9244fb  docs/reviews/runner-host-handle-loss-investigation-20261016.md
c0a61aad9e24c5c74c33e3ce277fb81c8c4083d2f9e53a77f318019238b09e59  docs/reviews/runner-host-handle-loss-investigation-20261016-evidence.json
```

Unresolved scope questions: none. The wrapper error exception, status migration and narrow launch-helper changes above are explicit plan decisions for the required Planreview, not silently retained business acceptance. Implementation remains pending controller adjudication and that review.
