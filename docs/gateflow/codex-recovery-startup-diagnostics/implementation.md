# Implementation: Codex recovery startup diagnostics

## Gate, authority, and status

- Work unit: `codex-recovery-startup-diagnostics`; gate: implementation; approved slice: **S1 only**.
- Branch observed: `fix/codex-recovery-startup-diagnostics`.
- Implemented the confirmed goal and approved plan. Implementation and required deterministic validation are complete; controller review/adjudication and original read-only structural replay remain pending.
- No agents were dispatched and no Git mutation, real provider call, business task, original-log access, live installation, or deployment was performed. The existing controller-owned modification to `state.md` was present at entry and was not edited.

## Changed files and decisions

| File | Change |
| --- | --- |
| `scripts/agent-run-result.py` | Added the pure exact startup recognizer, one internal counter, proof-only counting before ordinary Codex dispatch, and the bounded turn-ordinal equality. |
| `tests/test_agent_run_results.py` | Added the diagnostic builder and four adversarial startup tests; shared the existing selected-check, process-failure, and diagnostic-bounds assertions between adjacent and startup-gap tests; extended raw detail-mode assertions. |
| `docs/gateflow/codex-recovery-startup-diagnostics/implementation.md` | Recorded implementation decisions, actual validation outcomes, evidence limits, and handoff. |

The recognizer requires exactly the approved envelope/item keys and types, a nonblank string ID, the full case-sensitive diagnostic prefix, and a `re.fullmatch` of the approved ASCII absolute POSIX `config.toml` grammar. Directory components `.` and `..` are explicitly rejected. Paths are lexical payload and are never opened or normalized. The suppression setting is recognized as diagnostic text only.

The counter increments only when exactly one thread start and zero turn starts have been collected. The first recovery fence now requires the count to be zero or one and `turn_start_ordinal == 2 + startup_diagnostics_before_turn`. The first-thread, unique-valid-start, physical order, reconnect placement, final, terminal, parser, selected-check, and zero-exit fences and their failure reasons remain unchanged. The counter is neither reset nor serialized nor inferred from display-limited diagnostics.

Ordinary startup dispatch still records the original item as an anomaly. Reconnect recognition, report schema, statistics, counts, retention limits, runner routing, and Claude handling were not changed. Accepted startup-gap recovery therefore remains `completed` / `turn.completed` / `needs_review`, with business result `not_assessed`.

No design change or blocking conflict was encountered. The combined expected-tool-failure case explicitly passes `--last-message` with a fresh temporary destination, asserts the retained destination path, and reads back `OK`, as required by the controller clarification.

## Actual validation outcomes

All commands ran from the repository root. No test was skipped or weakened to obtain a pass.

| Command / execution | Exit | Observed outcome |
| --- | --- | --- |
| `python3 -B tests/test_agent_run_results.py RunnerResults.test_codex_startup_diagnostic_recovery_and_controls RunnerResults.test_codex_startup_diagnostic_lookalikes_do_not_bridge_gap RunnerResults.test_codex_startup_diagnostic_gap_order_and_count RunnerResults.test_codex_startup_diagnostic_keeps_recovery_fences -v` — first run | 1 | 4 tests in 6.415s; 1 test failure comparing macOS `/var` and canonical `/private/var` temporary destination spellings. The other 3 tests passed. |
| Same focused command — after fixing that assertion to compare the destination with `last.resolve()` | 0 | 4 tests in 9.238s; all passed, including accepted path/ID/reconnect variations and the saved `OK` combined case. |
| `python3 -B tests/test_agent_run_results.py` | 0 | 56 tests in 41.444s; all passed. Includes both adjacent and startup variants of selected checks, process failures, bounds, raw detail behavior, ordinary Codex/Claude behavior, and temporary installed-adapter validation. |
| `git diff --check` — before and after writing this artifact | 0 on both runs | No whitespace diagnostics. |

The macOS path assertion correction was confined to test expectations; it changed no matching policy or product behavior. The full suite uses deterministic fake runtime functions. Its installation check writes only its temporary test destinations and does not install the collector live.

Each fixture was additionally replayed directly with this actual command, substituting the three filenames below:

```sh
python3 -B scripts/agent-run-result.py --runtime codex --provider mimo --output docs/gateflow/codex-recovery-startup-diagnostics/evidence/<fixture> --stderr /dev/null --exit-code 0 --runner-exit-code 0 --wall-clock-seconds 2698.161843
```

