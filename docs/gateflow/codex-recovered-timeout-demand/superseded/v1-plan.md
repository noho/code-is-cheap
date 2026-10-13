# Plan: recovered Codex timeout / high-demand notices

## Artifact and decision

- Gate: plan.
- Work unit: `codex-recovered-timeout-demand`.
- Artifact: `docs/gateflow/codex-recovered-timeout-demand/plan.md`.
- Binding scope: [goal-confirmation.md](goal-confirmation.md), confirmed by the user; SHA256 `ad1a4d797b8ccebb825fdd3958d21a4a101296ca28b370efccb211b92c65f5b9` at plan creation.
- Reviewed code version: HEAD/base `62c3b26adeb994e81043d7b1afbcd4c6eb8974ae` on `fix/codex-recovered-timeout-demand`.
- Preflight: correct existing work branch; no tracked changes. The untracked work-unit directory is controller-owned input/output, not unrelated production work. No nested `AGENTS.md` was found in `scripts`, `tests`, `docs` or `skills`.
- Design-document alignment: no separate design document; the confirmed contract and repository code are the design basis.
- Decision: one behavioral slice, S1, extending only exact Codex notice recognition with regression evidence and the existing README's allowlist description.
- Completion status: plan prepared; implementation and plan-review approval are pending. No production code/test changes, commits, deployment, original-evidence replay or live probes were performed by this plan agent.
- Blocking open questions: none.
- Next entry point: **plan review**, using `planreview` through the controller's independent concurrent `mimo-flash` and `ds-flash` Claude-runtime routes. The controller owns adjudication, state changes and the accepted-plan commit; this document does not advance those gates.

## Goal, motivation and success signals

Recognize the two observed exact timeout/high-demand reconnect families as recovery candidates. When the existing proof establishes successful later completion of the same execution and all selected checks succeed, retain each notice as a warning rather than mechanically reject the execution. The narrow allowlist currently rejects these messages before that proof can apply.

The confirmed success signals remain:

1. Repository and reviewed installed collectors replay the original input with the saved **native/precollection exits both 0** and selected checks, yielding outer exit 0, `agent_status=completed`, `validation_status=needs_review`, `result_status=not_assessed`, errors=0/anomalies=3/warnings=5. Preserve original notice messages/lines, the three anomalies, canary match, `canary_read_candidate=false`, and both artifact checks. Original replay is read-only and controller-only; these values come from the confirmed contract, not a replay by this agent.
2. Synthetic positives cover both exact families and coexistence with the old families. Unknown/near-match/unsupported top-level error shapes, absent recovery, invalid starts/identity/order/terminal/final, native or postprocessing failures, and explicit check failures stay rejected. The existing runner-result regression suite passes.
3. Required independent reviews and controller adjudication complete in the prescribed Gateflow order, with durable artifacts, accepted commits and a new draft PR. The user merges manually.
4. After complete review, the controller performs the already authorized component sync and installed-source equality check, then separate `mimo-flash` Codex-runtime and Claude-runtime synthetic three-step integration probes. Each probe must tool-read synthetic input, program-compute/write a new result, then tool-read it back, with actual tool events and successful process completion verified. These are ordinary integration probes; they do not reproduce a real transient network failure.

## Non-goals and scope boundary

No business task acceptance, caller anomaly adjudication, business-agent rerun, automatic retry, upstream wording normalization, generic error suppression, retry-state framework, fault injector or unrelated refactor. Do not change Claude classification, startup diagnostic recognition, supported event shapes, identity/order/terminal rules, process exits, optional checks, schema or diagnostic limits. Do not merge, approve, mark ready, request reviewers or publish external comments.

All delegated inputs must be repository code, these Gateflow documents or synthetic samples. Do not open original `portfolio-manager-v2` evidence or any original business sources referenced by `goal-evidence.json`; original replay remains controller-only. Plan/implementation/fix agents do not deploy or probe. Controller authorization and ownership are established by the delegation and confirmed contract.

## First-principles judgment and direct code evidence

At the reviewed base:

- `scripts/agent-run-result.py:49`, `recognized_codex_connection_notice`, requires exactly top-level `{type,message}`, `type=error`, a string message, and full matching of either the stream-closed or server-request-error family. Both new families currently fail recognition. Collector SHA256 is `8a0be0d0e7d472ff145ee1c691f1849f7480cadd239a9f2dfb4e43900e3a0153`.
- `Collection.codex` at `:239`/`:269` immediately records other top-level errors, but buffers recognized notice counts and physical source lines. This is the sole behavior entry point that needs the extended allowlist.
- `codex_connection_recovery_failure` at `:316` already provides the requisite start/identity/order/final/terminal/exit/no-other-errors proof. `finalize_codex_connection_notices` at `:337` turns proven candidates into warnings, or unproven candidates into errors with the existing reason prefix.
- `collect` at `:405` performs strict JSON/text validation, terminal/final checks, selected last-message/canary/artifact checks, stderr classification and process validation before notice finalization at `:512`. Classification at `:513` is rejected for errors, needs_review for anomalies, otherwise passed; `result_status` remains not_assessed.
- `scripts/codex-agent-run:503–552` captures native exit separately from final-message postprocessing, supplies both to the collector, and only then substitutes a nonzero collection exit when runtime/postprocessing succeeded. Therefore the previously rejected **outer** collector exit is not a valid substitute for saved precollection exit 0 during replay. `--detail` bypasses collection. `scripts/claude-agent-run:445–458` retains its own exit/collection path.
- `tests/test_agent_run_results.py:81–145` provides synthetic notice construction, `recovered_codex(notices=...)`, direct collector replay and report/diagnostic assertions. Existing server-retry tests at `:150–315`, start/proof tests at `:317–759`, selected-check/process helpers at `:767–863`, diagnostic-bound tests at `:865–943`, Claude/report/detail controls at `:945–1000`, and isolated installation at `:1227` cover the unchanged surrounding behavior. Fake launchers/runtime streams make no model requests.
- `README.md:396` explicitly enumerates only the two old supported families. Its generic result/ownership description and `skills/sub-agents/SKILL.md:73–96` already fit the intended behavior.
- `scripts/sync-agent-tools.sh` copies the collector alongside both runners to `${AGENT_RUN_BIN_DIR:-$HOME/.local/bin}`; no skill/profile sync is needed for this change. Reading this boundary does not authorize this plan agent to run live sync.

The defect is recognition, not missing recovery state. Appending two exact matches lets the existing proof handle the synthetic sample and the controller's confirmed replay without weakening it. A parser framework, new state machine or additional runtime ownership would add unnecessary design and drift from the confirmed repair.

## Affected files and ownership

| File/module | Allowed change and owner |
| --- | --- |
| `scripts/agent-run-result.py` | Implementer extends only `recognized_codex_connection_notice`; all `Collection`, parser, schema, limits and exit behavior remain unchanged. |
| `tests/test_agent_run_results.py` | Implementer adds synthetic builders/cases for both new families and their proof/negative boundaries, using the existing helpers. Preserve old tests; no broad test refactor. |
| `README.md` | Implementer minimally updates the existing Runner results allowlist paragraph to include the two exact full new messages and U+2019. |
| `docs/gateflow/codex-recovered-timeout-demand/` | Controller manages implementation/review/adjudication/closeout and sanitized evidence artifacts; each delegate writes only its assigned artifact. Confirmed goal/state files are controller-owned. |

The runners, launchers, `sync-agent-tools.sh`, Claude adapter behavior, profiles, catalogs, shim, skills and business repositories are read-only for S1. No new public option, schema field, dependency or production module is introduced.

## Contracts, decisions and unchanged invariants

### Exact notice allowlist

Retain the two existing full-match branches byte-for-byte. Append full matches for these **complete decoded message strings**, with one ASCII attempt digit 1 through 5, fixed ASCII `/5`, literal spaces and punctuation:

```text
Reconnecting... [1-5]/5 (request timed out)
Reconnecting... [1-5]/5 (We’re currently experiencing high demand, which may cause temporary errors.)
```

`[1-5]` above denotes the permitted digit, not literal brackets. The apostrophe in `We’re` is **U+2019 RIGHT SINGLE QUOTATION MARK**; ASCII U+0027, U+2018 and wording variants are unsupported. Equivalent JSON escaping of U+2019 decodes to the same accepted character; recognition remains after ordinary strict JSON decoding.

Implementation can append the following regex full matches directly to the existing boolean expression:

```python
r"Reconnecting\.\.\. [1-5]/5 \(request timed out\)"
r"Reconnecting\.\.\. [1-5]/5 \(We’re currently experiencing high demand, which may cause temporary errors\.\)"
```

Continue requiring exactly `{type,message}`, `type == "error"`, string `message`, and `re.fullmatch`. Do not use `\d`, substring searches, `strip`, case folding, apostrophe substitution, widened retry budgets, new UUID forms or an arbitrary reconnect reason. No attempt sequence, deduplication or exhaust-at-five policy is added: repeated/mixed notices and any allowed attempt stay candidates, as today.

