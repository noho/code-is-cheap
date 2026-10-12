# User workflow update — 2026-10-12

## Authorized scope

Continue `feat/official-provider-catalogs` / draft [PR #55](https://github.com/noho/code-is-cheap/pull/55). The user authorizes all providers to read this repository and expressly permits the controller to complete this small documentation implementation. Allowed writes are `AGENTS.md`, `state.md` and this new artifact. The controller alone adjudicates and commits/pushes. No merge or live sync is authorized.

## Minimal implementation and docs choice

- Verify and retain the user-directed `AGENTS.md` draft: `gpt-6-sol` via `codex-agent-run` owns plan/implementation/fixes; independent parallel review defaults are `mimo-flash` and `ds-flash`, both via `claude-agent-run`.
- Record the current routing and pending new exact-OID PR review in `state.md`; preserve previous routing as history.
- Withdraw the controller-added no-delegation task restriction going forward. Nested delegation remains permitted within authorized scope. The user's explanation that larger reviews may delegate is background; no additional nested-delegation mandate or blanket restriction is added to `AGENTS.md`.
- Keep `README.zh.md` unchanged: its sync sections already describe the three scripts, installed runner location and shell reload. Put the requested closeout obligation in repository workflow instructions and record this task's evidence here. Archived prompts/reviews retain their original wording and routing.

## Checks

- Branch and GitHub facts: existing branch `feat/official-provider-catalogs`, PR #55 open/draft; prior published head `c1c9d0804779cab1b6b246f9c1521e043410d410`.
- Read `README.zh.md` sync sections (lines 261–295, 434–446, 819–842) and the three script sources. Each named script exists and is executable; roles below match the implementation.
- `bash -n` on each of the three sync scripts and `zsh -n` on each of the two runner scripts: pass. These are syntax checks only; no scripts were deployed or provider runtimes started.
- Both runner sources set their launcher-file default to `~/.config/zsh/agent-tools.zsh` and execute `source "$agent_tools_file"` themselves. A caller with the installed runner and its required tools on `PATH` need not source `~/.zshrc`; interactive launcher functions require a shell reload.
- Scoped diff checked; `git diff --cached --check`: pass. Commit restricted to the three allowed paths. Hash comparison preserves all 387 other tracked/pre-existing untracked files, including the prior review and snapshot; those two untracked records are outside this commit.

## Historical evidence and residual limits

The parent MiMo/Codex final review was interrupted with user authorization before this steering: managed46859 actual exit 130. No complete parent/child summary was collected; this does not establish that all children exited. Original DS final review managed34484 exited 0 and produced `docs/reviews/pr-55-review-20261012-172143.md` for exact head `c1c9d0804779cab1b6b246f9c1521e043410d410`, reporting finding 1 fixed and no new substantive findings. That report is preserved as historical evidence and does not review this update.

The next published PR head, including this update, still needs fresh literal base/head OIDs, an exact-OID compare, both new default reviews and controller adjudication. Final closeout has not passed. Existing product/runtime acceptance and residual limits are historical evidence; this update does not extend them. No production, cards, catalogs, tests, runtime, endpoint or source changes; no expensive native tests or provider probes. No Kimi API/development/review: its single status probe was already consumed, and this continuation uses no additional quota.

## Required later closeout reminder

After final closeout passes, remind the user to sync to live and copy the applicable commands into the final closeout artifact. Run them only with user deployment authorization, from the repository checkout containing the approved changes, selecting scripts for changed components:

```bash
./scripts/sync-skills.sh       # Codex / Claude skills
./scripts/sync-agent-tools.sh  # Launchers, runners, and shared helpers
./scripts/sync-codex-agent.sh  # Codex profiles, catalogs, routes, and shim service
```

The official-provider-catalogs product changes require `./scripts/sync-codex-agent.sh` after approval. Select the other scripts only when their components changed; this documentation update adds no deployment need. After deploying launcher changes, use `source ~/.zshrc` or open a new shell; reopen Agent sessions after skill updates. Installed runner callers already on `PATH` do not need the shell reload. No sync command was run here.
