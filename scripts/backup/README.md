# Backup maintenance copies

These are reviewable sources, not live backups. `agents-backup-restore.sh` is
maintained for `/Volumes/LEO/Agents/agents-backup-restore.sh`; `backupsysfiles.zsh`
contains only the function maintained in the user's `.zshrc`. Deployment belongs
to the controller and requires user authorization.

The runner collector is required. Old payloads missing
`.local/bin/agent-run-result.py` predate the required collector and must be
recreated to use the updated restore; they cannot restore a complete current
runner. Restore rejects them before changing target files. On the source, if
the collector is missing, install current agent tools by running
`./scripts/sync-agent-tools.sh` from the current repository checkout. Then run
`bash agents-backup-restore.sh backup` using the updated backup script and
`bash agents-backup-restore.sh verify` before migration. If the source is
unavailable, `verify` remains usable; retain the archive for separate manual
data recovery. This does not automatically restore a working runner.

The sandbox wrapper, Node adapter and installer are optional.
Backups record source SRT presence/version without executing SRT;
they omit `node_modules`, the machine-local SDK and `.local/bin/srt` symlink.
Normal restore uses no network for optional SRT and prints the installer command
if needed. `restore --install-deps` invokes the archived installer only when the
source had the Node package, installing `@anthropic-ai/sandbox-runtime@0.0.79`
into the target HOME. Node >=22.12 and npm are required; package/version/layout
and required modules are checked. A source without SRT does not request it.
Other existing CLI dependency installation behavior is retained.
If optional SRT installation or validation fails with `--install-deps`, restore
returns nonzero and reports that environment files were already restored plus
the path holding previous files. Those files are retained for manual recovery;
there is no automatic rollback, and optional SRT dependencies are not ready.
Installer errors are preserved on stderr.

Never commit backup payloads, private shell configuration, keys/endpoints or
session data. USB payloads under `scripts/backup/payload/` are ignored; run actual
backups from the authorized live location. The function backup retains its
existing session filtering and the shared `.codex` catalog/session coverage.
