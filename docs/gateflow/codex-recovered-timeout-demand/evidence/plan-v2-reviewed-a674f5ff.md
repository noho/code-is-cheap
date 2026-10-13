# Plan v2: native terminal completion for both public runners

## Artifact identity and gate decision

- Gate: revised plan; work unit: `codex-recovered-timeout-demand`.
- Branch: `fix/codex-recovered-timeout-demand`; source/base HEAD inspected: `62c3b26adeb994e81043d7b1afbcd4c6eb8974ae`.
- Binding scope: [goal-confirmation-v2.md](goal-confirmation-v2.md), confirmed by explicit user redirect. Its SHA-256 at planning time is `a68fd2c4dbc3be7e7cefb943eceff4434f40b2352b25a4083948f2c2001b49b6`.
- Design document alignment: no separate design document; the confirmed v2 goal and saved native protocol evidence are the design inputs.
- Decision: one implementation slice, ready for revised plan review; implementation has not started. This plan does not approve itself or claim a review pass.
- Artifact: `docs/gateflow/codex-recovered-timeout-demand/plan-v2.md`.
- Ownership of this delegation: write this plan only. Controller owns state, delegation, independent reviews, adjudication, accepted commits, draft PR, deployment and probes. No production/test mutation, delegation, commit, push or deployment was performed here.
- Next entry point: **revised plan review**, using `planreview`, against this file and the v2 goal. V1 plan/reviews are superseded acceptance inputs. Leave `goal-confirmation.md`, `plan.md`, old review files and state untouched.

## Goal, motivation and success signals

Determine call completion from the runtime's final execution state. A collected call succeeds when native process exit and necessary postprocessing exit are zero, exactly one valid successful terminal belongs to this execution, its final answer is complete and nonempty, the log is intact, and explicitly selected checks pass. Intermediate diagnostic wording must never determine eligibility for success. Preserve diagnostic evidence and caller-owned judgment; `result_status` stays `not_assessed`.

The current false rejection is caused by both adapters making unfamiliar top-level `error` messages fatal. Codex additionally conditions its completion proof on two notice regexes and one startup-message regex. Claude has the opposite false-acceptance case: its native result can say `subtype=success/is_error=false/terminal_reason=completed` while `stop_reason=content_filter`. Both problems belong to the same behavioral change: separate execution completion proof from intermediate diagnostics.

Success signals, named for the alignment table below:

- **S1 — completion and retention:** controller-only original-log replay returns `0/needs_review`, with all five notices and three existing anomalies retained, selected checks preserved, unchanged originals, and `result_status=not_assessed`. V1 category counts do not bind v2.
- **S2 — wording independence:** previously recognized and arbitrarily novel structurally valid intermediate diagnostics in both runtimes return `0/needs_review` after valid completion; bounded reports and full logs retain them.
- **S3 — rejection fences:** process/postprocessing failure, failed/missing/conflicting/invalid terminal, different-execution completion, parse damage, missing/incomplete final or failed selected check returns nonzero. Claude native negative completion metadata overrides a nominal success subtype.
- **S4 — public behavior:** report shape, raw/detail output, statistics, tool anomalies, artifact/canary checks and caller-owned task correctness remain supported and documented.
- **S5 — review and delivery:** new-goal independent plan/code/aggregate/actual-PR review gates and accepted commits precede a new draft PR; controller performs adjudication and fixes without merge or external comments.
- **S6 — installed validation:** controller syncs approved relevant components, records installed equality/runtime versions, and runs separate Codex and Claude `mimo-flash` three-step synthetic live probes with actual tool/completion/result records.

## Non-goals and boundaries

No retry engine, automatic business rerun, business acceptance, error-text inventory, hidden diagnostic suppression, new framework, generic event-schema library, full reconstruction of nested agent conversations or global item/UUID ledger. No provider/profile/shim change or CLI/report schema version change. Do not classify final prose as refusal, truncation or task correctness.

No delegate reads original portfolio-manager-v2 evidence or any business data. Only the controller replays original inputs read-only. Committed fixtures contain synthetic protocol records, not business content. Unrelated risks do not become extra slices or new acceptance conditions.

## First-principles judgment and direct source evidence

One fresh runner invocation produces a private raw stream, waits for the actual runtime exit, then invokes the existing collector. Completion can therefore be proved by validating that invocation's native terminal and final ownership; text matching of a preceding diagnostic adds no reliable completion evidence. A failed final execution, structural damage or failed selected check cannot be recovered merely by finding a success-looking string or event.

