# Plan fix 01: Codex recovered stream-error classification

- Gate: `fix` after controller plan-review adjudication; document fixes completed, independent `re-review` pending.
- Work unit: `codex-recovered-stream-errors`.
- Artifact: `docs/gateflow/codex-recovered-stream-errors/plan-fix-01.md`.
- Binding scope: [goal.md](goal.md), already user-confirmed; no new goal confirmation or acceptance criterion.
- Branch: `fix/codex-recovered-stream-errors`; HEAD remains `20fc6c37751836329143567c166990bdffa9de3c`.
- Changed repository files: [plan.md](plan.md) and this report only. Production implementation has not begun.
- Decision authority: [plan-adjudication.md](plan-adjudication.md); all five findings retain `accepted` adjudication. This report does not update controller state, statistics or adjudication files.
- Valid review inputs: [DS review](../../reviews/plan-review-20261011-033016.md) and [MiMo review](../../reviews/plan-review-20261011-034538.md), plus [Controller-01 evidence](evidence/controller-diagnostic-cap-check.json). The interrupted/unaccepted first report supplied no findings or review-pass evidence.
- Preflight: work branch already exists; no tracked changes; existing untracked work-unit artifacts and three supplied review paths have explicit ownership from this assignment. No branch creation, stage, commit or push was needed or performed.

## Per-finding fix evidence

Statuses below concern the **plan-document fix**, not production behavior or independent review-loop acceptance. Each is `已修复` at this gate, with final verification reserved for the next independent `re-review` and controller closure.

| Finding | Status / goal mapping | Applied fix and durable plan evidence | Validation and remaining proof |
| --- | --- | --- | --- |
| DS-1 | `已修复`; G4/G5 shared collector regression protection | S1 completion signal now requires all 38 existing test methods plus new cases. The validation command is `python3 -B tests/test_agent_run_results.py` without test selectors; the previous incomplete 16-test existing subset was replaced. Focused new-case execution remains supplementary. See plan **S1** and **Validation design and commands**. | AST confirms 38 baseline test methods and the unfiltered command in the revised plan. The whole module is deliberately **not run in this fix assignment**: its existing isolated sync/install fixture is not authorized here. It is required after S1 implementation, using local mock runtimes/private temporary destinations, with no host installation or live/API probe. No full-module pass is claimed. |
| MiMo-01 | `已修复`; G1/G3 conservative evidence, G5 ordinary-stream preservation | D2 explicitly selects **option (a)**: strict supported-shape recovery fence, not universal Codex schema/protocol invariants. D1's exact `re.fullmatch` grammar remains ASCII attempts `1..5/5`; only `1/5` is observed, `2..5` synthetic. The named supported-shape table independently covers extra fields on notice, thread start, turn start, terminal, final envelope and final item, plus preamble-before-start and item-between-starts. Paired no-candidate controls preserve baseline behavior. Extra fields/preambles/resume/final-order false negatives are classified. | 15 literal grammar checks passed; 17 actual baseline collector no-candidate extra-field/preamble controls all remain `passed`/0, with unchanged contract. These checks establish baseline controls and the grammar boundary, not the future amended proof helper. S1's named `test_codex_connection_notice_supported_shape_fence` must establish the recovery refusals and no-candidate parity. |
| MiMo-02 | `已修复`; G1 subsequent completion, G3 ambiguity rejection | D3 expressly requires `last_notice < selected_final`, including candidates beyond retention. Named `test_codex_connection_notice_mixed_order_rejected` fixes the six-line sequence: starts at 1/2, notice A at 3, final at 4, notice B at 5, terminal at 6. Assertions: rejected/report/collector/outer exit 1, exactly two notice errors, no recovered warning, and late notice B's original message at `stream=output`, `line=5`. | The clean ordering formula is true and the mixed formula false; the actual baseline mixed fixture rejects and retains the existing report contract. This baseline rejection does not prove the amended classifier; S1 must assert both candidates and line 5 through actual collector/runner paths. |
| MiMo-03 | `已修复`; G5 report/status preservation | Plan **Frozen complete report contract** enumerates the literal complete **29-key** baseline set. Set equality catches omissions/additions; freeze `schema_version=1`, `source=subagent_report`, `result_status=not_assessed`, `tool_evidence_scope=recorded_events_only`. Require clean/anomaly recovery, proof-failure including mixed order, ordinary Codex success, Claude success and Claude error controls. Named `test_agent_run_report_contract` is in the focused command. No proof/model/route field or schema bump. | AST comparison matches all 29 baseline return keywords to the plan's literal set. Six actual baseline controls (Codex clean/anomaly/known-notice failure/mixed failure and Claude clean/error) retain all keys and the four values. Amended recovery controls are explicitly required in S1; no product change or recovery-contract test pass is claimed now. |
| Controller-01 | `已修复`; G2 notice visibility, G3 complete failure evidence, G5 bounds/contract | D4 calculates proof first. With a retained candidate and target list exactly `DIAGNOSTIC_LIMIT`, remove only its **last displayed entry once**, then emit retained pairs in candidate order through existing `note()` and add only `candidate_count - len(retained_pairs)` for overflow. Never decrement counts, reset `text_truncated`, change `note()`, or repeatedly evict. At least the first notice's message/line is displayed; preserve first 19 old entries, full totals, cap 20, text cap 2000, final cap 12000 and existing truncation formula. Exact success/failure/saturation fixture table fixes the controller counterexample; no priority framework or public field. | Eight private arithmetic cases using actual baseline `Collection.note()` passed. 20 old warnings + 25 candidates => warnings **45**, display **20**, first notice line **23**, one eviction and first 19 old entries preserved. Failed category 20+25 => errors **45**, display **20**, first notice line **23**, all 20 preexisting errors counted. Overflowed failures 23+25 => **48**, display **20**, notice line **26**, all 23 old counts retained. Evicted long old warning/error fixtures keep `text_truncated=True`. Proof inputs in this experiment are explicit fixture values; integrated S1 saturation tests must validate production proof-before-emission and status behavior. |

