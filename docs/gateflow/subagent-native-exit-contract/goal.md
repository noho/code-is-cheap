# Sub-agent native exit contract — confirmed goal

User confirmed this work unit and branch creation on 2026-10-18, after defining sub-agents as one fresh CLI interaction. Branch: `fix/subagent-native-exit-contract`; starting base: `32a244d1e286086be86dba837976d3d72fdd6c1f` (`main`).

## Binding contract

- The runner launches the chosen Codex / Claude Code CLI, waits for actual exit, and faithfully returns its native exit code, final answer and retained logs. Native exit 0 plus a final answer is a successful interaction even if the answer reports missing inputs, an environment obstacle, inability to solve the task, or incomplete work.
- Parsing/protocol diagnostics and optional artifact/canary results are information for the caller. They must not rewrite the native runtime exit code or constitute business acceptance. Do not make a semantic task-success classifier.
- Whether requested work is complete, whether a report or other artifact is acceptable, and whether/how to continue or retry belong to the caller. Remove the skill's fixed one-same-provider retry ceiling and avoid treating normal follow-up interactions as provider failures. Preserve user/project authorization and routing rules.
- Preserve honest diagnostics, incomplete/partial/missing-final visibility, native nonzero codes, and source logs. Do not fabricate native success, final answers or unknown exit codes. Failures before the CLI starts remain runner setup failures. Necessary wrapper I/O/collection failures must be made visible without misattributing them to the native process; plan must spell out the exit/status ownership under this goal rather than quietly retain acceptance-based overrides.
- Update both runners/collector and directly affected helpers, regression tests, README documentation and repository sub-agents skill/reference as needed. Existing JSON diagnostic/check information may be retained; no unrelated schema redesign or infrastructure.

## Evidence and success signals

Current collector `scripts/agent-run-result.py:474–475,522–528,576` turns a missing optional report into an error, rejected status and code 1 even after runtime 0 and a real final. Both runners promote the collector/check exit into their outer exit. The same collector currently checks protocol proof and business-adjacent artifacts in one acceptance path. Installed runner/collector bytes matched this checkout during the investigation.

Use offline independent fixtures to prove: runtime 0 with a final explaining Python import failure and missing report stays 0; incomplete skeleton can be reported without any semantic task verdict; tool failures/recovered SSE/check failures/protocol diagnostics are retained without altering native exit; native nonzero remains exact; empty/absent/invalid final or damaged logs are honestly exposed. Cover Codex and Claude Code and necessary postprocessing failure paths. No paid replay of the portfolio task.

The prior investigation at `/Users/leo/workspace/portfolio-manager-v2/orch/workpapers/code-seed-20261017/upstream-a-review-investigation.md` explains the two Mimo calls, but its early business-failure interpretation is superseded by the user's clarified interaction contract. Do not modify or rerun that project.

User explicitly requested including the already untracked `docs/reviews/runner-host-handle-loss-investigation-20261016.md` and sibling `*-evidence.json`. They concern an earlier host-handle-loss incident (historical context), not the two Mimo calls. Preserve them as authored; inclusion does not authorize implementing their durability/supervisor/recovery proposals.

## Roles and workflow

Controller owns goal, gate state, evidence adjudication, review decisions and delivery. Dispatch only runner subprocesses: `gpt-6-sol` via `codex-agent-run` for plan/implementation/fixes; two independent parallel reviewers `mimo` and `ds-flash` via `claude-agent-run` (user's explicit routes override repository defaults). No built-in collaboration agents or recursive delegation. Use Planreview for this public exit/status contract and Deepreview for the final combined code change. Fix only accepted findings, then independently re-review affected changes.

## Non-goals and delivery

No provider route/config/model/shim changes, task-specific semantic checks, persistence/supervisor/result-store system, host-handle recovery implementation, portfolio business review, automatic retry/fallback, or live deployment. Existing historical evidence is not silently rewritten to the new contract.

Deliver tested, reviewed changes and gate artifacts as a draft PR; user merges manually. No merge, approve, mark-ready, reviewer requests, external comments or issue mutations. Record applicable sync commands in closeout and remind user to sync from the checkout with approved changes; do not run sync or modify installed skills/runners.

## Risks / uncovered areas

- Public exit/status behavior intentionally changes: covered by this approved work unit (plan, docs, regressions and independent reviews). Caller migrations outside this repository: owner user/callers; destination caller integration after merge, classified assigned to later work unit if needed.
- Historical host-handle loss cannot be solved by changing an exit contract: owner maintainer, destination separate explicitly authorized work unit; classified requiring new issue or explicit user decision, nonblocking for this scope.

No blocking scope question after user's confirmation. Next entry: plan.
