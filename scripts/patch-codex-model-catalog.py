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

Copy Codex's current catalog, set `codex-auto-review.tool_mode` to `direct`,
and add the selected profile's session model with its configured context
window. Unknown models otherwise inherit Codex's 272K fallback maximum, which
clamps even an explicit `model_context_window` override. The new entry uses a
current bundled direct-tool model as its schema template, then removes GPT-only
capabilities and forces direct tools. Never check in a generated catalog.

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
                               [--cards-dir DIR] [--output-dir DIR]

Writes ~/.codex/model-catalogs/<profile>.json for each selected profile card.
Standalone mode writes one profile at a time; sync-codex-agent.sh stages all
outputs before installation. Exits 0 on success, 1 if anything was skipped or
looked wrong.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HOME = Path.home()
SHARED_HOME = Path(os.environ.get("CODEX_SHARED_HOME", HOME / ".codex"))
CATALOG_DIR = SHARED_HOME / "model-catalogs"
DEFAULT_PROFILES = ["ds-flash", "glm", "glm-flash", "kimi", "local", "mimo", "mimo-fast", "mimo-flash", "qwen"]
TARGET_ENTRY = "codex-auto-review"
WANT_TOOL_MODE = "direct"
EXPECTED_BEFORE = "code_mode_only"
SESSION_TEMPLATE = "gpt-5.4"

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

    return catalog, True


def profile_model(profile: str, cards_dir: Path) -> tuple[str, int] | None:
    cfg = cards_dir / f"{profile}.config.toml"
    if not cfg.is_file():
        warn(f"{profile}: model card is missing: {cfg}")
        return None
    try:
        card = tomllib.loads(cfg.read_text())
    except (OSError, tomllib.TOMLDecodeError) as exc:
        warn(f"{profile}: cannot read model card: {exc}")
        return None
    model = card.get("model")
    window = card.get("model_context_window")
    expected_catalog = CATALOG_DIR / f"{profile}.json"
    if (not isinstance(model, str) or not model or type(window) is not int
            or window <= 0 or card.get("model_catalog_json") != str(expected_catalog)):
        warn(f"{profile}: card needs a model, positive context window and catalog path {expected_catalog}")
        return None
    return model, window


def session_entry(catalog: dict, model: str, window: int) -> dict | None:
    models = catalog["models"]
    if any(entry_key(entry) == model for entry in models):
        warn(f"{model}: already present in Codex's catalog; refusing to replace built-in metadata")
        return None
    template = next((entry for entry in models if entry_key(entry) == SESSION_TEMPLATE), None)
    if (template is None or not isinstance(template.get("base_instructions"), str)
            or template.get("tool_mode") not in (None, "direct")
            or template.get("shell_type") != "unified_exec"
            or template.get("use_responses_lite") is not False
            or template.get("experimental_supported_tools") != []):
        warn(f"{SESSION_TEMPLATE}: direct-tool template shape changed; inspect Codex's new catalog")
        return None
    # Catalog entries require base instructions. Reusing the installed Codex
    # template keeps the generated file in sync with this binary, while the
    # explicit fields below restore the third-party fallback's tool behavior.
    entry = copy.deepcopy(template)
    entry.update(
        slug=model,
        display_name=model,
        description="Third-party model profile",
        visibility="none",
        priority=99,
        context_window=window,
        max_context_window=window,
        tool_mode="direct",
        model_messages=None,
        default_reasoning_level=None,
        supported_reasoning_levels=[],
        default_reasoning_summary="auto",
        support_verbosity=False,
        default_verbosity=None,
        apply_patch_tool_type=None,
        web_search_tool_type="text",
        truncation_policy={"mode": "bytes", "limit": 10_000},
        supports_search_tool=False,
        supports_image_detail_original=False,
        include_skills_usage_instructions=False,
        include_plugin_usage_instructions=False,
        include_apps_usage_instructions=False,
        additional_speed_tiers=[],
        service_tiers=[],
        default_service_tier=None,
        upgrade=None,
        comp_hash=None,
        input_modalities=["text", "image"],
    )
    return entry


def write_targets(catalog: dict, profiles: list[str], dry_run: bool, cards_dir: Path, output_dir: Path) -> int:
    written = 0
    for profile in profiles:
        model_config = profile_model(profile, cards_dir)
        if model_config is None:
            continue
        model, window = model_config
        entry = session_entry(catalog, model, window)
        if entry is None:
            continue
        generated = copy.deepcopy(catalog)
        generated["models"].append(entry)
        target = output_dir / f"{profile}.json"
        if dry_run:
            print(f"dry-run: would write {target} ({model}, {window} tokens)")
            written += 1
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(generated, indent=2) + "\n")
        os.replace(tmp, target)
        print(f"wrote {target} ({target.stat().st_size} bytes)")
        written += 1
    return written


def verify(path: Path, profile: str, cards_dir: Path) -> None:
    """Read back a written catalog and confirm the patched field."""
    try:
        models = json.loads(path.read_text())["models"]
    except Exception as exc:  # noqa: BLE001 - report anything read back badly
        warn(f"{path}: cannot re-read written catalog ({exc})")
        return
    entry = next((m for m in models if entry_key(m) == TARGET_ENTRY), None)
    if entry is None or entry.get("tool_mode") != WANT_TOOL_MODE:
        warn(f"{path}: verification failed — `{TARGET_ENTRY}.tool_mode` is not {WANT_TOOL_MODE!r}")
    model_config = profile_model(profile, cards_dir)
    if model_config is None:
        return
    model, window = model_config
    session = [m for m in models if entry_key(m) == model]
    if len(session) != 1 or session[0].get("max_context_window") != window or session[0].get("tool_mode") != "direct":
        warn(f"{path}: session model {model} is missing or has incorrect window/tool metadata")


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="report actions without writing")
    ap.add_argument("--source", metavar="FILE", help="use a pre-rendered catalog instead of running codex")
    ap.add_argument("--profiles", default=",".join(DEFAULT_PROFILES), help="comma-separated profile names")
    ap.add_argument("--cards-dir", type=Path, default=SHARED_HOME, help="read installed profile cards here")
    ap.add_argument("--output-dir", type=Path, default=CATALOG_DIR, help="write generated catalogs here")
    args = ap.parse_args()

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    catalog = load_source(args.source)
    patched, ok = patch(catalog)
    if not ok:
        print("nothing written", file=sys.stderr)
        return 1

    count = write_targets(patched, profiles, args.dry_run, args.cards_dir, args.output_dir)
    if not args.dry_run:
        for profile in profiles:
            target = args.output_dir / f"{profile}.json"
            if target.is_file():
                verify(target, profile, args.cards_dir)

    if warnings:
        print(f"\n{len(warnings)} warning(s) — catalog may be stale; see above", file=sys.stderr)
        return 1
    print(f"ok: {count} catalog(s) {'checked' if args.dry_run else 'written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
