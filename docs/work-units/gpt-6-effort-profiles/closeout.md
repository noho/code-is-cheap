# GPT-6 effort providers closeout

Status: **review and final closeout pass**. Draft PR: [noho/code-is-cheap #64](https://github.com/noho/code-is-cheap/pull/64). The user merges manually. No live deployment was authorized or performed.

## Delivered behavior

| Effort | Astra provider | Sol provider |
|---|---|---|
| high | `gpt-6-astra` | `gpt-6-sol` |
| xhigh | `gpt-6-astra-x` | `gpt-6-sol-x` |
| max | `gpt-6-astra-max` | `gpt-6-sol-max` |

Astra uses upstream `gpt-6-astra`; Sol uses `gpt-6.1-sol`. `gpt-6-astra-x` replaces the old `gpt-6-astra-xhigh` canonical provider. Base Sol and its existing aliases now use high, and business continues following the base Sol card. CLI/App launchers, runner, sandbox classification, current documentation and the sub-agents provider list are updated. Existing dynamic discovery handles preflight, installation and sync.

AGENTS.md retains the two default Claude review routes and adds the user-requested Codex `ds-flash` backup when the Claude DS runtime is unavailable and its failure reason is recorded. That fallback was used after the original Claude DS request returned HTTP 403.

## Verification and review

The affected suite passed: 188 tests, 175 passed and 13 existing opt-in skips. Two focused follow-up checks, shell/Python syntax checks, all six skill validations and diff checks passed. [validation.log](validation.log) contains commands and results; [implementation.md](implementation.md) describes coverage.

Independent full Deepreviews through Claude `mimo-flash` and Codex `ds-flash`, plus the Mimo AGENTS.md supplement, all completed with native/outer exit 0 and no substantive findings. Both full reviewers independently reran the affected suite with the same passing result. The controller checked their evidence and resolved nonblocking questions; see [adjudication.md](adjudication.md). No implementation fix remained after review.

The reviewed source is commit `626dd0ef1f4dd4938b0b1d77693955de76c6daa5`, based on `bb3454de0d461d97aab1c3bfc71dd87d18b49d61`; [reviewed-version.json](reviewed-version.json) pins all substantive file states and the source diff hash. The subsequent commit containing these reports and this closeout changes evidence only. Its immutable published identity is retrievable with `git log -1 --format=%H -- docs/work-units/gpt-6-effort-profiles/closeout.md`. Final delivery checks verify that commit against the remote branch and PR head, the unchanged base and reviewed source identities; the delivery receipt is retained at `/private/tmp/gpt-6-effort-delivery-final.json`.

There is no repository Actions workflow and no commit status was returned by GitHub for the implementation. Required local checks passed. Remaining live model entitlement/App behavior, existing opt-in kernel skips and future membership-list maintenance have owners in the adjudication artifact; none blocks this scope.

## Manual merge and live sync reminder

After manually merging PR #64, run the following only with live-deployment authorization, from a repository checkout containing the approved changes:

```bash
./scripts/sync-skills.sh
./scripts/sync-agent-tools.sh
./scripts/sync-codex-agent.sh
```

Open a new shell to load the launchers and discard obsolete `gpt-6-astra-xhigh` functions. Alternatively, explicitly remove both obsolete functions with `unfunction gpt-6-astra-xhigh_codex gpt-6-astra-xhigh_codex_app`, then run `source ~/.zshrc`; sourcing alone does not remove old functions. Reopen Agent sessions to load updated skills. Installed runner callers need no shell reload when the runner is already on PATH.

Sync intentionally retains extra old model cards and old App data/session history. An old card may still work with native `codex -p`; it does not restore support for the old runner provider. New named App profiles use their own private homes.
