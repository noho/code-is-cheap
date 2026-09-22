#!/usr/bin/env python3
"""Merge a tracked Codex config template with the live file it will replace.

Why this exists
---------------
The templates under `codex-agent/profiles/` carry only what this repository
owns: model, reasoning effort, sandbox, approvals, web_search, service_tier and
the shell environment policy. The live files carry much more, because Codex
itself and the ChatGPT desktop app write into them: `[projects.*]` trust
entries, `[hooks.state]` hashes, `[mcp_servers.*]`, `[plugins.*]`,
`[marketplaces.*]`, `[tui.*]`, `[desktop]`, and root-level keys such as
`notify` — including versioned paths that change whenever the app updates. None
of that belongs in a versioned template, and dropping it on sync breaks the
profile.

So the sync script installs the template merged with everything the live file
had that the template does not define. Granularity is one root-level key or one
whole table: a live entry survives only when the template has no entry with the
same name. That keeps the repository authoritative for everything it defines and
the live machine authoritative for everything it does not.

Root-level keys are emitted before the first table, because a key written after
a `[table]` header would silently become part of that table.

Usage
-----
  codex-config-merge.py --template TEMPLATE [--live LIVE]

Prints the merged config to stdout. Without --live (or with an unreadable live
path) it prints the template unchanged. Exits non-zero when the template cannot
be read, so the caller can leave the live file untouched rather than install
something it could not derive.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^\s*\[\[?([^\]]+)\]\]?\s*(?:#.*)?$")
ROOT_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.\-]+)\s*=")


def _depth(line: str) -> int:
    """Rough bracket depth of one line, ignoring quoted strings.

    Good enough for machine-written TOML values, which is all this sees. It is
    only used to decide whether a root-level value continues on the next line.
    """
    depth = 0
    quote: str | None = None
    escaped = False
    for ch in line:
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
            continue
        if ch in "\"'":
            quote = ch
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
    return depth


def split_config(text: str) -> tuple[dict[str, list[str]], list[tuple[str, list[str]]]]:
    """Split config text into root-level keys and tables.

    Returns (root_keys, tables), where root_keys maps a key name to its verbatim
    lines and tables is an ordered list of (header name, verbatim lines). Blank
    and comment lines are held back and attached to whatever entry follows them,
    so a comment written above a preserved entry travels with it.
    """
    root_keys: dict[str, list[str]] = {}
    tables: list[tuple[str, list[str]]] = []
    pending: list[str] = []  # blank / comment lines not yet claimed
    header: str | None = None
    block: list[str] = []
    key: str | None = None
    depth = 0

    for line in text.splitlines():
        if key is not None:  # continuation of a multi-line root-level value
            root_keys[key].append(line)
            depth += _depth(line)
            if depth <= 0:
                key = None
            continue

        m = HEADER_RE.match(line)
        if m:
            if header is not None:
                tables.append((header, block))
            header = m.group(1)
            block = pending + [line]
            pending = []
            continue
        if header is None:
            km = ROOT_KEY_RE.match(line)
            if km:
                root_keys[km.group(1)] = pending + [line]
                pending = []
                start_depth = _depth(line)
                if start_depth > 0:
                    key = km.group(1)
                    depth = start_depth
                continue
            pending.append(line)  # blank line or comment at root level
            continue
        block.append(line)

    if header is not None:
        tables.append((header, block))
    return root_keys, tables


def merge(template_text: str, live_text: str) -> str:
    template_root, template_tables = split_config(template_text)
    live_root, live_tables = split_config(live_text)
    owned = set(template_root) | {header for header, _ in template_tables}

    lines: list[str] = []
    for block in template_root.values():
        lines.extend(block)
    for key, block in live_root.items():
        if key not in owned:
            lines.extend(block)

    table_blocks = [block for _, block in template_tables]
    table_blocks += [block for header, block in live_tables if header not in owned]
    for block in table_blocks:
        # A single blank line between tables; blocks usually carry their own
        # leading blank/comment lines over from the source file.
        if lines and lines[-1] != "" and (not block or block[0].strip()):
            lines.append("")
        lines.extend(block)

    return "\n".join(lines).strip("\n") + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--template", required=True, help="tracked template to install")
    ap.add_argument("--live", help="current live file to preserve runtime state from")
    args = ap.parse_args()

    try:
        template_text = Path(args.template).read_text()
    except OSError as exc:
        print(f"ERROR: cannot read template: {exc}", file=sys.stderr)
        return 1

    live_text = ""
    if args.live:
        try:
            live_text = Path(args.live).read_text()
        except OSError:
            print(f"note: no readable live file at {args.live}; installing the template as-is", file=sys.stderr)

    sys.stdout.write(merge(template_text, live_text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
