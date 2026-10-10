# S1 implementation: Codex recovered stream errors

- Gate: `implementation`; work unit: `codex-recovered-stream-errors`; slice: `S1`.
- Status: implementation and authorized validation complete; next unfinished gate: `code review`, owned by the controller.
- Branch: `fix/codex-recovered-stream-errors`; accepted plan checkpoint: `7c37bc6b4ef8b0e97ff63146cf66796ddc583d6e`; baseline: `20fc6c37751836329143567c166990bdffa9de3c`.
- Binding inputs: [goal.md](goal.md), [plan.md](plan.md), and root [plan-adjudication.md](plan-adjudication.md), including the non-proof-event and every-parser-accepted-start-counter clarifications. Verified plan SHA256: `15973171479f64c0820d82f6b57fc982e7f75fa920f06de45a55660f50e8401d`.
- Scope: D1-D4 only, a collector correction plus the approved named synthetic matrix and short classification docs. No scope change or blocking question.
- Artifact: `docs/gateflow/codex-recovered-stream-errors/implementation.md`; sanitized validation: [evidence/implementation-validation.json](evidence/implementation-validation.json).

The implementation handoff, command statistics and replay below describe the initial S1 snapshot. The start-counter wording is clarified under controller-authorized code finding MiMo 001; [code-fix-01.md](code-fix-01.md) and the additive `code_fix_01` evidence subsection record the subsequent fix and actual reruns separately. Initial product hashes and command/replay records remain historical evidence.

## Exact owned changes and behavior

| File | Change |
| --- | --- |
| `scripts/agent-run-result.py` | Exact notice helper, private bounded proof/candidate state, Codex bookkeeping, proof/finalization methods and one finalization call immediately before existing validation. |
| `tests/test_agent_run_results.py` | Eleven approved named tests in existing `RunnerResults`, using existing mock runners and direct collector calls for selected process/check controls. Existing 38 baseline methods unchanged. |
| `README.md` | One sentence describing proven recovered notice warnings and fatal unknown/unrecovered errors. |
| `README.zh.md` | Matching Chinese classification sentence. |
| `skills/sub-agents/SKILL.md` | Matching clarification in repository diagnostic guidance. |
| `docs/gateflow/codex-recovered-stream-errors/implementation.md` | This implementation handoff. |
| `docs/gateflow/codex-recovered-stream-errors/evidence/implementation-validation.json` | Actual command/exit/count/time records and sanitized assertions/replay controls. |

D1 matches only exact top-level `type`/`message` envelopes and the full literal ASCII `1..5/5` connection-notice grammar, without trimming or coercion. Only attempt 1 is observed; attempts 2-5 are synthetic grammar controls. All unknown errors retain immediate fatal handling.

D2 counts every parser-accepted thread/turn start, including duplicates and frames with invalid recovery-proof shapes. Strict JSON/event/UTF-8 validation precedes `Collection.codex()` dispatch: parser-rejected rows never reach these counters, remain independent fatal errors, and can never recover. D2 retains initial ordinals/physical lines, supported named-frame validity, selected last completed message validity, and complete first/last/count notice state while retaining at most 20 candidate events. Post-start non-proof event kinds retain baseline handling; no kind whitelist is added. Proof shape flags do not change ordinary streams without candidates.

D3 requires unique valid initial starts, the unique supported success terminal, and ordered starts/notices/selected final/terminal, using the last notice even beyond retention. Native and precollection exits must both be zero. All existing parsing, final/last-message, selected checks, stderr and process diagnostics run first; every preexisting hard error remains authoritative. Recovery does not depend on usage, time, tool visibility or zero anomalies. Failure reasons follow the approved start/candidate/terminal/final/process/other-check order.

D4 computes proof once before emitting diagnostics. Proven notices become warnings; unproven candidates become errors with a reason and original message/line. Finalization precedes existing validation. A full target category loses its last displayed entry once to reserve the first candidate; no error/count subtraction or truncation-flag reset occurs. Complete totals and baseline display caps remain. The prior diagnostic stream is restored. Existing 29 report keys, status/exit propagation, final/log/statistics handling, selected checks, Claude behavior and detail mode remain in place; no runner or routing change is needed.

