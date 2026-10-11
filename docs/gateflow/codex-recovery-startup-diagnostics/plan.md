# Implementation plan: Codex recovery with the evidenced startup diagnostic

## Gate, authority, and completion status

- Gate: `plan`; work unit: `codex-recovery-startup-diagnostics`.
- Binding contract: [confirmed goal](goal.md); execution state: [state](state.md).
- Branch: `fix/codex-recovery-startup-diagnostics`; base: `0b2b6a4bc41430e5398c227b026fa98af640f1c0`.
- Preflight verified the existing work branch. Initial status contained only the untracked work-unit artifact directory. Do not create/switch branches or include unrelated changes.
- This artifact is ready for independent `plan review`; it does not declare that review passed. The assigned planner writes only this file, performs no product implementation, dispatch, staging, commit, push, deployment, or gate-state update. The root controller owns those actions and adjudication.
- No separate design document was supplied. Alignment is with `goal.md`, the sanitized evidence, and the current collector contract; no new architecture contract is introduced.

## Goal, motivation, and success signal

Fix the false recovery rejection when one exact supported `skip_host_skill_discovery` startup diagnostic occupies the gap between a valid first `thread.started` and the single valid `turn.started`. Preserve the existing evidence required to classify an exact reconnect notice as recovered in the same execution.

The principal synthetic acceptance result is `completed` / `turn.completed`, native and runner exits 0, no recovery rejection, one retained startup anomaly, and one recovered connection warning. Its `validation_status` is **`needs_review`**, not `passed`. The adjacent-start control stays `passed`; the startup-warning-without-retry control stays `needs_review`. Business correctness remains `not_assessed`.

The controller separately owns the already-authorized read-only technical re-collection of the original native structure. That result may retain existing anomalies and `needs_review`. Neither the planner nor implementation/review agents replay the original task, canary/artifacts, or professional conclusions.

## Non-goals and scope boundary

- Only the supported Codex recovery-start proof changes. Ordinary event classification, general lifecycle collection, Claude behavior, exact reconnect recognition, terminal/final proof, selected checks, exit handling, stats, and diagnostic retention remain as they are.
- Do not change either runner, report keys/schema version, retry budgets, sandbox, configuration, provider/auth/routing, model cards, warning suppression, or installed live files.
- Do not create a general startup allowlist/validator framework, accept arbitrary error-like items, or strengthen unrelated post-start event handling. Existing acceptance of earlier messages within a started turn, post-start nonproof events, usage shapes, and trailing `rate_limit_event` is preserved.
- Read/write no caller workspace or business materials. Use only repository code and the three sanitized fixtures for delegated work. No original business dispatch, real provider request, forced network interruption, or live sync is part of validation.
- Future native envelope/text/path variants are maintenance work requiring evidence and separate authorization; do not implement speculative compatibility.

## First-principles judgment and direct evidence

The rejection comes from a start proof that treats adjacency as proof of no task activity before the turn. The minimum correction is to describe the one permitted intervening frame explicitly. All other recovery evidence remains necessary. A later successful terminal alone cannot establish that arbitrary preceding events belonged to the same supported lifecycle.