| Sanitized fixture | Collector/native/runner exits | Status / terminal | Events | Errors / anomalies / warnings | Retained output lines |
| --- | --- | --- | --- | --- | --- |
| `startup-warning-recovered.jsonl` | 0 / 0 / 0 | completed, needs_review / turn.completed | 6 | 0 / 1 / 1 | Startup anomaly 2; recovered warning 4. |
| `adjacent-starts-recovered.jsonl` | 0 / 0 / 0 | completed, passed / turn.completed | 5 | 0 / 0 / 1 | Recovered warning 3. |
| `startup-warning-no-retry.jsonl` | 0 / 0 / 0 | completed, needs_review / turn.completed | 5 | 0 / 1 / 0 | Startup anomaly 2; no recovered warning. |

All direct replays reported final `OK`, wall clock `2698.161843`, and the unchanged usage dictionary: `input_tokens=12848965`, `cached_input_tokens=12536064`, `cache_write_input_tokens=0`, `output_tokens=102201`, `reasoning_output_tokens=45179`. The fixture tests also assert unchanged schema/key set, `not_assessed`, final character count 2, no final/diagnostic truncation, session `synthetic-thread`, zero tool results, empty runtime metrics/artifacts, canary `not_run`, exact retained JSONL text, and exact anomaly dictionaries and warning locations.

The seven-event combined expected-command-failure regression passed through the public fake runner with exits 0, completed/turn.completed/needs_review, no errors, two unchanged anomalies at lines 2 and 4, one recovered warning at line 5, one tool result, and saved/event final `OK` agreement.

Adversarial coverage exercised supported paths/IDs and attempts 1–5/multiple notices; message, envelope, ID, extra-field, and path lookalikes; arbitrary gap frames alone and on either side of the supported diagnostic; zero/one/two/25 diagnostic counts; lifecycle multiplicity, shape and ordering; blank physical lines; invalid JSON, duplicate keys, nonfinite numbers, escaped lone surrogates and nonobjects; failed/missing/conflicting/extra-field terminals; invalid/misordered finals/notices and saved-final mismatch; unknown/unrecovered errors; native and pre-collection failures; all existing runner postprocessing modes; selected synthetic check success and failures; and saturated diagnostic categories with 25 reconnect notices. Display retention did not confer proof credit. No-retry unsupported warnings retained their ordinary anomaly semantics, and unknown top-level errors remained fatal.

Fixture SHA256 values matched before and after validation (both `shasum -a 256` executions exited 0):

| Fixture | SHA256 |
| --- | --- |
| `startup-warning-recovered.jsonl` | `14ffc9ecc55a741741883424a518b679c8a3df7b26af2db3050938ccb30a50a7` |
| `adjacent-starts-recovered.jsonl` | `3af911f77b3edbcf15619167a183a40d99e73a7c5db8f32b02fb99323a56745d` |
| `startup-warning-no-retry.jsonl` | `71d3a994041e194e837c80d375ee8bc49675459a5422124fd4a04992b82910de` |

## Docs decision

No product documentation change is needed, following the approved plan: no new flag, report field, configuration action, or operator workflow is introduced. The precise lexical/count policy is recorded in the helper comments, regression tests, plan, and this artifact. No warning-suppression advice was added. No README or other product file was edited.

## Uncovered areas and residual risks

| Area / risk | Classification | Owner / destination |
| --- | --- | --- |
| Evidenced single startup frame was incorrectly rejected; narrow matching and gap accounting needed protection against overmatching. | Fixed in current slice; deterministic validation passed, independent review pending. | Root controller: adjudicate independent review and any scoped fixes before acceptance. |
| Original native structural replay has not been performed by this implementer. | Required controller validation pending; not claimed complete. | Root controller: final authorized read-only replay, retaining original diagnostic/statistical evidence. Report conflicting evidence rather than broadening S1. |
| Future native fields/text/path formats, Unicode/space-containing directories, or multiple startup warnings are intentionally unsupported recovery gaps. | Assigned to later work unit; nonblocking maintenance boundary. | Collector maintenance owner through root controller: separate evidence-backed compatibility issue. Zero-or-one remains deliberate. |
| Original artifact/canary checks and business/professional acceptance were not replayed or adjudicated. Synthetic selected checks passed only within the fake harness. | Assigned to later work unit; explicitly outside this slice. | Caller/business controller: caller-owned validation. `not_assessed` and technical `needs_review` confer no business acceptance. |
| Live forced reconnect, merge, installation, deployment, and caller restoration were not exercised. | Assigned to later work unit. | User/deployment controller: separate authorization and deployment decisions; temporary test installation does not establish live availability. |

No unresolved implementation or validation blocker remains. Next entry: root-owned independent review/fix/re-review and original structural replay, followed by its Git/PR and gate actions. This artifact does not declare those gates closed.