Pre-existing controller dirtiness in `state.md` is preserved and excluded from owned changes. No goal/plan/adjudication/state/statistics/review file, runner, config or installed file was edited; no staging, commit, push, PR, delegation, live installation/deployment or API/business run occurred. The user's explicit S1 boundary overrides Gateflow's later automatic gates; this handoff does not claim code review, accepted slice checkpoint or final closeout.

## Actual validation

Exact argv, UTC start/end times, elapsed measurements and method counts are stored in the sanitized JSON. Commands were executed from the repository root through the private recorder at `/private/tmp/codex-recovered-s1-qm8nf4wb/record_command.py`. The top-level recorder command is `python3 -B /private/tmp/codex-recovered-s1-qm8nf4wb/record_command.py <label> <recorded argv>`; its subprocess command is recorded verbatim, including the required full-module invocation.

| Run | Exit | Test methods | Measured seconds |
| --- | --- | --- | --- |
| `focused` | 1 | 11 | 11.502783 |
| `original-replay` | 0 | — | 0.052498 |
| `focused-corrected` | 0 | 11 | 12.349329 |
| `full-module` | 0 | 49 | 27.989576 |
| `bounds-final` | 0 | 1 | 0.643808 |
| `full-module-final` | 0 | 49 | 28.216993 |
| `diff-check` | 0 | — | 0.017489 |

- Focused named matrix: 11 methods passed; attempt/shape/order/parser/final/selected-check/process/display/Claude/contract/detail assertions passed. Final strengthened bounds assertions also passed independently.
- Required final command: `python3 -B tests/test_agent_run_results.py`; 49 methods passed (38 baseline + 11 new), unittest-reported 28.176s. Its existing sync fixture writes only its private temporary destination and invokes mock runtimes; no host/live sync.
- `git diff --check`: exit 0. No additional syntax/static suite was needed after actual collector import and full module execution.
- Initial focused run had ten test assertion errors from assuming optional last-message output and one macOS resolved-path assertion failure. Explicit unique last-message destinations and a resolved artifact-path assertion corrected them. Subsequent focused/full runs passed; no unresolved effect. A final narrow test change added explicit overflow report/outer-exit assertions and triggered the recorded bounds/full reruns.

### Authorized original replay and limits

Actual command: `python3 -B /private/tmp/codex-recovered-s1-qm8nf4wb/replay_original.py`, exit 0. The script imports the actual amended `Collection`, reads only the four exact original filenames in the authorized index, and records structural controls, equality/hashes and native usage. It never emits raw final/tool/business payloads or executes log commands. The optional second owned review log was not used.

Supplied native/precollection inputs are `0/0`; original `canary_file=None`, `canary_expected=None`, `artifact=[]`. The archived runner exit 1 already contains the bug and is not a process input. The replay proves 211 parsed events, line 193 warning, final line 210, terminal line 211, errors/anomalies/warnings `0/5/1`, `completed/needs_review`, runner 0. Native final text equals event/saved/archive text (421 characters; only SHA256 persisted); usage, metrics, five anomalies, tool totals and log paths are preserved. All four source hashes match the authorized index before/after and remain unchanged.

`1271.418953` is the archived measured runner wall value supplied to the collector, not replay timing; actual replay duration is separately recorded above. Original optional/business validation is intentionally omitted and is not claimed. Selected mechanical checks are independently exercised with synthetic inputs. No model/API calls or original task reruns were used for validation.

## Docs decision and accepted finding status

The approved one-sentence clarification is present in both READMEs and repository skill only. No installed skill or setup/sync documentation change.

All five accepted plan findings were closed at the accepted plan checkpoint. The following implementation fixes are supported by actual automated evidence; independent code-review/re-review acceptance remains the controller's next gate.

| Finding | Adjudication / implementation fix status | Evidence |
| --- | --- | --- |
| DS-1 | accepted / 已修复 | Required full module: 49 methods = 38 baseline + 11 new; exit 0 |
| MiMo-01 | accepted as clarification (option a) / 已修复 | Supported proof shapes; 17 named extra-field/preamble negatives with paired baseline controls; all parser-accepted start events counted, including invalid-proof-shape duplicates after valid starts; parser-rejected rows independently fatal; no non-proof kind whitelist |
| MiMo-02 | accepted / 已修复 | Exact six-line mixed-order fixture rejects, counts 2/0/0, notice B line 5; last notice beyond retained 20 also rejects |
| MiMo-03 | accepted / 已修复 | Literal full 29-key set and four invariant values on six required recovery/failure/Codex/Claude controls |
| Controller-01 | accepted / 已修复 | One-time reservation retains first notice and first 19 old entries; full 45/48/44 counts, display 20, persistent long-message truncation flag |