The inspected relevant sources are unchanged from the base commit and are retrievable there:

| Source | Direct evidence and consequence |
| --- | --- |
| `scripts/agent-run-result.py:49-82` | Connection/startup recognition uses exact message regexes. Remove their acceptance role and the dependent proof queue/bookkeeping. |
| `scripts/agent-run-result.py:239-368` | Codex currently records completion/final shape but enforces it only in `codex_connection_recovery_failure()`. Make the necessary execution/final proof unconditional. |
| `scripts/agent-run-result.py:370-426` | Claude selects success from subtype/boolean, allows assistant text to populate final, and treats every top-level error as fatal. Validate native completion metadata and make root result own accepted final. |
| `scripts/agent-run-result.py:428-520` | Strict JSON/UTF-8 parsing, duplicate-key/nonfinite/surrogate rejection, post-terminal fence, selected checks, diagnostics, statistics and process exits already exist. Preserve their decisive roles and report layout. |
| `scripts/codex-agent-run:503-552` | Records native exit separately from final-message postprocessing; passes both to collector; preserves an existing nonzero exit over collector exit. No runner redesign is needed. |
| `scripts/claude-agent-run:440-458` | Waits for native exit, passes it to collector and retains it over collection rejection. No runner redesign is needed. |
| `tests/test_agent_run_results.py` | 61 test methods, deterministic fake runtimes and a direct collector harness. Many tests bind old wording, startup-gap limits, category counts or asymmetric proof behavior and must be revised. Parse/check/process/statistics/detail assertions still apply. |
| `README.md:374-421`; `skills/sub-agents/SKILL.md:57-98` | Both currently claim unfamiliar Codex diagnostics are fatal. Replace that contract with native completion and retained diagnostics. |

Protocol evidence is saved under [evidence/protocol/](evidence/protocol/): `codex-native-events.rs`, `codex-items.ts`, `claude-sdk-excerpts.txt`, `observed-terminal-fields.json`, `sources.json`. Codex snapshot is native `0.162.1`; prefer the Rust event definitions when the TypeScript item union omits newer variants. Claude SDK `0.2.138` is local schema evidence, **not** an exact match claim for CLI `2.1.296`; observed CLI fields provide the `end_turn` and `content_filter` examples. Do not retrieve the raw logs referenced by sanitized observations or old reviewer/business outputs.

The 61-method count was checked by AST inspection, not by rerunning tests. No full baseline rerun is needed for this planning delegation. Prior baseline pass evidence may support only unchanged assertions after the controller verifies its command, version and retrievable source; it cannot approve the changed v2 expectations or substitute for post-implementation validation.

## Affected files and ownership

| File/module | Planned change |
| --- | --- |
| `scripts/agent-run-result.py` | Existing `Collection` adapters and finalization: general completion proof, diagnostic/structural separation, Claude final metadata and ownership. Small local helpers/state are permitted; no new parser architecture. |
| `tests/test_agent_run_results.py` | Revise old-contract expectations/helpers and add synthetic positive/negative protocol matrices through the existing fake runners/collector. Prefer inline/generated synthetic fixtures. |
| `README.md` | Replace exact-notice acceptance documentation; describe native failure/completeness, `needs_review`, final text visibility and caller-owned correctness. |
| `skills/sub-agents/SKILL.md` | Same generic result semantics; remove unknown-text-fatal claim without adding task-specific workflow ceremony. |
| Both public runner scripts | Read/validate exit and collection integration; **no change expected**. A change is allowed only if review demonstrates one is necessary for this contract, with evidence and affected integration tests recorded by controller. |
| Gateflow artifacts | Controller separately writes implementation/review/closeout artifacts. This delegated plan does not edit state or v1 artifacts. |

## Contracts and implementation-ready decisions

### Shared parsing, states and precedence

Keep the existing sequential collector. Distinguish hard validation errors from structurally valid intermediate diagnostics as records arrive. No later terminal clears a hard error. State transitions are `before execution -> active -> one terminal -> trailing metadata only`; any duplicate terminal makes the result conflicting, including two identical successes or failure followed by success. Malformed terminal-shaped frames must still leave hard rejection evidence; they cannot silently vanish and permit a later terminal to rescue the log.

