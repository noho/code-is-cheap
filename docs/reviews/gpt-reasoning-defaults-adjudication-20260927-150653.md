# GPT reasoning defaults: review adjudication

Base: `main`. Branch: `feat/gpt-reasoning-defaults`.

Reviews: [Kimi](code-review-20260927-145914.md) and [MiMo](code-review-20260927-150337.md). Both runner results completed successfully; each reported its preflight canary correctly. The only stderr diagnostics were the runners' recognized `unrecognized_model` metadata warnings.

## Decisions

| Finding | Decision | Resolution |
| --- | --- | --- |
| Business config failure interrupts shared shim deployment (both reviews) | Accepted | Moved the business update after shared cards, shim binaries, routes and launchd handling. Added an isolated shell integration test: a dangling business config symlink returns nonzero while shared deployment completes. |
| Managed-key inline comments are removed (Kimi) | Rejected | The two key values are explicitly repository-managed; keeping a comment attached to an old value can leave misleading instructions. Unrelated TOML values and sections remain unchanged. |
| README file lists omit the new helper and test (Kimi) | Accepted | Added both files to the English and Chinese layout and maintenance lists. |
| Sol model policy is duplicated across shell, helper and documentation (MiMo) | Rejected | Shell selects the Sol card; the helper's Sol guard deliberately prevents a future caller from silently routing the separate business account to another model. README describes that policy and is not a runtime source. |

## Final verification

- `python3 -m unittest discover -s tests`: 36 tests passed.
- `bash -n scripts/sync-codex-agent.sh` and `git diff --check`: passed.
- A prior isolated full sync confirmed Astra/Sol/Luna installed efforts `high/high/xhigh` and business `gpt-6-sol/high`, preserving an unrelated `notify` setting.
- The local bundled Codex catalog lists `high` for Astra and Sol and `xhigh` for Luna among supported reasoning levels. No paid model request was needed for this configuration change.

Residual risk: live user homes are not changed by the PR itself; the sync script must be run after merge. The business config writer replaces its inode, so unusual ACLs or xattrs on that file are not preserved. An external writer can still race in the narrow interval between the final content check and `os.replace`.
