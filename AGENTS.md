# Project development workflow

These instructions apply to development of this repository.

1. Create a work branch before changing files; reuse the current work branch when continuing an unmerged PR.
2. Use `$sub-agents` to dispatch `gpt-6-sol` through `codex-agent-run` (Codex runtime) for plan, implementation, and fixes.
3. Use `$sub-agents` to dispatch two independent `$deepreview` reviews in parallel: `mimo-flash` through `claude-agent-run` (Claude runtime), and `ds-flash` through `claude-agent-run` (Claude runtime).
4. The controller checks the evidence, adjudicates findings, and dispatches accepted fixes to `gpt-6-sol` before closing the review loop.
5. Commit as needed, push the work branch, and create a PR. The user merges it manually.
6. After final closeout passes, remind the user to sync to live and record the applicable sync commands in the closeout artifact. Run the following commands from the repository checkout containing the approved changes, selecting the scripts needed for the changed components. Live deployment requires user authorization.

   ```bash
   ./scripts/sync-skills.sh       # Codex / Claude skills
   ./scripts/sync-agent-tools.sh  # Launchers, runners, and shared helpers
   ./scripts/sync-codex-agent.sh  # Codex profiles, catalogs, routes, and shim service
   ```

   Reload interactive launcher functions with `source ~/.zshrc` or open a new shell after deploying them; reopen Agent sessions to load updated skills. Runner callers do not need to source `~/.zshrc` when the installed runner is already on `PATH`.

These provider/runtime pairs are the default review routes for this repository. Explicit user instructions for a task take precedence.
