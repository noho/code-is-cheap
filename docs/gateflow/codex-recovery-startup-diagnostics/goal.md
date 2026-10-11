# Goal confirmation: Codex recovered reconnect with startup diagnostics

Status: confirmed by the user's delegated SubAgents upstream controller; plan authorized.

## Work unit and authorization

- Repository: code-is-cheap.
- Branch: `fix/codex-recovery-startup-diagnostics`.
- Base: `0b2b6a4bc41430e5398c227b026fa98af640f1c0`, current main/origin/main verified after fetch.
- User authorized a new work branch and new draft PR, with controller adjudication and the complete Gateflow chain after goal confirmation.
- External runner roles: GPT-6 Sol plan/implement/fix; MiMo through Codex and DS Flash through Claude in parallel, independent planreview/deepreview at the corresponding gates.
- No merge, live sync, session clearing/interruption, original business dispatch or caller-project edits are authorized.

## Goal / motivation

Correct the collector's false rejection of a demonstrably recovered Codex connection notice when an explicitly recognized startup diagnostic is emitted between a valid thread.started and turn.started. Preserve the proof that the same execution genuinely completed successfully. An unrelated warning must not make a valid lifecycle fail simply because turn.started is the third event instead of the second.

## Direct evidence and independent judgment

- `scripts/agent-run-result.py:285` evaluates recovery separately from ordinary event collection. Its current start proof requires exactly one valid thread/turn start, thread_start_ordinal == 1, turn_start_ordinal == 2 and thread-before-turn ordering.
- Authorized native log has 364 events: line 1 thread.started; line 2 item.completed/error reporting `Under-development features enabled: skip_host_skill_discovery` with the native explanatory/suppression text; line 3 turn.started; line 322 the exactly recognized `Reconnecting... 1/5 (stream disconnected before completion: stream closed before response.completed)`; line 364 turn.completed. Native runtime exit was 0.
- Controller independently re-collected the actual native log with pre-collection runner exit 0, avoiding reuse of the collector's final rejection exit 1 as input. It reproduced one rejection error with reason `start multiplicity, shape or initial frame order`; start ordinals were 1 and 3, with exactly one start of each kind.
- A six-event sanitized fixture reproduces the rejection. Removing only the startup warning yields accepted recovered completion. Removing only the reconnect yields completed/needs_review instead of rejection. This supports an overly restrictive recovery-start proof, not an unrecovered transport or invalid native terminal.
- Source and installed live collector SHA256 match. Evidence source hashes were checked unchanged after reading.
- Durable evidence: `evidence/baseline-reproduction.json` and three adjacent sanitized JSONL fixtures. Original business text, tool output and report conclusions are not copied into these artifacts.

## Minimum scope boundary

- Product scope: the Codex recovery-start predicate/bookkeeping in `scripts/agent-run-result.py`, targeted regression tests in `tests/test_agent_run_results.py`, and only directly necessary documentation clarifications.
- Recognition must be narrow enough to cover the evidenced startup diagnostic envelope/message and its supported path variation, while preserving valid lifecycle shape, uniqueness and ordering. Exact supported recognition and proof rules are to be specified/reviewed in plan, not inferred from arbitrary error-like text.
- Explicitly recognized startup diagnostics may account for the gap between starts; arbitrary item/event types, unknown errors, malformed shapes and task execution before turn start do not gain a new exemption.
- Preserve the existing exact reconnect recognition, final/terminal proof, nonzero exit handling, diagnostics and their source locations/counts, wall-clock/raw token statistics, optional canary/artifact validation, lifecycle collection and provider/runtime routing.
- This is a correction to the supported recovery exception, not a general event validator redesign. Existing unrelated event handling is not broadened or hardened as a side effect.
- Original caller logs are controller-only, read-only structural evidence. External agents receive repository code and sanitized fixtures, not the caller's business logs or conclusions.

## Non-goals

- Do not suppress/avoid the warning via runtime configuration, change agent-sandbox, providers/models/auth/CA, alter either runner's CLI/result schema, add routing proof fields, change retry budgets or downgrade all error events.
- Do not modify caller code/contracts/data/deny lists, rerun its task or accept its professional outputs.
- Do not read additional caller business materials or copy raw business history into review prompts/artifacts.
- Do not introduce dynamic stages, scheduling, a new sandbox/environment or broad compatibility machinery.

## Success signals

1. Actual read-only native-log re-collection and the sanitized startup-warning-plus-recovered-reconnect case produce completed/turn.completed with runtime/runner 0 and no reconnect rejection. Existing anomalies may correctly keep validation_status at needs_review; no promise of a clean passed business result is made.
2. Diagnostic text/locations/counts remain visible. Raw usage/wall-clock and optional-check semantics remain unchanged. Optional checks are verified with synthetic independent inputs; the original caller's professional/canary/artifact acceptance is not re-performed.
3. In recovery proof, unknown or malformed inter-start frames, execution/message frames in the gap, missing/duplicate/reversed starts, unrecovered disconnects, turn.failed, ambiguous/missing/faulty terminals/final answers, native/postprocessing nonzero, parser corruption and explicit check failures continue to reject. No new arbitrary-event exemption is introduced.
4. Existing adjacent-start recovery and ordinary non-recovery/Claude behavior remain covered by relevant regression tests.
5. Required independent review/fix/re-review gates close with accepted findings fixed, evidence/stats retained, scoped commits and a new draft PR. Final closeout states deployment limits and actual entrypoint availability accurately.

## Evidence limits / residual risk ownership

- Original artifact/canary checks and business correctness were not replayed or adjudicated: caller retains ownership; outside this work unit.
- A live forced network interruption is nondeterministic and unnecessary to isolate this parsing defect; native structural replay and equivalent synthetic cases are the required proof. Any live validation needs an explicit scoped reason, not replacement of the original business workflow.
- Future unrelated startup/event formats are outside the supported exception unless separately evidenced and authorized; collector maintenance follow-up owns such compatibility work.
- Merge/live deployment and caller restoration are separate user/caller decisions. Installed live collector remains unchanged during this work unit.

## Blocking open questions / next entry

No blocking input remains. The delegated user controller explicitly read goal.md, state.md and baseline-reproduction.json and confirmed the target, non-goals, boundaries, five success signals and residual-risk ownership. Confirmation includes narrow matching of the evidenced startup diagnostic/path variations, retaining original diagnostics and possible needs_review, controller-only raw business logs, external agents using sanitized replay only, and no merge/live authorization. Next entry is plan by the assigned GPT-6 Sol runner subprocess; ordinary gates advance automatically through draft PR and final closeout.
