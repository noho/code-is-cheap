# Goal confirmation: Codex recovered stream-error classification

- Gate: goal confirmation; status: confirmed by user delegation; authorized to progress through final closeout.
- Work unit: codex-recovered-stream-errors.
- Branch: fix/codex-recovered-stream-errors; base main 20fc6c37751836329143567c166990bdffa9de3c (#51 merged).
- Preflight: main clean; local main equals remote main 20fc6c37751836329143567c166990bdffa9de3c. No unrelated dirty changes found. User explicitly authorized a new work branch; created before artifacts.
- New draft PR required; do not reuse #51. User/caller confirmation received. No merge/live sync/clear authorized.
- Roles after confirmation: controller adjudicates; gpt-6-sol via codex-agent-run owns plan/implement/fix; parallel independent MiMo/Codex and DS Flash/Claude planreview/deepreview at required Gateflow gates. Native statistics/raw logs retained.

## Goal / motivation

Correct runner classification of a demonstrably recovered Codex connection interruption. A recognized intermediate retry/connection notification must remain diagnostic evidence, while a later valid native success plus existing checks can produce a usable completed result. Do not downgrade arbitrary error events or infer recovery when event evidence is ambiguous.

## Direct code / event evidence

- scripts/agent-run-result.py:194-208: codex() recognizes turn terminals but unconditionally calls note('errors', event, line) for every top-level type=error.
- scripts/agent-run-result.py:398-401: any error count yields validation_status=rejected and a synthesized runner_exit_code=1 even with completed agent/native success.
- scripts/codex-agent-run:539-552: collector receives native/process postprocessing exit codes; collector nonzero becomes outer runner exit when earlier run_exit=0.
- Authorized original JSONL has 211 strictly parsed events, one thread.started, one turn.started, one error (line 193), no turn.failed, and one turn.completed (line 211).
- Line 193: Reconnecting... 1/5 (stream disconnected before completion: stream closed before response.completed). Lines 194-209 record subsequent tool activity, line 210 final agent_message, line 211 successful native terminal. Final event text matches named last.md and saved summary final_answer.
- Original summary: runtime_exit_code=0, agent_status=completed, canary_status=match, existing regular artifact reported, but validation_status=rejected / runner_exit_code=1. Only hard diagnostic is line193; five unrelated tool/stderr anomalies already have non-fatal classification.
- Actual offline baseline collector replay using the exact named JSONL/stderr/last.md and precollection runner exit=0 reproduces rejection with exactly one error at line193; native terminal usage preserved. See evidence/goal-log-check.json (hashes, ordered structural evidence, native summary stats, scoped replay).

## Confirmed-by-proposal success signals

1. Define a narrow evidence-based rule for identifying recoverable Codex connection/retry notices and proving subsequent successful completion in the same valid recorded execution; unknown or ambiguous errors remain rejected with specific diagnostics.
2. Given valid successful completion, final answer and passing selected checks, recovered connection notices remain visible with original message/event location, without solely causing runner exit1 / rejected; ordinary existing anomalies may still yield needs_review.
3. Unrecovered connection failure, turn.failed, native/process postprocessing nonzero, malformed/conflicting/missing terminal, missing/invalid final answer and selected canary/artifact failures remain rejected. A later success cannot erase a prior turn.failed, arbitrary runtime error or structural failure.
4. Validate the classification using the original real log offline and a minimal synthetic success/failure matrix through relevant collector/runner paths. No real API/business re-execution is needed.
5. Native final answer, log locations, wall-clock/usage collection, optional checks, Claude behavior and routing remain intact. No route-proof fields or broad schema/redesign/retry layer added.

## Smallest scope / non-goals

Expected scope: scripts/agent-run-result.py, focused tests/test_agent_run_results.py, and only docs/skill clarification necessary to state the result classification; scripts/codex-agent-run only if the actual call chain demonstrates a required change. Gateflow/evidence/review artifacts included. Plan must justify every changed boundary and minimize slices.

Read scope for caller evidence is ONLY the named original JSONL, matching stderr/last.md and runner-summary.json. Process structural/control fields needed for this defect, not business conclusions. Do not recursively search job/project, read business artifacts, canary/expected files elsewhere, change caller files/content, judge business reviews, run original tasks, clear/interfere with workflow panes or modify original logs. Hashes/real statistics are retained; no raw business payload is copied into repository artifacts/prompts.

Original canary match and regular-artifact metadata are archived summary evidence, not an independently rerun check. Offline baseline replay deliberately omits those explicit checks because their original inputs are outside the named read scope. Their continued enforcement will be tested with independent synthetic material; do not describe scoped replay as a full re-run of original optional checks.

No model/provider routing proof additions, broad error downgrading, business rule changes, new runtime environment, compatibility/migration layer, merge or live deployment. No external issue/comment operation is authorized. New draft PR and final closeout after the required workflow are authorized following confirmation.

## Risks / open questions / next gate

- fixed in current slice (pending implementation/review): overly broad top-level error rejection and insufficient recovery classification.
- assigned to later work unit: unobserved protocol versions or unrelated runtime errors beyond the selected evidence, maintainer runtime/protocol validation; current rule must fail closed on unknown evidence.
- requiring explicit user decision: merge and deployment later (goal confirmation already received). Caller retains original task restoration ownership.

No additional blocking input is currently needed to propose this scope. Exact recognition/recovery predicates must be derived and reviewed in plan, not guessed here. User/caller confirmed goal, non-goals, boundaries and success signals; next gate is plan.

## Confirmation received

2026-10-11: Caller explicitly confirmed all scope/success criteria and authorized automatic Gateflow through new draft PR and final closeout, with named routes. Only recognized connection notices with reliable same-execution success can recover; unknown/unrecovered/error/turn.failed/nonzero/structure/selected-check failures remain rejected. No route-proof fields or caller business material access. Original logs used only for structural offline reproduction; optional checks use synthetic inputs. No merge or live deployment.
