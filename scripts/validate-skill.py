#!/usr/bin/env python3
"""Validate this repository's skill metadata without a preinstalled skill home."""
import re
import sys
from pathlib import Path
import yaml

def validate(path):
    text = (path / "SKILL.md").read_text()
    match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.S)
    if not match:
        raise ValueError("missing YAML frontmatter")
    meta = yaml.safe_load(match[1])
    if not isinstance(meta, dict):
        raise ValueError("metadata must be an object")
    if set(meta) - {"name", "description", "license", "allowed-tools", "metadata"}:
        raise ValueError("unknown metadata fields")
    if meta.get("name") != path.name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", path.name) or len(path.name) > 64:
        raise ValueError("name must match the skill directory and use hyphen case")
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip() or len(description) > 1024 or '<' in description or '>' in description:
        raise ValueError("invalid description")

if __name__ == '__main__':
    try:
        validate(Path(sys.argv[1]))
    except (OSError, ValueError, yaml.YAMLError, IndexError) as exc:
        sys.exit(f"Skill validation failed: {exc}")
    print('Skill is valid!')
