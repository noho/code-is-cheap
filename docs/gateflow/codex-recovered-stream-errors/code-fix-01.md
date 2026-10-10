# S1 code-fix-01: parser-accepted start contract and malformed-row coverage

- Gate: `fix`; work unit: `codex-recovered-stream-errors`; slice: `S1`.
- Branch: `fix/codex-recovered-stream-errors`; accepted plan checkpoint: `7c37bc6b4ef8b0e97ff63146cf66796ddc583d6e`.
- Finding: MiMo code finding 001, accepted by the controller in [code-adjudication.md](code-adjudication.md). This is distinct from historical plan finding MiMo-01.
- Authority: explicit controller S1 FIX assignment; the user-confirmed [goal.md](goal.md), frozen [plan.md](plan.md), and appended interpretation in [plan-adjudication.md](plan-adjudication.md).
- Decision/status: narrow wording/evidence/test mismatch addressed at the fix level. No production behavior change is needed. Independent re-review and accepted-finding closure remain controller-owned and pending.
- Artifact: `docs/gateflow/codex-recovered-stream-errors/code-fix-01.md`; additive validation: [implementation-validation.json](evidence/implementation-validation.json), `code_fix_01` subsection.

## Contract and exact changes

Counters cover every **parser-accepted** `thread.started`/`turn.started` dispatched to `Collection.codex()`, including duplicates and invalid recovery-proof shapes. Strict JSON/event/UTF-8 validation precedes dispatch. Parser-rejected start rows do not enter start counters or parsed-event ordinals; they independently reject the stream and must NEVER recover. Their detailed parser errors remain authoritative. With otherwise valid unique starts and final/terminal evidence, the notice's failure reason is `other collector validation errors`. Parser-accepted invalid-shape or duplicate starts continue to fail the start fence.

This preserves the confirmed goal: corrupt streams remain fatal, and no error family or protocol acceptance is expanded. Generic parsing/counting semantics, proof dispatch order and production code remain unchanged.

| Permitted file | Fix |
| --- | --- |
| `tests/test_agent_run_results.py` | Four raw malformed duplicate-start subcases in the existing same-execution method; no new methods or harness. |
| `implementation.md` | Narrow the start-counter descriptions and historical plan-finding evidence; label initial snapshot and append actual fix validation. |
| `evidence/implementation-validation.json` | Replace the broad current claim with a parser-accepted claim and scope; archive the original claim values and add fix commands, logs, counts, hashes, limits and residuals. |
| `plan-adjudication.md` | Append a clearly labeled controller-authorized interpretation; preserve all historical bytes. |
| `code-fix-01.md` | This fix handoff. |

The collector, both runners, frozen plan, goal, READMEs, repository skill, root code adjudication and MiMo report retain their pre-fix hashes. Lifecycle state/statistics were not edited. Historical original/review evidence was not changed; DS report and caller directories/logs were not accessed.

## Bounded synthetic negative evidence

The existing mock runner harness emits raw JSON rows with escaped lone surrogates; no caller fixture or business data is used. All rows below are duplicates after the valid initial starts, with the recognized notice at line 3 and successful terminal at line 6.

| Subcase | Malformed field | Placement | Retained parser-error line |
| --- | --- | --- | --- |
| `parser-rejected-duplicate-thread.started-before-final` | `thread_id` | Before selected final | 4 |
| `parser-rejected-duplicate-thread.started-after-final` | `thread_id` | After selected final | 5 |
| `parser-rejected-duplicate-turn.started-before-final` | `metadata` | Before selected final | 4 |
| `parser-rejected-duplicate-turn.started-after-final` | `metadata` | After selected final | 5 |

Each passing subcase asserts outer/report runner exit 1 and `validation_status=rejected`; one `invalid event:` diagnostic containing `surrogates not allowed` at the raw row's output line; the original notice retained as an error at line 3 with `other collector validation errors`; errors/anomalies/warnings `2/0/0`; no recovered notice warning; five parser-accepted events; native exit 0, `agent_status=completed`, `terminal=turn.completed`, and final `done`. The public report contract is also checked through the existing helper. Private start counters are not newly exposed or directly claimed as public test output.

