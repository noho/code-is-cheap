setup_status: ok
agent_status: completed
tool_evidence: yes
canary_status: match
warnings: ["claude-code:unrecognized_model"]
retry_class: none

# Launcher `--resume` adjudication

Scope: PR #39, current workspace changes for live repair-tool installation and the `xx_codex --resume` launcher option. Kimi artifact: `code-review-20260925-140750.md`. Kimi finished with exit 0, `subtype=success`, `is_error=false`, and matching canary. Its stderr warning matches the documented nonfatal predicate.

MiMo was dispatched in parallel after preflight passed. The user explicitly directed us to stop waiting. Its process was interrupted with exit 130, no structured result, and no review artifact. It was not counted as a successful review and was not retried.

Kimi findings:

1. Accepted. The launcher now supports both `--resume <id>` and `--resume=<id>`, avoiding accidental pass-through of the latter to Codex CLI.
2. Accepted. TOML parsing is loaded only for session-ID mode; older Python can still use the direct rollout-path repair mode. The launcher mode reports a clean Python 3.11 requirement, documented in both READMEs.
3. Accepted. One optional prompt is forwarded to the underlying `codex resume` after repair.
4. Accepted. Both READMEs now state that a session with no records to remove is left untouched and receives no backup.
5. Partially accepted. Added regression checks for equals-form syntax, optional prompt, missing ID, duplicate rollout matches, orphan reasoning, and repeated repair idempotency. Other fail-closed branches remain directly readable and do not warrant tests that mirror every conditional.

The controller also traced the entry point: the launcher recognizes `--resume` only as its first forwarded argument, resolves the selected Codex home and card, runs the installed repair tool with `--apply`, aborts on repair failure, then forwards `resume -p <profile> <id> [prompt]`. Plain `resume` remains a Codex CLI subcommand. The repair tool requires one canonical UUID match within that home and retains only the target model's reasoning records; messages and tool history remain. Changed sessions receive a private backup before atomic replacement.

Verification: 21 unit tests passed; `zsh -n`, `bash -n`, and `git diff --check` passed. A synthetic-home launcher test confirms repair-before-resume and argument forwarding without touching real sessions. `sync-agent-tools.sh` installed the new tool to `~/.local/bin/repair-codex-reasoning-history.py` and updated `~/.config/zsh/agent-tools.zsh`; installed bytes match repository sources.