Preserve strict UTF-8/JSON reading, duplicate-key rejection, object/type validation, finite-number checks, valid Unicode and source line numbers. Blank physical lines remain ignored. Parsed unfamiliar nonterminal event kinds during an active execution retain existing non-proof handling; they never manufacture completion. This is not a schema validator for every tool or future telemetry event. Recognized proof/diagnostic envelopes have the required-field validation below.

After a terminal, preserve the existing `rate_limit_event` metadata exception, subject to strict parsing. It cannot alter final, terminal, session identity or terminal statistics. Every other output event after a terminal, including diagnostics, assistant text, starts, tools and further results, rejects. Do not broaden the trailing-event exception based on message wording. Stderr remains separately retained/classified and is not a second execution stream.

Native failure and necessary postprocessing failure remain decisive; the public runner preserves its existing exact nonzero process/postprocessing code. With both zero, mechanical rejection returns `1`; accepted `passed` or `needs_review` returns `0`. Keep schema version 1 and existing fields. `validation_status` is rejected if hard-error total is nonzero, otherwise needs_review if anomaly total is nonzero, otherwise passed. Intermediate diagnostics do not create a fourth status.

`terminal` reports the native terminal kind/outcome or `conflicting`; a nominal Claude success with a negative/malformed completion field is `failed`. `agent_status` remains an execution-completion indicator: completed requires zero native/postprocessing exits and valid same-execution successful terminal/final proof; failed otherwise. A separately failed selected check can still yield `agent_status=completed` with `validation_status=rejected`, preserving the distinction from task acceptance. Parse damage is always rejection even when native completion evidence/final text remains displayable. `result_status` is always not_assessed.

Retain readable final/partial text on rejection for diagnosis. It is not acceptable-final proof. Do not fall back to earlier text to turn a missing, blank or malformed authoritative final into success.

### Codex execution identity and final ownership

The native stream exposes a `thread_id` on `thread.started`, but no turn ID or per-agent-message refusal/finish-reason. Prove the execution from one ordered thread start and one ordered turn start in this runner log, not from invented fields:

1. Exactly one `thread.started`, first nonblank output event, with required `type` and nonblank string `thread_id`; exactly one `turn.started` after it. Supported proof envelope fields are `{type, thread_id}` and `{type}` respectively. Missing, malformed, duplicate/reversed starts or a different thread start reject, with `session_id=null` when identities conflict.
2. Between the two starts allow any number of structurally valid Codex diagnostic frames: top-level `error` and completed error items. No startup text/path/feature recognition, fixed diagnostic count or exact turn-start ordinal. Actual work/final items or unsupported pre-turn frames cannot serve as startup diagnostics.
3. In the active turn, keep ordinary existing item/tool handling. A completed agent message requires the native `{type, item}` envelope and `{id, type, text}` item, with nonblank string id, `type=agent_message` and string text. The last completed agent message before the terminal owns final; a blank latest final rejects even if an earlier message was nonempty. Multiple earlier completed messages are allowed. Invalid completed agent-message shape remains a structural error even if followed by a valid message.
4. Exactly one `turn.completed` after the started turn and a valid nonempty completed agent message proves success. Supported terminal envelope is `type` plus optional `usage`; no unrecognized completion-bearing fields are silently treated as success. A `turn.failed` rejects regardless of error text or a later success. Validate its native error payload as an object with a string `message`; malformed failed events also reject. Statistics still use the existing best-effort telemetry handling below.
5. Diagnostics before the final, or after the final but before `turn.completed`, do not require another agent message. The completed terminal confirms the turn ended; the protocol supplies no evidence that a diagnostic's position by itself truncates an already completed message. Accordingly v1 “final must follow the last notice” rejection is superseded. Final before `turn.started` or after the terminal still rejects.
6. Explicit `--last-message` continues to compare the saved complete text with event final as currently implemented; missing/unreadable/mismatched files and save failures remain hard failures.

Native Codex has no independent refusal/finish-reason field on completed `agent_message`. Do not add word heuristics or pretend completion proves the final text answers the user's business request. Preserve text, diagnostics and not_assessed. Unknown added proof-envelope fields reject as unsupported proof shape until evidence establishes their meaning; this does not reject arbitrary diagnostic text.

### Claude root identity, final selection and nested messages

The native execution terminal is `result`, not a streamed assistant text or individual API message stop:

