#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
validator="${SKILL_VALIDATOR:-$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py}"
python_cmd="${SKILL_VALIDATOR_PYTHON:-${PYTHON:-}}"

if [[ ! -f "$validator" ]]; then
  echo "Skill validator not found: $validator" >&2
  echo "Set SKILL_VALIDATOR=/path/to/quick_validate.py and retry." >&2
  exit 1
fi

if [[ -z "$python_cmd" ]]; then
  for candidate in python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 python; do
    if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import yaml' >/dev/null 2>&1; then
      python_cmd="$candidate"
      break
    fi
  done
fi

if [[ -z "$python_cmd" ]] || ! "$python_cmd" -c 'import yaml' >/dev/null 2>&1; then
  echo "Could not find a Python interpreter with PyYAML installed." >&2
  echo "Install it with: python3 -m pip install pyyaml" >&2
  echo "Or set SKILL_VALIDATOR_PYTHON=/path/to/python with PyYAML available." >&2
  exit 1
fi

for skill_dir in "$repo_root"/skills/*; do
  [[ -d "$skill_dir" ]] || continue
  echo "Validating ${skill_dir#$repo_root/}"
  "$python_cmd" "$validator" "$skill_dir"
done
