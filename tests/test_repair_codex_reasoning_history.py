"""Recovery checks for cross-provider Codex reasoning history."""

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

    def test_launcher_resume_repairs_then_calls_codex(self) -> None:
        if not shutil.which("zsh"):
            self.skipTest("zsh unavailable")
        session_id = "01a0d626-0a68-7913-8394-a73c79d0f977"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home = root / "home"
            codex_home = home / ".codex"
            folder = codex_home / "sessions" / "2026" / "09" / "25"
            folder.mkdir(parents=True)
            (codex_home / "gpt-6-sol.config.toml").write_text('model = "gpt-6-sol"\n')
            rollout = folder / f"rollout-2026-09-25T00-00-00-{session_id}.jsonl"
            original = (
                row("turn_context", {"model": "gpt-6-sol"})
                + row("response_item", {"type": "reasoning", "encrypted_content": "native"})
                + row("turn_context", {"model": "kimi-k3"})
                + row("response_item", {"type": "reasoning", "encrypted_content": "foreign"})
                + row("response_item", {"type": "message", "content": [{"type": "output_text", "text": "answer"}]})
            )
            rollout.write_text(original)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            shutil.copy2(SCRIPT, bin_dir / SCRIPT.name)
            (bin_dir / SCRIPT.name).chmod(0o755)
            capture = root / "codex-args"
            stub = bin_dir / "codex"
            stub.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$CAPTURE_FILE"\n')
            stub.chmod(0o755)
            env = os.environ | {"HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}", "CAPTURE_FILE": str(capture)}
            launcher = SCRIPT.parent / "agent-tools.zsh"
            cmd = ["zsh", "-c", 'source "$1"; gpt-6-sol_codex resume "$2"', "_", str(launcher), session_id]
            done = subprocess.run(cmd, env=env, capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(capture.read_text().splitlines(), ["resume", "-p", "gpt-6-sol", session_id])
            self.assertEqual(len(rollout.read_text().splitlines()), 4)
            self.assertEqual(next(folder.glob("*.backup-*")).read_text(), original)
            capture.unlink()
            alias = subprocess.run(["zsh", "-c", 'source "$1"; gpt_codex resume "$2"', "_", str(launcher), session_id], env=env, capture_output=True, text=True)
            self.assertEqual(alias.returncode, 0, alias.stderr)
            self.assertEqual(capture.read_text().splitlines(), ["resume", "-p", "gpt-6-sol", session_id])
            capture.unlink()
            equal_form = subprocess.run(["zsh", "-c", 'source "$1"; gpt-6-sol_codex "--resume=$2" "next step"', "_", str(launcher), session_id], env=env, capture_output=True, text=True)
            self.assertEqual(equal_form.returncode, 0, equal_form.stderr)
            self.assertEqual(capture.read_text().splitlines(), ["resume", "-p", "gpt-6-sol", session_id, "next step"])
            self.assertEqual(len(list(folder.glob("*.backup-*"))), 1)
            capture.unlink()
            flagged = subprocess.run(["zsh", "-c", 'source "$1"; gpt-6-sol_codex --resume "$2"', "_", str(launcher), session_id], env=env, capture_output=True, text=True)
            self.assertEqual(flagged.returncode, 0, flagged.stderr)
            self.assertEqual(capture.read_text().splitlines(), ["resume", "-p", "gpt-6-sol", session_id])
            self.assertEqual(len(list(folder.glob("*.backup-*"))), 1)
            capture.unlink()
            bare = subprocess.run(["zsh", "-c", 'source "$1"; gpt-6-sol_codex resume', "_", str(launcher)], env=env, capture_output=True, text=True)
            self.assertEqual(bare.returncode, 0, bare.stderr)
            self.assertEqual(capture.read_text().splitlines(), ["resume", "-p", "gpt-6-sol"])
            capture.unlink()
            native_option = subprocess.run(["zsh", "-c", 'source "$1"; gpt-6-sol_codex resume --help', "_", str(launcher)], env=env, capture_output=True, text=True)
            self.assertEqual(native_option.returncode, 0, native_option.stderr)
            self.assertEqual(capture.read_text().splitlines(), ["resume", "-p", "gpt-6-sol", "--help"])
            capture.unlink()
            invalid = subprocess.run(["zsh", "-c", 'source "$1"; gpt-6-sol_codex --resume bad-id', "_", str(launcher)], env=env, capture_output=True, text=True)
            self.assertNotEqual(invalid.returncode, 0)
            self.assertFalse(capture.exists())
            missing = subprocess.run(["zsh", "-c", 'source "$1"; gpt-6-sol_codex --resume', "_", str(launcher)], env=env, capture_output=True, text=True)
            self.assertEqual(missing.returncode, 2)
            self.assertFalse(capture.exists())

    def test_sync_installs_repair_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            env = os.environ | {"AGENT_TOOLS_TARGET": str(root / "agent-tools.zsh"), "AGENT_RUN_BIN_DIR": str(bin_dir)}
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