1. A root frame has absent or null `parent_tool_use_id`; a nested assistant/user frame has a nonblank string parent tool ID. Other explicit values are malformed. Validate present session IDs as nonblank strings. All root pre-terminal frames that supply a session_id, including diagnostics, must agree; root identity conflicts reject and report session_id null. Different valid nested session IDs do not become root conflicts or supply root success.
2. Root `system/init` is optional for historical/minimal streams; when present it is unique and precedes root work/result. Missing historical root session IDs remain unavailable/null rather than fabricated or fatal: one fresh runner log and one root result bind execution when there is no conflicting identity. This preserves missing-session report behavior while rejecting explicit malformed/conflicting identity evidence. Do not require UUID format or persistence as proof of completion.
3. Exactly one root result owns accepted final through its own required string `result`, with nonempty trimmed content. It replaces any intermediate assistant text, including nested text. Missing, wrong-type or blank result rejects; earlier assistant text cannot rescue it. Retain earlier root text only as diagnostic/partial display when no readable result text exists, while keeping rejection. No assistant/final update after the terminal is allowed.
4. SDK evidence attaches `parent_tool_use_id` to assistant/user messages, not to `SDKResultMessage`. A result with an explicit nonnull parent is unsupported terminal structure and rejects; it cannot stand in for the root result or be counted as recovery. Do not invent a supported nested-result protocol. Absent/null parent on a result denotes the root for compatibility. Multiple root results conflict even if their session IDs or payloads match.
5. Keep assistant/user content-list and tool-pairing validation. Require dictionary blocks and correctly typed known text/tool identity fields. Scope the existing pending-tool map by parent context so identical nested/root tool IDs cannot consume each other's results; nested parent IDs must reference a recorded parent call. This is a small ownership correction within the current adapter, not a graph/state framework. Nested tool failures/errors remain anomalies; later root completion owns call outcome. Preserve tool counts/read evidence and unresolved-call anomalies.

### Claude native completion fields

Required completion proof is root `type=result`, `subtype=success`, literal boolean `is_error=false`, complete nonempty `result` and no explicit native negative completion field. Other subtypes, missing/wrong-type booleans or conflicting results reject. Optional or historical missing metadata is distinguished from a malformed explicit value:

| Result field | Accepted meaning | Rejection / diagnostic rule |
| --- | --- | --- |
| `stop_reason` | Absent or null: unavailable historical metadata. `end_turn`: observed normal completion. | Any other explicit string rejects as negative or unsupported completion; this includes the observed `content_filter`, truncation/refusal/context-limit reasons and `tool_use`/`pause_turn` at the **result**. Blank/nonstring values are malformed. No error-text regex. |
| `terminal_reason` | Absent: optional SDK field. Present `completed`: completion. | Null, blank/nonstring, unknown reason or every other declared TerminalReason rejects. The snapshot negatives are blocking_limit, rapid_refill_breaker, prompt_too_long, image_error, model_error, aborted_streaming, aborted_tools, stop_hook_prevented, hook_stopped, tool_deferred and max_turns. |
| `api_error_status` | Absent or null: no explicit final API error status. | Present nonboolean integer status is native final error evidence and rejects; other values are malformed and reject. Never override it with a success subtype. |
| `errors`, if carried on nominal success | Absent or empty list: no error entries. | Nonempty list rejects without inspecting strings for benign wording; wrong container/member type rejects. This prevents error-result payload evidence being ignored under a success label. |
| `deferred_tool_use`, if carried | Absent: no native deferred completion. | Present payload cannot prove ordinary completed work under the available schema excerpt and rejects as deferred/unsupported completion, including malformed null. `terminal_reason=tool_deferred` already rejects. No attempt to execute deferred tools. |

The saved evidence demonstrates positive `end_turn`, not another positive stop reason. In particular `stop_sequence` is an explicit unsupported result reason under this plan, pending native evidence in a later work unit; do not silently infer complete output from an unobserved reason. Absent/null stop metadata is intentionally compatible with existing minimal/historical results. These are protocol-value decisions within the confirmed goal, not diagnostic-text allowlists and not requests for renewed user confirmation.

Do not use intermediate assistant `message.stop_reason` (e.g. tool_use) as the overall execution terminal; it describes that API message. An assistant `error` or `system/api_retry` is an intermediate diagnostic and may be followed by a valid successful root result. Preserve native fields in the raw log/diagnostic rather than promoting every intermediate truncation/retry/error indication into final failure. Completion-field validation above applies to the authoritative result. Do not invent independent Codex fields or infer Claude refusal from final prose.

