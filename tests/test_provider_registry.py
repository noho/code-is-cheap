"""Regression checks for shared-provider resume configuration."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "codex-agent/model-providers.toml"
SYNC = ROOT / "scripts/sync-codex-providers.py"
COMPOSE = ROOT / "scripts/compose-codex-app-config.py"

spec = importlib.util.spec_from_file_location("sync_providers", SYNC)
assert spec and spec.loader
sync_providers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync_providers)


class ProviderRegistryTests(unittest.TestCase):
    def test_every_card_resolves_to_one_shared_gateway(self) -> None:
        providers = tomllib.loads(REGISTRY.read_text())["model_providers"]
        for card in (ROOT / "codex-agent/profiles").glob("*/config.toml"):
            with self.subTest(card=card.parent.name):
                data = tomllib.loads(card.read_text())
                self.assertNotIn("model_providers", data)
                self.assertIn(data.get("model_provider", "openai"), providers.keys() | {"openai"})
        self.assertNotEqual(providers["mimo"]["base_url"], providers["mimo_fast"]["base_url"])
        self.assertNotEqual(providers["mimo"]["base_url"], providers["mimo_flash"]["base_url"])
        self.assertNotEqual(providers["glm"]["base_url"], providers["glm_flash"]["base_url"])

    def test_registry_matches_shim_routes_and_launcher_keys(self) -> None:
        providers = tomllib.loads(REGISTRY.read_text())["model_providers"]
        routes = {route["port"]: route for route in json.loads((ROOT / "codex-agent/shim-routes.json").read_text())["routes"]}
        for card in (ROOT / "codex-agent/profiles").glob("*/config.toml"):
            data = tomllib.loads(card.read_text())
            provider_id = data.get("model_provider", "openai")
            if provider_id in {"openai", "local_llama"}:
                continue
            with self.subTest(card=card.parent.name):
                provider = providers[provider_id]
                port = urlsplit(provider["base_url"]).port
                self.assertIn(port, routes)
                self.assertEqual(routes[port]["to"], data["model"])
                if shutil.which("zsh"):
                    script = 'source "$1"; _codex_agent_shim_port "$2"; _codex_agent_key_name "$2"'
                    done = subprocess.run(["zsh", "-c", script, "_", str(ROOT / "scripts/agent-tools.zsh"), card.parent.name], check=True, capture_output=True, text=True)
                    actual_port, key_name = done.stdout.splitlines()
                    self.assertEqual(int(actual_port), port)
                    self.assertEqual(key_name, provider["env_key"])

    def test_sync_preserves_local_config_and_is_idempotent(self) -> None:
        base = 'model = "gpt-6-sol"\n\n[projects."/work"]\ntrust_level = "trusted"\n'
        registry = REGISTRY.read_text()
        first = sync_providers.compose(base, registry)
        self.assertEqual(first, sync_providers.compose(first, registry))
        data = tomllib.loads(first)
        self.assertEqual(data["projects"]["/work"]["trust_level"], "trusted")
        self.assertIn("kimi", data["model_providers"])

    def test_sync_refuses_unowned_conflict(self) -> None:
        base = '[model_providers.kimi]\nbase_url = "https://custom.example"\n'
        with self.assertRaisesRegex(ValueError, "already owned"):
            sync_providers.compose(base, REGISTRY.read_text())

    def test_sync_creates_missing_base_privately_and_refuses_malformed_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "config.toml"
            cmd = [sys.executable, str(SYNC), "--base", str(base), "--registry", str(REGISTRY)]
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertEqual(base.stat().st_mode & 0o777, 0o600)
            self.assertIn("kimi", tomllib.loads(base.read_text())["model_providers"])
            first = base.read_bytes()
            subprocess.run(cmd, check=True, capture_output=True)
            self.assertEqual(base.read_bytes(), first)

            malformed = root / "malformed.toml"
            malformed.write_text("[model_providers]\noops = 1\n")
            bad = subprocess.run(cmd[:-1] + [str(malformed)], capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertEqual(base.read_bytes(), first)

            malformed.write_text("[model_providers.kimi]\n")
            self.assertNotEqual(subprocess.run(cmd[:-1] + [str(malformed)], capture_output=True).returncode, 0)
            self.assertEqual(base.read_bytes(), first)

            base.write_text("model_providers = 5\n")
            bad = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("base model_providers must be a table", bad.stderr)
            self.assertNotIn("Traceback", bad.stderr)

    def test_sync_rejects_symlink_and_damaged_block_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "real.toml"
            link = root / "config.toml"
            target.write_text('model = "gpt-6-sol"\n')
            link.symlink_to(target)
            cmd = [sys.executable, str(SYNC), "--base", str(link), "--registry", str(REGISTRY)]
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_text(), 'model = "gpt-6-sol"\n')

            link.unlink()
            broken = '# BEGIN code-is-cheap managed model providers\n[model_providers.kimi]\nname = "Kimi"\n'
            link.write_text(broken)
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            self.assertEqual(link.read_text(), broken)

            inverted = '# END code-is-cheap managed model providers\n# BEGIN code-is-cheap managed model providers\n'
            link.write_text(inverted)
            bad = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("end precedes start", bad.stderr)
            self.assertEqual(link.read_text(), inverted)

    def test_existing_app_home_gets_new_provider_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.toml"
            card = root / "kimi.config.toml"
            out = root / "app.toml"
            base.write_text(sync_providers.compose('model = "gpt-6-sol"\n', REGISTRY.read_text()))
            card.write_text('model = "kimi-k3"\nmodel_provider = "kimi"\n')
            out.write_text('model = "old"\n\n[desktop]\nstate = "keep"\n')
            subprocess.run([sys.executable, str(COMPOSE), "--base", str(base), "--card", str(card), "--out", str(out)], check=True, capture_output=True)
            data = tomllib.loads(out.read_text())
            self.assertEqual(data["model"], "kimi-k3")
            self.assertEqual(data["desktop"]["state"], "keep")
            self.assertIn("kimi", data["model_providers"])

    def test_legacy_card_keeps_its_gateway_during_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.toml"
            card = root / "mimo-fast.config.toml"
            out = root / "app.toml"
            base.write_text(sync_providers.compose('model = "gpt-6-sol"\n', REGISTRY.read_text()))
            card.write_text('model = "mimo-v2.6-pro-ultraspeed"\nmodel_provider = "mimo"\n\n[model_providers.mimo]\nbase_url = "http://127.0.0.1:8794/v1"\n')
            done = subprocess.run([sys.executable, str(COMPOSE), "--base", str(base), "--card", str(card), "--out", str(out)], check=True, capture_output=True, text=True)
            self.assertIn("legacy provider table", done.stderr)
            self.assertEqual(tomllib.loads(out.read_text())["model_providers"]["mimo"]["base_url"], "http://127.0.0.1:8794/v1")

    def test_composer_reports_missing_shared_base_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            card = root / "kimi.config.toml"
            out = root / "app.toml"
            card.write_text('model = "kimi-k3"\nmodel_provider = "kimi"\n')
            out.write_text('model = "old"\n')
            done = subprocess.run([sys.executable, str(COMPOSE), "--base", str(root / "missing.toml"), "--card", str(card), "--out", str(out)], capture_output=True, text=True)
            self.assertEqual(done.returncode, 2)
            self.assertIn("run sync-codex-agent.sh", done.stderr)
            self.assertNotIn("Traceback", done.stderr)
            self.assertEqual(out.read_text(), 'model = "old"\n')


if __name__ == "__main__":
    unittest.main()