### Recovery proof and data flow remain unchanged

The new candidates follow the existing collection path: decoded event → exact recognizer → candidate count/first-last source lines → all ordinary validations and selected checks → existing proof → existing diagnostic category/prefix. A recognized message alone never proves recovery.

Preserve every current predicate and its priority/reason:

1. Exactly one thread start and one turn start. Thread start has exact `{type,thread_id}`, a nonblank string identity, and is the first decoded nonblank event. Turn start has exact `{type}` and is the next event, except for zero or one already-recognized exact startup diagnostic. Thread start precedes turn start in physical lines. No new thread/turn identity fields or associations are inferred from notices, which have only type/message.
2. First candidate occurs after turn start. A single supported `turn.completed` is required, with only `type` and optional `usage`; existing omitted/nonobject usage behavior is unchanged. Missing, failed, conflicting, duplicated or unsupported-shape terminal cannot establish recovery.
3. The selected last agent message has exact `{type,item}` and item `{id,type,text}`, nonblank string id/text, and is after the **last** candidate and before completion. Earlier messages do not substitute for a valid later final. No notice may occur after final without another valid later final; events after terminal retain ordinary validation, including the existing `rate_limit_event` allowance.
4. Native exit and runner **precollection** exit are both zero; other collector error counts are zero. Strict parsing, last-message matching, canary proof and artifact checks already contribute errors before finalization and remain decisive.

Successful candidates retain the existing `Recovered Codex connection notice: ` prefix and original event representation/physical line in warnings. Unproven candidates retain `Codex connection notice recovery not proven (<existing reason>): ` in errors. Unknown top-level errors retain immediate error classification. Ordinary tool/stderr/startup anomalies continue to produce needs_review, not mechanical rejection or business acceptance.

Report keys/schema_version=1, final/session/usage/statistics/log fields, `agent_status`, `result_status=not_assessed`, and exit propagation do not change. Diagnostic display remains 20 entries/category, 2,000 characters/entry, authoritative total counts and preserved first-candidate display reservation; final display remains 12,000 characters. Nested item errors are **not** top-level recovery candidates and retain their existing anomaly/warning semantics; this repair does not invent fatal classification for every unsupported non-error event shape.

## Goal alignment

| Decision/slice/validation | Confirmed goal or necessary success condition |
| --- | --- |
| S1: append only the two exact full-match branches | Minimal recognition repair; success signals 1–2. |
| Preserve shape/digits/U+2019 and all existing proof/check/exit predicates | Confirmed narrow scope and false-acceptance negatives in signal 2. |
| Positive family/attempt/sample/mixed/anomaly tests | Demonstrate warnings for recovered execution and preserved anomalies, signals 1–2. |
| Near-match, unrecovered, identity/order/terminal, process/check negatives | Demonstrate that added recognition cannot suppress other failures, signal 2. |
| Existing suite, report/detail/Claude/diagnostic/install controls | Confirm unchanged contracts and existing behavior, signal 2. |
| README allowlist paragraph and durable Gateflow artifacts | Confirmed docs decision and reviewable delivery, signal 3. |
| Controller-only original replay, sync equality and ordinary probes | Confirmed original/installed acceptance and integration, signals 1 and 4; outside delegate execution. |

## Implementation slice S1: classify exact recovered timeout/demand notices

- Objective/expected outcome: both exact new families become warnings only when the unchanged proof passes; all other behavior remains as documented above.
- Allowed files/modules: the three production/test/doc files in the affected-files table, plus the controller-assigned S1 implementation evidence artifact under this work unit. No goal/state edits by implementer.
- Prerequisites/dependencies: independent plan reviews completed and controller-adjudicated; accepted plan checkpoint created by the controller. No runtime/provider change or other slice dependency.
- Allowed scope: two appended exact regex full matches, synthetic regression helpers/cases, and minimal README wording. Implementer chooses local test organization within these constraints; no proof changes or general test-framework refactoring.
- Interfaces/data flow/identity/state/error invariants: the contracts above are binding; this slice changes candidate recognition only, not how recovery is proved or how diagnostics/exits are emitted.
- Non-goals: all confirmed exclusions and ownership boundaries above.
- Validation: execute the S1 test matrix and focused/full runner-result commands below; record exact commands, process results, affected-file hashes and assertion evidence. Controller independently performs required original/live acceptance at its authorized gates.
- Completion signal: source diff is confined to the approved files/behavior; new tests and existing 61-test baseline coverage pass; docs reflect the exact allowlist; implementation report and classified risks are present. This signals entry to **code review**, not overall completion.
- Stop condition: a needed fix changes recovery proof, public contract, scope/ownership or confirmed acceptance; required validation is blocked/fails without an in-scope fix; or an actual scope/contract blocker appears. Report evidence to the controller. Do not expand S1, create future slices or ask the user for confirmation from this delegation.

