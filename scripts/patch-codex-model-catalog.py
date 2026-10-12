#!/usr/bin/env python3
"""Assemble official cloud catalogs and the unchanged local direct-tool fallback.

Cloud inputs are byte-verified tracked snapshots, preserved in full. Only the
user-authorized GLM Flash identity derivation and independent native guardian
transport adaptations are applied. --source supplies native guardian/local
metadata only. The installed CLI parses every assembled catalog in an empty
home before any output replacement. --dry-run never writes the output directory.
Standalone writes are per file; sync owns narrow ordinary-install rollback.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
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
SOURCE_DIR = Path(__file__).resolve().parents[1] / "codex-agent/catalog-sources"
# Approved byte snapshots. --source injects only the independent native source.
SOURCE_HASHES = {
    "ds": "d47876f3bca395fe2d9d3c7fc7312282a60da8a2479dd13b995cb8e0fe2695dd",
    "glm": "94cf9e8df540be39aa2948bf14ae665ec76699b1740d5344f499dd67fc71d1a3",
    "kimi": "61990fe840fe299eafc08460b16da5b53c720cc34ccd147e820265dd2f1f50d4",
    "mimo": "8834dc34d879b8489b7376a5a1788f0d1b696f8410fc2df3544ad38ab145601a",
    "qwen": "4bc94831cb66e43aaf4c375543f92883bfa1d3116a4065c5796c5de29e8a019c",
}
OFFICIAL = {
    "ds-flash": ("ds", "deepseek-flash", "deepseek-flash"),
    "glm": ("glm", "glm-5.3", "glm-5.3"),
    "glm-flash": ("glm", "glm-5.3", "glm-5.3-flash"),
    "kimi": ("kimi", "k3", "k3"),
    "mimo": ("mimo", "mimo-v2.6-pro", "mimo-v2.6-pro"),
    "mimo-fast": ("mimo", "mimo-v2.6-pro-ultraspeed", "mimo-v2.6-pro-ultraspeed"),
    "mimo-flash": ("mimo", "mimo-v2.6-flash", "mimo-v2.6-flash"),
    "qwen": ("qwen", "qwen3.8-max", "qwen3.8-max"),
}

warnings: list[str] = []


def warn(msg: str) -> None:
    warnings.append(msg)
    print(f"WARNING: {msg}", file=sys.stderr)


def native_models(path: Path | None = None) -> dict:
    """Native parser owns the schema; never serialize its output as our input."""
    with tempfile.TemporaryDirectory(prefix="catalog-src.") as fresh_home:
        env = dict(os.environ, HOME=fresh_home, CODEX_HOME=fresh_home,
                   CODEX_SQLITE_HOME=fresh_home)
        cmd = (["codex", "-c", f'model_catalog_json={json.dumps(str(path.resolve()))}',
                "debug", "models"] if path else ["codex", "debug", "models", "--bundled"])
        try:
            out = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                check=True,
            ).stdout
        except FileNotFoundError:
            raise ValueError("`codex` not found on PATH") from None
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"native parser failed (exit {exc.returncode}): "
                             f"{exc.stderr.decode(errors='replace').strip()}") from None
    return json.loads(out)


def run_codex_debug_models() -> dict:
    return native_models()


def load_source(path: str | None) -> dict:
    if path:
        return json.loads(Path(path).read_text())
    return run_codex_debug_models()


def official_source(profile: str) -> dict:
    family, source_slug, _ = OFFICIAL[profile]
    path = SOURCE_DIR / f"{family}-model-catalogs.json"
    try:
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != SOURCE_HASHES[family]:
            raise ValueError("source SHA-256 differs from approved snapshot")
        catalog = json.loads(raw)
        if not isinstance(catalog, dict):
            raise ValueError("source root must be an object")
        models = catalog.get("models")
        if not isinstance(models, list) or not models:
            raise ValueError("source models must be a nonempty array")
        slugs = []
        for entry in models:
            if not isinstance(entry, dict) or not isinstance(entry.get("slug"), str) or not entry["slug"].strip():
                raise ValueError("every source model needs a nonempty string slug")
            slugs.append(entry["slug"])
        if len(set(slugs)) != len(slugs):
            raise ValueError("duplicate source slug")
        if TARGET_ENTRY in slugs:
            raise ValueError(f"source collides with reserved {TARGET_ENTRY}")
        if source_slug not in slugs:
            raise ValueError("mapped source slug is missing")
        return catalog
    except (OSError, ValueError) as exc:
        raise ValueError(f"{profile}: {path}, source slug {source_slug}: {exc}") from None


def guardian_entry(native: dict, profile: str) -> dict:
    models = native.get("models") if isinstance(native, dict) else None
    entries = [m for m in models or [] if isinstance(m, dict) and m.get("slug") == TARGET_ENTRY]
    if len(entries) != 1 or entries[0].get("tool_mode") != "code_mode_only" or entries[0].get("use_responses_lite") is not True:
        raise ValueError(f"{profile}: independent native guardian missing, duplicate or unexpected Code Mode/Lite metadata")
    guardian = copy.deepcopy(entries[0])
    if not profile.startswith("mimo"):
        guardian.update(tool_mode="direct", use_responses_lite=False)
    return guardian


def official_catalog(native: dict, profile: str, cards_dir: Path) -> dict:
    catalog = official_source(profile)
    _, source_slug, selected_slug = OFFICIAL[profile]
    selected = next(m for m in catalog["models"] if m["slug"] == source_slug)
    if selected_slug != source_slug:
        selected = copy.deepcopy(selected)
        selected.update(slug=selected_slug,
                        display_name=f"{selected_slug} (derived from official {source_slug})",
                        description=f"User-authorized derivation of official {source_slug} for {selected_slug}.")
        catalog["models"].append(selected)
    card_path = cards_dir / f"{profile}.config.toml"
    try:
        card = tomllib.loads(card_path.read_text())
        context = selected.get("context_window")
        if context is None:
            context = selected.get("max_context_window")
        maximum = selected.get("max_context_window")
        percent = selected.get("effective_context_window_percent", 95)
        if type(context) is not int or context <= 0:
            raise ValueError("selected resolved context must be a positive integer")
        if maximum is not None and (type(maximum) is not int or maximum <= 0 or maximum < context):
            raise ValueError("selected maximum context is inconsistent")
        if type(percent) is not int or not 1 <= percent <= 100:
            raise ValueError("selected effective context percent must be 1..100")
        if selected.get("tool_mode") not in (None, "direct", "code_mode", "code_mode_only"):
            raise ValueError("selected tool_mode is unknown")
        expected_window = 983616 if profile == "qwen" else 1048576
        if (card.get("model") != selected_slug or card.get("model_reasoning_effort") != "max"
                or card.get("model_catalog_json") != str(CATALOG_DIR / f"{profile}.json")
                or not CATALOG_DIR.is_absolute()):
            raise ValueError("card needs exact selected model, max effort and final absolute catalog path")
        if type(card.get("model_context_window")) is not int or card["model_context_window"] != context or context != expected_window:
            raise ValueError("card context must equal official context and approved window")
        compact = card.get("model_auto_compact_token_limit")
        if (type(compact) is not int or compact <= 0 or compact != context * 3 // 4
                or compact > context * percent // 100 or compact > context * 9 // 10):
            raise ValueError("card compact limit must equal approved 75% and fit effective/native cap")
    except (OSError, ValueError) as exc:
        raise ValueError(f"{profile}: {card_path}, selected slug {selected_slug}: {exc}") from None
    if profile.startswith("mimo") or profile == "qwen":
        status = "MiMo max is user-confirmed" if profile.startswith("mimo") else "Qwen max is selected but unadvertised"
        print(f"note: {profile}: {status}; official effort metadata is preserved")
    catalog["models"].append(guardian_entry(native, profile))
    return catalog


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


def select_session_template(catalog: dict) -> dict | None:
    """Use the first compatible session model in Codex's own catalog order.

    Code-mode entries carry instructions for functions.exec; changing their
    tool_mode alone does not make them suitable direct-tool session templates.
    The guardian is also not a session template, even after patch() changes it.
    """
    for entry in catalog["models"]:
        if (entry_key(entry) and entry_key(entry) != TARGET_ENTRY
                and isinstance(entry.get("base_instructions"), str)
                and entry["base_instructions"].strip()
                and entry.get("tool_mode") in (None, "direct")
                and entry.get("shell_type") == "unified_exec"
                and entry.get("use_responses_lite") is False
                and entry.get("experimental_supported_tools") == []):
            return entry
    warn("no compatible direct-tool session template in Codex's catalog; "
         "template shape changed or compatible models were removed; nothing written")
    return None


def session_entry(catalog: dict, model: str, window: int) -> dict | None:
    models = catalog["models"]
    if any(entry_key(entry) == model for entry in models):
        warn(f"{model}: already present in Codex's catalog; refusing to replace built-in metadata")
        return None
    template = select_session_template(catalog)
    if template is None:
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


def assemble(native: dict, profile: str, cards_dir: Path) -> dict:
    if profile in OFFICIAL:
        return official_catalog(native, profile, cards_dir)
    if profile != "local":
        raise ValueError(f"{profile}: no approved catalog mapping")
    generated, ok = patch(copy.deepcopy(native))
    config = profile_model(profile, cards_dir)
    if not ok or config is None:
        raise ValueError("local: cannot assemble native fallback")
    model, window = config
    entry = session_entry(generated, model, window)
    if entry is None:
        raise ValueError("local: cannot assemble direct session donor")
    generated["models"].append(entry)
    return generated


def write_targets(catalog: dict, profiles: list[str], dry_run: bool, cards_dir: Path, output_dir: Path) -> int:
    # All conversion checks and native parsing finish before output replacement.
    generated = {}
    try:
        for profile in profiles:
            generated[profile] = assemble(catalog, profile, cards_dir)
        with tempfile.TemporaryDirectory(prefix="catalog-validate.") as temp:
            for profile, doc in generated.items():
                path = Path(temp) / f"{profile}.json"
                path.write_text(json.dumps(doc, indent=2) + "\n")
                try:
                    native_models(path)
                except ValueError as exc:
                    raise ValueError(f"{profile}: staged {path}: {exc}") from None
    except (OSError, ValueError) as exc:
        warn(str(exc))
        return 0
    for profile, doc in generated.items():
        target = output_dir / f"{profile}.json"
        if dry_run:
            print(f"dry-run: would write {target}")
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", prefix=f".{profile}.", dir=target.parent, delete=False) as stream:
            tmp = Path(stream.name)
            try:
                stream.write(json.dumps(doc, indent=2) + "\n")
                stream.close()
                os.replace(tmp, target)
            finally:
                tmp.unlink(missing_ok=True)
        verify(target, profile, cards_dir, doc)
        print(f"wrote {target} ({target.stat().st_size} bytes)")
    return len(generated)


def verify(path: Path, profile: str, cards_dir: Path, expected: dict) -> None:
    """Exact assembly equality retains source metadata and authorized deltas."""
    try:
        actual = json.loads(path.read_text())
        if actual != expected:
            raise ValueError("installed catalog differs from validated assembly")
        # Equality covers selected source, guardian dialect and all root/model
        # data. The staged card was validated before this assembly was parsed.
        if profile_model(profile, cards_dir) is None:
            raise ValueError("local card mismatch")
    except (OSError, ValueError) as exc:
        warn(f"{profile}: {path}: verification failed: {exc}")


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="report actions without writing")
    ap.add_argument("--source", metavar="FILE", help="use a pre-rendered catalog instead of running codex")
    ap.add_argument("--profiles", default=",".join(DEFAULT_PROFILES), help="comma-separated profile names")
    ap.add_argument("--cards-dir", type=Path, default=SHARED_HOME, help="read installed profile cards here")
    ap.add_argument("--output-dir", type=Path, default=CATALOG_DIR, help="write generated catalogs here")
    args = ap.parse_args()

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()]
    try:
        catalog = load_source(args.source)
    except (OSError, ValueError) as exc:
        warn(f"independent native source: {exc}")
        return 1
    count = write_targets(catalog, profiles, args.dry_run, args.cards_dir, args.output_dir)

    if warnings:
        print(f"\n{len(warnings)} warning(s) — catalog may be stale; see above", file=sys.stderr)
        return 1
    print(f"ok: {count} catalog(s) {'checked' if args.dry_run else 'written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