## Actual validation and snapshot roles

Commands ran from the repository root through `/private/tmp/codex-recovered-code-fix-01-svnmn4da/record_command.py`. Exact argv, UTC times, measured duration, stdout/stderr hashes and tested product hashes are retained in the additive evidence and matching private JSON/log files.

| Actual command | Exit | Methods | Measured seconds | Unittest seconds |
| --- | --- | --- | --- | --- |
| `python3 -B tests/test_agent_run_results.py RunnerResults.test_codex_connection_notice_requires_same_execution_completion` | 0 | 1 | 4.725723 | 4.680 |
| `python3 -B tests/test_agent_run_results.py` | 0 | 49 | 27.605337 | 27.559 |
| `git diff --check` before final evidence writes | 0 | — | 0.018095 | — |

Both test commands reported `OK`, zero failures/errors. The module remains 49 methods: 38 baseline + 11 initial S1 additions; this fix adds four subcases and zero methods. Its existing sync fixture targets a private temporary directory and uses mock runtimes. No live install/sync/deploy or model/API/provider execution occurred.

Scope checks in `/private/tmp/codex-recovered-code-fix-01-svnmn4da/scope-check.json` verify 49 methods, only the assigned test method's AST changed, append-only adjudication, and unchanged protected-file hashes. The final `git diff --check` is recorded after final evidence/artifact writes in `diff-check-final.json`; finalized file sizes/hashes and preservation checks are in `final-snapshot.json` in the same private directory.

| Hash role | SHA256 / location |
| --- | --- |
| Initial implementation test snapshot | `a5dc6f5d985e27cc5861af3d147ddcd09e202c613501b0106eac162bbdb90a58` |
| Test file actually exercised by both fix runs | `a9fa04ed87c4d39faceab429bab4879bc6a3b4de152631e952bffa67fe114152` |
| Unchanged production collector | `0301f6dd9f589b7b705aa5e2f5033b573a2bfce23f0ae2ca23b40c374dab06e4` |
| Initial implementation-validation snapshot | `458ac40d2e4e5b7afbb3f85b111cf0fb10d96a51ed7976a520d0ec43304f34b8` |
| Updated implementation/evidence/adjudication/fix artifact | Additive `post_fix_sha256` plus external finalized `final-snapshot.json`; final evidence/artifact hashes are external to avoid self-reference. |

The complete initial evidence is archived under the private `initial/` directory. Original top-level command records, replay data, timestamps, product hashes and historical statuses are preserved; the two clarified original claim values are retained under `code_fix_01.initial_snapshot.clarified_claims`. The initial original replay was not rerun, and its optional/business limits remain unchanged. This fix uses synthetic material only.

Docs decision: clarify task evidence and the appended adjudication contract; no README/skill, frozen plan or historical review rewrite is authorized or performed.

## Classified remaining risks and incomplete items

| Residual / uncovered area | Classification | Owner / destination / basis |
| --- | --- | --- |
| Start-counter wording/evidence mismatch and raw malformed-start coverage | fixed in current slice | S1 fix owner; controller / S1 independent re-review. Four negatives and full regression pass; independent finding closure pending. |
| Unsupported notice/proof variants and generic protocol-validation weaknesses | assigned to later work unit | Runner/protocol maintainer / Separately confirmed evidence-backed protocol or collector validation work. Conservative recovery fence and generic semantics unchanged. |
| Original optional checks and business correctness | requiring new issue or explicit user decision | Caller/controller / Original task workflow. No original raw/business read or replay in this fix; historical replay remains structural-only evidence. |
| Merge, live deployment and original workflow restoration | requiring new issue or explicit user decision | User/caller / Later authorized controller or original workflow. Outside fix scope. |

No unresolved fix validation failure, blocking fix question or unclassified residual remains. Independent dual re-review, controller lifecycle/statistics/adjudication updates, review-loop closure and any accepted slice checkpoint remain incomplete and controller-owned. No staging, commit, push, delegation, workflow operation or installation was performed by this fix assignment.
