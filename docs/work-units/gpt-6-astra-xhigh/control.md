# GPT-6 Astra xhigh work unit

## Confirmed scope

User confirmed 2026-10-20: add independent `gpt-6-astra-xhigh` profile with upstream model `gpt-6-astra` and effort `xhigh`; preserve `gpt-6-astra` at `high`. Integrate CLI/App launchers, runner, sync/install, relevant tests and docs. Deliver a draft PR; do not merge or deploy live.

Preflight: clean `main` at `f300ca395dbdd8204ff009487f1d295235965852`; created `feat/gpt-6-astra-xhigh` with user authorization. No issue linked.

Evidence: existing Astra card contains model `gpt-6-astra`, effort `high`; launcher and runner enumerate supported profile IDs; sync discovers profile cards; sandbox has explicit subscription-backed provider lists.

Routing: plan/implementation/fix use `codex-agent-run --provider gpt-6-sol`; independent parallel full Deepreviews use `claude-agent-run --provider mimo` and `--provider ds-flash` (explicit user routes override project defaults). Controller adjudicates and handles delivery.

## Gate state

Goal confirmation: passed. Plan/controller check: passed. Current gate / next entry point: code review.

## Residual risks

Live deployment intentionally awaits user authorization; owner: user; destination: post-merge sync, classified assigned to later work unit. Live model invocation is not required for local routing/configuration acceptance.

## Plan/controller decision

Accepted [plan.md](plan.md), one implementation slice. This is an additive profile using existing configuration/dispatch contracts, with no important architecture, migration or state-machine decision; independent Planreview is not applicable. Controller checked launcher, runner, sync discovery, preflight generic path and both sandbox subscription lists against source.

Keep added test scope proportionate: cover real selection/configuration, sync discovery, App composition/dispatch and both sandbox subscription decisions with existing fixtures. Reuse existing generic resume/error/boundary tests rather than expanding unrelated negative cases. Missing new-card selection is relevant; a new exhaustive auth/CA failure matrix is unnecessary. No abstract registry refactor.

Planner runner exited 0, runtime_exit_code 0, terminal turn.completed; plan artifact inspected. Baseline 28 tests passed; native command diagnostic came from initial exploratory search, not test failure. Source logs: `/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-run.yJe4Jy93/output.jsonl`.

## Implementation/controller check

Inspected implementation.md, final validation log and complete runtime/test/docs diff. Final affected suite ran 167 tests: 157 passed, 10 explicit kernel-opt-in skips. Syntax, provider inventory/help, all six skills and diff whitespace checks exit 0. All new tests ran, including intercepted actual App launch on this host. Initial focused fixture failures were corrected before the final complete affected-suite run. No production changes after that run. Implementation runner exited 0, native runtime 0, terminal turn.completed; exploratory patch/fixture diagnostics are retained in runner logs and validation history.

Implementation evidence: [implementation.md](implementation.md), [validation.log](validation.log). Runner log: `/var/folders/2t/vbqfkdyj40v8f4jc4x180n5c0000gn/T/agent-run.T5YFt7K7/output.jsonl`.

Residual-risk classification applies to plan/implementation items:

- Profile-list drift: fixed in current slice; implemented and covered by launcher/runner/preflight/sandbox selection tests.
- Live remote entitlement/xhigh acceptance, cost/latency and real desktop UI behavior: assigned to later work unit; owner user; destination separately authorized post-merge live smoke test. Local selection is the agreed acceptance scope.
- Ten unchanged opt-in kernel tests: assigned to later work unit; owner maintainer; destination existing explicit Seatbelt/srt validation workflow. No kernel/isolation policy changed; new subscription branches are tested with captured exec.
- Pre-existing preflight diagnostic for a broken/non-executable helper: deferred-with-owner, assigned to later work unit; owner repository maintainer; destination separate preflight diagnostic work unit. Evidence is recorded in implementation.md; no new production preflight behavior is introduced, correctly installed helper and missing selected card are covered. Confirmed scope excludes unrelated generic preflight repairs, so this does not weaken current acceptance.
- Live installation/reload: assigned to later work unit; owner user; destination manual post-merge sync. No live sync authorized or run.

No unclassified residual risk or implementation blocker. Next: independent parallel Deepreviews through Claude mimo and ds-flash.
