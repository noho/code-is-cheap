#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
validator="${SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"

if [[ ! -f "$validator" ]]; then
  echo "Skill validator not found: $validator" >&2
  echo "Set SKILL_VALIDATOR=/path/to/quick_validate.py and retry." >&2
  exit 1
fi

for skill_dir in "$repo_root"/skills/*; do
  [[ -d "$skill_dir" ]] || continue
  echo "Validating ${skill_dir#$repo_root/}"
  python "$validator" "$skill_dir"
done

