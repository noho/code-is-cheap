#!/usr/bin/env bash
# Run from a checkout, or download this file and run it with bash.
set -euo pipefail
umask 077

die() { echo "install: $*" >&2; exit 1; }
install_service=true
case "${1:-}" in
  --no-service) install_service=false; shift ;;
  --help|-h)
    echo 'Usage: bash install.sh [--no-service]'
    echo 'Requires macOS, Git, Codex CLI, Claude Code, Python 3.11+, jq, uv, tmux, rsync, zsh and curl.'
    echo 'Installs project skills/tools/cards and tmux-cli; preserves local keys/endpoints.'
    exit 0 ;;
esac
[[ $# == 0 ]] || die "unknown arguments: $*"
[[ "$(uname -s)" == Darwin ]] || die 'this installer requires macOS (launchd and zsh launchers)'
export PATH="$HOME/.local/bin:$PATH"
for dependency in git codex claude python3 jq uv tmux rsync zsh curl; do
  command -v "$dependency" >/dev/null || die "missing prerequisite: $dependency"
done
python3 -c 'import sys; sys.exit(sys.version_info < (3, 11))' || die 'Python 3.11+ required'

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "${BASH_SOURCE[0]##*/}" == install.sh && -f "$script_dir/scripts/sync-codex-agent.sh" && -d "$script_dir/skills" ]]; then
  repo_root="$script_dir"
else
  repo_root="${AGENT_INSTALL_DIR:-$HOME/.local/share/code-is-cheap}"
  if [[ -e "$repo_root" ]]; then
    [[ -d "$repo_root/.git" ]] || die "install directory is not a checkout: $repo_root"
    [[ "$(git -C "$repo_root" remote get-url origin)" == 'https://github.com/noho/code-is-cheap.git' ]] || die 'unexpected checkout origin'
    [[ "$(git -C "$repo_root" branch --show-current)" == main ]] || die 'installer checkout must be on main'
    [[ -z "$(git -C "$repo_root" status --porcelain)" ]] || die 'installer checkout has local changes'
    git -C "$repo_root" pull --ff-only origin main
  else
    mkdir -p "$(dirname "$repo_root")"
    git clone --branch main https://github.com/noho/code-is-cheap.git "$repo_root"
  fi
fi

export PATH="$HOME/.local/bin:$PATH"
state_dir="$HOME/.local/share/code-is-cheap-installer"
mkdir -p "$state_dir"
uv venv --python "$(command -v python3)" --allow-existing "$state_dir/venv"
uv pip install --python "$state_dir/venv/bin/python" 'PyYAML==6.0.3'
export SKILL_VALIDATOR_PYTHON="$state_dir/venv/bin/python"
export SKILL_VALIDATOR="$repo_root/scripts/validate-skill.py"
"$repo_root/scripts/validate-skills.sh"

# Initialize private connections only when absent; validate existing files.
python3 "$repo_root/scripts/agent-endpoint.py" --initialize
python3 "$repo_root/scripts/agent-endpoint.py" --check
mkdir -p "$HOME/.codex/skills" "$HOME/.claude/skills"
"$repo_root/scripts/sync-skills.sh"
"$repo_root/scripts/sync-agent-tools.sh"
"$repo_root/scripts/sync-codex-agent.sh"
uv tool install --force 'claude-code-tools==1.29.1'

python3 - <<'PY'
from pathlib import Path
path = Path.home() / '.zshrc'
original = path.read_text() if path.exists() else ''
marker = '# code-is-cheap launchers'
if marker not in original:
    with path.open('a') as stream:
        stream.write('\n' + marker + '\nexport PATH="$HOME/.local/bin:$PATH"\n'
                     '[[ -r "$HOME/.config/zsh/agent-tools.zsh" ]] && source "$HOME/.config/zsh/agent-tools.zsh"\n')
PY
if [[ "$install_service" == true ]]; then
  "$HOME/.codex-agent/bin/codex-auto-review-shim-service" install
fi
echo 'Installed. Set connection api_key values in ~/.config/agent-tools/endpoints.json.'
echo 'Keep current connections in default; add whole runtime connections in override to switch gateways.'
echo 'Run: source ~/.zshrc; open new Agent sessions to reload skills.'
