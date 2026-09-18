#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
targets=(
  "$HOME/.codex/skills"
  "$HOME/.claude/skills"
)
obsolete_skills=(
  "init-agents"
)

"$repo_root/scripts/validate-skills.sh"

for target in "${targets[@]}"; do
  if [[ ! -d "$target" ]]; then
    echo "Skipping missing target: $target"
    continue
  fi

  echo "Syncing skills to $target"
  for skill_name in "${obsolete_skills[@]}"; do
    obsolete_path="$target/$skill_name"
    if [[ -d "$obsolete_path" ]]; then
      echo "Removing obsolete skill: $obsolete_path"
      rm -rf -- "$obsolete_path"
    fi
  done

  for skill_dir in "$repo_root"/skills/*; do
    [[ -d "$skill_dir" ]] || continue
    skill_name="$(basename "$skill_dir")"
    mkdir -p "$target/$skill_name"
    rsync -a --delete --exclude '.DS_Store' "$skill_dir/" "$target/$skill_name/"
  done
done
