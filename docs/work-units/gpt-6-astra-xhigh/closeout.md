# GPT-6 Astra xhigh final closeout

Status: **final closeout pass — work unit completed**. Draft PR: [noho/code-is-cheap #62](https://github.com/noho/code-is-cheap/pull/62). User merges manually. No issue was supplied; issue linkage and closeout comment are not applicable and none was posted.

## What changed

Added `gpt-6-astra-xhigh`, selecting upstream `gpt-6-astra` with `model_reasoning_effort = "xhigh"`. Existing `gpt-6-astra` and `astra` remain at `high`. Added distinct CLI/title/App entry points, runner help/list/dispatch, and both sandbox subscription classifications. Existing card discovery handles installation/sync and preflight. No gateway/catalog/policy redesign.

English and Chinese READMEs now document both effort choices, new CLI/runner/App commands and four subscription profiles across three upstream models. The sub-agents skill's Codex provider table includes the new ID.

## Verification and findings

Final affected suite: **157 passed, 10 pre-existing explicit opt-in kernel tests skipped** (167 total). All new tests ran, including actual App-launch interception on macOS, real runner-to-launcher selection, old Astra/alias controls, absent/denied new card, private repeated sync/install discovery and sandbox check/launch authentication decisions. No real model request or App instance was launched. Syntax, all six skill validations and diff checks passed; [validation.log](validation.log) retains actual commands, initial fixture failures and final successful results.

Parallel independent Deepreviews via Claude runners `mimo` and `ds-flash` both completed with runtime/outer exit 0 and no substantive finding. Controller inspected full reports and evidence and passed the review; no implementation fix or affected re-review was needed. [adjudication.md](adjudication.md) records decisions and all risk classifications.

PR delivery check passed at head `388e0dc8e120300c7c751bff264ab7b731aeaebf`, base `f300ca395dbdd8204ff009487f1d295235965852`. Repository/head repository are both `noho/code-is-cheap`; PR is draft/open with correct title/body. Full exact-OID compare diff and all file/blob identities were checked; all 13 substantive file hashes match reviewed implementation `6a92d08003e39b235a2ddf847ab61c400b521359`; push matched remote. No GitHub checks or Actions workflows exist; required local checks passed. Receipts: [delivery-initial.json](delivery-initial.json) and [delivery-initial.diff.gz](delivery-initial.diff.gz).

This closeout/evidence-only follow-up changes no reviewed source/test/README/skill content. Its final push is subject to the same exact-OID/full-diff/blob/hash check; final receipt is saved at `/private/tmp/astra-xhigh/delivery-final/facts.json` with full diff alongside it. The final immutable published version is the commit containing this closeout (retrievable with `git log -1 --format=%H -- docs/work-units/gpt-6-astra-xhigh/closeout.md`). No duplicate complete review is required for evidence-only additions.

## Remaining risks and owners

All are **assigned to later work unit**; none blocks this confirmed local configuration/routing scope:

- User: separately authorized post-merge live entitlement/xhigh acceptance, desktop UI and latency/cost smoke test; these are uncovered by fake-native/intercepted App tests.
- Maintainer: existing explicit Seatbelt/srt validation workflow for 10 opt-in kernel skips; no isolation policy changed here.
- Repository maintainer: separate preflight diagnostic work unit for the independently reproduced, unchanged broken-helper diagnostic at `scripts/sub-agent-preflight:136`; formally deferred-with-owner, outside this additive profile scope.
- Maintainer: future profile-list maintenance, optional combined preflight/sandbox test and CI setup, if justified. Current explicit selection points are implemented and behaviorally tested.
- User: live deployment/reload after manual merge and authorization. Installed configuration remains unchanged in this work unit.

## Next entry point and live sync reminder

User manually merges PR #62. From the repository checkout containing the approved changes, authorize/run the applicable sync commands:

```bash
./scripts/sync-skills.sh
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
source ~/.zshrc
```

Opening a new shell also reloads interactive launchers. Reopen Agent sessions for the updated skill. Installed runner callers need no shell reload when the runner is already on PATH. Live deployment was not authorized or performed. After sync, use `gpt-6-astra-xhigh_codex`, `gpt-6-astra-xhigh_codex_app`, or `codex-agent-run --provider gpt-6-astra-xhigh --cwd /absolute/workspace --prompt ...`.
