"""Checks for the independent business home's two managed model defaults."""

from __future__ import annotations

import importlib.util
import os
import shutil
import stat
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/sync-codex-model-defaults.py"
CARD = ROOT / "codex-agent/profiles/gpt-6-sol/config.toml"
SPEC = importlib.util.spec_from_file_location("sync_codex_model_defaults", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class BusinessModelDefaultsTests(unittest.TestCase):
    def test_three_gpt_cards_have_requested_efforts(self) -> None:
        for profile, model, effort in (("gpt-6-astra", "gpt-6-astra", "high"), ("gpt-6-sol", "gpt-6.1-sol", "high"), ("gpt-6-luna", "gpt-6-luna", "xhigh")):
            with self.subTest(profile=profile):
                card = tomllib.loads((ROOT / "codex-agent/profiles" / profile / "config.toml").read_text())
                self.assertEqual(card["model"], model)
                self.assertEqual(card["model_reasoning_effort"], effort)

    def test_updates_only_business_defaults_and_preserves_local_settings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "config.toml"
            original = (
                'model = "gpt-5.4"\nmodel_reasoning_effort = "medium"\n'
                'notify = ["/private/path", "turn-ended"]\n\n'
                '[projects."/work"]\ntrust_level = "trusted"\n'
            )
            config.write_text(original)
            config.chmod(0o600)
            self.assertTrue(module.sync(config, CARD))
            updated = tomllib.loads(config.read_text())
            self.assertEqual(updated["model"], "gpt-6.1-sol")
            self.assertEqual(updated["model_reasoning_effort"], "high")
            self.assertEqual(updated["notify"], ["/private/path", "turn-ended"])
            self.assertEqual(updated["projects"], {"/work": {"trust_level": "trusted"}})
            self.assertEqual(stat.S_IMODE(config.stat().st_mode), 0o600)
            self.assertFalse(module.sync(config, CARD))

    def test_inserts_missing_defaults_before_tables(self) -> None:
        result = module.compose('[projects."/work"]\ntrust_level = "trusted"\n', CARD.read_text())
        self.assertEqual(tomllib.loads(result)["model"], "gpt-6.1-sol")
        self.assertEqual(tomllib.loads(result)["model_reasoning_effort"], "high")
        self.assertIn('[projects."/work"]\ntrust_level = "trusted"\n', result)

    def test_invalid_config_and_symlink_do_not_replace_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            config = Path(temp) / "config.toml"
            config.write_text('model = "one"\nmodel = "two"\n')
            with self.assertRaises(tomllib.TOMLDecodeError):
                module.sync(config, CARD)
            self.assertEqual(config.read_text(), 'model = "one"\nmodel = "two"\n')
            link = Path(temp) / "link.toml"
            link.symlink_to(config)
            with self.assertRaises(ValueError):
                module.sync(link, CARD)

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is required for catalog generation")
    def test_business_failure_does_not_interrupt_shared_sync(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            shared = root / "shared"
            shared.mkdir()
            target = root / "agent"
            business = target / "business"
            business.mkdir(parents=True)
            (business / "config.toml").symlink_to(root / "missing.toml")
            bin_dir = root / "bin"
            bin_dir.mkdir()
            launchctl = bin_dir / "launchctl"
            launchctl.write_text("#!/bin/sh\nexit 1\n")
            launchctl.chmod(0o755)
            env = os.environ | {
                "CODEX_SHARED_HOME": str(shared),
                "CODEX_AGENT_TARGET": str(target),
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
            }
            done = subprocess.run(
                ["bash", str(ROOT / "scripts/sync-codex-agent.sh")],
                env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("config must be an existing regular file", done.stderr)
            self.assertTrue((shared / "gpt-6-sol.config.toml").is_file())
            self.assertTrue((target / "bin/codex-auto-review-shim").is_file())
            self.assertTrue((target / "shim-routes.json").is_file())


if __name__ == "__main__":
    unittest.main()
