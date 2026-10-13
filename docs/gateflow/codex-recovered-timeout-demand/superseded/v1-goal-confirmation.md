# Goal confirmation: recovered Codex timeout / high-demand notices

- Gate: goal confirmation; decision: root cause established; user confirmed the binding scope contract in the follow-up instruction.
- Work unit: `codex-recovered-timeout-demand`.
- Branch: `fix/codex-recovered-timeout-demand`; clean preflight on `main`, branch creation explicitly authorized.
- Base: `62c3b26` (previous recovered server-retry fix, merged as PR #58).
- Goal confirmation passed. Current gate / next entry point is recorded in state.json.
- Controller owns adjudication. Plan / implementation / accepted fixes: `gpt-6-sol` via `codex-agent-run`; independent review routes: concurrent `mimo-flash` and `ds-flash` via `claude-agent-run`. Plan review uses planreview; code / aggregate / PR reviews use deepreview.

## Direct evidence and first-principles judgment

`scripts/agent-run-result.py:49` accepts only exact top-level `{type,message}` errors matching existing stream-closed or server-request-error notice families. Both observed new families return false in repository and installed collectors. Both collectors have SHA256 `8a0be0d0e7d472ff145ee1c691f1849f7480cadd239a9f2dfb4e43900e3a0153`.

The false results send all five notices through the immediate fatal-error path at `scripts/agent-run-result.py:269`. Recovery proof and diagnostic reclassification already exist at `:316` and `:337`. They require initial frame shape/order and unique thread/turn, notices within the turn, a single supported successful terminal, valid final answer after the last notice and before terminal, native/precollection exits zero, and no other collector validation errors. Selected canary/artifact/last-message checks run before reclassification.

Controller read-only replay using the saved diagnosis argv reproduced collector exit 1, errors=5, anomalies=3, warnings=0. An exploratory **in-memory** recognizer extension for exactly the two new families, with the remainder of Collection unchanged, yielded runner exit 0, errors=0, anomalies=3, warnings=5, `validation_status=needs_review`, `result_status=not_assessed`. This establishes that the existing proof suffices for this execution; it is not an implemented or reviewed fix.

Observed frames: one thread start at line 1, one turn start at line 2; timeout notice at line 3; demand notices at lines 176–179 (attempts 2–5); last agent message at line 186; sole turn.completed at line 187; no turn.failed. Native and precollection exit arguments are 0. Stderr is empty. Canary matches, both selected artifacts exist as regular files. `canary_read_candidate=false` and the other anomalies remain unchanged; mechanical recovery must not erase them.

Evidence: [goal-evidence.json](evidence/goal-evidence.json), including read-only source hashes and sanitized result comparisons. [minimal-events.jsonl](evidence/minimal-events.jsonl) contains synthetic identities/final text and only the two observed notice families; no business contents. Original business evidence is never modified or passed to sub-agents. Controller alone may replay it read-only and preserve sanitized results.

## Proposed binding scope

Goal: classify recovered timeout and high-demand reconnect notices correctly, avoiding mechanical rejection of an execution that meets the existing recovery proof.

Minimal repair: extend only the narrow notice recognition allowlist to exact full messages `Reconnecting... [1-5]/5 (request timed out)` and `Reconnecting... [1-5]/5 (We’re currently experiencing high demand, which may cause temporary errors.)`. Preserve exact event shape, ASCII attempts 1–5, budget 5, full-match behavior and the observed U+2019 apostrophe. Retain existing recognized families and all recovery predicates; no generic substring/error suppression or schema change.

Non-goals / boundaries:

- No caller business acceptance changes, automatic retry, or business-agent rerun.
- No change to generic errors, Claude collection, startup diagnostic handling, terminal/identity/order rules, exit propagation, optional checks, output schema or diagnostic limits.
- No retry-state framework, broad wording normalization, network fault injector or unrelated refactoring.
- No merge, PR approval, mark-ready, reviewer request or external comment authorization.

## Success signals

1. Reviewed repository and then installed collector replay the original input with its saved native/precollection exit=0 and selected checks: exit 0, completed, needs_review, errors=0/anomalies=3/warnings=5, original diagnostic lines/messages retained, canary match and both artifact checks retained. The previously rejected outer collector exit must not be fed back as a precollection runtime/postprocessing failure.
2. Synthetic positive cases cover both exact notice families and coexistence with existing recognized notices. Unknown/near-match/unsupported-shape errors, unrecovered execution, bad ordering/identity/terminal, nonzero native or postprocessing exit, and explicit check failures remain rejected. Existing runner-result regression suite passes.
3. All gateflow gates pass with durable artifacts and controller adjudication, required independent reviews complete; a new draft PR and accepted commits are delivered. User merges manually.
4. After full review, run authorized `./scripts/sync-agent-tools.sh` from this reviewed checkout; record installed collector path/hash and equality to reviewed source. Only component-appropriate sync is needed. Then use `mimo-flash` separately through Codex and Claude Code runtimes for new synthetic three-step live probes: tool-read input, program-compute/write a new result, tool-read result back. Verify actual tool events, computed output and process completion. These ordinary probes prove live tool/runtime integration, not reproduction of a real network fault; original replay plus negative regression prove this classification repair.

## Docs, risk classification and completion

Docs decision: gateflow artifacts, tests, review evidence and final closeout document the behavior and deployment/probe commands. Determine any minimal existing user-document update during plan; no new public interface.

Residual risks / uncovered areas:

- Exact upstream wording variants outside the two observed families remain rejected: assigned to a later work unit if new evidence warrants it; owner repository maintainer. This is intentional scope, not a blocker.
- Original business correctness and three retained anomalies are caller-owned: assigned to the existing caller workflow, not acceptance of this work unit. `result_status=not_assessed` remains.
- Actual transient network failure is not injected by ordinary live probes: assigned to a later work unit if explicitly requested; owner user/controller. Deterministic original-log replay covers this repair.

Blocking open questions: none.

Completion status: goal confirmation passed by explicit user follow-up; proceed automatically through plan and subsequent gates. Live sync is authorized after complete review; merge is not authorized.
