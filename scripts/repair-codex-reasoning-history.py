#!/usr/bin/env python3
"""Repair third-party reasoning fields that OpenAI rejects on session replay.

By default this only reports the number of affected rollout items. --apply
creates a private backup beside the rollout before atomically replacing it.
Close every Codex client using the session before applying the repair.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path


def repair_lines(data: bytes, drop_reasoning_models: frozenset[str] = frozenset(),
                 drop_counts: dict[str, int] | None = None) -> tuple[bytes, int]:
    changed = 0
    result: list[bytes] = []
    current_model: str | None = None
    for number, line in enumerate(data.splitlines(keepends=True), 1):
        if not line.strip():
            result.append(line)
            continue
        try:
            item = json.loads(line)
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError(f"invalid JSONL at line {number}: {exc}; repair the malformed line separately") from exc
        if not isinstance(item, dict):
            raise ValueError(f"JSONL object expected at line {number}")
        payload = item.get("payload")
        if item.get("type") == "turn_context" and isinstance(payload, dict):
            current_model = payload.get("model")
            if not isinstance(current_model, str):
                raise ValueError(f"invalid model in turn_context at line {number}; no files changed")
        if item.get("type") != "response_item" or not isinstance(payload, dict) or payload.get("type") != "reasoning":
            result.append(line)
            continue
        if current_model in drop_reasoning_models:
            changed += 1
            if drop_counts is not None:
                drop_counts[current_model] += 1
            continue
        content = payload.get("content")
        strip_content = isinstance(content, list) and bool(content)
        if not strip_content:
            result.append(line)
            continue
        if strip_content and not all(isinstance(part, dict) and part.get("type") == "reasoning_text" for part in content):
            raise ValueError(f"unsupported reasoning content at line {number}; no files changed")
        payload["content"] = None
        ending = b"\r\n" if line.endswith(b"\r\n") else b"\n" if line.endswith(b"\n") else b"\r" if line.endswith(b"\r") else b""
        result.append(json.dumps(item, ensure_ascii=False, separators=(",", ":")).encode() + ending)
        changed += 1
    return b"".join(result), changed


def private_new_file(directory: Path, prefix: str, data: bytes, mode: int) -> Path:
    fd, name = tempfile.mkstemp(prefix=prefix, dir=directory)
    path = Path(name)
    try:
        os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def write_backup(path: Path, data: bytes, mode: int) -> None:
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, mode)
    try:
        with os.fdopen(fd, "wb") as saved:
            os.fchmod(saved.fileno(), mode)
            saved.write(data)
            saved.flush()
            os.fsync(saved.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rollout", type=Path, help="rollout-*.jsonl file to inspect")
    parser.add_argument("--apply", action="store_true", help="back up and atomically repair the rollout")
    parser.add_argument("--drop-reasoning-model", action="append", default=[], metavar="MODEL",
                        help="remove reasoning items from turns using MODEL; repeat as needed")
    args = parser.parse_args()

    path = args.rollout
    if path.is_symlink() or not path.is_file():
        parser.error("rollout must be an existing regular file, not a symlink")
    before_stat = path.stat()
    before = path.read_bytes()
    drop_counts = dict.fromkeys(args.drop_reasoning_model, 0)
    try:
        after, count = repair_lines(before, frozenset(args.drop_reasoning_model), drop_counts)
    except ValueError as exc:
        parser.error(str(exc))
    print(f"affected reasoning items: {count}")
    for model, dropped in drop_counts.items():
        print(f"dropped reasoning items for {model}: {dropped}")
        if dropped == 0:
            print(f"warning: no reasoning items matched model {model!r}; check turn_context model names", file=sys.stderr)
    if not args.apply or count == 0:
        return 0

    mode = stat.S_IMODE(before_stat.st_mode) & 0o600
    stamp = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{time.time_ns()}"
    backup = path.with_name(f"{path.name}.backup-{stamp}")
    if backup.exists():
        parser.error(f"backup already exists: {backup}")
    temp = private_new_file(path.parent, f".{path.name}.repair-", after, mode)
    try:
        current_stat = path.stat()
        if (current_stat.st_dev, current_stat.st_ino, current_stat.st_size, current_stat.st_mtime_ns) != (
            before_stat.st_dev, before_stat.st_ino, before_stat.st_size, before_stat.st_mtime_ns
        ) or path.read_bytes() != before:
            parser.error("rollout changed while preparing repair; close Codex and retry")
        write_backup(backup, before, mode)
        current_stat = path.stat()
        if (current_stat.st_dev, current_stat.st_ino, current_stat.st_size, current_stat.st_mtime_ns) != (
            before_stat.st_dev, before_stat.st_ino, before_stat.st_size, before_stat.st_mtime_ns
        ) or path.read_bytes() != before:
            parser.error("rollout changed during backup; original left untouched")
        os.replace(temp, path)
        print(f"repaired: {path}")
        print(f"backup: {backup}")
    finally:
        temp.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as exc:
        sys.exit(f"repair-codex-reasoning-history.py: error: {exc}")