One slice is sufficient because recognition, tests and its existing documentation form one verifiable behavior change. Splitting by file or by timeout versus demand would add gate cost without an independent behavior boundary.

## S1 synthetic tests and expected assertions

Add `timeout_notice(attempt=1)` and `demand_notice(attempt=1)` test builders (or equally small local construction) with exact strings. Use `recovered_codex(notices=...)`, `run_agent`, `run_collector`, `assert_connection_result` and `assert_report_contract`; do not modify production proof helpers. New methods may use the names below to support the focused command.

| Test method / coverage | Expected result |
| --- | --- |
| `test_codex_timeout_demand_recovered_connection_notice`: each family individually at all ASCII attempts 1–5; equivalent decoded U+2019; a notice list equivalent to `evidence/minimal-events.jsonl` (timeout attempt 2 followed by demand attempts 2–5); repeated/mixed notices including both old stream/server families | Clean case: outer exit 0, runtime_exit_code=runner_exit_code=0 with precollection exit 0, completed, passed, errors=0/anomalies=0/warnings=notice count, terminal turn.completed; original warning text/physical lines/prefix and report fields retained. Equivalent minimal sample has five warnings. Keep old family recognition unchanged. |
| Same positive method: optional recognized startup diagnostic; failed tool/stderr anomalies after starts; combined startup + failed tool + nonempty stderr with the five-notice synthetic sequence | Recovery still succeeds; combined case errors=0/anomalies=3/warnings=5, needs_review, result not_assessed. Assert anomaly text/locations, final/session/usage, raw log content and saved last-message content. Anomaly counts reflect fixture construction, not an assertion of original business equivalence. |
| `test_codex_timeout_demand_notice_lookalikes_rejected`: for **each** family, unrelated failure, prefixes/suffixes, leading/trailing/internal whitespace/newline, case/wording/punctuation changes, missing closing parenthesis, attempt 0/6/01/fullwidth/Arabic-Indic digits, budget 6/05/fullwidth 5; demand ASCII/U+2018 apostrophes; missing/null/nonstring message and extra top-level keys code/metadata/status/error | One ordinary inserted top-level error yields outer exit 1, rejected, errors=1, warnings=0 and exact ordinary diagnostic source line/message. An unknown error mixed with valid candidates rejects all candidates with the existing other-errors reason; no recovered warning. |
| `test_codex_timeout_demand_notice_recovery_fences`: run representative mutations for **both** families: missing/duplicate/malformed/reversed starts; missing/blank/nonstring thread identity; notice before turn; unsupported/multiple startup-gap diagnostics; missing/blank/nonstring/malformed-id/envelope/item final; final before last notice/after terminal; missing/failed/duplicate/conflicting/extra-field terminal; notice/event after terminal; malformed JSON/duplicate key/NaN/non-object event mixed with candidates | Rejected, no recovered warnings; candidate diagnostics retain source lines and the existing start/final/terminal/other-validation reason selected by predicate priority. Cover truncated unrecovered stream with notices but neither final nor successful terminal. Preserve existing ordinary-event behavior; do not add new generic validation. |
| `test_codex_timeout_demand_notice_keeps_selected_checks`: call existing `assert_codex_connection_selected_checks(startup, notices=[one_new_notice])` separately for both families and startup False/True, in isolated temp subdirectories | Good matching canary + actual read candidate + new regular artifact + matching last-message succeeds; mismatch/missing proof, missing/unreadable expected input, missing/nonregular/hard-linked/log-alias artifact, and missing/mismatched last-message reject. Existing prelaunch invalid canary/existing artifact still exits 2 without runtime invocation. Clear fixture environment variables via existing helper behavior. |
| `test_codex_timeout_demand_notice_keeps_process_failures`: call existing `assert_codex_connection_process_failures(startup, notices=[one_new_notice])` separately for both families and startup False/True | Native exit 7 preserved by public runner/report, agent failed/rejected; missing/raced/unsavable final-message postprocessing and direct native=0/precollection=1 stay rejected with runner exit 1. All candidates remain errors; no warnings. |
| New-family Claude/detail controls, placed in the recovery-fences method or small adjacent tests | Both new notices are fatal top-level errors through Claude collection even with successful Claude terminal; Codex --detail returns raw stdout/stderr and native 0/7 without classification. |
| Existing regression suite, unchanged | Old stream/server successes and negatives; startup diagnostic rules; ordinary Codex/Claude collection; full report contract; statistics/session/usage; parser/final/check errors; diagnostic saturation/counts/truncation; raw detail; self-contained isolated sync/install remain passing. |

