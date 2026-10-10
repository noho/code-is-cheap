# Plan: Codex recovered stream-error classification

- Gate: plan-review fix completed; next unfinished gate: `re-review`; work unit: `codex-recovered-stream-errors`.
- Artifact: `docs/gateflow/codex-recovered-stream-errors/plan.md`.
- Branch: `fix/codex-recovered-stream-errors`; HEAD/base: `20fc6c37751836329143567c166990bdffa9de3c` (#51 merged).
- Binding scope: [goal.md](goal.md), confirmed by the caller. No separate design document.
- Preflight: requested work branch already exists at the baseline. Status shows this work unit's untracked artifact directory and three supplied review-report paths; no tracked changes. File ownership is explicitly restricted by this fix assignment.
- Decision: one behavior slice, confined to collector classification, focused offline runner tests and short documentation clarification. No runner change is required by the inspected call chain.
- Status: five controller-accepted plan findings addressed; revised proposal awaits independent re-review. This is not a review-loop pass, accepted-plan commit, implementation pass or work-unit closeout.
- This fix assignment writes only `plan.md` and [plan-fix-01.md](plan-fix-01.md). It does not edit `state.md`, statistics, evidence/review artifacts, product code, tests, READMEs or skills; delegate; stage/commit/push; create a PR; install; make live/API calls; or read/rerun original caller material. Existing historical evidence below is attributed to prior gates and is not rerun here. The controller resumes at `re-review`, then `accepted plan commit` before implementation.
- Decision inputs: [plan-adjudication.md](plan-adjudication.md), valid reviews [DS-1 source](../../reviews/plan-review-20261011-033016.md) and [MiMo-01/02/03 source](../../reviews/plan-review-20261011-034538.md), and [Controller-01 evidence](evidence/controller-diagnostic-cap-check.json). The unaccepted first report contributes no findings or pass evidence.

## Goal, motivation and completion behavior

The adapter currently mistakes a native retry notification for an unrecovered runtime error. Correct that classification only when a recognized notification is followed by reliable success in the same recorded execution and all selected mechanical checks pass. A final answer or native exit 0 alone cannot establish recovery.

The confirmed success signals, used below as alignment identifiers, are:

| ID | Binding success signal |
| --- | --- |
| G1 | Recognize narrowly and prove subsequent success in the same valid recorded execution; unknown/ambiguous errors remain fatal. |
| G2 | Retain original recovered notice and event location as diagnostics; it does not alone cause rejection/exit 1. Existing anomalies can still produce `needs_review`. |
| G3 | Unrecovered notices, arbitrary errors, `turn.failed`, native/postprocessing nonzero, malformed/conflicting/missing terminal or final, and selected-check failures remain rejected. |
| G4 | Validate the real log offline and a small independent synthetic matrix through collector/runner boundaries. |
| G5 | Preserve native final/logs/statistics, selected checks, Claude behavior and routing; add no proof fields or broad redesign. |

Expected behavior: a clean recovered synthetic stream returns `agent_status=completed`, `validation_status=passed`, `runner_exit_code=0`, with the notice in `warnings`. The authorized real stream retains its five existing anomalies and becomes `needs_review`/runner 0, with line 193 in `warnings`. Neither result claims business correctness; `result_status` remains `not_assessed`.

Non-goals: creating a retry policy; retrying tasks; interpreting tool failures as top-level runtime errors; downgrading unknown errors; changing routing/model settings; introducing compatibility/migration or generic protocol-validation layers; new report fields/schema; independent verification of the caller's business work; restoring caller workflows; merge or deployment. Outside-goal improvements remain classified residuals.

## First-principles judgment and source ownership

The JSONL contains a notification about an interrupted stream, followed by native continuation and a successful terminal. The native process did finish successfully. The defect is the adapter's unconditional fatal classification, not absence of native completion or a retry implementation.

Direct baseline code evidence:

| Source | Existing responsibility and relevant behavior |
| --- | --- |
| `scripts/agent-run-result.py:194-239`, `Collection.codex()` | Codex event interpretation. Lines 207-208 put every top-level `error` into fatal diagnostics. Terminal conflicts/`turn.failed` already stay fatal; tool anomalies have separate treatment. |
| `scripts/agent-run-result.py:291-397`, `Collection.collect()` | Strict JSON/UTF-8 parsing, event order after terminal, final/last-message agreement, selected canary/artifact checks, stderr diagnostics, native/postprocessing exit checks. It is the owner of final recovery eligibility because it sees all these results. |
| `scripts/agent-run-result.py:398-410`, `main():448-450` | Error counts determine rejection and synthesized runner exit 1; `main()` exits 1 only for rejection. Native usage and display/log fields are already collected separately. |
| `scripts/codex-agent-run:498-552` | Native invocation and exit, final-message postprocessing, then collector invocation with both original `runtime_exit` and precollection `run_exit`. It preserves earlier nonzero exits and otherwise propagates collector exit. |
| `tests/test_agent_run_results.py:12-64` | Existing deterministic fake-runtime harness exercises the actual shell runners without model requests. Native functions are replaced by local fixtures. |

Call chain: `codex-agent-run -> run_codex -> native exit -> optional last-message save -> Collection.collect -> strict parser -> Collection.codex -> remaining final/selected/stderr/process checks -> recovery finalization -> existing report/status -> main exit -> outer runner exit`.

Recovery must be finalized after all checks, rather than during the `error` event or immediately on `turn.completed`. Otherwise a later malformed event, stale last-message, failed optional check or postprocessing failure could be hidden. Do not consult an archived report's `runner_exit_code=1` as the native/precollection code: the archive already includes this bug's collector rejection.

### Authorized observed shape

Prior goal/plan evidence is indexed in [evidence/goal-log-check.json](evidence/goal-log-check.json) and summarized in the binding goal and both valid reviews. The prior gate's permitted structural-only script recorded all four named files' sizes/hashes and these facts; this fix gate does not read those original inputs or rerun that script:

- 211 strictly parsed events; first native frames are one `thread.started` then one `turn.started`.
- Thread frame keys: `type`, `thread_id`, with nonblank string identity. Turn-start keys: `type`.
- Error at line 193 has exactly `type` and `message`. Its complete message is:

  ```text
  Reconnecting... 1/5 (stream disconnected before completion: stream closed before response.completed)
  ```

- Tools complete after that notice at lines 194-209. The selected final is an `item.completed` / `agent_message` at line 210, followed by the unique `turn.completed` at line 211, with native exit 0 and no `turn.failed`.
- Final event keys: `type`, `item`; final item keys: `id`, `type`, `text`. Terminal keys: `type`, `usage`.
- Earlier completed agent messages exist at lines 3, 12, 139 and 158. Therefore do **not** require exactly one agent message; use the collector's last completed message, with validated order/shape.
- Last-message, event final and archived summary final are exactly equal. The adapter's existing comparison uses stripped text and stays unchanged.
- Archived canary `match` and regular-artifact metadata are reported evidence only. The original optional checks were not independently rerun. No original canary/expected inputs or business artifact content were read.

Tool completion is corroborating continuation, not an additional recovery prerequisite. A legitimate text-only turn can prove completion by a valid post-notice final and native terminal. Usage/time are statistics, not success predicates.

## Implementation decisions and exact safety predicates

### D1 — recognize only the recorded notification family (G1, G3)

Add a private pure helper `recognized_codex_connection_notice(event)` in `scripts/agent-run-result.py`. It returns true only when:

1. The event keys are **exactly** `{"type", "message"}`, and `type == "error"`.
2. `message` is a string and `re.fullmatch` matches the following pattern, without stripping, case folding, substring search or coercion:

   ```python
   r"Reconnecting\.\.\. [1-5]/5 \(stream disconnected before completion: stream closed before response\.completed\)"
   ```

Only the ASCII attempt digit varies, bounded by the recorded five-attempt budget; the transport/completion text and punctuation are literal. The original observation covers `1/5`; `2/5` through `5/5` are explicitly synthetic cases for that same bounded grammar, not additional observed provider behavior. Do not infer recovery from attempt count, require monotonic retry progression, or expand to arbitrary reconnect/timeout/disconnection wording.

Missing/nonstring message, extra fields including `code`/`error`, other budgets, Unicode digits, whitespace/prefix/suffix/newline differences and other transport reasons go through the existing immediate `note("errors", event, line)` path. Embedded item errors, stderr and Claude's top-level errors do not use this helper.

### D2 — retain candidates pending complete collection (G1, G2, G3, G5)

Add private Codex-only proof state to `Collection.__init__`; no report schema change:

- Thread/turn-start counters, first line and parsed-event ordinal, and known-frame validity flags.
- First completed-terminal line and known-frame validity flag; use existing `self.terminal` for uniqueness/conflicts/failure.
- Validity flag for the selected last completed agent-message frame; use existing `self.final` and `self.final_line`.
- Candidate count, first/last candidate lines, and at most `DIAGNOSTIC_LIMIT` retained `(line, event)` pairs.

`Collection.codex()` records this state while retaining its existing parsing/data extraction. A recognized top-level notice is deferred, rather than immediately counted as an error. Unknown errors and all existing parser/terminal errors remain immediate and permanent. Counters/first-last positions cover **every** candidate even after the display cap; do not use retained diagnostic samples as the proof source.

**Chosen MiMo-01 option (a): strict supported-shape recovery only.** Known-frame validity and initial parsed-event ordinals are intentionally conservative positive recovery fences for notice-bearing streams. They describe the supported evidence shape for this exception, not universal Codex protocol/schema invariants derived from one observation. Keep these predicates; option (b), loosening the fences, is not selected. G1 requires reliable same-execution proof and G3 refuses ambiguous evidence:

| Frame | Required positive evidence |
| --- | --- |
| `thread.started` | Exactly `type`, `thread_id`; identity is a nonblank string. |
| `turn.started` | Exactly `type`. |
| `turn.completed` | Keys contained in `type`, `usage`; `usage` is optional and does not become a validity gate. Existing extraction retains a dict verbatim or returns null. |
| Selected `item.completed/agent_message` | Event keys exactly `type`, `item`; item keys exactly `id`, `type`, `text`; ID is a nonblank string and text is a nonblank string. |

This deliberately refuses recovery for unobserved envelopes, added metadata/control/error/status fields, preamble frames or items between starts. A potentially legitimate variant can therefore be a false negative; refusal is evidence conservatism, not a claim that its native protocol is invalid. Exact fields and ordinals are not applied to ordinary Codex streams without a recognized candidate, nor to Claude. Keep baseline final/metric/session interpretation and baseline acceptance for those controls. Unsupported notice wording/budgets, extra frame fields, preambles, resume/persist variants and final-before-last-notice streams are classified limitations below, assigned to later evidence-backed work. D1 retains exactly the ASCII `1..5/5` grammar; only `1/5` is observed, and recovery never follows from the attempt digit. No generic validator or compatibility layer is introduced.

### D3 — prove a single successful execution, after all selected gates (G1, G3, G5)

Add `Collection.codex_connection_recovery_failure()` returning `None` on proof success or a specific short reason on failure. Evaluate only when `runtime == "codex"` and at least one candidate exists. All predicates must hold:

1. Exactly one valid thread start and one valid turn start in the whole stream, at parsed-event ordinals 1 and 2 respectively. Blank physical lines remain ignored. Duplicate starts fail even with the same identity; conflicting/missing/late starts cannot prove same-execution recovery.
2. The existing terminal is uniquely `turn.completed`, with a valid known terminal frame. Existing multiple-terminal detection, `turn.failed`, parse errors and post-terminal event rejection remain authoritative. Preserve the existing allowed post-terminal `rate_limit_event` exception.
3. The selected last completed agent-message frame is valid and nonblank, and the ordered physical lines satisfy:

   ```text
   thread_start < turn_start < first_notice <= last_notice < selected_final < completed_terminal
   ```

   Earlier messages are allowed; an old message before the notice cannot serve as the recovered final. Final after terminal, notice after terminal or a terminal preceding final cannot recover. The mixed sequence `notice A < selected_final < notice B < completed_terminal` also fails: the **last** candidate, including candidates beyond the retained display cap, must precede the selected final. The named mixed-order fixture below retains notice B at physical line 5 as an error.
4. Both `args.exit_code` (native) and `args.runner_exit_code` (precollection/postprocessing) equal 0. They are required collector inputs supplied by the existing runner; do not synthesize native success from report text.
5. Before finalizing the pending candidates, `self.counts["errors"] == 0` after **all** existing final/last-message, strict parsing, selected canary/artifact, stderr-reading and process checks. Arbitrary errors, failure terminals and structural errors can never be erased by later success.

Use this deterministic first-failing reason order: start multiplicity/shape or initial frame order; candidate outside started turn; terminal identity/shape; final shape/order; native/postprocessing nonzero; other collector validation errors. Reasons are short and specific; tests assert the applicable reason category, original notice text, line and outcome rather than an exact prose sentence. A failure caused by another existing check retains that check's detailed diagnostic as well. Do not require zero anomalies, visible tools, canary selection, artifact selection, usage or elapsed time.

### D4 — emit diagnostic category once, keep existing statuses (G2, G3, G5)

Add `Collection.finalize_codex_connection_notices()` and call it after existing session diagnostics (baseline line 397), immediately before the existing validation expression (line 398).

- On proof success, each candidate is a `warning` with prefix `Recovered Codex connection notice: ` followed by the original event representation.
- On proof failure, each candidate is an `error` with prefix `Codex connection notice recovery not proven (<reason>): ` followed by the original event representation.
- Use `note()` with `stream="output"`, original physical line and existing diagnostic fields; restore the prior stream afterward. Original message/location stay available and full original events stay in untouched logs.
- Compute the proof once **before** any diagnostic reservation/emission; choose `warnings` on success, otherwise `errors`. Every preexisting hard failure count must still participate in this proof. Do not infer safety from displayed samples.
- **Controller-01 reservation:** with at least one retained candidate, before emitting any retained pair through existing `note()`, if the target category list is already exactly `DIAGNOSTIC_LIMIT`, remove its last displayed entry **once** (`target.pop()`). This reserves one first-candidate slot, preserving the earliest `DIAGNOSTIC_LIMIT - 1` existing diagnostics. Do not decrement counts, reset `text_truncated`, change `note()` or repeatedly evict for later candidates. If the list has room, do not remove an entry.
- Emit retained pairs in original candidate order through `note()`, including its normal count increments and text-truncation handling. Then add `candidate_count - len(retained_pairs)` to the chosen category count for candidates beyond retention, as before. A retained pair that finds a full target still increments its count via `note()`; do not add it again. Category totals are exactly `old_count + candidate_count`, independent of display eviction.
- Keep per-category display cap 20, message cap 2000 characters, final display cap 12000 and existing `diagnostics_truncated = text_truncated or any(count > DIAGNOSTIC_LIMIT)`. At least the first candidate's original message and physical line must appear in the chosen category, even if full at entry. Messages for recognized notices plus the specified short prefix fit the current text cap. Existing long-message truncation state survives even if the reserved slot evicts its displayed entry. No second public list, generic priority framework or new report field is added.
- Leave existing `validation_status`, `runner_exit_code`, `agent_status`, terminal metrics, final display/truncation, optional-check reporting and `main()` exit logic unchanged.

Outcome table:

| Evidence | Candidate category | Result |
| --- | --- | --- |
| Known notice + complete proof + no existing anomalies | warning | passed, completed, runner/collector/outer exit 0 |
| Known notice + complete proof + ordinary anomalies | warning | needs_review, completed, exit 0 |
| Known notice with missing/ambiguous proof or any hard check failure | error | rejected; native/earlier runner nonzero preserved, otherwise exit 1 |
| Unknown/arbitrary top-level error, even with final/terminal/exit 0 | existing error | rejected |
| No recognized notice or Claude execution | no new decision | existing behavior |

`agent_status=completed` may still accompany rejected selected checks, as today; do not redefine it as collector acceptance. No route/model-proof fields, schema bump, retry scheduling, error taxonomy framework or shell special case is needed.

## One implementation slice

### S1 — preserve a recovered notice without hiding real failure

- Objective/outcome: implement D1-D4 together so recognized recovered Codex streams can complete while all binding negative cases remain rejected. One behavior increment warrants one implementation/review loop; separating recognition, proof, tests or documentation would leave an incomplete behavior.
- Prerequisites: controller-adjudicated plan review/re-review pass and accepted-plan checkpoint. Use this branch/baseline; inspect status before editing. Existing supplied goal/state/evidence files remain controller-owned.
- Implementation/fix owner: designated runner owner from `goal.md`. Controller owns decisions, gate transitions, accepted checkpoints and review-loop closure.
- Allowed product files: `scripts/agent-run-result.py`, `tests/test_agent_run_results.py`, `README.md`, `README.zh.md`, `skills/sub-agents/SKILL.md`.
- Exact code changes: private matcher; bounded candidate/proof state; Codex bookkeeping/defer branch; two private proof/finalization methods with D4's single-slot reservation; one finalization call before status construction. Retain existing strict parser, ordinary error branches, checks, metrics extraction and complete report contract. These are future S1 changes, not permitted in this plan-fix gate.
- Tests: extend existing `RunnerResults` with synthetic recovered fixtures/subtests and direct adapter calls where needed to select process inputs independently. Do not add external real-log fixtures, another test framework or generic fake-runtime redesign.
- Documentation: only the short classification clarification specified below, within this slice.
- Reviewed but not writable product boundary: `scripts/codex-agent-run` and `scripts/claude-agent-run`. The existing propagation already supports collector-only correction. If implementation demonstrates a required runner change, present the concrete evidence to the controller before changing file ownership; do not introduce a shell downgrade path.
- Invariants: every arbitrary/unknown top-level error remains counted; failures cannot revert to success; candidates are warned only after positive complete proof; no skipped selected checks; bounded displayed diagnostics plus complete counts; preserved final/statistics/logs/Claude behavior.
- Non-goals: all listed above; no opportunistic schema hardening or broad treatment of `item.*` failures.
- Completion signal: focused new synthetic public-runner/adapter tests **and the entire `tests/test_agent_run_results.py` offline module** pass, including all 38 baseline test methods plus added tests; authorized original scoped replay has line 193 warning and unchanged native data, all selected-check negatives reject, minimal docs align, and controller code-review/re-review accepts the slice. The full-file requirement closes DS-1 shared-path regression coverage; a selected existing-test subset cannot substitute for it.
- Stop conditions: baseline/ownership drift; inability to implement the specified proof within the allowed boundary; original source hash mismatch/unavailability; a required validation failure; evidence requiring scope or acceptance changes. Record outside-goal findings as residuals rather than silently adding work.

## Validation design and commands

Use independent synthetic text/tool output/canary/expected/artifact inputs. Runtime commands are local deterministic fixtures only; never invoke a native provider/model, business replay or caller task. Originals stay external immutable inputs; only scripts selecting structural/control fields and equality/hashes may process the four paths named in the index.

### Required focused tests for S1

Add these named `RunnerResults` tests; use subtests to avoid separate behavioral slices:

| Test | Assertions and goal alignment |
| --- | --- |
| `test_codex_recovered_connection_notice` | Attempt digits 1-5 within the exact grammar, one/multiple notices, multiple earlier agent messages, text-only recovery and tool/stderr anomalies. Original message/line appear in warnings; no notice error; clean passed/0 or anomalies needs_review/0; native final/usage/log fields preserved; complete frozen report contract below holds for clean/anomaly recovery. G1, G2, G5. |
| `test_codex_connection_notice_lookalikes_rejected` | Prefix/suffix/newline/changed transport, budget/attempt/Unicode variants, missing/nonstring message, extra error/code fields, arbitrary error plus a known candidate, and an arbitrary error after more than 20 candidates. Native completed/exit 0 cannot downgrade them. G1, G3. |
| `test_codex_connection_notice_supported_shape_fence` | Named extra-field/preamble negatives in the fixture table below refuse recovery, with the candidate in errors/rejected/1. Paired streams without a candidate retain baseline acceptance, including extra fields and preambles. Strict shape is a recovery fence only. G1, G3, G5. |
| `test_codex_connection_notice_mixed_order_rejected` | Exact six-line `notice/final/notice/terminal` fixture below rejects/1 and retains late notice B at output line 5 in errors; no recovered warning. The last candidate controls proof. G1, G3. |
| `test_codex_connection_notice_requires_same_execution_completion` | Missing/duplicate/conflicting/invalid starts, duplicate same-ID start, prefix/orphan event or an item between starts, notice before start, final only before notice, missing/failed/duplicate/conflicting terminal, event/notice/final after terminal, malformed JSON/duplicate keys/nonfinite values/lone surrogates, missing/blank/nonstring/unknown final envelope, success envelope with error/status fields. Allowed trailing rate-limit event still works. Missing/invalid usage remains unavailable, not a new success requirement. G1, G3, G5. |
| `test_codex_connection_notice_keeps_selected_checks` | Matching synthetic canary plus real fixture read candidate and new regular artifact succeeds; mismatching/missing proof, missing/unreadable selected expected input, missing artifact and invalid artifact/log alias still reject. Last-message matching/mismatching is enforced. Existing prelaunch failures remain prelaunch failures; for post-run-only invalid artifact cases use direct adapter fixtures or existing hard-link harness. No original optional inputs. G3, G4, G5. |
| `test_codex_connection_notice_keeps_process_failures` | Native exit 7 remains 7/failed; native 0 plus missing/raced/unwritable final-message save remains rejected/outer 1. Use existing `SKIP_LAST_MESSAGE`, `OCCUPY_LAST_MESSAGE`, `BREAK_LAST_PARENT` fixture controls and distinct new destinations. Direct collector native0/precollection1 stays rejected. G3, G5. |
| `test_codex_connection_notice_diagnostic_bounds` | Unsaturated and saturated success/failure fixtures in the exact bounds table below assert full totals, display cap, earliest old entries, first-candidate message/line and truncation. Late failures beyond retained samples cannot recover. No count subtraction, text-flag reset or repeated eviction. G2, G3, G5. |
| `test_claude_connection_error_stays_fatal` | The identical notice text as Claude top-level error before success result remains fatal; clean Claude unchanged. Both retain the complete frozen report contract below. G3, G5. |
| `test_agent_run_report_contract` | Assert the literal complete baseline key set and four invariant values below on clean/anomaly recovery, proof failure, ordinary Codex success, Claude success and Claude top-level error controls. Do not derive the expected set from the amended collector or assert only absence of selected proof keys. G5. |
| `test_codex_connection_notice_detail_preserves_raw_stream` | `--detail` still emits raw JSONL, does not collect/reclassify or run optional closing checks; native exit/redirection preserved. G5. |

### Named supported-shape negatives (MiMo-01; G1, G3, G5)

Use otherwise clean `thread.started`, `turn.started`, recognized notice, valid final, `turn.completed`, with exits 0/0. Each named mutation independently fails recovery and keeps the original notice message/physical line in errors, `validation_status=rejected`, collector/report/outer exit 1. Subtest names are fixture identifiers, not additional slices. Exercise arbitrary `metadata` fields and explicit `status`/`error` fields where listed; added fields are refused even if apparently benign.

| Fixture/subtest | Mutation and failed fence |
| --- | --- |
| `notice-extra-field` | Add `code`, `metadata`, `status` or `error` to the top-level error; D1 no longer recognizes it and baseline fatal behavior applies (`lookalikes_rejected`). |
| `thread-start-extra-field` | Add `metadata`, `status` or `error` to `thread.started`; exact start key set fails. |
| `turn-start-extra-field` | Add `metadata`, `status` or `error` to `turn.started`; exact start key set fails. |
| `terminal-extra-field` | Add `metadata`, `status` or `error` to `turn.completed`; terminal key subset fails. |
| `final-envelope-extra-field` | Add `metadata`, `status` or `error` to selected `item.completed`; final event key set fails. |
| `final-item-extra-field` | Add `metadata`, `status` or `error` to selected agent-message item; final item key set fails. |
| `preamble-before-thread-start` | Prefix one valid nonterminal `rate_limit_event` before thread/turn starts; starts now have ordinals 2/3 and recovery fails. |
| `item-between-starts` | Insert a completed ordinary message between starts; turn start has ordinal 3 and recovery fails. |

For every frame/preamble mutation except `notice-extra-field`, remove the candidate in a paired control and assert the actual baseline outcome remains `passed`/0 with the same final/session/usage semantics. `notice-extra-field` remains fatal without any recognized candidate because it is an arbitrary error. This locks the conservative fence without introducing generic validation. Existing missing/duplicate/invalid-start and envelope tests remain required.

### Last-candidate mixed-order negative (MiMo-02; G1, G3)

Use these six physical lines, with distinct notice attempts and native/precollection exits 0/0:

1. valid `thread.started`;
2. valid `turn.started`;
3. recognized notice A (`1/5`);
4. valid completed agent-message final;
5. recognized notice B (`2/5`);
6. valid `turn.completed`.

Assert `agent_status=completed` can remain, but `validation_status=rejected`, report/collector/outer exit 1, both candidates counted as errors (exact error count 2 with this otherwise clean fixture), no recovered warning, and notice B's original message at `stream=output`, `line=5` in errors. The first notice alone would pass ordering; the last notice after the selected final is the decisive rejection. This fixture has no saturation, so both lines 3 and 5 must be displayed. The bounded late-candidate tests separately ensure proof observes candidates beyond retained samples.

### Frozen complete report contract (MiMo-03; G5)

Freeze the following **29** top-level keys literally from baseline `Collection.collect()` (lines 399-410); use set equality, so both additions and omissions fail:

```python
{
    "schema_version", "source", "runtime", "provider",
    "runtime_exit_code", "runner_exit_code", "agent_status",
    "validation_status", "result_status", "final_answer",
    "final_answer_truncated", "final_answer_chars", "wall_clock_seconds",
    "usage", "runtime_metrics", "session_id", "terminal",
    "tool_evidence_scope", "tool_results", "events", "canary_status",
    "canary_read_candidate", "errors", "anomalies", "warnings",
    "diagnostic_counts", "diagnostics_truncated", "artifacts", "logs"
}
```

Also assert `schema_version == 1`, `source == "subagent_report"`, `result_status == "not_assessed"`, and `tool_evidence_scope == "recorded_events_only"`. Required controls are Codex clean recovery, recovery with anomaly (`needs_review`), proof failure (including the mixed-order fixture), ordinary Codex success with no candidate, Claude clean success and Claude identical-text top-level error followed by success. Runtime/provider values remain their actual fixture inputs; no route/model/recovery-proof fields are permitted. Existing final/usage/log/status tests supplement this fixed key-set assertion.

### Exact bounded diagnostic fixtures (Controller-01; G2, G3, G5)

Each successful-proof fixture has valid starts, post-last-notice final/terminal and exits 0/0. Old warning events are benign completed `item/error` events with `Model metadata for fixture not found` text; old failure events are arbitrary top-level errors. Give old entries distinct messages so tests can detect repeated eviction. Retain only the first 20 candidate pairs while tracking all first/last lines and total candidates.

| Fixture/subtest | Exact totals/display/visibility assertions |
| --- | --- |
| `unsaturated-success-25` | 25 notices and no old diagnostics: warnings 25, errors/anomalies 0, 20 warnings displayed, first candidate displayed, passed/0, diagnostics truncated. |
| `unsaturated-failure-25` | Same 25 notices but selected final before them and valid later terminal: errors exactly 25, warnings/anomalies 0, 20 errors displayed, first candidate displayed, rejected/1, diagnostics truncated. |
| `saturated-success-20-old-25-notices` | Old warnings at lines 3-22; notices at lines 23-47; final/terminal lines 48/49. Warnings **45**, errors/anomalies 0; display **20** = first 19 old entries + first notice at line **23**; passed/0 and diagnostics truncated. Later notices must not evict that first notice or any earlier old entry. |
| `saturated-failure-20-old-25-notices` | 20 arbitrary errors at lines 3-22 plus the same 25 candidates at lines 23-47 and clean final/terminal: errors **45**, warnings/anomalies 0; display **20** = first 19 old errors + first candidate at line **23**; all 20 original failure counts remain; rejected/1 and diagnostics truncated. |
| `overflowed-failure-23-old-25-notices` | 23 arbitrary errors at lines 3-25 plus 25 candidates at lines 26-50 and clean final/terminal: errors **48**, warnings/anomalies 0; display **20** = first 19 old errors + first candidate at line **26**; no subtraction of displayed/undisplayed old errors; rejected/1 and diagnostics truncated. |
| `one-slot-success-19-old-25-notices` | Old warnings 19 plus notices 25: warnings **44**, display **20**, all 19 old entries plus first candidate retained; no eviction needed; passed/0 and diagnostics truncated. |
| `evicted-long-diagnostic-keeps-text-truncation` | Direct private diagnostic-finalization fixture: 20 existing category entries, last message length 2501, one candidate; final total **21**, display **20**, first 19 entries plus first candidate; `text_truncated` remains true. Also assert emitted fields respect message cap 2000 and original `message_chars`/`truncated` semantics. Do not expose this private flag in the report. |

Use existing real `note()` behavior, not a new priority mechanism. Proof is calculated before reserving the slot; the failure fixtures must never recover because removing a displayed old error does not change `counts["errors"]`. Check every diagnostic's existing fields and maximum length, plus final display limit 12000 in the existing long-final regression. These exact fixtures close the controller's `45 counted / 20 displayed / 0 notices` counterexample.

Commands after implementation (from repository root; not executed as product verification in this plan-only task):

```bash
python3 -B tests/test_agent_run_results.py \
  RunnerResults.test_codex_recovered_connection_notice \
  RunnerResults.test_codex_connection_notice_lookalikes_rejected \
  RunnerResults.test_codex_connection_notice_supported_shape_fence \
  RunnerResults.test_codex_connection_notice_mixed_order_rejected \
  RunnerResults.test_codex_connection_notice_requires_same_execution_completion \
  RunnerResults.test_codex_connection_notice_keeps_selected_checks \
  RunnerResults.test_codex_connection_notice_keeps_process_failures \
  RunnerResults.test_codex_connection_notice_diagnostic_bounds \
  RunnerResults.test_claude_connection_error_stays_fatal \
  RunnerResults.test_agent_run_report_contract \
  RunnerResults.test_codex_connection_notice_detail_preserves_raw_stream

# Required whole-file offline regression: all existing and added RunnerResults tests.
python3 -B tests/test_agent_run_results.py

git diff --check
```

All assertions must pass. The whole-file offline command is mandatory because `codex()` and `collect()` share existing final/parser/tool/canary/status paths, including the 22 baseline methods omitted by the earlier subset. The existing `test_sync_installs_self_contained_result_adapter` uses only its private temporary fixture destination and mock runtimes; it belongs to this later S1 full-module run. No host installation/sync, live/API probes or original business rerun is part of validation. This fix-only assignment does not execute the module or that sync fixture because installation is disallowed here; current checks below are synthetic diagnostic/contract feasibility checks only. No new framework, benchmark or business acceptance test is added. Repeat only for new changes, failures or unresolved evidence.

For implemented original replay, use a new private script reading the index's exact named JSONL/stderr/last-message only, importing the actual amended `Collection`. Supply recorded native/precollection exit 0, `canary_file=None`, `canary_expected=None`, `artifact=[]`; select only control fields/counts/usage/locations and final equality/hash for output. Assert line 193 is the recognized warning, errors/anomalies/warnings `0/5/1`, completed/needs_review/runner0, terminal and final/usage/log locations unchanged. Verify all four source hashes before and after. Do not emit the raw final, event payloads, tool content or complete collector report.

If passing `1271.418953` as the replay wall argument, label it as the **archived measured runner value supplied to the collector**, not replay duration. Never replace it with experiment timing or estimated usage. Archived canary/artifact results remain distinguishable from this deliberately scoped replay.

### Historical plan assumption experiments (prior gate; G4)

Private directory: `/private/tmp/codex-recovered-plan.83MB5qQz` (outside repository). Exact top-level commands:

```bash
python3 -B /private/tmp/codex-recovered-plan.83MB5qQz/inspect_structure.py
python3 -B /private/tmp/codex-recovered-plan.83MB5qQz/experiment.py
```

Evidence retained there:

- `inspect_structure.py`, `structure-results.json`: strict parsing, allowed frame keys, event order, final hashes/equalities and four input size/SHA256 checks. No business text persisted/displayed.
- `experiment.py`, `experiment-results.json`: baseline `Collection` versus a private subclass implementing the proposed predicates; final run **58 cases, all assertions passed**: one authorized scoped real replay, 54 independent synthetic collector comparisons and three baseline fake-runtime shell samples. Every collector pair asserts unchanged final display/full-length metadata, usage/metrics, wall argument, logs, terminal/agent status, tool counts, canary/artifact reporting and session ID.
- `commands.json`: exact top-level command, constructor arguments, synthetic fixture definitions, actual shell argv/effective fixture environment and selected results. `execution-log.txt` retains command history/results including a resolved private fixture-directory reuse error. The production repository was not patched to run these experiments.

| Experiment | Result |
| --- | --- |
| Actual baseline collector on authorized real inputs, optional checks intentionally omitted | completed / rejected / runner1; errors/anomalies/warnings `1/5/0`, only error line 193. |
| Private proposed-rule subclass on the same real inputs | completed / needs_review / runner0; `0/5/1`, warning line 193; native final/usage/log metadata preserved. |
| Synthetic known notices, clean/recovered and bounded-overflow cases | pass/0, or needs_review/0 with preexisting anomaly; exact counts/limits preserved. |
| Synthetic unknown errors, unsafe frames/order/final/terminal/process or selected-check failures | rejected; unrelated errors remain fatal. Claude error unchanged. |
| Actual unchanged shell runner using fake known-notice stream | native0, collector rejection -> outer1, confirming the defective boundary. Fake native7 -> outer7; fake last-message mismatch -> outer1. |
| Originals after all experiments | all four indexed SHA256 values unchanged. |

These are historical plan feasibility checks, not an implemented-slice test pass or new execution in this fix gate. The valid MiMo review establishes that the private subclass post-processes `super().collect()` and recomputes fields; it does not prove the required production finalization-before-validation insertion. The actual shell samples still used the baseline adapter. The amended plan's supported-shape, mixed-order, complete-contract and saturated-category cases are additional requirements and are not claimed as covered by the historical 58 cases. S1 must establish the corrected path through the public runner and whole-module tests above. No native model/provider execution or original business rerun is needed.

### Current plan-fix feasibility validation (synthetic only; G1-G5)

Private directory: `/private/tmp/codex-recovered-plan-fix-l5z6d88i`. Executed:

```bash
python3 -B /private/tmp/codex-recovered-plan-fix-l5z6d88i/check_plan_fix.py
```

All assertions passed: 8 diagnostic-reservation arithmetic cases using the unchanged `Collection.note()`, 6 baseline report-contract controls, 17 baseline ordinary-stream controls for added fields/preambles, 15 literal grammar checks (5 supported digits and 10 negatives), and 2 ordering-formula checks (clean and mixed order). Static AST checks confirm all 29 report keys, 38 existing test methods and the required full-file command. Exact fixtures/results are in `check_plan_fix.py` and `experiment-results.json` in that directory; [plan-fix-01.md](plan-fix-01.md) records per-finding evidence and validation limits.

The saturation experiment uses explicit success/failure proof inputs and the real existing `note()`; it verifies reservation/count/truncation arithmetic, not an implemented production proof or finalization path. The 6 report controls use the baseline collector (including its current known-notice rejection); amended recovery still requires S1 tests. Extra-field/preamble no-candidate controls remain baseline `passed`/0. No original logs, caller business content, provider/API runtime, sync fixture or installed destination was accessed or run by this experiment. The full module is a future S1 requirement, not a test pass claimed here.

## Docs and contract decisions

No CLI, public function, schema or report-field changes. Only the category of a narrowly recognized, fully proven recovered Codex notice and the minimal D4 bounded display reservation change; status propagation already follows that category. Counts and flags preserve all existing failure/truncation evidence even when one last displayed entry is displaced. Private proof bookkeeping remains internal to the collector. This is the complete state transition: unseen known notice -> pending diagnostic -> warning after full positive proof, otherwise error at EOF. A failed/unknown event never transitions back to success.

In S1, add one short sentence to the runner-result explanation in `README.md`, mirror it in `README.zh.md`, and clarify the diagnostic/status explanation in repository `skills/sub-agents/SKILL.md`: recognized Codex connection retry notices are warnings only after valid later completion in the same execution and successful selected checks; unknown/unrecovered errors remain fatal. Do not list speculative variants or imply exit0/business correctness. Do not edit installed skill copies or synchronization/setup instructions. This plan-only task makes no such edits.

Why this is minimal: a pure literal-family matcher, bounded pending diagnostics and one conditional last-entry removal are enough; the existing collector supplies every remaining check and the shell supplies both exits. The reservation directly enforces G2 visibility, and complete counts plus unchanged text flags enforce G3/G5. Strict supported-shape option (a) resolves the review assumption without claiming a universal native schema; named negatives are necessary G1/G3 boundaries. The mixed last-notice negative, literal full-key assertion and full-file regression lock G1/G3/G5 within the existing test harness. One slice implements a single corrected behavior and its necessary false-positive guards. Strict known-frame predicates apply only to the proposed exception, rather than broadening ordinary-stream validation. Every decision/test maps to G1-G5; docs explain only G2/G3. No outside-goal improvement is promoted to a requirement.

## Classified residuals and open questions

| Residual / uncovered area | Classification | Owner / destination / nonblocking basis |
| --- | --- | --- |
| Current unconditional rejection of the recorded recoverable notice | fixed in current slice — planned, not yet fixed | Designated S1 owner; accepted implementation/re-review evidence required before claiming fixed. This is the work unit's binding defect. |
| Unobserved notification wording/budgets, extra fields on thread start / turn start / selected final event or item / terminal, and valid preambles or items between starts | assigned to later work unit | Runner/protocol maintainer; destination: separately confirmed evidence-backed protocol-variant support work unit. Chosen option (a) deliberately refuses recovery, even for possibly benign metadata/preambles; this is a supported-evidence limitation, not a universal schema assertion. Ordinary streams without candidates retain baseline behavior. |
| Resume/persist recovery streams with repeated starts, or final before the last notice (including mixed notice/final/notice/terminal) | assigned to later work unit | Runner maintainer/controller; destination: the same evidence-backed protocol-variant work unit if real evidence warrants it. Current same-execution/subsequent-final proof rejects these ambiguous shapes; mode alone is not forbidden, and goal expansion is not authorized. |
| Missing/duplicate starts or unrelated generic protocol weaknesses on streams without recognized notices | assigned to later work unit | Runner maintainer; destination: separately confirmed collector protocol validation work if needed. Do not tighten those streams in S1. Recovery-bearing streams cannot use such evidence to downgrade. |
| Original archived canary/artifact inputs and business correctness not independently verified | requiring new issue or explicit user decision | Caller/controller owns any further original-task verification decision; destination: original task workflow. Nonblocking under the explicit binding read/replay limit: archive values are labeled evidence and selected gates are independently exercised with synthetic inputs. Do not read original optional inputs to close this residual. |
| New recognition/recovery false positives, hidden notice in a saturated category, or incomplete regression/report-contract protection | fixed in current slice — planned, not yet fixed | S1 owner and controller; revised D1-D4 and named synthetic/full-file tests implement the five accepted plan fixes. Plan wording is repaired here; production correctness requires S1 and independent review. Acceptance depends on evidence, not risk classification alone. |
| Private prototype does not exercise the amended production insertion or corrected outer-runner recovery path | fixed in current slice — planned, not yet fixed | S1 owner/controller; destination: this work unit's single S1 after accepted-plan checkpoint. Actual public-runner tests and full-module regression must validate implementation; no later slice or product pass is claimed here. |
| Deferred notice diagnostic order and displacement of one last displayed old entry when a category is saturated | fixed in current slice — planned, not yet fixed | S1 owner; destination: D4 and exact saturation tests. First 19 old diagnostics, first notice, full totals, persistent text-truncation flag and untouched raw logs are the approved bounded visibility tradeoff; no chronological merge or priority redesign. |
| Merge, deployment and original-workflow restoration | requiring new issue or explicit user decision | User/caller; destination: after authorized new draft PR/final closeout or original workflow. Not needed to complete this plan gate. |

No later approved slice, existing issue or additional acceptance criterion is invented. No blocking open question currently remains for the specified proposal. Conservative false rejection of unsupported evidence is explicit; broadening recognition requires new evidence and controller review, or renewed goal confirmation if it changes scope.

## Completion report and next gate

Plan handoff reports: readiness/decision, this artifact path, concrete blockers, classified residuals, exact experiment paths/commands, counts and original-evidence limitations. Do not claim plan approval, implemented behavior, independent original optional-check success or business correctness.

Controller next entry point: `re-review` of this revised plan and `plan-fix-01.md` using the prescribed independent review routes, followed only on pass by `accepted plan commit`. All five findings remain accepted; fixes are recorded as `已修复` at the plan-document level with independent verification still pending. This assignment performs no delegation, state/statistics edit or checkpoint. Later implementation/code review/aggregate deepreview/new draft PR/PR review/final closeout remain in the authorized Gateflow order and under controller ownership; #51 is not reused.

S1 completion report must identify changed files and exact behavior, real/synthetic verification with evidence paths, docs decision, each finding's adjudication/final fix status, residual owner/destination and next unfinished gate. The controller must not close the slice while an accepted finding is unfixed or evidence is invalid.