Only required completion/identity/structural fields affect acceptance; ancillary SDK/CLI metadata is not subjected to a new exhaustive SDK-version gate. Preserve unknown ancillary metadata in raw logs. A future changed terminal discriminator/reason or contradictory native completion field needs protocol evidence rather than an error-text addition.

### Valid diagnostics versus structural failure

| Frame | Valid diagnostic shape and handling |
| --- | --- |
| Codex or Claude top-level `error` | Required string `message`; preserve entire event and output line as anomaly regardless of text, punctuation, language, attempt text or extra ancillary fields. Missing/nonstring message is malformed and remains hard error. |
| Codex completed `item.type=error` | Required nonblank string item id and string message in an object item/envelope; preserve as anomaly regardless of startup feature/path/text. Diagnostic extensions do not manufacture completion. Malformed required fields remain hard errors. |
| Claude assistant envelope `error` | If present, nonempty string diagnostic code (known SDK examples or novel value); validate normal message/content envelope and preserve event as anomaly. It is not a result terminal. Missing error is ordinary assistant handling; explicit null/wrong type is malformed. |
| Claude `system/api_retry` | Required numeric attempt/max_retries/retry_delay_ms, string error and number-or-null error_status per saved schema. Integer counters must be nonboolean/nonnegative; delay/status types must be valid/finite. Validate supplied identity fields. Preserve event as anomaly; no configured attempt budget, exact code or wording conditions acceptance. Missing/wrong-type required payload is hard error. |
| Ordinary tools, pending calls, stderr | Keep existing anomaly/visibility and selected-proof behavior. Existing benign stderr warning classification may remain because it only affects presentation, never acceptance eligibility. No new benign-message inventory is needed. |

Record intermediate diagnostics as anomalies immediately, including on rejected calls. Hard failure evidence is separately recorded in errors; do not promote/demote whole diagnostic queues based on a recovery-text recognizer. Remove obsolete connection recognition/recovery helpers, first/last notice ordering checks and startup-text/count bookkeeping. Native item-error benign wording recognition is unnecessary for acceptance and can be replaced by uniform anomaly reporting. No diagnostic is discarded merely because final completion succeeds.

Use `note()` bounds directly: each category has total count, at most 20 displayed records, at most 2000 displayed characters each, original character count, truncation flag, stream and source line; raw logs retain all records. No new reserved-slot or category-count promise for old notice prefixes. Update tests that asserted queue eviction/prefix/category details to v2 bounded-retention semantics while retaining overflow/truncation/source assertions.

### Preserved statistics and selected checks

`usage`, Claude durations/cost/modelUsage and wall clock remain telemetry, not completion fields. Keep existing best-effort behavior: dictionary usage copied verbatim, missing/nonobject usage null, finite valid numeric metrics retained including zero, absent/invalid metrics omitted, no estimated or summed streaming totals. Even a failed unambiguous terminal can retain telemetry. Missing/conflicting terminals provide no trusted totals. Native usage schemas have more required members than older fixtures; do not widen this completion fix into metrics-schema enforcement.

Keep unchanged canary token parsing and proof source locations, candidate-read visibility, fresh regular artifact/log-alias/hard-link checks, prelaunch validation, final-message comparison, raw file retention and character truncation. Selected check failure is always rejection despite native successful completion and retained diagnostics. Missing tool visibility continues to produce needs_review rather than invented business failure. `--detail` continues to bypass collection/optional checks and preserve raw stdout/stderr/redirection and runtime exit.

## Goal alignment and one behavioral slice

| Decision / validation | Confirmed goal alignment |
| --- | --- |
| General Codex/Claude completion proof and separate diagnostic handling | S1, S2, S3: completion depends on native state, not intermediate words. |
| Claude result metadata, root identity/final ownership and nested tool scoping | S3: success-label negative evidence, wrong-execution completion and invalid final cannot pass. |
| Existing parser/check/exit fences; bounded diagnostics/statistics/detail | S2, S3, S4: retained diagnostics do not weaken mechanical failure or public behavior. |
| README/generic skill contract update | S4: caller understands completion, visibility and not_assessed. |
| Revised reviews, controller original replay, approved component sync and dual live probes | S1, S5, S6: evidence applies to v2 and to the delivered installed version. |

