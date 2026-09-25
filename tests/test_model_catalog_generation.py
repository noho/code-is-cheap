"""Integration checks for generated third-party Codex model catalogs."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/patch-codex-model-catalog.py"
CARDS = ROOT / "codex-agent/profiles"


class ModelCatalogGenerationTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is required for its bundled catalog")
    def test_generated_catalogs_follow_codex_and_card_windows(self) -> None:
        source = json.loads(subprocess.check_output(["codex", "debug", "models", "--bundled"]))
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            source_path = home / "source.json"
            source_path.write_text(json.dumps(source))
            profiles = ("kimi", "glm", "local")
            for profile in profiles:
                card = (CARDS / profile / "config.toml").read_text()
                (home / f"{profile}.config.toml").write_text(card.replace("@HOME@/.codex", str(home)))

            cmd = [sys.executable, str(SCRIPT), "--source", str(source_path), "--profiles", ",".join(profiles)]
            env = os.environ | {"CODEX_SHARED_HOME": str(home)}
            first = subprocess.run(cmd, env=env, capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            for profile in profiles:
                with self.subTest(profile=profile):
                    card = tomllib.loads((home / f"{profile}.config.toml").read_text())
                    generated = json.loads((home / "model-catalogs" / f"{profile}.json").read_text())
                    builtins = [m for m in generated["models"] if m["slug"] != card["model"]]
                    original = [m for m in source["models"] if m["slug"] != "codex-auto-review"]
                    self.assertEqual([m["slug"] for m in builtins], [m["slug"] for m in source["models"]])
                    self.assertEqual(
                        [m for m in builtins if m["slug"] != "codex-auto-review"], original
                    )
                    session = next(m for m in generated["models"] if m["slug"] == card["model"])
                    self.assertEqual(session["max_context_window"], card["model_context_window"])
                    self.assertEqual(session["tool_mode"], "direct")
                    guardian = next(m for m in generated["models"] if m["slug"] == "codex-auto-review")
                    self.assertEqual(guardian["tool_mode"], "direct")

            before = (home / "model-catalogs" / "kimi.json").read_bytes()
            (home / "kimi.config.toml").write_text('model = "kimi-k3"\n')
            bad = subprocess.run(cmd[:-1] + ["kimi"], env=env, capture_output=True, text=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertEqual((home / "model-catalogs" / "kimi.json").read_bytes(), before)

            (home / "kimi.config.toml").write_text((CARDS / "kimi" / "config.toml").read_text().replace("@HOME@/.codex", str(home)))
            changed = json.loads(source_path.read_text())
            next(m for m in changed["models"] if m["slug"] == "gpt-5.4")["tool_mode"] = "code_mode_only"
            source_path.write_text(json.dumps(changed))
            drift = subprocess.run(cmd[:-1] + ["kimi"], env=env, capture_output=True, text=True)
            self.assertNotEqual(drift.returncode, 0)
            self.assertIn("template shape changed", drift.stderr)
            self.assertEqual((home / "model-catalogs" / "kimi.json").read_bytes(), before)

    def test_sync_keeps_installed_cards_when_catalog_generation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            home = root / "home"
            home.mkdir()
            original_card = b'model = "previous-model"\n'
            (home / "kimi.config.toml").write_bytes(original_card)
            catalog_dir = home / "model-catalogs"
            catalog_dir.mkdir()
            original_catalog = b'{"models": []}\n'
            (catalog_dir / "kimi.json").write_bytes(original_catalog)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            codex = bin_dir / "codex"
            codex.write_text('#!/bin/sh\nprintf "{}\\n"\n')
            codex.chmod(0o755)
            launchctl = bin_dir / "launchctl"
            launchctl.write_text("#!/bin/sh\nexit 1\n")
            launchctl.chmod(0o755)
            env = os.environ | {
                "CODEX_SHARED_HOME": str(home),
                "CODEX_AGENT_TARGET": str(root / "target"),
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
            }
            done = subprocess.run(
                ["bash", str(ROOT / "scripts/sync-codex-agent.sh")],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(done.returncode, 0)
            self.assertEqual((home / "kimi.config.toml").read_bytes(), original_card)
            self.assertEqual((catalog_dir / "kimi.json").read_bytes(), original_catalog)


if __name__ == "__main__":
    unittest.main()
