#!/usr/bin/env python3
"""Generate the patched Codex model catalogs for the third-party profiles.

Why this exists
---------------
Codex's auto-review guardian (`approvals_reviewer = "auto_review"`) always asks
for the catalog model id `codex-auto-review`. With the stock catalog that entry
carries `tool_mode = "code_mode_only"`, which makes Codex attach a code-mode
`additional_tools` developer item containing a custom `exec` tool. Several
third-party gateways (kimi, mimo) reject that item, so every escalation fails
closed and unattended dispatch breaks.

The fix is a one-field patch: copy Codex's built-in catalog and flip
`codex-auto-review.tool_mode` from `code_mode_only` to `direct`. The resulting
catalog deliberately contains **no session-model entries** — the profiles'
models (deepseek-flash, kimi-k3, mimo-v2.6-pro, mimo-v2.6-flash, mimo-v2.6-pro-ultraspeed, qwen3.8-max, ...) keep using
fallback metadata. Do not "fix" that by adding catalog entries for them: giving
a session model real catalog metadata changes which tools Codex exposes and was
observed to break tool calling entirely.

Source of truth
---------------
`codex debug models` renders Codex's built-in catalog as JSON. It must be run
under a **fresh, empty CODEX_HOME** — any existing home can carry a
`model_catalog_json` (or other config) that changes what is rendered. The
verifier in this script compares against the expected shape and warns loudly
when the format drifts, which is the failure mode to watch after Codex
upgrades.

Usage
-----
  patch-codex-model-catalog.py [--dry-run] [--source FILE] [--profiles a,b,c]

Writes ~/.codex-agent/codex/model-catalogs/<profile>.json for each profile card
(`codex -p <profile>`) that sets `model_catalog_json`. Exits 0 on success, 1 if
anything was skipped or looked wrong — warnings are printed to stderr either way.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
AGENT_DIR = HOME / ".codex-agent"
SHARED_HOME = AGENT_DIR / "codex"
CATALOG_DIR = SHARED_HOME / "model-catalogs"
DEFAULT_PROFILES = ["kimi", "mimo", "mimo-fast", "mimo-flash", "qwen"]
TARGET_ENTRY = "codex-auto-review"
WANT_TOOL_MODE = "direct"
EXPECTED_BEFORE = "code_mode_only"

# Every third-party session model that must NOT appear in the catalog.
SESSION_MODEL_PROFILES = ["ds-flash", "glm", "glm-flash", "kimi", "mimo", "mimo-fast", "mimo-flash", "qwen", "local"]

warnings: list[str] = []


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"WARNING: {msg}", file=sys.stderr)


def run_codex_debug_models() -> dict:
    """Render Codex's built-in catalog under a fresh empty CODEX_HOME."""
    with tempfile.TemporaryDirectory(prefix="catalog-src.") as fresh_home:
        env = dict(os.environ, CODEX_HOME=fresh_home)
        try:
            out = subprocess.run(
                ["codex", "debug", "models"],
                env=env,
                capture_output=True,
                check=True,
            ).stdout
        except FileNotFoundError:
            raise SystemExit("ERROR: `codex` not found on PATH")
        except subprocess.CalledProcessError as exc:
            raise SystemExit(
                f"ERROR: `codex debug models` failed (exit {exc.returncode}): "
                f"{exc.stderr.decode(errors='replace').strip()[:400]}"
            )
    return json.loads(out)


def load_source(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text())
    return run_codex_debug_models()


def entry_key(model: dict) -> str:
    return model.get("slug") or model.get("id") or ""


def session_models() -> dict[str, str]:
    """model id per profile, read from each profile's model card."""
    found = {}
    for profile in SESSION_MODEL_PROFILES:
        cfg = SHARED_HOME / f"{profile}.config.toml"
        if not cfg.is_file():
            continue
        m = re.search(r'^model\s*=\s*"([^"]+)"', cfg.read_text(), re.MULTILINE)
        if m:
            found[profile] = m.group(1)
    return found


def patch(catalog: dict) -> tuple[dict, bool]:
    models = catalog.get("models")
    if not isinstance(models, list) or not models:
        warn("catalog has no `models` array — format changed? nothing written")
        return catalog, False

    target = next((m for m in models if entry_key(m) == TARGET_ENTRY), None)
    if target is None:
        warn(
            f"`{TARGET_ENTRY}` missing from the built-in catalog — the guardian "
            f"model id may have been renamed; nothing written"
        )
        return catalog, False

    before = target.get("tool_mode")
    if before == WANT_TOOL_MODE:
        print(f"note: `{TARGET_ENTRY}` already `{WANT_TOOL_MODE}` (catalog may be pre-patched)")
    elif before != EXPECTED_BEFORE:
        warn(
            f"`{TARGET_ENTRY}.tool_mode` is {before!r}, expected "
            f"{EXPECTED_BEFORE!r} — Codex changed it; review before trusting this patch"
        )
        return catalog, False
    target["tool_mode"] = WANT_TOOL_MODE

    # Safety property: no session model may gain catalog metadata here.
    keys = {entry_key(m) for m in models}
    leaked = {p: m for p, m in session_models().items() if m in keys}
    if leaked:
        warn(
            "session model(s) present in the catalog: "
            + ", ".join(f"{p}={m}" for p, m in leaked.items())
            + " — writing it would change session tool exposure; nothing written"
        )
        return catalog, False

    return catalog, True


def write_targets(catalog: dict, profiles: list[str], dry_run: bool) -> int:
    written = 0
    for profile in profiles:
        target = CATALOG_DIR / f"{profile}.json"
        cfg = SHARED_HOME / f"{profile}.config.toml"
        if cfg.is_file() and "model_catalog_json" not in cfg.read_text():
            warn(f"{profile}: model card has no `model_catalog_json` — skipped")
            continue
        if dry_run:
            print(f"dry-run: would write {target}")
            written += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(catalog, indent=2) + "\n")
        shutil.move(tmp, target)
        print(f"wrote {target} ({target.stat().st_size} bytes)")
        written += 1
    return written


def verify(path: Path) -> None:
    """Read back a written catalog and confirm the patched field."""
    try:
        models = json.loads(path.read_text())["models"]
    except Exception as exc:  # noqa: BLE001 - report anything read back badly
        warn(f"{path}: cannot re-read written catalog ({exc})")
        return
    entry = next((m for m in models if entry_key(m) == TARGET_ENTRY), None)
    if entry is None or entry.get("tool_mode") != WANT_TOOL_MODE:
        warn(f"{path}: verification failed — `{TARGET_ENTRY}.tool_mode` is not {WANT_TOOL_MODE!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="report actions without writing")
    ap.add_argument("--source", metavar="FILE", help="use a pre-rendered catalog instead of running codex")
    ap.add_argument("--profiles", default=",".join(DEFAULT_PROFILES), help="comma-separated profile names")
    args = ap.parse_args()

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    catalog = load_source(args.source)
    patched, ok = patch(catalog)
    if not ok:
        print("nothing written", file=sys.stderr)
        return 1

    count = write_targets(patched, profiles, args.dry_run)
    if not args.dry_run:
        for profile in profiles:
            target = CATALOG_DIR / f"{profile}.json"
            if target.is_file():
                verify(target)

    if warnings:
        print(f"\n{len(warnings)} warning(s) — catalog may be stale; see above", file=sys.stderr)
        return 1
    print(f"ok: {count} catalog(s) {'checked' if args.dry_run else 'written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
