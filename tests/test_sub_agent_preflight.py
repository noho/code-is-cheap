"""Regression checks for stale canary input in the preflight task body."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT = ROOT / "scripts/sub-agent-preflight"
BODY = "Goal\nInspect the CANARY concept and token validation.\nNon-goals\nNo dispatch.\nStop condition\nFinish setup.\n"
CODEX_PROVIDERS = "ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local gpt-6-astra gpt-6-sol gpt-6-luna business".replace(" ", "\n") + "\n"
CLAUDE_PROVIDERS = "ds-flash mimo mimo-fast mimo-flash qwen kimi glm glm-flash local hy".replace(" ", "\n") + "\n"


class PreflightStaleCanaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        home = self.root / "home"
        (home / ".codex").mkdir(parents=True)
        (home / ".codex/mimo.config.toml").write_text("", encoding="utf-8")
        tools = self.root / "agent-tools.zsh"
        tools.write_text("mimo_codex() { :; }\n", encoding="utf-8")
        bin_dir = self.root / "bin"
        bin_dir.mkdir()
        for name in ("codex-agent-run", "claude-agent-run"):
            runner = bin_dir / name
            prefix = "CODEX" if name.startswith("codex") else "CLAUDE"
            runner.write_text(
                "#!/bin/sh\n"
                '[ "$1" = "--list-providers" ] || exit 99\n'
                f'printf "%s" "${{FAKE_{prefix}_CATALOG}}"\n'
                f'exit "${{FAKE_{prefix}_EXIT}}"\n',
                encoding="utf-8",
            )
            runner.chmod(0o755)
        self.env = os.environ | {
            "HOME": str(home),
            "TMPDIR": str(self.root),
            "AGENT_TOOLS_FILE": str(tools),
            "PATH": f"{bin_dir}:{os.environ['PATH']}",
            "FAKE_CODEX_CATALOG": CODEX_PROVIDERS,
            "FAKE_CLAUDE_CATALOG": CLAUDE_PROVIDERS,
            "FAKE_CODEX_EXIT": "0",
            "FAKE_CLAUDE_EXIT": "0",
        }

    def preflight(self, source: str, body: str | Path, *options: str) -> tuple[subprocess.CompletedProcess[str], dict[str, str]]:
        if source == "--task":
            value = str(body)
        elif isinstance(body, Path):
            value = str(body)
        else:
            task_file = self.root / f"{source[2:]}.txt"
            task_file.write_text(body, encoding="utf-8")
            value = str(task_file)
        result = subprocess.run(
            [
                "bash", str(PREFLIGHT), "--runtime", "codex", "--provider", "mimo",
                "--cwd", str(ROOT), "--label", "preflight-stale-canary-test", source, value, *options,
            ],
            env=self.env, capture_output=True, text=True, check=False,
        )
        report = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        return result, report

    def test_optional_envelope_setup_failure_never_prints_dispatch(self):
        wrapper = self.root / "bin/agent-sandbox"
        wrapper.write_text("#!/bin/sh\necho 'unsupported original permission profile' >&2\nexit 1\n")
        wrapper.chmod(0o755)
        denied = self.root / "denied.json"
        denied.write_text('[]')
        result, report = self.preflight("--task", BODY, "--deny-list", str(denied))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report["command"], "")
        self.assertIn("unsupported original permission profile", result.stdout)

    def test_optional_envelope_and_full_access_commands(self):
        wrapper = self.root / "bin/agent-sandbox"
        wrapper.write_text("#!/bin/sh\nexit 0\n")
        wrapper.chmod(0o755)
        denied = self.root / "denied.json"
        denied.write_text('[]')
        result, report = self.preflight("--task", BODY, "--deny-list", str(denied))
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertTrue(report["command"].startswith("agent-sandbox --cwd "))
        self.assertIn("--full-access --no-persist", report["command"])

    def test_prompt_file_directory_reports_structured_failure(self) -> None:
        directory = self.root / "prompt-input-dir"
        directory.mkdir()
        result, report = self.preflight("--prompt-file", directory)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(report["setup_status"], "fail")
        self.assertIn(f"failure=--prompt-file 不可读或为空: {directory}", result.stdout)
        self.assertEqual(report["command"], "")

    def test_task_file_directory_reports_structured_failure(self) -> None:
        directory = self.root / "task-input-dir"
        directory.mkdir()
        result, report = self.preflight("--task-file", directory)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(report["setup_status"], "fail")
        self.assertIn(f"failure=--task-file 不可读或为空: {directory}", result.stdout)
        self.assertEqual(report["command"], "")

    def test_clean_concept_discussion_passes_for_all_three_sources(self) -> None:
        for source in ("--task", "--task-file", "--prompt-file"):
            with self.subTest(source=source):
                body = BODY + "A fix-deadbeef reference is unrelated to the canary.\n"
                result, report = self.preflight(source, body)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual(report["setup_status"], "ok")
                prompt = Path(report["prompt_file"]).read_text(encoding="utf-8")
                self.assertIn(body, prompt)
                self.assertEqual(prompt.count("RUNTIME/PROVIDER/MODEL:"), 1)
                self.assertEqual(prompt.count(report["canary_file"]), 1)
                self.assertNotIn(Path(report["canary_file"]).read_text(), prompt)
                if source == "--prompt-file":
                    self.assertEqual((self.root / "prompt-file.txt").read_text(), body)

    def test_stale_inputs_fail_before_final_prompt_is_written(self) -> None:
        stale_cases = (
            "Read sub-agents.OLD123/canary.txt.",
            "Read /tmp/sub-agents.OLD123/canary.expected.",
            "Read ./legacy/canary.txt.",
            "Read ../legacy/canary.expected.",
            "Read /tmp/legacy/canary.txt.",
            "Read //tmp/legacy/canary.expected.",
            "Read canary.txt.",
            "CANARY: old-canary-00000000",
            "CANARY=old-task-00000000",
            "Use bare mimo-deadbeef as the result.",
            "Use bare hy-deadbeef as the result.",
            "Use bare old-canary-deadbeef as the result.",
            "RUNTIME/PROVIDER/MODEL: codex/mimo/old",
        )
        for source in ("--task", "--task-file", "--prompt-file"):
            for stale_text in stale_cases:
                with self.subTest(source=source, stale_text=stale_text):
                    result, report = self.preflight(source, BODY + stale_text + "\n")
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertEqual(report["setup_status"], "fail")
                    self.assertEqual(report["command"], "")
                    self.assertEqual(report["prompt_file"], "")
                    self.assertFalse((Path(report["run_dir"]) / "prompt.txt").exists())
                    self.assertIn("failure=任务正文含", result.stdout)

    def test_catalog_failures_and_partial_output_fail_setup(self) -> None:
        scenarios = (
            ("codex nonzero", {"FAKE_CODEX_EXIT": "7"}),
            ("claude nonzero", {"FAKE_CLAUDE_EXIT": "7"}),
            ("both nonzero", {"FAKE_CODEX_EXIT": "7", "FAKE_CLAUDE_EXIT": "7"}),
            ("partial nonzero", {"FAKE_CODEX_CATALOG": "mimo\n", "FAKE_CODEX_EXIT": "7"}),
            ("codex partial", {"FAKE_CODEX_CATALOG": "mimo\n"}),
            ("claude partial", {"FAKE_CLAUDE_CATALOG": "mimo\n"}),
        )
        for name, overrides in scenarios:
            with self.subTest(scenario=name):
                env = self.env.copy()
                self.env.update(overrides)
                result, report = self.preflight("--task", BODY + "A fix-deadbeef reference is unrelated.\n")
                self.env = env
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(report["setup_status"], "fail")
                self.assertEqual(report["command"], "")
                if "nonzero" in name:
                    self.assertIn("provider catalog", result.stdout)
                else:
                    self.assertIn("输出不完整", result.stdout)

    def test_canary_shape_check_is_independent_of_catalog(self) -> None:
        self.env["FAKE_CODEX_EXIT"] = "7"
        self.env["FAKE_CLAUDE_EXIT"] = "7"
        for source in ("--task", "--task-file", "--prompt-file"):
            with self.subTest(source=source):
                result, report = self.preflight(source, BODY + "Use old-canary-deadbeef.\n")
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertEqual(report["setup_status"], "fail")
                self.assertIn("failure=任务正文含 canary token", result.stdout)


if __name__ == "__main__":
    unittest.main()
