#!/usr/bin/env python3
"""Compose a desktop-app CODEX_HOME config from the shared base + a model card.

The ChatGPT desktop app reads `$CODEX_HOME/config.toml` in full and has no `-p`
card layering (app instances are launched via `open`, not `codex app`), so each
managed app instance gets its own real directory whose config is the shared
base text with the agent's model-card keys overlaid (card wins).

The overlay is textual and idempotent: re-running refreshes card-owned top-level
keys and the shared base's provider registry while preserving anything else in
the destination (including state the app has written since).

Usage:
  compose-codex-app-config.py --base ~/.codex/config.toml \
    --card ~/.codex/kimi.config.toml --out <app-home>/config.toml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SECTION_RE = re.compile(r"^\[([^\]]+)\]\s*$")
KEY_RE = re.compile(r"^([A-Za-z0-9_]+)\s*=")


def split_sections(text: str) -> tuple[str, dict[str, str]]:
    """Split TOML text into (header, {section_name: section_text})."""
    header_lines: list[str] = []
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        m = SECTION_RE.match(line.strip())
        if m:
            name = m.group(1)
            current = name
            sections.setdefault(name, []).append(line)
        elif current is None:
            header_lines.append(line)
        else:
            sections[current].append(line)
    return "\n".join(header_lines), {k: "\n".join(v) for k, v in sections.items()}


def scalar_overrides(card_header: str) -> dict[str, str]:
    """Top-level `key = value` assignments from the card header (comments skipped)."""
    out: dict[str, str] = {}
    for line in card_header.splitlines():
        m = KEY_RE.match(line.strip())
        if m:
            out[m.group(1)] = line.strip()[len(m.group(1)) :].lstrip()[1:].strip()
    return out


def apply_scalars(header: str, overrides: dict[str, str]) -> str:
    lines = header.splitlines()
    seen: set[str] = set()
    for i, line in enumerate(lines):
        m = KEY_RE.match(line.strip())
        if m and m.group(1) in overrides:
            lines[i] = f"{m.group(1)} = {overrides[m.group(1)]}"
            seen.add(m.group(1))
    missing = [f"{k} = {v}" for k, v in overrides.items() if k not in seen]
    return "\n".join(lines + missing)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--base", required=True, help="shared-home base config.toml")
    ap.add_argument("--card", required=True, help="model card to overlay")
    ap.add_argument("--out", required=True, help="destination config.toml (composed app home)")
    args = ap.parse_args()

    out_path = Path(args.out)
    shared_path = Path(args.base)
    if not shared_path.is_file():
        ap.error(f"shared base config missing: {shared_path}; run sync-codex-agent.sh")
    shared_text = shared_path.read_text()
    base_text = out_path.read_text() if out_path.exists() else shared_text
    card_text = Path(args.card).read_text()

    card_header, card_sections = split_sections(card_text)
    base_header, base_sections = split_sections(base_text)
    _, shared_sections = split_sections(shared_text)

    header = apply_scalars(base_header, scalar_overrides(card_header))
    for name, body in shared_sections.items():
        if name.startswith("model_providers."):
            base_sections[name] = body
    for name, body in card_sections.items():
        if name.startswith("model_providers."):
            # During an upgrade the installed card may still use the old format.
            # Its model_provider ID may be shared by gateway variants, so keep
            # the old card's route until sync-codex-agent.sh replaces the card.
            base_sections[name] = body
            print(f"warning: legacy provider table in {args.card}; re-sync Codex cards", file=sys.stderr)

    parts = [header.rstrip()]
    parts += [body.rstrip() for body in base_sections.values()]
    out_path.write_text("\n\n".join(p for p in parts if p) + "\n")
    print(f"composed {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