## Contradictions resolved in the plan

1. **Frame shape versus protocol claims:** option (a) now identifies intentionally supported evidence, with named false-negative limitations. Unknown shapes refuse recovery; ordinary no-candidate streams retain baseline acceptance. There is no generic Codex validator or newly asserted universal invariant.
2. **A bounded list versus required notice visibility:** the single reservation displaces one last displayed old entry while preserving all counts and flags. This is the smallest mechanism that satisfies G2 without weakening G3/G5. Proof reads full existing errors before any display mutation.
3. **Historical prototype versus production evidence:** the prior subclass recomputed fields after `super().collect()`; the plan now states that it does not prove the production finalization-before-validation insertion or amended outer-runner success. Historical 58-case evidence is not claimed to cover the new saturated/shape/mixed/key-set cases.
4. **Subset coverage versus DS-1:** the whole-file command and completion condition replace the incomplete existing-test subset. The existing private-temp sync fixture belongs only to that later offline S1 run; this assignment performs no installation/sync or full-module execution.
5. **Gate progression versus current authority:** the revised plan and this report hand off at `re-review`, followed only on pass by `accepted plan commit`, then implementation. Prior wording sending the controller back to initial `plan review` or allowing this owner to continue further is removed. Controller state/statistics stay untouched.

Every decision serves G1-G5 as identified in the table. One behavior slice remains; no new scope, future slice, acceptance criterion, schema, shell downgrade path, retry layer or business validation has been introduced.

## Validation performed

Private experiment directory: `/private/tmp/codex-recovered-plan-fix-l5z6d88i`.

Executed command:

```bash
python3 -B /private/tmp/codex-recovered-plan-fix-l5z6d88i/check_plan_fix.py
python3 -B /private/tmp/codex-recovered-plan-fix-l5z6d88i/check_artifacts.py
```

Durable private evidence: `check_plan_fix.py`, `experiment-results.json`, `check_artifacts.py`, `validation.json`, `plan-before.md`, `edit_plan.py` and narrowed `repository-before.json`. The script imports the actual unchanged adapter, calls `Collection.note()` for diagnostic arithmetic and `Collection.collect()` only on newly created synthetic files. It performs no native runtime/provider invocation, shell runner, sync/install, original-log replay or original-task execution.

| Check | Result / interpretation |
| --- | --- |
| 8 diagnostic reservation/count/truncation cases | All assertions passed; exact counts/display/first-candidate lines and one-or-zero eviction recorded in `experiment-results.json`. Explicit proof fixture inputs; no amended production proof. |
| 6 baseline report-contract controls | All 29 keys and four frozen values match; baseline clean/anomaly/failure/Claude behavior observed, including baseline known-notice rejection. |
| 17 baseline ordinary-stream controls | Added `metadata`/`status`/`error` at each of five frame positions plus two preamble/order variants remain accepted without a recognized candidate. No new universal frame validation inferred. |
| 15 matcher checks | Five ASCII attempt values match; ten prefix/suffix/newline/case/budget/Unicode/wording variants do not. |
| 2 physical-order formula checks | Clean post-notice final passes the formula; notice/final/notice/terminal fails because last notice 5 follows final 4. Specification checks only. |
| AST contract/module check | Baseline report has 29 keys; revised literal set equals the actual return keywords. Existing test module has 38 methods; revised plan includes the unfiltered full-file command. |
| Whitespace, links, branch/HEAD and write-boundary checks | Checked after report creation; results retained in private `validation.json`. Required input/product/state/statistics hashes remain unchanged; no tracked production diff. |

