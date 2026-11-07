"""Manual legacy recovery and native launcher resume boundary checks."""

from __future__ import annotations

import json
import importlib.util
import contextlib
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/repair-codex-reasoning-history.py"
SPEC = importlib.util.spec_from_file_location("repair_reasoning", SCRIPT)
assert SPEC and SPEC.loader
repair_reasoning = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair_reasoning)


def row(kind: str, payload: dict) -> str:
    return json.dumps({"type": kind, "payload": payload}, separators=(",", ":")) + "\n"


class RepairReasoningHistoryTests(unittest.TestCase):
    def test_target_model_keeps_own_reasoning_and_drops_foreign_reasoning(self) -> None:
        original = (
            row("turn_context", {"model": "gpt-6-sol"})
            + row("response_item", {"type": "reasoning", "encrypted_content": "native"})
            + row("turn_context", {"model": "kimi-k3"})
            + row("response_item", {"type": "reasoning", "encrypted_content": "foreign"})
            + row("response_item", {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "answer"}]})
        ).encode()
        fixed, count = repair_reasoning.repair_lines(original, keep_reasoning_model="gpt-6-sol")
        self.assertEqual(count, 1)
        self.assertEqual(fixed.splitlines()[1], original.splitlines()[1])
        self.assertEqual(fixed.splitlines()[-1], original.splitlines()[-1])
        self.assertEqual(len(fixed.splitlines()), 4)

    def test_launcher_resume_forwards_without_repair(self) -> None:
        if not shutil.which("zsh"):
            self.skipTest("zsh unavailable")
        session_id = "01a0d626-0a68-7913-8394-a73c79d0f977"
        prompt = "continue with spaces\n下一步 🌱"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            codex_home = home / ".codex"
            folder = codex_home / "sessions" / "2026" / "09" / "25"
            folder.mkdir(parents=True)
            (codex_home / "gpt-6-sol.config.toml").write_text('model = "gpt-6.1-sol"\n')
            rollout = folder / f"rollout-2026-09-25T00-00-00-{session_id}.jsonl"
            original = (
                row("session_meta", {"id": session_id, "model_provider": "openai"})
                + row("turn_context", {"model": "gpt-6.1-sol", "model_provider": "openai"})
                + row("response_item", {"type": "reasoning", "encrypted_content": "native"})
                + row("turn_context", {"model": "kimi-k3", "model_provider": "kimi"})
                + row("response_item", {"type": "reasoning", "encrypted_content": "foreign"})
                + row("response_item", {"type": "message", "content": [{"type": "output_text", "text": "answer"}]})
            ).encode()
            rollout.write_bytes(original)
            files_before = set(codex_home.rglob("*"))
            bin_dir = root / "bin"
            bin_dir.mkdir()
            trap = root / "repair-called"
            repair = bin_dir / SCRIPT.name
            repair.write_text('#!/bin/sh\ntouch "$REPAIR_TRAP"\nexit 97\n')
            repair.chmod(0o755)
            capture = root / "codex-args.json"
            stub = bin_dir / "codex"
            stub.write_text('#!' + sys.executable + "\n" +
                'import json,os,sys\nfrom pathlib import Path\n'
                'Path(os.environ["CAPTURE_FILE"]).write_text(json.dumps(dict(argv=sys.argv[1:], '
                'home=os.environ["CODEX_HOME"], sqlite=os.environ["CODEX_SQLITE_HOME"])))\n'
                'sys.stdout.write(os.environ.get("NATIVE_STDOUT", ""))\n'
                'sys.stderr.write(os.environ.get("NATIVE_STDERR", ""))\n'
                'sys.exit(int(os.environ.get("NATIVE_EXIT", "0")))\n')
            stub.chmod(0o755)
            env = {"HOME": str(home), "PATH": f"{bin_dir}:/usr/bin:/bin",
                   "CAPTURE_FILE": str(capture), "REPAIR_TRAP": str(trap)}
            launcher = SCRIPT.parent / "agent-tools.zsh"
            cases = [
                (["resume"], ["resume"]),
                (["--resume"], ["resume"]),
                (["--resume="], ["resume", ""]),
                (["resume", ""], ["resume", ""]),
                (["resume", session_id], ["resume", session_id]),
                (["--resume", session_id, prompt], ["resume", session_id, prompt]),
                (["--title", "saved thread", "--resume", session_id, prompt], ["resume", session_id, prompt]),
                (["--resume", "", prompt], ["resume", "", prompt]),
                ([f"--resume={session_id}", prompt], ["resume", session_id, prompt]),
                (["resume", "--help"], ["resume", "--help"]),
                (["--resume", "--last", "--all"], ["resume", "--last", "--all"]),
                (["resume", "named session", "--model", "other", "--", prompt, ""],
                 ["resume", "named session", "--model", "other", "--", prompt, ""]),
                (["--resume=named session", "--model", "other", "--", prompt, ""],
                 ["resume", "named session", "--model", "other", "--", prompt, ""]),
                (["resume", "--all", "unavailable-session", "--model", "other", prompt],
                 ["resume", "--all", "unavailable-session", "--model", "other", prompt]),
                (["--resume", "unavailable-session", "--model", "other", prompt],
                 ["resume", "unavailable-session", "--model", "other", prompt]),
                (["--resume=", "--", prompt], ["resume", "", "--", prompt]),
                # Alias-looking prompts and arguments after the delimiter stay literal.
                (["--", "--resume=literal", prompt], ["--", "--resume=literal", prompt]),
                (["--", "--resume", ""], ["--", "--resume", ""]),
                (["resume", session_id, "--resume=literal"], ["resume", session_id, "--resume=literal"]),
                (["exec", "resume", session_id, "--", prompt], ["exec", "resume", session_id, "--", prompt]),
            ]
            for entry in ("gpt-6-sol_codex", "gpt_codex"):
                for supplied, forwarded in cases:
                    with self.subTest(entry=entry, supplied=supplied):
                        done = subprocess.run([
                            "zsh", "-f", "-c", 'source "$1"; launcher="$2"; shift 2; "$launcher" "$@"',
                            "_", str(launcher), entry, *supplied,
                        ], env=env, capture_output=True, text=True)
                        self.assertEqual(done.returncode, 0, done.stderr)
                        expected = ([forwarded[0], "-p", "gpt-6-sol", *forwarded[1:]]
                                    if forwarded[0] in ("resume", "exec")
                                    else ["-p", "gpt-6-sol", *forwarded])
                        native = json.loads(capture.read_text())
                        self.assertEqual(native["argv"], expected)
                        self.assertEqual(native["home"], str(codex_home))
                        self.assertEqual(native["sqlite"], str(codex_home))
                        self.assertEqual(rollout.read_bytes(), original)
                        self.assertEqual(set(codex_home.rglob("*")), files_before)
                        self.assertFalse(trap.exists())
            # Native validation/provider messages and failures pass through without a fallback.
            for supplied in (["resume", "unavailable-session"], ["--resume="], ["--resume"]):
                with self.subTest(native_failure=supplied):
                    stdout = "Continue in a new chat.\n"
                    stderr = "modelProviderMismatch: this chat is read-only\n"
                    done = subprocess.run([
                        "zsh", "-f", "-c", 'source "$1"; shift; gpt-6-sol_codex "$@"',
                        "_", str(launcher), *supplied,
                    ], env=env | {"NATIVE_STDOUT": stdout, "NATIVE_STDERR": stderr, "NATIVE_EXIT": "23"},
                        capture_output=True, text=True)
                    self.assertEqual(done.returncode, 23)
                    self.assertEqual(done.stdout, stdout)
                    self.assertEqual(done.stderr, stderr)
                    self.assertEqual(rollout.read_bytes(), original)
                    self.assertEqual(set(codex_home.rglob("*")), files_before)
                    self.assertFalse(trap.exists())

    def test_sync_installs_repair_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            env = os.environ | {"HOME": str(root / "home"), "AGENT_TOOLS_TARGET": str(root / "agent-tools.zsh"), "AGENT_RUN_BIN_DIR": str(bin_dir)}
            done = subprocess.run(["bash", str(SCRIPT.parent / "sync-agent-tools.sh")], env=env, capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            installed = bin_dir / SCRIPT.name
            self.assertEqual(installed.read_bytes(), SCRIPT.read_bytes())
            self.assertEqual(installed.stat().st_mode & 0o777, 0o755)

    def test_session_lookup_and_orphan_reasoning_fail_closed(self) -> None:
        session_id = "01a0d626-0a68-7913-8394-a73c79d0f977"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sessions = root / "sessions"
            sessions.mkdir()
            card = root / "target.config.toml"
            card.write_text('model = "gpt-6-sol"\n')
            first = sessions / f"rollout-first-{session_id}.jsonl"
            second = sessions / f"rollout-second-{session_id}.jsonl"
            original = row("response_item", {"type": "reasoning", "encrypted_content": "opaque"})
            first.write_text(original)
            second.write_text(original)
            cmd = [sys.executable, str(SCRIPT), "--session-id", session_id, "--sessions-root", str(sessions), "--target-config", str(card), "--apply"]
            duplicate = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn("found 2", duplicate.stderr)
            second.unlink()
            orphan = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(orphan.returncode, 2)
            self.assertIn("no preceding turn_context", orphan.stderr)
            self.assertEqual(first.read_text(), original)
            self.assertEqual(list(sessions.glob("*.backup-*")), [])

    def test_drops_reasoning_only_for_selected_model(self) -> None:
        original = (
            row("turn_context", {"model": "gpt-6-sol"})
            + row("response_item", {"type": "reasoning", "encrypted_content": "openai-secret", "content": None})
            + row("turn_context", {"model": "kimi-k3"})
            + row("response_item", {"type": "reasoning", "encrypted_content": "kimi-secret", "content": None, "summary": [{"type": "summary_text", "text": "summary"}]})
        ).encode()
        fixed, count = repair_reasoning.repair_lines(original, frozenset({"kimi-k3"}))
        self.assertEqual(count, 1)
        lines = fixed.splitlines()
        self.assertEqual(lines[1], original.splitlines()[1])
        self.assertEqual(lines[2], original.splitlines()[2])
        self.assertEqual(len(lines), 3)

    def test_reports_unmatched_model_and_rejects_invalid_context(self) -> None:
        original = row("turn_context", {"model": "kimi-k3"}) + row("response_item", {"type": "reasoning", "encrypted_content": "opaque"})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_text(original)
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--drop-reasoning-model", "kimi"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn("warning: no reasoning items matched", result.stderr)
            path.write_text(row("turn_context", {"model": {"unexpected": "object"}}) + original)
            bad = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)
            self.assertIn("invalid model in turn_context at line 1", bad.stderr)
            self.assertNotIn("Traceback", bad.stderr)

    def test_consecutive_repairs_make_distinct_backups(self) -> None:
        original = (
            row("turn_context", {"model": "mimo-v2.6-pro"})
            + row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "x"}]})
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_text(original)
            path.chmod(0o600)
            first = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            second = subprocess.run([sys.executable, str(SCRIPT), str(path), "--drop-reasoning-model", "mimo-v2.6-pro", "--apply"], capture_output=True, text=True)
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(len(list(Path(tmp).glob("*.backup-*"))), 2)

    def test_backup_mode_ignores_restrictive_umask(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "backup"
            previous = os.umask(0o777)
            try:
                repair_reasoning.write_backup(path, b"private", 0o600)
            finally:
                os.umask(previous)
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_repairs_only_reasoning_text_and_preserves_backup(self) -> None:
        original = (
            row("session_meta", {"id": "sample"})
            + row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "private"}], "summary": []})
            + row("response_item", {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "answer"}]})
            + row("response_item", {"type": "reasoning", "content": None, "summary": []})
        ).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_bytes(original)
            path.chmod(0o600)
            dry = subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)
            self.assertEqual(dry.returncode, 0, dry.stderr)
            self.assertIn("affected reasoning items: 1", dry.stdout)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(tmp).glob("*.backup-*")), [])

            applied = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            self.assertEqual(applied.returncode, 0, applied.stderr)
            backup, = Path(tmp).glob("*.backup-*")
            self.assertEqual(backup.read_bytes(), original)
            self.assertEqual(backup.stat().st_mode & 0o777, 0o600)
            fixed = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertIsNone(fixed[1]["payload"]["content"])
            self.assertEqual(fixed[2]["payload"]["content"][0]["text"], "answer")
            self.assertEqual(fixed[3]["payload"]["content"], None)
            again = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
            self.assertEqual(again.returncode, 0, again.stderr)
            self.assertIn("affected reasoning items: 0", again.stdout)
            self.assertEqual(len(list(Path(tmp).glob("*.backup-*"))), 1)

    def test_rejects_unsupported_reasoning_and_invalid_json_without_writes(self) -> None:
        for original in [
            row("response_item", {"type": "reasoning", "content": [{"type": "other", "text": "x"}]}).encode(),
            b"{broken\n",
        ]:
            with self.subTest(original=original), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "rollout-sample.jsonl"
                path.write_bytes(original)
                bad = subprocess.run([sys.executable, str(SCRIPT), str(path), "--apply"], capture_output=True, text=True)
                self.assertNotEqual(bad.returncode, 0)
                self.assertEqual(path.read_bytes(), original)
                self.assertEqual(list(Path(tmp).glob("*.backup-*")), [])

    def test_preserves_blank_lines_and_carriage_return_endings(self) -> None:
        target = row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "x"}]}).rstrip("\n")
        untouched = row("response_item", {"type": "message", "role": "user", "content": []}).rstrip("\n")
        original = (target + "\r\r" + untouched + "\r").encode()
        fixed, count = repair_reasoning.repair_lines(original)
        self.assertEqual(count, 1)
        self.assertEqual(fixed.split(b"\r")[1], b"")
        self.assertEqual(fixed.split(b"\r")[2], untouched.encode())
        self.assertIsNone(json.loads(fixed.split(b"\r")[0])["payload"]["content"])

    def test_aborts_if_rollout_changes_during_backup(self) -> None:
        original = row("response_item", {"type": "reasoning", "content": [{"type": "reasoning_text", "text": "x"}]}).encode()
        appended = row("response_item", {"type": "message", "role": "user", "content": []}).encode()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rollout-sample.jsonl"
            path.write_bytes(original)
            real_write_backup = repair_reasoning.write_backup

            def append_during_backup(backup: Path, data: bytes, mode: int) -> None:
                real_write_backup(backup, data, mode)
                with path.open("ab") as out:
                    out.write(appended)

            with mock.patch.object(repair_reasoning, "write_backup", side_effect=append_during_backup), mock.patch.object(sys, "argv", [str(SCRIPT), str(path), "--apply"]), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as exit_context:
                    repair_reasoning.main()
            self.assertEqual(exit_context.exception.code, 2)
            self.assertEqual(path.read_bytes(), original + appended)
            self.assertEqual(next(Path(tmp).glob("*.backup-*")).read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
