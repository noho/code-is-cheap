# Plan fix: Codex recovery startup diagnostics

## Scope and completion

- Work unit: `codex-recovery-startup-diagnostics`; gate: plan fix.
- Branch verified: `fix/codex-recovery-startup-diagnostics`.
- Scoped plan correction is complete. This records the root controller's adjudication; it does not declare plan re-review, implementation or product validation complete.
- Changed files: [plan.md](plan.md) and this evidence artifact only. No product/test changes, agent dispatch, staging, commit, push, deployment or gate-state update were performed.
- Read inputs: `AGENTS.md`, `goal.md`, `plan.md`, and relevant sections of `scripts/agent-run-result.py` and `tests/test_agent_run_results.py`. No review artifacts/history, original business evidence, caller files, credentials or real provider calls were accessed.

## Findings and dispositions

### Accepted: explicitly combine startup recovery with an ordinary tool anomaly

The existing plan covered a supported startup gap and successful selected-check tools, but lacked an explicit combined regression with an ordinary expected failed command after `turn.started`. This is a preservation assertion under confirmed goal signals 2 and 4, not a new behavior or slice.

Evidence from allowed code: `Collection.codex` records a completed `command_execution` with a nonzero item exit as an anomaly (`scripts/agent-run-result.py:272–275`); the recovery fence rejects collector errors rather than ordinary anomalies (`:300–301`). The adjacent-start recovery test already retains tool anomalies (`tests/test_agent_run_results.py:120–122,149–151`). The added case must prove that the supported startup gap preserves these semantics together.

Fix in plan section “1. Reproduction, accepted paths, diagnostics, and stats”: add the named `supported-gap-with-expected-command-failure` case to `test_codex_startup_diagnostic_recovery_and_controls`. Its seven frames contain one supported gap diagnostic, a completed `rg no-match` command with item exit 1 after turn start, the exact recovered reconnect, valid final `OK` with matching fake saved-final input, and successful terminal/native exit 0. Required assertions are public/runner/runtime exits 0, `completed`/`turn.completed`/`needs_review`, errors empty, exact counts `errors:0/anomalies:2/warnings:1`, events 7 and tool results 1. Preserve startup/tool anomaly text and metadata at output lines 2/4 and the recovered notice at line 5, plus schema, final, usage and raw output assertions. Existing adjacent-start and no-retry controls remain unchanged.

Disposition: fixed in the plan; test implementation and observed product results remain pending with the S1 implementer and root controller.

### Rejected with reason: restrict paths to fixed observed directory families

This is the root controller's decision, not an additional finding to implement. The user explicitly authorized supported path variations. Absolute configuration paths are dynamic diagnostic payload rather than event identity; hard-coding ephemeral workspace roots would not satisfy the confirmed goal. Exact envelope, feature, complete explanatory/suppression text, lexical absolute `config.toml` grammar and no traversal retain narrow recognition. Arbitrary other frames/text remain disallowed.

The root reports its pre-implementation structural check confirmed the actual native envelope and randomized absolute configuration path match the reviewed grammar. That evidence was not reread by this fixer. The plan briefly clarifies the identity/path distinction and records the root-owned check in the existing risk row; the recognition algorithm, grammar, count bound and lifecycle fences are unchanged. No new recognition criteria or directory-family restriction were added.

## Validation

- `git branch --show-current`: exit 0; expected work branch confirmed; no Git mutation performed.
- `git diff --check`: exit 0; no whitespace errors reported.
- `python3 -B` stdin document assertions: exit 0. Verified the explicit combined case, native/runner outcomes, exact counts, diagnostic source lines, retained controls and unchanged directory-component grammar. Explicit document whitespace/final-newline checks cover the edited artifacts, including untracked files that ordinary `git diff --check` may omit.
- Product tests and collector replays were not run in this plan-only fix. The newly specified assertions are requirements for implementation, not claimed passing runtime results.

## Documentation, residual risks and owners

- Retain the plan's no-README-change decision. The root reports its README accuracy spot-check is complete; no README was read or edited here. The regression instructions and finding evidence belong in these two work-unit documents.
- S1 implementer owns implementing and executing the combined regression; root owns evidence adjudication and independent plan/code re-review. Recognition overmatch and anomaly preservation remain planned validation obligations, not verified product fixes.
- Root owns the pending post-implementation original technical replay and any conflicting structural evidence. Its pre-implementation envelope/path check is already reported complete; no broader matching is authorized.
- Collector maintenance owns future unsupported native formats through separately evidenced work. Caller/business controller owns original business and selected-check acceptance. User/deployment controller owns merge, live deployment and restoration decisions.

## Handoff and incomplete items

Return to the root controller for plan re-review and subsequent gates. Product implementation, the focused and full result tests, independent code review/fix/re-review, original technical replay, and root-owned Git/PR/closeout work remain incomplete. No blocking input or scope expansion was introduced by this plan correction.