Tests should use code-local synthetic identities/content, not business contents or a required dependency on Gateflow evidence files. The sample replay below separately exercises the exact saved synthetic sample. Do not turn normal tool exit 1 anomalies into process/check negatives.

Run from the repository root after implementation (these are planned commands, not claimed passes):

```bash
python3 -B -m unittest discover -s tests -p 'test_agent_run_results.py' -k timeout_demand
python3 -B -m unittest discover -s tests -p 'test_agent_run_results.py'
git diff --check
git diff -- scripts/agent-run-result.py tests/test_agent_run_results.py README.md
```

Focused tests must execute both families and the listed failure boundaries; full runner-result suite must include all original 61 tests plus the new methods. Repeat the exact synthetic replay command below against implemented code: expected recognized_notices all true, collector exit 0, completed/passed/not_assessed, native=0/runner=0, terminal turn.completed, errors=0/anomalies=0/warnings=5. Also inspect/preserve the synthetic report's warning diagnostics at lines 3–7; the baseline harness prints error lines only, which should then be empty. No production-runner edit is needed. Broader unrelated suites, skill validation and network fault simulation are not acceptance additions; run additional checks only for actual change impact or a concrete review finding.

## Actual baseline evidence

Run on the unchanged reviewed HEAD on 2026-10-13 before writing this plan. No model calls or original evidence were used.

```bash
python3 -B -m unittest discover -s tests -p 'test_agent_run_results.py'
```

Actual result: exit 0, **61 tests in 46.131s, OK**. This supports old behavior at the base; it does not validate the not-yet-implemented new allowlist.

The exact one-off synthetic baseline command was:

```bash
python3 -B - <<'PY'
import importlib.util
import json
import subprocess
import tempfile
from pathlib import Path
root = Path.cwd()
source = root / 'scripts/agent-run-result.py'
sample = root / 'docs/gateflow/codex-recovered-timeout-demand/evidence/minimal-events.jsonl'
spec = importlib.util.spec_from_file_location('synthetic_baseline_collector', source)
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
events = [json.loads(line) for line in sample.read_text().splitlines()]
print(json.dumps({'recognized_notices': [adapter.recognized_codex_connection_notice(event) for event in events if event['type'] == 'error']}, ensure_ascii=False))
with tempfile.TemporaryDirectory(prefix='codex-timeout-plan-baseline-') as directory:
    stderr = Path(directory) / 'empty.stderr'
    stderr.write_text('')
    argv = ['python3', '-B', str(source), '--runtime', 'codex', '--provider', 'mimo', '--output', str(sample), '--stderr', str(stderr), '--exit-code', '0', '--runner-exit-code', '0']
    result = subprocess.run(argv, capture_output=True, text=True)
    report = json.loads(result.stdout)
    print(json.dumps({'collector_exit': result.returncode, **{key: report[key] for key in ('agent_status', 'validation_status', 'result_status', 'runtime_exit_code', 'runner_exit_code', 'terminal', 'diagnostic_counts')}, 'diagnostic_lines': [item['line'] for item in report['errors']]}, ensure_ascii=False))
    if result.stderr:
        print(result.stderr)
PY
```

Actual command exit 0 (the harness deliberately reports the child exit), with empty child stderr and these results:

```json
{"recognized_notices": [false, false, false, false, false]}
{"collector_exit": 1, "agent_status": "completed", "validation_status": "rejected", "result_status": "not_assessed", "runtime_exit_code": 0, "runner_exit_code": 1, "terminal": "turn.completed", "diagnostic_counts": {"errors": 5, "anomalies": 0, "warnings": 0}, "diagnostic_lines": [3, 4, 5, 6, 7]}
```

