# GPT-6.2 model ID closeout

[Draft PR #71](https://github.com/noho/code-is-cheap/pull/71) is ready for the user's manual merge. The repository delivery is complete. Live deployment awaits authorization.

The `gpt-6-sol` and `gpt-6-astra` profiles now select `gpt-6.2-sol` and `gpt-6.2-astra`, respectively. Each family's base, `-x`, and `-max` aliases select high, xhigh, and max. The `business` home follows the base Sol card at high. Both READMEs, the sub-agents skill, and six test files reflect the new selections.

## Verification

The implementation ran each suite with `python3 -m unittest discover -s tests -p <file> -v` in a separate temporary home. The suites covered managed model cards, business sync, runner and app selection, sandbox staging, preflight, and resume.

| Suite | Passed | Skipped |
| --- | ---: | ---: |
| `test_codex_model_defaults.py` | 5 | 0 |
| `test_model_catalog_generation.py` | 30 | 0 |
| `test_provider_registry.py` | 11 | 0 |
| `test_install_endpoints.py` | 38 | 0 |
| `test_agent_sandbox.py` | 72 | 10 |
| `test_sub_agent_preflight.py` | 14 | 0 |
| `test_repair_codex_reasoning_history.py` | 12 | 0 |

The ten skips require explicit opt-in to macOS kernel checks. `./scripts/validate-skills.sh` passed for all six skills, and `git diff --check` passed. Controller probes confirmed that `business` updates an existing GPT-6.1 Sol config to GPT-6.2 Sol at high, preserves unrelated settings, and rejects both the previous Sol model card and the current Astra card. The rejection branch predates this change and was exercised directly by both reviewers as well.

[Claude `ds-flash`](../../reviews/code-review-20261119-114054.md) and [Claude `mimo-flash`](../../reviews/code-review-20261119-114512.md) independently reviewed the same tracked diff and reported no material findings. Both exited 0. DS reproduced the full suite result and MiMo reproduced focused results. No implementation fixes were required. The controller checked the findings, test logs, and exact reviewed diff.

The reviewed code, docs, and tests are in `f09493c8127ff14fbecc082d02a824f3e0c26293` based on `6405b8a874089e5f3ccee4182f99684a44bc37c5`. The reviewed source SHA-256 is `93412e354118afd3e70951038f60d6cb04921ac224683d16518921a6aa5e8882`, reproducible with `git diff --binary <base> <reviewed-head> -- README.md README.zh.md codex-agent scripts skills tests`. The controller matched GitHub's full compare diff to Git at the PR base and head, verified the title and body, and confirmed the pushed branch. There are no required GitHub status checks for `main`. The subsequent commit adds only this closeout. The final delivery receipt is stored by PR head OID under `/private/tmp/gpt-6-2-model-ids-delivery/`.

## Live sync after merge

The deployment owner should check a refreshed model catalog for the target CLI and account before relying on the new profiles. The locally installed Codex 0.167.2 bundled catalog omits both new IDs. The offline review reproduced the generic prompt fallback when there was no model metadata. It did not test account access, server acceptance, or actual `max` support. Those checks belong to the authorized live rollout.

After merging #71 and authorizing deployment, run these commands from the checkout containing the approved changes:

```bash
./scripts/sync-skills.sh
./scripts/sync-codex-agent.sh
```

Reopen Agent sessions to load the updated skill. The sync updates the managed profile cards and `business` defaults. A bare `codex` invocation still uses the machine-local default.
