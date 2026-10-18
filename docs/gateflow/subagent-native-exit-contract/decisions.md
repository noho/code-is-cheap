# Controller decisions

Binding goal: [goal.md](goal.md). Initial plan is preserved in commit `25120e6`; independent Planreviews are in progress. No implementation approval yet.

## Initial plan check

### C-P1 — optional last-message copy must not override native success

- Decision: **accepted**. Fix status: **未修复**.
- Evidence: plan.md, “Native versus setup and delivery” item 5, exit formula, “Codex explicit last-message handling” copy-failure item, and matrix row “Codex regular last-message exists but destination is raced/unwritable or copy fails” allow native 0 with an event-owned final to become outer 1 because a requested auxiliary file cannot be copied.
- Trigger: CLI completes 0, final is available in raw JSONL and can be returned in the normal summary, but auxiliary `--last-message` destination is occupied/unwritable or copy fails.
- Conflict: the confirmed contract treats the native interaction as complete and optional output/check information as caller-owned. Successfully returned native final plus a missing extra copy must not become a failed interaction. Keeping temp file and precise copy diagnostics is necessary; overriding the observed native code is not.
- Required plan fix: distinguish inability to deliver the primary result/execute the wrapper from failure to save an auxiliary final copy. Optional last-message copy/race failures must preserve native exit and final/log/retained-temp visibility in summary and detail mode. Do not introduce a second native-success acceptance gate through wrapper status.
- Validation: public Codex runner fixtures with runtime 0 and 7, existing/raced/unwritable auxiliary destination, final in JSONL, exact outer/native code, truthful copy diagnostic and retained temp source, no clobber.
- Destination: gpt-6-sol plan fix after independent reviews and combined adjudication, then both reviewers independently re-review affected contract. No implementation before closure.
- Residual risk: fixed in current slice; owner plan/implementation author, destination plan + regression tests; not deferred.

## User scope clarification / initial-plan disposition

- Initial-plan gate: **fail / superseded**, implementation not authorized from this plan. Binding later user clarification is scope-amendment.md.
- DS review docs/reviews/plan-review-20261018-085247.md: actual outer/native/runner 0/0/0, pass-with-risks, no blocking findings from reviewer. Its acceptance of multiple state enums/new wrapper_exit_code and auxiliary-copy override is **rejected-with-reason** by controller: conflicts with the clarified thin CLI goal, C-P1 and explicit latest user rejection. Native exit, final and factual diagnostics suffice; a separate wrapper outcome state is not an approved design goal.
- DS implementation-level questions (negative metadata, candidate text, no clobber, launch error visibility, damaged-log diagnostics) remain useful facts for revised plan/implementation; they do not authorize retaining the old state machine or adding mechanisms. Destination revised plan and final code review. Historical baseline tests are old-version evidence, not verification of a future fix; sandbox local-bind failure is an environment limitation, not waived required validation.
- C-P2: **accepted**, **未修复**: remove competing agent/validation/result states rather than add incomplete/wrapper states; simplify factual diagnostics. Direct evidence: old plan result-fields/status table, additive wrapper field and N/W public outcome framework; explicit user correction in scope-amendment.md. Owner gpt-6-sol, destination revised plan + implementation. Risk classified fixed in current slice.
- C-P3: **accepted**, **未修复**: return full final and remove 12000 cap plus final length/truncation fields. Direct evidence: scripts/agent-run-result.py:11,528–529 and PR #50 provenance; explicit user question/simplification goal. Owner gpt-6-sol, destination revised plan + long-final fixtures and docs. Risk classified fixed in current slice.
- Mimo old-target review is still running. Preserve actual exit and report when received, mark reviewed version and superseded scope honestly; no assumption of pass/fail, no kill, no automatic retry. New plan is a separate file to avoid mutating its target mid-read.

Proceed with gpt-6-sol authoring plan-v2.md only; both independent reviewers must review the revised plan before implementation. No unclassified risk; no additional user permission required for these explicitly directed corrections.

## Replacement plan controller check

- plan-v2.md delivered by gpt-6-sol with actual outer/native/runner 0/0/0; plan-v2-receipt.json retains three recovered ordinary inspection/diff diagnostics. Those do not invalidate the authored plan.
- Controller checked the complete 107-line plan: schema v2 removes three verdict states, runner/wrapper code rollups, final length/truncation metadata and three diagnostic classes; returns full original final, actual native code, useful identity/metrics/logs, one factual diagnostic list and optional check observations. No automatic continuation/semantic acceptance or final cap remains.
- C-P1/C-P2/C-P3 text corrections are present in plan-v2.md, **部分修复** pending both independent revised-plan reviews and actual implementation regressions. Old review approval does not apply to the revised contract.
- The remaining narrow pre-exec error handoff is internal launch plumbing only; reviewers must verify necessity/minimality, exec failure versus actual equal native code, and preservation of interactive callers. No general lifecycle/result mechanism is approved.
- User reiterated “做成cli薄封装就对了” and “不要截断final answer”; these are binding and consistent with scope-amendment.md. No further goal confirmation required.
- Next entry: independent parallel Planreview of plan-v2.md; implementation still not started. Residual risks remain classified in that plan.