Because both artifacts are untracked, whitespace validation also uses `git diff --no-index --check /dev/null <artifact>`; its exit 1 with no diagnostic output indicates the expected content difference, not a whitespace error. The first private validation-harness run incorrectly required exit 0; the harness was corrected to accept that documented status only with empty output, and the final artifact checks passed. No repository fix was needed for that harness error.

Full implementation validation, public-runner recovery, full-module regression and original scoped replay remain required in S1 after accepted-plan checkpoint. They were not performed here and must not be inferred from private feasibility checks. Original optional inputs and business correctness remain unassessed.

Scope audit: the initial integrity snapshot unnecessarily computed hashes of 273 repository files, including the unaccepted first review. Its text was never displayed, analyzed or used as review evidence. Before experiments, the snapshot/check scope was narrowed to 11 authorized input and protected-boundary files; no further access to that report occurred. This boundary deviation is disclosed, with subsequent checks corrected. No original external logs or caller business material were read.

## Scope and docs decision

Current writes are exactly `plan.md` and `plan-fix-01.md`; private synthetic files are outside the repository. The shell runner already passes the correct native/precollection exits and propagates collector rejection, so no runner implementation is proposed. No production, test, README, installed skill, controller state/statistics, evidence or review report was changed.

The existing S1 docs decision remains the minimum classification sentence in `README.md`, mirrored in `README.zh.md` and repository `skills/sub-agents/SKILL.md`. It explains recognized notices with valid later same-execution completion and passing selected checks, preserves unknown/unrecovered fatal behavior, and makes no business-correctness promise. The strict shape limitations and reservation mechanics stay in plan/test evidence; this is not a protocol-reference expansion. No documentation outside these two authorized plan artifacts was edited at this gate.

## Classified residual risks and uncovered areas

| Residual / uncovered area | Classification | Owner / destination / closure condition |
| --- | --- | --- |
| Five accepted plan gaps | fixed in current slice | This plan-fix owner; revised plan and per-finding evidence above. Document fixes completed; independent re-review/controller verification is still required to close the plan loop. |
| Runtime classification/proof, saturated notice visibility and all amended integration/regression assertions | fixed in current slice — planned, not implemented | Designated S1 owner/controller; destination: this work unit's single S1 after accepted-plan checkpoint. Product pass requires actual collector/public-runner tests, full-file offline run and independent code reviews. This is not a second slice or deferred accepted plan finding. |
| Unobserved wording/budgets, extra thread/turn/final/terminal fields, preambles, items between starts, repeated-start resume/persist variants and final-before-last-notice evidence | assigned to later work unit | Runner/protocol maintainer; separately confirmed evidence-backed protocol-variant support work if real evidence warrants it. Current conservative refusal is intentional and nonblocking under G1/G3; no universal schema claim. |
| Generic frame weaknesses in ordinary no-candidate Codex streams | assigned to later work unit | Runner maintainer; separately confirmed collector-protocol work if needed. G5 requires baseline behavior here; this work unit does not harden unrelated streams. |
| One last displayed old diagnostic displaced on category saturation; deferred candidates appear after old diagnostics | fixed in current slice — planned, not implemented | S1 owner; D4/exact saturation tests. Approved bounded tradeoff preserves first 19 old entries, first notice, totals, flags and untouched raw logs. No chronological merge or generic priority work. |
| Original optional canary/artifact inputs, business correctness and semantic completeness of the recovered answer not independently verified | requiring new issue or explicit user decision | Caller/controller; original workflow. Nonblocking due to confirmed evidence/read boundaries and `result_status=not_assessed`; synthetic selected-check coverage remains mandatory. No original business reread/rerun is allowed in this fix gate. |
| Initial overly broad integrity hashing | fixed in current slice | This plan-fix owner; narrowed subsequent checks before experiments. No unaccepted report content was used; no further access or outstanding remediation is needed for these document fixes. |
| Merge, live deployment and original workflow restoration | requiring new issue or explicit user decision | User/caller; after authorized draft PR/final closeout or in original task workflow. Outside this assignment. |

No unclassified risk, deferred accepted finding, new scope question or unresolved plan-fix item remains. Classified production and protocol limits are not evidence of an implementation pass.

## Completion status and next entry point

- Plan-document fixes: **completed**, all five accepted findings `已修复` at this fix gate.
- Independent verification / review-loop acceptance: **pending**; this report does not certify a `re-review` pass or alter adjudication/state/statistics.
- Next unfinished gate: **`re-review`** of the revised plan and this fix report under controller ownership, followed only after acceptance by **`accepted plan commit`**.
- Implementation, reviews, commits, pushes and PR operations remain later gates; none began here. No delegation, installation, live/API call or original business rerun occurred.