## Classified residuals / owners

| Residual or uncovered area | Classification | Owner / destination | Nonblocking basis |
| --- | --- | --- | --- |
| Known notice rejection, complete proof, diagnostic visibility and regression contract | fixed in current slice | S1 implementer; controller verifies at code review / codex-recovered-stream-errors code review | D1-D4 implemented; focused/full/replay assertions passed; independent review pending |
| Unobserved notice wording/budgets, added proof-frame fields, preambles/items between starts, repeated starts and final before last notice | assigned to later work unit | Runner/protocol maintainer / Separately confirmed evidence-backed protocol-variant work unit if warranted | Conservative recovery fence intentionally refuses unsupported proof; ordinary no-candidate streams retain baseline handling |
| Generic validation of non-proof event kinds or unrelated no-candidate protocol weaknesses | assigned to later work unit | Runner/protocol maintainer / Separately confirmed collector protocol-validation work unit if needed | Binding controller clarification forbids a new kind whitelist or generic hardening in S1 |
| Original optional checks and business correctness | requiring new issue or explicit user decision | Caller/controller / Original task workflow | Nonblocking under binding named-input limit: original optional checks intentionally omitted; selected checks independently covered by synthetic fixtures |
| Merge, live deployment and original workflow restoration | requiring new issue or explicit user decision | User/caller / Later controller workflow or original task workflow | Outside S1 authorization; no merge, deployment or restoration performed |

No unclassified residual or unresolved implementation validation failure remains. Next entry point is controller `code review` of this S1 diff and these artifacts; review/fix/re-review and any accepted slice commit remain outstanding.

## Controller-authorized S1 code-fix-01 addendum

MiMo code finding 001 is addressed at the fix/evidence level by clarifying the parser-accepted-start boundary above, appending the controller-authorized interpretation to `plan-adjudication.md`, and adding four raw malformed duplicate-start subcases to the existing `test_codex_connection_notice_requires_same_execution_completion`. Independent re-review and finding closure remain controller-owned and pending. See [code-fix-01.md](code-fix-01.md).

The new synthetic rows contain a lone surrogate in `thread.started/thread_id` or `turn.started/metadata`, placed before or after the selected final and before the terminal. Each subcase asserts the retained parser error at output line 4 or 5, the notice's `other collector validation errors` reason at line 3, rejected/runner 1, errors/anomalies/warnings `2/0/0`, five parser-accepted events, and preserved native exit 0/completed/final/terminal facts. No production collector, runner, generic parsing/counting rule, notice family, README or skill changes are part of this fix.

Actual fix checks, separately recorded from the initial implementation runs:

| Run | Exit | Test methods | Measured seconds |
| --- | --- | --- | --- |
| `focused-fix-01` | 0 | 1 | 4.725723 |
| `full-module-fix-01` | 0 | 49 | 27.605337 |
| `diff-check-before-evidence` | 0 | — | 0.018095 |

Exact argv, UTC times, log hashes and results are additive under `code_fix_01` in [evidence/implementation-validation.json](evidence/implementation-validation.json); raw validation logs are retained in `/private/tmp/codex-recovered-code-fix-01-svnmn4da`. The focused command is `python3 -B tests/test_agent_run_results.py RunnerResults.test_codex_connection_notice_requires_same_execution_completion`; the full command is `python3 -B tests/test_agent_run_results.py`, with unittest reporting 49 methods/27.559s/OK. Method count remains 38 baseline + 11 original S1 additions; this fix adds only four subcases. The existing sync test used its private temporary destination and mock runtimes; no live sync or deployment occurred.

The final diff check and finalized file hashes are recorded separately in that private directory as `diff-check-final.json` and `final-snapshot.json`, after this addendum and evidence are written. Initial product hashes, command statistics and original replay remain the initial snapshot; the replay was not rerun and no caller original/raw/business files were read. Existing classified residuals retain their owners/destinations; no unresolved fix validation failure or new unclassified risk is introduced.