| Current code/evidence | Implication for this plan |
| --- | --- |
| [`recognized_codex_connection_notice`, lines 49–53](../../../scripts/agent-run-result.py#L49) checks exact keys and a full message match. | Leave reconnect recognition unchanged; use similarly exact shape/text matching for the startup frame. |
| [`Collection.__init__`, lines 153–162](../../../scripts/agent-run-result.py#L153) stores internal recovery proof separately from report data. | Add one internal gap counter here; no schema field. |
| [`Collection.codex`, lines 213–225](../../../scripts/agent-run-result.py#L213) records first start ordinals/shapes and total multiplicity. | Preserve these checks and the first-event thread proof. |
| [`Collection.codex`, lines 248–281](../../../scripts/agent-run-result.py#L248), especially 276–279, records non-benign completed error items as anomalies via `note`. | The supported startup item remains an anomaly with its original item text and source line. Recognition must not return early or alter this branch. |
| [`codex_connection_recovery_failure`, lines 285–302](../../../scripts/agent-run-result.py#L285) requires ordinals 1/2, then notice placement, completed terminal/final shapes and order, zero exits, and no validation errors. | Replace only the fixed turn ordinal with a bounded, fully accounted-for gap. Keep all subsequent fences and failure reason strings. |
| [`collect`, lines 385–398](../../../scripts/agent-run-result.py#L385) counts only parsed event objects; blank lines are skipped, malformed rows generate errors. | Count recognized gap frames among parsed events; preserve physical diagnostic lines and parser errors. |
| [`collect`, lines 407–479](../../../scripts/agent-run-result.py#L407) evaluates saved final, canary/artifact checks, stderr and exits before finalizing connection notices. | Preserve this order: startup recognition cannot bypass selected-check failures or nonzero exits. |
| [`collect`, lines 480–492](../../../scripts/agent-run-result.py#L480) derives status from errors/anomalies and copies stats/report fields. | A supported startup anomaly still yields `needs_review`; do not normalize statistics or alter report serialization. |
| [`RunnerResults`, lines 55–113](../../../tests/test_agent_run_results.py#L55) supplies fake runtimes, collector replay, report-contract and connection-result assertions. | Extend these deterministic tools; no new provider/test infrastructure. |
| [Baseline reproduction](evidence/baseline-reproduction.json) and its three fixtures isolate the inter-start warning. | The exact diagnostic at ordinal 2 is the only newly supported gap frame. |

Planner verification used the current collector, `python3 -B`, native/pre-collection runner inputs 0, empty stderr (`/dev/null`), and wall-clock input `2698.161843`. All three sanitized replays reproduced the recorded results:

| Fixture | Collector exit / runner report | Validation | Diagnostic totals (errors/anomalies/warnings) |
| --- | --- | --- | --- |
| `startup-warning-recovered.jsonl` | 1 / 1 | `rejected` | 1 / 1 / 0; recovery failure `start multiplicity, shape or initial frame order` |
| `adjacent-starts-recovered.jsonl` | 0 / 0 | `passed` | 0 / 0 / 1 |
| `startup-warning-no-retry.jsonl` | 0 / 0 | `needs_review` | 0 / 1 / 0 |

Collector SHA256 matched the baseline: `0301f6dd9f589b7b705aa5e2f5033b573a2bfce23f0ae2ca23b40c374dab06e4`. All replays retained the fixture usage dictionary verbatim and the supplied wall clock. No original inputs were read, and no product test suite has been run by the planner.

## Affected files and ownership

| File | Exact allowed implementation scope |
| --- | --- |
| `scripts/agent-run-result.py` | One pure startup recognizer beside reconnect recognition; one internal counter initialized in `Collection`; gap bookkeeping at entry to `Collection.codex`; bounded gap condition in `codex_connection_recovery_failure`; short comments explaining proof-only recognition. |
| `tests/test_agent_run_results.py` | One diagnostic fixture builder, targeted startup/gap regression matrices, and scoped extensions of existing recovery/check/process/bounds/detail tests. Preserve existing assertions and fake runtime isolation. |
| `docs/gateflow/codex-recovery-startup-diagnostics/plan.md` | This plan and review-directed plan corrections only. |

The three JSONL fixtures and baseline JSON are read-only. Root-owned gate artifacts/state may be recorded by the controller under the existing work-unit directory; they are workflow evidence, not additional product modules or implementation slices. No README, runner, configuration, installer, other test module, or caller file is an implementation target.

## Recognition contract

Add pure helper `recognized_codex_startup_diagnostic(event)` returning a boolean. It must accept only this envelope:

```json
{"type":"item.completed","item":{"id":"<nonblank string>","type":"error","message":"<exact supported message>"}}
```

Require a dict with exactly `{"type", "item"}`, `type == "item.completed"`, a dict item with exactly `{"id", "type", "message"}`, `item.type == "error"`, string `id` with `bool(id.strip())`, and string message. Item IDs may vary; their actual value is not a recovery identity. Missing, extra, non-string, or blank IDs and all extra envelope/item fields fail recognition. Do not accept `item.started`, `item.updated`, top-level `error`, or a message-bearing item of any other kind.

The entire message must equal the following fixed prefix (shown as a Python string literal), followed by the permitted path and one literal final period:

```python
"Under-development features enabled: skip_host_skill_discovery. Under-development features are incomplete and may behave unpredictably. To suppress this warning, set `suppress_unstable_features_warning = true` in "
```

The prefix ends with exactly one space after `in`. The feature list is exactly `skip_host_skill_discovery`; case, wording, punctuation, spaces, suppression setting, and explanatory text are fixed. Do not trim, lowercase, use substring matching, or match only the beginning of the message. A prefix/suffix, newline, alternate feature list, or alternate warning text fails recognition. The embedded suppression instruction is recognized as text only; it authorizes no configuration change.

**Permitted path variation:** a lexical absolute POSIX path `/<directory>[/<directory>...]/config.toml`, with at least one directory component. Each directory is a nonempty sequence of ASCII letters, digits, `.`, `_`, or `-`, and is neither `.` nor `..`. The basename is exactly `config.toml`. Examples supported by this grammar are `/tmp/synthetic-codex/config.toml`, `/home/synthetic/.codex/config.toml`, and `/Users/synthetic/.codex/agent-homes/profile_1/config.toml`. These are synthetic strings, not paths to inspect.

Relative/tilde paths, root-only `/config.toml`, doubled slashes, dot/traversal components, backslashes, quotes/backticks, whitespace/control characters, non-ASCII directory characters, different basenames/case/extensions, URLs, and extra text following the final period are unsupported. Paths need not exist; do not open, resolve, normalize, or compare them to current environment/configuration. This permits ordinary directory/home changes without turning arbitrary warning prose into a recognized diagnostic.

Absolute configuration paths are dynamic diagnostic payload, not event identity. The confirmed goal authorizes the supported path variations above; restricting recognition to fixed observed directory families or an ephemeral workspace root would not satisfy it. The exact envelope, feature, complete explanatory/suppression text, lexical absolute `config.toml` grammar and no-traversal checks remain binding; arbitrary other frames or text remain unsupported.

Concrete matching algorithm: after the exact envelope/type checks, use `re.fullmatch(re.escape(prefix) + r"((?:/[A-Za-z0-9._-]+)+/config\.toml)\.", message)`. Reject when it fails or any captured directory component (`path.split("/")[1:-1]`) is `.` or `..`. Use `fullmatch`, not a `$` anchor that could tolerate a terminal newline. This is one narrow helper, not configurable recognition machinery.

## Recovery state, call path, and proof invariants

Add `self.startup_diagnostics_before_turn = 0` next to the existing Codex start-proof fields. At the entry of `codex(event, line)`, before ordinary kind dispatch, increment it once for that event **only if** `self.thread_starts == 1`, `self.turn_starts == 0`, and `recognized_codex_startup_diagnostic(event)` is true. Continue through ordinary dispatch unconditionally. It is not reset on later/duplicate lifecycle events, not based on retained diagnostic arrays, and not emitted in the report.

Replace only `self.turn_start_ordinal != 2` in the first recovery fence with:

```python
self.startup_diagnostics_before_turn not in (0, 1)
or self.turn_start_ordinal != 2 + self.startup_diagnostics_before_turn
```

Keep this inside the existing short-circuit rejection expression alongside unchanged start multiplicity, valid start shapes, `thread_start_ordinal == 1`, and thread-before-turn line order. Missing start ordinals must still short-circuit via multiplicity/shape checks before comparisons. Preserve the existing start-failure reason. Do not merely change the ordinal to `>= 2` or subtract all diagnostic/item events from event totals.

For a valid recovery proof, the prefix of parsed events therefore has exactly one of these two shapes:

```text
thread.started, turn.started
thread.started, supported startup diagnostic, turn.started
```

The first shape has counter 0 and turn ordinal 2. The second has counter 1 and turn ordinal 3. Because `self.events` counts every parsed frame, any unsupported inter-start frame consumes an ordinal without increasing the allowed count; equality fails. Two supported diagnostics increase the count to 2, outside the permitted set. A malformed row may not consume an ordinal, but its existing collector error still defeats recovery. Blank physical lines remain ignored; they may shift diagnostic line numbers but never prove an extra event.

| Placement/count case | Required behavior |
| --- | --- |
| Supported diagnostic before thread start | Thread is no longer the first event; recovery fails, even if the later gap is supported. |
| One supported diagnostic between the sole starts | Accounts for exactly one gap frame; original anomaly is retained. |
| Two or more supported gap diagnostics, same or different IDs/paths | Recovery fails; keep all anomaly totals under existing display limits. No deduplication. |
| Unsupported warning/envelope/path, unknown event, rate-limit frame, benign metadata warning, reconnect, execution/tool/file/message frame in gap | Does not count as permitted startup proof; recovery fails. Ordinary classification of each frame remains unchanged. |
| Supported gap warning plus any unsupported frame, in either order | Recovery fails; the warning cannot hide the other ordinal. |
| Duplicate/malformed/reversed/missing thread or turn starts anywhere | Existing multiplicity, shape, first-event and ordering proof still fails. |
| Supported diagnostic after turn start | No gap credit; retain ordinary anomaly behavior. It does not invalidate an otherwise supported recovery solely by being an anomaly, or create a new general post-start fence. |
| Supported diagnostic after terminal | Existing post-terminal error rejects; no exception. |

After the start fence, leave all existing requirements unchanged: notices occur strictly after turn start; one supported successful terminal; final item shape/nonblank text and ID; last notice before final before completion; native/pre-collection exits zero; no other collector validation errors. Do not add usage requirements: existing omitted/non-dict usage behavior is deliberately unchanged. Collection and selected checks still finish before notices are classified, and anomalies still result in `needs_review` rather than automatic rejection.

## One minimal behavioral slice

**S1 — account for the supported startup gap while retaining recovery fences.**

- Objective/outcome: the six-event sanitized recovered case becomes `completed` / `turn.completed` / `needs_review` with runner exit 0, original anomaly and recovered warning; all unsupported gaps and existing failure proofs remain rejected.
- Allowed files: only the collector and test file listed above; this plan may be corrected through controller-owned plan review. No further product slice is planned.
- Prerequisites: controller acceptance of this plan after independent plan review/fix/re-review, existing work branch and baseline files intact. No native/provider access dependency.
- Changes: implement the exact helper, internal counter and ordinal equality described above; add the behavioral tests below using current fake runners/direct collector. No early return from diagnostic handling, public report change, collector-wide refactor, or auxiliary framework.
- Data flow: strict JSON parsing → parsed event ordinal → Codex proof counter/start bookkeeping → existing anomaly/tool/final/terminal handling → existing optional checks/stderr/exits → unchanged notice finalization using the amended start fence → unchanged report/status calculation.
- Errors/invariants/non-goals: exactly the recognition and proof rules above; no expanded warning downgrade and no new fatal classification outside recovery.
- Validation/completion: all specified synthetic assertions and the full result test module pass, whitespace check passes, raw input/diagnostic/stat preservation is evidenced, and no unsupported behavior/files were changed. Controller then performs code review/fix/re-review and the existing subsequent gates.
- Stop condition: any ambiguity or failure requiring a different recognition contract, broader validator change, changed acceptance semantics, unexpected file ownership, or unavailable validation must be returned to the controller before expanding S1.

One slice is appropriate because recognition plus gap proof is a single observable behavior and neither part independently solves the bug. Splitting by helper/bookkeeping/tests would incur gates without an independently useful increment. This is the minimum change: one exact predicate, one counter, and one bounded equality preserve the original proof while accepting the evidenced ordinal 1/3 prefix. There is no event registry, whole-stream buffering, generalized state machine, warning suppression, or future-format work.

## Tests and exact expected assertions

Use `RunnerResults` and its current fake runtime/temporary-file harness. Add `startup_diagnostic(path='/tmp/synthetic-codex/config.toml', identity='startup-warning')` returning the exact event above. Build gap variants by inserting that event at index 1 of `recovered_codex()`; leave existing no-gap tests intact. Reuse `assert_report_contract` and `assert_connection_result(..., recovered=True, status='needs_review')` for supported-gap successes. Keep physical line/count assertions explicit; do not mechanically reuse hardcoded adjacent-case line numbers for gap cases.

### 1. Reproduction, accepted paths, diagnostics, and stats

Add `test_codex_startup_diagnostic_recovery_and_controls`. Read all three committed work-unit fixtures as JSONL (do not rewrite them). Direct collector replay with native/pre-collection inputs 0 and wall clock `2698.161843` must assert:

| Fixture | Expected result after S1 |
| --- | --- |
| Startup warning + reconnect | exit 0; runtime/runner 0; completed/turn.completed; `needs_review`; events 6; errors `[]`; counts `{errors:0, anomalies:1, warnings:1}`; startup anomaly output line 2; recovered warning output line 4. |
| Adjacent starts + reconnect | Existing exit 0 / `passed`; events 5; counts `0/0/1`; recovered warning output line 3. |
| Startup warning without retry | Existing exit 0 / `needs_review`; events 5; counts `0/1/0`; same startup anomaly output line 2; no recovery warning. |

For all three assert schema/key set unchanged, `result_status='not_assessed'`, final `OK`, final chars 2, no final truncation, session `synthetic-thread`, tool results 0, runtime metrics `{}`, canary `not_run`, artifacts `[]`, diagnostic truncation false, verbatim fixture usage (including zeros and large input/cache values), exact supplied wall clock, and raw retained output equal to serialized input. Assert the startup diagnostic dictionary equals the existing representation: `message == str(event['item'])`, full `message_chars`, `stream='output'`, physical line 2, `path/proof_line=None`, `truncated=False`. Do not assert that its text vanishes or is downgraded to warnings.

In the same test add an explicit `supported-gap-with-expected-command-failure` regression case through the public fake Codex runner, with empty stderr and native exit 0. Build `recovered_codex(text='OK')`, insert exactly one supported startup diagnostic at index 1, then insert at index 3 an ordinary expected no-match command result: `{'type':'item.completed','item':{'id':'tool','type':'command_execution','command':'rg no-match','exit_code':1,'status':'completed','aggregated_output':''}}`. Run with `self.run_agent('codex', events, exit_code=0, err='', final='OK')` so the fake saved final agrees with the event final. The seven physical lines are `thread.started`, supported startup diagnostic, `turn.started`, failed `command_execution`, the exact attempt-1 reconnect notice, valid final `OK`, and successful `turn.completed`. The tool failure occurs after `turn.started`; it is an ordinary retained anomaly, not an inter-start exemption or a native process failure.

Use `assert_report_contract` and `assert_connection_result(..., recovered=True, status='needs_review')`; assert public/runner/runtime exits 0, `agent_status='completed'`, `terminal='turn.completed'`, `validation_status='needs_review'`, errors `[]`, exact counts `{errors:0, anomalies:2, warnings:1}`, events 7 and tool results 1. Assert both anomaly dictionaries preserve `message == str(the corresponding event['item'])`, full `message_chars`, `stream='output'`, physical lines 2 (startup) and 4 (tool), `path/proof_line=None` and `truncated=False`. The sole warning must retain `Recovered Codex connection notice: ` plus the exact reconnect message at output line 5, with its full text/length and untruncated metadata; there must be no recovery rejection. Retain final `OK`/chars 2, `result_status='not_assessed'`, schema, usage and exact raw output assertions. Keep the existing adjacent-start and startup-without-retry controls unchanged. This combined case verifies the already-confirmed preservation signal; it adds no product scope or recognition criterion.

Also exercise accepted path examples and nonblank ID changes through the public fake Codex runner. Assert runner wall clock finite/nonnegative, unchanged final/usage/raw output/stderr/saved-final fields. Cover supported reconnect attempts 1–5 and multiple reconnect notices with one startup gap; recovered warning counts/locations must equal the actual notice frames, while the startup anomaly count stays 1.

### 2. Exact recognition rejection matrix

Add `test_codex_startup_diagnostic_lookalikes_do_not_bridge_gap`. Each variant replaces the single gap frame in an otherwise successful recovered stream. Assert exit 1, `rejected`, no recovered warnings, and a reconnect rejection citing the existing start-failure reason. Retain ordinary diagnostic handling rather than asserting every lookalike itself is fatal. Cover:

- Text prefix/suffix; leading/trailing whitespace; final newline; case change; omitted explanatory/suppression text; changed punctuation/setting; another feature, a multi-feature list and a longer feature-name lookalike; nonstring/null/list/missing message.
- Missing/blank/whitespace/nonstring ID; missing item/type; list/null item; alternate item type; `item.started`/`item.updated`; top-level error with the exact warning message.
- Extra top-level and item fields, independently: `metadata`, `status`, `error`, `code`; use `error=None` too, so even apparently inert extras cannot qualify.
- Relative, tilde, root-only, doubled-slash, `/./`, `/../`, empty directory, whitespace/tab/newline/backtick/quoted/non-ASCII directory, Windows/URL paths, wrong filename/case/extension, missing final period, trailing text/newline, and a path embedded in otherwise unknown text.

Include a no-retry paired control for a representative unsupported item warning: it stays its ordinary anomaly/`needs_review` with exit 0. A top-level unknown error remains fatal. This checks that recovery failure is not implemented by globally hardening ordinary diagnostics.

### 3. Gap order/count and arbitrary-frame exclusion

Add `test_codex_startup_diagnostic_gap_order_and_count`. Assert start recovery failure for unknown future events (including an otherwise ignored kind), `rate_limit_event`, benign metadata error items, command/MCP/file execution items (started and completed), agent-message items, unknown error items, and top-level unknown/reconnect errors in the gap. Cover an unsupported frame alone and before/after the one supported diagnostic. Assert supported-diagnostic counts 0/1 accept only the two specified prefixes; counts 2 and 25 reject, with same IDs and distinct IDs/accepted paths. For count 25 retain anomaly total 25, display length 20, `diagnostics_truncated=True`, and the connection error; display truncation never grants gap credit.

Cover supported diagnostic before thread; missing/malformed/duplicate/reversed starts with a supported gap; duplicate starts before and after turn; supported diagnostic after turn (ordinary anomaly, recovered reconnect if all other fences pass); and after terminal (existing rejection). Add blank physical lines before/between prefix frames: allowed parsed-event sequence stays accepted and diagnostic physical lines shift correctly. Add parser-corrupt rows in the gap (invalid JSON, duplicate key, invalid number, escaped lone surrogate, non-object); rejection must retain an `invalid event:` diagnostic even if the parsed-event gap otherwise qualifies.

### 4. Other recovery fences and selected checks with a valid gap

Add `test_codex_startup_diagnostic_keeps_recovery_fences` for unknown top-level errors after start, unrecovered/unknown disconnect wording, missing/failed/duplicate/conflicting/extra-field terminals, missing/blank/nonstring/extra-field finals, final before last notice/after terminal, notice after terminal, and saved-final mismatch. Assert existing rejection/category/reason behavior with no recovered warning. Retain original tests of these same fences for adjacent starts.

Extend the existing selected-check and process-failure coverage with the single valid gap (keep adjacent cases). Synthetic check success uses only `self.canary`, `self.expected`, a new fake-runtime artifact, and a recorded successful tool read **after turn start**. Assert matching canary, read candidate true, regular artifact fields, tool count 1, runner/runtime 0, original startup anomaly, recovered notice warning, and `needs_review`. Mismatched/missing proof, unreadable expected input, missing/nonregular/log-alias/hard-linked artifact, missing/stale saved final, and prelaunch selected-check rejection retain existing errors and do not become recovered successes. Native exit 7 stays public exit 7 and failed/rejected; pre-collection exit 1 with native 0 stays failed/rejected. Keep all runner postprocessing failure modes. Direct collector replay must use **pre-collection** input exit, never its own prior rejection output.

Extend diagnostic-bounds coverage to a valid startup gap with >20 reconnect notices and existing saturated categories: total counts remain authoritative, the startup anomaly stays visible, notice locations/category and current reservation behavior persist. Do not copy retention-limited arrays into proof state. Extend fake-runner `--detail` coverage with the startup frame: exact raw JSONL/stderr and native exit behavior remain unchanged, no report/classification inserted.

Run the full result test module to cover ordinary Codex, Claude fatal errors/success/metrics, report schema, terminal stats, tool anomalies, detail mode, and temporary installed-adapter behavior. That harness uses fake runtime functions; it does not call real providers or deploy live tools.

### Commands and evidence ownership

From repository root after implementation, run the focused new behavior first:

```sh
python3 -B tests/test_agent_run_results.py RunnerResults.test_codex_startup_diagnostic_recovery_and_controls RunnerResults.test_codex_startup_diagnostic_lookalikes_do_not_bridge_gap RunnerResults.test_codex_startup_diagnostic_gap_order_and_count RunnerResults.test_codex_startup_diagnostic_keeps_recovery_fences -v
python3 -B tests/test_agent_run_results.py -v
git diff --check
```

Expected: every specified test passes and whitespace check exits 0. Do not run unrelated provider suites. If a harness/environment failure prevents a required assertion, record the actual failure and stop at the controller rather than weaken an assertion. Record exit codes, assertion coverage and fixture hashes in the implementation artifact; no business text.

Sanitized direct replay command (repeat with each of the three fixture filenames; before implementation the recovered-warning fixture intentionally exits 1):

```sh
python3 -B scripts/agent-run-result.py --runtime codex --provider mimo --output docs/gateflow/codex-recovery-startup-diagnostics/evidence/startup-warning-recovered.jsonl --stderr /dev/null --exit-code 0 --runner-exit-code 0 --wall-clock-seconds 2698.161843
```

Controller-only original structural replay is the remaining goal signal: re-collect the already-authorized original input with actual native/pre-collection exits 0, preserve its hashes/text/locations/counts/raw usage/time, and verify removal of the one reconnect rejection with all original anomalies retained. Input paths and contents need not be copied into delegated artifacts. Do not replay original selected checks or claim their acceptance. This is a technical collection comparison, not execution of the business task.

## Docs decision

No product documentation edit is necessary. `README.md:389–419` and `README.zh.md:363–387` already describe valid recovered retry notices, retained anomalies/needs_review, raw stats and selected checks accurately. There is no new flag, configuration advice, report field, or operator action. The exact supported diagnostic/path/count policy belongs in the helper comments, tests, this plan and gate evidence. Do not add warning-suppression guidance. Controller artifacts must report this explicit no-README-change decision.

## Goal alignment and absence of scope drift

| Decision/slice/validation | Binding goal signal / necessary invariant |
| --- | --- |
| Exact shape/text/path helper; one bounded gap counter; S1 | Correct the evidenced ordinal 1/3 false rejection; goal signals 1 and 3. |
| First-event thread, unique valid starts, equality covering every gap frame; count/order/near-match tests | Prevent arbitrary/execution/unknown frames or duplicates from bridging startup; signal 3. |
| Unchanged diagnostic dispatch, stats/schema, bounds and raw-stream assertions | Keep original evidence/locations/totals/time/usage; signals 2 and 4. |
| Unchanged terminal/final/exit/check evaluation with synthetic failure tests | Recovery remains proof of successful same execution; signals 2 and 3. |
| Three controls, full deterministic result module, detail/Claude checks | Preserve adjacent, ordinary and Claude behavior; signal 4. |
| Root-owned original structural replay and independent gate evidence | Technical original reproduction and reviewed completion; signals 1 and 5. |
| No README/runtime/config change, no original business acceptance | Confirmed non-goals and caller evidence boundary. |

Every planned product change belongs to S1 and the confirmed defect. Potential changes to general event validation, post-start item semantics or native format compatibility are not requirements, additional slices, or grounds for quietly broadening this plan.

## Residual risks, uncovered areas, and owners

| Risk / uncovered area | Gateflow classification | Owner / destination / disposition |
| --- | --- | --- |
| Recognizer overmatches or gap accounting silently admits arbitrary frames | `fixed in current slice` (planned; not yet verified) | S1 implementer; controller requires adversarial tests and independent review evidence before acceptance. |
| Actual original path/envelope not covered by the specified policy | `requiring new issue or explicit user decision` if observed | Root controller reports its pre-implementation structural check confirmed the actual envelope/path matches this unchanged grammar. No original evidence was read by the plan fixer. Root owns post-implementation technical replay and any conflicting evidence; do not broaden matching without goal-aligned adjudication. |
| Future warnings, extra native fields, multi-warning starts, Unicode/space-containing config directories or other unsupported formats remain rejected when placed in the inter-start gap | `assigned to later work unit` | Collector maintenance owner via root controller; later evidence-backed compatibility work. Intentional supported-format boundary, nonblocking now; no future slice here. |
| Business correctness and original canary/artifact/professional acceptance are unverified | `assigned to later work unit` | Caller/business controller; caller-owned validation outside this work unit, explicitly authorized as uncovered. Technical `needs_review`/`not_assessed` is acceptable here. |
| Live network interruption and deployment/restoration are not exercised | `assigned to later work unit` | User/deployment controller; native structural replay plus deterministic fixtures prove this parser defect. Merge/live sync requires separate authorization. |

No blocking design question remains with the sanitized evidence. Required product implementation, independent review and controller technical replay are pending work, not completed validation. No residual is assigned to a nonexistent later slice or treated as a reason to expand S1.

## Explicit stop conditions and controller handoff

Stop and report to the root controller if the existing work branch/ownership differs; inputs are missing/changed; a required validation cannot run; a new finding changes the confirmed goal, accepted envelope/path/count, report/public contract or ordinary semantics; original structural comparison disproves the proposed support policy; or an accepted finding cannot be fixed inside S1. Do not relax matching/fences, touch extra files, read prohibited inputs, dispatch real tasks, or deploy live tools to get a pass. Unsupported future formats alone are classified maintenance follow-ups, not a current validation requirement.

Planner completion means this artifact exists with code evidence, exact decisions, one slice, assertions, docs decision and classified ownership. Next entry belongs to the root controller: independent `plan review` and any required fix/re-review, followed by the already-authorized Gateflow chain. Only the root controller performs dispatch, finding adjudication, commits, push, draft PR and state transitions. Nothing in this plan authorizes merge, live sync, external messaging or caller changes.

Implementation/review completion reports must contain: gate/work-unit/slice and artifact path; exact changed/reviewed files; decisions and finding dispositions with evidence; commands/exit codes and key observed assertions; original-diagnostic/raw-stat/selected-check preservation; docs decision; classified residual risks with owners/destinations; completion status and next entry. Controller closeout additionally records the original technical replay outcome, review/re-review status, scoped commit/PR evidence and deployment limits. Distinguish `completed/needs_review` technical success from business acceptance; never claim unperformed original checks passed.
