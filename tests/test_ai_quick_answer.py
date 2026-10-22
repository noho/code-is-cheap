"""Focused AI launcher checks with a fake native Codex; no network or real home."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which("zsh"), "zsh is required")
class AIQuickAnswerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.work = self.home / "non-git"
        self.work.mkdir()
        bins = self.home / "bin"
        bins.mkdir()
        cards = self.home / ".codex"
        cards.mkdir()
        for provider in ("gpt-6-sol", "gpt-6-luna"):
            (cards / f"{provider}.config.toml").write_text("")
        business = self.home / ".codex-agent/business"
        business.mkdir(parents=True)
        (business / "config.toml").write_text("")
        self.capture = self.home / "native.json"
        self.env = {
            "HOME": str(self.home), "ZDOTDIR": str(self.home),
            "PATH": f"{bins}:/usr/bin:/bin", "NATIVE_CAPTURE": str(self.capture),
        }
        native = bins / "codex"
        native.write_text("#!" + sys.executable + "\n" + '''import json, os, sys
from pathlib import Path
Path(os.environ["NATIVE_CAPTURE"]).write_text(json.dumps({
    "argv": sys.argv[1:], "stdin": sys.stdin.read(), "cwd": os.getcwd(),
    "home": os.environ["CODEX_HOME"], "sqlite": os.environ["CODEX_SQLITE_HOME"],
}))
sys.stdout.write("native answer\\n")
sys.stderr.write("native diagnostic\\n")
sys.exit(int(os.environ.get("NATIVE_EXIT", "0")))
''')
        native.chmod(0o755)

    def run_ai(self, *args, options="", exit_code=0):
        self.capture.unlink(missing_ok=True)
        return subprocess.run(
            ["zsh", "-f", "-c", 'source "$1"; shift; ' + options + 'AI "$@"',
             "_", str(ROOT / "scripts/agent-tools.zsh"), *args],
            cwd=self.work, env=self.env | {"NATIVE_EXIT": str(exit_code)},
            capture_output=True, text=True, timeout=10,
        )

    def assert_native(self, done, prompt, provider="gpt-6-sol", exit_code=0):
        self.assertEqual(done.returncode, exit_code, done.stderr)
        self.assertEqual(done.stdout, "native answer\n")
        self.assertEqual(done.stderr, "native diagnostic\n")
        native = json.loads(self.capture.read_text())
        profile = [] if provider == "business" else ["-p", provider]
        self.assertEqual(native["argv"], ["exec", *profile, "--ephemeral",
            "--skip-git-repo-check", "--sandbox", "read-only", "--", "-"])
        self.assertEqual(native["stdin"], prompt + "\n")
        self.assertEqual(native["cwd"], str(self.work))
        expected_home = self.home / (".codex-agent/business" if provider == "business" else ".codex")
        self.assertEqual(native["home"], str(expected_home))
        self.assertEqual(native["sqlite"], str(expected_home))

    def test_default_and_provider_selection_from_non_git_directory(self):
        git = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"],
            cwd=self.work, env=self.env, capture_output=True, timeout=10)
        self.assertNotEqual(git.returncode, 0, "fixture must be outside Git")
        for args, provider in (([], "gpt-6-sol"), (["-p", "gpt-6-luna"], "gpt-6-luna"),
                (["--provider", "business"], "business")):
            with self.subTest(args=args):
                self.assert_native(self.run_ai(*args, "日常问答"), "日常问答", provider)

    def test_prompt_is_literal_stdin_and_parsing_stops_at_first_body(self):
        marker = self.work / "must-not-exist"
        special = '雪 "quotes" \'single\' \\ $HOME $(touch must-not-exist); `touch must-not-exist` * [x]\nnext\n'
        for args, prompt in (([special], special), (["-"], "-"), (["resume"], "resume"),
                (["--", "--full-access"], "--full-access"),
                (["body", "-p", "invalid", "--provider", "--", "--full-access"],
                 "body -p invalid --provider -- --full-access"),
                (["", "body", "", "tail"], " body  tail")):
            with self.subTest(args=args):
                self.assert_native(self.run_ai(*args), prompt)
                self.assertFalse(marker.exists())

    def test_usage_errors_do_not_launch_native_codex(self):
        for args, message in (([], "prompt"), ([""], "prompt"),
                ([" \t\r\n", "  "], "prompt"), (["--"], "prompt"),
                (["-p"], "provider"), (["--provider", ""], "provider"),
                (["-p", "--", "body"], "provider"),
                (["--provider", "unknown", "body"], "未知 provider"),
                (["-p", "hy", "body"], "未知 provider"),
                (["--full-access", "body"], "未知选项")):
            with self.subTest(args=args):
                done = self.run_ai(*args)
                self.assertEqual(done.returncode, 2, done.stderr)
                self.assertEqual(done.stdout, "")
                self.assertIn("AI:", done.stderr)
                self.assertIn(message, done.stderr)
                self.assertFalse(self.capture.exists())

    def test_native_exit_codes_and_streams_are_preserved(self):
        for code in (0, 1, 2, 42, 126, 127):
            with self.subTest(code=code):
                self.assert_native(self.run_ai("answer", exit_code=code), "answer", exit_code=code)

    def test_caller_shell_options_are_localized(self):
        options = "setopt shwordsplit ksharrays rcexpandparam globsubst extendedglob nounset; "
        self.assert_native(self.run_ai("spaces and * [x]", "tail", options=options),
            "spaces and * [x] tail")


if __name__ == "__main__":
    unittest.main()
