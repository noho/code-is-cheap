#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
targets=(
  "$HOME/.codex/skills"
  "$HOME/.codex-pro/skills"
  "$HOME/.codex-business/skills"
  "$HOME/.claude/skills"
)

"$repo_root/scripts/validate-skills.sh"

for target in "${targets[@]}"; do
  if [[ ! -d "$target" ]]; then
    echo "Skipping missing target: $target"
    continue
  fi

  echo "Syncing skills to $target"
  for skill_dir in "$repo_root"/skills/*; do
    [[ -d "$skill_dir" ]] || continue
    skill_name="$(basename "$skill_dir")"
    mkdir -p "$target/$skill_name"
    rsync -a --delete --exclude '.DS_Store' "$skill_dir/" "$target/$skill_name/"
  done
done

