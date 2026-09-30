#!/usr/bin/env python3
"""Sync only the model defaults from a card into an independent Codex home."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import tempfile
import tomllib
from pathlib import Path


KEYS = ("model", "model_reasoning_effort")
ASSIGNMENT = re.compile(r"^\s*(model|model_reasoning_effort)\s*=")
SECTION = re.compile(r"^\s*\[")


def compose(original: str, card: str) -> str:
    current = tomllib.loads(original)
    defaults = tomllib.loads(card)
    values = {key: defaults.get(key) for key in KEYS}
    if any(not isinstance(value, str) or not value for value in values.values()):
        raise ValueError("card must define nonempty model and model_reasoning_effort strings")
    if values["model"] != "gpt-6.1-sol":
        raise ValueError("business defaults must use the gpt-6-sol card")

    lines = original.splitlines(keepends=True)
    header_end = next((i for i, line in enumerate(lines) if SECTION.match(line)), len(lines))
    seen: set[str] = set()
    for i in range(header_end):
        match = ASSIGNMENT.match(lines[i])
        if match:
            key = match.group(1)
            lines[i] = f"{key} = {json.dumps(values[key])}\n"
            seen.add(key)

    missing = [f"{key} = {json.dumps(values[key])}\n" for key in KEYS if key not in seen]
    if missing:
        lines[header_end:header_end] = missing
    result = "".join(lines)
    parsed = tomllib.loads(result)
    if any(parsed.get(key) != value for key, value in values.items()):
        raise ValueError("could not set top-level business model defaults")
    if any(parsed.get(key) != value for key, value in current.items() if key not in KEYS):
        raise ValueError("sync would change unrelated business settings")
    return result


def sync(config: Path, card: Path) -> bool:
    if config.is_symlink() or not config.is_file():
        raise ValueError(f"config must be an existing regular file, not a symlink: {config}")
    original = config.read_text()
    result = compose(original, card.read_text())
    if result == original:
        return False

    mode = stat.S_IMODE(config.stat().st_mode)
    fd, tmp_name = tempfile.mkstemp(prefix=".config.toml.", dir=config.parent)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "w") as stream:
            stream.write(result)
            stream.flush()
            os.fsync(stream.fileno())
        if config.is_symlink() or config.read_text() != original:
            raise ValueError(f"config changed during sync; retry: {config}")
        os.replace(tmp_name, config)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--card", required=True, type=Path)
    args = parser.parse_args()
    try:
        changed = sync(args.config, args.card)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        parser.error(str(exc))
    print(f"{'synced' if changed else 'already current'} business model defaults: {args.config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