### Slice S-1 — terminal-driven completion with retained intermediate diagnostics

- **Objective/outcome:** both public collected runners implement the above completion predicate; structurally valid novel diagnostics return 0/needs_review after valid native completion, while negative/invalid/missing/conflicting completion and existing hard failures reject.
- **Prerequisites:** v2 goal confirmed; this revised plan and its independent review/adjudication accepted; same work branch/base verified. Old plan approval is insufficient.
- **Allowed files:** collector, existing test file, README and generic sub-agents SKILL listed above. Runner integration reads/checks required; source mutation only for an evidenced necessary adjustment adjudicated by controller.
- **Allowed scope:** existing adapter-local proof state and small validation helpers; result-owned Claude final and optional-field policy; bounded anomaly recording; corresponding synthetic regression/doc changes. No extra behavioral slice or unrelated cleanup.
- **Data flow/interfaces:** runtime streams -> existing strict parser -> runtime-specific execution/final proof and intermediate diagnostics -> existing selected checks/process checks -> unchanged schema 1 report/exit. Available native IDs establish ownership; no invented common finish-reason interface.
- **State/error invariants:** hard failures persist; terminal cardinality applies even without diagnostics; same-execution success never rescues a failed terminal or damaged frame; partial text may remain visible without proving success; final result metadata beats nominal subtype; result_status remains not_assessed.
- **Non-goals:** all boundaries above, including business replay by delegate, retries, deployment, task-specific skill ceremony and complete nested conversation reconstruction.
- **Validation/completion signal:** post-change synthetic runner/collector suite, appropriate syntax/diff checks and documented acceptance matrix below pass for the actual source version; docs match behavior; implementation artifact lists exact files/commands/results and no unclassified residual risks. Controller then enters slice code review, not directly PR or closeout.
- **Stop condition:** implementation discovers actual native evidence contradicting one of these proof/metadata rules or a necessary change outside approved scope. Report the evidence to controller for adjudication; do not invent user tradeoffs, broaden scope or silently add compatibility. Ordinary local code choices and diagnostic wording are not stop conditions.

This is one verifiable behavior increment. Splitting by runtime, tests or documentation would add gates without producing a separately useful accepted public contract. The existing collector is sufficient; no framework, retry mechanism or future slice is required. Every planned change maps to confirmed completion/retention or a necessary ownership/structure fence, so the plan does not drift into business correctness or generic hardening.

## Validation commands and expected assertions

Implementation runs from the repository checkout, records source version/hash and actual results:

```bash
python3 -B -m unittest discover -s tests -p 'test_agent_run_results.py' -v
zsh -n scripts/codex-agent-run scripts/claude-agent-run
git diff --check
```

Use the current fake-runtime harness; make the direct collector helper support both runtimes for necessary native/postprocessing/structural cases. A single full affected-suite run after behavior changes is justified; do not repeatedly rerun the unchanged baseline or replay the same suite at every review. Rerun affected cases after fixes, broadening only for real change impact/counterexamples. The sync-install test already exercises installation in temporary targets, not live deployment. No new production task is needed to validate this slice.

The matrix is required coverage; cases can share table-driven fixtures. Preserve still-applicable assertions from the 61 existing tests rather than requiring that obsolete expectations pass.