Input/version applicability: collector SHA256 above; tests SHA256 `394d9e6960553dd8b046c5653ed36aed51f23e2154fe878004e518fa42881dae`; synthetic sample SHA256 `b04d258b59291ca3a7a05ea4c7d390eca9e4039f70d0d7b947f4ca64c48197ee`. Base code is retrievable from the exact commit, and the synthetic input is preserved at the linked repository path. The minimal sample has no selected canary/artifact checks and **zero** anomalies; it does not claim the original's three anomalies or selected-check coverage. Temporary stderr was empty and removed with the harness's temp directory. Hash changes or affected code changes invalidate reuse for changed assertions; implementation evidence must record the new version and actual outcomes.

## Docs decision

Update only the existing README Runner results allowlist paragraph: retain old families and their lowercase UUID constraint; add the two new complete message forms, ASCII attempts/budget and exact U+2019 apostrophe. Keep the existing distinction between mechanical completion and caller-owned business assessment. No CLI/schema change, new guide or skill update is needed; `skills/sub-agents/SKILL.md` already describes proof-gated notices generically. Gateflow implementation/review/closeout artifacts carry the regression, original replay and deployment/probe evidence.

## Residual risks and uncovered scope

| Risk/uncovered area | Classification | Owner / destination / non-blocking basis |
| --- | --- | --- |
| Current false rejection of these two exact recovered notice families | **fixed in current slice** (planned, not yet achieved) | S1 implementer + controller; completion requires reviewed code and actual S1 validation. |
| Exact upstream wording, apostrophe, attempt/budget or envelope variants outside the confirmed two families | **assigned to later work unit** | Repository maintainer; a separately confirmed repair if future evidence warrants it. Intentional narrow allowlist, not unfinished S1 acceptance. |
| Original business correctness and the retained three anomalies | **assigned to later work unit** | Caller, through its existing business adjudication workflow. This unit never accepts that business result; not_assessed and anomaly visibility persist. No original source access by delegates. |
| Actual transient network failure and vendor behavior are not injected by ordinary live probes | **assigned to later work unit** | User/controller if explicitly requested. Deterministic original-log replay covers this classification defect; ordinary probes cover live runtime/tool integration only. |

No later approved slice, linked issue or new issue is required by this plan. No unclassified residual risk or blocking open question is known. Original replay, installed equality and the two runtime probes are **pending required validation owned by the controller**, not deferred risks or something synthetic passes can replace. A concrete in-scope failure blocks its applicable gate; a repair requiring changed confirmed scope returns to the controller for goal confirmation.

## Completion report and controller continuation

The S1 implementation artifact/final report must contain:

1. Gate/work unit/slice, exact reviewed base and resulting version or file hashes, artifact path, and approved scope reference.
2. Changed files and concrete behavior; confirmation that both old full matches and the recovery predicates/schema/runners/limits are unchanged.
3. Actual validation commands, exits, test counts and observed assertion results, including both families, rejects, old controls and sample replay. Separate planned/unrun/controller-owned checks from achieved evidence; include retrievable synthetic inputs/results.
4. Docs decision/result, findings or deviations, classified residual risks/uncovered areas with owners/destinations, completion status and blockers.
5. Next entry point **code review** for S1; controller adjudicates independent reviews and dispatches accepted fixes. No delegate commit, push, sync or business task.

Controller continuation after plan review follows the mandatory Gateflow order: accepted plan commit → S1 implementation → independent code review/adjudication and applicable fix/re-review → accepted slice commit → aggregate deepreview/adjudication and applicable fix/re-review → accepted deepreview commit → ready-to-open-draft-PR → push/create draft PR → PR review/adjudication and applicable fix/re-review → accepted PR review commit/final push → draft-PR-pass → final closeout. One unchanged slice still requires the later independent aggregate/PR judgments. Controller performs the original replay read-only at repository and installed versions and records sanitized comparisons.

Final closeout must record actual verification, findings and classified risks, docs, draft PR URL, applicable issue-link status, pending/manual merge and next entry point. Record the component-appropriate deployment command below, installed collector path/hash/equality, and the two ordinary integration probe commands/results. The confirmed contract already authorizes controller live sync **after complete review**; this delegate does not execute it:

```bash
./scripts/sync-agent-tools.sh
```

Run from the repository checkout containing the reviewed approved changes. No `sync-skills.sh` or `sync-codex-agent.sh` is applicable to the planned files. Remind the user to sync to live, stating whether the authorized sync was actually completed. Reload interactive launcher functions with `source ~/.zshrc` or a new shell when deploying them; installed runner callers already on PATH do not need that reload. Do not claim a real network-fault reproduction from the ordinary probes. User merge remains manual.
