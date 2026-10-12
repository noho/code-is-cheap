function backupsysfiles() {
  local backup_root="$HOME/Documents/_8ssh"
  local helper source_path backup_name
  local srt_path srt_version=''
  local -a volatile_agent_data=(
    '--exclude=node_modules'
    '--exclude=.tmp/'
    '--exclude=tmp/'
    '--exclude=cache/'
    '--exclude=paste-cache/'
    '--exclude=*Cache/'
    '--exclude=*_cache/'
    '--exclude=*_cache_store/'
    '--exclude=*-cache.json'
    '--exclude=*_cache.json'
    '--exclude=log/'
    '--exclude=logs/'
    '--exclude=*.log'
    '--exclude=*.sock'
    '--exclude=fsmonitor--daemon.ipc'
    '--exclude=LOG'
    '--exclude=LOG.old'
    '--exclude=logs_2.sqlite*'
    '--exclude=sessions/'
    '--exclude=archived_sessions/'
    '--exclude=projects/'
    '--exclude=file-history/'
    '--exclude=shell_snapshots/'
    '--exclude=shell-snapshots/'
    '--exclude=history.jsonl'
    '--exclude=thread_history_1.sqlite*'
  )

  if [[ ! -d "$HOME/.codex" || -L "$HOME/.codex" ]]; then
    print -u2 -- "backupsysfiles: ~/.codex must be a real directory"
    return 1
  fi
  if [[ ! -f "$HOME/.local/bin/agent-run-result.py" ]]; then
    print -u2 -- "backupsysfiles: required runner collector ~/.local/bin/agent-run-result.py is missing"
    return 1
  fi

  mkdir -p "$backup_root"

  crontab -l > "$backup_root/crontab.conf"
  cp "$HOME/.zshrc" "$backup_root/zshrc"
  cp "$HOME/.claude.json" "$backup_root/claude.json"
  cp "$HOME/.config/zsh/agent-tools.zsh" "$backup_root/agent-tools.zsh"
  if [[ -f "$HOME/.config/zsh/agent-tools.local.zsh" ]]; then
    cp "$HOME/.config/zsh/agent-tools.local.zsh" "$backup_root/agent-tools.local.zsh"
  else
    rm -f "$backup_root/agent-tools.local.zsh"
  fi
  for source_path backup_name in \
    "$HOME/.config/agent-tools/endpoints.json" "endpoints.json" \
    "$HOME/.local/bin/agent-endpoints.defaults.json" "agent-endpoints.defaults.json" \
    "$HOME/.tmux.conf" "tmux.conf"; do
    if [[ -f "$source_path" ]]; then
      cp "$source_path" "$backup_root/$backup_name"
      chmod 600 "$backup_root/$backup_name"
    else
      rm -f "$backup_root/$backup_name"
    fi
  done
  cp "$HOME/.local/bin/claude-agent-run" "$backup_root/claude-agent-run"
  cp "$HOME/.local/bin/codex-agent-run" "$backup_root/codex-agent-run"
  cp -p "$HOME/.local/bin/agent-run-result.py" "$backup_root/agent-run-result.py" || return 1
  for helper in sub-agent-preflight compose-codex-app-config.py repair-codex-reasoning-history.py agent-endpoint.py \
    agent-sandbox agent-sandbox-launch.mjs install-agent-sandbox.sh; do
    if [[ -f "$HOME/.local/bin/$helper" ]]; then
      cp -p "$HOME/.local/bin/$helper" "$backup_root/$helper"
    else
      rm -f "$backup_root/$helper"
    fi
  done
  # Minimal dependency metadata only; never copy the SDK or its srt symlink.
  # Match the Node package layout checked by agent-sandbox-launch.mjs.
  srt_path="$(command -v srt || true)"
  [[ -n "$srt_path" ]] || srt_path="$HOME/.local/bin/srt"
  if command -v node >/dev/null 2>&1; then
    srt_version="$(node - "$srt_path" <<'NODE'
const fs = require('node:fs');
const path = require('node:path');
try {
  const cli = fs.realpathSync(process.argv[2]);
  const root = path.dirname(path.dirname(cli));
  const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
  if (pkg.name !== '@anthropic-ai/sandbox-runtime' || typeof pkg.version !== 'string' ||
      !pkg.version || path.resolve(root, pkg.bin?.srt ?? '') !== cli) throw Error('package/layout mismatch');
  for (const file of [cli, path.join(root, 'dist/utils/shell-quote.js'),
                      path.join(root, 'dist/sandbox/macos-sandbox-utils.js')]) {
    if (!fs.statSync(file).isFile()) throw Error('required module is not a file');
    fs.accessSync(file, fs.constants.R_OK);
  }
  console.log(pkg.version);
} catch { process.exitCode = 1; }
NODE
    )" || srt_version=''
  fi
  if [[ -n "$srt_version" ]]; then
    printf 'sandbox_runtime_installed=true\nsandbox_runtime_version=%s\n' "$srt_version" > "$backup_root/agent-sandbox-runtime.txt"
  else
    printf 'sandbox_runtime_installed=false\nsandbox_runtime_version=not-installed\n' > "$backup_root/agent-sandbox-runtime.txt"
  fi
  chmod 600 "$backup_root/agent-sandbox-runtime.txt"
  if [[ -f "$HOME/Library/LaunchAgents/com.leo.codex-auto-review-shim.plist" ]]; then
    cp "$HOME/Library/LaunchAgents/com.leo.codex-auto-review-shim.plist" \
      "$backup_root/com.leo.codex-auto-review-shim.plist"
  else
    rm -f "$backup_root/com.leo.codex-auto-review-shim.plist"
  fi
  if [[ -f /Volumes/LEO/Agents/agents-backup-restore.sh ]]; then
    cp /Volumes/LEO/Agents/agents-backup-restore.sh "$backup_root/agents-backup-restore.sh"
  fi

  # The Claude and profile copies omit volatile data. The shared Codex home
  # retains CLI sessions so they can be resumed after migration.
  rsync -a --delete --delete-excluded "${volatile_agent_data[@]}" \
    "$HOME/.claude/" "$backup_root/claude/"
  rsync -a --delete --delete-excluded "${volatile_agent_data[@]}" \
    "$HOME/.codex-agent/" "$backup_root/codex-agent/"
  rsync -a --exclude=node_modules "$HOME/.codex/" "$backup_root/.codex/"
  # Prune SDK copies from older backups without deleting retained shared sessions.
  find "$backup_root/.codex" -name node_modules -prune -exec rm -rf {} +

  #cp ~/.python_startup.py ~/Documents/_8ssh/python_startup.py
  cp /etc/auto_resources "$backup_root/auto_resources"
}