| Matrix | Required assertions |
| --- | --- |
| Ordinary success, both runtimes | Native/postprocessing 0 + valid unique successful terminal + nonempty final + intact stream/checks => report/outer exit 0, completed, passed, not_assessed. Clean minimal Claude absent stop/terminal metadata stays supported. |
| Novel diagnostic recovery, both | Arbitrary new phrases, changed reconnect attempts/UUIDs, Unicode/multiline/empty string messages, old notice variants, multiple unknown errors => 0/needs_review; every diagnostic counted once with raw content/source; no text rule added. Mix valid and novel diagnostics with ordinary failed tools/stderr. |
| Codex startup/order | Zero/one/many arbitrary valid diagnostic frames between starts accepted without feature/path/count dependency. Diagnostics after final but before terminal accepted. Missing/duplicate/reversed/malformed starts, invalid thread id, work before turn, final outside turn and concatenated executions reject, with/without diagnostics. |
| Codex final/terminal | Last of several completed agent messages selected; invalid/blank latest cannot fall back. Missing id/text, wrong type/envelope, unsupported proof fields, missing/failed/duplicate/conflicting terminal and final after terminal reject, including clean streams. Refusal-like or incomplete-sounding prose with valid native fields is delivered without word classification. |
| Claude native metadata | Observed success/content_filter/completed rejects; observed success/end_turn/completed accepts. Exercise every declared negative terminal reason, native refusal/truncation/context/tool/pause reasons, unknown/blank reasons, wrong-type/null terminal_reason, error api status/malformed status, errors entries/malformed list and deferred payload. Success subtype never overrides them. Optional absent/null stop metadata versus explicit malformed values follows table. |
| Claude intermediate versus final | Valid assistant.error/API retry/tool_use message stop reason followed by valid result succeeds with diagnostics retained; errors earlier than later successful completion do not become final failure. Invalid diagnostic/content envelopes reject. Result final overrides intermediate/root/nested text; absent/nonstring/blank result cannot use earlier assistant text to pass. |
| Root/nested identity | Matching supplied root IDs pass; root conflicts/invalid values/duplicate init reject. Historically absent root IDs stay null and supported. Valid nested assistant/user identity does not contaminate root session/final. Parent/tool scopes cannot cross-consume matching IDs; unsupported parented result or child-only final cannot prove root success. |
| Terminal ordering | Duplicate successes and failed-then-success reject in both runtimes. Only parse-valid trailing rate_limit_event remains permitted and cannot change trusted fields. Post-terminal diagnostic/tool/text/start/unknown event or malformed trailing metadata rejects. |
| Structural damage | Invalid JSON/UTF-8, duplicate keys, nonobject/missing/wrong-type event type, nonfinite/overflow numbers, surrogate strings/keys, malformed required diagnostic/final/terminal fields reject regardless of later native success. Preserve diagnostic source locations and a valid serializable report. |
| Process/postprocessing | Native nonzero retained exactly by both public runners even with terminal success/final. Codex absent/raced/unwritable last-message destination, stale/missing saved final and direct precollection nonzero remain rejection; native code takes precedence in public runner. Diagnostic retention survives all failures. |
| Selected checks, both runtimes | With recovered novel diagnostics, valid artifact/canary checks pass; wrong/missing proof, unreadable expected input, absent/nonregular/hard-linked/log-alias artifact and saved-final mismatch reject. Invalid prelaunch setup does not invoke fake runtime. |
| Bounds/report/statistics/detail | Unchanged key set/schema/source/not_assessed. More than 20 diagnostics and >2000-char records retain full counts/truncation/lines/raw logs; >12000-char finals retain raw complete text/length flag. Verbatim terminal usage/zero metrics, no streaming accumulation, missing/conflicting terminal metrics and wall-clock behavior remain. Raw detail stdout/stderr/redirection/native exits and bypassed optional checks remain unchanged for both runtimes. |

Explicitly revise the old test groups for notice/server-text lookalikes, startup message/path matching, one-warning gap limit, final-before-last-notice, Claude top-level-error fatality, old warning/error promotions and clean-stream proof bypass. Convert wording-only rejections into successful needs_review controls. Keep malformed payload cases in separate rejection tables. Revise ordinary invalid/conflicting identity tests to reject where explicit evidence is malformed/conflicting; do not weaken Unicode/parse/check/process failure assertions to make the suite green.

Controller-owned later validation, after reviewed source is available:

1. Read-only original replay against repository collector and installed collector using known original paths/check arguments. Record versions/hashes, exact commands/outcomes and input equality before/after; original contents never enter delegate fixtures. Assert S1, each diagnostic source/content retained, full check outcomes and not_assessed. Do not impose v1 fixed category counts.
2. Complete revised plan review, slice dual independent code review, aggregate dual deepreview and actual-PR dual deepreview in Gateflow order. Controller checks evidence, adjudicates and routes accepted fixes to `gpt-6-sol`; code/aggregate/PR review defaults are independent Claude-runtime `mimo-flash` and `ds-flash`. Record applicable evidence reuse and fix/re-review versions. Controller commits/pushes/creates draft PR; no merge/approval/mark-ready/reviewer request/external comment.
3. From the approved checkout run already authorized component deployment: `./scripts/sync-agent-tools.sh` for collector/runners and `./scripts/sync-skills.sh` for the generic skill. Record installed file equality and Codex/Claude versions. `./scripts/sync-codex-agent.sh` is not applicable unless separately approved profile/catalog/route/shim changes actually occur; none are planned. Retain these applicable commands in closeout and remind the user to sync to live for later changes. Reopen Agent sessions for updated skills; runner callers already on PATH need not source zshrc. Reload with `source ~/.zshrc` or a new shell if launcher functions are deployed/changed.
4. Separately invoke `mimo-flash` through each installed runtime with synthetic input and a new result path: tool-read input, program-compute/write result, tool-read it back. Check actual native/tool/result events, exact computed content, process/report outcomes and retained raw logs. These probes prove installed dispatch/completion/tool behavior, not reproduction of transient network faults. Fault classification is covered by synthetic matrices and original replay.

