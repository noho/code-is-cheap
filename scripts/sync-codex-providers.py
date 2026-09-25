#!/usr/bin/env python3
"""Atomically sync repository-owned provider tables into a Codex base config.

Only the marked block belongs to this repository. An unmarked table with a
managed provider ID is an ownership conflict, so stop instead of overwriting it.
"""

from __future__ import annotations

import argparse
import os
import stat
import tempfile
import tomllib
from pathlib import Path

START = "# BEGIN code-is-cheap managed model providers"
END = "# END code-is-cheap managed model providers"


def compose(base_text: str, registry_text: str) -> str:
    registry = tomllib.loads(registry_text)
    providers = registry.get("model_providers")
    if (set(registry) != {"model_providers"} or not isinstance(providers, dict)
            or not providers or any(not isinstance(value, dict) or not value for value in providers.values())):
        raise ValueError("registry must contain only nonempty [model_providers.*] tables")
    managed_ids = set(providers)

    if base_text.count(START) != base_text.count(END) or base_text.count(START) > 1:
        raise ValueError("incomplete or duplicate managed provider block")
    if START in base_text and base_text.index(END) < base_text.index(START):
        raise ValueError("managed provider block end precedes start")
    if START in base_text:
        before, rest = base_text.split(START, 1)
        _, after = rest.split(END, 1)
        outside = before + after
    else:
        outside = base_text

    existing = tomllib.loads(outside).get("model_providers", {})
    if not isinstance(existing, dict):
        raise ValueError("base model_providers must be a table")
    overlap = managed_ids & set(existing)
    if overlap:
        raise ValueError("provider IDs already owned outside managed block: " + ", ".join(sorted(overlap)))

    result = outside.rstrip() + "\n\n" + START + "\n" + registry_text.strip() + "\n" + END + "\n"
    tomllib.loads(result)  # Refuse to replace a valid config with invalid TOML.
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--registry", required=True, type=Path)
    args = ap.parse_args()

    base = args.base
    if base.is_symlink():
        ap.error(f"base config must be a regular file, not a symlink: {base}")
    if base.exists() and not base.is_file():
        ap.error(f"base config must be a regular file: {base}")
    existed = base.exists()
    try:
        original = base.read_text() if existed else ""
        result = compose(original, args.registry.read_text())
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        ap.error(str(exc))

    if result == original:
        print(f"provider registry already current: {base}")
        return 0

    try:
        fd, tmp_name = tempfile.mkstemp(prefix=".config.toml.", dir=base.parent)
    except OSError as exc:
        ap.error(f"cannot create temporary config: {exc}")
    try:
        try:
            os.fchmod(fd, stat.S_IMODE(base.stat().st_mode) if existed else 0o600)
            with os.fdopen(fd, "w") as stream:
                stream.write(result)
                stream.flush()
                os.fsync(stream.fileno())
            if base.is_symlink() or base.exists() != existed or (existed and base.read_text() != original):
                ap.error(f"base config changed during sync; retry: {base}")
            os.replace(tmp_name, base)
        except OSError as exc:
            try:
                os.close(fd)
            except OSError:
                pass
            ap.error(f"cannot update base config: {exc}")
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    print(f"synced provider registry: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
