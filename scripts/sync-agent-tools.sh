#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
agent_tools_source="$repo_root/scripts/agent-tools.zsh"
agent_tools_target="${AGENT_TOOLS_TARGET:-$HOME/.config/zsh/agent-tools.zsh}"
agent_run_bin_dir="${AGENT_RUN_BIN_DIR:-$HOME/.local/bin}"

mkdir -p "$(dirname "$agent_tools_target")" "$agent_run_bin_dir"
install -m 600 "$agent_tools_source" "$agent_tools_target"
install -m 755 "$repo_root/scripts/claude-agent-run" "$agent_run_bin_dir/claude-agent-run"
install -m 755 "$repo_root/scripts/codex-agent-run" "$agent_run_bin_dir/codex-agent-run"
install -m 755 "$repo_root/scripts/sub-agent-preflight" "$agent_run_bin_dir/sub-agent-preflight"
install -m 755 "$repo_root/scripts/compose-codex-app-config.py" "$agent_run_bin_dir/compose-codex-app-config.py"
install -m 755 "$repo_root/scripts/repair-codex-reasoning-history.py" "$agent_run_bin_dir/repair-codex-reasoning-history.py"

echo "Synced agent tools to $agent_tools_target"
echo "Synced agent runners to $agent_run_bin_dir"