## Documentation decision

Update README and the generic sub-agents skill in S-1. State the native-terminal completion predicate, recovery independent of intermediate text, retained diagnostics/needs_review, native negative completion rejection and caller-owned not_assessed. Explain Codex's refusal/finish-reason visibility limit, Claude result ownership/optional reason metadata and the distinction between intermediate tools/retries and final completion. Preserve current statistics/detail/artifact/canary descriptions. Remove long supported-notice wording/UUID/attempt inventories and the unknown-text-fatal assertion. Do not add universal audit/permission/retry ceremony or task-specific business requirements.

## Classified risks, uncovered areas and questions

| Risk / uncovered area | Classification, owner and destination |
| --- | --- |
| Current unfamiliar-diagnostic false rejection and Claude success-labeled negative completion | **fixed in current slice** (planned S-1); implementation agent, then controller code/aggregate/PR review. Not yet claimed fixed. |
| Current proof bypass in clean Codex calls, Claude assistant-text fallback and root identity/tool-scope ambiguity | **fixed in current slice** (planned S-1), only the proof/ownership behavior specified above; implementation agent/controller tests and review. |
| Codex completed text lacks native independent refusal/finish-reason | **assigned to later work unit** if richer native evidence becomes available; owner maintainer/caller. Preserve prose and not_assessed; no heuristic fix or blocker here. |
| SDK/CLI version gap, unobserved positive Claude stop reasons and future native completion variants | **assigned to later work unit** for evidence-backed protocol compatibility; owner maintainer. Known typed/observed fields are specified here; explicit unsupported final reasons fail closed. No claim to validate every future field/schema or full SDK message union. |
| Historical absent Claude identities/reason metadata limits independent attribution/completeness visibility | **assigned to later work unit** if stronger runtime metadata is required; owner maintainer. Current decision uses fresh dedicated log, unique root result and any supplied identities; absence is compatible, explicit conflict/malformed/negative evidence rejects. No user decision required for this bounded contract. |
| Task/business correctness, unresolved business conclusions and artifact content/provenance beyond selected checks | **assigned to later work unit**, owner caller, destination the caller's existing task-verification workflow. Completion, canary or multiple agents agreeing does not prove task correctness. No business evidence read or assessment here. |
| Actual transient fault reproduction; future real network/provider behavior | **assigned to later work unit if requested**, owner user/controller. Ordinary live probes do not inject faults; current classification relies on original read-only replay and synthetic fences. |
| Native message/telemetry/tool variants outside the specified proof fields | **assigned to later work unit**, owner maintainer. Keep current non-proof handling; no complete nested graph or general schema migration in S-1. Evidence contradicting a current mandatory completion rule goes to controller, not silent scope widening. |

No blocking question or material uncovered user tradeoff is established by the supplied evidence. Protocol choices above are explicit implementation decisions for revised plan review. Nothing requires a new goal confirmation, original-business access or production mutation during this delegation.

## Completion report and continuation

Implementation completion report must identify work unit/gate/S-1, approved plan and exact source version, changed files and contract behavior, actual command/results, v2 acceptance-matrix coverage and retained/revised baseline assertions, docs changes, finding status, classified residual risks/uncovered areas, artifact path and **next entry point: slice code review**. Rejected/failed validation is reported with exact evidence, not counted as completion. Controller owns durable gate records, review adjudication, accepted commits and subsequent entries.

This plan's completion report: relevant goal/code/tests/docs/protocol evidence inspected; 61 test methods counted; production sources match base; no baseline rerun, business read, synthetic/model request, production/test edit or deployment. Only this revised plan is authored. Decision is plan-ready, review pending. **Next entry point: revised plan review of `plan-v2.md` against `goal-confirmation-v2.md`.**
